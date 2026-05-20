# Curation Parameter Sweep — Results

## Overview

A grid sweep over the curation pipeline to find the best combination of search
breadth, snippet length, and scoring budget. Each variant runs the full
pipeline (DuckDuckGo search → Wine Searcher / Vivino / CellarTracker scraping
→ scoring → LLM verdict) against a fixed ground-truth set of 10 wines.

- **Model**: `gemma3n:e4b` @ `http://localhost:8080/v1/chat/completions`
- **Sources**: Wine Searcher, Vivino, CellarTracker
- **Ground truth**: 10 wines (see `ground_truth.json`)
- **Grid**: 27 variants × 10 wines = **270 pipeline runs**
- **Sweep wall time**: 186.8 min
- **Raw log**: `test_params1.txt` · **Raw data**: `params_results.json`

## Variables

| Variable    | Values            | Effect                                                                 |
|-------------|-------------------|------------------------------------------------------------------------|
| `DDG`       | 2, 3, 5           | DuckDuckGo results fetched per source query. Higher = broader evidence, slower. |
| `SNIPPET`   | 750, 1500, 3000   | Characters pulled per search result. Higher = more context, more tokens. |
| `SCORING`   | 200, 300, 500     | Cap on aggregated text fed to the scoring/matching stage.              |

## Output metrics

| Metric            | Meaning                                                              |
|-------------------|----------------------------------------------------------------------|
| `pct_auto`        | Share of wines auto-accepted (vs `needs_review`).                    |
| `avg_conf (auto)` | Mean LLM confidence on auto-accepted items.                          |
| `avg top match`   | Fuzzy-match score of chosen candidate vs ground truth.               |
| `avg time/wine`   | Wall-clock seconds per wine.                                         |
| `overall accuracy`| Mean field accuracy across the 5 evaluated fields.                   |
| `field accuracy`  | Per-field correctness: `country`, `region`, `grapes`, `is_blend`, `organic`. |

## Effects observed

- **DDG**: 2 → 3 yields a modest accuracy bump. 3 → 5 mostly adds latency
  (≈35s → 50s+) with no consistent accuracy gain. Diminishing returns past 3.
- **SNIPPET**: 1500 is the sweet spot. 750 occasionally starves scoring;
  3000 sometimes helps but adds tokens/noise.
- **SCORING**: non-monotonic. 200 and 500 each top the leaderboard once; 300
  is the most consistent middle ground. Higher isn't strictly better — 500
  can drop `pct_auto` by surfacing more ambiguous candidates.
- **grapes**: stuck at 0.6 across nearly every variant (one run hits 0.7).
  This is a pipeline ceiling, not a tunable.
- **organic**: 1.0 across all variants — trivially solved or uniform in
  ground truth.

## Top configurations (sorted by accuracy, then %auto)

| DDG | SNIPPET | SCORE | %auto | conf | match | acc   | t/wine |
|-----|---------|-------|-------|------|-------|-------|--------|
| 3   | 3000    | 200   | 90.0% | 94.8 | 96.0  | 90.0% | 37.6s  |
| 5   | 750     | 500   | 70.0% | 92.9 | 95.3  | 90.0% | 47.6s  |
| 5   | 3000    | 500   | 70.0% | 93.6 | 96.9  | 90.0% | 49.0s  |
| 2   | 3000    | 300   | 90.0% | 94.4 | 96.0  | 88.0% | 35.4s  |
| 3   | 1500    | 200   | 90.0% | 93.9 | 95.3  | 88.0% | 37.4s  |
| 2   | 1500    | 300   | 80.0% | 93.8 | 95.8  | 88.0% | 32.2s  |
| 3   | 1500    | 500   | 70.0% | 92.1 | 95.7  | 88.0% | 40.8s  |
| 5   | 1500    | 500   | 70.0% | 94.3 | 96.8  | 88.0% | 51.8s  |
| 5   | 3000    | 200   | 70.0% | 94.3 | 97.2  | 88.0% | 45.2s  |
| 5   | 750     | 300   | 50.0% | 94.0 | 94.5  | 88.0% | 55.5s  |

## Recommendations

- **Best overall**: `DDG=3, SNIPPET=3000, SCORING=200` — top accuracy (0.90),
  top %auto (90%), mid-pack latency (37.6s).
- **Best latency/quality trade-off**: `DDG=2, SNIPPET=1500, SCORING=300` —
  0.88 accuracy at 80% auto in 32.2s/wine.
- **Avoid**: `DDG=5` configurations — added latency rarely buys accuracy.

## Next steps

- Investigate the `grapes` ceiling (0.6) — likely a normalization or
  source-coverage issue rather than a tunable parameter.
- Expand ground truth beyond 10 wines to reduce variance at the
  per-variant level (single-wine flips swing `pct_auto` by 10pp).

---

# Experiment 2 — Finer sweep around the winner

Follow-up sweep holding `DDG=3` (confirmed sweet spot) and widening the
SNIPPET and SCORING grids to probe around the experiment 1 recommendation.

- **Grid**: 30 variants × 10 wines = **300 pipeline runs**
- **Sweep wall time**: 338.2 min
- **Raw log**: `test_params2.txt` · **Raw data**: `params_results.json`

## Variables

| Variable    | Values                       | Notes                                               |
|-------------|------------------------------|-----------------------------------------------------|
| `DDG`       | 3                            | Fixed — exp 1 showed diminishing returns past 3.    |
| `SNIPPET`   | 1500, 2000, 2500, 3000, 4000, 5000 | Wider range than exp 1, denser around 2000–3000. |
| `SCORING`   | 100, 200, 300, 400, 500      | Added 100 and 400 to fill gaps in exp 1.            |

## Top configurations (sorted by accuracy, then %auto)

| DDG | SNIPPET | SCORE | %auto | conf | match | acc   | t/wine |
|-----|---------|-------|-------|------|-------|-------|--------|
| 3   | 2000    | 100   | 90.0% | 91.7 | 99.0  | 88.0% | 36.9s  |
| 3   | 2500    | 500   | 90.0% | 93.9 | 95.2  | 88.0% | 48.3s  |
| 3   | 4000    | 400   | 90.0% | 92.2 | 96.3  | 88.0% | 51.3s  |
| 3   | 5000    | 200   | 90.0% | 94.4 | 96.8  | 88.0% | 60.2s  |
| 3   | 3000    | 100   | 80.0% | 93.8 | 97.3  | 88.0% | 41.3s  |
| 3   | 4000    | 500   | 80.0% | 93.8 | 96.2  | 88.0% | 49.5s  |
| 3   | 4000    | 200   | 70.0% | 92.1 | 96.5  | 88.0% | 106.3s |
| 3   | 2500    | 200   | 60.0% | 94.2 | 96.2  | 88.0% | 45.9s  |
| 3   | 2000    | 400   | 50.0% | 94.0 | 96.8  | 88.0% | 42.7s  |
| 3   | 2000    | 200   | 90.0% | 93.9 | 96.2  | 86.0% | 42.8s  |

## Effects observed

- **Accuracy ceiling dropped to 0.88** (from 0.90 in exp 1). No config
  cleared the previous bar. Six configs tied at 0.88 — the surface around
  the optimum is flat, not peaked.
- **New sweet spot**: `SNIPPET=2000, SCORING=100` — 0.88 accuracy, 90%
  auto, 36.9s/wine. Cheaper SCORING than exp 1's winner and slightly
  smaller SNIPPET.
- **SCORING=100 is viable**: not tested in exp 1; here it tops the
  leaderboard at SNIPPET=2000 and ties at SNIPPET=3000. Lower scoring
  budget does not hurt and reduces token cost.
- **Exp 1 winner regressed**: `SNIPPET=3000, SCORING=200` scored 0.86
  here vs 0.90 previously. Run-to-run variance on 10 wines is too high
  to distinguish near-equivalent configs reliably.
- **Larger SCORING budgets (300–400) at SNIPPET ≥ 3000** consistently
  underperform (0.80–0.82) — reinforces exp 1's note that more context
  surfaces more ambiguous candidates.
- **`grapes` still pinned at 0.6** across 29/30 variants (one outlier at
  0.7). Confirmed structural ceiling.
- **`organic` = 1.0** universally (unchanged).
- **Scraper hangs**: variants 5, 14, 22, 29 had single-wine stalls of
  700–1040s. These skew `avg time/wine` (variant 5 reports 537s/wine)
  but are not parameter effects — they are scraping I/O outliers.

## Revised recommendations

- **Best overall**: `DDG=3, SNIPPET=2000, SCORING=100` — 0.88 accuracy,
  90% auto, 36.9s/wine, lowest token cost of the top tier.
- **If higher confidence is wanted**: `DDG=3, SNIPPET=2500, SCORING=500`
  — same accuracy, higher `avg_conf` (93.9), at ~11s/wine extra.
- **Avoid**: `SCORING ≥ 300` paired with `SNIPPET ≥ 3000` — consistent
  accuracy hit with no latency benefit.

## Next steps

- The flat 0.88 plateau across many configs (and exp 1's 0.90 not
  reproducing) strongly suggests **ground-truth size is now the binding
  constraint**. Expand beyond 10 wines before further parameter tuning.
- Investigate the `grapes` ceiling — confirmed across 60 variants and
  600 runs. Almost certainly a normalization/source-coverage issue.
- Add a scraper timeout to eliminate the multi-minute single-wine hangs.
