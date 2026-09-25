# Why wines reach the tagger with one snippet / one source

Analysis of `logs/20260915-221614` (latest), compared against
`logs/20260915-170657` and `-170657b`. 24 wines, 9 queries each,
`DDG_MAX_RESULTS = 3` → 27 possible snippets per wine.

## Headline

The single-source problem is mostly **fixed** in the latest run. What is
left is a search-recall problem, not a scoring one.

| run | wines at ≤1 source | error mode |
|---|---|---|
| 170657 | 5 | 101 DDG `TimeoutException` |
| 170657b | 3 | same logs, re-scored |
| **221614** | **1** (Bila Haut) | 70 `DDGSException: No results found` |

Source distribution in 221614: `{1: 1, 2: 1, 3: 5, 4: 7, 5: 10}`.
The wines in the earlier table (Urruzola, Neirano, Massaya, Li Veli) now
land at 4–5 sources. Only Bila Haut still starves.

## The funnel (221614, distinct source families per wine)

```
searched        5.75
post-gate       5.58   (producer gate costs almost nothing now)
post-threshold  4.29   ← the real scoring loss
in-context      4.00   (TOP_N_SNIPPETS = 5 binds on only 3 wines)
```

Out of 9 query slots, a wine gets ~5.75 sources back. So **search recall,
not the gate, is the ceiling** — and the threshold shaves another 1.5.

## Cause 1 — quoted `site:` queries die on store shorthand (biggest)

Four of the nine queries are `site:X "{name}"` with the name as an exact
phrase. When `combined.csv` carries a store shorthand rather than the wine's
label, the phrase matches zero pages and all four go dark at once.

Bila Haut is the pure case: **8 of 9 queries returned nothing.** The CSV name
is `Bila Haut Roussillon`; the wine is *M. Chapoutier Les Vignes de Bila-Haut
Côtes du Roussillon Villages*. `"Bila Haut Roussillon"` is not a string that
appears on Wine-Searcher, Vivino, CellarTracker or Wine.com — the hyphen and
the missing "Côtes du" are enough. Only the unquoted natural-language
`Grapes Q` survived, giving 3 snippets from 1 source.

Failure counts by source, 221614 (wines with ≥1 result / wines with an error):

```
CellarTracker  19/5   Wine.com 19/5   Region Q 18/5   Grapes Q 17/7
Wine Searcher  16/8   Vivino   14/9   UPC      13/10  fallback 13/6
Winebow (dist)  9/12  Monsieur Touton (dist) 0/3
```

Errors are **not** time-clustered (no throttling signature), so these are
genuine zero-result queries, unlike 170657 where every failure was a timeout.

## Cause 2 — the distributor query returns the distributor's homepage

`("{supplier} (distributor)", "site:{dist} {name}", "{dist}")` is **unquoted**.
DDG therefore answers with whatever is on the site:

```
0  https://www.winebow.com/                 "Winebow is an importer and distributor…"
0  https://www.winebow.com/wholesale/fl     "Winebow comprises national import…"
0  https://dev.winebow.com/our-brands/figuiere   (for Li Veli Passamante)
0  https://dev.winebow.com/our-brands/damilano   (for Cloudline PN)
```

**24 of 26 winebow snippets scored <70 — 92%, the worst of any source.**
Monsieur Touton returned results for 0 of 3 wines. The query burns a slot and
three result slots per wine, and `_pick_diverse` gives it *first* priority on
the rare occasions something survives.

## Cause 3 — the scorer inverts on thin evidence

116 of 309 snippets (38%) scored <70; 59 (19%) scored a flat 0 while passing
the producer gate. Twenty of the low scores are snippets where the product
name is in the URL but not the body — the `url_only` hint is meant to cover
exactly this and is not reliably working.

Bila Haut shows the failure at its sharpest. Three snippets, one call:

| # | snippet | score |
|---|---|---|
| 0 | vinodivino — *"Grape: Syrah, Grenache, and Carignan … Côtes du Roussillon Villages … Michel Chapoutier"* | **0** |
| 1 | vivino — generic Languedoc-Roussillon region blurb | 0 |
| 2 | hattersleywines — *"Aromas of black cherry … warm soils of the Roussillon area"* (no grape, no producer, no appellation) | **88** |

The most informative snippet was discarded and the least informative one
became the entire context. Both had the identical `url_only` hint
(`bila, haut`), so the hint is not what separated them — the model appears to
penalize snippet 0 for naming a producer ("Michel Chapoutier") that is absent
from the product name, and to reward snippet 2 for containing nothing it can
contradict. The run then correctly routed the wine to `needs_review`
(`single_snippet_cap`, conf 84→69), but for the wrong reason: the evidence
was there and was thrown away.

Natural-language `Grapes Q` / `Region Q` also pull Vivino's generic region
boilerplate ("Wine from the Languedoc-Roussillon region is produced in the
South of France…"), which is correctly scored 0 but still consumes slots:
15 and 7 url-only cases respectively.

## Recommendations, ranked by expected recall gain

1. **Query the label, not the SKU name.** Before searching, resolve the CSV
   name to a fuller wine name (one unquoted `{name} wine` probe, or the MCP
   library's producer table), then run the `site:` queries against that. This
   alone would have given Bila Haut 4–5 sources instead of 1.
2. **Drop the quotes, or fall back when a quoted query returns zero.** A
   quoted `site:` query that errors with "No results found" should be retried
   unquoted before the source is written off.
3. **Fix or retire the distributor query.** Quote the name
   (`site:winebow.com "{name}"`), and drop any result whose URL is the site
   root, `/wholesale/*`, or a `dev.` host. At 92% waste it is currently
   net-negative.
4. **Re-ask the scorer when the survivor count is low.** If fewer than two
   sources clear `SNIPPET_MATCH_THRESHOLD`, re-score the zero-scored snippets
   one at a time with the URL spelled out. Batch-of-3 scoring on a wine with
   only 3 snippets has no redundancy to absorb one bad judgement.
5. **Do not let a snippet with zero facts outrank one with three.** `facts`
   is already collected; a survivor with `facts == []` and no other candidate
   should be treated as no context at all rather than as a single-source
   context.

Not a cause: the producer gate (5.75 → 5.58 sources) and `TOP_N_SNIPPETS`
(binds on 3 wines, all of which had 5+ sources anyway). Both were the suspects
in the 170657 era and both have been tuned out of the way.
