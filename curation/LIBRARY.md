# Normalization Libraries

## Purpose

Normalize the country, region, and grape names returned by the Phase 2 LLM
so that synonyms, casing drift, and diacritic variants collapse to a single
canonical tag — and so that obvious data-quality errors (e.g. region=Veneto
with country=USA) get flagged for review instead of silently committed.

The libraries are pure-Python modules — no LLM calls, no I/O — consumed by
`curate.py` between the tag-inference step and the DB write.

## Problem

The LLM in Phase 2 returns whatever spelling appears in the web snippet, plus
the occasional clear mistake. Real-world examples from a recent 24-wine test
run:

- `Zenato Pinot Grigio` → tagged `country=USA, region=Veneto` (Wine Searcher
  snippet literally said "delle Venezie, Italy" with match=95).
- `Librandi Cirò Bianco` → tagged `grapes=['Cirò Bianco']` (Cirò Bianco is a
  DOC, not a grape).
- `Tessellae Old Vines` → tagged `grapes=['Red Rhone Blend']` (placeholder,
  not a grape list).
- `USA` vs `United States` (used interchangeably across wines).
- `Languedoc Roussillon` (no hyphen) vs `Languedoc-Roussillon`.
- `Coastal Region Cape Peninsula` / `Coastal Region Paarl` — sub-region jammed
  onto WO district.
- `region="Portugal"` — country name in the region slot.
- `Garnacha` vs `Grenache`, `Tinta Roriz` vs `Tempranillo`, `Shiraz` vs
  `Syrah` — regional naming for the same grape.

Without normalization, a customer searching the tag `Syrah` misses every wine
tagged `Shiraz`, the catalog double-counts varieties, and the Zenato bug ships
to production.

## Scope

In scope:
- Synonym → canonical mapping for the ~30 wine-producing countries, ~80
  regions, and ~60 grape varieties covering >99% of the catalog.
- Case folding and diacritic stripping for matching.
- Preserving the canonical form's diacritics in the output (e.g. always emit
  `Carmenère`, not `Carmenere`).
- Region → country pinning so the catalog can detect Zenato-style mismatches.
- A set of "placeholder" grape phrases (`unknown`, `Bordeaux Blend`,
  `Red Rhone Blend`, …) that are stripped from the grape list and flagged.

Out of scope:
- Vintage, style, or producer normalization.
- Disambiguating names that overlap across families (e.g. "Malvasia" covers
  several distinct varieties — for v1 we collapse to one).
- Cross-checking grape against region (e.g. "Nebbiolo outside Piedmont must
  be unusual") — that's the Phase 3 LLM-review concern (see REVIEW.md).

## Module layout

Flat files in `curation/`:

| File | Responsibility |
|------|----------------|
| `grape_library.py` | `CANONICAL_GRAPES`, `PLACEHOLDER_GRAPES`, `normalize_grape`, `normalize_grapes`, `is_placeholder_grape` |
| `country_library.py` | `CANONICAL_COUNTRIES`, `normalize_country`, `is_known_country` |
| `region_library.py` | `REGIONS` (with country pinning), `COUNTRY_AS_REGION`, `normalize_region`, `is_known_region` |
| `normalize.py` | `normalize_tags(parsed) -> (parsed, issues)` orchestrator used by `curate.py` |

### `normalize_tags` contract

```python
def normalize_tags(parsed: dict) -> tuple[dict, list[str]]:
    """Apply libraries to LLM output. Returns (normalized_parsed, issues).
    A non-empty issues list means the row should be marked needs_review."""
```

Possible entries in `issues`:

| Issue | Meaning |
|-------|---------|
| `placeholder_grapes` | LLM emitted a vague placeholder (`unknown`, `Bordeaux Blend`, …) instead of real grape names. The placeholder is dropped from the grape list; if the wine was blend-flagged, `is_blend=True` is preserved. |
| `region_country_mismatch` | Region maps to a country different from the one the LLM reported. The headline reason for review — catches Zenato-style mistakes. |
| `country_in_region_slot` | LLM put a country name (e.g. `Portugal`) in the region field. Blanked out. |
| `no_grapes` | Grape list ended up empty after placeholder removal. |

### Canonical-form rules

For each grape we pick the spelling most familiar to an Australian retail
customer (the project's target market). When tied, prefer the French form for
international varieties:

| Canonical | Synonyms collapsed |
|-----------|--------------------|
| Shiraz | Shiraz, Syrah |
| Pinot Gris | Pinot Gris, Pinot Grigio, Grauburgunder |
| Grenache | Grenache, Garnacha, Cannonau |
| Mourvèdre | Mourvèdre, Mourvedre, Monastrell, Mataro |
| Tempranillo | Tempranillo, Tinto Fino, Tinta de Toro, Tinta del País, Tinta Roriz, Aragonez, Cencibel |
| Carmenère | Carmenère, Carmenere |
| Sangiovese | Sangiovese, Brunello, Prugnolo Gentile |
| Carignan | Carignan, Cariñena, Mazuelo |
| Cabernet Sauvignon | Cabernet Sauvignon, Cab Sauv, Cab |
| Sauvignon Blanc | Sauvignon Blanc, Sauv Blanc, SB, Fumé Blanc |
| Riesling | Riesling, Johannisberg Riesling, White Riesling |

(The full list lives in `grape_library.py`.)

> **Note on Shiraz vs Syrah:** the abbreviation guide in `curate.py` already
> tells the LLM "Shiraz = Syrah". The library is the second line of defence —
> it canonicalizes whichever spelling the model actually emitted. Decision:
> collapse to **Shiraz** (Australian retail convention).

For countries: `USA / US / U.S. / America / United States of America` →
`United States`. For regions: hyphenation, diacritics, and language drift
collapse to a single canonical form (`Piemonte` → `Piedmont`, `Bourgogne` →
`Burgundy`, `Languedoc Roussillon` → `Languedoc-Roussillon`).

### Region → country pinning

Every entry in `REGIONS` has an `expected_country`. When the LLM reports
`region=Veneto` and `country=USA`, `normalize_region("Veneto")` returns
`("Veneto", "Italy")`; the orchestrator compares against `"USA"` →
`"United States"` and emits `region_country_mismatch`.

Unknown regions pass through (no constraint, no flag). Sub-region noise like
`Coastal Region Cape Peninsula` is handled by a substring fallback: if any
known synonym is contained in the normalized input, the canonical region wins.

## Integration with `curate.py`

In the main loop, immediately after `infer_tags` returns:

```python
parsed, norm_issues = normalize_tags(parsed)
if norm_issues:
    tag_status = "needs_review"
```

This sits alongside the existing `forced_review` and confidence-threshold
checks. `web_context` and `tag_log.raw_response` are unmodified — they are the
audit trail of what the model originally said.

## Building the synonym list

1. Start from the hand-curated seeds in each library file.
2. After a curation run, query for unknowns:

   ```sql
   SELECT json_each.value AS grape, COUNT(*) AS n
   FROM products, json_each(products.grapes)
   GROUP BY grape ORDER BY n DESC;
   ```

   Any variety appearing >2 times that is *not* in `grape_library.py` is a
   candidate (either a new canonical or a synonym of an existing one). Run
   the equivalent query against `country` and `region` columns.
3. Iterate.

## Testing

Suggested coverage for `curation/test/test_normalize.py`:

- `normalize_grape("syrah") == "Shiraz"`
- `normalize_grape("SHIRAZ") == "Shiraz"`
- `normalize_grape("carmenere") == "Carmenère"` (diacritic re-injected)
- `normalize_grape("Assyrtiko") == "Assyrtiko"` (unknown → title-cased passthrough)
- `is_placeholder_grape("Bordeaux Blend") is True`
- `normalize_grapes(["Syrah", "Shiraz", "Grenache"]) == ["Shiraz", "Grenache"]`
- `normalize_country("USA") == "United States"`
- `normalize_region("Veneto") == ("Veneto", "Italy")`
- `normalize_region("Coastal Region Paarl") == ("Coastal Region", "South Africa")`
- `normalize_region("Portugal") == ("", None)` — country in region slot
- `normalize_tags({"country": "USA", "region": "Veneto", "grapes": ["Pinot Grigio"]})` →
  issues contains `"region_country_mismatch"`, grape becomes `"Pinot Gris"`.

## Open questions

| # | Question | Tentative answer |
|---|----------|------------------|
| 1 | Canonical for Shiraz/Syrah? | **Shiraz** — AU retail context. Revisit if catalog skews European. |
| 2 | Expose the synonym tables as JSON for non-Python consumers? | Not yet — keep them Python-only until distribution actually needs them. |
| 3 | Ambiguous names like "Malvasia"? | v1: collapse to `Malvasia`. Split later if customer feedback surfaces the distinction. |
| 4 | Show the LLM the canonical lists in its prompt? | Out of scope here — covered by Phase 3 review (see REVIEW.md). |
| 5 | `region_country_mismatch` — flip the country automatically? | No. Flag for review only. The mismatch could go either way (wrong country, wrong region) and we don't want the library to silently overwrite LLM output. Phase 3 review can make that call with more context. |
