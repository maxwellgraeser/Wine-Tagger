# Wine Warehouse DDD Data Pipeline

A three-domain pipeline that takes raw Lightspeed exports, enriches them with AI-generated wine metadata, and produces a dashboard for review and re-upload.

```
┌─────────────┐       ┌─────────────┐       ┌────────────────┐
│  Ingestion  │──CSV──▶  Curation   │──DB───▶  Distribution  │
│  (Python)   │       │  (Python +  │       │  (React/Vite/  │
│             │       │   Gemma)    │       │   TypeScript)  │
└─────────────┘       └─────────────┘       └────────────────┘
```

## How to Run

Execute the three domains in order:

```sh
./ingestion/run.sh
./curation/run.sh
./distribution/run.sh   # starts the local dashboard
```

Each domain is self-contained. Data flows strictly downstream — no domain reaches back into an upstream domain's internals.

---

## Domain 1 — Ingestion

**Run:** `./ingestion/run.sh`

**What it does:** Reads the two raw `.xlsx` exports from Lightspeed, cleans and normalizes them, and writes a single merged CSV.

**Inputs** (place in `Sample Xlsx/`):
- `product-export.xlsx` — full product catalog (id, name, SKU, prices, supplier, tags, etc.)
- `inventory-report.xlsx` — sales stats per product (units sold, margin, customer count, etc.)

**Output:** `ingestion/output/combined.csv` — one row per wine with all product columns and sales stats merged via a case-insensitive full outer join on the product name.

**Key processing steps:**
1. Read both xlsx files with openpyxl.
2. Normalize column names (lowercase, underscores).
3. Drop always-empty variant/composite columns.
4. Full outer join on `name` — products with no sales data are included (sales columns left blank); inventory rows with no matching product are appended with only the sales columns filled.
5. Coerce numeric types, strip whitespace, validate UUIDs, handle nulls consistently.

**Tech:** Python 3.11+, openpyxl (or pandas), stdlib csv — no network access needed.

---

## Domain 2 — Curation

**Run:**

```sh
# Standard run (all wines, no pausing)
./curation/run.sh

# Pause for review after every 10 wines
./curation/run.sh --batch-size 10

# Use LM Studio instead of llama.cpp
./curation/run.sh --api-url http://localhost:1234/v1/chat/completions

# Lower the confidence threshold (accept more tags without manual review)
./curation/run.sh --confidence-threshold 60

# Ignore saved run state and start over from the beginning
./curation/run.sh --force

# Combine flags
./curation/run.sh --batch-size 20 --confidence-threshold 60 --api-url http://localhost:1234/v1
```

**What it does:** For each wine, looks it up on the web, then calls a local Gemma model to infer structured metadata (country, region, grapes, blend status, organic status). Writes everything to a SQLite database.

**Input:** `ingestion/output/combined.csv`

**Output:** `curation/output/wines.db` (SQLite)

### Web Lookup

For each wine the script queries DuckDuckGo using site-scoped queries against a curated priority list of sources (Jeb Dunnuck, James Suckling, Vinous, Robert Parker, Wine Enthusiast). It takes the first useful snippet (≤ 400 chars) and caches it in `curation/output/web_cache.json` keyed by product id so re-runs skip the network for already-looked-up wines.

- If no curated source returns a snippet, it falls back to an unscoped query.
- If nothing useful is found at all, `web_context` is set to null and the wine is flagged `needs_review`.
- A 0.5 s delay between requests keeps DDG happy; HTTP errors retry once then proceed with null context.

### LLM Inference

Uses a locally-running Gemma model (via **llama.cpp's `llama-server`** at `http://localhost:8080/v1/chat/completions`, or **LM Studio** at `http://localhost:1234/v1/chat/completions`). Pass `--api-url` or set the env var to switch runtimes.

The model receives the product name, category, brand, and web snippet and returns JSON:

```json
{
  "country": "France",
  "region": "Bordeaux",
  "grapes": ["Cabernet Sauvignon", "Merlot"],
  "is_blend": true,
  "organic": false,
  "confidence": 92
}
```

After parsing, `tags_raw` is assembled as a semicolon-separated string ready for Lightspeed — e.g. `France; Bordeaux; Cabernet Sauvignon; Merlot; Blend`.

### Confidence & Review Flags

- Rows with `confidence < 75` (default, adjustable via `--confidence-threshold` or `CURATION_CONFIDENCE_THRESHOLD`) are flagged `tag_status = 'needs_review'`.
- Private-label wines (no web result found) go through LLM inference but are always flagged `needs_review`.
- `organic = true` is only set when the web snippet or model response contains `"certified organic"`, `"biodynamic"`, or `"certified biodynamic"` — softer signals are ignored.
- Rows with `tag_status = 'manual'` are never overwritten on re-run.

### CLI Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--api-url` | llama.cpp (`http://localhost:8080/v1/chat/completions`) | LLM API base URL |
| `--confidence-threshold` | 75 | Minimum confidence to auto-accept tags |
| `--batch-size N` | 0 (all) | Pause for review after every N wines |
| `--force` | off | Ignore saved run state; restart from row 0 |

### Resumability

After each committed wine the script writes `curation/output/.run_state.json`. If the run is interrupted (user declined to continue a batch, or the process was killed), re-running the same command resumes from where it left off. `--force` discards the state file and starts fresh.

### SQLite Schema

```
products   — one row per wine; holds all catalog fields plus LLM-generated tags
sales      — sales stats per SKU, joined to products via product_id
tag_log    — raw LLM prompt/response pairs for every inference (for auditing)
```

**Tech:** Python 3.11+, sqlite3, requests/httpx — no paid APIs or API keys required.

---

## Domain 3 — Distribution

**Run:** `./distribution/run.sh`

**What it does:** A local web dashboard for browsing, editing, and exporting the curated wine data.

**Input:** `curation/output/wines.db`

**Output:** Lightspeed-compatible `.xlsx` with columns `id`, `name`, `tags` (semicolon-separated).

### Dashboard Features

- **Wine table** — sortable, filterable (by category, country, region, tag_status), searchable by name.
- **Inline tag editing** — edit country, region, and grapes directly in the table; saving flips `tag_status` to `reviewed`.
- **Sales stats** — per-wine details plus summary stats (top sellers, highest margin, most customers).
- **Export** — one-click `.xlsx` download containing only `id`, `name`, and `tags`.

### API Endpoints

```
GET    /api/wines              list wines (?search, ?category, ?status)
GET    /api/wines/:id          single wine + sales stats
PATCH  /api/wines/:id          update tags (sets tag_status = 'reviewed')
GET    /api/wines/export       download Lightspeed xlsx
GET    /api/stats/summary      aggregate sales stats
```

**Tech:** Node.js 18+, Vite + React + TypeScript, Express/Fastify, better-sqlite3, exceljs/SheetJS, Tailwind CSS.

---

## Folder Structure

```
Wine Warehouse DDD/
├── README.md
├── PLAN.md
├── ingestion/
│   ├── PLAN.md
│   ├── run.sh
│   └── output/
│       └── combined.csv        (generated)
├── curation/
│   ├── PLAN.md
│   ├── run.sh
│   └── output/
│       ├── wines.db            (generated)
│       ├── web_cache.json      (generated)
│       └── .run_state.json     (generated, deleted on clean completion)
├── distribution/
│   ├── PLAN.md
│   └── run.sh
└── Sample Xlsx/
    ├── product-export.xlsx
    └── inventory-report (...).xlsx
```
