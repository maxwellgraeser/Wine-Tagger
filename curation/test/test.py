#!/usr/bin/env python3
"""
Quick smoke test: send the first 10 data rows of combined.csv through the LLM
and print the parsed results. No DB writes.
"""

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from curate import infer_tags, web_lookup, DEFAULT_API_URL, DEFAULT_MODEL
from sources import CURATED_SOURCES

CSV_PATH = Path(__file__).parent / "combined.csv"
ROWS_TO_TEST = 10


def main():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [row for _, row in zip(range(ROWS_TO_TEST), reader)]

    source_names = [s["name"] for s in CURATED_SOURCES]
    print(f"Testing {len(rows)} wines against {DEFAULT_MODEL} at {DEFAULT_API_URL}")
    print(f"Web lookup sources ({len(CURATED_SOURCES)}): {', '.join(source_names)}\n")

    cache = {}
    for i, row in enumerate(rows, 1):
        name = row.get("name", "?")
        print(f"[{i:02d}] {name}")
        source_log = []
        web_context = web_lookup(row, cache, source_log=source_log)
        hit_entry = next((e for e in source_log if e["hit"]), None)
        if hit_entry:
            label = "fallback" if hit_entry["fallback"] else hit_entry["name"]
            print(f"     source: {label}")
        else:
            tried = [e["name"] for e in source_log]
            print(f"     source: none (tried: {', '.join(tried) or '—'})")
        print(f"     web: {(web_context or 'none')[:100]!r}")
        parsed, _prompt, raw = infer_tags(row, web_context=web_context,
                                          api_url=DEFAULT_API_URL,
                                          model=DEFAULT_MODEL)
        if parsed:
            print(f"     country={parsed.get('country')}  region={parsed.get('region')}")
            print(f"     grapes={parsed.get('grapes')}  is_blend={parsed.get('is_blend')}")
            print(f"     organic={parsed.get('organic')}  confidence={parsed.get('confidence')}")
        else:
            print(f"     PARSE FAILED — raw: {raw[:120]!r}")
        print()


if __name__ == "__main__":
    main()
