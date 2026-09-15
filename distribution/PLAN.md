# Distribution Domain

> **⬜ NOT BUILT.** This domain is a design plan only — the folder currently
> contains just this `PLAN.md` (no `run.sh`, no source). Everything below is
> the intended design, not a description of existing code.
>
> **Input source changed:** it reads `fermentation/wines.db` (the
> `fermentation/` domain replaced `curation/`). The schema is compatible —
> `products` / `sales` tables with the columns this plan assumes — but the
> `tag_log` shape differs (fermentation stores an MCP tool-call transcript, not
> raw prompt/response). Distribution does not read `tag_log`, so this is not a
> blocker.

## Purpose

Provide a local web dashboard for browsing, editing, and exporting wine data. Reads from the SQLite database produced by fermentation. Exports a Lightspeed-compatible `.xlsx` for re-upload.

## Architecture

```
┌──────────────────────────────────────────────┐
│  React + Vite + TypeScript (Frontend)        │
│  - Wine table with search/filter/sort        │
│  - Tag editing (country, region, grapes)     │
│  - Sales stats view                          │
│  - Export button                             │
├──────────────────────────────────────────────┤
│  Express or Fastify API (Backend)            │
│  - REST endpoints for CRUD on wines          │
│  - Export endpoint (generates xlsx)          │
│  - Reads/writes to SQLite via better-sqlite3 │
├──────────────────────────────────────────────┤
│  SQLite (fermentation/wines.db)              │
└──────────────────────────────────────────────┘
```

## Frontend

### Tech Stack

- React 18+
- Vite
- TypeScript
- Tailwind CSS (or a lightweight component library -- TBD)

### Key Views

**Wine Table (main view)**
- Columns: name, category, country, region, grapes, tags_raw, supply_price, retail_price, supplier, tag_status.
- Sortable by any column.
- Filterable by category, country, region, tag_status.
- Searchable by name.
- Inline editing for country, region, grapes. On save, tag_status flips to `reviewed`.

**Sales Stats**
- Per-wine: items sold, margin, sale count, customer count.
- Summary stats: top sellers, highest margin, most customers.
- Could be a detail panel or a separate view.

**Export**
- Button that triggers an xlsx download.
- Output columns: `id`, `name`, `tags` (semicolon-separated).
- Tags string built from: country, region, and each grape variety, joined with `; `.
  - Example: `France; Bordeaux; Cabernet Sauvignon; Merlot`

## Backend API

A lightweight Node.js server running alongside Vite in dev mode.

### Endpoints

```
GET    /api/wines              -- list all wines (supports ?search, ?category, ?status query params)
GET    /api/wines/:id          -- single wine detail with sales stats
PATCH  /api/wines/:id          -- update tags (country, region, grapes), sets tag_status = 'reviewed'
GET    /api/wines/export       -- download Lightspeed xlsx
GET    /api/stats/summary      -- aggregate sales stats
```

### Database Access

- `better-sqlite3` for synchronous, simple SQLite access from Node.
- Reads from `fermentation/wines.db` (path configurable via env var).
- Writes only to the `products` table (tag edits) -- never modifies `sales` or `tag_log`.

### Export Logic

When `/api/wines/export` is called:
1. Query all products.
2. For each, build the tags string: `{country}; {region}; {grape1}; {grape2}; ...`
3. Generate an xlsx with three columns: `id`, `name`, `tags`.
4. Stream it as a download.

Use `exceljs` or `xlsx` (SheetJS) for xlsx generation on the server side.

## Tech

- Node.js 18+
- Vite + React + TypeScript
- Express or Fastify
- better-sqlite3
- exceljs or xlsx (SheetJS)
- Tailwind CSS

## Open Questions

- Should the backend be a separate Express server or use Vite's built-in server middleware?
- Do we want pagination on the wine table, or is the dataset small enough to load everything at once?
- Should edits to tags write back to the same `wines.db` or to a separate "overrides" database to keep curation's output clean?
- Do we need auth, or is this purely a local tool?
- Should the export include wines where `tag_status = 'auto'` (unreviewed), or only reviewed ones?
