#!/usr/bin/env python3
"""fermentation/ferment.py — CLI controller for the fermentation pipeline.

Runs three phases over the whole product set, in order:

    search  every wine's web snippets      -> logs/<run>/search/
    score   every wine's snippets scored   -> logs/<run>/scorer/
    tag     every wine tagged via MCP      -> logs/<run>/tagger/, final/, output/wines.json

The MCP `submit_tags` output is authoritative; there is no post-tagger
normalize pass. The producer-absent check is a hard exclusion in scorer.py.

Resume: after every wine `output/.run_state.json` records (run_id, phase,
cursor). Re-running resumes there; `--force` starts a fresh run.
`--stop-after PHASE` pauses at a phase boundary (state saved, so the next
run continues with the following phase) — the dashboard's "pause after each
phase" mode.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import Optional

from . import phases, settings as settings_mod, store as store_mod
from .constants import DEFAULT_API_URL, DEFAULT_MODEL
from .events import EventSink
from .paths import INPUT_CSV, PHASES, WINES_JSON, run_dir
from .types import Product


# ---------------------------------------------------------------------------
# CSV load
# ---------------------------------------------------------------------------

def _to_float(v) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _to_int(v) -> Optional[int]:
    f = _to_float(v)
    return None if f is None else int(f)


def load_products(csv_path: Path) -> list[Product]:
    products: list[Product] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            products.append(Product(
                id=row["id"],
                name=row["name"],
                sku=(row.get("sku") or None),
                brand=(row.get("brand_name") or None),
                category=(row.get("product_category") or None),
                supply_price=_to_float(row.get("supply_price")),
                retail_price=_to_float(row.get("retail_price")),
                supplier=(row.get("supplier_name") or None),
                items_sold=_to_int(row.get("items_sold")),
                margin_pct=_to_float(row.get("margin_pct")),
                sale_count=_to_int(row.get("sale_count")),
                customer_count=_to_int(row.get("customer_count")),
                avg_sale_value=_to_float(row.get("avg_sale_value")),
            ))
    return products


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Fermentation: tag wine metadata via local LLM + MCP library.",
    )
    p.add_argument("--api-url", default=os.environ.get("FERMENTATION_API_URL", DEFAULT_API_URL))
    p.add_argument("--model", default=os.environ.get("FERMENTATION_MODEL", DEFAULT_MODEL))
    p.add_argument(
        "--confidence-threshold", type=int,
        default=int(os.environ.get("FERMENTATION_CONFIDENCE_THRESHOLD",
                                   settings_mod.confidence_threshold())),
        help="Min tagger confidence for tag_status=model (default: settings.json, "
             f"else {settings_mod.defaults()['confidence_threshold']})",
    )
    p.add_argument("--force", action="store_true",
                   help="Ignore saved run state and start a fresh run")
    p.add_argument("--input", default=str(INPUT_CSV), help="Path to combined.csv")
    p.add_argument("--limit", type=int, default=0, help="Process at most N wines (0 = all)")
    p.add_argument("--no-producer-gate", action="store_true",
                   help="Disable the scorer's producer-absent hard gate (debugging aid).")
    p.add_argument("--phase", choices=PHASES, default=None,
                   help="Start a fresh run at this phase, reusing an earlier run's logs "
                        "(requires --run-id).")
    p.add_argument("--run-id", default=None,
                   help="Reuse this run id (with --phase, re-run from that phase using its logs).")
    p.add_argument("--stop-after", choices=PHASES, default=None,
                   help="Pause the run after this phase finishes. The run's state is saved "
                        "so re-running (or --phase NEXT --run-id ID) continues from the next phase.")
    p.add_argument("--events-json", action="store_true",
                   help="Print one JSON event per line on stdout (for the cellar web app).")
    return p


def main(argv: Optional[list[str]] = None) -> None:
    args = build_parser().parse_args(argv)

    products_all = load_products(Path(args.input))
    store = store_mod.load_store()
    store["source_csv"] = str(Path(args.input).resolve())

    # ---- decide run_id / resume point -------------------------------------
    run_id: str
    resume_phase = "search"
    resume_cursor = 0
    products: list[Product]

    explicit_rerun = bool(args.run_id and args.phase)
    state = None if (args.force or explicit_rerun) else phases.load_run_state()
    requested = products_all[: args.limit] if args.limit > 0 else products_all

    # Only resume if the saved run covers exactly the wines this invocation
    # asks for; otherwise a new --limit would silently continue the old set.
    # (An explicit --phase/--run-id re-run always works on that run's own set.)
    prev_state_run = phases.load_run_json(state["run_id"]) if state else None
    if prev_state_run is not None and (prev_state_run.get("product_ids") or []) != [p.id for p in requested]:
        print(
            f"note: saved run {state['run_id']} covers a different wine set; starting a fresh run",
            file=sys.stderr,
        )
        state, prev_state_run = None, None
        phases.clear_run_state()

    if explicit_rerun:
        # Explicit re-run of a phase over an existing run's logs.
        run_id = args.run_id
        prev = phases.load_run_json(run_id)
        if prev is None:
            sys.exit(f"error: no logs/{run_id}/run.json to re-run from")
        ids = set(prev.get("product_ids") or [])
        products = [p for p in products_all if p.id in ids]
        resume_phase = args.phase
    elif state and phases.load_run_json(state["run_id"]):
        run_id = state["run_id"]
        prev = phases.load_run_json(run_id) or {}
        ids = set(prev.get("product_ids") or [])
        products = [p for p in products_all if p.id in ids]
        resume_phase = state.get("phase", "search")
        resume_cursor = int(state.get("cursor", 0))
    else:
        run_id = args.run_id or phases.new_run_id()
        products = products_all[: args.limit] if args.limit > 0 else products_all
        if args.force:
            phases.clear_run_state()

    sink = EventSink(run_id, run_dir(run_id) / "events.jsonl", json_lines=args.events_json)
    config = phases.RunConfig(
        api_url=args.api_url,
        model=args.model,
        confidence_threshold=args.confidence_threshold,
        producer_gate=not args.no_producer_gate,
        limit=args.limit,
        input_csv=str(Path(args.input).resolve()),
    )
    ctx = phases.RunContext(run_id=run_id, config=config, products=products, sink=sink, store=store)

    existing = phases.load_run_json(run_id)
    if existing is not None and (state or args.phase):
        ctx.run_json = existing
        ctx.run_json["config"] = config.__dict__ | {"resumed_at": phases._now()}
        for ph in PHASES:
            if PHASES.index(ph) >= PHASES.index(resume_phase):
                ctx.run_json["phases"][ph]["status"] = "pending"
        ctx.save_run_json()
    else:
        phases.init_run_json(ctx)

    # Make sure every product in this run has a store row before we start.
    for p in products:
        store_mod.ensure_wine(store, p)
    store_mod.save_store(store)

    sink.info(
        f"Run {run_id}: {len(products)} wines, starting at phase {resume_phase}"
        + (f" (wine {resume_cursor + 1})" if resume_cursor else ""),
        run_id=run_id, total=len(products), phase=resume_phase, cursor=resume_cursor,
        model=args.model, api_url=args.api_url,
    )
    if args.no_producer_gate:
        sink.info("NOTE: --no-producer-gate set; producer-absent gating disabled.")

    try:
        paused = phases.run_all(
            ctx, resume_phase=resume_phase, resume_cursor=resume_cursor, stop_after=args.stop_after,
        )
    except KeyboardInterrupt:
        ctx.run_json["status"] = "interrupted"
        ctx.save_run_json()
        sink.error("Interrupted. Re-run the same command to resume.")
        sink.close()
        sys.exit(130)
    except Exception as exc:  # noqa: BLE001
        ctx.run_json["status"] = "failed"
        ctx.run_json["error"] = f"{type(exc).__name__}: {exc}"
        ctx.save_run_json()
        sink.error(f"Run failed: {type(exc).__name__}: {exc}", error=str(exc))
        sink.close()
        raise

    if paused is not None:
        nxt = PHASES[PHASES.index(paused) + 1]
        sink.emit(
            "paused",
            f"=== Paused after {paused} === re-run to continue with {nxt}",
            phase=paused, next_phase=nxt, run_id=run_id,
        )
        sink.close()
        return

    wines = ctx.store["wines"]
    ids = {p.id for p in products}
    n_model = sum(1 for w in wines if w["id"] in ids and w["tag_status"] == "model")
    n_review = sum(1 for w in wines if w["id"] in ids and w["tag_status"] == "needs_review")
    n_human = sum(1 for w in wines if w["id"] in ids and w["tag_status"] == "human")
    sink.emit(
        "done",
        f"=== Done === model={n_model} needs_review={n_review} human={n_human} -> {WINES_JSON}",
        model=n_model, needs_review=n_review, human=n_human, output=str(WINES_JSON),
    )
    sink.close()


if __name__ == "__main__":
    main()
