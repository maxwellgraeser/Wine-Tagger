# Curation Domain

## Purpose

Take the clean CSVs from ingestion, look up each wine online to gather authoritative metadata, then use a locally-running Gemma model to turn that web context into structured tags (country, region, grapes, varietal/blend classification, organic status). Store everything in a SQLite database that serves as the single source of truth for the distribution layer.

## Inputs

From `ingestion/output/`:
- `combined.csv` -- single file containing product catalog columns and sales stats merged per row. Each row is one wine; sales columns are empty for products with no inventory match. Key columns: `id`, `name`, `sku`, `product_category`, `supply_price`, `retail_price`, `brand_name`, `supplier_name`, `items_sold`, `sale_count`, `margin_pct`, `customer_count`, `avg_sale_value`.

## Processing Steps

1. **Load CSV** into memory (pandas or stdlib csv).
2. **For each product, perform a web lookup** to gather raw context about the wine before calling the LLM:
   - Search using the product name (and brand/supplier where available) via DuckDuckGo Instant Answer (free, no API key required).
   - Extract the top result's description / fact sheet snippet (producer, region, grapes, organic/biodynamic mentions).
   - Store the raw snippet for the prompt and for the `tag_log`.
3. **For each product, call the local LLM** with the wine's name *and* the web snippet to infer:
   - `country` -- country of origin (e.g. `France`, `USA`, `Spain`)
   - `region` -- wine region (e.g. `Bordeaux`, `Napa Valley`, `Ribera del Duero`)
   - `grapes` -- grape varieties (e.g. `["Cabernet Sauvignon", "Merlot"]`)
   - `is_blend` -- `true` if multiple grapes, `false` if single varietal
   - `organic` -- `true` if the wine is certified organic/biodynamic/natural, otherwise omit / `false`
   - `confidence` -- integer 0–100 reflecting how certain the model is about the metadata as a whole (100 = definitive web evidence, 0 = pure guess from name alone)
4. **Parse the LLM response** into structured fields. Use a consistent prompt that requests JSON output to make parsing reliable.
5. **Write everything to SQLite** -- products, sales stats, and the new tags.

## Web Lookup

### Goal

Give the local model real-world context rather than asking it to guess from a product name alone. A single web snippet per wine dramatically improves accuracy for obscure labels.

### Approach

1. Build a site-scoped search query for each source in `curation/sources.py` (checked in priority order): `site:{domain} "{name}" {brand}`. The `CURATED_SOURCES` list covers Jeb Dunnuck, James Suckling, Vinous, Robert Parker Wine Advocate, and Wine Enthusiast — each with its domain.
2. Hit the DuckDuckGo Instant Answer API (free, no API key required) with each site-scoped query in turn; stop at the first source that returns a meaningful snippet.
3. Take the first meaningful text snippet (≤ 400 chars). If none of the curated sources returns anything useful (e.g. the product is a private label), fall back to an unscoped query `"{name}" {brand} wine region grapes` before giving up.
4. If still nothing useful for a **known label**, set `web_context` to `null` and let the model do its best from the name alone — then mark `tag_status = 'needs_review'` regardless of confidence (private-label / unknown wine path).
   If DDG itself errors or returns no results at all (total lookup failure), skip LLM inference entirely and immediately set `tag_status = 'needs_review'`.
5. Cache results in a local file (`curation/output/web_cache.json`, keyed by product id) so re-runs don't hit the network for already-looked-up wines.

### Rate Handling

- Add a short delay (0.5 s) between lookups to be polite to public APIs.
- On HTTP error, retry once, then proceed with `web_context = null`.

---

## LLM Integration

### Runtime

Either Ollama or LM Studio, both exposing an OpenAI-compatible API at localhost.

- **Ollama:** `http://localhost:11434/v1/chat/completions`
- **LM Studio:** `http://localhost:1234/v1/chat/completions`

The script should accept a `--api-url` flag or read from an env var so it works with either runtime.

### Model

Gemma (likely `gemma2:9b` or similar). The prompt should be tuned for this model's strengths.

### Prompt Strategy

For each wine, send the name, available catalog fields, and the web snippet (if any) and ask for structured output:

```
You are a wine expert. Use the product information and the web context below to identify the wine's metadata.

Product name: {name}
Category: {category}
Brand: {brand}
Web context: {web_context or "none"}

Rules:
- is_blend is true if the wine contains more than one grape variety, false if it is a single varietal.
- organic is true only if the wine is certified organic, biodynamic, or explicitly marketed as natural/organic. Omit the field (or set false) if uncertain.
- If the web context contradicts the product name, trust the web context.
- confidence is an integer from 0 to 100 reflecting your overall certainty about this wine's metadata:
  - 90–100: strong web evidence confirmed the wine's details
  - 60–89: partial web evidence; some fields inferred
  - 30–59: web context was vague or absent; mostly inferred from the name
  - 0–29: little or no usable information; high chance of error

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
- After a successful parse, if `confidence < CONFIDENCE_THRESHOLD` (default 75), set `tag_status = 'needs_review'` even if parsing succeeded.
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
- `confidence` is the LLM's self-reported certainty (0–100) about the metadata as a whole. Rows below `CONFIDENCE_THRESHOLD` (default 75, set via `--confidence-threshold` flag or `CURATION_CONFIDENCE_THRESHOLD` env var) are automatically set to `tag_status = 'needs_review'`.
- `web_context` stores the raw snippet used as model input so you can audit why a tag was chosen. A non-NULL value here is the main driver of a high confidence score.
- `tags_raw` is the pre-computed semicolon-separated string ready for Lightspeed export, e.g. `France; Bordeaux; Cabernet Sauvignon; Merlot; Blend; Organic`. Single-varietal wines get `Single Varietal` instead of `Blend`; organic wines get `Organic` appended.
- `tag_status` tracks whether the tags were auto-generated, need human review, reviewed, or manually entered.
- `tag_log` preserves the raw LLM interaction (including the web snippet used) for debugging and prompt iteration.

## Output Contract

Downstream (distribution) reads from `wines.db` and expects:
- The `products` table with all columns above.
- The `sales` table joined on `product_id`.
- `tags_raw` is the canonical export field; downstream should not re-derive tags from individual columns.

## Tech

- Python 3.11+
- `sqlite3` (stdlib)
- `requests` or `httpx` for LLM API calls and DuckDuckGo web lookups
- `web_cache.json` at `curation/output/web_cache.json` for search result caching (keyed by product id)
- No paid external APIs or API keys required

## Decisions

All open questions have been resolved:

| # | Question | Decision |
|---|----------|----------|
| 1 | **Web search reliability** — what to do when DDG returns nothing | Immediately set `tag_status = 'needs_review'` and skip LLM inference. |
| 2 | **Confidence threshold** | Default **75**. Expose as `--confidence-threshold` CLI flag and `CURATION_CONFIDENCE_THRESHOLD` env var so it can be adjusted without touching code. |
| 3 | **Private-label wines** (no useful web result) | Attempt LLM inference from name alone, then automatically set `tag_status = 'needs_review'` regardless of confidence. |
| 4 | **Organic evidence threshold** | Require **explicit wording** only: `"certified organic"`, `"biodynamic"`, `"certified biodynamic"`. Soft signals (`"natural"`, `"no added sulfites"`, `"low intervention"`) are not sufficient — `organic` stays `false`. |
| 5 | **Re-run behaviour** | Re-run re-tags all rows **except** those with `tag_status = 'manual'`. Rows with `'reviewed'`, `'needs_review'`, and `'auto'` are all eligible to be re-tagged. |
| 6 | **Batching (LLM)** | One wine per LLM call. |

## Batch-Review Mode

In addition to sequential processing, curation supports a **batch-review workflow** that pauses after every N wines so results can be inspected before continuing.

### CLI flag

```
--batch-size N    Process N wines, then pause for review before continuing.
                  Set to 0 (default) to run all wines without pausing.
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
