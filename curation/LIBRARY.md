# Grape Tagging Library

## Purpose

Normalize grape variety names across the catalog so that synonyms (e.g. Shiraz / Syrah, Pinot Gris / Pinot Grigio) collapse to a single canonical tag. Without this, the downstream tag string `tags_raw` and any region/grape filter in distribution would treat the same grape as two different entities.

The library is a pure-Python module — no LLM calls, no I/O — consumed by `curate.py` after the tag-inference step (Phase 2) and before `build_tags_raw`.

## Problem

The LLM in Phase 2 returns whatever grape spelling appears in the web snippet. Real-world examples we have already seen:

- `Shiraz` vs `Syrah` (same grape, regional naming convention)
- `Pinot Gris` vs `Pinot Grigio` (same grape, FR vs IT name)
- `Tempranillo` vs `Tinto Fino` vs `Tinta de Toro` (same grape, regional synonyms)
- `Grenache` vs `Garnacha` (FR vs ES)
- `Mourvèdre` vs `Monastrell` vs `Mataro` (FR vs ES vs AU)
- `Carmenère` vs `Carménère` (diacritic variant)
- Casing drift: `cabernet sauvignon`, `Cabernet sauvignon`, `Cabernet Sauvignon`

If left unnormalized, a customer searching the tag `Syrah` misses every wine tagged `Shiraz`, and reporting on grape mix double-counts.

## Scope

In scope:
- Synonym → canonical mapping for the ~60 grape varieties that account for >99% of the catalog.
- Case folding and diacritic stripping for matching.
- Preserving the canonical form's diacritics in the output (e.g. always emit `Carmenère`, not `Carmenere`).
- A small helper to normalize a list of grapes returned by the LLM.

Out of scope:
- Region/country normalization (separate concern; could be a sibling library later).
- Disambiguating grapes that share a name across families (e.g. "Malvasia" covers several distinct varieties — for v1 we collapse to one).
- Vintage, style, or producer normalization.

## Design

### Module layout

A new file `curation/grape_library.py` with:

```python
CANONICAL_GRAPES: dict[str, list[str]]
# Maps canonical name → list of synonyms (including the canonical itself).
# Example: "Syrah": ["Syrah", "Shiraz"]

def normalize_grape(raw: str) -> str:
    """Return the canonical spelling for a single grape name.
    Falls back to title-cased raw input if no match is found."""

def normalize_grapes(raw: list[str]) -> list[str]:
    """Normalize a list of grapes, deduplicating after canonicalization."""
```

### Lookup table construction

A reverse lookup `_SYNONYM_TO_CANONICAL: dict[str, str]` is built once at import time. Keys are the **normalized** form of each synonym (lowercased, diacritics stripped, whitespace collapsed). Values are the canonical display form.

```python
# pseudocode
_SYNONYM_TO_CANONICAL = {
    _norm_key(syn): canonical
    for canonical, synonyms in CANONICAL_GRAPES.items()
    for syn in synonyms
}
```

`_norm_key` uses `unicodedata.normalize("NFKD", s)` + ASCII-only filter + `.lower().strip()`.

### Choice of canonical form

For each grape we pick the spelling most familiar to an Australian retail customer (the project's target market). When tied, prefer the French form for international varieties:

| Canonical | Synonyms collapsed |
|-----------|--------------------|
| Shiraz | Shiraz, Syrah |
| Pinot Gris | Pinot Gris, Pinot Grigio |
| Grenache | Grenache, Garnacha |
| Mourvèdre | Mourvèdre, Mourvedre, Monastrell, Mataro |
| Tempranillo | Tempranillo, Tinto Fino, Tinta de Toro, Tinta del País, Cencibel |
| Carmenère | Carmenère, Carmenere |
| Sangiovese | Sangiovese, Brunello, Prugnolo Gentile |
| Garganega | Garganega, Grecanico |
| Trebbiano | Trebbiano, Ugni Blanc |
| Malbec | Malbec, Côt, Auxerrois |
| Cabernet Sauvignon | Cabernet Sauvignon, Cab Sauv, Cab |
| Sauvignon Blanc | Sauvignon Blanc, Sauv Blanc, SB |
| Chardonnay | Chardonnay, Chard |
| Pinot Noir | Pinot Noir, PN |
| Riesling | Riesling, Johannisberg Riesling, White Riesling |

(The full list lives in the module itself — this table is illustrative.)

> **Note on Shiraz vs Syrah:** the abbreviation guide in `curate.py` already tells the LLM "Shiraz = Syrah". This library is the second line of defence — it canonicalizes whichever spelling the model actually emitted. Decision: collapse to **Shiraz** (Australian retail convention).

### Integration with `curate.py`

In `build_tags_raw` (currently at `curate.py:363`), wrap the LLM-returned `grapes` list:

```python
from grape_library import normalize_grapes
...
grapes = normalize_grapes(parsed.get("grapes") or [])
```

And similarly in `upsert_product` before serializing to JSON for the `grapes` column. This keeps both `grapes` (stored JSON) and `tags_raw` (semicolon string) consistent.

The `web_context` and `tag_log.raw_response` should remain unmodified — they are the audit trail of what the model originally said.

## Building the synonym list

1. Start from a hand-curated seed of the 60ish most common varieties (see table above + the rest).
2. Cross-check with the grape names already appearing in `wines.db.products.grapes` after a first curation run — any variety appearing >2 times that is *not* in the library is a candidate for inclusion (either as a new canonical or as a synonym of an existing one).
3. Iterate.

Suggested workflow once the library exists:

```sql
SELECT json_each.value AS grape, COUNT(*) AS n
FROM products, json_each(products.grapes)
GROUP BY grape ORDER BY n DESC;
```

Grapes appearing only once are usually either misspellings, abbreviations the LLM didn't expand, or genuine rare varieties — review case by case.

## Testing

Add `curation/test/test_grape_library.py` covering:

- `normalize_grape("syrah") == "Shiraz"`
- `normalize_grape("SHIRAZ") == "Shiraz"`
- `normalize_grape("carmenere") == "Carmenère"` (diacritic re-injected)
- `normalize_grape("Pinot  Grigio") == "Pinot Gris"` (whitespace collapsed)
- `normalize_grape("Assyrtiko") == "Assyrtiko"` (unknown grape → title-cased passthrough)
- `normalize_grapes(["Syrah", "Shiraz", "Grenache"]) == ["Shiraz", "Grenache"]` (dedupe after canonicalization)

## Open questions

| # | Question | Tentative answer |
|---|----------|------------------|
| 1 | Which canonical for Shiraz/Syrah? | **Shiraz** — AU retail context. Revisit if catalog skews European. |
| 2 | Do we expose the synonym table as JSON for non-Python consumers (e.g. distribution)? | Not yet — keep it Python-only until distribution actually needs it. |
| 3 | How do we handle ambiguous names like "Malvasia"? | v1: collapse to `Malvasia`. If a customer complaint surfaces the distinction, split later. |
| 4 | Should the LLM see the canonical list in its prompt? | Possibly — could shrink the synonym table over time. Out of scope for v1; library handles the cleanup post-hoc. |
