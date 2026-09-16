"""Offline tests for the scorer's missing-index handling and fact-first
selection, and for the tagger evidence rules. No LLM, no network."""

from __future__ import annotations

import json

import pytest

from fermentation import constants, evidence, scorer
from fermentation.phases import apply_evidence_rules, decide_tag_status
from fermentation.types import ParsedTags, Product, ScoredSnippet, Snippet


def _product(name="Aster Ribera del Duero", brand=None) -> Product:
    return Product(id="p1", name=name, sku=None, brand=brand, category="Red",
                   supply_price=None, retail_price=None, supplier=None, items_sold=None,
                   margin_pct=None, sale_count=None, customer_count=None, avg_sale_value=None)


def _snip(i: int, body: str, source="Vivino", url="https://vivino.com/x") -> Snippet:
    return Snippet(source=f"{source} #{i}", domain="vivino.com", body=body, url=url)


# ---------------------------------------------------------------------------
# scorer: every index gets scored, missing ones are re-asked
# ---------------------------------------------------------------------------

def test_missing_indices_are_reasked_not_zeroed(monkeypatch):
    snippets = [_snip(i, f"Bodegas Aster Ribera del Duero snippet {i}") for i in range(5)]
    replies = []

    def fake_llm(prompt, api_url, model, timeout=0):
        # First call: answer only some indices. Later calls: answer everything asked.
        asked = [int(x) for x in prompt.split("EVERY index ")[1].split(".")[0].split(", ")]
        replies.append(asked)
        if len(replies) == 1:
            answer = {str(i): {"score": 90, "facts": ["grape"]} for i in asked[:2]}
        else:
            answer = {str(i): {"score": 20, "facts": []} for i in asked}
        return json.dumps(answer)

    monkeypatch.setattr(scorer, "_call_llm", fake_llm)
    monkeypatch.setattr(constants, "SCORING_BATCH_SIZE", 8)
    results, raw = scorer._batch_match_score(_product(), snippets, "u", "m")
    assert set(results) == {0, 1, 2, 3, 4}
    assert results[0] == (90, ["grape"])
    assert results[3] == (20, [])
    assert raw["missing"] == []
    assert replies[0] == [0, 1, 2, 3, 4]
    assert replies[1] == [2, 3, 4]


def test_never_scored_is_marked_unscored(monkeypatch):
    snippets = [_snip(i, f"Bodegas Aster snippet {i}") for i in range(3)]
    monkeypatch.setattr(scorer, "_call_llm", lambda *a, **k: json.dumps({"0": 95}))
    _ctx, scored = scorer.score_and_assemble(_product(), snippets, api_url="u", model="m",
                                             producer_gate=False)
    assert scored[0].match_score == 95 and scored[0].dropped_reason is None
    assert scored[1].dropped_reason == "unscored"
    assert scored[2].dropped_reason == "unscored"


def test_bare_int_replies_still_parse():
    assert scorer._parse_entry(88) == (88, [])
    assert scorer._parse_entry({"score": "70", "facts": ["Grape", "bogus"]}) == (70, ["grape"])
    assert scorer._parse_entry({"facts": ["grape"]}) is None


def test_prompt_shows_url_and_index_list(monkeypatch):
    seen = {}
    monkeypatch.setattr(scorer, "_call_llm", lambda p, *a, **k: seen.setdefault("p", p) and "{}")
    snippets = [_snip(0, "A White wine from Calabria. Made from Greco Bianco.",
                      url="https://www.vivino.com/en/librandi-ciro-bianco/w/1")]
    scorer._batch_match_score(_product("Librandi Ciro Bianco"), snippets, "u", "m")
    assert "https://www.vivino.com/en/librandi-ciro-bianco/w/1" in seen["p"]
    assert "EVERY index 0." in seen["p"]


# ---------------------------------------------------------------------------
# scorer: fact coverage decides context, score only gates
# ---------------------------------------------------------------------------

def test_context_prefers_fact_rich_snippets_over_price_pages():
    def ss(i, score, facts, source):
        return ScoredSnippet(snippet=_snip(i, f"body {i}", source=source), match_score=score,
                             cleaned_body=f"body {i}", facts=facts)
    scored = [
        ss(0, 98, [], "Wine Searcher"),
        ss(1, 98, [], "Total Wine"),
        ss(2, 90, ["grape", "region"], "Wine.com"),
        ss(3, 95, ["region"], "Vivino"),
        ss(4, 98, [], "CellarTracker"),
        ss(5, 97, [], "fallback"),
    ]
    ctx = scorer._build_web_context(scored, threshold=85, top_n=2)
    chosen = [s for s in scored if s.in_context]
    assert [s.snippet.source for s in chosen] == ["Wine.com #2", "Vivino #3"]
    assert ctx.startswith("[Wine.com #2 | match=90]")


def test_score_below_threshold_never_enters_context_even_with_facts():
    s = ScoredSnippet(snippet=_snip(0, "b"), match_score=50, cleaned_body="b", facts=["grape"])
    assert scorer._build_web_context([s], threshold=85, top_n=5) is None


# ---------------------------------------------------------------------------
# evidence rules
# ---------------------------------------------------------------------------

CTX_ONE = "[CellarTracker | match=89]\nCommunity wine reviews on 2017 M. Chapoutier Bila-Haut V.I.T."
CTX_TWO = CTX_ONE + "\n\n[Vivino #1 | match=90]\nA Red wine from Rioja. Made from Tempranillo and Garnacha."


def test_context_snippet_count():
    assert evidence.context_snippet_count(CTX_ONE) == 1
    assert evidence.context_snippet_count(CTX_TWO) == 2
    assert evidence.context_snippet_count("") == 0


def test_unsupported_grapes_by_canonical_name():
    assert evidence.unsupported_grapes(["Tempranillo"], CTX_TWO) == []
    assert evidence.unsupported_grapes(["Cinsault", "Tempranillo"], CTX_TWO) == ["Cinsault"]


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_unsupported_grapes_accepts_library_synonyms():
    # "Garnacha" in the text supports a submitted "Grenache".
    assert evidence.unsupported_grapes(["Grenache"], CTX_TWO) == []


def test_single_snippet_confidence_is_clamped():
    tags = ParsedTags(country="France", grapes=["Cinsault"], confidence=89)
    reasons = apply_evidence_rules(tags, CTX_ONE)
    assert "single_snippet_cap" in reasons
    assert tags.confidence == constants.SINGLE_SNIPPET_CONFIDENCE_CAP
    assert any(r == "unsupported_grape:Cinsault" for r in reasons)
    assert decide_tag_status(normalized=tags, confidence_threshold=85, review_reasons=reasons) == "needs_review"


def test_supported_grapes_and_two_snippets_pass():
    tags = ParsedTags(country="Spain", grapes=["Tempranillo"], confidence=90)
    reasons = apply_evidence_rules(tags, CTX_TWO)
    assert reasons == []
    assert tags.confidence == 90
    assert decide_tag_status(normalized=tags, confidence_threshold=85, review_reasons=reasons) == "model"


def test_unsupported_grape_routes_to_review_even_at_high_confidence():
    tags = ParsedTags(country="Spain", grapes=["Tempranillo"], confidence=98)
    ctx = "[A | match=98]\nBodegas Aster, Ribera del Duero.\n\n[B | match=98]\nShop Aster Crianza."
    reasons = apply_evidence_rules(tags, ctx)
    assert reasons == ["unsupported_grape:Tempranillo"]
    assert decide_tag_status(normalized=tags, confidence_threshold=85, review_reasons=reasons) == "needs_review"


# ---------------------------------------------------------------------------
# category inference
# ---------------------------------------------------------------------------

def test_generic_synonym_does_not_count_as_grape_evidence():
    # "Tinto" is a library synonym of Tempranillo but here it is just the product name.
    ctx = "[A | match=98]\nQuinta de Chocapalha Tinto, Vinho Regional Lisboa.\n\n[B | match=98]\nA blend of indigenous Portuguese varietals."
    assert evidence.unsupported_grapes(["Tempranillo"], ctx) == ["Tempranillo"]


def test_model_category_fills_blank_and_survives_csv_refresh():
    from fermentation import store as store_mod
    product = _product("La Rioja Alta Ardanza")
    product.category = None                              # the one CSV row with no category
    st = {"wines": []}
    row = store_mod.ensure_wine(st, product)
    tags = ParsedTags(country="Spain", grapes=["Tempranillo"], confidence=90, category="Red")
    store_mod.apply_tags(row, tags, "ctx", "model", False, "run1")
    assert row["category"] == "Red" and row["category_source"] == "model"
    # Next run refreshes catalog fields from the CSV, which still has no category.
    row = store_mod.ensure_wine(st, product)
    assert row["category"] == "Red"
    # When the CSV finally has one, it wins and the marker goes away.
    product.category = "White"
    row = store_mod.ensure_wine(st, product)
    assert row["category"] == "White" and "category_source" not in row


def test_csv_category_is_never_overwritten_by_model():
    from fermentation import store as store_mod
    product = _product("Zenato Pinot Grigio"); product.category = "White"
    st = {"wines": []}
    row = store_mod.ensure_wine(st, product)
    store_mod.apply_tags(row, ParsedTags(country="Italy", grapes=["Pinot Grigio"], confidence=90, category="Red"),
                         "ctx", "model", False, "run1")
    assert row["category"] == "White" and "category_source" not in row


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_submit_tags_category():
    from fermentation.library_mcp import server
    ok = server.submit_tags("Spain", ["Rioja"], ["Tempranillo"], False, False, 90, category="rosé")
    assert ok["ok"] and ok["normalized"]["category"] == "Rose"
    none = server.submit_tags("Spain", ["Rioja"], ["Tempranillo"], False, False, 90)
    assert none["ok"] and none["normalized"]["category"] is None
    bad = server.submit_tags("Spain", ["Rioja"], ["Tempranillo"], False, False, 90, category="orange")
    assert not bad["ok"] and "unknown_category" in bad["issues"]


# ---------------------------------------------------------------------------
# searcher retry on partial throttling
# ---------------------------------------------------------------------------

def test_search_retries_when_most_queries_errored():
    from fermentation import searcher
    raw = [Snippet(source="Wine Searcher (UPC) #1", domain="", body="x", url="u"),
           Snippet(source="Wine Searcher (UPC) #2", domain="", body="x", url="u2"),
           Snippet(source="CellarTracker", domain="", body="x", url="u3")]
    errs = [{"source": f"q{i}", "query": "", "error": "TimeoutException"} for i in range(9)]
    assert searcher._mostly_failed(raw, errs)                      # 9 errors vs 2 sources
    assert searcher._mostly_failed([], [])                          # nothing at all
    assert not searcher._mostly_failed(raw, [])                     # clean run
    assert not searcher._mostly_failed(raw, [{"source": "*", "query": "", "error": "3 off-site"}])
    assert not searcher._mostly_failed(raw, errs[:1])               # one failure out of three


def test_scorer_flags_name_only_in_url(monkeypatch):
    seen = {}
    monkeypatch.setattr(scorer, "_call_llm", lambda p, *a, **k: seen.setdefault("p", p) and "{}")
    snippets = [
        _snip(0, "A Red wine from Ribera del Duero. Made from Tempranillo.",
              url="https://www.vivino.com/en/es-aster-reserva/w/1"),
        _snip(1, "Bodegas Aster Ribera del Duero Crianza", url="https://x.com/y"),
    ]
    scorer._batch_match_score(_product("Aster Ribera del Duero"), snippets, "u", "m")
    assert seen["p"].count('[note: "aster" from the product name appears in this URL') == 1
    assert seen["p"].index("[note:") < seen["p"].index("A Red wine from Ribera")
