"""The three fermentation phases, each run over the whole product set.

    search : every wine  -> logs/<run>/search/<id>.json   (raw snippets)
    score  : every wine  -> logs/<run>/scorer/<id>.json   (scores, gate, web_context)
    tag    : every wine  -> logs/<run>/tagger/<id>.json   (MCP transcript)
                         -> logs/<run>/final/<id>.json    (normalized + tag_status)
                         -> output/wines.json             (the store)

Phases are strictly sequential: score reads the search logs, tag reads the
scorer logs. That is what makes each intermediate visible on disk and lets
a run resume mid-phase from `output/.run_state.json`.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from . import scorer, searcher, store as store_mod, tagger
from .constants import (
    GRAPE_MIN_SOURCES, ORGANIC_PHRASES, REGION_UPGRADE_NEEDS_REVIEW, REQUIRE_GRAPE_EVIDENCE,
    SINGLE_SOURCE_CONFIDENCE_CAP,
)
from .evidence import (
    blend_named_whole, context_calls_it_a_blend, context_source_count, finer_regions_named, grape_source_counts,
    longer_regions_named, region_from_name, region_from_sources, replace_region, unsupported_regions,
    white_grapes_only,
)
from .events import EventSink
from .paths import PHASES, RUN_STATE_PATH, phase_dir, run_dir
from .types import ParsedTags, Product, ScoredSnippet, Snippet


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_run_id() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


# ---------------------------------------------------------------------------
# Run context + run.json
# ---------------------------------------------------------------------------

@dataclass
class RunConfig:
    api_url: str
    model: str
    confidence_threshold: int
    producer_gate: bool = True
    limit: int = 0
    input_csv: str = ""
    grape_color: bool = True       # lookup_grape shows the colour (setting lookup_grape_color)


@dataclass
class RunContext:
    run_id: str
    config: RunConfig
    products: list[Product]          # the fixed set this run works on
    sink: EventSink
    store: dict
    run_json: dict = field(default_factory=dict)

    @property
    def dir(self) -> Path:
        return run_dir(self.run_id)

    def save_run_json(self) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "run.json").write_text(
            json.dumps(self.run_json, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )


def load_run_json(run_id: str) -> Optional[dict]:
    p = run_dir(run_id) / "run.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return None


def init_run_json(ctx: RunContext) -> None:
    ctx.run_json = {
        "run_id": ctx.run_id,
        "started_at": _now(),
        "ended_at": None,
        "status": "running",
        "config": asdict(ctx.config),
        "product_ids": [p.id for p in ctx.products],
        "product_names": {p.id: p.name for p in ctx.products},
        "phases": {
            ph: {"status": "pending", "started_at": None, "ended_at": None, "counts": {}}
            for ph in PHASES
        },
    }
    ctx.save_run_json()


def run_plan(total: int, resume_phase: str, cursor: int) -> dict[str, dict]:
    """Each phase's state as an invocation starts at (resume_phase, cursor):
    earlier phases are done, the resume phase has `cursor` wines done."""
    start = PHASES.index(resume_phase)
    plan = {}
    for i, ph in enumerate(PHASES):
        if i < start:
            plan[ph] = {"state": "done", "done": total}
        else:
            plan[ph] = {"state": "pending", "done": cursor if i == start else 0}
    return plan


def _phase_state(ctx: RunContext, phase: str) -> dict:
    return ctx.run_json["phases"][phase]


# ---------------------------------------------------------------------------
# Run state (resume cursor) — output/.run_state.json
# ---------------------------------------------------------------------------

def load_run_state() -> Optional[dict]:
    if RUN_STATE_PATH.exists():
        try:
            return json.loads(RUN_STATE_PATH.read_text(encoding="utf-8"))
        except ValueError:
            return None
    return None


def save_run_state(run_id: str, phase: str, cursor: int) -> None:
    RUN_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUN_STATE_PATH.write_text(json.dumps({
        "run_id": run_id, "phase": phase, "cursor": cursor, "saved_at": _now(),
    }), encoding="utf-8")


def clear_run_state() -> None:
    if RUN_STATE_PATH.exists():
        RUN_STATE_PATH.unlink()


# ---------------------------------------------------------------------------
# Per-product log files
# ---------------------------------------------------------------------------

def _write_log(ctx: RunContext, phase_folder: str, product_id: str, payload: dict) -> None:
    d = ctx.dir / phase_folder
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{product_id}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8",
    )


def _read_log(ctx: RunContext, phase: str, product_id: str) -> Optional[dict]:
    p = phase_dir(ctx.run_id, phase) / f"{product_id}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return None


def _is_human(ctx: RunContext, product: Product) -> bool:
    """Human-edited rows are never re-processed."""
    row = store_mod.find_wine(ctx.store, product.id)
    return bool(row and row.get("tag_status") == "human")


def _set_phase_status(ctx: RunContext, product: Product, phase: str, status: str) -> None:
    row = store_mod.ensure_wine(ctx.store, product)
    row["phase_status"][phase] = status
    if status != "skipped":
        # A skipped (human-edited) wine keeps pointing at the run that produced its logs.
        row["run_id"] = ctx.run_id
    row["updated_at"] = _now()


def _begin_phase(ctx: RunContext, phase: str, start: int) -> None:
    st = _phase_state(ctx, phase)
    if st["started_at"] is None:
        st["started_at"] = _now()
    st["status"] = "running"
    ctx.run_json["status"] = "running"
    ctx.save_run_json()
    ctx.sink.phase_start(phase, len(ctx.products))
    if start:
        ctx.sink.info(f"Resuming {phase} from wine {start + 1}", phase=phase, cursor=start)


def _end_phase(ctx: RunContext, phase: str, counts: dict) -> None:
    st = _phase_state(ctx, phase)
    st["status"] = "done"
    st["ended_at"] = _now()
    st["counts"] = counts
    ctx.save_run_json()
    ctx.sink.phase_end(phase, **counts)


def _checkpoint(ctx: RunContext, phase: str, next_index: int) -> None:
    store_mod.save_store(ctx.store)
    save_run_state(ctx.run_id, phase, next_index)


# ---------------------------------------------------------------------------
# Phase 1 — search
# ---------------------------------------------------------------------------

def run_search(ctx: RunContext, start: int = 0) -> None:
    _begin_phase(ctx, "search", start)
    total = len(ctx.products)
    counts = {"searched": 0, "skipped_human": 0, "no_snippets": 0, "snippets_total": 0}
    for idx in range(start, total):
        product = ctx.products[idx]
        if _is_human(ctx, product):
            counts["skipped_human"] += 1
            _set_phase_status(ctx, product, "search", "skipped")
            ctx.sink.progress("search", idx, total, product.id, product.name, "skip (human)",
                              skipped=True)
            _checkpoint(ctx, "search", idx + 1)
            continue

        ctx.sink.wine_start("search", idx, total, product.id, product.name)
        snippets, search_errors, n_dup = searcher.gather_snippets(product, return_errors=True)
        _write_log(ctx, "search", product.id, {
            "product_id": product.id,
            "name": product.name,
            "brand": product.brand,
            "sku": product.sku,
            "raw_snippet_count": len(snippets),
            "snippets": [asdict(s) for s in snippets],
            # One entry per query that raised (rate limits, timeouts). An empty
            # snippet list with errors here means the search engine, not the wine.
            "errors": search_errors,
            # Near-duplicate bodies collapsed before this list was written.
            "near_duplicates_dropped": n_dup,
            "written_at": _now(),
        })
        counts["searched"] += 1
        counts["snippets_total"] += len(snippets)
        if not snippets:
            counts["no_snippets"] += 1
        _set_phase_status(ctx, product, "search", "ok" if snippets else "empty")
        err_note = f", {len(search_errors)} query errors" if search_errors else ""
        ctx.sink.progress("search", idx, total, product.id, product.name,
                          f"{len(snippets)} snippets{err_note}",
                          snippet_count=len(snippets), error_count=len(search_errors))
        _checkpoint(ctx, "search", idx + 1)
    _end_phase(ctx, "search", counts)


# ---------------------------------------------------------------------------
# Phase 2 — score
# ---------------------------------------------------------------------------

def _snippets_from_log(log: Optional[dict]) -> list[Snippet]:
    if not log:
        return []
    out = []
    for s in log.get("snippets") or []:
        out.append(Snippet(
            source=s.get("source", ""), domain=s.get("domain", ""),
            body=s.get("body", ""), url=s.get("url", ""),
        ))
    # Older search logs (before 2026-09-15) were not deduped on write.
    out, _ = searcher.dedupe_near_duplicates(out)
    return out


def _scored_payload(product: Product, scored: list[ScoredSnippet], web_context: Optional[str],
                    input_count: int, llm_raw: Optional[dict] = None) -> dict:
    dropped = sum(1 for s in scored if s.dropped_reason == "producer_absent")
    return {
        "product_id": product.id,
        "name": product.name,
        "input_count": input_count,
        "producer_gate_dropped": dropped,
        "context_count": sum(1 for s in scored if s.in_context),
        "scored_snippets": [
            {
                "source": s.snippet.source,
                "domain": s.snippet.domain,
                "url": s.snippet.url,
                "body": s.cleaned_body,
                "match_score": s.match_score,
                "dropped_reason": s.dropped_reason,
                # True for the top-N survivors that were pasted into web_context
                # and therefore seen by the tagger LLM.
                "in_context": s.in_context,
                # What the scorer LLM says the snippet states: subset of
                # grape/region/producer. Logged for comparison only.
                "facts": s.facts,
                # Library grapes and regions the body names; these rank the
                # survivors for the context (scorer._fact_rank).
                "text_facts": s.text_facts,
            }
            for s in scored
        ],
        "web_context_built": web_context is not None,
        "web_context": web_context,
        # Every scoring call's reply/error (`calls`) and indices never scored (`missing`).
        "llm": llm_raw,
        "written_at": _now(),
    }


def run_score(ctx: RunContext, start: int = 0) -> None:
    _begin_phase(ctx, "score", start)
    total = len(ctx.products)
    cfg = ctx.config
    counts = {"scored": 0, "skipped_human": 0, "with_context": 0, "no_context": 0}
    for idx in range(start, total):
        product = ctx.products[idx]
        if _is_human(ctx, product):
            counts["skipped_human"] += 1
            _set_phase_status(ctx, product, "score", "skipped")
            ctx.sink.progress("score", idx, total, product.id, product.name, "skip (human)",
                              skipped=True)
            _checkpoint(ctx, "score", idx + 1)
            continue

        ctx.sink.wine_start("score", idx, total, product.id, product.name)
        snippets = _snippets_from_log(_read_log(ctx, "search", product.id))
        web_context, scored, llm_raw = scorer.score_and_assemble(
            product, snippets, api_url=cfg.api_url, model=cfg.model,
            producer_gate=cfg.producer_gate, return_raw=True,
        )
        _write_log(ctx, "scorer", product.id,
                   _scored_payload(product, scored, web_context, len(snippets), llm_raw))
        counts["scored"] += 1
        if web_context is None:
            counts["no_context"] += 1
        else:
            counts["with_context"] += 1
        best = max((s.match_score for s in scored), default=0)
        _set_phase_status(ctx, product, "score", "ok" if web_context else "no_context")
        ctx.sink.progress(
            "score", idx, total, product.id, product.name,
            f"best={best} {'context built' if web_context else 'no web context'}",
            best_score=best, web_context_built=web_context is not None,
        )
        _checkpoint(ctx, "score", idx + 1)
    _end_phase(ctx, "score", counts)


# ---------------------------------------------------------------------------
# Phase 3 — tag
# ---------------------------------------------------------------------------

def apply_evidence_rules(
    normalized: Optional[ParsedTags],
    web_context: Optional[str],
    *,
    product_name: str = "",
    category: Optional[str] = None,
    confidence_threshold: Optional[int] = None,
) -> list[str]:
    """Mechanical checks on what the tagger submitted versus the text it was
    shown. Mutates `normalized` (confidence clamp, region upgrades) and returns the reasons
    that will route the row to needs_review:

      * "no_submit": the model never got a submission accepted.
      * "single_source": every snippet in context came from the same site, so
        nothing corroborates it. Confidence is clamped to
        SINGLE_SOURCE_CONFIDENCE_CAP and the row is routed to review outright
        (see decide_tag_status) — the clamp alone only worked while the
        threshold sat above the cap.
      * "unsupported_grape:<name>": a submitted grape, or any library synonym
        of it, appears nowhere in web_context. The model inferred it from the
        name, region or style (Aster → Tempranillo, Bila Haut → Cinsault).
      * "uncorroborated_grape:<name>": only one source names the grape
        (Curator's Sémillon, Bila Haut's Mourvèdre from a region blurb).
        Skipped when single_source already covers the whole context, and for
        a blend that one snippet names whole (evidence.blend_named_whole)
        while another source names one of its grapes. Also skipped for a
        single varietal (one grape, not is_blend) unless the context calls
        the wine a blend: one source naming the only grape was the largest
        source of false alarms (12 of 29 on the logs to 2026-10-01: Aster ×5,
        Mont Gravet, Librandi…) and a blend is where a grape goes missing.
      * "incomplete_blend": is_blend with one grape. A source calls the wine
        a blend but names only this grape (Chocapalha, Vilafonte).
      * "white_grapes_only": a red or rosé wine submitted with white grapes
        only. `category` is the product's; when it has none, the one the
        model inferred. Urruzola's rosé lost its Hondarrabi Beltza this way.
      * "region_from_name:<submitted>→<name>": the product name names a region
        below the submitted one ("Neirano Barolo", submitted Piedmont), or the
        model submitted none. The gate puts that region and its parents in
        place of the submission (evidence.region_from_name). A reason only
        while REGION_UPGRADE_NEEDS_REVIEW is on; the upgrade happens either way.
      * "name_region_conflict:<name>": the product name names a region on
        another branch than the submitted one. Nothing is changed.
      * "region_from_sources:<submitted>→<name>": after that, exactly one
        finer region outweighs the submitted one in the sources (what
        coarse_region / longer_region would report), so it replaces the
        submission (evidence.region_from_sources). Same switch.
      * "coarse_region:<name>": the context names a canonical region below the
        submitted one (Barolo when the model submitted Piedmont).
      * "longer_region:<name>": the context names a canonical region whose
        name contains the submitted one's (Côte de Brouilly for Brouilly).
        Both region checks need the other region named by enough sources
        (FINER_REGION_MIN_SOURCES, or as many as name the submitted one).
      * "unsupported_region:<name>": the most specific submitted region is
        named nowhere in the context or the product name, nor is any region
        below it (evidence.unsupported_regions). A region from the library,
        not the text: a lookup_sub_regions pick no snippet mentions.
      * "no_grapes": the submission had no grapes.
      * "low_confidence": the model's own confidence, before any clamp, is
        below `confidence_threshold` (when one is given).
    """
    if normalized is None:
        return ["no_submit"]
    reasons: list[str] = []
    own_confidence = normalized.confidence
    single = web_context is not None and context_source_count(web_context) <= 1
    if single:
        if (normalized.confidence is None
                or normalized.confidence > SINGLE_SOURCE_CONFIDENCE_CAP):
            normalized.confidence = SINGLE_SOURCE_CONFIDENCE_CAP
        reasons.append("single_source")
    if REQUIRE_GRAPE_EVIDENCE and normalized.grapes:
        counts = grape_source_counts(normalized.grapes, web_context or "")
        whole_blend = (max(counts.values()) >= GRAPE_MIN_SOURCES
                       and blend_named_whole(normalized.grapes, web_context or ""))
        varietal = (len(normalized.grapes) == 1 and not normalized.is_blend
                    and not context_calls_it_a_blend(web_context or ""))
        for g in normalized.grapes:
            if counts[g] == 0:
                reasons.append(f"unsupported_grape:{g}")
            elif counts[g] < GRAPE_MIN_SOURCES and not single and not whole_blend and not varietal:
                reasons.append(f"uncorroborated_grape:{g}")
    if normalized.is_blend and len(normalized.grapes) == 1:
        reasons.append("incomplete_blend")
    if white_grapes_only(normalized.grapes, category or normalized.category):
        reasons.append("white_grapes_only")
    if product_name:
        action, name = region_from_name(normalized.region, country=normalized.country,
                                        product_name=product_name)
        if action == "upgrade":
            was = normalized.region[0] if normalized.region else "none"
            normalized.region = replace_region(normalized.region, name, country=normalized.country)
            if REGION_UPGRADE_NEEDS_REVIEW:
                reasons.append(f"region_from_name:{was}→{name}")
        elif action == "conflict":
            reasons.append(f"name_region_conflict:{name}")
    if normalized.region and web_context:
        where = dict(country=normalized.country, product_name=product_name)
        finer = region_from_sources(normalized.region, web_context, **where)
        if finer:
            was = normalized.region[0]
            normalized.region = replace_region(normalized.region, finer, country=normalized.country)
            if REGION_UPGRADE_NEEDS_REVIEW:
                reasons.append(f"region_from_sources:{was}→{finer}")
        for region in finer_regions_named(normalized.region, web_context, **where):
            reasons.append(f"coarse_region:{region}")
        for region in longer_regions_named(normalized.region, web_context, **where):
            reasons.append(f"longer_region:{region}")
        for region in unsupported_regions(normalized.region, web_context, **where):
            reasons.append(f"unsupported_region:{region}")
    if not normalized.grapes:
        reasons.append("no_grapes")
    if confidence_threshold is not None and (
            own_confidence is None or own_confidence < confidence_threshold):
        reasons.append("low_confidence")
    return reasons


def decide_tag_status(
    *,
    normalized: Optional[ParsedTags],
    confidence_threshold: int,
    review_reasons: Optional[list[str]] = None,
) -> str:
    """None -> needs_review; no grapes -> needs_review; any review reason ->
    needs_review; confidence < threshold -> needs_review; else model.

    `submit_tags` accepts an empty grape list (with a `no_grapes` warning) so
    the country/region the model *did* find are kept on the row; the empty
    grapes are what route it to review. `review_reasons` comes from
    `apply_evidence_rules`; every reason is a hard route, so it holds whatever
    the threshold is set to."""
    if normalized is None:
        return "needs_review"
    if not normalized.grapes:
        return "needs_review"
    if review_reasons:
        return "needs_review"
    conf = normalized.confidence
    if conf is None or conf < confidence_threshold:
        return "needs_review"
    return "model"


def organic_confirmed(web_context: Optional[str], normalized: Optional[ParsedTags]) -> bool:
    """True only if explicit certification language appears. The model's own
    `organic` flag is not trusted on its own."""
    parts = []
    if web_context:
        parts.append(web_context)
    if normalized is not None:
        parts.append(json.dumps(asdict(normalized), default=str))
    hay = " ".join(parts).lower()
    return any(p in hay for p in ORGANIC_PHRASES)


def run_tag(ctx: RunContext, start: int = 0) -> None:
    _begin_phase(ctx, "tag", start)
    total = len(ctx.products)
    cfg = ctx.config
    counts = {"tagged": 0, "model": 0, "needs_review": 0, "skipped_human": 0, "no_context": 0}

    with tagger.library_mcp_session(grape_color=cfg.grape_color) as mcp:
        for idx in range(start, total):
            product = ctx.products[idx]
            row = store_mod.ensure_wine(ctx.store, product)
            if row.get("tag_status") == "human":
                counts["skipped_human"] += 1
                _set_phase_status(ctx, product, "tag", "skipped")
                ctx.sink.progress("tag", idx, total, product.id, product.name, "skip (human)",
                                  skipped=True)
                _checkpoint(ctx, "tag", idx + 1)
                continue

            ctx.sink.wine_start("tag", idx, total, product.id, product.name)
            score_log = _read_log(ctx, "score", product.id) or {}
            web_context: Optional[str] = score_log.get("web_context")
            normalized: Optional[ParsedTags] = None
            transcript: list[dict] = []
            review_reasons: list[str] = []

            if web_context is None:
                tag_status = "needs_review"
                review_reasons = ["no_context"]
                counts["no_context"] += 1
                _set_phase_status(ctx, product, "tag", "no_context")
            else:
                normalized, transcript = tagger.infer_tags(
                    product, web_context, api_url=cfg.api_url, model=cfg.model, mcp_session=mcp,
                )
                review_reasons = apply_evidence_rules(
                    normalized, web_context, product_name=product.name,
                    category=product.category, confidence_threshold=cfg.confidence_threshold,
                )
                tag_status = decide_tag_status(
                    normalized=normalized, confidence_threshold=cfg.confidence_threshold,
                    review_reasons=review_reasons,
                )
                _set_phase_status(ctx, product, "tag", "ok" if normalized else "no_submit")

            submit_attempts = sum(
                1 for m in transcript
                if isinstance(m, dict) and m.get("role") == "tool" and m.get("name") == "submit_tags"
            )
            _write_log(ctx, "tagger", product.id, {
                "product_id": product.id,
                "name": product.name,
                "had_web_context": web_context is not None,
                "submit_attempts": submit_attempts,
                "success": normalized is not None,
                "transcript": transcript,
                "written_at": _now(),
            })

            organic = organic_confirmed(web_context, normalized)
            store_mod.apply_tags(row, normalized, web_context, tag_status, organic, ctx.run_id)
            _write_log(ctx, "final", product.id, {
                "product_id": product.id,
                "name": product.name,
                "tag_status": tag_status,
                # Why a row that submitted fine still went to needs_review (see apply_evidence_rules).
                "review_reasons": review_reasons,
                "organic": organic,
                "normalized": store_mod.parsed_tags_to_dict(normalized),
                "tags_raw": row["tags_raw"],
                "written_at": _now(),
            })

            counts["tagged"] += 1
            counts[tag_status if tag_status in ("model", "needs_review") else "needs_review"] += 1
            conf = normalized.confidence if normalized and normalized.confidence is not None else None
            why = f" [{', '.join(review_reasons)}]" if review_reasons else ""
            ctx.sink.progress(
                "tag", idx, total, product.id, product.name,
                f"{tag_status} (conf={conf if conf is not None else '—'}){why} {row['tags_raw'] or ''}",
                tag_status=tag_status, confidence=conf, tags_raw=row["tags_raw"],
                review_reasons=review_reasons,
            )
            _checkpoint(ctx, "tag", idx + 1)

    _end_phase(ctx, "tag", counts)


PHASE_RUNNERS = {"search": run_search, "score": run_score, "tag": run_tag}


def run_all(
    ctx: RunContext,
    resume_phase: str = "search",
    resume_cursor: int = 0,
    stop_after: Optional[str] = None,
) -> Optional[str]:
    """Run phases in order starting at (resume_phase, resume_cursor).

    With `stop_after=PHASE` the run pauses once that phase completes: run.json
    gets status "paused", and the resume cursor points at the *next* phase so
    a plain re-run (or `--phase NEXT --run-id ID`) continues from there.
    Returns the phase it paused after, or None when the run finished.
    """
    started = False
    for phase in PHASES:
        if phase == resume_phase:
            started = True
            PHASE_RUNNERS[phase](ctx, resume_cursor)
        elif started:
            PHASE_RUNNERS[phase](ctx, 0)
        else:
            continue
        if stop_after == phase and phase != PHASES[-1]:
            nxt = PHASES[PHASES.index(phase) + 1]
            ctx.run_json["status"] = "paused"
            ctx.run_json["paused_after"] = phase
            ctx.store["last_run_id"] = ctx.run_id
            store_mod.save_store(ctx.store)
            ctx.save_run_json()
            save_run_state(ctx.run_id, nxt, 0)
            return phase
    ctx.run_json["status"] = "done"
    ctx.run_json.pop("paused_after", None)
    ctx.run_json["ended_at"] = _now()
    ctx.store["last_run_id"] = ctx.run_id
    store_mod.save_store(ctx.store)
    ctx.save_run_json()
    clear_run_state()
    return None
