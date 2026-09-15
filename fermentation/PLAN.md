# Fermentation — Plan

The tagging domain: reads `combined.csv`, drives a local LLM through the MCP
wine library, and writes `output/wines.json`. The MCP library replaces any
post-hoc normalization pass.

`fermentation/` is self-contained.

---

## Implementation status

> **2026-09-15 — phased pipeline + JSON store.** The per-wine
> `search → score → tag` loop was replaced by three whole-set phases in
> `phases.py` (`run_search`, `run_score`, `run_tag`): all wines are searched,
> then all scored, then all tagged. Each phase writes one JSON per wine to
> `logs/<run_id>/{search,scorer,tagger,final}/` (always on; the old
> `--debug-output` / `debug_output.py` are gone), plus `run.json` and
> `events.jsonl`. The SQLite `wines.db` was replaced by `output/wines.json`
> (`store.py`); `output/.run_state.json` records `(run_id, phase, cursor)` so a
> run resumes inside a phase. `--phase P --run-id R` re-runs from a phase over
> an earlier run's logs. `--events-json` emits JSON-lines progress for the
> `cellar/` web app. `--batch-size` (interactive pause) was dropped — the web
> app's Stop button + resume covers that use. References to `wines.db` and
> `fermentation/output/` further down describe the previous design.

> Snapshot of what is actually in the tree vs. what this plan describes.
> Everything below "## Architecture" is the *design*; this section is the
> *reality*. See `Tree.html` at the repo root for a visual map and a
> severity-ordered findings list.

**Built and wired (Phases 1–5 core):**

- `ferment.py`, `searcher.py`, `scorer.py`, `tagger.py`, `types.py`,
  `constants.py`, `debug_output.py` — all present and integrated.
- `library_mcp/server.py` — FastMCP stdio server with all six browse tools
  plus `submit_tags` and its issue/hint codes.
- `library_mcp/seed/` — `build_db.py`, `sparql/*.rq`, Wikipedia parsers
  (`italy.py`, `germany.py`).
- `--no-producer-gate` is now wired (was a no-op in an earlier draft).
- `wines.db` schema: `region`/`grapes` stored as JSON-encoded TEXT arrays;
  `tag_log` stores the MCP transcript.

**NOT done — known gaps / bugs (fix before relying on a run):**

1. ~~DDG import mismatch (critical).~~ **Fixed 2026-09-15.** `searcher.py`
   imports `ddgs` (pinned in `requirements.txt`; the `duckduckgo_search`
   fallback was dropped because it warns on every query). A missing package
   now raises at import instead of silently yielding zero snippets.
2. ~~The "Reseed plan" below is UNBUILT.~~ **Built 2026-09-15.** Allowlist
   YAMLs, QID resolver + lock file, allowlist-driven `build_db.py`,
   placeholder pass, canonical-first server, and a test suite are in.
   `BATON.md` records what changed versus the first draft (every
   hand-typed QID in it was wrong) and how to re-seed.
3. **Confidence threshold is self-defeating.** `DEFAULT_CONFIDENCE_THRESHOLD
   = 90`, but `SYSTEM_PROMPT_MCP` caps confidence at 84 for single-snippet
   answers, and the producer gate + `SNIPPET_MATCH_THRESHOLD = 85` often
   leave a single surviving snippet. A correct single-source wine maxes at
   84 < 90 → forced `needs_review`. Lower the threshold (~80) or relax the
   cap; tune the two together.

**Not built (out of fermentation's current scope):**

- No `fermentation/run.sh` (Phase 4 cutover). Run via
  `python -m fermentation.ferment`.
- Tests cover `library_mcp` only (`fermentation/library_mcp/tests/`:
  allowlist validation, 24-wine coverage, server gate). `searcher` /
  `scorer` / `tagger` / `ferment` remain untested.
- No snippet cache (deliberate, per Risk #7 — but compounds bug #1: a
  throttled DDG run is indistinguishable from a clean all-`needs_review` run).

---

## Architecture

Four-file controller-and-modules split, plus a sibling MCP server package.

```
fermentation/
  ferment.py        # controller — CLI, DB, run-state, per-product orchestration
  searcher.py       # DDG queries, URL dedupe, snippet cleanup, web_context assembly input
  scorer.py         # LLM match-scoring, top-N trim, producer-absent hard gate
  tagger.py         # LLM tag inference via MCP tool loop; owns submit_tags consumption
  constants.py      # thresholds, prompts, source defs
  types.py          # shared dataclasses (Product, Snippet, ScoredSnippet, ParsedTags)
  debug_output.py   # write_search/scorer/tagger/final_output helpers; no-ops unless --debug-output
  library_mcp/
    __init__.py
    server.py       # FastMCP server, stdio transport (sketch already in tree)
    seed/           # one-shot Wikidata + Wikipedia ingest scripts
      sparql/       # .rq query files
      wikipedia/    # per-country list parsers
      build_db.py   # orchestrates seed → SQLite
    schema.sql      # canonical schema; checked in
    library.db      # baked-in SQLite, shipped with the server
```

### Module responsibilities

- **`searcher.py`** — owns the network for snippets. DDG queries, cross-query
  URL dedupe, boilerplate strip, price-only filter. Output: `list[Snippet]`.
- **`scorer.py`** — owns LLM-based match scoring (`batch_match_score`),
  applies the producer-absent hard gate, trims to top N. Output:
  `list[ScoredSnippet]` and an assembled `web_context` string (or `None` if
  nothing survived gating). **No snippet that fails the producer gate
  reaches the tagger** — this is a hard exclusion, not a confidence cap.
- **`tagger.py`** — owns LLM tag inference. Spawns the `library_mcp` stdio
  subprocess (once per run), drives the llama.cpp tool-call loop, returns
  the canonical `normalized` block from the last successful `submit_tags`.
- **`ferment.py`** — controller. CLI, CSV load, run-state, DB upsert,
  per-product pipeline `searcher → scorer → tagger → DB write`.

Dependency arrow is one-way: `ferment → {searcher, scorer, tagger}`. Modules
do not import each other. `scorer` receives raw snippets from `ferment`;
`tagger` receives the `web_context` string from `ferment`. The model/api_url
are passed in by `ferment`, so neither `scorer` nor `tagger` owns config.

---

## Build order

1. **Phase 1 — `library_mcp`.** Seed the SQLite library from Wikidata +
   Wikipedia, define the schema, implement the MCP tool surface
   (`lookup_*`, `list_*`, `submit_tags`). This blocks tagger.
2. **Phase 2 — `searcher.py` + `scorer.py` + `ferment.py` skeleton.** Can
   start in parallel with Phase 1; verifies the snippet pipeline against a
   no-op tagger that just writes raw `web_context`.
3. **Phase 3 — `tagger.py` with MCP tool loop.** Lands once Phase 1 ships
   a working server. Wires the full pipeline end-to-end.
4. **Phase 4 — Cut over.** Add a `run.sh` that points at
   `fermentation/ferment.py`.

---

## Phase 1 — `library_mcp`

### Why self-built

No single open-source package ships a clean, structured dataset of wine
regions, grapes, and countries together. Options that exist are either
hosted APIs (paid, key-required, young), web scrapers (ToS/licensing
concerns, messy product data), or computer-vision/agronomy datasets
(wrong kind of data). For a long-lived Wine Warehouse asset with full
ownership across all three axes, assembling a local dataset from public
structured sources is the right call.

### Seed sources

Two complementary tiers, both used.

**Wikidata — the backbone (machine-queryable).** Typed entities for
grape varieties, wine regions, and countries, all linked by properties
and queryable via SPARQL with JSON output. One query pulls every entity
that `wdt:P31 wd:Q10978` (grape variety) along with country of origin,
color, parent grapes. Wikidata assigns one stable QID per grape and
attaches synonyms as aliases — the QID is the primary key and the main
defense against duplication.

**Wikipedia structured lists — gap-fillers (richer, messier).** Fill
what Wikidata leaves sparse:

- List of grape varieties — columns for synonyms, origin, parentage
- List of wine-producing regions
- Per-country grape lists, denser (the Italian list is a clean
  Grape / Color / Region table)
- Per-country region lists, with real hierarchy (German regions nest as
  Anbaugebiet → Bereich → Großlage → Einzellage)

That nesting is the model to generalize for appellations.

### The synonym problem

Synonyms are everywhere and are the primary source of duplication. Bical
(white, Portuguese, from Bairrada) also appears as Arinto de Alcobaça,
Borrado das Moscas, etc. Without explicit synonym modeling, one grape
shows up as several. Keying on Wikidata QID rather than names solves
this.

### Schema (`library_mcp/schema.sql`)

| Table | Fields |
|---|---|
| `countries` | id, name, iso_code |
| `regions` | id, name, country_id, parent_region_id (self-ref), classification |
| `grapes` | id, canonical_name, color, species, origin_country_id, wikidata_qid |
| `grape_synonyms` | id, grape_id, synonym |
| `region_grapes` | region_id, grape_id (m:n; permitted/grown) |

Self-referencing `parent_region_id` represents appellation hierarchy.
SQLite recursive CTE handles "give me Barolo and everything under
Piedmont."

### Seed pipeline (`library_mcp/seed/build_db.py`)

1. **Countries.** SPARQL: every country with `wdt:P31 wd:Q6256`, name +
   ISO-3166-1 alpha-2. Write to `countries`.
2. **Grapes.** SPARQL on `wdt:P31 wd:Q10978` (grape variety) — fields:
   QID, label, color (`wdt:P462`), origin country (`wdt:P495`), aliases
   (via `skos:altLabel`). Write to `grapes` + `grape_synonyms`.
3. **Regions.** SPARQL on wine regions (`wdt:P31 wd:Q204754` and
   subclasses), country pin via `wdt:P17`, parent region via
   `wdt:P131`. Write to `regions`.
4. **Wikipedia enrichment.** Per-country grape and region list parsers
   (`seed/wikipedia/<country>.py`) fill missing synonyms and populate
   `region_grapes`. Pull the rendered HTML via the Wikipedia REST API,
   parse with BeautifulSoup. Skip rows where the linked Wikidata QID is
   absent — never insert un-keyed entries.
5. **Dedup.** Keyed on Wikidata QID. Any row that comes in twice merges
   (union of synonyms, prefer Wikidata canonical name).
6. **Bake.** Commit `library.db` to the repo. Server ships with data
   baked in; no runtime fetch.

Re-seeding is a deliberate dev action (re-run `build_db.py`, commit the
new `.db`).

### MCP tool surface

Browse tools (read-only):

| Tool | Returns | Use case |
|------|---------|----------|
| `lookup_country(name)` | `{canonical, iso, known}` | Model has a country string. |
| `lookup_region(name)` | `{canonical, country, parents[], known}` | Region → parent chain + pinned country. |
| `lookup_grape(name)` | `{canonical, color, origin, synonyms[], is_placeholder, known}` | Per-grape resolve; QID-aware so synonyms collapse. |
| `list_countries()` | `string[]` | ~30 names. |
| `list_regions(country?)` | `string[]` | Filtered by canonical country. |
| `list_grapes(country?, region?)` | `string[]` | Filtered browse. |

Terminal tool: **`submit_tags(country, region[], grapes[], is_blend, organic, confidence)`**.

Success:
```json
{
  "ok": true,
  "normalized": {
    "country": "Italy",
    "region": ["Valpolicella", "Veneto"],
    "grapes": ["Corvina", "Rondinella"],
    "is_blend": true,
    "organic": false,
    "confidence": 85
  }
}
```

Failure:
```json
{
  "ok": false,
  "issues": ["region_country_mismatch", "non_canonical_grape"],
  "hints": {
    "region_country_mismatch": "Your region resolves to a different country …",
    "non_canonical_grape": "These grape names aren't in the canonical list: ['Pin Blanc'] …"
  }
}
```

Issue codes: `placeholder_grapes`, `no_grapes`, `non_canonical_grape`,
`region_country_mismatch`, `country_in_region_slot`, `is_blend_mismatch`.

The library *is* the contract — the model cannot ship a row without the
server canonicalizing it. Whatever `submit_tags` emits is what
`ferment.py` writes to the DB; there is no second normalization pass.
Partial answers are accepted (e.g. country known, grapes unknown emits
`no_grapes` but the row may still proceed to `needs_review`).

### Why MCP and not a bigger prompt

Three options considered:

1. Dump canonical lists into the system prompt — prompt grows ~150
   lines, model still guesses at parent-region chains, no way to detect
   when it ignored the list.
2. A post-hoc `normalize_tags` step — every fixable mistake becomes a
   `needs_review` row.
3. MCP tools the model calls during inference — picked. Synonyms
   collapse upfront; mismatches surface as a tool-call failure the model
   can correct in-loop; structured transcript per lookup.

Trade-off: latency goes up (multi-turn loop) and we depend on llama.cpp
tool-calling working on the chosen model. Both are measurable; see
Risks.

### Licensing

Wikidata is CC0. Wikipedia text is CC BY-SA, but facts themselves
("Aglianico is a red grape from Campania") are not copyrightable.
Keeping the dataset to structured fields rather than copied descriptions
keeps it clean.

---

## Phase 2 — `searcher.py`

**Owns:** DDG queries, URL dedupe, boilerplate cleanup, price-only
filter. Single module that touches the network for snippets.

**Does not own:** scoring, gating, caching (no `web_cache.json` —
dropped), LLM calls.

### Public surface

```python
def gather_snippets(product: Product) -> list[Snippet]:
    """UPC + per-source + fallback queries with cross-query URL dedupe.
    Returns cleaned snippets (boilerplate stripped, price-only dropped)."""
```

### Internal helpers

- `_is_upc(sku)`
- `_ddg_snippets(query)`
- `_gather_all_snippets(product)` — orchestrates UPC + per-source + fallback
- `_clean_snippet_text(text)` — boilerplate phrase stripping
- `_is_price_only(text)`

### Out of `searcher.py`

- Producer/name verification — moves to `scorer.py` (it's a relevance
  judgment, not snippet hygiene).
- Web cache — dropped. Reruns re-hit DDG. If caching becomes necessary
  later, design a fresh mechanism.

---

## Phase 3 — `scorer.py`

**Owns:** LLM match-scoring, the producer-absent hard gate, top-N trim,
`web_context` assembly.

### Public surface

```python
def score_and_assemble(
    product: Product,
    snippets: list[Snippet],
    *,
    api_url: str,
    model: str,
) -> tuple[Optional[str], list[ScoredSnippet]]:
    """Score snippets, apply producer-absent hard gate, trim to top N,
    assemble web_context. Returns (web_context_or_None, scored_full_list).
    web_context is None if no snippet survived gating."""
```

### Producer-absent gate (hard exclusion)

Token-overlap check: significant tokens from `product.name`/`product.brand`
must appear in the snippet body. Snippets that fail are **dropped, not
zeroed**. If *every* snippet fails the gate, `score_and_assemble`
returns `(None, scored)` and the product flows straight to
`needs_review` without ever invoking the tagger.

The producer-absent check is a hard gate rather than a soft confidence
cap applied post-tagging, so it skips the expensive LLM tag-inference
call.

### Internal helpers

- `_batch_match_score(product, snippets, api_url, model)` — one LLM
  call, returns `{idx: score}`
- `_significant_tokens(text)` — accent-strip + stopword + min-length
- `_snippet_contains_any_token(body, tokens)`
- `_apply_producer_gate(snippets, product)` — returns the filtered list
- `_build_web_context(scored)` — top-N labeled block

---

## Phase 4 — `tagger.py`

**Owns:** the MCP subprocess lifecycle, the llama.cpp tool-call loop,
extraction of the authoritative `normalized` block from the last
successful `submit_tags`.

**Does not own:** snippet prep, scoring, DB writes.

### Public surface

```python
def infer_tags(
    product: Product,
    web_context: str,             # never None — ferment skips this call if it is
    *,
    api_url: str,
    model: str,
    mcp_session: MCPSession,
) -> tuple[Optional[ParsedTags], list[dict]]:
    """Drive the tool-call loop. Returns (normalized_or_None, transcript).
    None means: model never produced a successful submit_tags within
    MAX_SUBMIT_RETRIES — caller sets tag_status='needs_review'."""
```

### Server lifecycle

Spawn `library_mcp/server.py` once per `ferment.py` run as a stdio
subprocess inside a context manager. Not per-product.

### Tool-call loop

```python
MAX_ITERS = 8
MAX_SUBMIT_RETRIES = 3

messages = [system_prompt_mcp, user_prompt(product, web_context)]
last_ok_normalized = None
submit_failures = 0

for _ in range(MAX_ITERS):
    resp = post_llama(api_url, model, messages, tools=TOOL_SCHEMAS)
    msg = resp["choices"][0]["message"]
    messages.append(msg)
    calls = msg.get("tool_calls") or []
    if not calls:
        break
    for call in calls:
        result = mcp_session.call_tool(name, args)
        messages.append({"role": "tool", "tool_call_id": call["id"], ...})
        if name == "submit_tags":
            if result["ok"]:
                last_ok_normalized = result["normalized"]
            else:
                submit_failures += 1
                if submit_failures >= MAX_SUBMIT_RETRIES:
                    return None, messages
    if last_ok_normalized is not None:
        break

return last_ok_normalized, messages
```

### Prompt

Rather than "return JSON with fields …" instructions, use something
like:

> You have tools to look up canonical wine countries, regions, and
> grapes. Use `lookup_region` and `lookup_grape` when unsure about a
> spelling or synonym (Garnacha vs Grenache, Piemonte vs Piedmont).
> When you have your final answer, call `submit_tags`. If it returns
> `ok: false`, read `hints`, fix your submission, and call again. Do
> not reply with free-text JSON.

The prompt also includes an abbreviation guide, snippet ordering, and a
confidence rubric.

---

## Phase 5 — `ferment.py`

Controller. Responsibilities:

1. **CLI** — `--api-url`, `--model`, `--confidence-threshold`,
   `--batch-size`, `--force`, `--input`, `--limit`,
   `--no-producer-gate`, `--debug-output`.
2. **CSV load** — `load_products(path) → list[Product]`.
3. **Run state** — `load_run_state` / `save_run_state` /
   `clear_run_state`.
4. **DB** — `open_db`, `upsert_product`, `upsert_sales`, `log_tag`,
   `is_eligible`. Schema may change to match `submit_tags` output (see
   DB note below).
5. **Per-product pipeline:**

```
with library_mcp_session() as mcp:
    for product in products[start_cursor:]:
        if not is_eligible(conn, product):
            save_run_state(...); continue

        snippets = searcher.gather_snippets(product)
        web_context, scored = scorer.score_and_assemble(
            product, snippets, api_url=..., model=...,
        )

        if web_context is None:
            # producer-absent: hard skip tagging
            upsert_product(conn, product, None, None, tag_status='needs_review')
        else:
            normalized, transcript = tagger.infer_tags(
                product, web_context, api_url=..., model=..., mcp_session=mcp,
            )
            log_tag(conn, product.id, transcript, ok=normalized is not None)
            tag_status = decide_tag_status(
                normalized=normalized,
                confidence_threshold=args.confidence_threshold,
            )
            upsert_product(conn, product, normalized, web_context, tag_status)

        upsert_sales(conn, product)
        conn.commit()
        save_run_state(product.id, idx + 1, args.batch_size)
```

6. **Batch summary + pause loop.**

### Helpers in `ferment.py`

- `decide_tag_status(normalized, confidence_threshold)` — small,
  readable, unit-testable. Precedence: missing normalized →
  `needs_review`; confidence < threshold → `needs_review`; else
  `auto`.
- `organic_confirmed(web_context, normalized)` — explicit-phrase check
  (carried over) if still needed for the DB write path.
- `build_tags_raw(normalized)` — DB tag-string assembly.

Note: there is **no** post-tagger `normalize_tags` call and **no**
producer-absent confidence cap in `ferment.py`. The MCP `submit_tags`
output is authoritative; the producer-absent check already gated the
input.

---

## Debug Output Mode (`fermentation/debug_output.py`)

Add `--debug-output` flag to `ferment.py`. When set, each pipeline stage writes
a persistent JSON file per product into `fermentation/output/`. All helpers
live in `debug_output.py` and no-op if `--debug-output` is not set, so there
is zero overhead in normal runs.

### Folder layout

```
fermentation/output/
  search/     # raw snippets from searcher, before scoring
  scorer/     # scored + gated snippets and assembled web_context
  tagger/     # MCP tool-call transcript
  final/      # normalized block written to DB (or null) + tag_status
```

File naming: `{product_id}_{sku}.json` — overwrites on rerun so you always see
the latest result.

### File shapes

**`output/search/{id}.json`** — raw output of `searcher.gather_snippets`:
```json
{
  "product_id": "abc123",
  "query_count": 4,
  "raw_snippet_count": 12,
  "snippets": [
    {"source": "vivino", "domain": "vivino.com", "body": "...", "url": "..."}
  ]
}
```

**`output/scorer/{id}.json`** — output of `scorer.score_and_assemble`:
```json
{
  "product_id": "abc123",
  "input_count": 12,
  "producer_gate_dropped": 3,
  "scored_snippets": [
    {"source": "vivino", "body": "...", "match_score": 87, "dropped_reason": null},
    {"source": "wine-searcher", "body": "...", "match_score": 34, "dropped_reason": "producer_absent"}
  ],
  "web_context_built": true,
  "web_context": "..."
}
```

**`output/tagger/{id}.json`** — MCP tool-call transcript from `tagger.infer_tags`:
```json
{
  "product_id": "abc123",
  "tool_calls": [
    {"tool": "lookup_grape", "args": {"name": "Garnacha"}, "result": {"canonical": "Grenache", "known": true}},
    {"tool": "submit_tags", "args": {}, "result": {"ok": false, "issues": ["non_canonical_grape"], "hints": {}}},
    {"tool": "submit_tags", "args": {}, "result": {"ok": true, "normalized": {}}}
  ],
  "submit_attempts": 2,
  "success": true
}
```

**`output/final/{id}.json`** — what was written to the DB:
```json
{
  "product_id": "abc123",
  "tag_status": "auto",
  "normalized": {
    "country": "Spain",
    "region": ["Priorat"],
    "grapes": ["Grenache", "Carignan"],
    "is_blend": true,
    "organic": false,
    "confidence": 88
  }
}
```

### Write helpers in `debug_output.py`

- `write_search_output(product, snippets)` — called in `ferment.py` after `gather_snippets`
- `write_scorer_output(product, scored, web_context)` — called after `score_and_assemble`
- `write_tagger_output(product, transcript)` — called after `infer_tags`
- `write_final_output(product, normalized, tag_status)` — called after `upsert_product`

All four accept an `enabled: bool` parameter (bound to `--debug-output`) and
return immediately if `False`.

---

## Shared types (`fermentation/types.py`)

```python
@dataclass
class Product:
    id: str; name: str; sku: Optional[str]; brand: Optional[str]
    category: Optional[str]; supply_price: Optional[float]
    retail_price: Optional[float]; supplier: Optional[str]
    items_sold: Optional[int]; margin_pct: Optional[float]
    sale_count: Optional[int]; customer_count: Optional[int]
    avg_sale_value: Optional[float]

@dataclass
class Snippet:
    source: str; domain: str; body: str; url: str

@dataclass
class ScoredSnippet:
    snippet: Snippet
    match_score: int
    cleaned_body: str
    dropped_reason: Optional[str] = None   # "producer_absent" | None

@dataclass
class ParsedTags:
    """Mirror of submit_tags 'normalized' block."""
    country: Optional[str]
    region: list[str] = field(default_factory=list)
    grapes: list[str] = field(default_factory=list)
    is_blend: Optional[bool] = None
    organic: Optional[bool] = None
    confidence: Optional[int] = None
```

---

## Constants

`fermentation/constants.py` holds no post-hoc normalization knobs (there
is no `PRODUCER_ABSENT_CONFIDENCE_CAP` — the gate is hard). `searcher.py` imports snippet-related
constants; `scorer.py` imports the scoring prompt + producer-gate
thresholds; `tagger.py` imports the MCP prompt; `ferment.py` imports
orchestration-level (`DEFAULT_CONFIDENCE_THRESHOLD`,
`ORGANIC_PHRASES`).

---

## DB / `wines.db`

Schema is open for changes. Align column shape with `submit_tags`
output (e.g. region stored as JSON array or a join table rather than a
delimited string, if cleaner). No migrations — fermentation starts a
fresh `wines.db`.

---

## Risks & open questions

| # | Risk / Question | Notes |
|---|-----------------|-------|
| 1 | llama.cpp tool-calling quality is model-dependent | Smaller/older quants skip tools and emit JSON anyway. Fallback (needs_review on no-submit) must be solid before ship. |
| 2 | Latency cost of multi-turn inference | Single-shot tagging: one POST per product. MCP: 4–6 round-trips. Benchmark before celebrating. |
| 3 | MCP subprocess robustness | If the server crashes mid-run, the batch stalls. Add healthcheck + restart in `ferment.py`, or accept and document the failure mode. |
| 4 | Hard producer gate may over-exclude | A soft cap would only lower confidence; fermentation drops snippets outright. Sample the `needs_review` rate during phase 2 and revisit the gate's token-match threshold if too aggressive. |
| 5 | Wikidata coverage gaps | Some niche grapes/regions have thin Wikidata entries. Wikipedia enrichment exists to backfill, but expect a residual `unknown` rate. Track during Phase 1 validation. |
| 6 | Re-seed cadence | `library.db` is baked. New grapes/regions require a re-run of `build_db.py` and a new commit. Accept; document as a dev op. |
| 7 | No snippet cache | Reruns are expensive (DDG + politeness delay). Acceptable for now; revisit if iteration cost hurts. |
| 8 | `submit_tags` partial-answer policy | Sketch accepts partial (country known, grapes unknown → `no_grapes` issue, row proceeds to needs_review). Confirm during Phase 1 build. |

---

## Out of scope

- Async/parallel DDG queries (politeness delay stays).
- Async/parallel MCP tool dispatch within a single response.
- Exposing `library_mcp` to other MCP clients (Claude Desktop, Cursor).
  Server is namespace-clean enough to do this later; not a v1 concern.
- Constrained decoding / GBNF grammars. Possible fallback if
  tool-use compliance is poor (see Risk #1).
- Replacing the snippet-scoring LLM call in `scorer.py` with anything
  fancier (cross-encoder, embedding similarity). Single-shot LLM
  scoring stays.
- A second-pass LLM review of flagged rows, unless explicitly pulled into
  a later phase here.

---

## Post-build loose ends

Captured after the Wave 1–4 agent build. Address before runtime smoke
test / cutover.

1. **`requirements.txt`** — add `beautifulsoup4` (used by
   `library_mcp/seed/wikipedia/*`). `mcp` and `requests` already present.
2. **`--no-producer-gate` flag is currently a NO-OP** in `ferment.py`.
   The flag parses and prints a stderr warning, but the gate still
   fires. To wire it: add `producer_gate: bool = True` kwarg to
   `scorer.score_and_assemble`, skip `_apply_producer_gate` when False,
   and pass `producer_gate=not args.no_producer_gate` from ferment.
3. **Wikipedia parser deviation** — `seed/wikipedia/*.py` modules return
   a `ParsedCountry` dataclass (with `.country`, `.grapes`, `.regions`,
   `.region_grapes`) instead of the spec'd
   `{"grapes": ..., "regions": ..., "region_grapes": ...}` dict.
   Functionally equivalent and arguably better-typed; `build_db.py` is
   already wired to it. Spot-check Italian `region_grapes` (204 rows
   landed) before relying on it.
4. **Region SPARQL is narrow** — current `wdt:P31/wdt:P279* wd:Q204754`
   yielded only 36 regions in the baked `library.db`. Many wine regions
   on Wikidata are typed as country-specific classes (e.g. `Q1330099`
   "wine region of France"). Broaden the query (union over the known
   wine-region subclasses) and re-run `build_db.py`.

---

## Reseed plan — Hybrid allowlist + filtered firehose

The first seed pass (`build_db.py` v1) treated Wikidata as a firehose:
every `Q958314` (grape) landed, every `Q6256` (country) landed. Result
was 1672 grapes — most of them American hybrids, table grapes, raisin
varieties, lab crossings (`Salem`, `Cottage`, `Mars grape`,
`Diana Hamburg`, `Jaeger 70`) — 213 countries including historical
states (`Pahlavi Iran`, `Principality of Waldeck`), and 36 regions. Of
the 1672 grapes, 1671 had no color, 1310 no origin, 0 had species.
That's not a wine reference, it's noise.

This section supersedes the SPARQL files and `build_db.py` flow above.
Schema additions are additive; existing tables stay.

### Two tiers: canonical + placeholder

- **Canonical tier** — entries on a checked-in allowlist. Quality is
  human-reviewed; these are what `submit_tags` validates against and
  what `list_*` returns by default.
- **Placeholder tier** — long-tail entries from a *filtered* Wikidata
  pass (vinifera-only / wine-use only). Resolves obscure snippet
  mentions via `lookup_*` but flagged `is_placeholder=true` so the
  tagger is steered toward canonical names.

The existing `is_placeholder` field on `lookup_grape` becomes
load-bearing.

### Schema bumps

```sql
ALTER TABLE grapes    ADD COLUMN is_canonical INTEGER NOT NULL DEFAULT 0;
ALTER TABLE regions   ADD COLUMN is_canonical INTEGER NOT NULL DEFAULT 0;
ALTER TABLE countries ADD COLUMN is_canonical INTEGER NOT NULL DEFAULT 0;

CREATE TABLE region_synonyms (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id  INTEGER NOT NULL REFERENCES regions(id) ON DELETE CASCADE,
    synonym    TEXT    NOT NULL,
    UNIQUE (region_id, synonym)
);
CREATE INDEX idx_region_synonyms_nocase
    ON region_synonyms (synonym COLLATE NOCASE);
```

`region_synonyms` is the missing twin of `grape_synonyms` — handles
Piemonte/Piedmont, Bourgogne/Burgundy, and the
`Emilia-Romagna` / `Emilia Romagna` duplication observed in the v1 db.

### Allowlist files

Three YAMLs under `library_mcp/seed/allowlist/`. Each entry is
minimal — QID plus optional overrides. Wikidata supplies the rest.

```yaml
# grapes.yaml — target ~400–600 entries
- qid: Q146045
  name: Sangiovese                              # override label only if needed
  color: red                                    # override only if Wikidata is wrong/missing
  synonyms: [Brunello, Prugnolo Gentile]        # appended; Wikidata altLabels also flow in

# countries.yaml — ~50 wine-producing countries (OIV-aligned)
- qid: Q38
  iso: IT

# regions.yaml — ~300 entries, hierarchy via parent_qid
- qid: Q43417
  name: Piedmont
  country_qid: Q38
  classification: null
  synonyms: [Piemonte]
- qid: Q272561
  name: Barolo
  country_qid: Q38
  parent_qid: Q43417
  classification: DOCG
```

Why YAML, not Python: PR-reviewable, no code execution at load time,
machine-validatable. CI step: every QID must resolve on Wikidata at
build time, otherwise the build fails — catches typos and moved QIDs.

### Targeted SPARQL (replaces the three `.rq` files)

`VALUES`-bound queries fetch exactly the allowlist QIDs in one
round-trip per entity type:

```sparql
SELECT ?entity ?entityLabel ?colorLabel ?origin ?originLabel
       (GROUP_CONCAT(DISTINCT ?alt; SEPARATOR="||") AS ?synonyms)
WHERE {
  VALUES ?entity { wd:Q146045 wd:Q272561 ... }
  OPTIONAL { ?entity wdt:P462 ?color }
  OPTIONAL { ?entity wdt:P495 ?origin }
  OPTIONAL { ?entity skos:altLabel ?alt . FILTER(LANG(?alt)="en") }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
GROUP BY ?entity ?entityLabel ?colorLabel ?origin ?originLabel
```

Same shape for countries (ISO via P297) and regions (parent via P131).
All allowlist rows land with `is_canonical=1`.

### Placeholder pass (optional fourth ingest step)

After canonical ingest, an opt-in pass pulls long-tail grapes filtered
to **both**:

- `wdt:P31/wdt:P279* wd:Q10978` (grape variety), **and**
- `wdt:P225 "Vitis vinifera"` (species) **or** `wdt:P366 wd:Q282`
  (has use: wine).

Insert with `is_canonical=0`. Skip QIDs already present from the
canonical pass. This filter drops `Salem`, `Cottage`, `Mars grape`,
`Diana Hamburg`, `Jaeger 70` — none of which are vinifera or
wine-use-tagged.

Equivalent placeholder pass for regions: filter to wine-region
subclasses (the loose-end #4 broadening), QIDs not in allowlist land as
placeholders. Countries do not get a placeholder pass — the ~50 OIV
list is exhaustive enough.

### Wikipedia parsers — QID-aware

The current Italian/German parsers match grapes and regions by
`name COLLATE NOCASE`. Rewrite to extract Wikidata QIDs from `<a>` tags
in the Wikipedia REST HTML (carries `data-wikidata-item-id` on linked
entities), and join on QID first. Name-match becomes a fallback only.

This stops parsers from minting new region rows that compete with
allowlist canonicals (the v1 source of `Emilia Romagna` /
`Emilia-Romagna` divergence).

### MCP surface impact

- `lookup_grape` / `lookup_region` / `lookup_country` resolve canonical
  first; placeholders surface only when the search term explicitly hits
  one. Return `is_placeholder: true` for those (field already in spec).
- `submit_tags` issue code `non_canonical_grape` already exists. Add
  `non_canonical_region`. Placeholders cannot pass `submit_tags`
  cleanly — the LLM is forced to canonicalize via the hint loop.
- `list_*` returns canonical only. No wire-shape change.

### Phasing

1. Schema migration: add `is_canonical` columns + `region_synonyms`
   table.
2. Allowlist scaffolding: empty YAMLs + loader + QID validator.
3. Populate allowlists — the bulk of the human work. Sources:
   OIV country list; Jancis Robinson / Wine Grapes for the canonical
   grape vocabulary; per-country DOCG/AOC/AVA region lists.
4. Rewrite `ingest_countries` / `ingest_grapes` / `ingest_regions` to
   consume allowlists via `VALUES`-bound SPARQL. Drop the firehose
   queries.
5. Update Wikipedia parsers to be QID-aware. Re-validate Italian
   `region_grapes` (204 rows today).
6. Filtered placeholder pass. Ship-blocker only if canonical coverage
   proves insufficient in tagger trials.
7. Update `lookup_*` / `submit_tags` to enforce canonical-first
   resolution.

### Open calls

- **Grape allowlist size.** 400–600 covers ~99% of commercial wine.
  Tighter (~150) is viable if the placeholder pass picks up the rest;
  decide before step 3.
- **Region hierarchy authority.** Wikidata `P131` is administrative,
  not viticultural (Barolo `P131` → Piedmont, but the wine relationship
  is tighter than the admin one). Allow `parent_qid` in `regions.yaml`
  to override P131 for the top ~50 nested regions.
- **Re-seed cadence stays a dev op.** Re-run `build_db.py`, commit the
  new `library.db`. No runtime fetch (unchanged from v1 PLAN).

### Revisions made while executing (2026-09-15)

Everything above in this section is the *intended* design; the build
diverges from it in these specific ways, each forced by what Wikidata
actually contains. `BATON.md` has the longer rationale.

- **Allowlists keyed by name; QIDs machine-resolved into
  `allowlist/qids.lock.yaml`.** Every hand-typed QID in the first draft
  pointed at the wrong entity. `seed/resolve_qids.py` does batched
  entity search through the SPARQL MWAPI service and records label +
  description per pick for review; `qid:` in a YAML entry overrides it.
- **Region QIDs optional.** Hierarchy, country and classification are
  authored in `regions.yaml`; Wikidata's typing of wine regions is too
  inconsistent (wine / valley / commune / AVA / AOC) to be load-bearing.
  Grape QIDs remain mandatory (and are checked to be `grape variety`).
- **Colour authored in `grapes.yaml`** — Wikidata P462 exists on 2 grapes.
- **Placeholder filter is "has an enwiki article"**, not
  `P225 "Vitis vinifera"` (which is a taxon-name property and matches
  nothing useful). ~680 grapes qualify. Regions: `wine-producing region`
  + `AVA` subclasses with an enwiki article, pinned to an allowlisted
  country.
- **Wikipedia parsers resolve by name/synonym and never mint rows**
  (Parsoid HTML has no QIDs on anchors). That, not QID-awareness, is
  what stops the duplicate-region problem.
- **`submit_tags` semantics tightened.** Unknown regions/countries are
  issues (`unknown_region`, `unknown_country`), placeholders are issues
  (`non_canonical_region`, `placeholder_grape`), `placeholder_grapes`
  became `phrase_grapes`, hints list the offending values, regions are
  expanded to their parent chain, and country is inferred from regions
  when omitted. `lookup_grape` returns `is_phrase` + `is_placeholder`.
- **`country_synonyms` table added** alongside `region_synonyms`;
  ISO codes resolve as country names.
- **Server uses in-memory folded indexes** (no per-miss table scans).
- **No migrations**: `build_db.py` rebuilds into a temp file and renames.

Built 2026-09-15: 46 countries; 675 canonical + 275 placeholder regions;
335 canonical + 375 placeholder grapes; 48 tests green. Counts and the
re-seed procedure live in `BATON.md`.

### Coverage notes — `library_mcp/tests/fixtures/combined.csv`

The 24-wine test set exercises the plan as follows:

- **Countries** — 8 distinct (USA, France, Italy, Spain, Portugal,
  South Africa, Argentina, Lebanon). All canonical under the OIV-aligned
  ~50-entry country allowlist. No placeholder territory.
- **Grapes** — ~25 distinct, of which the canonical core covers Pinot
  Noir, Tempranillo, Sauvignon Blanc, Chardonnay, Grenache, Syrah,
  Carignan, Cinsault, Malbec, Nebbiolo, Gamay, Pinot Gris, Negroamaro,
  Greco Bianco, Touriga Nacional, Castelão, Cabernet
  Sauvignon/Franc, Merlot, Picpoul. Synonym layer earns its keep on:
  `Aragonez → Tempranillo`, `Tinto Fino → Tempranillo`,
  `Pinot Grigio → Pinot Gris`, `Picpoul ↔ Piquepoul`. The Basque
  `Hondarrabi Zuri` / `Hondarrabi Beltza` (Urruzola Txakolina) were
  promoted to canonical during the build — they are on a stocked label,
  which is the whole test for inclusion. The placeholder tier is
  exercised by the test suite against whatever the pass produces.
- **Regions** — most concentrated work. Solidly canonical in any
  reasonable 300-region list: Napa, Ribera del Duero, Rioja, Barolo,
  Veneto, Côtes du Roussillon, Touraine, Brouilly, Willamette Valley,
  Mendoza, Constantia, Robertson, Paarl. Borderline (depth-dependent):
  Picpoul de Pinet, Lisboa, Salice Salentino, Cirò DOC, Getariako
  Txakolina, delle Venezie. Should be canonical despite IGP/single-region
  status: **Pays d'Oc** (volume), **Bekaa Valley** (Lebanon's only
  serious region), **Alenquer** (otherwise Chocapalha pins to Lisboa).

Two refinements this surfaces, not previously in the plan:

1. **High-volume IGP branch.** `regions.yaml` should explicitly carve
   space for Pays d'Oc, Vin de France, IGP Côtes de Gascogne, IGT
   Toscana — high-retail-volume non-appellation regions. Not
   prestigious, but represent meaningful chunks of US wine retail.
2. **Single-region floor.** If a country is on the allowlist, its top
   1–3 regions land canonical regardless of global rank: Lebanon →
   Bekaa; Greece → Nemea, Santorini; Lebanon → Bekaa; Uruguay →
   Canelones. Prevents the "country known, region placeholder"
   degenerate case.

**Runtime resolution stays local.** `lookup_grape` /
`lookup_region` / `lookup_country` query the baked SQLite only — three
passes (canonical name → synonym → accent-folded canonical), no
network. The placeholder tier expands what resolves locally; it does
not add runtime fetches. A grape entirely absent from the seed returns
`known: false` and the tagger handles it as "unknown" — there is no
live Wikidata fallback. CI smoke test should resolve every grape and
region implied by `library_mcp/tests/fixtures/combined.csv` against `library.db`
after a build, with at most the documented placeholder set returning
`is_placeholder: true`.
