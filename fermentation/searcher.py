"""DDG snippet gathering for the fermentation pipeline.

Owns the network for snippets: per-source + UPC + fallback queries, cross-query
URL dedupe, boilerplate strip, price-only filter. Producer/name verification,
scoring, gating, and LLM calls live elsewhere.
"""

import re
from urllib.parse import urlparse
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
    """Strip known CMS/UI boilerplate phrases, and region-blurb sentences,
    from a snippet body.

    Case-insensitive removal. The original casing of surviving text is
    preserved by walking the string with re.sub.
    """
    if not text:
        return text
    cleaned = text
    for phrase in constants.SNIPPET_BOILERPLATE_PHRASES:
        cleaned = re.sub(re.escape(phrase), " ", cleaned, flags=re.IGNORECASE)
    for sentence in constants.SNIPPET_BOILERPLATE_SENTENCES:
        cleaned = re.sub(sentence, " ", cleaned, flags=re.IGNORECASE)
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


def _is_blocked(url: str) -> bool:
    """True if the URL's host is (or is under) a domain in BLOCKED_DOMAINS."""
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in constants.BLOCKED_DOMAINS)


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


def _client() -> "DDGS": # type: ignore
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
    sku = (product.sku or "").strip()
    dist_domain = _distributor_domain(product.supplier)
    plan: list[tuple[str, str, str]] = []  # (source_label, scope_domain, query)
    for label, template, scope in constants.SEARCH_QUERIES:
        if "{sku}" in template and not _is_upc(sku):
            continue
        if "{dist}" in (template + scope + label) and not dist_domain:
            continue
        fmt = {"name": name, "sku": sku, "dist": dist_domain or "", "supplier": product.supplier or "Distributor"}
        plan.append((label.format(**fmt), scope.format(**fmt), template.format(**fmt)))

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
    blocked = 0
    for (source_name, domain, _query), (snippets, _err) in zip(plan, per_query):
        # Engines (Bing especially) pad site-scoped results with ads from
        # elsewhere; a "Winebow (distributor)" snippet must actually be winebow.com.
        kept_on_site = [it for it in snippets if _on_site(it["href"], domain)]
        off_site += len(snippets) - len(kept_on_site)
        # Known-bad hosts (AI-generated wine pages) never reach the scorer.
        kept = [it for it in kept_on_site if not _is_blocked(it["href"])]
        blocked += len(kept_on_site) - len(kept)
        snippets = kept
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
    if blocked:
        errors.append({"source": "*", "query": "", "error": f"{blocked} results from blocked domains dropped"})
    return results, errors


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------

_WORD_RE = re.compile(r"[a-z]{3,}")


def _word_set(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def _same_url(a: Snippet, b: Snippet) -> bool:
    return (a.url or "").strip().lower().rstrip("/") == (b.url or "").strip().lower().rstrip("/")


def split_aggregate_bodies(snippets: list[Snippet]) -> tuple[list[Snippet], int]:
    """Cut engine answer-blobs back to their own page's text.

    A long body that verbatim-contains at least SNIPPET_BLOB_MIN_SEGMENTS other
    snippets' whole bodies, from other URLs, is not a page description — it is
    several results glued together under one attribution. Everything from the
    first foreign segment onward belongs to some other page (which is already
    in the list, under its own URL and source label), so it is cut. A blob with
    nothing of its own before the splice is dropped outright.

    Returns (snippets, n_trimmed). This must run BEFORE dedupe_near_duplicates:
    trimming is what makes the remaining bodies comparable.
    """
    out: list[Snippet] = []
    trimmed = 0
    for i, snip in enumerate(snippets):
        body = snip.body
        if len(body) < constants.SNIPPET_BLOB_MIN_CHARS:
            out.append(snip)
            continue
        cuts: list[int] = []
        for j, other in enumerate(snippets):
            if i == j or _same_url(snip, other):
                continue
            ob = other.body
            if len(ob) < constants.SNIPPET_BLOB_MIN_SEGMENT or len(ob) >= len(body):
                continue
            at = body.find(ob)
            if at >= 0:
                cuts.append(at)
        if len(cuts) < constants.SNIPPET_BLOB_MIN_SEGMENTS:
            out.append(snip)
            continue
        trimmed += 1
        own = body[:min(cuts)].strip()
        if len(own) < constants.SNIPPET_MIN_CLEANED_CHARS:
            continue
        out.append(Snippet(source=snip.source, domain=snip.domain, body=own, url=snip.url))
    return out, trimmed


def dedupe_near_duplicates(snippets: list[Snippet]) -> tuple[list[Snippet], int]:
    """Drop snippets that repeat an earlier kept one. Returns (kept, dropped).
    Order (and so source labels) is preserved; the earlier snippet wins because
    the plan lists higher-value sources first.

    Two rules, either of which marks a duplicate:

    * word-set Jaccard >= SNIPPET_DEDUPE_JACCARD — the original rule, for one
      page returned under several vintages.
    * both bodies over SNIPPET_BLOB_MIN_CHARS and overlap against the *smaller*
      word set >= SNIPPET_BLOB_CONTAINMENT — the same engine blob served under
      different URLs. Jaccard misses these because each copy is truncated at
      SNIPPET_CHAR_LIMIT at a different offset, so the tails differ enough to
      hold the score just under the threshold (Chocapalha Tinto: 0.84/0.89/0.75
      across three copies of one sentence). Containment is only safe between two
      long bodies; a short snippet's words are routinely a subset of a long
      one's without the two being duplicates at all.
    """
    kept: list[Snippet] = []
    kept_words: list[set[str]] = []
    dropped = 0
    blob_floor = constants.SNIPPET_BLOB_MIN_CHARS
    for s in snippets:
        words = _word_set(s.body)
        is_long = len(s.body) >= blob_floor
        dup = False
        for other_snip, other in zip(kept, kept_words):
            if not words or not other:
                continue
            overlap = len(words & other)
            if overlap / len(words | other) >= constants.SNIPPET_DEDUPE_JACCARD:
                dup = True
                break
            if (
                is_long
                and len(other_snip.body) >= blob_floor
                and overlap / min(len(words), len(other)) >= constants.SNIPPET_BLOB_CONTAINMENT
            ):
                dup = True
                break
        if dup:
            dropped += 1
            continue
        kept.append(s)
        kept_words.append(words)
    return kept, dropped


def _mostly_failed(raw: list[Snippet], errors: list[dict]) -> bool:
    """True when the engine is throttling us: no results at all, or at least
    DDG_RETRY_ERROR_FRACTION of the real queries raised. Bila Haut on the
    2026-09-15 run had 9 of 11 queries time out; the 4 junk results from the
    other two were enough to skip the retry, and its whole context became one
    page about a different cuvée."""
    if not raw:
        return True
    query_errors = [e for e in errors if e.get("source") != "*"]
    if not query_errors:
        return False
    total = len(query_errors) + len({s.source.rsplit(" #", 1)[0] for s in raw})
    return len(query_errors) / max(1, total) >= constants.DDG_RETRY_ERROR_FRACTION


def gather_snippets(product: Product, *, return_errors: bool = False):
    """UPC + per-source + fallback queries with cross-query URL dedupe.

    Returns cleaned snippets: boilerplate phrases stripped, snippets that are
    mostly boilerplate or price-only dropped. Producer/name verification and
    LLM scoring are downstream (scorer.py).

    Engine answer-blobs — one long body that splices several results together
    under a single URL — are cut back to their own page's text first
    (split_aggregate_bodies), then near-duplicate bodies are collapsed to the
    first (dedupe_near_duplicates: one price page listed for three vintages,
    and the same blob served under different URLs).

    If *every* query comes back empty, or most of them raised, the engine is
    almost certainly throttling us (Zenato Pinot Grigio got nothing from any
    query; Bila Haut had 9 of 11 time out), so the whole plan is retried
    after each delay in DDG_RETRY_DELAYS. With `return_errors=True` a second element lists the
    per-query errors from the final attempt.
    """
    raw, errors = _gather_all_snippets(product)
    for delay in constants.DDG_RETRY_DELAYS:
        if not _mostly_failed(raw, errors):
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
    out, n_blob = split_aggregate_bodies(out)
    out, n_dup = dedupe_near_duplicates(out)
    if n_blob:
        errors.append({"source": "*", "query": "", "error": f"{n_blob} aggregate bodies trimmed to their own page"})
    if return_errors:
        return out, errors, n_dup
    return out
