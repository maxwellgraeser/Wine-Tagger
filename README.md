# Wine Warehouse DDD Data Pipeline

A domain-driven pipeline that takes raw Lightspeed exports, enriches them with
AI-generated wine metadata, and produces a database for review and re-upload.

```
  ┌─────────────┐      ┌──────────────────┐      ┌────────────────┐
  │  Ingestion  │─CSV─▶│   Fermentation   │─DB──▶│  Distribution  │
  │  (Python)   │      │ (Python + local  │      │  (React/Vite/  │
  │             │      │  LLM + MCP lib)  │      │   TypeScript)  │
  └─────────────┘      └──────────────────┘      └────────────────┘
        done                  active                 not built
```

> `fermentation/` drives a local LLM through a self-built **MCP wine
> library** to tag wines. `distribution/` is still only a plan.
>
> See `Tree.html` (repo root) for a visual component map and a
> severity-ordered list of known issues.

## Status at a glance

| Domain | State | Entry point | In → Out |
|---|---|---|---|
| `ingestion/` | ✅ Implemented | `./ingestion/run.sh` | 2× `.xlsx` → `combined.csv` |
| `fermentation/` | 🟧 Active build | `python -m fermentation.ferment` | `combined.csv` → `wines.db` |
| `distribution/` | ⬜ Not built | — | `wines.db` → Lightspeed `.xlsx` |

Each domain is self-contained. Data flows strictly downstream — no domain
reaches back into an upstream domain's internals; the contract between domains
is their output format (`combined.csv`, then `wines.db`).

## How to Run

```sh
# 1. Ingestion — xlsx → CSV
./ingestion/run.sh

# 2. Fermentation — starts llama-server on :8080 if it isn't already up
#    (default ./gemma3n.sh), waits for /health, then runs the module.
#    Flags pass through to ferment.
./ferment.sh --force --limit 3
LLAMA_SCRIPT=./qwen25-7b.sh ./ferment.sh   # use a different model

# 3. Distribution — not built yet
```

> `ferment.sh` leaves a server it started running, so later runs skip the model
> load. To stop it, run `kill "$(cat .llama-server.pid)"`. To run the module
> without the wrapper, use `python -m fermentation.ferment` from the repo root.

---

## Domain 1 — Ingestion

**Run:** `./ingestion/run.sh`

**What it does:** Reads the two raw `.xlsx` exports from Lightspeed, cleans and
normalizes them, and writes a single merged CSV.

**Inputs** (place in `Sample Xlsx/`):
- `product-export.xlsx` — full product catalog (id, name, SKU, prices, supplier, tags, etc.)
- `inventory-report.xlsx` — sales stats per product (units sold, margin, customer count, etc.)

**Output:** `ingestion/output/combined.csv` — one row per wine with all product
columns and sales stats merged via a case-insensitive **inner join** on the
product name. Rows present in only one source are dropped and logged as
warnings.

**Key processing steps:**
1. Read both xlsx files with openpyxl.
2. Normalize column names (lowercase, underscores).
3. Drop always-empty variant/composite columns.
4. Inner join on `name` — products and inventory rows must match on both sides;
   unmatched rows are dropped and counted.
5. Coerce numeric types, strip whitespace, validate UUIDs, handle nulls consistently.

**Tech:** Python 3.11+, openpyxl, stdlib csv — no network access needed.

See `ingestion/PLAN.md` for the full column contract.

---

## Domain 2 — Fermentation

**Run:** `python -m fermentation.ferment [flags]`

**What it does:** For each wine, gathers web snippets, uses a local LLM to score
their relevance, then drives a second LLM through a **tool-call loop against the
`library_mcp` server** to infer and *canonicalize* structured metadata
(country, region(s), grapes, blend status, organic status, confidence). Writes
everything to a fresh SQLite database.

**Input:** `ingestion/output/combined.csv`
**Output:** `fermentation/wines.db` (SQLite)

### Architecture

A controller (`ferment.py`) orchestrates three independent modules — they never
import each other; config (model, api_url) is owned by the controller and
passed down:

- **`searcher.py`** — owns the network for snippets. DuckDuckGo queries (UPC +
  per-source + fallback), cross-query URL dedupe, boilerplate strip, price-only
  filter. → `list[Snippet]`.
- **`scorer.py`** — one LLM call scores each snippet 0–100 for product match. A
  **producer-absent hard gate** drops snippets that don't mention the producer
  name (a hard exclusion, not a confidence cap). Top-N survivors are assembled
  into `web_context` — or `None`, in which case the wine routes straight to
  `needs_review` and the tagger is skipped.
- **`tagger.py`** — drives the MCP tool-call loop. The model browses canonical
  countries/regions/grapes via `lookup_*`/`list_*`, then commits via
  `submit_tags`. `submit_tags` **is the canonicalization gate** — whatever it
  accepts is what `ferment.py` writes; there is no second normalization pass.

### The `library_mcp` server

A FastMCP **stdio server** (`fermentation/library_mcp/server.py`) backed by a
baked SQLite wine library (`library.db`), seeded offline from Wikidata +
Wikipedia (`seed/build_db.py`). Tool surface:

- Browse (read-only): `lookup_country`, `lookup_region`, `lookup_grape`,
  `list_countries`, `list_regions`, `list_grapes`.
- Terminal: `submit_tags(country, region[], grapes[], is_blend, organic, confidence)`
  → `{ok, normalized}` on success, or `{ok:false, issues, hints}` so the model
  can correct and retry in-loop.

Why MCP instead of a bigger prompt or a post-hoc pass: synonyms collapse
upfront (Garnacha → Grenache), mismatches surface as a correctable tool failure,
and every lookup is captured in a structured transcript. See
`fermentation/PLAN.md` for the full rationale.

### LLM runtime

A single local model (default `gemma3n:e4b`) is hit at **two points** via an
OpenAI-compatible `/v1/chat/completions` endpoint:

- **llama.cpp `llama-server`:** `http://localhost:8080/v1/chat/completions` (default)
- **LM Studio (alternative):** `http://localhost:1234/v1/chat/completions` — pass `--api-url`

### Confidence & review flags

- A wine with no usable `web_context` (no snippets, or all dropped by the
  producer gate) is written as `needs_review` without ever calling the tagger.
- After tagging, `confidence < threshold` (default in `constants.py`) → `needs_review`.
- `organic` is set only when explicit certification language
  (`certified organic`, `biodynamic`, `certified biodynamic`) appears.
- Rows with `tag_status = 'manual'` are never overwritten on re-run.

### CLI flags

| Flag | Default | Description |
|------|---------|-------------|
| `--api-url` | llama.cpp (`:8080`) | LLM API URL (or `FERMENTATION_API_URL`) |
| `--model` | `gemma3n:e4b` | Model name (or `FERMENTATION_MODEL`) |
| `--confidence-threshold` | see `constants.py` | Min confidence to auto-accept |
| `--batch-size N` | 0 (all) | Pause for review after every N wines |
| `--limit N` | 0 (all) | Process at most N wines |
| `--force` | off | Ignore saved run state; restart from row 0 |
| `--input` | `ingestion/output/combined.csv` | Path to the input CSV |
| `--no-producer-gate` | off | Disable the producer-absent hard gate (debug) |
| `--debug-output` | off | Write per-stage JSON snapshots to `fermentation/output/` |

### Resumability

After each committed wine, `fermentation/.run_state.json` records the cursor.
Re-running the same command resumes from where it left off; `--force` discards
the state and starts fresh.

### SQLite schema (`fermentation/wines.db`)

```
products   — one row per wine; catalog fields + canonical tags (region/grapes as JSON arrays)
sales      — sales stats per SKU, joined to products via product_id
tag_log    — the MCP tool-call transcript per inference (for auditing)
```

**Tech:** Python 3.11+, sqlite3, requests, `mcp` (FastMCP), DuckDuckGo search —
no paid APIs or keys required.

> **Known issues (see `Tree.html` / `fermentation/PLAN.md`):** the default
> confidence threshold (90) fights the prompt's confidence caps, so most wines
> land in `needs_review`. The DDG import and the library reseed are fixed; see
> `fermentation/BATON.md`.

---

## Domain 3 — Distribution

**Status: not built** — `distribution/` contains only `PLAN.md`.

**Planned:** a local React + Vite + TypeScript dashboard that reads
`fermentation/wines.db`, lets you browse/search/edit tags, and exports a
Lightspeed-compatible `.xlsx` with columns `id`, `name`, `tags`
(semicolon-separated). See `distribution/PLAN.md`.

---

## Folder Structure

```
Wine Warehouse DDD/
├── README.md
├── PLAN.md
├── Tree.html                    # visual architecture map + findings
├── requirements.txt
├── gemma3n.sh / qwen25-7b.sh    # local LLM server helpers
├── ingestion/
│   ├── PLAN.md
│   ├── ingest.py
│   ├── run.sh
│   └── output/combined.csv      (generated)
├── fermentation/                # active
│   ├── PLAN.md
│   ├── ferment.py               # controller
│   ├── searcher.py · scorer.py · tagger.py
│   ├── types.py · constants.py · debug_output.py
│   ├── wines.db                 (generated)
│   └── library_mcp/
│       ├── server.py            # FastMCP stdio server
│       ├── schema.sql · library.db
│       └── seed/                # offline Wikidata + Wikipedia build
├── distribution/                # not built
│   └── PLAN.md
└── Sample Xlsx/
    ├── product-export.xlsx
    └── inventory-report (...).xlsx
```
