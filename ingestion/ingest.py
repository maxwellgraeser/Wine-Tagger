"""
Ingestion domain: reads raw Lightspeed .xlsx exports, normalizes, joins, and
writes clean CSV files to ingestion/output/.
"""

import csv
import glob
import logging
import os
import re
import sys
import uuid
from pathlib import Path

import openpyxl

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

SAMPLE_DIR = Path(__file__).parent.parent / "Sample Xlsx"
OUTPUT_DIR = Path(__file__).parent / "output"

# Columns to drop from product export (always empty for single-variant wines)
PRODUCT_DROP = {
    "composite_name",
    "composite_sku",
    "composite_quantity",
    "variant_option_one_name",
    "variant_option_one_value",
    "variant_option_two_name",
    "variant_option_two_value",
    "variant_option_three_name",
    "variant_option_three_value",
    "account_code",
    "account_code_purchase",
}

# Numeric columns in product export (stored as strings in xlsx)
PRODUCT_NUMERIC = {"supply_price", "retail_price", "inventory_atlantic_beach_wine_warehouse"}

# Inventory column name normalisation map (normalized header -> output name).
# Keys are what norm_col() produces from the raw header.
INVENTORY_RENAME = {
    "product": "name",
    "margin": "margin_pct",          # "Margin (%)" normalises to "margin"
    "avg_items_per_sale": "avg_items_per_sale",  # "Avg. Items per Sale"
    "avg_sale_value": "avg_sale_value",           # "Avg. Sale Value"
    "sell_through_rate": "sell_through_rate",     # "Sell-through Rate"
}

# Columns to store as float
INVENTORY_FLOAT = {
    "closing_inventory", "items_sold_per_day", "days_cover",
    "sell_through_rate", "margin_pct", "avg_items_per_sale", "avg_sale_value",
}

# Columns to store as int
INVENTORY_INT = {"items_sold", "sale_count", "customer_count"}


def norm_col(name: str) -> str:
    """Lowercase, replace spaces and special chars with underscores."""
    if name is None:
        return ""
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")


def read_xlsx(path: Path) -> tuple[list[str], list[list]]:
    """Return (headers, rows) from the active sheet."""
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    if ws is None:
        raise ValueError("No active sheet in the workbook")
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    headers = [str(h) if h is not None else "" for h in rows[0]]
    data = [list(r) for r in rows[1:]]
    return headers, data


def coerce_numeric(val):
    """Convert a value to float, returning None on failure."""
    if val is None or val == "":
        return None
    try:
        return float(str(val).strip().replace(",", ""))
    except ValueError:
        return None


def coerce_int(val):
    n = coerce_numeric(val)
    return int(round(n)) if n is not None else None


def is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


def clean_str(val) -> str:
    if val is None:
        return ""
    return str(val).strip()


def load_products() -> tuple[list[str], list[dict]]:
    path = SAMPLE_DIR / "product-export.xlsx"
    raw_headers, raw_rows = read_xlsx(path)
    headers = [norm_col(h) for h in raw_headers]

    out_headers = [h for h in headers if h not in PRODUCT_DROP]

    records = []
    for i, row in enumerate(raw_rows, start=2):
        rec = dict(zip(headers, row))

        # Validate UUID
        pid = clean_str(rec.get("id", ""))
        if not is_valid_uuid(pid):
            log.warning("Row %d: invalid UUID %r — skipping", i, pid)
            continue

        # Build cleaned record, dropping unwanted columns
        cleaned = {}
        for col in out_headers:
            val = rec.get(col)
            if col in PRODUCT_NUMERIC:
                cleaned[col] = coerce_numeric(val)
            elif col == "active" or col == "track_inventory":
                cleaned[col] = clean_str(val)
            else:
                cleaned[col] = clean_str(val)

        records.append(cleaned)

    log.info("Products loaded: %d rows, %d columns", len(records), len(out_headers))
    return out_headers, records


def load_inventory() -> tuple[list[str], list[dict]]:
    pattern = str(SAMPLE_DIR / "inventory*.xlsx")
    matches = glob.glob(pattern)
    if not matches:
        log.error("No inventory xlsx found matching %s", pattern)
        sys.exit(1)
    path = Path(matches[0])
    log.info("Reading inventory from %s", path.name)

    raw_headers, raw_rows = read_xlsx(path)
    norm_headers = [norm_col(h) for h in raw_headers]

    # Rename to canonical output names
    out_headers = [INVENTORY_RENAME.get(h, h) for h in norm_headers]

    records = []
    for row in raw_rows:
        rec = dict(zip(out_headers, row))
        cleaned = {}
        for col in out_headers:
            val = rec.get(col)
            if col in INVENTORY_INT:
                cleaned[col] = coerce_int(val)
            elif col in INVENTORY_FLOAT:
                cleaned[col] = coerce_numeric(val)
            else:
                cleaned[col] = clean_str(val)
        # Skip blank rows (no product name)
        if not cleaned.get("name"):
            continue
        records.append(cleaned)

    log.info("Inventory loaded: %d rows", len(records))
    return out_headers, records


SALES_ONLY_COLS = [
    "closing_inventory", "items_sold_per_day", "items_sold", "days_cover",
    "sell_through_rate", "sale_count", "margin_pct", "customer_count",
    "avg_items_per_sale", "avg_sale_value",
]


def merge_datasets(
    prod_headers: list[str],
    products: list[dict],
    inventory: list[dict],
) -> tuple[list[str], list[dict]]:
    """
    Inner join of products and inventory on name (case-insensitive).
    Rows not present in both sources are dropped.
    Returns (headers, rows) for the combined CSV.
    """
    combined_headers = prod_headers + SALES_ONLY_COLS

    inv_by_name: dict[str, dict] = {
        row["name"].strip().lower(): row for row in inventory if row.get("name")
    }

    rows: list[dict] = []
    products_only = 0

    for prod in products:
        key = prod.get("name", "").strip().lower()
        inv = inv_by_name.get(key)
        if inv is None:
            log.warning("Dropping product with no inventory match: %r", prod.get("name"))
            products_only += 1
            continue
        row = {col: prod.get(col, "") for col in prod_headers}
        for col in SALES_ONLY_COLS:
            row[col] = inv.get(col, "")
        rows.append(row)

    matched_names = {r["name"].strip().lower() for r in rows}
    inventory_only = sum(
        1 for inv in inventory if inv.get("name", "").strip().lower() not in matched_names
    )
    for inv in inventory:
        key = inv.get("name", "").strip().lower()
        if key not in matched_names:
            log.warning("Dropping inventory row with no product match: %r", inv.get("name"))

    log.info(
        "Merge complete: %d matched, %d products-only dropped, %d inventory-only dropped",
        len(rows),
        products_only,
        inventory_only,
    )
    return combined_headers, rows


def prompt_missing_categories(rows: list[dict]) -> None:
    """Interactively prompt the user to fill in any missing product_category values."""
    missing = [r for r in rows if not r.get("product_category")]
    if not missing:
        return
    print(f"\n{len(missing)} wine(s) have no category. Please assign one for each.\n")
    for row in missing:
        while True:
            cat = input(f"  Category for '{row['name']}': ").strip()
            if cat:
                row["product_category"] = cat
                break
            print("  Category cannot be empty — try again.")


def write_csv(path: Path, headers: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    log.info("Wrote %d rows to %s", len(rows), path)


def main() -> None:
    prod_headers, products = load_products()
    _inv_headers, inventory = load_inventory()
    combined_headers, combined = merge_datasets(prod_headers, products, inventory)

    prompt_missing_categories(combined)

    write_csv(OUTPUT_DIR / "combined.csv", combined_headers, combined)
    log.info("Ingestion complete.")


if __name__ == "__main__":
    main()
