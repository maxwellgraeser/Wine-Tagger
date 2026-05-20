#!/usr/bin/env python3
"""
Quick smoke test: send the first X data rows of combined.csv through the LLM
and print the parsed results. No DB writes.
"""

import csv
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import curate
from curate import infer_tags, web_lookup, DEFAULT_API_URL, DEFAULT_MODEL
from constants import CURATED_SOURCES, DEFAULT_CONFIDENCE_THRESHOLD, SNIPPET_MATCH_THRESHOLD, TOP_N_SNIPPETS
from normalization import normalize_tags

CSV_PATH = Path(__file__).parent / "combined.csv"
ROWS_TO_TEST = 24

_llm_call_count = 0
_in_inference = False


def _patched_ddg_snippets(query: str) -> list[dict]:
    domain = query.split("site:")[-1].split(" ")[0] if "site:" in query else "web"
    print(f"       [DDG] {domain} ...", end="", flush=True)
    t0 = time.time()
    results = _orig_ddg_snippets(query)
    elapsed = time.time() - t0
    print(f" {len(results)} result(s) ({elapsed:.1f}s)")
    return results


def _patched_call_llm(prompt: str, api_url: str, model: str, timeout: int = 60) -> str:
    global _llm_call_count
    _llm_call_count += 1
    label = "inferring tags" if _in_inference else "scoring snippets"
    print(f"       [LLM #{_llm_call_count}] {label} ...", end="", flush=True)
    t0 = time.time()
    result = _orig_call_llm(prompt, api_url, model, timeout)
    elapsed = time.time() - t0
    print(f" done ({elapsed:.1f}s)")
    return result


_orig_ddg_snippets = curate.ddg_snippets
_orig_call_llm = curate.call_llm
curate.ddg_snippets = _patched_ddg_snippets
curate.call_llm = _patched_call_llm


def main():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [row for _, row in zip(range(ROWS_TO_TEST), reader)]

    source_names = [s["name"] for s in CURATED_SOURCES]
    print(f"Testing {len(rows)} wines against {DEFAULT_MODEL} at {DEFAULT_API_URL}")
    print(f"Web lookup sources ({len(CURATED_SOURCES)}): {', '.join(source_names)}\n")

    cache = {}
    n_auto = 0
    n_review = 0
    review_reasons: dict[str, int] = {}
    per_wine_times: list[float] = []
    for i, row in enumerate(rows, 1):
        global _llm_call_count, _in_inference
        _llm_call_count = 0
        name = row.get("name", "?")
        print(f"[{i:02d}/{len(rows)}] {name}")
        t_wine = time.time()

        print(f"     --- web lookup ---")
        t_web = time.time()
        web_context, scored = web_lookup(row, cache, api_url=DEFAULT_API_URL, model=DEFAULT_MODEL)
        web_elapsed = time.time() - t_web

        if scored:
            relevant = [s for s in scored if s.get("match_score", 0) >= SNIPPET_MATCH_THRESHOLD]
            top = max(scored, key=lambda s: s.get("match_score", 0))
            print(f"       {len(scored)} snippets gathered, {len(relevant)} relevant")
            print(f"       best: {top.get('source', '?')} (match_score={top.get('match_score')})")
        elif web_context:
            print(f"       cache hit")
        else:
            print(f"       no snippets found")

        # Sources actually fed to the tagger (top-N relevant after scoring)
        if scored:
            tagging_sources = sorted(
                [s for s in scored if s.get("match_score", 0) >= SNIPPET_MATCH_THRESHOLD],
                key=lambda x: x.get("match_score", 0),
                reverse=True,
            )[:TOP_N_SNIPPETS]
            if tagging_sources:
                print(f"       tagging inputs ({len(tagging_sources)} of top-{TOP_N_SNIPPETS}):")
                for s in tagging_sources:
                    print(f"         - {s.get('source', '?')} (match={s.get('match_score')})")
            else:
                print(f"       tagging inputs: none passed threshold ({SNIPPET_MATCH_THRESHOLD})")
        print(f"       web context: {(web_context or 'none')[:120]!r}")
        print(f"       web lookup total: {web_elapsed:.1f}s")

        print(f"     --- LLM inference ---")
        _in_inference = True
        t_llm = time.time()
        parsed, _prompt, raw = infer_tags(row, web_context=web_context,
                                          api_url=DEFAULT_API_URL,
                                          model=DEFAULT_MODEL)
        llm_elapsed = time.time() - t_llm
        _in_inference = False

        forced_review = web_context is None
        norm_issues: list[str] = []
        if parsed:
            parsed, norm_issues = normalize_tags(parsed)
            region_disp = parsed.get('region')
            if isinstance(region_disp, list):
                region_disp = ", ".join(region_disp) if region_disp else None
            print(f"       country={parsed.get('country')}  region={region_disp}")
            print(f"       grapes={parsed.get('grapes')}  is_blend={parsed.get('is_blend')}")
            print(f"       organic={parsed.get('organic')}  confidence={parsed.get('confidence')}")
        else:
            print(f"       PARSE FAILED — raw: {raw[:120]!r}")
        print(f"       inference total: {llm_elapsed:.1f}s")

        if not parsed:
            tag_status, reason = "needs_review", "parse_failed"
        elif forced_review:
            tag_status, reason = "needs_review", "no_web_context"
        elif norm_issues:
            tag_status, reason = "needs_review", ",".join(norm_issues)
        elif (parsed.get("confidence") or 0) < DEFAULT_CONFIDENCE_THRESHOLD:
            tag_status, reason = "needs_review", f"confidence<{DEFAULT_CONFIDENCE_THRESHOLD}"
        else:
            tag_status, reason = "auto", "ok"
        print(f"       label: {tag_status} ({reason})")
        if tag_status == "needs_review":
            n_review += 1
            review_reasons[reason] = review_reasons.get(reason, 0) + 1
        else:
            n_auto += 1
        wine_elapsed = time.time() - t_wine
        per_wine_times.append(wine_elapsed)
        print(f"       wine total: {wine_elapsed:.1f}s")
        print()

    total = n_auto + n_review
    pct_review = (n_review / total * 100) if total else 0.0
    pct_auto = (n_auto / total * 100) if total else 0.0
    print("=" * 50)
    print(f"GRADE: {n_review}/{total} flagged for review ({pct_review:.1f}%)")
    print(f"       {n_auto}/{total} auto-tagged ({pct_auto:.1f}%)")
    if per_wine_times:
        avg_time = sum(per_wine_times) / len(per_wine_times)
        print(f"       avg time/wine: {avg_time:.1f}s (over {len(per_wine_times)} wines, total {sum(per_wine_times):.1f}s)")
    if review_reasons:
        print("       review reasons:")
        for reason, count in sorted(review_reasons.items(), key=lambda x: -x[1]):
            print(f"         - {reason}: {count}")


if __name__ == "__main__":
    main()
