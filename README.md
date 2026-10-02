# Wine Warehouse DDD Data Pipeline

> [!WARNING]
> **Every wine's tags need a human check before they go into Lightspeed.**
> The tags are built from information found online, and that information
> describes *a* wine, not necessarily *your* vintage. Producers change their
> blends from year to year, so a page can be about exactly the right wine and
> still describe a different year's composition. Web information can also be
> outdated. The pipeline does not match on vintage.
>
> - **Country and region** are a good basis. They rarely change between vintages.
> - **Grape blends** may be slightly inaccurate depending on the vintage, unless
>   the blend for that vintage is provided or confirmed (the label, the
>   producer's tech sheet). Check them.
> - A high confidence score does **not** cover this. It says nothing about
>   whether the grapes match the vintage on the shelf.
>
> Review and correct tags in Cellar (Distribute tab). Edits mark a wine `human`,
> and re-runs never overwrite those.

Built for **Wine Warehouse**, a wine shop in Atlantic Beach, Florida. Since the store moved to Lightspeed for the POS, new products come in with
no category and no country, region or grape tags, so the catalogue can't be
searched or filtered the way the staff need. This project picks the wines out
of the catalogue, researches and tags each one with a local LLM, and produces
a file to import back into Lightspeed.

A domain-driven pipeline: the raw Lightspeed product export goes in,
AI-generated wine tags are reviewed in a local web app, and a Lightspeed
import `.xlsx` comes out.

```
  ┌─────────────┐      ┌──────────────────┐      ┌────────────────┐
  │  Ingestion  │─CSV─▶│   Fermentation   │─JSON▶│  Distribution  │
  │  (Python)   │      │ (Python + local  │      │  (tag review + │
  │             │      │  LLM + MCP lib)  │      │  xlsx export)  │
  └─────────────┘      └──────────────────┘      └────────────────┘
        done                  active                  in Cellar
  ═══════════════════════════════════════════════════════════════════
                  Cellar — one web app that runs all three
                  (FastAPI + React, ./run.sh, :8000)
```

> `fermentation/` drives a local LLM through a self-built **MCP wine
> library** to tag wines. `distribution/` became `cellar/`, the web app.

## Status at a glance

| Domain | State | Entry point | In → Out |
|---|---|---|---|
| `ingestion/` | ✅ Implemented | Cellar → Ingest | product-export `.csv` → filters → `combined.csv` + `excluded.csv` |
| `fermentation/` | 🟧 Active build | Cellar → Ferment / `python -m fermentation.ferment` | `combined.csv` → `output/wines.json` + `logs/` |
| `cellar/` | ✅ Built | `./run.sh` | web app over all stages; `wines.json` → Lightspeed `.xlsx` |

Each domain is self-contained. Data flows strictly downstream — no domain
reaches back into an upstream domain's internals; the contract between domains
is their output format (`combined.csv`, then `output/wines.json`).

## How to Run

**The easy way — Cellar.** One web page runs every stage, streams progress,
and lets you inspect logs, edit tags, and export:

```sh
./run.sh                   # http://localhost:8000  (first run: npm install + build)
./run.sh dev               # hot reload: API on :8000, Vite on :5173
CELLAR_PORT=8010 VITE_PORT=5183 ./run.sh dev   # a second checkout (git worktree) beside the main one
```

Cellar starts in **Developer** view (all logs and knobs); toggle to
**Simple** in the top bar. The top bar shows the llama-server state and has
**Start / Stop model server** buttons (model: `LLAMA_MODEL=qwen|gemma`, default
qwen). Starting it needs `llama-server` (llama.cpp) on your `PATH`; it pulls
the GGUF from Hugging Face on first start.

In the Ferment panel, **Pause after each phase** runs search, stops, and
shows a *Continue → score* button (then *Continue → tag*), so you can check
the snippets and scores in Distribute before the LLM tags anything. The
confidence threshold you set there is saved to `settings.json` at the repo
root and used by console runs too (initial default 85).

**From the console** (without the dashboard), from the repo root:

```sh
.venv/bin/python ingestion/ingest.py --input export.csv      # 1. product export → combined.csv
.venv/bin/python -m fermentation.ferment --force --limit 3   # 2. needs llama-server on :8080
# 3. Distribution — the export lives in Cellar (Distribute tab → Export),
#    or GET http://localhost:8000/api/export.xlsx
```

**Stopping:** Ctrl-C in the `./run.sh` terminal stops Cellar. The llama-server
runs detached so it survives Cellar restarts — stop it with **Stop model
server** in the top bar before you quit, so it doesn't keep eating RAM/GPU.
Re-running `./run.sh` kills anything already on :8000 first, so it always gives
you a fresh process.

**Tests** (all offline, ~8 s):

```sh
.venv/bin/python -m pytest
```

---

## Domain 1 — Ingestion

**Run:** Cellar → Ingest (drag & drop the export, pick it, *Run ingestion*),
or `.venv/bin/python ingestion/ingest.py --input <export.csv>`

**What it does:** Takes the Lightspeed **product export CSV** (the whole
catalogue — wine, beer, sake, accessories…), decides which rows are wines,
and writes them to `combined.csv`. Since the POS switch new products have no
category, so the filters green-light what is known and sift the rest.

**Input:** one `product-export-*.csv` (Lightspeed → Products → Export → CSV).
It is the only accepted format; the header row is checked on upload. Uploads
live in `ingestion/uploads/`. The Ingest panel also offers the **Test set
(24 wines)** — `ingestion/fixtures/test-wines.csv`, the wines the pipeline was
developed on, kept with their sales stats for quick fermentation runs.

**Filters** (`ingestion/filters.toml` — edit it, run again):
1. **Category whitelist** — Red, White, Rose, Sparkling, Orange/Amber are
   kept as-is; any other category (Beer, Dessert, Sherry, Accessories…) is excluded.
2. **Vendor blacklist** — uncategorized rows from beer/accessory-only
   suppliers (Cavalier, Progressive, North Fl Sales, Champion, True,
   Lottie Dottie, Warehouse) are excluded.
3. **Name & keyword exclusions** — uncategorized rows whose name is on the
   exclude list or contains a whole-word term (IPA, stout, cider, junmai, port,
   tawny, vermouth, aszu, corkscrew, delivery…) are excluded. Whole-word
   matching keeps `port` from hitting Portugal and `aszu` from hitting dry Tokaji.

**Output:** `ingestion/output/combined.csv` (wines, with `ingest_pass` =
`category` | `uncategorized`), `excluded.csv` (every dropped row with
`excluded_by` + `excluded_reason`) and `summary.json` (the counts the
Ingest panel shows). Uncategorized wines are categorized by fermentation.

**Tech:** Python 3.11+, stdlib csv + tomllib — no network access needed.
Tests: `pytest ingestion/tests`.

See `ingestion/PLAN.md` for the column contract and the keyword calibration.

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

- **`searcher.py`** — owns the network for snippets. Ten web queries per
  wine through `ddgs` (Yahoo → Bing → DuckDuckGo): question-style, per-site
  (Wine-Searcher, Vivino, CellarTracker, Wine.com), UPC, distributor site and
  a fallback — see `SEARCH_QUERIES` in `constants.py`. Cross-query URL dedupe,
  near-duplicate and spliced-blob removal, boilerplate strip (including
  Vivino's per-region grape blurbs), blocked AI-content domains, price-only
  filter. → `list[Snippet]`.
- **`scorer.py`** — the LLM scores each snippet 0–100 for product match
  *and* lists the facts it states (`grape` / `region` / `producer`). Snippets
  go in batches of `SCORING_BATCH_SIZE` with their URL (the producer is often
  only in the slug), and any index the model leaves out of its reply is
  re-asked rather than silently scored 0 — that omission lost 28 % of matching
  snippets on the 2026-09-15 run. A **producer-absent hard gate** drops
  snippets that don't mention the producer name, and content gates drop
  Wine-Searcher pages that only echo the query and URLs naming another colour
  (a `…-blanc` page for a red). Of the survivors above
  `SNIPPET_MATCH_THRESHOLD` (70, the rubric's "very likely the same wine"
  band), the grape-naming, most-fact-rich ones fill `web_context` (score
  only gates identity) — or `None`, in which case the wine routes straight
  to `needs_review` and the tagger is skipped. Method and evidence:
  `journal/2026-09-15-SCORING.md`.
- **`evidence.py`** — mechanical checks on the tagger's output against the
  text it was shown (see "Confidence & review flags").
- **`tagger.py`** — drives the MCP tool-call loop. The model browses canonical
  countries/regions/grapes via `lookup_*`/`list_*`, then commits via
  `submit_tags`. `submit_tags` **is the canonicalization gate** — whatever it
  accepts is what gets written; there is no second normalization pass.

Supporting modules: `store.py` (read/write `output/wines.json`, manual edits,
export rows), `events.py` (progress events: human lines, or `--events-json`
JSON lines for Cellar, always appended to `events.jsonl`), `settings.py`
(`settings.json`, shared with Cellar), `paths.py` (the folder layout).

### The `library_mcp` server

A FastMCP **stdio server** (`fermentation/library_mcp/server.py`) backed by a
baked SQLite wine library (`library.db`, committed — nothing is fetched at
tag time). It currently holds 46 countries, 2,832 canonical regions and 555
canonical grapes, plus a placeholder tier (77 regions, 268 grapes) of real but
niche names that lookups recognise and `submit_tags` rejects.

The library is built by `seed/build_db.py` from hand-curated YAML allowlists
(`seed/allowlist/`: `countries.yaml`, `regions.yaml`, `grapes.yaml`, and
`qids.lock.yaml` pinning each entry to its Wikidata item). Regions — hierarchy,
classification, label spellings and their grapes — are authored in YAML;
Wikidata supplies grape synonyms and origins and the placeholder tier;
per-country Wikipedia parsers add region → grape edges. The regions and grapes
were filled in country by country by research agents (`seed/research/`: one
`<slug>.regions.yaml` / `.grapes.yaml` / `.md` per slice, merged into the
allowlists), then reconciled and checked against the locked Wikidata items.
Rebuild with `python -m fermentation.library_mcp.seed.build_db` (always from
scratch; `--offline` skips the network). Tool surface:

- Browse (read-only): `lookup_country`, `lookup_region`, `lookup_sub_regions`,
  `lookup_grape`, `list_countries`, `list_regions`, `list_grapes`.
- `lookup_sub_regions(region)` lists the canonical regions one level below a
  region (Langhe → Barbaresco, Barolo, …). The prompt tells the model to use
  it when it thinks the wine is from a sub-region but is not sure which, and
  to submit one only if a snippet names it.
- `lookup_grape` shows the grape's colour unless the developer switch
  *Grape colour in lookup_grape* (Ferment panel, `lookup_grape_color` in
  `settings.json`, `--no-grape-color` on the console) is off. Shown a red
  grape next to a rosé, the 7B has argued it out of the blend.
- Region names resolve leniently: when the exact name misses, the lookup
  drops classification words ("Barolo DOCG", "W.O. Stellenbosch") and tries
  each comma-separated part ("Swartland, Western Cape, South Africa"). The
  same region name may exist in two countries (La Rioja: Spain, Argentina);
  `lookup_region(name, country?)` and `submit_tags` pick by the wine's country.
- Terminal: `submit_tags(country, region[], grapes[], is_blend, organic, confidence, category?)`
  → `{ok, normalized}` on success, or `{ok:false, issues, hints}` so the model
  can correct and retry in-loop. Parent regions are filled in from the tree
  (`Russian River Valley` → Sonoma County → North Coast → California).

Why MCP instead of a bigger prompt or a post-hoc pass: synonyms collapse
upfront (Garnacha → Grenache), mismatches surface as a correctable tool failure,
and every lookup is captured in a structured transcript. See
`fermentation/PLAN.md` for the full rationale.

### LLM runtime

A single local model (default **Qwen2.5-7B-Instruct**, Q6_K GGUF) is hit at
**two points** — scoring and tagging — via an OpenAI-compatible
`/v1/chat/completions` endpoint. The tagger needs tool-call support: `gemma3n`
is still selectable (`LLAMA_MODEL=gemma`) but its chat template ignores `tools`
under llama.cpp, so it can't drive the MCP loop.

- **llama.cpp `llama-server`:** `http://localhost:8080/v1/chat/completions` (default;
  started from the Cellar top bar)
- **LM Studio (alternative):** `http://localhost:1234/v1/chat/completions` — pass `--api-url`

### Confidence & review flags

- A wine with no usable `web_context` (no snippets, or all dropped by the
  producer gate) is written as `needs_review` without ever calling the tagger.
- After tagging, `confidence < threshold` → `needs_review`. The threshold
  comes from CLI flag > `FERMENTATION_CONFIDENCE_THRESHOLD` > `settings.json`
  (saved from Cellar) > `DEFAULT_CONFIDENCE_THRESHOLD` (80) in `constants.py`.
- **Evidence rules** (`phases.apply_evidence_rules`, enforced in code, not
  just asked for in the prompt): a submitted grape that appears nowhere in
  `web_context` — by canonical name or any library synonym — routes the row
  to `needs_review` (`review_reasons: ["unsupported_grape:Cinsault"]` in
  `final/<id>.json`); when every snippet in context came from the same site,
  confidence is clamped to `SINGLE_SOURCE_CONFIDENCE_CAP` (69) and the row is
  routed to review (`review_reasons: ["single_source"]`). Sources are counted
  by family, so "Vivino #1" and "Vivino #2" are one source.
  A grape named by only one source (`uncorroborated_grape:<name>`), a blend
  with one known grape (`incomplete_blend`), a red or rosé with white grapes
  only (`white_grapes_only`), a region coarser than one the context
  names (`coarse_region:Barolo` when the model said Piedmont), a region
  whose longer name the context uses (`longer_region:Côte de Brouilly` when
  the model said Brouilly), and a region that nothing in the context or the
  product name names (`unsupported_region:<name>`) route to review too.
  Before those checks the gate upgrades the region itself when the product
  name names a finer one (`region_from_name:Piedmont→Barolo` for "Neirano
  Barolo") or exactly one finer region is named by at least as many sources
  (`region_from_sources:Brouilly→Côte de Brouilly`); for now those rows are
  routed to review as well (`REGION_UPGRADE_NEEDS_REVIEW`, temporary). One
  snippet naming a whole blend corroborates its grapes, unless it says the
  list is partial ("and touches of other grapes"); a single varietal needs
  only one source naming its grape, unless the context calls the wine a
  blend. A region named by one source does not outweigh the several that
  name the submitted one. Every review route
  records a reason, including `low_confidence`, `no_grapes`, `no_submit` and
  `no_context`; Cellar shows them on the wine's *Final* tab.
- **Category**: when the CSV has no `product_category`, the tagger submits
  one of `Red / White / Rose / Sparkling` from the snippets; the store keeps
  it (`category_source: "model"`, shown as *inferred* in Cellar) until the
  CSV supplies a real one. A CSV category is never overwritten.
- **Vintage is not checked.** The scorer treats a vintage the product name
  doesn't mention as missing information, not a conflict, so the context can
  come from a different year than the bottle. Grape blends are the field most
  exposed to this; the evidence rules above check that sources agree with each
  other, not that they describe the right vintage. A human check is still
  required (see the warning at the top).
- `organic` is set only when explicit certification language
  (`certified organic`, `biodynamic`, `certified biodynamic`) appears.
- Rows with `tag_status = 'human'` (edited in Cellar) are never overwritten on re-run.

### CLI flags

| Flag | Default | Description |
|------|---------|-------------|
| `--api-url` | llama.cpp (`:8080`) | LLM API URL (or `FERMENTATION_API_URL`) |
| `--model` | `qwen2.5-7b-instruct` | Model name (or `FERMENTATION_MODEL`) |
| `--confidence-threshold` | `settings.json`, else 85 | Min confidence to auto-accept |
| `--limit N` | 0 (all) | Process at most N wines (fresh runs only) |
| `--force` | off | Ignore saved run state; start a fresh run |
| `--input` | `ingestion/output/combined.csv` | Path to the input CSV |
| `--no-producer-gate` | off | Disable the producer-absent hard gate (debug) |
| `--phase P --run-id R` | — | Re-run from phase `search`/`score`/`tag` over run R's existing logs |
| `--stop-after P` | — | Pause once phase P finishes (Cellar's *Pause after each phase*); run again to continue |
| `--events-json` | off | One JSON event per line on stdout (what Cellar reads) |

### Resumability

After every wine, `output/.run_state.json` records `(run_id, phase, cursor)`.
Re-running (or pressing Run again in Cellar) resumes inside that phase;
`--force` starts a fresh run with a new run id. Ctrl-C / the Stop button
checkpoints cleanly.

### `output/wines.json`

```jsonc
{
  "version": 3, "generated_at": "…", "last_run_id": "20260915-132128", "source_csv": "…",
  "wines": [{
    "id": "…", "name": "…", "sku": "…", "category": "Red", "brand": null,
    "supply_price": 17.99, "retail_price": 25.99, "supplier": "Winebow",
    "country": "Spain", "region": ["Ribera del Duero", "Castilla y León"],
    "grapes": ["Tempranillo"], "is_blend": false, "organic": false,
    "confidence": 84, "web_context": "…", "tags_raw": "Spain; Ribera del Duero; …",
    "tag_status": "model",                // pending | model | needs_review | human
    "sales": {"items_sold": 81, "margin_pct": 0.31, "sale_count": 46, "customer_count": 29, "avg_sale_value": 29.5},
    "run_id": "20260915-132128", "tag_run_id": "20260915-132128",
    "phase_status": {"search": "ok", "score": "ok", "tag": "ok"},
    "created_at": "…", "updated_at": "…"
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

**Tech:** Python 3.11+, sqlite3, requests, `mcp` (FastMCP), `ddgs` web search,
PyYAML (library seed) — no paid APIs or keys required.
Tests: `pytest fermentation` (scorer, evidence rules, and the library's
allowlists, lookups and `submit_tags` gate).

> **Scoring methodology:** see `journal/2026-09-15-SCORING.md` for why
> the snippet score was rebuilt (batched per-index scoring, URL shown,
> facts-first context, threshold 70) and the evidence rules that gate the
> tagger's output. `journal/2026-09-15-ACCURACY.md` is the earlier
> per-wine accuracy review; `journal/2026-09-15-BATON.md` the library reseed.
> `journal/2026-09-27-RUN-COMPARE.md` covers the latest run and the review
> gate built from it. Every dated note (reviews, batons, run comparisons)
> lives in `journal/`, named `YYYY-MM-DD-TOPIC.md` so it sorts in the order
> it was written; `journal/README.md` indexes them. The journal is
> git-ignored — it exists only in the local checkout.

---

## Domain 3 — Distribution, and Cellar

**Run:** `./run.sh` → http://localhost:8000

`cellar/` is the web app (FastAPI backend in `cellar/server/app.py`, React +
Vite + TypeScript + Tailwind frontend in `cellar/web/`). It owns the
distribution step — browse, search, sort, edit tags (edits mark a wine
`human`, which fermentation never overwrites), and **Export** a
Lightspeed-compatible `.xlsx` with `id`, `name`, `tags` — and it also runs the
two upstream stages with live progress and a drill-down into every phase log.

Three tabs follow the pipeline: **Ingest** (upload an export, see what the
filters kept and excluded, and why), **Ferment** (start/stop/resume runs,
pause between phases, the confidence threshold) and **Distribute** (run
history, the wine table and export). Clicking a wine opens its snippets, scores, the tagger's full MCP
transcript and the *Final* tab with any review reasons; the tag editor offers
the library's canonical countries, regions and grapes. The top bar starts and
stops the llama-server. See `cellar/PLAN.md` for the API.

---

## Folder Structure

```
Wine Warehouse DDD/
├── README.md
├── PLAN.md
├── requirements.txt
├── run.sh                       # starts the Cellar dashboard
├── settings.json                (git-ignored) confidence threshold, written by Cellar
├── journal/                     (git-ignored) dated notes, YYYY-MM-DD-TOPIC.md (read newest first)
├── ingestion/
│   ├── PLAN.md
│   ├── ingest.py                # product-export CSV → filters → combined.csv
│   ├── filters.py · filters.toml   # the category / vendor / keyword rules
│   ├── fixtures/test-wines.csv  # the 24 development wines (with sales stats)
│   ├── tests/
│   ├── uploads/                 (git-ignored) exports dropped in the Ingest panel
│   └── output/                  (git-ignored) combined.csv · excluded.csv · summary.json
├── fermentation/                # active
│   ├── PLAN.md
│   ├── ferment.py               # CLI
│   ├── phases.py                # search → score → tag, each over all wines
│   ├── searcher.py · scorer.py · tagger.py · evidence.py
│   ├── store.py · events.py · settings.py · paths.py · types.py · constants.py
│   ├── tests/                   # offline scorer / evidence / category tests
│   └── library_mcp/
│       ├── server.py            # FastMCP stdio server
│       ├── schema.sql · library.db
│       ├── tests/               # allowlist, lookup and submit_tags tests
│       └── seed/
│           ├── build_db.py      # allowlists + Wikidata + Wikipedia → library.db
│           ├── resolve_qids.py  # pins allowlist entries to Wikidata items
│           ├── allowlist/       # countries · regions · grapes · qids.lock (YAML)
│           ├── research/        # per-country research slices + agent brief
│           └── wikipedia/       # per-country region → grape parsers
├── output/                      (generated) wines.json, .run_state.json, lightspeed-export.xlsx
├── logs/                        (generated) one folder per fermentation run
├── cellar/                      # the web app
│   ├── PLAN.md
│   ├── server/app.py            # FastAPI
│   └── web/                     # React + Vite + TypeScript + Tailwind
└── Sample Xlsx/                 (git-ignored) raw Lightspeed exports
    └── product-export-2026-09-16.csv
```
