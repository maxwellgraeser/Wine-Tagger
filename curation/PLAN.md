# Curation Domain

## Purpose

Take the clean CSVs from ingestion, look up each wine online to gather authoritative metadata, then use a locally-running Gemma model to turn that web context into structured tags (country, region, grapes, varietal/blend classification, organic status). Store everything in a SQLite database that serves as the single source of truth for the distribution layer.

## Inputs

From `ingestion/output/`:
- `combined.csv` -- single file containing product catalog columns and sales stats merged per row. Each row is one wine; sales columns are empty for products with no inventory match. Key columns: `id`, `name`, `sku`, `product_category`, `supply_price`, `retail_price`, `brand_name`, `supplier_name`, `items_sold`, `sale_count`, `margin_pct`, `customer_count`, `avg_sale_value`.

## Processing Steps

1. **Load CSV** into memory (pandas or stdlib csv).
2. **For each product, gather web snippets** from all curated sources in parallel (no early stop):
   - Query every source in `curation/sources.py` plus an unscoped fallback via DuckDuckGo.
   - Collect every snippet returned (multiple sources may hit).
3. **Phase 1 — LLM match scoring** (one LLM call per product):
   - Send all snippets to the LLM in a single prompt asking it to rate each snippet 0–100 for how well it matches the product name.
   - Wine abbreviations are expanded in this prompt (PN → Pinot Noir, SB → Sauvignon Blanc, etc.).
   - Snippets below `SNIPPET_MATCH_THRESHOLD` (default 65) are discarded.
4. **Phase 2 — LLM tag inference** (one LLM call per product):
   - Combine all passing snippets into a labeled context block (`[source | match=N]\n...`).
   - Ask the LLM to infer country, region, grapes, is_blend, organic, and confidence from this richer context.
   - Confidence rubric has hard limits: max 84 with a single source, max 69 if the producer name is absent.
5. **Parse the LLM response** into structured fields. Use a consistent prompt that requests JSON output to make parsing reliable.
6. **Write everything to SQLite** -- products, sales stats, and the new tags.

## Web Lookup

### Goal

Give the local model real-world context rather than asking it to guess from a product name alone. Multiple corroborating sources improve accuracy for obscure labels and guard against a single bad snippet inflating confidence.

### Approach (two-phase)

#### Phase 1 — gather and score

0. **UPC lookup (runs first when SKU is a barcode)** — if `sku` matches `^\d{8,14}$`, run site-scoped queries `site:{domain} "{sku}"` on all `upc_capable` sources in `curation/sources.py` (Wine Searcher, Vivino, CellarTracker), plus an unscoped `"{sku}" wine` fallback. Barcode hits tend to be exact matches and appear early in the scored list.
1. Build a site-scoped query for **every** source in `curation/sources.py`: `site:{domain} "{name}" {brand}`. Unlike the old approach, processing does **not** stop at the first hit — all sources are queried.
2. Add an unscoped fallback query `"{name}" {brand} wine region grapes` at the end.
3. Collect every snippet returned as individual results — up to `DDG_MAX_RESULTS` per source, each capped at `SNIPPET_CHAR_LIMIT` chars. Each DDG result is its own entry (labelled `Source #1`, `Source #2`, etc.) so the scoring LLM can rate them independently.
4. Send all snippets to the LLM in a **single batch match-scoring call**. The prompt instructs the model to expand common wine abbreviations (PN → Pinot Noir, SB → Sauvignon Blanc, Shiraz = Syrah, etc.) and rate each snippet 0–100 for how well it matches the product.
5. Discard snippets scoring below `SNIPPET_MATCH_THRESHOLD` (default **65**).

#### Phase 2 — context assembly

6. Take the top `TOP_N_SNIPPETS` (default **3**) surviving snippets by match score and combine them into a labeled context block:
   ```
   [Vivino | match=82]
   De Bortoli Noble One Botrytis Semillon is a luscious dessert wine...

   [Wine Searcher | match=71]
   Noble One from De Bortoli winery in Riverina, New South Wales...
   ```
7. Pass this context to the tag-inference LLM call (see LLM Integration below).
8. Cache the final assembled context string in `curation/output/web_cache.json` (keyed by product id). Re-runs use the cache directly, skipping both DDG and match scoring.

### Rate Handling

- Add a 0.5 s delay between DDG queries to be polite to public APIs.
- On DDG error, skip that source and continue.
- If **no** snippets pass the match threshold, `web_context` is `null`; the product is tagged from name alone and set to `tag_status = 'needs_review'`.

---

## LLM Integration

### Runtime

Ollama, exposing an OpenAI-compatible API at localhost.

- **Ollama:** `http://localhost:11434/v1/chat/completions` (default when running via `run.sh`)
- **llama.cpp fallback:** `http://localhost:8080/v1/chat/completions` (default in `constants.py` when invoking `curate.py` directly without the env var set)

Start Ollama with the `gemma3n` shell command (project root). `curate.py` accepts a `--api-url` flag or reads from `CURATION_API_URL` env var to override.

### Model

Gemma (`gemma3n:e4b` by default; override with `--model` or `CURATION_MODEL` env var).

### Prompt Strategy

#### Match-scoring call (Phase 1)

Sent once per product with all snippets bundled. The model returns a JSON object mapping snippet index to a 0–100 match score. Abbreviation expansion guidance is embedded in the prompt. Prompt text is defined as `BATCH_MATCH_SCORE_PROMPT` in `curation/constants.py`.

#### Tag-inference call (Phase 2)

Sent with the combined multi-source context assembled in Phase 1. Prompt text is defined as `PROMPT_TEMPLATE` (with a `STRICT_SUFFIX` appended on retry) in `curation/constants.py`.

```
You are a wine expert. Use the product information and the web context below to identify the wine's metadata.

Product name: {name}
Category: {category}
Brand: {brand}

Web context: {combined snippet block, or "none"}

Rules:
- is_blend is true if the wine contains more than one grape variety, false if it is a single varietal.
- organic is true only if the wine is certified organic, biodynamic, or explicitly marketed as certified biodynamic. Omit or set false if uncertain.
- If the web context contradicts the product name, trust the web context.
- confidence is an integer from 0 to 100 reflecting certainty that the tags are correct:
  - 90–100: two or more independent sources explicitly confirm producer, region, AND grape variety
  - 70–89:  one strong source confirms the producer name plus most key details
  - 50–69:  one source confirms region or grape but not both; or a weak match
  - 30–49:  no strong web source; details inferred from name and abbreviations only
  - 0–29:   no usable web context; pure guesswork
  Hard limits:
  * Max 84 if only one source contributed to your answer
  * Max 69 if the producer/brand name does not appear in any web snippet

Respond in JSON only — no explanation, no markdown fences:
{
  "country": "...",
  "region": "...",
  "grapes": ["...", "..."],
  "is_blend": true | false,
  "organic": true | false,
  "confidence": 0-100
}
```

### Rate & Error Handling

- Process wines sequentially (local model, no rate limits to worry about, but only one inference at a time).
- If the model returns unparseable output, retry once with a stricter prompt ("Return only raw JSON, no text before or after."). On second failure, flag the product for manual review (`tag_status = 'needs_review'`).
- After a successful parse, if `confidence < CONFIDENCE_THRESHOLD` (default **90** in `constants.py`; `run.sh` overrides to **75** via `CURATION_CONFIDENCE_THRESHOLD`; further override with `--confidence-threshold` CLI flag or env var), set `tag_status = 'needs_review'` even if parsing succeeded.
- `organic` is set to `true` only when the web snippet or model response contains the exact phrases `"certified organic"`, `"biodynamic"`, or `"certified biodynamic"`. All other signals are ignored.
- Log every response (prompt, raw response, parse result) to `tag_log`.

## SQLite Schema

Database file: `curation/output/wines.db`

```sql
CREATE TABLE products (
    id          TEXT PRIMARY KEY,  -- Lightspeed UUID
    name        TEXT NOT NULL,
    sku         TEXT,
    category    TEXT,              -- product_category from Lightspeed
    supply_price REAL,
    retail_price REAL,
    supplier    TEXT,
    brand       TEXT,
    country     TEXT,              -- from LLM
    region      TEXT,              -- from LLM
    grapes      TEXT,              -- JSON array, e.g. '["Cabernet Sauvignon","Merlot"]'
    is_blend    INTEGER,           -- 1 = blend, 0 = single varietal, NULL = unknown
    organic     INTEGER DEFAULT 0, -- 1 = certified organic/biodynamic, 0 = not/unknown
    confidence  INTEGER,           -- LLM certainty 0–100 (NULL if not yet tagged)
    web_context TEXT,              -- raw web snippet used as LLM input (NULL if none found)
    tags_raw    TEXT,              -- semicolon-separated tag string for Lightspeed
    tag_status  TEXT DEFAULT 'auto', -- 'auto' | 'needs_review' | 'reviewed' | 'manual'
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE sales (
    sku             TEXT PRIMARY KEY,
    product_id      TEXT REFERENCES products(id),
    items_sold      INTEGER,
    margin_pct      REAL,
    sale_count      INTEGER,
    customer_count  INTEGER,
    avg_sale_value  REAL,
    report_period   TEXT              -- date range of the source report
);

CREATE TABLE tag_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id  TEXT REFERENCES products(id),
    raw_prompt  TEXT,
    raw_response TEXT,
    parsed_ok   INTEGER,            -- 1 = success, 0 = failed to parse
    created_at  TEXT DEFAULT (datetime('now'))
);
```

### Notes on Schema

- `grapes` is stored as a JSON array string for flexibility (a wine can have multiple grapes).
- `is_blend` is a SQLite integer boolean (`1`/`0`); NULL means the model couldn't determine it.
- `organic` defaults to `0`; only set to `1` when the model finds explicit certification evidence.
- `confidence` is the LLM's self-reported certainty (0–100) about the metadata as a whole. Rows below `CONFIDENCE_THRESHOLD` (90 in `constants.py`, 75 when run via `run.sh`; override with `--confidence-threshold` flag or `CURATION_CONFIDENCE_THRESHOLD` env var) are automatically set to `tag_status = 'needs_review'`.
- `web_context` stores the raw snippet used as model input so you can audit why a tag was chosen. A non-NULL value here is the main driver of a high confidence score.
- `tags_raw` is the pre-computed semicolon-separated string ready for Lightspeed export, e.g. `France; Bordeaux; Cabernet Sauvignon; Merlot; Blend; Organic`. Single-varietal wines get `Single Varietal` instead of `Blend`; organic wines get `Organic` appended.
- `tag_status` tracks whether the tags were auto-generated, need human review, reviewed, or manually entered.
- `tag_log` preserves the raw LLM interaction (including the web snippet used) for debugging and prompt iteration.

## Grape Normalization Library (planned)

See `curation/LIBRARY.md` for the full spec. `grape_library.py` does not exist yet.

The module (`curation/grape_library.py`) will normalize LLM-returned grape names to canonical forms so that synonyms collapse to a single tag (e.g. Shiraz/Syrah → Shiraz, Pinot Grigio/Pinot Gris → Pinot Gris). It exposes:

- `normalize_grape(raw: str) -> str` — single grape, falls back to title-cased input for unknowns
- `normalize_grapes(raw: list[str]) -> list[str]` — list with deduplication after canonicalization

Integration point: call `normalize_grapes` inside `build_tags_raw` and `upsert_product` (before serializing to JSON) so both `grapes` (DB column) and `tags_raw` stay consistent.

## Output Contract

Downstream (distribution) reads from `wines.db` and expects:
- The `products` table with all columns above.
- The `sales` table joined on `product_id`.
- `tags_raw` is the canonical export field; downstream should not re-derive tags from individual columns.

## Tech

- Python 3.11+
- `sqlite3` (stdlib)
- `requests` for LLM API calls
- `ddgs` (`duckduckgo-search` package) for DuckDuckGo web lookups — gracefully skipped if not installed
- `web_cache.json` at `curation/output/web_cache.json` for search result caching (keyed by product id)
- `run.sh` — entry point script; sets Ollama defaults and installs `requests` if missing, then delegates to `curate.py`
- No paid external APIs or API keys required

## Decisions

All open questions have been resolved:

| # | Question | Decision |
|---|----------|----------|
| 1 | **Web search reliability** — what to do when DDG returns nothing | Attempt LLM inference from name alone (same as Decision 3), then automatically set `tag_status = 'needs_review'` regardless of confidence. |
| 2 | **Confidence threshold** | Default **90** in `constants.py`; `run.sh` overrides to **75**. Exposed as `--confidence-threshold` CLI flag and `CURATION_CONFIDENCE_THRESHOLD` env var so it can be adjusted without touching code. |
| 3 | **Private-label wines** (no useful web result) | Attempt LLM inference from name alone, then automatically set `tag_status = 'needs_review'` regardless of confidence. |
| 4 | **Organic evidence threshold** | Require **explicit wording** only: `"certified organic"`, `"biodynamic"`, `"certified biodynamic"`. Soft signals (`"natural"`, `"no added sulfites"`, `"low intervention"`) are not sufficient — `organic` stays `false`. |
| 5 | **Re-run behaviour** | Re-run re-tags all rows **except** those with `tag_status = 'manual'`. Rows with `'reviewed'`, `'needs_review'`, and `'auto'` are all eligible to be re-tagged. |
| 6 | **LLM calls per wine** | **Two**: one batch match-scoring call (rates all snippets), one tag-inference call (uses filtered context). |
| 7 | **Multi-source web lookup** | Query **all** curated sources, not just the first hit. Each DDG result is kept as a separate scored snippet (labelled `Source #N`) so individual results are rated independently. Discard snippets below match score **65** (`SNIPPET_MATCH_THRESHOLD`); pass the top **3** survivors (by score) to Phase 2 (`TOP_N_SNIPPETS`). |
| 8 | **Confidence hard limits** | Max 84 with a single source; max 69 if the producer name is absent from all snippets. Prevents inflated scores from weak evidence. |

## Batch-Review Mode

In addition to sequential processing, curation supports a **batch-review workflow** that pauses after every N wines so results can be inspected before continuing.

### CLI flags

```
--batch-size N    Process N wines, then pause for review before continuing.
                  Set to 0 (default) to run all wines without pausing.
--limit N         Process at most N wines total (0 = all). Useful for smoke-testing
                  a run without committing to the full catalog.
```

### Behaviour

1. Process wines one at a time (sequential LLM calls, as per decision 6).
2. After every `N` wines, print a summary of the batch to stdout:
   - Total processed, auto-tagged count, needs-review count, skipped (manual) count.
   - List of `needs_review` wines in the batch (id, name, confidence).
3. Prompt the user: **"Continue with next batch? [y/N]"**
   - `y` / `yes` → proceed with the next N wines.
   - Any other input (or EOF) → stop cleanly. The run state is saved to `curation/output/.run_state.json` (see Resumability below).
4. After the final batch (or after all wines if no pause was needed), print an overall summary and delete `.run_state.json`.

### Resumability

Interrupted runs (user declined to continue, or the process was killed) are resumed by re-running the exact same command. The mechanism:

1. **State file** — `curation/output/.run_state.json` records the `id` of the last successfully committed product and the cursor position (row index in the ordered product list). It is written after each wine is committed to `wines.db` and deleted on clean completion.

   ```json
   { "last_committed_id": "abc-123", "cursor": 42, "batch_size": 10 }
   ```

2. **On startup**, if `.run_state.json` exists and `--force` is not passed, the script reads `cursor` and skips the first `cursor` products in its ordered list — jumping straight to the next unprocessed wine. It prints: `"Resuming from product 43 of 500 (last committed: {name})"`.

3. **Normal re-run decision (Decision 5) is unaffected** — it only applies when no state file exists (i.e., a fresh run, not a resume). A fresh run still re-tags `'auto'`, `'needs_review'`, and `'reviewed'` rows, skipping only `'manual'`.

4. **`--force`** deletes `.run_state.json` and starts from row 0, re-tagging all eligible rows.

5. If the state file exists but `--batch-size` differs from the saved value, the script warns and asks the user to confirm before resuming (the cursor position is still valid; only the pause cadence changes).
