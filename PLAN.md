# Wine Warehouse -- DDD Data Pipeline

## Overview

A domain-driven pipeline that takes raw Lightspeed product and inventory
exports, enriches them with AI-generated wine tags, and (eventually) produces a
dashboard for review and re-upload.

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

## Status at a glance

| Domain | State | Entry point | Notes |
|---|---|---|---|
| `ingestion/` | ✅ Implemented | `ingestion/run.sh` | xlsx → `combined.csv` |
| `fermentation/` | 🟧 Active build | `python -m fermentation.ferment` | no `run.sh` yet |
| `distribution/` | ⬜ Not built | — | only `distribution/PLAN.md` exists |

See each domain's `PLAN.md` for detail, and `Tree.html` (repo root) for a
visual component map plus an ordered list of known issues.

## Domains

### 1. Ingestion (`ingestion/`)

Reads the raw `.xlsx` exports from Lightspeed (product catalog and
inventory/sales report), cleans and normalizes the data, and outputs a single
CSV that downstream domains consume without any xlsx dependency.

**Input:** Two `.xlsx` files (product export, inventory report) in `Sample Xlsx/`
**Output:** `ingestion/output/combined.csv` — product catalog columns and sales
stats merged into one row per wine via a name-based **inner join**
(case-insensitive; rows present in only one source are dropped and logged).

### 2. Fermentation (`fermentation/`)

Consumes `combined.csv`. For each wine it gathers web snippets (DuckDuckGo),
uses a local LLM to score snippet relevance, then drives a second LLM tool-call
loop against the **`library_mcp`** server to infer and *canonicalize* tags —
country, region(s), grapes, blend status, organic status, confidence. Results
land in a fresh SQLite database.

Architecture is a controller (`ferment.py`) over three independent modules:

- `searcher.py` — DDG queries, dedupe, snippet cleanup → `list[Snippet]`.
- `scorer.py` — one LLM call scores snippets 0–100, a **producer-absent hard
  gate** drops snippets missing the producer name, top-N assembled into
  `web_context` (or `None`, which short-circuits to `needs_review`).
- `tagger.py` — drives the MCP tool-call loop; the model browses canonical
  countries/regions/grapes via `lookup_*`/`list_*` and commits via
  `submit_tags`, which is the canonicalization gate — whatever it accepts is
  what gets written; there is no second normalization pass.

The **`library_mcp/`** package is a FastMCP stdio server backed by a baked
SQLite wine library (`library.db`), seeded offline from Wikidata + Wikipedia.

**Input:** `ingestion/output/combined.csv`
**Output:** SQLite database at `fermentation/wines.db` (tables: `products`,
`sales`, `tag_log`).

### 3. Distribution (`distribution/`)

*Planned — not yet implemented.* A local React + Vite + TypeScript dashboard
that reads the SQLite database, lets you browse/search/edit tags, and exports a
Lightspeed-compatible `.xlsx` (`id`, `name`, `tags`). See
`distribution/PLAN.md`.

**Input:** SQLite database from `fermentation/wines.db`
**Output:** Lightspeed import `.xlsx`

## Data Flow

Each domain is self-contained in its own folder. Data flows strictly
downstream — no domain reaches back into an upstream domain's internals. The
contract between domains is their output format:

- Ingestion → Fermentation: `combined.csv` with agreed column names.
- Fermentation → Distribution: SQLite database with a known schema.

## Running the Pipeline

```
./ingestion/run.sh
python -m fermentation.ferment          # (no run.sh wrapper yet)
# ./distribution/run.sh                 # not built
```

Fermentation needs a local OpenAI-compatible LLM endpoint running first
(llama.cpp `llama-server` on :8080, or LM Studio on :1234). The `gemma3n.sh` /
`qwen25-7b.sh` helper scripts at the repo root start a server.

## Folder Structure

```
Wine Warehouse DDD/
├── PLAN.md                  # this file
├── README.md
├── Tree.html                # visual architecture map + findings
├── requirements.txt
├── ingestion/
│   ├── PLAN.md
│   ├── ingest.py
│   └── run.sh
├── fermentation/            # active
│   ├── PLAN.md
│   ├── ferment.py           # controller
│   ├── searcher.py · scorer.py · tagger.py
│   ├── types.py · constants.py · debug_output.py
│   └── library_mcp/         # FastMCP server + baked library.db + seed/
├── distribution/            # not built
│   └── PLAN.md
└── Sample Xlsx/
    ├── product-export.xlsx
    └── inventory-report (...).xlsx
```
