#!/usr/bin/env python3
"""fermentation/ferment.py — controller for the fermentation pipeline.

Pipeline per product: searcher → scorer → tagger → DB write.

The MCP `submit_tags` output is authoritative; there is NO post-tagger
normalize pass and NO producer-absent confidence cap (the producer-absent
check is a hard exclusion enforced in scorer.py).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sqlite3
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from . import debug_output, scorer, searcher, tagger
from .constants import (
    DEFAULT_API_URL,
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_MODEL,
    ORGANIC_PHRASES,
)
from .types import ParsedTags, Product

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
INPUT_CSV = PROJECT_ROOT / "ingestion" / "output" / "combined.csv"
DB_PATH = SCRIPT_DIR / "wines.db"
RUN_STATE_PATH = SCRIPT_DIR / ".run_state.json"


# ---------------------------------------------------------------------------
# Schema — fresh DB. region/grapes stored as JSON-encoded TEXT arrays so they
# match the shape of submit_tags' `normalized` block directly.
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
    region       TEXT,             -- JSON array, e.g. '["Valpolicella","Veneto"]'
    grapes       TEXT,             -- JSON array
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
    transcript   TEXT,              -- JSON-encoded MCP tool-call transcript
    parsed_ok    INTEGER,
    created_at   TEXT DEFAULT (datetime('now'))
);
"""


def open_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# CSV load
# ---------------------------------------------------------------------------

def _to_float(v) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _to_int(v) -> Optional[int]:
    f = _to_float(v)
    if f is None:
        return None
    return int(f)


def load_products(csv_path: Path) -> list[Product]:
    products: list[Product] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            products.append(Product(
                id=row["id"],
                name=row["name"],
                sku=(row.get("sku") or None),
                brand=(row.get("brand_name") or None),
                category=(row.get("product_category") or None),
                supply_price=_to_float(row.get("supply_price")),
                retail_price=_to_float(row.get("retail_price")),
                supplier=(row.get("supplier_name") or None),
                items_sold=_to_int(row.get("items_sold")),
                margin_pct=_to_float(row.get("margin_pct")),
                sale_count=_to_int(row.get("sale_count")),
                customer_count=_to_int(row.get("customer_count")),
                avg_sale_value=_to_float(row.get("avg_sale_value")),
            ))
    return products


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
# DB writes
# ---------------------------------------------------------------------------

def is_eligible(conn: sqlite3.Connection, product: Product) -> bool:
    row = conn.execute(
        "SELECT tag_status FROM products WHERE id = ?", (product.id,)
    ).fetchone()
    if row is None:
        return True
    return row["tag_status"] != "manual"


def build_tags_raw(normalized: Optional[ParsedTags]) -> Optional[str]:
    """Assemble a semicolon-delimited human-readable tag string for DB display."""
    if normalized is None:
        return None
    parts: list[str] = []
    if normalized.country:
        parts.append(normalized.country)
    if normalized.region:
        parts.extend(r for r in normalized.region if r)
    if normalized.grapes:
        parts.extend(normalized.grapes)
    if normalized.is_blend is True:
        parts.append("Blend")
    elif normalized.is_blend is False:
        parts.append("Single Varietal")
    if normalized.organic:
        parts.append("Organic")
    return "; ".join(parts) if parts else None


def organic_confirmed(
    web_context: Optional[str],
    normalized: Optional[ParsedTags],
) -> bool:
    """True only if explicit certification language appears in web_context or
    the model already flagged organic and we can corroborate from text.

    We intentionally do not trust the model's `organic` field alone — the DB
    column reflects whether explicit certification language was seen.
    """
    haystack_parts = []
    if web_context:
        haystack_parts.append(web_context)
    if normalized is not None:
        haystack_parts.append(json.dumps(asdict(normalized), default=str))
    haystack = " ".join(haystack_parts).lower()
    return any(phrase in haystack for phrase in ORGANIC_PHRASES)


def upsert_product(
    conn: sqlite3.Connection,
    product: Product,
    normalized: Optional[ParsedTags],
    web_context: Optional[str],
    tag_status: str,
) -> None:
    country = None
    region_json = None
    grapes_json = None
    is_blend = None
    confidence = None
    if normalized is not None:
        country = normalized.country
        region_json = json.dumps(list(normalized.region or []))
        grapes_json = json.dumps(list(normalized.grapes or []))
        if normalized.is_blend is True:
            is_blend = 1
        elif normalized.is_blend is False:
            is_blend = 0
        confidence = normalized.confidence

    organic = 1 if organic_confirmed(web_context, normalized) else 0
    tags_raw = build_tags_raw(normalized)

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
            product.id, product.name, product.sku, product.category,
            product.supply_price, product.retail_price,
            product.supplier, product.brand,
            country, region_json, grapes_json, is_blend, organic, confidence,
            web_context, tags_raw, tag_status,
        ),
    )


def upsert_sales(conn: sqlite3.Connection, product: Product) -> None:
    if not product.sku:
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
            product.sku, product.id,
            product.items_sold, product.margin_pct, product.sale_count,
            product.customer_count, product.avg_sale_value,
        ),
    )


def log_tag(
    conn: sqlite3.Connection,
    product_id: str,
    transcript: list[dict],
    ok: bool,
) -> None:
    try:
        payload = json.dumps(transcript, default=str)
    except Exception:
        payload = json.dumps([{"_error": "transcript serialization failed"}])
    conn.execute(
        "INSERT INTO tag_log (product_id, transcript, parsed_ok) VALUES (?,?,?)",
        (product_id, payload, 1 if ok else 0),
    )


# ---------------------------------------------------------------------------
# tag_status policy
# ---------------------------------------------------------------------------

def decide_tag_status(
    *,
    normalized: Optional[ParsedTags],
    confidence_threshold: int,
) -> str:
    """None → needs_review; confidence < threshold → needs_review; else auto."""
    if normalized is None:
        return "needs_review"
    conf = normalized.confidence
    if conf is None or conf < confidence_threshold:
        return "needs_review"
    return "auto"


# ---------------------------------------------------------------------------
# Batch summary
# ---------------------------------------------------------------------------

def _print_batch_summary(
    processed: int,
    auto: int,
    review: int,
    skipped: int,
    review_list: list[dict],
) -> None:
    print(f"\n--- Batch summary (last {processed} wines) ---")
    print(f"  Auto-tagged: {auto}  |  Needs review: {review}  |  Skipped: {skipped}")
    if review_list:
        print("  Needs-review wines:")
        for w in review_list:
            print(f"    {w['id']} — {w['name']} (conf={w['confidence']})")
    print("---")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fermentation: tag wine metadata via local LLM + MCP library.",
    )
    parser.add_argument(
        "--api-url",
        default=os.environ.get("FERMENTATION_API_URL", DEFAULT_API_URL),
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("FERMENTATION_MODEL", DEFAULT_MODEL),
    )
    parser.add_argument(
        "--confidence-threshold",
        type=int,
        default=int(os.environ.get(
            "FERMENTATION_CONFIDENCE_THRESHOLD", DEFAULT_CONFIDENCE_THRESHOLD,
        )),
    )
    parser.add_argument("--batch-size", type=int, default=0,
                        help="Pause for review every N wines (0 = no pausing)")
    parser.add_argument("--force", action="store_true",
                        help="Ignore run state and start from the beginning")
    parser.add_argument("--input", default=str(INPUT_CSV),
                        help="Path to combined.csv")
    parser.add_argument("--limit", type=int, default=0,
                        help="Process at most N wines (0 = all)")
    parser.add_argument(
        "--no-producer-gate",
        action="store_true",
        help="Disable the scorer's producer-absent hard gate (debugging aid).",
    )
    parser.add_argument(
        "--debug-output",
        action="store_true",
        help="Write per-stage JSON snapshots to fermentation/output/",
    )
    args = parser.parse_args()

    if args.no_producer_gate:
        print(
            "NOTE: --no-producer-gate set; producer-absent gating disabled.",
            file=sys.stderr,
        )

    if args.force:
        clear_run_state()
        print("--force: starting from scratch.")

    run_state = load_run_state()
    start_cursor = 0
    if run_state and not args.force:
        saved_batch = run_state.get("batch_size", 0)
        if args.batch_size and saved_batch != args.batch_size:
            ans = input(
                f"Warning: saved batch-size={saved_batch} differs from "
                f"--batch-size={args.batch_size}. Resume anyway? [y/N] "
            ).strip().lower()
            if ans not in ("y", "yes"):
                print("Aborted.")
                sys.exit(0)
        start_cursor = run_state.get("cursor", 0)
        last_id = run_state.get("last_committed_id", "?")
        print(f"Resuming from product {start_cursor + 1} (last committed: {last_id})")

    products = load_products(Path(args.input))
    total = len(products)
    print(f"Loaded {total} products from {args.input}")

    conn = open_db(DB_PATH)

    n_auto = n_review = n_skipped = 0
    batch_auto = batch_review = batch_skipped = 0
    batch_review_list: list[dict] = []

    effective_limit = args.limit if args.limit > 0 else total
    end_idx = min(total, start_cursor + effective_limit)

    with tagger.library_mcp_session() as mcp:
        for idx in range(start_cursor, end_idx):
            product = products[idx]
            pos = idx + 1

            if not is_eligible(conn, product):
                n_skipped += 1
                batch_skipped += 1
                print(f"[{pos}/{total}] SKIP (manual) — {product.name}")
                save_run_state(product.id, idx + 1, args.batch_size)
                conn.commit()
                continue

            print(f"[{pos}/{total}] {product.name}", end="", flush=True)

            # ----- searcher -----
            snippets = searcher.gather_snippets(product)
            debug_output.write_search_output(
                product, snippets, enabled=args.debug_output,
            )

            # ----- scorer -----
            web_context, scored = scorer.score_and_assemble(
                product, snippets, api_url=args.api_url, model=args.model,
                producer_gate=not args.no_producer_gate,
            )
            debug_output.write_scorer_output(
                product, scored, web_context, enabled=args.debug_output,
            )

            normalized: Optional[ParsedTags] = None
            if web_context is None:
                # Producer-absent hard exclusion (or no snippets at all):
                # skip the tagger entirely and route to needs_review.
                tag_status = "needs_review"
                print(" | no web context → needs_review", end="", flush=True)
                upsert_product(conn, product, None, None, tag_status)
                debug_output.write_final_output(
                    product, None, tag_status, enabled=args.debug_output,
                )
            else:
                print(f" | ctx: {web_context[:50]}...", end="", flush=True)
                # ----- tagger -----
                normalized, transcript = tagger.infer_tags(
                    product, web_context,
                    api_url=args.api_url, model=args.model,
                    mcp_session=mcp,
                )
                debug_output.write_tagger_output(
                    product, transcript,
                    enabled=args.debug_output,
                    success=normalized is not None,
                )
                log_tag(conn, product.id, transcript, ok=normalized is not None)
                tag_status = decide_tag_status(
                    normalized=normalized,
                    confidence_threshold=args.confidence_threshold,
                )
                upsert_product(conn, product, normalized, web_context, tag_status)
                debug_output.write_final_output(
                    product, normalized, tag_status, enabled=args.debug_output,
                )

            upsert_sales(conn, product)
            conn.commit()
            save_run_state(product.id, idx + 1, args.batch_size)

            if tag_status == "needs_review":
                n_review += 1
                batch_review += 1
                conf_str = str(normalized.confidence) if normalized and normalized.confidence is not None else "—"
                batch_review_list.append({
                    "id": product.id, "name": product.name, "confidence": conf_str,
                })
                print(f" → needs_review (conf={conf_str})")
            else:
                conf_str = str(normalized.confidence) if normalized and normalized.confidence is not None else "—"
                n_auto += 1
                batch_auto += 1
                print(f" → auto (conf={conf_str})")

            # Batch pause
            batch_pos = idx - start_cursor + 1
            if args.batch_size > 0 and batch_pos % args.batch_size == 0:
                _print_batch_summary(
                    batch_pos, batch_auto, batch_review, batch_skipped,
                    batch_review_list,
                )
                batch_auto = batch_review = batch_skipped = 0
                batch_review_list = []
                ans = input("Continue with next batch? [y/N] ").strip().lower()
                if ans not in ("y", "yes"):
                    print("Paused. Re-run the same command to resume.")
                    conn.close()
                    return

    clear_run_state()
    conn.close()
    processed = n_auto + n_review + n_skipped
    print("\n=== Done ===")
    print(f"  Processed   : {processed}")
    print(f"  Auto-tagged : {n_auto}")
    print(f"  Needs review: {n_review}")
    print(f"  Skipped     : {n_skipped}")
    print(f"  DB: {DB_PATH}")


if __name__ == "__main__":
    main()
