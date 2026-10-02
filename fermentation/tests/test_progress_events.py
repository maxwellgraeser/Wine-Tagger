"""Offline tests for the events the dashboard's progress bars are built from:
`run_plan` at the start of an invocation, and `wine_start` / `progress`
inside each phase loop. No LLM, no network, nothing written to disk."""

from __future__ import annotations

import json

from fermentation import phases, searcher, store as store_mod
from fermentation.events import EventSink
from fermentation.types import Product


def _product(pid: str, name: str) -> Product:
    return Product(id=pid, name=name, sku=None, brand=None, category="Red",
                   supply_price=None, retail_price=None, supplier=None, items_sold=None,
                   margin_pct=None, sale_count=None, customer_count=None, avg_sale_value=None)


def _events(capsys) -> list[dict]:
    return [json.loads(ln) for ln in capsys.readouterr().out.splitlines() if ln.strip()]


# ---------------------------------------------------------------------------
# run_plan
# ---------------------------------------------------------------------------

def test_run_plan_fresh_run_has_every_phase_to_do():
    assert phases.run_plan(24, "search", 0) == {
        "search": {"state": "pending", "done": 0},
        "score": {"state": "pending", "done": 0},
        "tag": {"state": "pending", "done": 0},
    }


def test_run_plan_resume_mid_phase_marks_earlier_phases_done():
    assert phases.run_plan(24, "score", 11) == {
        "search": {"state": "done", "done": 24},
        "score": {"state": "pending", "done": 11},
        "tag": {"state": "pending", "done": 0},
    }


def test_run_plan_rerun_from_tag():
    plan = phases.run_plan(24, "tag", 0)
    assert plan["search"] == plan["score"] == {"state": "done", "done": 24}
    assert plan["tag"] == {"state": "pending", "done": 0}


def test_run_plan_event_carries_the_plan(capsys):
    sink = EventSink("r1", None, json_lines=True)
    sink.run_plan(24, "score", 11, "score", phases.run_plan(24, "score", 11))
    (ev,) = _events(capsys)
    assert ev["type"] == "run_plan"
    assert ev["total"] == 24 and ev["resume_phase"] == "score" and ev["cursor"] == 11
    assert ev["stop_after"] == "score"
    assert ev["phases"]["score"] == {"state": "pending", "done": 11}
    assert ev["message"] == "Plan: 24 wines; search done, score from wine 12, tag to do (pausing after score)"


# ---------------------------------------------------------------------------
# wine_start / progress in a phase loop
# ---------------------------------------------------------------------------

def test_search_loop_announces_each_wine_and_flags_skips(monkeypatch, capsys):
    products = [_product("a", "Aster"), _product("h", "Human Wine"), _product("c", "Cloudline")]
    store = store_mod.empty_store()
    store_mod.ensure_wine(store, products[1])["tag_status"] = "human"

    monkeypatch.setattr(searcher, "gather_snippets", lambda product, return_errors: ([], [], 0))
    monkeypatch.setattr(phases, "_write_log", lambda *a, **k: None)
    monkeypatch.setattr(phases, "_checkpoint", lambda *a, **k: None)
    monkeypatch.setattr(phases.RunContext, "save_run_json", lambda self: None)

    ctx = phases.RunContext(
        run_id="r1", config=phases.RunConfig(api_url="", model="", confidence_threshold=80),
        products=products, sink=EventSink("r1", None, json_lines=True), store=store,
    )
    ctx.run_json = {"phases": {ph: {"status": "pending", "started_at": None} for ph in phases.PHASES}}
    phases.run_search(ctx)

    seq = [(e["type"], e.get("index"), e.get("skipped", False)) for e in _events(capsys)
           if e["type"] in ("wine_start", "progress")]
    assert seq == [
        ("wine_start", 0, False), ("progress", 0, False),
        ("progress", 1, True),  # a human-edited wine: no wine_start, flagged as a skip
        ("wine_start", 2, False), ("progress", 2, False),
    ]
