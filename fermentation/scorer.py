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
        "temperature": 0.1,
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
) -> dict[int, int]:
    """One LLM call rating each snippet 0-100 for product-match quality.

    Returns {snippet_index: score}. Missing/invalid entries are treated as 0
    by the caller. Snippets arriving here are already cleaned by searcher;
    we score against `body` directly.
    """
    if not snippets:
        return {}

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
    try:
        raw = _call_llm(prompt, api_url, model, timeout=45)
        raw_scores = _extract_json(raw) or {}
    except Exception:
        raw_scores = {}

    out: dict[int, int] = {}
    for i in range(len(snippets)):
        try:
            score = int(raw_scores.get(str(i), raw_scores.get(i, 0)))
        except (TypeError, ValueError):
            score = 0
        out[i] = min(100, max(0, score))
    return out


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
        if not _snippet_contains_any_token(item.snippet.body, gate_tokens):
            item.dropped_reason = "producer_absent"
    return scored


# ---------------------------------------------------------------------------
# Web-context assembly
# ---------------------------------------------------------------------------

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
    top = survivors[:top_n]
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
) -> tuple[Optional[str], list[ScoredSnippet]]:
    """Score snippets, apply producer-absent hard gate, trim top-N, assemble context.

    Returns `(web_context_or_None, scored_full_list)`. The full list always
    includes every input snippet (with `dropped_reason` set where applicable);
    web_context is built only from snippets that passed the gate AND cleared
    the score threshold. If the gate kills every snippet — or none clear
    threshold — web_context is None and the caller should route the product
    straight to needs_review without invoking the tagger.
    """
    if not snippets:
        return None, []

    raw_scores = _batch_match_score(product, snippets, api_url, model)

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
            return None, scored

    web_context = _build_web_context(scored)
    return web_context, scored
