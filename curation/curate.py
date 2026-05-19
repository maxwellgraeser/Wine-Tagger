#!/usr/bin/env python3
"""
curation/curate.py — wine metadata tagger

Reads ingestion/output/combined.csv, enriches each wine with a web snippet,
calls a local LLM for structured tags, and writes results to curation/output/wines.db.
"""

import argparse
import csv
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Optional

import requests

try:
    from ddgs import DDGS
except ImportError:
    DDGS = None

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
INPUT_CSV = PROJECT_ROOT / "ingestion" / "output" / "combined.csv"
OUTPUT_DIR = SCRIPT_DIR / "output"
DB_PATH = OUTPUT_DIR / "wines.db"
CACHE_PATH = OUTPUT_DIR / "web_cache.json"
RUN_STATE_PATH = OUTPUT_DIR / ".run_state.json"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
from constants import (
    DEFAULT_API_URL,
    DEFAULT_MODEL,
    DEFAULT_CONFIDENCE_THRESHOLD,
    DDG_MAX_RESULTS,
    DDG_SLEEP_SECONDS,
    SNIPPET_CHAR_LIMIT,
    SCORING_SNIPPET_CHARS,
    SNIPPET_MATCH_THRESHOLD,
    TOP_N_SNIPPETS,
    ORGANIC_PHRASES,
    BATCH_MATCH_SCORE_PROMPT,
    PROMPT_TEMPLATE,
    STRICT_SUFFIX,
)

# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------
sys.path.insert(0, str(SCRIPT_DIR))
from constants import CURATED_SOURCES
from normalization import normalize_tags
from normalization.grape_library import CANONICAL_GRAPES

CANONICAL_GRAPES_BLOCK = ", ".join(CANONICAL_GRAPES.keys())


# ---------------------------------------------------------------------------
# SQLite setup
# ---------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    sku          TEXT,
    category     TEXT,
    supply_price REAL,
    retail_price REAL,
    supplier     TEXT,
    brand        TEXT,
    country      TEXT,
    region       TEXT,
    grapes       TEXT,
    is_blend     INTEGER,
    organic      INTEGER DEFAULT 0,
    confidence   INTEGER,
    web_context  TEXT,
    tags_raw     TEXT,
    tag_status   TEXT DEFAULT 'auto',
    created_at   TEXT DEFAULT (datetime('now')),
    updated_at   TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sales (
    sku            TEXT PRIMARY KEY,
    product_id     TEXT REFERENCES products(id),
    items_sold     INTEGER,
    margin_pct     REAL,
    sale_count     INTEGER,
    customer_count INTEGER,
    avg_sale_value REAL,
    report_period  TEXT
);

CREATE TABLE IF NOT EXISTS tag_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id   TEXT REFERENCES products(id),
    raw_prompt   TEXT,
    raw_response TEXT,
    parsed_ok    INTEGER,
    created_at   TEXT DEFAULT (datetime('now'))
);
"""


def open_db(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# Web cache
# ---------------------------------------------------------------------------

def load_cache(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return {}
    return {}


def save_cache(path: Path, cache: dict) -> None:
    path.write_text(json.dumps(cache, indent=2))


# ---------------------------------------------------------------------------
# Web lookup — multi-source with LLM match scoring
# ---------------------------------------------------------------------------

def ddg_snippets(query: str) -> list[dict]:
    """Search DuckDuckGo and return one {body, href} dict per result."""
    if DDGS is None:
        return []
    try:
        results = DDGS().text(query, max_results=DDG_MAX_RESULTS, timelimit=None)
    except Exception:
        return []
    if not results:
        return []
    return [
        {"body": r["body"][:SNIPPET_CHAR_LIMIT], "href": r.get("href", "") or ""}
        for r in results if r.get("body")
    ]


def _is_upc(sku: str) -> bool:
    """Return True if sku looks like a numeric barcode (UPC-A/EAN/GTIN, 8–14 digits)."""
    return bool(sku and re.match(r'^\d{8,14}$', sku.strip()))


def gather_all_snippets(product: dict) -> list[dict]:
    """Query every curated source plus unscoped fallback. Returns one dict per individual DDG result."""
    name = product["name"]
    brand = product.get("brand_name", "") or ""
    sku = (product.get("sku") or "").strip()
    results = []
    seen_urls: set[str] = set()

    def _collect(source_name: str, domain: str, query: str) -> None:
        snippets = ddg_snippets(query)
        time.sleep(DDG_SLEEP_SECONDS)
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
            results.append({"source": label, "domain": domain, "snippet": item["body"], "url": item["href"]})

    # UPC lookup — run first so high-confidence barcode hits appear early
    if _is_upc(sku):
        for source in [s for s in CURATED_SOURCES if s.get("upc_capable")]:
            _collect(f"{source['name']} (UPC)", source["domain"], f'site:{source["domain"]} "{sku}"')
        _collect("UPC fallback", "*", f'"{sku}" wine')

    # Name-based lookup across all curated sources
    for source in CURATED_SOURCES:
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


def score_snippets(product: dict, all_snippets: list[dict], api_url: str, model: str) -> list[dict]:
    """One LLM call to rate all snippets for name-match quality. Returns snippets with match_score added."""
    if not all_snippets:
        return []

    lines = [f"[{i}] ({item['source']}): {item['snippet'][:SCORING_SNIPPET_CHARS]}"
             for i, item in enumerate(all_snippets)]
    snippets_block = "\n\n".join(lines)

    prompt = BATCH_MATCH_SCORE_PROMPT.format(
        name=product["name"],
        brand=product.get("brand_name", "") or "unknown",
        snippets_block=snippets_block,
    )

    try:
        raw = call_llm(prompt, api_url, model, timeout=45)
        scores = extract_json(raw) or {}
        return [
            {**item, "match_score": min(100, max(0, int(scores.get(str(i), scores.get(i, 0)))))}
            for i, item in enumerate(all_snippets)
        ]
    except Exception:
        return [{**item, "match_score": 0} for item in all_snippets]


def build_web_context(scored_snippets: list[dict], threshold: int = SNIPPET_MATCH_THRESHOLD,
                      top_n: int = TOP_N_SNIPPETS) -> Optional[str]:
    """Combine top-N snippets that passed the match threshold into a single labeled context string."""
    relevant = sorted(
        [s for s in scored_snippets if s["match_score"] >= threshold],
        key=lambda x: x["match_score"],
        reverse=True,
    )[:top_n]
    if not relevant:
        return None
    parts = [
        f"[{item['source']} | match={item['match_score']}]\n{item['snippet']}"
        for item in relevant
    ]
    return "\n\n".join(parts)


def web_lookup(product: dict, cache: dict, api_url: str = "", model: str = "") -> tuple[Optional[str], list[dict]]:
    """Multi-source web lookup with LLM match scoring. Returns (web_context, scored_snippets).

    On cache hit, returns the cached context with an empty snippet list.
    api_url and model are required for cache misses (match scoring).
    """
    pid = product["id"]
    if pid in cache:
        return cache[pid], []

    all_snippets = gather_all_snippets(product)
    if not all_snippets:
        cache[pid] = None
        return None, []

    scored = score_snippets(product, all_snippets, api_url, model)
    context = build_web_context(scored)
    cache[pid] = context
    return context, scored


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------

def call_llm(prompt: str, api_url: str, model: str, timeout: int = 60) -> str:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "stream": False,
    }
    resp = requests.post(api_url, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def extract_json(text: str) -> Optional[dict]:
    """Pull the first {...} block out of text and parse it."""
    # Strip markdown fences if present
    text = re.sub(r"```(?:json)?", "", text).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


def infer_tags(product: dict, web_context: Optional[str], api_url: str, model: str):
    """Call LLM, retry once on parse failure. Returns (parsed, prompt, raw_response)."""
    prompt = PROMPT_TEMPLATE.format(
        name=product["name"],
        category=product.get("product_category", ""),
        brand=product.get("brand_name", ""),
        web_context=web_context or "none",
        canonical_grapes=CANONICAL_GRAPES_BLOCK,
    )

    raw = ""
    try:
        raw = call_llm(prompt, api_url, model)
        parsed = extract_json(raw)
        if parsed is not None:
            return parsed, prompt, raw
    except Exception as e:
        raw = f"ERROR: {e}"

    # Retry with stricter prompt
    strict_prompt = prompt + STRICT_SUFFIX
    try:
        raw2 = call_llm(strict_prompt, api_url, model)
        parsed = extract_json(raw2)
        if parsed is not None:
            return parsed, strict_prompt, raw2
        raw = raw2
    except Exception as e:
        raw = f"ERROR on retry: {e}"

    return None, prompt, raw


# ---------------------------------------------------------------------------
# Tag assembly
# ---------------------------------------------------------------------------

def build_tags_raw(parsed: dict) -> str:
    parts = []
    if parsed.get("country"):
        parts.append(parsed["country"])
    if parsed.get("region"):
        parts.append(parsed["region"])
    grapes = parsed.get("grapes") or []
    parts.extend(grapes)
    if parsed.get("is_blend"):
        parts.append("Blend")
    elif parsed.get("is_blend") is False:
        parts.append("Single Varietal")
    if parsed.get("organic"):
        parts.append("Organic")
    return "; ".join(parts)


def organic_confirmed(web_context: Optional[str], parsed: dict) -> bool:
    """Only flag organic when explicit certification language is present."""
    text = ((web_context or "") + " " + json.dumps(parsed)).lower()
    return any(phrase in text for phrase in ORGANIC_PHRASES)


# ---------------------------------------------------------------------------
# DB writes
# ---------------------------------------------------------------------------

def upsert_product(conn: sqlite3.Connection, product: dict, parsed: Optional[dict],
                   web_context: Optional[str], tag_status: str) -> None:
    tags_raw = build_tags_raw(parsed) if parsed else None
    is_blend = None
    organic = 0
    confidence = None
    country = region = grapes_json = None

    if parsed:
        country = parsed.get("country")
        region = parsed.get("region")
        grapes = parsed.get("grapes") or []
        grapes_json = json.dumps(grapes)
        is_blend = 1 if parsed.get("is_blend") else (0 if parsed.get("is_blend") is False else None)
        organic = 1 if organic_confirmed(web_context, parsed) else 0
        confidence = parsed.get("confidence")

    conn.execute(
        """
        INSERT INTO products
            (id, name, sku, category, supply_price, retail_price, supplier, brand,
             country, region, grapes, is_blend, organic, confidence, web_context,
             tags_raw, tag_status, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name, sku=excluded.sku, category=excluded.category,
            supply_price=excluded.supply_price, retail_price=excluded.retail_price,
            supplier=excluded.supplier, brand=excluded.brand,
            country=excluded.country, region=excluded.region, grapes=excluded.grapes,
            is_blend=excluded.is_blend, organic=excluded.organic,
            confidence=excluded.confidence, web_context=excluded.web_context,
            tags_raw=excluded.tags_raw, tag_status=excluded.tag_status,
            updated_at=datetime('now')
        """,
        (
            product["id"], product["name"], product.get("sku"),
            product.get("product_category"),
            float(product["supply_price"]) if product.get("supply_price") else None,
            float(product["retail_price"]) if product.get("retail_price") else None,
            product.get("supplier_name"), product.get("brand_name"),
            country, region, grapes_json, is_blend, organic, confidence,
            web_context, tags_raw, tag_status,
        ),
    )


def upsert_sales(conn: sqlite3.Connection, product: dict) -> None:
    sku = product.get("sku")
    if not sku:
        return
    conn.execute(
        """
        INSERT INTO sales (sku, product_id, items_sold, margin_pct, sale_count,
                           customer_count, avg_sale_value)
        VALUES (?,?,?,?,?,?,?)
        ON CONFLICT(sku) DO UPDATE SET
            product_id=excluded.product_id, items_sold=excluded.items_sold,
            margin_pct=excluded.margin_pct, sale_count=excluded.sale_count,
            customer_count=excluded.customer_count, avg_sale_value=excluded.avg_sale_value
        """,
        (
            sku, product["id"],
            int(float(product["items_sold"])) if product.get("items_sold") else None,
            float(product["margin_pct"]) if product.get("margin_pct") else None,
            int(float(product["sale_count"])) if product.get("sale_count") else None,
            int(float(product["customer_count"])) if product.get("customer_count") else None,
            float(product["avg_sale_value"]) if product.get("avg_sale_value") else None,
        ),
    )


def log_tag(conn: sqlite3.Connection, product_id: str, prompt: str, raw: str, ok: bool) -> None:
    conn.execute(
        "INSERT INTO tag_log (product_id, raw_prompt, raw_response, parsed_ok) VALUES (?,?,?,?)",
        (product_id, prompt, raw, 1 if ok else 0),
    )


# ---------------------------------------------------------------------------
# Run state
# ---------------------------------------------------------------------------

def load_run_state() -> Optional[dict]:
    if RUN_STATE_PATH.exists():
        try:
            return json.loads(RUN_STATE_PATH.read_text())
        except Exception:
            return None
    return None


def save_run_state(last_id: str, cursor: int, batch_size: int) -> None:
    RUN_STATE_PATH.write_text(json.dumps({
        "last_committed_id": last_id,
        "cursor": cursor,
        "batch_size": batch_size,
    }))


def clear_run_state() -> None:
    if RUN_STATE_PATH.exists():
        RUN_STATE_PATH.unlink()


# ---------------------------------------------------------------------------
# CSV loading
# ---------------------------------------------------------------------------

def load_products(csv_path: Path) -> list[dict]:
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def is_eligible(conn: sqlite3.Connection, product: dict) -> bool:
    """Return True if this product should be (re-)tagged."""
    row = conn.execute(
        "SELECT tag_status FROM products WHERE id = ?", (product["id"],)
    ).fetchone()
    if row is None:
        return True
    return row["tag_status"] != "manual"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Curate wine metadata via local LLM.")
    parser.add_argument("--api-url", default=os.environ.get("CURATION_API_URL", DEFAULT_API_URL))
    parser.add_argument("--model", default=os.environ.get("CURATION_MODEL", DEFAULT_MODEL))
    parser.add_argument(
        "--confidence-threshold",
        type=int,
        default=int(os.environ.get("CURATION_CONFIDENCE_THRESHOLD", DEFAULT_CONFIDENCE_THRESHOLD)),
    )
    parser.add_argument("--batch-size", type=int, default=0,
                        help="Pause for review every N wines (0 = no pausing)")
    parser.add_argument("--force", action="store_true",
                        help="Ignore run state and start from the beginning")
    parser.add_argument("--input", default=str(INPUT_CSV),
                        help="Path to combined.csv")
    parser.add_argument("--limit", type=int, default=0,
                        help="Process at most N wines (0 = all); useful for testing")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Handle --force
    if args.force:
        clear_run_state()
        print("--force: starting from scratch.")

    # Load run state
    run_state = load_run_state()
    start_cursor = 0
    if run_state and not args.force:
        saved_batch = run_state.get("batch_size", 0)
        if args.batch_size and saved_batch != args.batch_size:
            ans = input(
                f"Warning: saved batch-size={saved_batch} differs from --batch-size={args.batch_size}. "
                "Resume anyway? [y/N] "
            ).strip().lower()
            if ans not in ("y", "yes"):
                print("Aborted.")
                sys.exit(0)
        start_cursor = run_state.get("cursor", 0)
        last_id = run_state.get("last_committed_id", "?")
        print(f"Resuming from product {start_cursor + 1} (last committed: {last_id})")

    # Load data
    products = load_products(Path(args.input))
    total = len(products)
    print(f"Loaded {total} products from {args.input}")

    conn = open_db(DB_PATH)
    cache = load_cache(CACHE_PATH)

    # Counters
    n_auto = n_review = n_skipped = 0
    batch_auto = batch_review = batch_skipped = 0
    batch_review_list: list[dict] = []

    effective_limit = args.limit if args.limit > 0 else total

    for idx in range(start_cursor, min(total, start_cursor + effective_limit)):
        product = products[idx]
        pos = idx + 1  # 1-based display

        if not is_eligible(conn, product):
            n_skipped += 1
            batch_skipped += 1
            print(f"[{pos}/{total}] SKIP (manual) — {product['name']}")
            save_run_state(product["id"], idx + 1, args.batch_size)
            conn.commit()
            continue

        print(f"[{pos}/{total}] {product['name']}", end="", flush=True)

        # Web lookup — gather all sources, score for name match, build combined context
        web_context, scored_snippets = web_lookup(product, cache, args.api_url, args.model)
        save_cache(CACHE_PATH, cache)
        if scored_snippets:
            n_relevant = sum(1 for s in scored_snippets if s["match_score"] >= SNIPPET_MATCH_THRESHOLD)
            print(f" | sources: {len(scored_snippets)} found, {n_relevant} relevant", end="", flush=True)
        if web_context:
            print(f" | ctx: {web_context[:50]}...", end="", flush=True)
        else:
            print(" | no web context", end="", flush=True)

        # Determine tag_status before LLM
        if web_context is None:
            # Total DDG failure path: was a known label but no snippet → needs_review
            # We still attempt LLM inference
            forced_review = True
        else:
            forced_review = False

        # LLM inference
        parsed, prompt, raw = infer_tags(product, web_context, args.api_url, args.model)

        ok = parsed is not None
        log_tag(conn, product["id"], prompt, raw, ok)

        # Normalize via grape/country/region libraries; any issue → needs_review
        norm_issues: list[str] = []
        if parsed is not None:
            parsed, norm_issues = normalize_tags(parsed)
            if norm_issues:
                print(f" | norm: {','.join(norm_issues)}", end="", flush=True)

        if not ok:
            tag_status = "needs_review"
        elif forced_review:
            tag_status = "needs_review"
        elif norm_issues:
            tag_status = "needs_review"
        elif parsed is not None and parsed.get("confidence", 0) < args.confidence_threshold:
            tag_status = "needs_review"
        else:
            tag_status = "auto"

        upsert_product(conn, product, parsed, web_context, tag_status)
        upsert_sales(conn, product)
        conn.commit()
        save_run_state(product["id"], idx + 1, args.batch_size)

        if tag_status == "needs_review":
            n_review += 1
            batch_review += 1
            confidence_str = str(parsed.get("confidence", "—")) if parsed else "—"
            batch_review_list.append({"id": product["id"], "name": product["name"], "confidence": confidence_str})
            print(f" → needs_review (conf={confidence_str})")
        else:
            n_auto += 1
            batch_auto += 1
            print(f" → auto (conf={parsed.get('confidence') if parsed else '—'})")

        # Batch pause
        batch_pos = idx - start_cursor + 1
        if args.batch_size > 0 and batch_pos % args.batch_size == 0:
            _print_batch_summary(batch_pos, batch_auto, batch_review, batch_skipped, batch_review_list)
            batch_auto = batch_review = batch_skipped = 0
            batch_review_list = []
            ans = input("Continue with next batch? [y/N] ").strip().lower()
            if ans not in ("y", "yes"):
                print("Paused. Re-run the same command to resume.")
                conn.close()
                return

    # Done
    clear_run_state()
    conn.close()
    processed = n_auto + n_review + n_skipped
    print(f"\n=== Done ===")
    print(f"  Processed : {processed}")
    print(f"  Auto-tagged: {n_auto}")
    print(f"  Needs review: {n_review}")
    print(f"  Skipped (manual): {n_skipped}")
    print(f"  DB: {DB_PATH}")


def _print_batch_summary(processed: int, auto: int, review: int, skipped: int,
                          review_list: list[dict]) -> None:
    print(f"\n--- Batch summary (last {processed} wines) ---")
    print(f"  Auto-tagged: {auto}  |  Needs review: {review}  |  Skipped: {skipped}")
    if review_list:
        print("  Needs-review wines:")
        for w in review_list:
            print(f"    {w['id']} — {w['name']} (conf={w['confidence']})")
    print("---")


if __name__ == "__main__":
    main()
