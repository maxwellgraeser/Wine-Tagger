# Cellar — the dashboard

> **✅ Built (2026-09-15).** Cellar replaces the old `distribution/` plan. It
> is one local web app that drives all three pipeline stages — Ingest,
> Ferment, Distribute — and includes the Lightspeed export that
> `distribution/` was going to own.

## Purpose

Stop running the pipeline from the console. One page shows the state of
every stage, runs each stage with a button, streams progress live, lets you
inspect exactly what each fermentation phase saw and produced, edit tags,
and export the Lightspeed `.xlsx`.

## Run

```sh
./cellar/run.sh          # builds the frontend once, serves on http://localhost:8000
./cellar/run.sh dev      # uvicorn :8000 (auto-reload) + vite :5173 (HMR)
```

## Architecture

```
cellar/
  run.sh                 launcher (serve | dev)
  server/app.py          FastAPI — stage runners, SSE job streams, wines CRUD, export
  web/                   React 19 + Vite 8 + TypeScript + Tailwind v4
    src/api.ts           typed client for the /api surface
    src/components/      TopBar, StageTabs, IngestPanel, FermentPanel, DistributePanel,
                         WineTable, WineDrawer, TagEditor, EventLog, TranscriptView, ...
```

Data it reads and writes (all at the repo root):

| Path | Owner | Cellar does |
|---|---|---|
| `Sample Xlsx/*.xlsx` | you | lists them |
| `ingestion/output/combined.csv` | ingestion | previews rows |
| `output/wines.json` | fermentation | reads, `PATCH`es tag edits (marks `manual`) |
| `output/.run_state.json` | fermentation | shows resume cursor |
| `logs/<run_id>/…` | fermentation | browses per-phase logs and transcripts |
| `fermentation/library_mcp/library.db` | library seed | read-only vocab for the tag editor |
| `output/lightspeed-export.xlsx` | cellar | writes on export |

## Views

- **Developer** (default until release) — stage panels with run options,
  three phase progress bars, live event log, run history, and a per-wine
  drill-down: raw snippets → scored snippets (with producer-gate drops) →
  web_context → MCP transcript → final normalized block.
- **Simple** — the wine table, a tag editor, one "Run pipeline" control, and
  the export button.

The toggle lives in the top bar and is remembered in `localStorage`.

## Stage runners

Each stage is a subprocess of the repo's `.venv` Python:

- Ingest → `ingestion/ingest.py`
- Ferment → `python -m fermentation.ferment --events-json [flags]`

The backend buffers every stdout line (fermentation emits one JSON event per
line) and fans it out over Server-Sent Events at
`GET /api/jobs/{id}/events`. History is replayed on connect, so reloading
the page mid-run picks the stream back up. Only one job runs at a time.
`POST /api/jobs/{id}/stop` sends SIGINT; fermentation checkpoints after
every wine, so the next run resumes where it stopped.

## API

```
GET    /api/status                       everything the top bar and stage cards need
POST   /api/ingest/run                   -> job
POST   /api/ferment/run                  {force, limit, confidence_threshold, model,
                                          api_url, no_producer_gate, phase, run_id} -> job
POST   /api/llama/start                  start the llama-server script in the background
GET    /api/llama/log?lines=
GET    /api/jobs · /api/jobs/{id} · /api/jobs/{id}/events (SSE) · POST /api/jobs/{id}/stop
GET    /api/ingestion/rows               combined.csv as JSON
GET    /api/wines                        output/wines.json
GET    /api/wines/{id}?run_id=           wine + its search/scorer/tagger/final logs
PATCH  /api/wines/{id}                   tag edit -> tag_status = manual
GET    /api/runs · /api/runs/{id} · /api/runs/{id}/events · /api/runs/{id}/{phase}/{product_id}
GET    /api/library/countries · /regions?country= · /grapes
GET    /api/export.xlsx?status=auto,manual   Lightspeed export (id, name, tags)
```

## Export

Columns `id`, `name`, `tags`, where tags = `country; region…; grape…` joined
with `; `. Optional `status` filter restricts to given `tag_status` values.
The file is also written to `output/lightspeed-export.xlsx`.

## Not done / later

- Auth: none, it is a local tool.
- Pagination: the table loads everything; fine for hundreds of wines.
- The old `distribution/` open question "separate overrides DB" is moot —
  edits mark the row `manual` in `wines.json` and fermentation never
  overwrites a `manual` row.
