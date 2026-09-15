# Ingestion Domain

> **Status: ✅ Implemented** (`ingestion/ingest.py`, run via `ingestion/run.sh`).

## Purpose

Read raw Lightspeed `.xlsx` exports, clean and normalize the data, and output structured CSV files that downstream domains can consume without needing xlsx tooling.

## Inputs

Two files from `Sample Xlsx/`:

### product-export.xlsx (Product Catalog)

Key columns (29 total):

| Column | Description | Notes |
|--------|-------------|-------|
| `id` | Lightspeed UUID | Primary key, must be preserved for re-upload |
| `handle` | URL slug | e.g. `annabella-pinot-noir` |
| `sku` | Barcode / UPC | |
| `name` | Display name | e.g. `Annabella Pinot Noir` |
| `description` | Product description | Often empty |
| `product_category` | Lightspeed category | e.g. `Red`, `Sparkling` |
| `tags` | Existing tags | Currently empty -- this is what fermentation will fill |
| `supply_price` | Cost price | |
| `retail_price` | Selling price | |
| `brand_name` | Brand | |
| `supplier_name` | Distributor | |
| `active` | Active status | |
| `inventory_*` | Stock count | Outlet-specific column |
| Variant columns | Multi-variant support | Mostly empty for wines |

### inventory-report.xlsx (Sales Stats)

Key columns (17 total):

| Column | Description | Notes |
|--------|-------------|-------|
| `Product` | Wine name | Join key -- matches `name` in product export |
| `SKU` | Barcode | Secondary join key |
| `Supplier Code` | | Often empty |
| `Brand` | | Often empty |
| `Supplier` | Distributor name | e.g. `Breakthru`, `RNDC` |
| `Category` | Same as `product_category` | e.g. `Red`, `Sparkling` |
| `Tag` | Existing tags | Currently empty |
| `Closing Inventory` | Stock at end of period | |
| `Items Sold per Day` | Daily run rate | |
| `Items Sold` | Total units sold | |
| `Days Cover` | Stock / daily rate | |
| `Sell-through Rate` | % of stock sold | |
| `Sale Count` | Number of transactions | |
| `Margin (%)` | Profit margin | |
| `Customer Count` | Unique customers | |
| `Avg. Items per Sale` | Basket size | |
| `Avg. Sale Value` | Basket value | |

## Processing Steps

1. **Read** both xlsx files using openpyxl.
2. **Normalize column names** -- lowercase, underscores, strip whitespace.
3. **Drop variant/composite columns** that are always empty for single-variant wines (`composite_*`, `variant_option_*`, `account_code*`).
4. **Join** the two datasets on `name` (case-insensitive, inner join). Rows not present in both sources are dropped and logged as warnings.
5. **Clean**:
   - Strip whitespace from string fields.
   - Coerce numeric columns to proper types (float for prices/rates, int for counts).
   - Handle missing/empty values consistently (empty string for text, None for numbers).
   - Validate UUIDs in the `id` column; skip rows with invalid UUIDs.
6. **Output** a single combined CSV to `ingestion/output/`:
   - `combined.csv` -- all product columns plus sales stats merged into one row per wine.

## Output Contract

Downstream (**fermentation**) reads a single file:
`ingestion/output/combined.csv`

**Product columns (from product-export.xlsx):**
- `id` (string, Lightspeed UUID)
- `handle` (string, URL slug)
- `sku` (string)
- `name` (string)
- `description` (string)
- `product_category` (string)
- `tags` (string, empty -- filled by fermentation)
- `supply_price` (float)
- `retail_price` (float)
- `brand_name` (string)
- `supplier_name` (string)
- `supplier_code` (string)
- `active` (string)
- `track_inventory` (string)
- `outlet_tax_atlantic_beach_wine_warehouse` (string)
- `inventory_atlantic_beach_wine_warehouse` (float)
- `reorder_point_atlantic_beach_wine_warehouse` (string)
- `restock_level_atlantic_beach_wine_warehouse` (string)

**Sales columns (from inventory-report.xlsx, merged inline):**
- `closing_inventory` (float)
- `items_sold_per_day` (float)
- `items_sold` (int)
- `days_cover` (float)
- `sell_through_rate` (float)
- `sale_count` (int)
- `margin_pct` (float)
- `customer_count` (int)
- `avg_items_per_sale` (float)
- `avg_sale_value` (float)

## Tech

- Python 3.11+
- openpyxl or pandas for reading xlsx
- Standard library csv for writing output
- No external services or network access needed

## Open Questions

- Are there edge cases in product names that would cause join failures (e.g. trailing size info like "750ml")?
- ~~Should unmatched inventory rows (no product UUID) be included in the combined output at all?~~ Resolved: inner join, both-sides-only rows are dropped.
