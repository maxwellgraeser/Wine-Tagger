# Wine Warehouse DDD Data Pipeline

A domain-driven pipeline that takes raw Lightspeed exports, enriches them with
AI-generated wine metadata, and produces a database for review and re-upload.

```
  ┌─────────────┐      ┌──────────────────┐      ┌────────────────┐
  │  Ingestion  │─CSV─▶│   Fermentation   │─JSON▶│  Distribution  │
  │  (Python)   │      │ (Python + local  │      │  (tag review + │
  │             │      │  LLM + MCP lib)  │      │  xlsx export)  │
  └─────────────┘      └──────────────────┘      └────────────────┘
        done                  active                  in Cellar
  ═══════════════════════════════════════════════════════════════════
                  Cellar — one web app that runs all three
                  (FastAPI + React, ./cellar/run.sh, :8000)
```

> `fermentation/` drives a local LLM through a self-built **MCP wine
> library** to tag wines. `distribution/` became `cellar/`, the web app.
>
> See `Tree.html` (repo root) for a visual component map and a
> severity-ordered list of known issues.

## Status at a glance

| Domain | State | Entry point | In → Out |
|---|---|---|---|
| `ingestion/` | ✅ Implemented | `./ingestion/run.sh` | 2× `.xlsx` → `combined.csv` |
| `fermentation/` | 🟧 Active build | `./ferment.sh` / `python -m fermentation.ferment` | `combined.csv` → `output/wines.json` + `logs/` |
| `cellar/` | ✅ Built | `./cellar/run.sh` | web app over all stages; `wines.json` → Lightspeed `.xlsx` |

Each domain is self-contained. Data flows strictly downstream — no domain
reaches back into an upstream domain's internals; the contract between domains
is their output format (`combined.csv`, then `output/wines.json`).

## How to Run

**The easy way — Cellar.** One web page runs every stage, streams progress,
and lets you inspect logs, edit tags, and export:

```sh
./cellar/run.sh            # http://localhost:8000  (first run: npm install + build)
./cellar/run.sh dev        # hot reload: API on :8000, Vite on :5173
```

Cellar starts in **Developer** view (all logs and knobs); toggle to
**Simple** in the top bar. If the llama-server isn't up, the top bar offers
to start it.

In the Ferment panel, **Pause after each phase** runs search, stops, and
shows a *Continue → score* button (then *Continue → tag*), so you can check
the snippets and scores in Distribute before the LLM tags anything. The
confidence threshold you set there is saved to `settings.json` at the repo
root and used by console runs too (initial default 85).

**From the console:**

```sh
# 1. Ingestion — xlsx → CSV
./ingestion/run.sh

# 2. Fermentation — starts llama-server on :8080 if it isn't already up
#    (default ./gemma3n.sh), waits for /health, then runs the module.
#    Flags pass through to ferment.
./ferment.sh --force --limit 3
LLAMA_SCRIPT=./qwen25-7b.sh ./ferment.sh   # use a different model

# 3. Distribution — the export lives in Cellar (Distribute tab → Export),
#    or GET http://localhost:8000/api/export.xlsx
```

> `ferment.sh` leaves a server it started running, so later runs skip the model
> load. To stop it, run `kill "$(cat .llama-server.pid)"`. To run the module
> without the wrapper, use `python -m fermentation.ferment` from the repo root.

**Stopping everything:**

```sh
./stop-all.sh   # kills cellar backend (:8000), vite dev (:5173), llama-server (:8080)
```

Run this when you're done for the day so nothing keeps eating RAM/GPU in the
background. It's safe to run even if some or all of those servers aren't up.
`./cellar/run.sh` (and `./cellar/run.sh dev`) also kill anything already
bound to their own ports before starting, so re-running either one always
gives you a fresh process — you don't need to `stop-all.sh` first just to
restart Cellar.

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

**What it does:** Runs three phases, each over the **whole** wine list before
the next starts:

1. **search** — gather web snippets for every wine → `logs/<run>/search/`
2. **score** — the LLM scores every snippet (in batches of 8, URL shown,
   missing indices re-asked) for same-wine match and notes which facts it
   states; the producer-absent gate drops non-matches; the most fact-rich
   survivors become `web_context` → `logs/<run>/scorer/`
3. **tag** — drive the LLM through a **tool-call loop against the
   `library_mcp` server** to infer and *canonicalize* country, region(s),
   grapes, blend, organic, confidence → `logs/<run>/tagger/`, `final/`, and
   `output/wines.json`

Running phase-by-phase (111 222 333 rather than 123 123 123) means every
intermediate is on disk and inspectable before the next phase spends LLM time
on it, and a phase can be re-run alone with `--phase … --run-id …`.

**Input:** `ingestion/output/combined.csv`
**Output:** `output/wines.json` (one JSON document, see below) and
`logs/<run_id>/` (per-phase, per-wine JSON plus `run.json` and `events.jsonl`)

### Architecture

`ferment.py` (CLI) → `phases.py` (the three phase loops) → three independent
modules that never import each other; config (model, api_url) is passed down:

- **`searcher.py`** — owns the network for snippets. DuckDuckGo queries (UPC +
  per-source + fallback), cross-query URL dedupe, boilerplate strip, price-only
  filter. → `list[Snippet]`.
- **`scorer.py`** — the LLM scores each snippet 0–100 for product match
  *and* lists the facts it states (`grape` / `region` / `producer`). Snippets
  go in batches of `SCORING_BATCH_SIZE` with their URL (the producer is often
  only in the slug), and any index the model leaves out of its reply is
  re-asked rather than silently scored 0 — that omission lost 28 % of matching
  snippets on the 2026-09-15 run. A **producer-absent hard gate** drops
  snippets that don't mention the producer name. Of the survivors above
  `SNIPPET_MATCH_THRESHOLD` (70, the rubric's "very likely the same wine"
  band), the grape-naming, most-fact-rich ones fill `web_context` (score
  only gates identity) — or `None`, in which case the wine routes straight
  to `needs_review` and the tagger is skipped. Method and evidence:
  `fermentation/SCORING-2026-09-15.md`.
- **`evidence.py`** — mechanical checks on the tagger's output against the
  text it was shown (see "Confidence & review flags").
- **`tagger.py`** — drives the MCP tool-call loop. The model browses canonical
  countries/regions/grapes via `lookup_*`/`list_*`, then commits via
  `submit_tags`. `submit_tags` **is the canonicalization gate** — whatever it
  accepts is what gets written; there is no second normalization pass.

Supporting modules: `store.py` (read/write `output/wines.json`, manual edits,
export rows), `events.py` (progress events: human lines, or `--events-json`
JSON lines for Cellar, always appended to `events.jsonl`), `paths.py`
(the folder layout).

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
- **Evidence rules** (`phases.apply_evidence_rules`, enforced in code, not
  just asked for in the prompt): a submitted grape that appears nowhere in
  `web_context` — by canonical name or any library synonym — routes the row
  to `needs_review` (`review_reasons: ["unsupported_grape:Cinsault"]` in
  `final/<id>.json`); when only one snippet was in context, confidence is
  clamped to `SINGLE_SNIPPET_CONFIDENCE_CAP` (84).
- **Category**: when the CSV has no `product_category`, the tagger submits
  one of `Red / White / Rose / Sparkling` from the snippets; the store keeps
  it (`category_source: "model"`, shown as *inferred* in Cellar) until the
  CSV supplies a real one. A CSV category is never overwritten.
- `organic` is set only when explicit certification language
  (`certified organic`, `biodynamic`, `certified biodynamic`) appears.
- Rows with `tag_status = 'human'` (edited in Cellar) are never overwritten on re-run.

### CLI flags

| Flag | Default | Description |
|------|---------|-------------|
| `--api-url` | llama.cpp (`:8080`) | LLM API URL (or `FERMENTATION_API_URL`) |
| `--model` | `gemma3n:e4b` | Model name (or `FERMENTATION_MODEL`) |
| `--confidence-threshold` | see `constants.py` | Min confidence to auto-accept |
| `--limit N` | 0 (all) | Process at most N wines (fresh runs only) |
| `--force` | off | Ignore saved run state; start a fresh run |
| `--input` | `ingestion/output/combined.csv` | Path to the input CSV |
| `--no-producer-gate` | off | Disable the producer-absent hard gate (debug) |
| `--phase P --run-id R` | — | Re-run from phase `search`/`score`/`tag` over run R's existing logs |
| `--events-json` | off | One JSON event per line on stdout (what Cellar reads) |

### Resumability

After every wine, `output/.run_state.json` records `(run_id, phase, cursor)`.
Re-running (or pressing Run again in Cellar) resumes inside that phase;
`--force` starts a fresh run with a new run id. Ctrl-C / the Stop button
checkpoints cleanly.

### `output/wines.json`

```jsonc
{
  "version": 2, "generated_at": "…", "last_run_id": "20260915-132128",
  "wines": [{
    "id": "…", "name": "…", "sku": "…", "category": "Red", "brand": null,
    "supply_price": 17.99, "retail_price": 25.99, "supplier": "Winebow",
    "country": "Spain", "region": ["Ribera del Duero", "Castilla y León"],
    "grapes": ["Tempranillo"], "is_blend": false, "organic": false,
    "confidence": 84, "web_context": "…", "tags_raw": "Spain; Ribera del Duero; …",
    "tag_status": "model",                // pending | model | needs_review | human
    "sales": {"items_sold": 81, "margin_pct": 0.31, "sale_count": 46, "customer_count": 29, "avg_sale_value": 29.5},
    "run_id": "20260915-132128",
    "phase_status": {"search": "ok", "score": "ok", "tag": "ok"}
  }]
}
```

### `logs/<run_id>/`

```
run.json              args, product ids, per-phase status + counts
events.jsonl          every progress event of the run
search/<id>.json      raw snippets (source, domain, url, body)
scorer/<id>.json      match_score + dropped_reason per snippet, web_context
tagger/<id>.json      the full MCP tool-call transcript
final/<id>.json       normalized block + tag_status as written to wines.json
```

**Tech:** Python 3.11+, sqlite3, requests, `mcp` (FastMCP), DuckDuckGo search —
no paid APIs or keys required.

> **Scoring methodology:** see `fermentation/SCORING-2026-09-15.md` for why
> the snippet score was rebuilt (batched per-index scoring, URL shown,
> facts-first context, threshold 70) and the evidence rules that gate the
> tagger's output. `fermentation/ACCURACY-2026-09-15.md` is the earlier
> per-wine accuracy review; `fermentation/BATON.md` the library reseed.

---

## Domain 3 — Distribution, and Cellar

**Run:** `./cellar/run.sh` → http://localhost:8000

`cellar/` is the web app (FastAPI backend in `cellar/server/app.py`, React +
Vite + TypeScript + Tailwind frontend in `cellar/web/`). It owns the
distribution step — browse, search, sort, edit tags (edits mark a wine
`human`, which fermentation never overwrites), and **Export** a
Lightspeed-compatible `.xlsx` with `id`, `name`, `tags` — and it also runs the
two upstream stages with live progress and a drill-down into every phase log.
See `cellar/PLAN.md` for the API.

---

## Folder Structure

```
Wine Warehouse DDD/
├── README.md
├── PLAN.md
├── Tree.html                    # visual architecture map + findings
├── requirements.txt
├── ferment.sh                   # runs fermentation, starting llama-server if needed
├── stop-all.sh                  # kills cellar backend, vite dev, and llama-server
├── gemma3n.sh / qwen25-7b.sh    # local LLM server helpers
├── ingestion/
│   ├── PLAN.md
│   ├── ingest.py
│   ├── run.sh
│   └── output/combined.csv      (generated)
├── fermentation/                # active
│   ├── PLAN.md · SCORING-2026-09-15.md · ACCURACY-2026-09-15.md · BATON.md
│   ├── ferment.py               # CLI
│   ├── phases.py                # search → score → tag, each over all wines
│   ├── searcher.py · scorer.py · tagger.py · evidence.py
│   ├── store.py · events.py · paths.py · types.py · constants.py
│   ├── tests/                   # offline scorer / evidence / category tests
│   └── library_mcp/
│       ├── server.py            # FastMCP stdio server
│       ├── schema.sql · library.db
│       └── seed/                # offline Wikidata + Wikipedia build
├── output/                      (generated) wines.json, .run_state.json, lightspeed-export.xlsx
├── logs/                        (generated) one folder per fermentation run
├── cellar/                      # the web app
│   ├── PLAN.md · run.sh
│   ├── server/app.py            # FastAPI
│   └── web/                     # React + Vite + Tailwind
└── Sample Xlsx/
    ├── product-export.xlsx
    └── inventory-report (...).xlsx
```
