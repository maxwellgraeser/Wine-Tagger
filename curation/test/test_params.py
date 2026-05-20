#!/usr/bin/env python3
"""
Parameter sweep: explore how DDG_MAX_RESULTS x SNIPPET_CHAR_LIMIT x SCORING_SNIPPET_CHARS
affect curation quality and cost.

For each (DDG, SNIPPET, SCORING) tuple in the grid below:
  - Monkeypatch the three constants inside the `curate` module.
  - Run the first WINES_PER_RUN rows of combined.csv through the full pipeline.
  - Collect per-run metrics (% auto, avg confidence on auto rows, avg top-N match score,
    avg time/wine, correctness vs ground_truth.json).
  - Print a sorted summary table at the end and dump results to params_results.json.

Edit the *_VALUES lists to change the grid. Fewer values = faster sweep.
"""

import csv
import json
import sys
import time
import itertools
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import curate
from curate import infer_tags, web_lookup, DEFAULT_API_URL, DEFAULT_MODEL
from constants import (
    CURATED_SOURCES,
    DEFAULT_CONFIDENCE_THRESHOLD,
    SNIPPET_MATCH_THRESHOLD,
    TOP_N_SNIPPETS,
)
from normalization import normalize_tags

# ---------------------------------------------------------------------------
# Grid — edit these lists to change which parameter values are explored.
# ---------------------------------------------------------------------------
DDG_MAX_RESULTS_VALUES     = [2, 3, 5]
SNIPPET_CHAR_LIMIT_VALUES  = [750, 1500, 3000]
SCORING_SNIPPET_CHARS_VALUES = [200, 300, 500]

CSV_PATH         = Path(__file__).parent / "combined.csv"
GROUND_TRUTH_PATH = Path(__file__).parent / "ground_truth.json"
RESULTS_PATH     = Path(__file__).parent / "params_results.json"
WINES_PER_RUN    = 10


# ---------------------------------------------------------------------------
# Correctness scoring against ground_truth.json
# ---------------------------------------------------------------------------
def _norm_str(s):
    if s is None:
        return None
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.strip().lower()


def _norm_grape_set(grapes):
    if not grapes:
        return frozenset()
    return frozenset(_norm_str(g) for g in grapes if g)


def _to_region_set(region):
    """Accept a list[str] or str (legacy ground-truth) and return a normalized set."""
    if region is None:
        return None
    if isinstance(region, str):
        region = [region]
    return frozenset(_norm_str(r) for r in region if r)


def score_correctness(parsed, truth):
    """Return dict of {field: bool|None} comparing parsed tags to ground truth.

    None means the field has no ground-truth value (skip in totals).
    region is compared as set-of-strings: parsed (post-normalize, includes
    parent expansion) must be a superset of every region the truth lists.
    This way truth = ["Willamette Valley"] still counts as correct when the
    pipeline returns ["Willamette Valley", "Oregon"], and truth that lists
    both still counts when the pipeline returns the same expansion.
    """
    if parsed is None or truth is None:
        return {"country": None, "region": None, "grapes": None,
                "is_blend": None, "organic": None}

    def cmp_country():
        t = truth.get("country")
        if t is None:
            return None
        return _norm_str(parsed.get("country")) == _norm_str(t)

    def cmp_region():
        truth_set = _to_region_set(truth.get("region"))
        if truth_set is None:
            return None
        parsed_set = _to_region_set(parsed.get("region")) or frozenset()
        return truth_set.issubset(parsed_set)

    return {
        "country":  cmp_country(),
        "region":   cmp_region(),
        "grapes":   None if truth.get("grapes") is None
                    else _norm_grape_set(parsed.get("grapes")) == _norm_grape_set(truth["grapes"]),
        "is_blend": None if truth.get("is_blend") is None
                    else bool(parsed.get("is_blend")) == bool(truth["is_blend"]),
        "organic":  None if truth.get("organic") is None
                    else bool(parsed.get("organic")) == bool(truth["organic"]),
    }


# ---------------------------------------------------------------------------
# Per-variant run
# ---------------------------------------------------------------------------
def run_variant(rows, ddg, snippet_limit, scoring_chars, truth_by_id):
    """Run the pipeline against `rows` with the three params monkeypatched.

    Returns a dict of aggregate metrics.
    """
    # Monkeypatch the three constants on the curate module (curate.py imports
    # them by name at module load, so the imported globals are what's used).
    curate.DDG_MAX_RESULTS       = ddg
    curate.SNIPPET_CHAR_LIMIT    = snippet_limit
    curate.SCORING_SNIPPET_CHARS = scoring_chars

    cache = {}  # fresh per variant — otherwise variant N reuses variant N-1's context
    n_auto = 0
    n_review = 0
    confidences_auto = []
    top_match_scores = []
    times = []
    field_correct = {"country": 0, "region": 0, "grapes": 0, "is_blend": 0, "organic": 0}
    field_total   = {"country": 0, "region": 0, "grapes": 0, "is_blend": 0, "organic": 0}
    per_wine = []

    for i, row in enumerate(rows, 1):
        t_wine = time.time()
        web_context, scored = web_lookup(row, cache,
                                          api_url=DEFAULT_API_URL,
                                          model=DEFAULT_MODEL)

        if scored:
            relevant = sorted(
                [s for s in scored if s.get("match_score", 0) >= SNIPPET_MATCH_THRESHOLD],
                key=lambda s: s.get("match_score", 0),
                reverse=True,
            )[:TOP_N_SNIPPETS]
            for s in relevant:
                top_match_scores.append(s["match_score"])

        parsed, _prompt, raw = infer_tags(row, web_context=web_context,
                                          api_url=DEFAULT_API_URL,
                                          model=DEFAULT_MODEL)

        forced_review = web_context is None
        norm_issues = []
        if parsed:
            parsed, norm_issues = normalize_tags(parsed)

        if not parsed:
            tag_status = "needs_review"
        elif forced_review:
            tag_status = "needs_review"
        elif norm_issues:
            tag_status = "needs_review"
        elif (parsed.get("confidence") or 0) < DEFAULT_CONFIDENCE_THRESHOLD:
            tag_status = "needs_review"
        else:
            tag_status = "auto"

        if tag_status == "auto":
            n_auto += 1
            confidences_auto.append((parsed or {}).get("confidence") or 0)
        else:
            n_review += 1

        truth = truth_by_id.get(row["id"])
        correctness = score_correctness(parsed, truth)
        for field, ok in correctness.items():
            if ok is None:
                continue
            field_total[field] += 1
            if ok:
                field_correct[field] += 1

        elapsed = time.time() - t_wine
        times.append(elapsed)
        per_wine.append({
            "id": row["id"],
            "name": row.get("name"),
            "tag_status": tag_status,
            "confidence": (parsed or {}).get("confidence"),
            "correct": correctness,
            "elapsed_s": round(elapsed, 2),
        })
        print(f"   [{i:02d}/{len(rows)}] {row.get('name'):<35} "
              f"{tag_status:<13} "
              f"conf={(parsed or {}).get('confidence')!s:<5} "
              f"{elapsed:5.1f}s")

    total = n_auto + n_review
    field_acc = {}
    for f in field_correct:
        field_acc[f] = (field_correct[f] / field_total[f]) if field_total[f] else None
    overall_correct = sum(field_correct.values())
    overall_total   = sum(field_total.values())
    overall_acc     = (overall_correct / overall_total) if overall_total else None

    return {
        "pct_auto":        (n_auto / total * 100) if total else 0.0,
        "n_auto":          n_auto,
        "n_review":        n_review,
        "avg_conf_auto":   (sum(confidences_auto) / len(confidences_auto)) if confidences_auto else None,
        "avg_top_match":   (sum(top_match_scores) / len(top_match_scores)) if top_match_scores else None,
        "avg_time_s":      (sum(times) / len(times)) if times else 0.0,
        "total_time_s":    sum(times),
        "field_accuracy":  field_acc,
        "overall_accuracy": overall_acc,
        "per_wine":        per_wine,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [row for _, row in zip(range(WINES_PER_RUN), reader)]

    if GROUND_TRUTH_PATH.exists():
        with open(GROUND_TRUTH_PATH, encoding="utf-8") as f:
            truth_raw = json.load(f)
        truth_by_id = {k: v for k, v in truth_raw.items() if not k.startswith("_")}
        print(f"Ground truth loaded: {len(truth_by_id)} wines")
    else:
        truth_by_id = {}
        print("WARNING: no ground_truth.json — correctness metrics will be empty")

    combos = list(itertools.product(
        DDG_MAX_RESULTS_VALUES,
        SNIPPET_CHAR_LIMIT_VALUES,
        SCORING_SNIPPET_CHARS_VALUES,
    ))

    print(f"\nGrid: {len(combos)} variants x {WINES_PER_RUN} wines = "
          f"{len(combos) * WINES_PER_RUN} pipeline runs")
    print(f"Sources: {', '.join(s['name'] for s in CURATED_SOURCES)}")
    print(f"Model:   {DEFAULT_MODEL} @ {DEFAULT_API_URL}\n")

    all_results = []
    t_sweep = time.time()
    for vi, (ddg, snippet, scoring) in enumerate(combos, 1):
        print("=" * 78)
        print(f"VARIANT {vi}/{len(combos)}  DDG={ddg}  SNIPPET={snippet}  SCORING={scoring}")
        print("=" * 78)
        t0 = time.time()
        metrics = run_variant(rows, ddg, snippet, scoring, truth_by_id)
        variant_elapsed = time.time() - t0
        result = {
            "params": {
                "DDG_MAX_RESULTS": ddg,
                "SNIPPET_CHAR_LIMIT": snippet,
                "SCORING_SNIPPET_CHARS": scoring,
            },
            "metrics": metrics,
            "variant_elapsed_s": round(variant_elapsed, 1),
        }
        all_results.append(result)

        print(f"\n   pct_auto         = {metrics['pct_auto']:.1f}%  "
              f"({metrics['n_auto']}/{metrics['n_auto'] + metrics['n_review']})")
        print(f"   avg_conf (auto)  = {metrics['avg_conf_auto']}")
        print(f"   avg top match    = {metrics['avg_top_match']}")
        print(f"   avg time/wine    = {metrics['avg_time_s']:.1f}s")
        print(f"   overall accuracy = {metrics['overall_accuracy']}")
        print(f"   field accuracy   = {metrics['field_accuracy']}")
        print()

    sweep_elapsed = time.time() - t_sweep

    # Summary table — sorted by overall accuracy desc, then pct_auto desc.
    print("\n" + "=" * 78)
    print("SUMMARY (sorted by overall accuracy, then pct_auto)")
    print("=" * 78)
    header = f"{'DDG':>3} {'SNIPPET':>7} {'SCORE':>5}  " \
             f"{'%auto':>6} {'conf':>5} {'match':>5} {'acc':>5} {'t/wine':>7}"
    print(header)
    print("-" * len(header))

    def sort_key(r):
        acc = r["metrics"]["overall_accuracy"] or 0
        return (-acc, -r["metrics"]["pct_auto"])

    for r in sorted(all_results, key=sort_key):
        p = r["params"]
        m = r["metrics"]
        acc = m["overall_accuracy"]
        print(f"{p['DDG_MAX_RESULTS']:>3} "
              f"{p['SNIPPET_CHAR_LIMIT']:>7} "
              f"{p['SCORING_SNIPPET_CHARS']:>5}  "
              f"{m['pct_auto']:>5.1f}% "
              f"{(m['avg_conf_auto'] or 0):>5.1f} "
              f"{(m['avg_top_match'] or 0):>5.1f} "
              f"{(acc * 100 if acc is not None else 0):>4.1f}% "
              f"{m['avg_time_s']:>6.1f}s")

    print(f"\nSweep total: {sweep_elapsed/60:.1f} min")

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "wines_per_run": WINES_PER_RUN,
            "grid": {
                "DDG_MAX_RESULTS":       DDG_MAX_RESULTS_VALUES,
                "SNIPPET_CHAR_LIMIT":    SNIPPET_CHAR_LIMIT_VALUES,
                "SCORING_SNIPPET_CHARS": SCORING_SNIPPET_CHARS_VALUES,
            },
            "results": all_results,
        }, f, indent=2)
    print(f"Full results -> {RESULTS_PATH}")


if __name__ == "__main__":
    main()
