"""
Ingestion domain: reads one Lightspeed product-export CSV, normalizes it, runs
the filters in ingestion/filters.toml, and writes to ingestion/output/:

    combined.csv    the wines fermentation should tag
    excluded.csv    every row that was filtered out, with excluded_by / excluded_reason
    summary.json    counts per filter and per matched value, for the dashboard

Usage:
    python ingestion/ingest.py                      # newest CSV in ingestion/uploads/ (else Sample Xlsx/)
    python ingestion/ingest.py --input path.csv     # a specific export
    python ingestion/ingest.py --input ingestion/fixtures/test-wines.csv   # the 24 test wines
    python ingestion/ingest.py --events-json        # one JSON event per line (the Cellar web app)
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.filters import FILTERS_PATH, STAGES, Filters  # noqa: E402

UPLOADS_DIR = HERE / "uploads"
FIXTURES_DIR = HERE / "fixtures"
OUTPUT_DIR = HERE / "output"
SAMPLE_DIR = PROJECT_ROOT / "Sample Xlsx"

COMBINED_CSV = OUTPUT_DIR / "combined.csv"
EXCLUDED_CSV = OUTPUT_DIR / "excluded.csv"
SUMMARY_JSON = OUTPUT_DIR / "summary.json"

# Columns every accepted export must have (after header normalisation).
REQUIRED_COLUMNS = ("id", "name", "product_category", "supplier_name")

# Columns dropped from the export (always empty for single-variant wines).
PRODUCT_DROP = {
    "composite_name", "composite_sku", "composite_quantity",
    "variant_option_one_name", "variant_option_one_value",
    "variant_option_two_name", "variant_option_two_value",
    "variant_option_three_name", "variant_option_three_value",
    "account_code", "account_code_purchase",
}

# Numeric columns (stored as text in the export). Any inventory_* column counts.
PRODUCT_NUMERIC = {"supply_price", "retail_price"}

# Added to every output row: how the row was decided.
PASS_COLUMN = "ingest_pass"          # combined.csv: category | uncategorized
EXCLUDED_BY_COLUMN = "excluded_by"   # excluded.csv: category | vendor | name | keyword
EXCLUDED_REASON_COLUMN = "excluded_reason"


# ---------------------------------------------------------------------------
# Output: plain log lines, or JSON events for the Cellar job runner
# ---------------------------------------------------------------------------

class Emitter:
    def __init__(self, json_lines: bool) -> None:
        self.json_lines = json_lines

    def __call__(self, type_: str, message: str, **fields) -> None:
        if self.json_lines:
            print(json.dumps({"type": type_, "message": message, **fields}), flush=True)
        else:
            print(f"{type_.upper():8} {message}", flush=True)


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------

def norm_col(name: str | None) -> str:
    """Lowercase, replace spaces and special chars with underscores."""
    if name is None:
        return ""
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")


def coerce_numeric(val):
    if val is None or str(val).strip() == "":
        return None
    try:
        return float(str(val).strip().replace(",", ""))
    except ValueError:
        return None


def is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


def clean_str(val) -> str:
    return "" if val is None else str(val).strip()


class InputError(Exception):
    pass


def validate_headers(raw_headers: list[str]) -> list[str]:
    """Normalise headers and check the required columns exist. Returns the
    normalised header list. Raises InputError with a readable message."""
    headers = [norm_col(h) for h in raw_headers]
    missing = [c for c in REQUIRED_COLUMNS if c not in headers]
    if missing:
        raise InputError(
            "not a Lightspeed product export: missing column(s) "
            + ", ".join(missing)
            + f" (found: {', '.join(h for h in headers if h)[:200]})"
        )
    return headers


def read_export(path: Path) -> tuple[list[str], list[dict]]:
    """Read a product-export CSV. Returns (output headers, raw records keyed
    by normalised header). Only `.csv` is accepted."""
    if path.suffix.lower() != ".csv":
        raise InputError(f"only .csv product exports are accepted, got {path.name}")
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        try:
            raw_headers = next(reader)
        except StopIteration:
            raise InputError(f"{path.name} is empty") from None
        headers = validate_headers(raw_headers)
        records = [dict(zip(headers, row)) for row in reader if any(c.strip() for c in row)]
    out_headers = [h for h in headers if h and h not in PRODUCT_DROP]
    return out_headers, records


def clean_record(rec: dict, out_headers: list[str]) -> dict:
    cleaned = {}
    for col in out_headers:
        val = rec.get(col)
        if col in PRODUCT_NUMERIC or col.startswith("inventory_"):
            cleaned[col] = coerce_numeric(val)
        else:
            cleaned[col] = clean_str(val)
    return cleaned


# ---------------------------------------------------------------------------
# Input discovery
# ---------------------------------------------------------------------------

def newest_csv(*dirs: Path) -> Path | None:
    candidates = [p for d in dirs if d.exists() for p in d.glob("*.csv")]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def default_input() -> Path | None:
    return newest_csv(UPLOADS_DIR) or newest_csv(SAMPLE_DIR)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def write_csv(path: Path, headers: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)


def run(input_path: Path, filters_path: Path = FILTERS_PATH, output_dir: Path = OUTPUT_DIR,
        emit: Emitter | None = None) -> dict:
    emit = emit or Emitter(False)
    filters = Filters.load(filters_path)
    emit("info", f"Filters: {filters_path} — {len(filters.category_whitelist)} whitelisted categories, "
                 f"{len(filters.vendor_blacklist)} blacklisted vendors, "
                 f"{sum(len(v) for v in filters.keywords.values())} keywords in {len(filters.keywords)} groups")

    emit("info", f"Reading {input_path}")
    out_headers, records = read_export(input_path)
    emit("info", f"{len(records)} rows, {len(out_headers)} columns kept", rows=len(records))

    kept: list[dict] = []
    excluded: list[dict] = []
    invalid = 0
    kept_by = Counter()                       # category | uncategorized
    kept_categories: Counter = Counter()      # Red: n, ...
    excluded_by: Counter = Counter()          # category | vendor | name | keyword
    breakdown: dict[str, Counter] = {s: Counter() for s in STAGES}
    keyword_groups: Counter = Counter()

    total = len(records)
    for i, rec in enumerate(records, start=1):
        pid = clean_str(rec.get("id"))
        if not is_valid_uuid(pid):
            invalid += 1
            emit("log", f"row {i + 1}: invalid id {pid!r} — skipped")
            continue
        row = clean_record(rec, out_headers)
        d = filters.decide_row(row)
        if d.keep:
            row[PASS_COLUMN] = d.stage
            kept.append(row)
            kept_by[d.stage] += 1
            if d.stage == "category":
                kept_categories[d.match] += 1
        else:
            row[EXCLUDED_BY_COLUMN] = d.stage
            row[EXCLUDED_REASON_COLUMN] = d.reason
            excluded.append(row)
            excluded_by[d.stage] += 1
            breakdown[d.stage][d.match] += 1
            if d.stage == "keyword":
                keyword_groups[d.group] += 1
        if i % 500 == 0 or i == total:
            emit("progress", f"{i}/{total} rows — {len(kept)} kept, {len(excluded)} excluded",
                 index=i, total=total, kept=len(kept), excluded=len(excluded))

    kept.sort(key=lambda r: r.get("name", "").casefold())
    excluded.sort(key=lambda r: (STAGES.index(r[EXCLUDED_BY_COLUMN]), r.get("name", "").casefold()))

    write_csv(output_dir / "combined.csv", out_headers + [PASS_COLUMN], kept)
    write_csv(output_dir / "excluded.csv", out_headers + [EXCLUDED_BY_COLUMN, EXCLUDED_REASON_COLUMN], excluded)

    st = input_path.stat()
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input": {
            "path": str(input_path), "name": input_path.name, "size": st.st_size,
            "mtime": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(timespec="seconds"),
            "rows": total, "invalid_rows": invalid,
        },
        "filters_path": str(filters_path),
        "kept": {
            "total": len(kept),
            "by_category": kept_by["category"],
            "uncategorized": kept_by["uncategorized"],
            "categories": dict(kept_categories.most_common()),
        },
        "excluded": {
            "total": len(excluded),
            "by": {s: excluded_by[s] for s in STAGES},
            "breakdown": {s: dict(breakdown[s].most_common()) for s in STAGES},
            "keyword_groups": dict(keyword_groups.most_common()),
        },
        "output": {
            "combined": str(output_dir / "combined.csv"),
            "excluded": str(output_dir / "excluded.csv"),
        },
    }
    with open(output_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    emit("info", f"Kept {len(kept)} wines ({kept_by['category']} by category, "
                 f"{kept_by['uncategorized']} uncategorized); excluded {len(excluded)} "
                 f"({', '.join(f'{s} {excluded_by[s]}' for s in STAGES)}); {invalid} invalid ids skipped")
    emit("done", f"Wrote {output_dir / 'combined.csv'} and {output_dir / 'excluded.csv'}", summary=summary)
    return summary


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Ingestion: Lightspeed product export CSV → combined.csv")
    p.add_argument("--input", default=None,
                   help="Product export CSV (default: newest in ingestion/uploads/, else Sample Xlsx/)")
    p.add_argument("--filters", default=str(FILTERS_PATH), help="Filters TOML (default: ingestion/filters.toml)")
    p.add_argument("--output-dir", default=str(OUTPUT_DIR))
    p.add_argument("--events-json", action="store_true",
                   help="Print one JSON event per line on stdout (for the Cellar web app).")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    emit = Emitter(args.events_json)
    input_path = Path(args.input) if args.input else default_input()
    if input_path is None:
        emit("error", "no input CSV: upload one in Cellar or pass --input")
        return 2
    if not input_path.exists():
        emit("error", f"input not found: {input_path}")
        return 2
    try:
        run(input_path, Path(args.filters), Path(args.output_dir), emit)
    except InputError as e:
        emit("error", str(e))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
