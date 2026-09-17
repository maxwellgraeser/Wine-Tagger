# Ingestion Domain

> **Status: ✅ Implemented** (`ingestion/ingest.py`, run from Cellar → Ingest or
> `python ingestion/ingest.py`). Rewritten 2026-09-16: one CSV in, filters
> decide what is a wine, excluded rows are kept for review.

## Purpose

Take the Lightspeed **product export CSV** (the whole catalogue: wine, beer,
sake, accessories, gift cards…), keep only the rows that are wines worth
tagging, and write them as `combined.csv` for fermentation.

The problem it solves: since the POS switch, new products are added with **no
category**. Legacy items still carry one. So the filters green-light what we
know, then sift the uncategorized rows for beer and accessories.

## Input

One file, dropped into the Cellar Ingest panel (drag & drop or browse) or
passed with `--input`. Only Lightspeed's product export **CSV** is accepted
(Lightspeed → Products → Export → CSV). The header row is validated on
upload; anything else (an inventory report, an `.xlsx`) is rejected with the
reason.

Uploads are stored in `ingestion/uploads/` (git-ignored) and stay selectable
until deleted. Without `--input` the CLI uses the newest upload, else the
newest `*.csv` in `Sample Xlsx/`.

Columns of the export (32), after normalisation (`lowercase_with_underscores`):

| Column | Notes |
|---|---|
| `id` | Lightspeed UUID — primary key, preserved for re-upload. Rows with an invalid id are skipped and counted. |
| `handle`, `sku`, `name`, `description` | |
| `product_category` | One of 13 store categories, or **empty** for post-switch products |
| `tags` | Empty — fermentation fills it |
| `supply_price`, `retail_price` | Coerced to float |
| `brand_name`, `supplier_name`, `supplier_code` | `supplier_name` drives the vendor filter |
| `active`, `track_inventory`, `outlet_tax_*` | |
| `inventory_*`, `reorder_point_*`, `reorder_quantity_*`, `min_quantity_*`, `max_quantity_*`, `items_on_special_order_*` | Outlet columns; `inventory_*` coerced to float |
| `composite_*`, `variant_option_*`, `account_code*` | **Dropped** (always empty for single-variant wines) |

### The test set

`ingestion/fixtures/test-wines.csv` holds the 24 wines the pipeline was
developed on, in `combined.csv` layout **with** the sales columns from the old
inventory-report join. It shows up in the Ingest panel as *Test set (24
wines)* and always passes the filters. Use it for a quick fermentation run.

## Filters — `ingestion/filters.toml`

All rules live in one TOML file so lists can grow without touching code.
Rows are decided in this order (`ingestion/filters.py`):

| # | Filter | Applies to | Rule |
|---|---|---|---|
| 1 | `categories.whitelist` | every row | Category on the whitelist (Red, White, Rose, Sparkling, Orange/Amber) → **kept**, no further checks. Any *other* non-empty category (Beer, Dessert, Sherry, Aperitif, Cider, Accessories, Food, Tasting) → excluded. |
| 2 | `vendors.blacklist` | uncategorized rows | Supplier equals an entry or starts with it as whole words (`Cavalier` ⇒ `Cavalier Distributing Florida`; `True` ⇏ `Truett-Hurst`) → excluded. Cavalier, Progressive, North Fl Sales, Champion, True, Lottie Dottie, Warehouse. |
| 3a | `names.exclude` | uncategorized rows | Exact name match → excluded (one-offs no keyword catches safely, e.g. `Kai Lychee 4pk`). |
| 3b | `keywords.<group>` | uncategorized rows | Whole-word, accent-insensitive match of any term in any group → excluded. Groups: beer, cider, sake, fortified, fortified_producers, dessert, spirits, accessories, services. |

What survives is a wine: either green-lit by category or **uncategorized**
(fermentation infers Red / White / Rose / Sparkling for those).

### Is the keyword filter redundant?

No, but it is small. On the 2026-09-16 export (3,485 rows) filters 1 and 2
leave 330 uncategorized rows from non-blacklisted vendors; 16 of them are not
wine and only the name gives it away: vermouth ×2, tawny ×2, Marsala ×2,
Amontillado, white Porto, Banyuls, Beaumes de Venise, Muscat, Tokaji Aszú,
a Boulevard Tank 7 beer, Kai sake cans ×2, and a "Delivery" line item.

Keyword calibration was done against the *categorized* rows of the same
export (which category does each term appear under?), and the store's own
conventions were followed:

- sake is filed under Beer and mostly named `Junmai` / `Ginjo` / `Nigori` → those are sake terms
- Muscat and Moscato are filed under Dessert → excluded
- Spätlese / Auslese / Kabinett are filed under White → **not** excluded
- spritz and Bellini are filed under Sparkling → **not** excluded
- **Tokaji**: Tokaji *Aszú* is a botrytised sweet wine (≥120 g/l residual
  sugar) → `aszu` is excluded; the Tokaj region also makes dry Furmint, so
  `tokaji` / `furmint` are **not** keywords.
- word boundaries matter: `port` ≠ Portugal, `gin` ≠ Ginestet, `rum` ≠ Rumor,
  `ale` ≠ Alesia, Cassis (appellation) ≠ `creme cassis`.

## Output — `ingestion/output/`

| File | Contents |
|---|---|
| `combined.csv` | Kept rows, product columns + `ingest_pass` (`category` \| `uncategorized`). Sorted by name. |
| `excluded.csv` | Every excluded row, product columns + `excluded_by` (`category` \| `vendor` \| `name` \| `keyword`) + `excluded_reason`. |
| `summary.json` | Input file info, kept/excluded totals, breakdown per filter and per matched value. The Ingest panel renders this. |

### Output contract (what fermentation reads)

`fermentation/ferment.py::load_products` reads `id`, `name`, `sku`,
`brand_name`, `product_category`, `supply_price`, `retail_price`,
`supplier_name`, plus the optional sales columns (`items_sold`, `margin_pct`,
`sale_count`, `customer_count`, `avg_sale_value`) which are empty for real
exports and present only in the test set. Unknown columns are ignored.

## Cellar API

```
POST   /api/ingest/upload            multipart file → stored upload (header validated)
GET    /api/ingest/uploads           uploads (newest first) + the test set
DELETE /api/ingest/uploads/{name}
POST   /api/ingest/run               {"input": "<upload name>" | "test-wines"} → job
GET    /api/ingestion/summary        summary.json
GET    /api/ingestion/excluded       excluded.csv as JSON
GET    /api/ingestion/rows?limit=N   combined.csv as JSON
GET    /api/ingestion/filters        parsed filters.toml
```

`GET /api/status` → `ingestion: { uploads, csv, summary }`.

## Tech

Python 3.11+ (`tomllib`), stdlib `csv`. No network. Tests:
`pytest ingestion/tests` (filter rules incl. the Portugal/port and
Tokaji cases, an end-to-end run, and the fixture).

## Not done / open

- The inventory-report join (sales stats) is gone. Sales columns still exist
  in the wine store and the Distribute table; they are empty for real runs.
- Fermentation's `CATEGORY_OPTIONS` is Red/White/Rose/Sparkling — an
  uncategorized orange wine will be inferred as one of those, never
  Orange/Amber.
- Rows from blacklisted vendors that *do* carry a whitelisted category
  (e.g. 19 "Warehouse" wines) are kept — the category wins.
