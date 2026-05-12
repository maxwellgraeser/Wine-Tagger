# Curation Domain

## Purpose

Take the clean CSVs from ingestion, look up each wine online to gather authoritative metadata, then use a locally-running Gemma model to turn that web context into structured tags (country, region, grapes, varietal/blend classification, organic status). Store everything in a SQLite database that serves as the single source of truth for the distribution layer.

## Inputs

From `ingestion/output/`:
- `combined.csv` -- single file containing product catalog columns and sales stats merged per row. Each row is one wine; sales columns are empty for products with no inventory match. Key columns: `id`, `name`, `sku`, `product_category`, `supply_price`, `retail_price`, `brand_name`, `supplier_name`, `items_sold`, `sale_count`, `margin_pct`, `customer_count`, `avg_sale_value`.

## Processing Steps

1. **Load CSV** into memory (pandas or stdlib csv).
2. **For each product, perform a web lookup** to gather raw context about the wine before calling the LLM:
   - Search using the product name (and brand/supplier where available) against a public source (e.g. Wine-Searcher, Vivino, or a general web search via SerpAPI / DuckDuckGo Instant Answer).
   - Extract the top result's description / fact sheet snippet (producer, region, grapes, organic/biodynamic mentions).
   - Store the raw snippet for the prompt and for the `tag_log`.
3. **For each product, call the local LLM** with the wine's name *and* the web snippet to infer:
   - `country` -- country of origin (e.g. `France`, `USA`, `Spain`)
   - `region` -- wine region (e.g. `Bordeaux`, `Napa Valley`, `Ribera del Duero`)
   - `grapes` -- grape varieties (e.g. `["Cabernet Sauvignon", "Merlot"]`)
   - `is_blend` -- `true` if multiple grapes, `false` if single varietal
   - `organic` -- `true` if the wine is certified organic/biodynamic/natural, otherwise omit / `false`
4. **Parse the LLM response** into structured fields. Use a consistent prompt that requests JSON output to make parsing reliable.
5. **Write everything to SQLite** -- products, sales stats, and the new tags.

## Web Lookup

### Goal

Give the local model real-world context rather than asking it to guess from a product name alone. A single web snippet per wine dramatically improves accuracy for obscure labels.

### Approach

1. Build a search query: `"{name}" {brand} wine region grapes` (drop supplier if it's just a distributor name).
2. Hit a lightweight source -- DuckDuckGo Instant Answer API (no key required) is the zero-config option; SerpAPI is the reliable paid alternative. Either is fine -- the script should accept a `--search-backend` flag (`ddg` | `serp`).
3. Take the first meaningful text snippet (≤ 400 chars). If nothing useful comes back (e.g. the product is a private label), set `web_context` to `null` and let the model do its best from the name alone.
4. Cache results in a local file (`curation/output/web_cache.json`, keyed by product id) so re-runs don't hit the network for already-looked-up wines.

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

Respond in JSON only — no explanation, no markdown fences:
{
  "country": "...",
  "region": "...",
  "grapes": ["...", "..."],
  "is_blend": true | false,
  "organic": true | false
}
```

### Rate & Error Handling

- Process wines sequentially (local model, no rate limits to worry about, but only one inference at a time).
- If the model returns unparseable output, retry once with a stricter prompt ("Return only raw JSON, no text before or after."). On second failure, flag the product for manual review (`tag_status = 'needs_review'`).
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
- `web_context` stores the raw snippet used as model input so you can audit why a tag was chosen.
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
- `requests` or `httpx` for LLM API calls and web lookups
- `web_cache.json` at `curation/output/web_cache.json` for search result caching (keyed by product id)
- No other external dependencies (SerpAPI key optional via `SERP_API_KEY` env var; falls back to DuckDuckGo)

## Open Questions

- **Web search backend**: DuckDuckGo (no key, less reliable) vs. SerpAPI (paid, more reliable). Should the default be DDG with a fallback message if results are poor?
- **Private-label wines**: when a web lookup returns nothing useful, should we still attempt LLM inference from name alone, or immediately mark `tag_status = 'needs_review'`?
- **Organic evidence threshold**: should the model require explicit wording ("certified organic", "biodynamic") or accept softer signals ("natural wine", "no added sulfites")?
- **Re-run behaviour**: should re-running curation skip wines that already have `tag_status = 'reviewed'` or `'manual'`, and re-tag only `'auto'` and `'needs_review'` rows?
- **Batching**: should we batch multiple wines into one LLM call for speed, or keep one-at-a-time for reliability? (One-at-a-time is safer given JSON parsing requirements.)
