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
from constants import CURATED_SOURCES

CSV_PATH = Path(__file__).parent / "combined.csv"
ROWS_TO_TEST = 24

_llm_call_count = 0


def _patched_ddg_snippets(query: str) -> list[str]:
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
    label = "scoring snippets" if len(prompt) > 800 else "inferring tags"
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
    for i, row in enumerate(rows, 1):
        global _llm_call_count
        _llm_call_count = 0
        name = row.get("name", "?")
        print(f"[{i:02d}/{len(rows)}] {name}")

        print(f"     --- web lookup ---")
        t_web = time.time()
        web_context, scored = web_lookup(row, cache, api_url=DEFAULT_API_URL, model=DEFAULT_MODEL)
        web_elapsed = time.time() - t_web

        if scored:
            relevant = [s for s in scored if s.get("match_score", 0) >= 50]
            top = max(scored, key=lambda s: s.get("match_score", 0))
            print(f"       {len(scored)} snippets gathered, {len(relevant)} relevant")
            print(f"       best: {top.get('source', '?')} (match_score={top.get('match_score')})")
        elif web_context:
            print(f"       cache hit")
        else:
            print(f"       no snippets found")
        print(f"       web context: {(web_context or 'none')[:120]!r}")
        print(f"       web lookup total: {web_elapsed:.1f}s")

        print(f"     --- LLM inference ---")
        t_llm = time.time()
        parsed, _prompt, raw = infer_tags(row, web_context=web_context,
                                          api_url=DEFAULT_API_URL,
                                          model=DEFAULT_MODEL)
        llm_elapsed = time.time() - t_llm

        if parsed:
            print(f"       country={parsed.get('country')}  region={parsed.get('region')}")
            print(f"       grapes={parsed.get('grapes')}  is_blend={parsed.get('is_blend')}")
            print(f"       organic={parsed.get('organic')}  confidence={parsed.get('confidence')}")
        else:
            print(f"       PARSE FAILED — raw: {raw[:120]!r}")
        print(f"       inference total: {llm_elapsed:.1f}s")
        print()


if __name__ == "__main__":
    main()
