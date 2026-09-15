"""DDG snippet gathering for the fermentation pipeline.

Owns the network for snippets: per-source + UPC + fallback queries, cross-query
URL dedupe, boilerplate strip, price-only filter. Producer/name verification,
scoring, gating, and LLM calls live elsewhere.
"""

import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from typing import Optional

from .types import Product, Snippet
from . import constants

# A missing package is a hard error: a silent fallback here makes every wine
# route to needs_review with zero snippets and no explanation.
try:
    from ddgs import DDGS
except ImportError as _exc:  # pragma: no cover
    raise ImportError(
        "searcher needs the `ddgs` package; install requirements.txt"
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

# Ad / tracking redirect hosts some engines slip into results regardless of
# `site:`. Never useful as wine evidence.
_AD_HOSTS = ("bing.com", "duckduckgo.com", "googleadservices.com", "doubleclick.net")


def _host(url: str) -> str:
    m = re.match(r"https?://([^/?#]+)", url or "")
    return (m.group(1) if m else "").lower().removeprefix("www.")


def _on_site(url: str, domain: str) -> bool:
    """True if a result belongs to the site a `site:` query asked for.
    domain '*' (unscoped queries) only rejects ad-redirect hosts."""
    host = _host(url)
    if not host:
        return False
    if domain == "*":
        return not any(host == h or host.endswith("." + h) for h in _AD_HOSTS)
    d = domain.lower().removeprefix("www.")
    return host == d or host.endswith("." + d)


_local = threading.local()


def _client() -> "DDGS":
    """One DDGS per worker thread, so engine HTTP sessions are reused across
    queries without sharing them between threads."""
    if not hasattr(_local, "ddgs"):
        _local.ddgs = DDGS(timeout=constants.DDG_TIMEOUT_SECONDS)
    return _local.ddgs


def _ddg_snippets(query: str) -> tuple[list[dict], Optional[str]]:
    """Search DuckDuckGo. Returns `(results, error)`: one {body, href} dict per
    result, and the exception text if the query raised (rate limit, timeout)
    so the caller can tell "no results" from "the engine refused us"."""
    try:
        results = _client().text(
            query, max_results=constants.DDG_MAX_RESULTS, timelimit=None,
            backend=constants.DDG_BACKEND,
        )
    except Exception as exc:  # noqa: BLE001 — ddgs raises several types; all are "no answer"
        return [], f"{type(exc).__name__}: {exc}"[:300]
    if not results:
        return [], None
    return [
        {"body": r["body"][:constants.SNIPPET_CHAR_LIMIT], "href": r.get("href", "") or ""}
        for r in results if r.get("body")
    ], None


# ---------------------------------------------------------------------------
# Multi-source gather
# ---------------------------------------------------------------------------

def _distributor_domain(supplier: "str | None") -> "str | None":
    """Map a Lightspeed supplier name to a website via DISTRIBUTOR_SITES
    (case-insensitive substring match, e.g. 'Winebow' / 'WINEBOW INC')."""
    if not supplier:
        return None
    key = supplier.strip().lower()
    for needle, domain in constants.DISTRIBUTOR_SITES.items():
        if needle in key:
            return domain
    return None


def _gather_all_snippets(product: Product) -> tuple[list[Snippet], list[dict]]:
    """Query every curated source plus unscoped fallback. Returns one Snippet per
    individual DDG result, deduped across queries by URL, plus a list of
    `{source, query, error}` for every query that raised.
    """
    name = product.name
    brand = product.brand or ""
    sku = (product.sku or "").strip()
    plan: list[tuple[str, str, str]] = []  # (source_name, domain, query)

    # UPC lookup — listed first so high-confidence barcode hits appear early
    if _is_upc(sku):
        for source in [s for s in constants.CURATED_SOURCES if s.get("upc_capable")]:
            plan.append((f"{source['name']} (UPC)", source["domain"], f'site:{source["domain"]} "{sku}"'))
        plan.append(("UPC fallback", "*", f'"{sku}" wine'))

    # Name-based lookup across all curated sources
    for source in constants.CURATED_SOURCES:
        query = f'site:{source["domain"]} "{name}"'
        if brand:
            query += f" {brand}"
        plan.append((source["name"], source["domain"], query))

    # The distributor's own site, when we know it (see DISTRIBUTOR_SITES)
    # Unquoted on purpose: engines index only a slice of an importer's site,
    # and the product page title rarely matches our catalog name verbatim
    # ("Áster Crianza" vs "Aster Ribera del Duero"). The site: scope plus the
    # URL-host filter keep the noise down.
    dist_domain = _distributor_domain(product.supplier)
    if dist_domain:
        plan.append((f"{product.supplier} (distributor)", dist_domain, f"site:{dist_domain} {name}"))

    # Unscoped name fallback
    fallback_query = f'"{name}"'
    if brand:
        fallback_query += f" {brand}"
    fallback_query += " wine region grapes"
    plan.append(("fallback", "*", fallback_query))

    def _run(i: int) -> tuple[list[dict], Optional[str]]:
        # Stagger starts so concurrent queries don't all hit engines at once.
        time.sleep(i * constants.DDG_SLEEP_SECONDS)
        return _ddg_snippets(plan[i][2])

    # Queries run concurrently; map() keeps plan order, so dedupe and labels
    # come out exactly as they did when queries ran one after another.
    with ThreadPoolExecutor(max_workers=max(1, constants.DDG_CONCURRENCY)) as ex:
        per_query = list(ex.map(_run, range(len(plan))))

    errors = [
        {"source": src, "query": q, "error": err}
        for (src, _d, q), (_r, err) in zip(plan, per_query) if err
    ]
    results: list[Snippet] = []
    seen_urls: set[str] = set()
    off_site = 0
    for (source_name, domain, _query), (snippets, _err) in zip(plan, per_query):
        # Engines (Bing especially) pad site-scoped results with ads from
        # elsewhere; a "Winebow (distributor)" snippet must actually be winebow.com.
        kept_on_site = [it for it in snippets if _on_site(it["href"], domain)]
        off_site += len(snippets) - len(kept_on_site)
        snippets = kept_on_site
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

    if off_site:
        errors.append({"source": "*", "query": "", "error": f"{off_site} off-site/ad results dropped"})
    return results, errors


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------

_WORD_RE = re.compile(r"[a-z]{3,}")


def _word_set(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def dedupe_near_duplicates(snippets: list[Snippet]) -> tuple[list[Snippet], int]:
    """Drop snippets whose word set overlaps an earlier kept one by at least
    SNIPPET_DEDUPE_JACCARD. Returns (kept, dropped_count). Order (and so
    source labels) is preserved; the earlier snippet wins because the plan
    lists higher-value sources first."""
    kept: list[Snippet] = []
    kept_words: list[set[str]] = []
    dropped = 0
    for s in snippets:
        words = _word_set(s.body)
        dup = False
        for other in kept_words:
            if not words or not other:
                continue
            if len(words & other) / len(words | other) >= constants.SNIPPET_DEDUPE_JACCARD:
                dup = True
                break
        if dup:
            dropped += 1
            continue
        kept.append(s)
        kept_words.append(words)
    return kept, dropped


def gather_snippets(product: Product, *, return_errors: bool = False):
    """UPC + per-source + fallback queries with cross-query URL dedupe.

    Returns cleaned snippets: boilerplate phrases stripped, snippets that are
    mostly boilerplate or price-only dropped. Producer/name verification and
    LLM scoring are downstream (scorer.py).

    Near-duplicate bodies (word-set Jaccard >= SNIPPET_DEDUPE_JACCARD, e.g.
    one price page listed for three vintages) are collapsed to the first.

    If *every* query comes back empty the engine is almost certainly
    throttling us (that is what happened to Zenato Pinot Grigio, wine 24/24
    of a run), so the whole plan is retried after each delay in
    DDG_RETRY_DELAYS. With `return_errors=True` a second element lists the
    per-query errors from the final attempt.
    """
    raw, errors = _gather_all_snippets(product)
    for delay in constants.DDG_RETRY_DELAYS:
        if raw:
            break
        time.sleep(delay)
        raw, errors = _gather_all_snippets(product)
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
    out, n_dup = dedupe_near_duplicates(out)
    if return_errors:
        return out, errors, n_dup
    return out
