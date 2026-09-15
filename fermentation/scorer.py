"""LLM match-scoring, producer-absent hard gate, and web_context assembly.

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

def _batch_match_score(
    product: Product,
    snippets: list[Snippet],
    api_url: str,
    model: str,
) -> tuple[dict[int, int], dict]:
    """One LLM call rating each snippet 0-100 for product-match quality.

    Returns `({snippet_index: score}, raw)` where `raw` records what the LLM
    returned (`response`, `parsed`, `attempts`, `error`) so a parse failure
    is visible in the scorer log instead of silently scoring everything 0.
    If the first reply does not parse as JSON, one retry is made with
    STRICT_SUFFIX appended. Snippets arriving here are already cleaned by
    searcher; we score against `body` directly.
    """
    raw: dict = {"response": None, "parsed": None, "attempts": 0, "error": None}
    if not snippets:
        return {}, raw

    lines = [
        f"[{i}] ({s.source}): {s.body[:constants.SCORING_SNIPPET_CHARS]}"
        for i, s in enumerate(snippets)
    ]
    snippets_block = "\n\n".join(lines)

    prompt = constants.BATCH_MATCH_SCORE_PROMPT.format(
        name=product.name,
        brand=product.brand or "unknown",
        snippets_block=snippets_block,
    )

    raw_scores: dict = {}
    for attempt, text in enumerate((prompt, prompt + constants.STRICT_SUFFIX), start=1):
        raw["attempts"] = attempt
        try:
            reply = _call_llm(text, api_url, model, timeout=constants.SCORING_TIMEOUT_SECONDS)
        except Exception as exc:  # noqa: BLE001 — network/HTTP failure: try once more, then score 0s
            raw["error"] = f"{type(exc).__name__}: {exc}"
            continue
        raw["response"] = reply
        parsed = _extract_json(reply)
        if isinstance(parsed, dict) and parsed:
            raw_scores = parsed
            raw["parsed"] = parsed
            raw["error"] = None
            break
        raw["error"] = "no JSON object in reply"

    out: dict[int, int] = {}
    for i in range(len(snippets)):
        try:
            score = int(raw_scores.get(str(i), raw_scores.get(i, 0)))
        except (TypeError, ValueError):
            score = 0
        out[i] = min(100, max(0, score))
    return out, raw


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


def _pick_diverse(survivors: list[ScoredSnippet], top_n: int) -> list[ScoredSnippet]:
    """Choose up to `top_n` survivors (already sorted by score, desc) so the
    context holds distinct facts rather than three copies of one page:

      1. the distributor's snippet, if one survived (it names the exact blend);
      2. the best-scoring snippet from each source not yet represented;
      3. remaining slots by score.

    Output keeps score order within each pass so the tagger still sees the
    strongest evidence first.
    """
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
    survivors.sort(key=lambda s: s.match_score, reverse=True)
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
    `return_raw=True` a third element carries the scoring LLM's raw reply.
    """
    def _ret(ctx, scored_list, raw):
        return (ctx, scored_list, raw) if return_raw else (ctx, scored_list)

    if not snippets:
        return _ret(None, [], {"response": None, "parsed": None, "attempts": 0, "error": None})

    raw_scores, llm_raw = _batch_match_score(product, snippets, api_url, model)

    scored: list[ScoredSnippet] = [
        ScoredSnippet(
            snippet=s,
            match_score=raw_scores.get(i, 0),
            cleaned_body=s.body,
            dropped_reason=None,
        )
        for i, s in enumerate(snippets)
    ]

    if producer_gate:
        _apply_producer_gate(scored, product)

        # If every snippet failed the producer gate, signal hard-skip to caller.
        if all(s.dropped_reason == "producer_absent" for s in scored):
            return _ret(None, scored, llm_raw)

    web_context = _build_web_context(scored)
    return _ret(web_context, scored, llm_raw)
