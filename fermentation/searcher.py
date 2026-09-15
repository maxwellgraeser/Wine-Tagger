"""DDG snippet gathering for the fermentation pipeline.

Owns the network for snippets: per-source + UPC + fallback queries, cross-query
URL dedupe, boilerplate strip, price-only filter. Producer/name verification,
scoring, gating, and LLM calls live elsewhere.
"""

import re
import time

from .types import Product, Snippet
from . import constants

# `ddgs` is the renamed successor of `duckduckgo-search`; accept either so
# the pinned requirement and a newer install both work. A missing package is
# a hard error: a silent None here makes every wine route to needs_review
# with zero snippets and no explanation.
try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError as _exc:  # pragma: no cover
        raise ImportError(
            "searcher needs the `ddgs` (or legacy `duckduckgo-search`) package; "
            "install requirements.txt"
        ) from _exc


# ---------------------------------------------------------------------------
# UPC detection
# ---------------------------------------------------------------------------

def _is_upc(sku: str) -> bool:
    """Return True if sku looks like a numeric barcode (UPC-A/EAN/GTIN, 8-14 digits)."""
    return bool(sku and re.match(r'^\d{8,14}$', sku.strip()))


# ---------------------------------------------------------------------------
# Snippet cleanup
# ---------------------------------------------------------------------------

def _clean_snippet_text(text: str) -> str:
    """Strip known CMS/UI boilerplate phrases from a snippet body.

    Case-insensitive substring removal. The original casing of surviving text is
    preserved by walking the string with re.sub.
    """
    if not text:
        return text
    cleaned = text
    for phrase in constants.SNIPPET_BOILERPLATE_PHRASES:
        cleaned = re.sub(re.escape(phrase), " ", cleaned, flags=re.IGNORECASE)
    # Collapse whitespace left behind by removals
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


_PRICE_ONLY_RE = re.compile(r"^[\s\$\€\£\d\.\,\-x×]+$")


def _is_price_only(text: str) -> bool:
    """True if the cleaned text is essentially just a price tag (numbers/currency)."""
    if not text:
        return True
    return bool(_PRICE_ONLY_RE.match(text))


# ---------------------------------------------------------------------------
# DDG query
# ---------------------------------------------------------------------------

def _ddg_snippets(query: str) -> list[dict]:
    """Search DuckDuckGo and return one {body, href} dict per result."""
    if DDGS is None:
        return []
    try:
        results = DDGS().text(query, max_results=constants.DDG_MAX_RESULTS, timelimit=None)
    except Exception:
        return []
    if not results:
        return []
    return [
        {"body": r["body"][:constants.SNIPPET_CHAR_LIMIT], "href": r.get("href", "") or ""}
        for r in results if r.get("body")
    ]


# ---------------------------------------------------------------------------
# Multi-source gather
# ---------------------------------------------------------------------------

def _gather_all_snippets(product: Product) -> list[Snippet]:
    """Query every curated source plus unscoped fallback. Returns one Snippet per
    individual DDG result, deduped across queries by URL.
    """
    name = product.name
    brand = product.brand or ""
    sku = (product.sku or "").strip()
    results: list[Snippet] = []
    seen_urls: set[str] = set()

    def _collect(source_name: str, domain: str, query: str) -> None:
        snippets = _ddg_snippets(query)
        time.sleep(constants.DDG_SLEEP_SECONDS)
        # Dedupe across all queries: first query to hit a URL keeps it. Prevents
        # repeated URLs from boxing out the top-N pool used for context.
        deduped = []
        for item in snippets:
            key = item["href"].strip().lower().rstrip("/")
            if key and key in seen_urls:
                continue
            if key:
                seen_urls.add(key)
            deduped.append(item)
        for i, item in enumerate(deduped):
            label = f"{source_name} #{i + 1}" if len(deduped) > 1 else source_name
            results.append(Snippet(
                source=label,
                domain=domain,
                body=item["body"],
                url=item["href"],
            ))

    # UPC lookup — run first so high-confidence barcode hits appear early
    if _is_upc(sku):
        for source in [s for s in constants.CURATED_SOURCES if s.get("upc_capable")]:
            _collect(f"{source['name']} (UPC)", source["domain"], f'site:{source["domain"]} "{sku}"')
        _collect("UPC fallback", "*", f'"{sku}" wine')

    # Name-based lookup across all curated sources
    for source in constants.CURATED_SOURCES:
        query = f'site:{source["domain"]} "{name}"'
        if brand:
            query += f" {brand}"
        _collect(source["name"], source["domain"], query)

    # Unscoped name fallback
    fallback_query = f'"{name}"'
    if brand:
        fallback_query += f" {brand}"
    fallback_query += " wine region grapes"
    _collect("fallback", "*", fallback_query)

    return results


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------

def gather_snippets(product: Product) -> list[Snippet]:
    """UPC + per-source + fallback queries with cross-query URL dedupe.

    Returns cleaned snippets: boilerplate phrases stripped, snippets that are
    mostly boilerplate or price-only dropped. Producer/name verification and
    LLM scoring are downstream (scorer.py).
    """
    raw = _gather_all_snippets(product)
    out: list[Snippet] = []
    for snip in raw:
        cleaned = _clean_snippet_text(snip.body)
        original_len = max(1, len(snip.body))
        keep_ratio = len(cleaned) / original_len
        if (
            len(cleaned) < constants.SNIPPET_MIN_CLEANED_CHARS
            or keep_ratio < constants.SNIPPET_BOILERPLATE_KEEP_RATIO
            or _is_price_only(cleaned)
        ):
            continue
        out.append(Snippet(
            source=snip.source,
            domain=snip.domain,
            body=cleaned,
            url=snip.url,
        ))
    return out
