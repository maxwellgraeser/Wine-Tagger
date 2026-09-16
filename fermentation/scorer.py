"""LLM match-scoring, producer-absent hard gate, and web_context assembly.

The scoring LLM sees each snippet's URL and body (in batches of
SCORING_BATCH_SIZE) and returns, per snippet, a 0-100 same-wine score and the
facts it states (grape / region / producer). Indices missing from a reply are
re-asked. The score gates identity (SNIPPET_MATCH_THRESHOLD); the facts decide
which survivors are worth the tagger's context window.

The producer-absent check is a **hard exclusion** (snippets failing the token-overlap test are dropped from
web_context entirely) rather than a post-tagging confidence cap.

If every snippet fails the producer gate, `score_and_assemble` returns
`(None, scored)` and the caller routes the product straight to needs_review
without invoking the tagger.
"""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Optional

import requests

from . import constants
from .types import Product, ScoredSnippet, Snippet


# ---------------------------------------------------------------------------
# Tokenization / stopwords
# ---------------------------------------------------------------------------

_STOPWORDS = {
    "wine", "wines", "vino", "vin", "vins", "vinho", "weingut", "domaine", "domaines",
    "chateau", "château", "estate", "estates", "winery", "wineries", "cellars", "cellar",
    "the", "a", "an", "of", "and", "or", "&", "et", "und", "y",
    "de", "du", "des", "da", "do", "dos", "das", "di", "della", "delle", "del", "dei",
    "le", "la", "les", "el", "los", "las", "il", "lo", "gli",
    "red", "white", "rose", "rosé", "rosado", "rosato",
    "brut", "extra", "dry", "sec", "doux", "demi", "sweet",
    "reserve", "reserva", "riserva", "gran", "grand", "grande", "vieille", "vieilles", "old", "vines",
    "vintage", "nv", "non", "vintage",
    "ml", "cl", "l", "750ml", "1l", "375ml", "1.5l",
    "bottle", "bottles",
}

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _strip_accents(text: str) -> str:
    """Lowercase + strip diacritics for tolerant token matching."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def _significant_tokens(text: str, min_len: int = 4) -> list[str]:
    """Tokenize text -> lowercase, accent-stripped, stopwords removed, len >= min_len."""
    if not text:
        return []
    normalized = _strip_accents(text)
    return [t for t in _TOKEN_RE.findall(normalized)
            if len(t) >= min_len and t not in _STOPWORDS]


def _snippet_contains_any_token(snippet_body: str, tokens: list[str]) -> bool:
    """True if any (already-normalized) token appears as a substring in the normalized snippet.

    If there are no significant tokens to check (e.g. very short product name),
    fall back to letting the snippet through.
    """
    if not tokens:
        return True
    haystack = _strip_accents(snippet_body)
    return any(t in haystack for t in tokens)


# ---------------------------------------------------------------------------
# LLM call helpers
# ---------------------------------------------------------------------------

def _call_llm(prompt: str, api_url: str, model: str, timeout: int = 45) -> str:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,   # deterministic: at 0.1 the same snippet swung 0<->98 between runs
        "stream": False,
    }
    resp = requests.post(api_url, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def _extract_json(text: str) -> Optional[dict]:
    """Pull the first {...} block out of text and parse it."""
    text = re.sub(r"```(?:json)?", "", text).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# Batch match-score
# ---------------------------------------------------------------------------

_FACT_KINDS = ("grape", "region", "producer")


def _parse_entry(value) -> Optional[tuple[int, list[str]]]:
    """One reply entry -> (score, facts). Accepts the new {"score", "facts"}
    shape and a bare integer (older prompt / a model that ignores the shape)."""
    if isinstance(value, dict):
        raw_score = value.get("score")
        raw_facts = value.get("facts") or []
    else:
        raw_score, raw_facts = value, []
    try:
        score = int(raw_score)
    except (TypeError, ValueError):
        return None
    facts = [f for f in raw_facts if isinstance(f, str) and f.lower() in _FACT_KINDS] \
        if isinstance(raw_facts, list) else []
    return min(100, max(0, score)), sorted({f.lower() for f in facts})


def _score_batch(
    product: Product,
    snippets: list[Snippet],
    indices: list[int],
    api_url: str,
    model: str,
    log: list[dict],
) -> dict[int, tuple[int, list[str]]]:
    """One LLM call over the given snippet indices. Returns whatever parsed
    for those indices (possibly a subset). Appends a record to `log`."""
    name_tokens = _significant_tokens(f"{product.name} {product.brand or ''}")
    lines = []
    for i in indices:
        snip = snippets[i]
        body = snip.body[:constants.SCORING_SNIPPET_CHARS]
        # Vivino / CellarTracker descriptions often omit the producer while the
        # slug has it; the model sometimes overlooks the URL, so say it outright.
        hint = ""
        body_norm, url_norm = _strip_accents(body), _strip_accents(snip.url or "")
        url_only = [t for t in name_tokens if t in url_norm and t not in body_norm]
        if url_only:
            hint = (f"    [note: \"{', '.join(url_only)}\" from the product name appears in "
                    f"this URL but not in the text]\n")
        lines.append(f"[{i}] ({snip.source}) {snip.url}\n{hint}    {body}")
    prompt = constants.BATCH_MATCH_SCORE_PROMPT.format(
        name=product.name,
        brand=product.brand or "unknown",
        snippets_block="\n\n".join(lines),
        index_list=", ".join(str(i) for i in indices),
    )
    rec: dict = {"indices": indices, "response": None, "error": None, "attempts": 0}
    log.append(rec)
    parsed: dict = {}
    for attempt, text in enumerate((prompt, prompt + constants.STRICT_SUFFIX), start=1):
        rec["attempts"] = attempt
        try:
            reply = _call_llm(text, api_url, model, timeout=constants.SCORING_TIMEOUT_SECONDS)
        except Exception as exc:  # noqa: BLE001 — network/HTTP failure: try once more
            rec["error"] = f"{type(exc).__name__}: {exc}"
            continue
        rec["response"] = reply
        got = _extract_json(reply)
        if isinstance(got, dict) and got:
            parsed = got
            rec["error"] = None
            break
        rec["error"] = "no JSON object in reply"
    out: dict[int, tuple[int, list[str]]] = {}
    for i in indices:
        value = parsed.get(str(i), parsed.get(i))
        if value is None:
            continue
        entry = _parse_entry(value)
        if entry is not None:
            out[i] = entry
    return out


def _batch_match_score(
    product: Product,
    snippets: list[Snippet],
    api_url: str,
    model: str,
) -> tuple[dict[int, tuple[int, list[str]]], dict]:
    """Score every snippet 0-100 for product match and record which facts
    (grape / region / producer) it states.

    Snippets are scored in batches of SCORING_BATCH_SIZE; any index the model
    leaves out of its reply is re-asked (SCORING_MISSING_RETRIES rounds) rather
    than silently treated as 0 — on the 2026-09-15 run 28% of name-matching
    snippets were lost that way. Indices still missing afterwards are absent
    from the returned dict so the caller can mark them "unscored".

    Returns `({index: (score, facts)}, raw)`; `raw` holds every call's reply
    and error under `calls`, plus `missing` (indices never scored).
    """
    raw: dict = {"calls": [], "missing": [], "attempts": 0}
    if not snippets:
        return {}, raw

    results: dict[int, tuple[int, list[str]]] = {}
    pending = list(range(len(snippets)))
    size = max(1, constants.SCORING_BATCH_SIZE)
    for round_no in range(1 + constants.SCORING_MISSING_RETRIES):
        if not pending:
            break
        for start in range(0, len(pending), size):
            chunk = pending[start:start + size]
            results.update(_score_batch(product, snippets, chunk, api_url, model, raw["calls"]))
        pending = [i for i in pending if i not in results]
    raw["missing"] = pending
    raw["attempts"] = len(raw["calls"])
    return results, raw


# ---------------------------------------------------------------------------
# Producer-absent gate (hard exclusion)
# ---------------------------------------------------------------------------

def _apply_producer_gate(
    scored: list[ScoredSnippet],
    product: Product,
) -> list[ScoredSnippet]:
    """Mark snippets that lack any product/brand significant token as dropped.

    This is a hard exclusion (not a post-tagging confidence cap) applied
    *before* the tagger ever runs: failing snippets get
    `dropped_reason="producer_absent"` and are excluded from web_context.
    They remain in the returned scored list so the scorer log can record them.

    Returns the same list (mutated in place) for convenience.
    """
    name_tokens = _significant_tokens(product.name or "")
    brand_tokens = _significant_tokens(product.brand or "")
    gate_tokens = list({*name_tokens, *brand_tokens})

    # If we have no tokens at all, _snippet_contains_any_token would let
    # everything through — preserve that behavior here too (no-op gate).
    if not gate_tokens:
        return scored

    for item in scored:
        if item.dropped_reason is not None:
            continue
        # The body is the primary check; the URL slug is a legitimate second
        # place for the producer to appear (vivino.com/en/cloudline-pinot-noir/…)
        # when a site-scoped search returns a description that omits the name.
        haystack = f"{item.snippet.body} {item.snippet.url or ''}"
        if not _snippet_contains_any_token(haystack, gate_tokens):
            item.dropped_reason = "producer_absent"
    return scored


# ---------------------------------------------------------------------------
# Web-context assembly
# ---------------------------------------------------------------------------

def _source_family(s: ScoredSnippet) -> str:
    """'Wine Searcher (UPC) #2' -> 'wine searcher (upc)'; groups a source's
    numbered results together so diversity is measured across sources."""
    return re.sub(r"\s*#\d+$", "", s.snippet.source or "").strip().lower()


def _fact_rank(s: ScoredSnippet) -> tuple[int, int, int]:
    """Sort key (desc): grape named, number of facts, score. The score is an
    identity gate; among survivors what matters is what the snippet *says*."""
    return (1 if "grape" in s.facts else 0, len(s.facts), s.match_score)


def _pick_diverse(survivors: list[ScoredSnippet], top_n: int) -> list[ScoredSnippet]:
    """Choose up to `top_n` survivors so the context holds distinct facts
    rather than five price pages that repeat the name.

    Survivors are ordered by `_fact_rank` (grape-naming first, then most
    facts, then score); then:
      1. the distributor's snippet, if one survived (it names the exact blend);
      2. the best snippet from each source not yet represented;
      3. remaining slots in rank order.

    Output keeps rank order within each pass so the tagger sees the most
    informative evidence first.
    """
    survivors = sorted(survivors, key=_fact_rank, reverse=True)
    chosen: list[ScoredSnippet] = []
    seen_families: set[str] = set()

    def take(s: ScoredSnippet) -> None:
        chosen.append(s)
        seen_families.add(_source_family(s))

    for s in survivors:
        if len(chosen) >= top_n:
            break
        if "(distributor)" in (s.snippet.source or "") and _source_family(s) not in seen_families:
            take(s)
    for s in survivors:
        if len(chosen) >= top_n:
            break
        if s not in chosen and _source_family(s) not in seen_families:
            take(s)
    for s in survivors:
        if len(chosen) >= top_n:
            break
        if s not in chosen:
            take(s)
    return chosen


def _build_web_context(
    scored: list[ScoredSnippet],
    threshold: int = constants.SNIPPET_MATCH_THRESHOLD,
    top_n: int = constants.TOP_N_SNIPPETS,
) -> Optional[str]:
    """Top-N labeled block built from survivors only.

    Caller must have already applied the producer gate; we skip anything with
    a `dropped_reason` set and anything below the score threshold. Top-N trim
    is the LAST step (after gating), per PLAN.md.
    """
    survivors = [
        s for s in scored
        if s.dropped_reason is None and s.match_score >= threshold
    ]
    if not survivors:
        return None
    top = _pick_diverse(survivors, top_n)
    for s in top:
        s.in_context = True
    parts = [
        f"[{s.snippet.source} | match={s.match_score}]\n{s.snippet.body}"
        for s in top
    ]
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_and_assemble(
    product: Product,
    snippets: list[Snippet],
    *,
    api_url: str,
    model: str,
    producer_gate: bool = True,
    return_raw: bool = False,
):
    """Score snippets, apply producer-absent hard gate, trim top-N, assemble context.

    Returns `(web_context_or_None, scored_full_list)`. The full list always
    includes every input snippet (with `dropped_reason` set where applicable);
    web_context is built only from snippets that passed the gate AND cleared
    the score threshold. If the gate kills every snippet — or none clear
    threshold — web_context is None and the caller should route the product
    straight to needs_review without invoking the tagger.

    Snippets that made the top-N cut are flagged `in_context=True`. With
    `return_raw=True` a third element carries every scoring call's raw reply.
    """
    def _ret(ctx, scored_list, raw):
        return (ctx, scored_list, raw) if return_raw else (ctx, scored_list)

    if not snippets:
        return _ret(None, [], {"calls": [], "missing": [], "attempts": 0})

    results, llm_raw = _batch_match_score(product, snippets, api_url, model)

    scored: list[ScoredSnippet] = []
    for i, s in enumerate(snippets):
        if i in results:
            score, facts = results[i]
            scored.append(ScoredSnippet(snippet=s, match_score=score, cleaned_body=s.body, facts=facts))
        else:
            # Never scored even after re-asks: visible in the log as "unscored",
            # not disguised as a confident 0.
            scored.append(ScoredSnippet(snippet=s, match_score=0, cleaned_body=s.body,
                                        dropped_reason="unscored"))

    if producer_gate:
        _apply_producer_gate(scored, product)

        # If every snippet is gone (gate or unscored), signal hard-skip to caller.
        if all(s.dropped_reason is not None for s in scored):
            return _ret(None, scored, llm_raw)

    web_context = _build_web_context(scored)
    return _ret(web_context, scored, llm_raw)
