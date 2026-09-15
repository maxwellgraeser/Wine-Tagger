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
> library** to tag wines. `distribution/` was renamed `cellar/` and built as the web app.

## Status at a glance

| Domain | State | Entry point | Notes |
|---|---|---|---|
| `ingestion/` | ✅ Implemented | `ingestion/run.sh` | xlsx → `combined.csv` |
| `fermentation/` | 🟧 Active build | `./ferment.sh` / `python -m fermentation.ferment` | |
| `cellar/` | ✅ Built | `cellar/run.sh` | web app over all three stages; owns the Lightspeed export (was `distribution/`) |

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
**Output:** `output/wines.json` (all wines, tags, sales, per-phase status) plus
`logs/<run_id>/` with every phase's per-wine JSON. Fermentation runs its three
phases — search, score, tag — each over the whole list before the next.

### 3. Distribution — Cellar (`cellar/`)

A local FastAPI + React/Vite/TypeScript/Tailwind dashboard that runs all three
stages with live progress, browses every fermentation log, lets you
search/edit tags, and exports a Lightspeed-compatible `.xlsx` (`id`, `name`,
`tags`). Developer view (default) and Simple view. See `cellar/PLAN.md`.

**Input:** `output/wines.json` + `logs/`
**Output:** Lightspeed import `.xlsx`

## Data Flow

Each domain is self-contained in its own folder. Data flows strictly
downstream — no domain reaches back into an upstream domain's internals. The
contract between domains is their output format:

- Ingestion → Fermentation: `combined.csv` with agreed column names.
- Fermentation → Cellar: `output/wines.json` with a known shape
  (`tag_status` ∈ pending | model | needs_review | human).
- Cellar ↔ Fermentation: `settings.json` at the repo root (confidence
  threshold) — written by the dashboard, read by both.

## Running the Pipeline

```
./cellar/run.sh                         # everything, from the browser (:8000)

./ingestion/run.sh                      # or stage by stage from the console
./ferment.sh [--force --limit N]
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
│   ├── ferment.py           # CLI
│   ├── phases.py            # search → score → tag, each over all wines
│   ├── searcher.py · scorer.py · tagger.py
│   ├── store.py · events.py · paths.py · types.py · constants.py
│   └── library_mcp/         # FastMCP server + baked library.db + seed/
├── cellar/                  # the web app (FastAPI + React)
│   ├── PLAN.md · run.sh · server/app.py · web/
├── output/                  (generated) wines.json, .run_state.json
├── logs/                    (generated) per-run phase logs
└── Sample Xlsx/
    ├── product-export.xlsx
    └── inventory-report (...).xlsx
```
