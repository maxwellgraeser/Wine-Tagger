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
from .constants import ORGANIC_PHRASES
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


def _is_manual(ctx: RunContext, product: Product) -> bool:
    row = store_mod.find_wine(ctx.store, product.id)
    return bool(row and row.get("tag_status") == "manual")


def _set_phase_status(ctx: RunContext, product: Product, phase: str, status: str) -> None:
    row = store_mod.ensure_wine(ctx.store, product)
    row["phase_status"][phase] = status
    if status != "skipped":
        # A skipped (manual) wine keeps pointing at the run that produced its logs.
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
    counts = {"searched": 0, "skipped_manual": 0, "no_snippets": 0, "snippets_total": 0}
    for idx in range(start, total):
        product = ctx.products[idx]
        if _is_manual(ctx, product):
            counts["skipped_manual"] += 1
            _set_phase_status(ctx, product, "search", "skipped")
            ctx.sink.progress("search", idx, total, product.id, product.name, "skip (manual)")
            _checkpoint(ctx, "search", idx + 1)
            continue

        snippets = searcher.gather_snippets(product)
        _write_log(ctx, "search", product.id, {
            "product_id": product.id,
            "name": product.name,
            "brand": product.brand,
            "sku": product.sku,
            "raw_snippet_count": len(snippets),
            "snippets": [asdict(s) for s in snippets],
            "written_at": _now(),
        })
        counts["searched"] += 1
        counts["snippets_total"] += len(snippets)
        if not snippets:
            counts["no_snippets"] += 1
        _set_phase_status(ctx, product, "search", "ok" if snippets else "empty")
        ctx.sink.progress("search", idx, total, product.id, product.name,
                          f"{len(snippets)} snippets", snippet_count=len(snippets))
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
    return out


def _scored_payload(product: Product, scored: list[ScoredSnippet], web_context: Optional[str],
                    input_count: int) -> dict:
    dropped = sum(1 for s in scored if s.dropped_reason == "producer_absent")
    return {
        "product_id": product.id,
        "name": product.name,
        "input_count": input_count,
        "producer_gate_dropped": dropped,
        "scored_snippets": [
            {
                "source": s.snippet.source,
                "domain": s.snippet.domain,
                "url": s.snippet.url,
                "body": s.cleaned_body,
                "match_score": s.match_score,
                "dropped_reason": s.dropped_reason,
            }
            for s in scored
        ],
        "web_context_built": web_context is not None,
        "web_context": web_context,
        "written_at": _now(),
    }


def run_score(ctx: RunContext, start: int = 0) -> None:
    _begin_phase(ctx, "score", start)
    total = len(ctx.products)
    cfg = ctx.config
    counts = {"scored": 0, "skipped_manual": 0, "with_context": 0, "no_context": 0}
    for idx in range(start, total):
        product = ctx.products[idx]
        if _is_manual(ctx, product):
            counts["skipped_manual"] += 1
            _set_phase_status(ctx, product, "score", "skipped")
            ctx.sink.progress("score", idx, total, product.id, product.name, "skip (manual)")
            _checkpoint(ctx, "score", idx + 1)
            continue

        snippets = _snippets_from_log(_read_log(ctx, "search", product.id))
        web_context, scored = scorer.score_and_assemble(
            product, snippets, api_url=cfg.api_url, model=cfg.model,
            producer_gate=cfg.producer_gate,
        )
        _write_log(ctx, "scorer", product.id, _scored_payload(product, scored, web_context, len(snippets)))
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

def decide_tag_status(*, normalized: Optional[ParsedTags], confidence_threshold: int) -> str:
    """None -> needs_review; confidence < threshold -> needs_review; else auto."""
    if normalized is None:
        return "needs_review"
    conf = normalized.confidence
    if conf is None or conf < confidence_threshold:
        return "needs_review"
    return "auto"


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
    counts = {"tagged": 0, "auto": 0, "needs_review": 0, "skipped_manual": 0, "no_context": 0}

    with tagger.library_mcp_session() as mcp:
        for idx in range(start, total):
            product = ctx.products[idx]
            row = store_mod.ensure_wine(ctx.store, product)
            if row.get("tag_status") == "manual":
                counts["skipped_manual"] += 1
                _set_phase_status(ctx, product, "tag", "skipped")
                ctx.sink.progress("tag", idx, total, product.id, product.name, "skip (manual)")
                _checkpoint(ctx, "tag", idx + 1)
                continue

            score_log = _read_log(ctx, "score", product.id) or {}
            web_context: Optional[str] = score_log.get("web_context")
            normalized: Optional[ParsedTags] = None
            transcript: list[dict] = []

            if web_context is None:
                tag_status = "needs_review"
                counts["no_context"] += 1
                _set_phase_status(ctx, product, "tag", "no_context")
            else:
                normalized, transcript = tagger.infer_tags(
                    product, web_context, api_url=cfg.api_url, model=cfg.model, mcp_session=mcp,
                )
                tag_status = decide_tag_status(
                    normalized=normalized, confidence_threshold=cfg.confidence_threshold,
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
                "organic": organic,
                "normalized": store_mod.parsed_tags_to_dict(normalized),
                "tags_raw": row["tags_raw"],
                "written_at": _now(),
            })

            counts["tagged"] += 1
            counts[tag_status if tag_status in ("auto", "needs_review") else "needs_review"] += 1
            conf = normalized.confidence if normalized and normalized.confidence is not None else None
            ctx.sink.progress(
                "tag", idx, total, product.id, product.name,
                f"{tag_status} (conf={conf if conf is not None else '—'}) {row['tags_raw'] or ''}",
                tag_status=tag_status, confidence=conf, tags_raw=row["tags_raw"],
            )
            _checkpoint(ctx, "tag", idx + 1)

    _end_phase(ctx, "tag", counts)


PHASE_RUNNERS = {"search": run_search, "score": run_score, "tag": run_tag}


def run_all(ctx: RunContext, resume_phase: str = "search", resume_cursor: int = 0) -> None:
    """Run phases in order starting at (resume_phase, resume_cursor)."""
    started = False
    for phase in PHASES:
        if phase == resume_phase:
            started = True
            PHASE_RUNNERS[phase](ctx, resume_cursor)
        elif started:
            PHASE_RUNNERS[phase](ctx, 0)
    ctx.run_json["status"] = "done"
    ctx.run_json["ended_at"] = _now()
    ctx.store["last_run_id"] = ctx.run_id
    store_mod.save_store(ctx.store)
    ctx.save_run_json()
    clear_run_state()
