"""Filesystem layout shared by fermentation and the cellar web app.

    <repo>/
      ingestion/output/combined.csv   input
      output/wines.json               final product + tag store (JSON)
      output/.run_state.json          resume cursor (phase + index)
      logs/<run_id>/                  one folder per fermentation run
        run.json                      args, phase states, counts
        events.jsonl                  every progress event
        search/<product_id>.json      raw snippets per wine
        scorer/<product_id>.json      scored + gated snippets, web_context
        tagger/<product_id>.json      MCP tool-call transcript
        final/<product_id>.json       normalized block + tag_status
"""

from __future__ import annotations

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent

INPUT_CSV = PROJECT_ROOT / "ingestion" / "output" / "combined.csv"

OUTPUT_DIR = PROJECT_ROOT / "output"
WINES_JSON = OUTPUT_DIR / "wines.json"
RUN_STATE_PATH = OUTPUT_DIR / ".run_state.json"

LOGS_DIR = PROJECT_ROOT / "logs"

PHASES = ("search", "score", "tag")
# Folder name per phase inside logs/<run_id>/
PHASE_DIRS = {"search": "search", "score": "scorer", "tag": "tagger"}


def run_dir(run_id: str) -> Path:
    return LOGS_DIR / run_id


def phase_dir(run_id: str, phase: str) -> Path:
    return run_dir(run_id) / PHASE_DIRS[phase]
