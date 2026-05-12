# Wine Warehouse -- DDD Data Pipeline

## Overview

A three-domain pipeline that takes raw Lightspeed product and inventory exports, enriches them with AI-generated tags, and produces a dashboard for review and re-upload.

```
  ┌─────────────┐       ┌─────────────┐       ┌────────────────┐
  │  Ingestion   │──CSV──▶  Curation   │──DB───▶  Distribution  │
  │  (Python)    │       │  (Python +   │       │  (React/Vite/  │
  │              │       │   Gemma)     │       │   TypeScript)  │
  └─────────────┘       └─────────────┘       └────────────────┘
```

## Domains

### 1. Ingestion (`ingestion/`)

Reads the raw `.xlsx` exports from Lightspeed (product catalog and inventory/sales report), cleans and normalizes the data, and outputs well-structured CSV files that downstream domains can consume without any xlsx dependency.

**Input:** Two `.xlsx` files (product export, inventory report)
**Output:** Single `combined.csv` in `ingestion/output/` -- product catalog columns and sales stats merged into one row per wine via a name-based full outer join.

### 2. Curation (`curation/`)

Consumes the clean CSVs. Uses a locally-running Gemma model (via Ollama or LM Studio) to search the internet and generate tags for each wine -- country of origin, region, and grape varieties. Stores everything in a SQLite database that becomes the single source of truth.

**Input:** `combined.csv` from `ingestion/output/`
**Output:** SQLite database at `curation/output/wines.db`

### 3. Distribution (`distribution/`)

A local React + Vite + TypeScript dashboard that reads from the SQLite database. Lets you browse, search, and edit wine data and tags. Exports a Lightspeed-compatible `.xlsx` with the columns `id`, `name`, and `tags` (semicolon-separated).

**Input:** SQLite database from `curation/output/wines.db`
**Output:** Lightspeed import `.xlsx`

## Data Flow

Each domain is self-contained in its own folder. Data flows strictly downstream -- no domain reaches back into an upstream domain's internals. The contract between domains is defined by their output format:

- Ingestion -> Curation: `combined.csv` with agreed-upon column names (products + sales stats in one file)
- Curation -> Distribution: SQLite database with a known schema

## Running the Pipeline

Each domain has its own run script. Execute them in order:

```
./ingestion/run.sh
./curation/run.sh
./distribution/run.sh   # starts the dev server
```

## Folder Structure

```
Wine Warehouse DDD/
├── PLAN.md                  # this file
├── ingestion/
│   ├── PLAN.md
│   ├── run.sh
│   └── ...
├── curation/
│   ├── PLAN.md
│   ├── run.sh
│   └── ...
├── distribution/
│   ├── PLAN.md
│   ├── run.sh
│   └── ...
└── Sample Xlsx/
    ├── product-export.xlsx
    └── inventory-report (...).xlsx
```
