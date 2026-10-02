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
./run.sh                 # builds the frontend once, serves on http://localhost:8000
./run.sh dev             # uvicorn :8000 (auto-reload) + vite :5173 (HMR)
```

## Architecture

```
cellar/
  server/app.py          FastAPI — stage runners, SSE job streams, wines CRUD, export
  web/                   React 19 + Vite 8 + TypeScript + Tailwind v4
    src/api.ts           typed client for the /api surface
    src/components/      TopBar, StageTabs, IngestPanel, FermentPanel, DistributePanel,
                         WineTable, WineDrawer, TagEditor, EventLog, TranscriptView, ...
```

Data it reads and writes (all at the repo root):

| Path | Owner | Cellar does |
|---|---|---|
| `ingestion/uploads/*.csv` | you (drag & drop in Ingest) | stores, lists, deletes |
| `ingestion/fixtures/test-wines.csv` | repo | offers as "Test set (24 wines)" |
| `ingestion/filters.toml` | you | shows the rules |
| `ingestion/output/combined.csv` · `excluded.csv` · `summary.json` | ingestion | shows counts, previews rows, browses excluded rows |
| `output/wines.json` | fermentation | reads, `PATCH`es tag edits (marks `human`) |
| `settings.json` | cellar | user knobs shared with the CLI (confidence threshold) |
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
POST   /api/ingest/upload                multipart product-export CSV (header validated) -> stored upload
GET    /api/ingest/uploads · DELETE /api/ingest/uploads/{name}
POST   /api/ingest/run                   {input: upload name | "test-wines"} -> job
POST   /api/ferment/run                  {force, limit, confidence_threshold, model,
                                          api_url, no_producer_gate, phase, run_id,
                                          stop_after} -> job
POST   /api/llama/start                  start llama-server in the background (LLAMA_MODEL=qwen|gemma)
POST   /api/llama/stop                   stop llama-server (pid file + whatever listens on its port)
GET    /api/llama/log?lines=
GET    /api/jobs · /api/jobs/{id} · /api/jobs/{id}/events (SSE) · POST /api/jobs/{id}/stop
GET    /api/ingestion/rows?limit=        combined.csv as JSON
GET    /api/ingestion/excluded           excluded.csv as JSON
GET    /api/ingestion/summary            summary.json
GET    /api/ingestion/filters            parsed filters.toml
GET    /api/wines                        output/wines.json
GET    /api/wines/{id}?run_id=           wine + its search/scorer/tagger/final logs
PATCH  /api/wines/{id}                   tag edit -> tag_status = human
POST   /api/wines/reset-human            flip every human row back to pending
GET    /api/settings · PATCH /api/settings   settings.json (confidence_threshold)
GET    /api/runs · /api/runs/{id} · /api/runs/{id}/events · /api/runs/{id}/{phase}/{product_id}
GET    /api/runs/{id}/results            the wine table as that run produced it (final/*.json)
DELETE /api/runs/{id}                    rm -rf logs/{id} (409 if the active job writes to it)
POST   /api/runs/delete                  {run_ids} | {keep_latest: N} | {all: true}
GET    /api/library/countries · /regions?country= · /grapes
GET    /api/export.xlsx?status=model,human   Lightspeed export (id, name, tags)
```

## Which run am I looking at?

Every row in `wines.json` carries two run ids: `run_id` is the last run that
touched the row in *any* phase (a search-only run counts), `tag_run_id` is
the run whose tag phase produced the tags shown. Rows written before
`tag_run_id` existed get it backfilled on read (newest run with a
`final/<id>.json`). The Distribute table shows `tag_run_id` in the developer
"Tagged in" column.

The **Results from** selector on Distribute picks what the table shows:

- a run: exactly what `logs/<run>/` says — its wine set, tags from
  `final/`, phase dots derived from which log files exist; wines the run
  never reached are `pending`. Human edits are not shown here (they only
  live in the store) but rows the store has since hand-edited get a ✎ mark.
- **Live table**: `output/wines.json`, the merged result of every run plus
  hand edits, and what the export uses.

It defaults to the latest run and switches to a new run as soon as the job
reports its id, so a fresh run never shows a previous iteration's results.

## Deleting runs

Ferment → Run history lists every `logs/<run_id>/` with per-run delete,
"Delete all but latest 5" and "Delete all"; Distribute has "Delete this
run" for the selected run. The server never deletes the run the active job
writes to, and clears `output/.run_state.json` if it pointed at a deleted
run. `wines.json` is untouched.

## Export

Columns `id`, `name`, `tags`, where tags = `country; region…; grape…` joined
with `; `. Optional `status` filter restricts to given `tag_status` values.
The file is also written to `output/lightspeed-export.xlsx`.

## Not done / later

- Known bugs and their fix plan: `journal/2026-10-01-BUG-FIXES.md` (first
  item: the Ferment progress bars).
- Auth: none, it is a local tool.
- Pagination: the table loads everything; fine for hundreds of wines.
- The old `distribution/` open question "separate overrides DB" is moot —
  edits mark the row `human` in `wines.json` and fermentation never
  overwrites a `human` row.

## Tag statuses

| value | meaning |
|---|---|
| `pending` | not tagged yet |
| `model` | the LLM tagged it and cleared the confidence threshold |
| `needs_review` | the LLM could not tag it confidently (no context, no grapes, low confidence), or an evidence rule fired — `final/<id>.json` → `review_reasons` says which: `unsupported_grape:<name>` (grape not in the context it was shown), `single_source` (every snippet came from one site → confidence clamped to 69 and routed to review), and the rest listed in `fermentation/PLAN.md` (`uncorroborated_grape`, `coarse_region`, `longer_region`, `unsupported_region`, …) |
| `human` | a person saved tags in Cellar; fermentation skips it until "Reset human tags" |

(`auto` / `manual` were the names before 2026-09-15; `store.load_store` migrates them.)

A row whose CSV `product_category` is blank gets one inferred by the tagger
(`Red` / `White` / `Rose` / `Sparkling`), stored with `category_source:
"model"` and shown as *inferred* in the drawer. A CSV category always wins.

## Phased runs

"Pause after each phase" (Ferment panel) sends `stop_after=search`; the run
exits after search with status `paused` and the panel shows **Continue → score**,
which posts `{run_id, phase: score, stop_after: score}`, and so on. The
table in Distribute refreshes live during a run (every progress event,
throttled to one reload per 2 s) so tags appear as each wine is written.
