"""Offline tests for the scorer's missing-index handling and fact-first
selection, and for the tagger evidence rules. No LLM, no network."""

from __future__ import annotations

import json

import pytest

from fermentation import constants, evidence, scorer, searcher
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


CTX_ONE_SITE = (CTX_ONE.replace("CellarTracker", "Vivino #3") + "\n\n"
                + "[Vivino #4 | match=88]\nAnother Vivino page for the same wine.")


def test_context_snippet_count():
    assert evidence.context_snippet_count(CTX_ONE) == 1
    assert evidence.context_snippet_count(CTX_TWO) == 2
    assert evidence.context_snippet_count("") == 0


def test_context_source_count_folds_numbered_results():
    assert evidence.context_source_count(CTX_ONE) == 1
    assert evidence.context_source_count(CTX_TWO) == 2     # CellarTracker + Vivino
    assert evidence.context_source_count("") == 0
    # Two snippets, one site: snippet count says 2, source count says 1.
    assert evidence.context_snippet_count(CTX_ONE_SITE) == 2
    assert evidence.context_source_count(CTX_ONE_SITE) == 1


def test_unsupported_grapes_by_canonical_name():
    assert evidence.unsupported_grapes(["Tempranillo"], CTX_TWO) == []
    assert evidence.unsupported_grapes(["Cinsault", "Tempranillo"], CTX_TWO) == ["Cinsault"]


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_unsupported_grapes_accepts_library_synonyms():
    # "Garnacha" in the text supports a submitted "Grenache".
    assert evidence.unsupported_grapes(["Grenache"], CTX_TWO) == []


def test_single_source_confidence_is_clamped():
    tags = ParsedTags(country="France", grapes=["Cinsault"], confidence=89)
    reasons = apply_evidence_rules(tags, CTX_ONE)
    assert "single_source" in reasons
    assert tags.confidence == constants.SINGLE_SOURCE_CONFIDENCE_CAP
    assert any(r == "unsupported_grape:Cinsault" for r in reasons)
    assert decide_tag_status(normalized=tags, confidence_threshold=85, review_reasons=reasons) == "needs_review"


def test_several_snippets_from_one_site_are_still_one_source():
    # The old snippet-count rule saw two snippets here and let the row pass.
    tags = ParsedTags(country="Spain", grapes=["Tempranillo"], confidence=95)
    ctx = ("[Vivino #1 | match=95]\nA Red wine from Rioja. Made from Tempranillo.\n\n"
           "[Vivino #2 | match=92]\nRioja Reserva, Tempranillo, from the same shop page.")
    reasons = apply_evidence_rules(tags, ctx)
    assert reasons == ["single_source"]
    assert tags.confidence == constants.SINGLE_SOURCE_CONFIDENCE_CAP
    assert decide_tag_status(normalized=tags, confidence_threshold=85, review_reasons=reasons) == "needs_review"


def test_single_source_routes_to_review_below_the_cap_too():
    # A hard route, so it holds however low the threshold is set.
    tags = ParsedTags(country="Spain", grapes=["Tempranillo"], confidence=60)
    ctx = "[Vivino #1 | match=95]\nA Red wine from Rioja. Made from Tempranillo."
    reasons = apply_evidence_rules(tags, ctx)
    assert reasons == ["single_source"]
    assert tags.confidence == 60        # already below the cap; not raised to it
    assert decide_tag_status(normalized=tags, confidence_threshold=50, review_reasons=reasons) == "needs_review"


CTX_BOTH_NAME_IT = CTX_TWO + "\n\n[Wine.com #1 | match=95]\nRioja Crianza, 100% Tempranillo."


def test_supported_grapes_and_two_snippets_pass():
    tags = ParsedTags(country="Spain", grapes=["Tempranillo"], confidence=90)
    reasons = apply_evidence_rules(tags, CTX_BOTH_NAME_IT)
    assert reasons == []
    assert tags.confidence == 90
    assert decide_tag_status(normalized=tags, confidence_threshold=85, review_reasons=reasons) == "model"


def test_grape_named_by_one_source_is_uncorroborated():
    # Two sources in context, but only Vivino names Tempranillo.
    assert evidence.grape_source_counts(["Tempranillo", "Cinsault"], CTX_TWO) == {"Tempranillo": 1, "Cinsault": 0}
    tags = ParsedTags(country="Spain", grapes=["Tempranillo"], confidence=90)
    reasons = apply_evidence_rules(tags, CTX_TWO)
    assert reasons == ["uncorroborated_grape:Tempranillo"]
    assert decide_tag_status(normalized=tags, confidence_threshold=85, review_reasons=reasons) == "needs_review"


def test_grape_source_counts_fold_numbered_results():
    ctx = ("[Vivino #1 | match=95]\nMade from Tempranillo.\n\n"
           "[Vivino #2 | match=92]\nTempranillo again.\n\n[CellarTracker | match=90]\nA red Rioja.")
    assert evidence.grape_source_counts(["Tempranillo"], ctx) == {"Tempranillo": 1}


def test_uncorroborated_is_not_stacked_on_single_source():
    tags = ParsedTags(country="Spain", grapes=["Tempranillo"], confidence=80)
    reasons = apply_evidence_rules(tags, "[Vivino #1 | match=95]\nMade from Tempranillo.")
    assert reasons == ["single_source"]


def test_blend_with_one_named_grape_routes_to_review():
    tags = ParsedTags(country="Portugal", grapes=["Touriga Nacional"], is_blend=True, confidence=95)
    ctx = ("[Vivino #1 | match=95]\nMade from Touriga Nacional.\n\n"
           "[Wine.com #1 | match=90]\nA blend of indigenous varietals, led by Touriga Nacional.")
    reasons = apply_evidence_rules(tags, ctx)
    assert reasons == ["incomplete_blend"]
    assert decide_tag_status(normalized=tags, confidence_threshold=85, review_reasons=reasons) == "needs_review"


def test_every_review_route_records_a_reason():
    # Below the threshold on the model's own say-so (Mont Gravet at 80).
    tags = ParsedTags(country="Spain", grapes=["Tempranillo"], confidence=80)
    assert apply_evidence_rules(tags, CTX_BOTH_NAME_IT, confidence_threshold=85) == ["low_confidence"]
    tags = ParsedTags(country="Spain", grapes=["Tempranillo"], confidence=85)
    assert apply_evidence_rules(tags, CTX_BOTH_NAME_IT, confidence_threshold=85) == []
    # No grapes submitted.
    tags = ParsedTags(country="Spain", grapes=[], confidence=90)
    assert apply_evidence_rules(tags, CTX_BOTH_NAME_IT, confidence_threshold=85) == ["no_grapes"]
    # The model never got a submission accepted.
    assert apply_evidence_rules(None, CTX_TWO) == ["no_submit"]


def test_single_source_clamp_does_not_add_low_confidence():
    # The model said 90; the clamp to 69 is single_source's doing, not the model's.
    tags = ParsedTags(country="Spain", grapes=["Tempranillo"], confidence=90)
    reasons = apply_evidence_rules(tags, "[Vivino #1 | match=95]\nMade from Tempranillo.", confidence_threshold=85)
    assert reasons == ["single_source"]


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_coarse_region_when_context_names_a_finer_one():
    ctx = ("[Wine.com #1 | match=100]\nG.D. Vajra Barolo Albe 2021 from Barolo, Piedmont, Italy.\n\n"
           "[Vivino #1 | match=90]\nA Red wine from Piemonte, Italy. Made from Nebbiolo.")
    assert evidence.finer_regions_named(["Piedmont"], ctx, country="Italy",
                                        product_name="Vajra Barolo Albe") == ["Barolo"]
    tags = ParsedTags(country="Italy", region=["Piedmont"], grapes=["Nebbiolo"], confidence=85)
    reasons = apply_evidence_rules(tags, ctx, product_name="Vajra Barolo Albe")
    assert "coarse_region:Barolo" in reasons
    # The precise answer, parents included, has nothing finer to point at.
    assert evidence.finer_regions_named(["Barolo", "Langhe", "Piedmont"], ctx, country="Italy",
                                        product_name="Vajra Barolo Albe") == []


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_coarse_region_ignores_a_region_inside_the_producer_name():
    name = "La Rioja Alta Ardanza"
    ctx = "[Vivino #1 | match=95]\nLa Rioja Alta S.A. Vina Ardanza Reserva, a Red wine from Rioja."
    assert evidence.finer_regions_named(["Rioja"], ctx, country="Spain", product_name=name) == []
    # A mention of the sub-zone on its own still counts.
    ctx += "\n\n[Wine.com #1 | match=90]\nFruit from the Rioja Alta sub-zone."
    assert evidence.finer_regions_named(["Rioja"], ctx, country="Spain", product_name=name) == ["Rioja Alta"]


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_coarse_region_ignores_where_the_winery_is():
    ctx = ("[Region Q #2 | match=95]\nBodegas Faustino, located in Oyon, Rioja Alavesa, makes Faustino VII.\n\n"
           "[Vivino #1 | match=90]\nA Red wine from Rioja, Spain.")
    assert evidence.finer_regions_named(["Rioja"], ctx, country="Spain", product_name="Faustino VII Rioja") == []


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


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_submit_tags_accepts_a_blend_with_one_named_grape():
    from fermentation.library_mcp import server
    res = server.submit_tags("Portugal", ["Lisboa"], ["Touriga Nacional"], True, False, 90)
    assert res["ok"], res
    assert res["warnings"] == ["incomplete_blend"]
    assert res["normalized"]["is_blend"] is True
    # Two grapes still cannot be a single varietal.
    res = server.submit_tags("Portugal", ["Lisboa"], ["Touriga Nacional", "Syrah"], False, False, 90)
    assert not res["ok"] and "is_blend_mismatch" in res["issues"]


# ---------------------------------------------------------------------------
# scorer content gates and region-blurb stripping
# ---------------------------------------------------------------------------

def test_search_echo_is_dropped_but_a_matched_search_page_is_kept():
    assert scorer._is_search_echo(
        "Find the best local price for bila haut. Find and shop from stores and merchants near you in USA")
    assert scorer._is_search_echo(
        "Find the best local price for a badenhorst curator white coastal. Find and shop from stores and merchants near you.")
    assert not scorer._is_search_echo(
        "Find the best local price for Vilafonte Seriously Old Dirt Red, Paarl, South Africa. "
        "Avg Price (ex-tax) $38 / 750ml. Find and shop from stores and merchants near you in USA")


def test_colour_conflict_reads_the_url_slug():
    red = _product("Bila Haut Roussillon")
    assert scorer._colour_conflict(red, "https://www.vivino.com/en/m-chapoutier-les-vignes-de-bila-haut-cotes-du-roussillon-blanc/w/2256359")
    assert scorer._colour_conflict(red, "https://www.wine.com/product/bila-haut-by-michel-chapoutier-cotes-du-roussillon-blanc-2024/3636735")
    assert not scorer._colour_conflict(red, "https://www.vivino.com/en/m-chapoutier-les-vignes-de-bila-haut-cotes-du-roussillon-villages/w/20677")
    white = _product("Curator White"); white.category = "White"
    # Wine-Searcher's trailing related-query segment is not the slug.
    assert not scorer._colour_conflict(white, "https://www.wine-searcher.com/find/a+badenhorst+the+curator+white+coastal+western+cape+south+africa/1/-/a+badenhorst+red+swartland")
    assert not scorer._colour_conflict(white, "https://www.totalwine.com/wine/white-wine/chardonnay/excelsior-chardonnay/p/97127750")
    # A colour word in the product name is not a conflict; no category, no check.
    rose = _product("Mont Gravet Rose"); rose.category = "Rose"
    assert not scorer._colour_conflict(rose, "https://example.com/mont-gravet-rose-2024")
    assert scorer._colour_conflict(rose, "https://example.com/mont-gravet-blanc-2024")
    unknown = _product("La Rioja Alta Ardanza"); unknown.category = None
    assert not scorer._colour_conflict(unknown, "https://example.com/la-rioja-alta-blanco")


def test_content_gates_keep_dropped_snippets_out_of_context(monkeypatch):
    product = _product("Bila Haut Roussillon")
    snippets = [
        Snippet(source="Vivino #1", domain="vivino.com", url="https://www.vivino.com/en/bila-haut-cotes-du-roussillon-blanc/w/1",
                body="M. Chapoutier Bila-Haut Cotes du Roussillon Blanc. Made from Grenache Blanc, Macabeo."),
        Snippet(source="Wine Searcher #1", domain="wine-searcher.com", url="https://www.wine-searcher.com/find/bila+haut",
                body="Find the best local price for bila haut. Find and shop from stores and merchants near you in USA"),
        Snippet(source="Wine.com #1", domain="wine.com", url="https://www.wine.com/product/bila-haut-villages-2022/1",
                body="Bila-Haut Cotes du Roussillon Villages, a blend of Syrah, Grenache and Carignan."),
    ]
    monkeypatch.setattr(scorer, "_call_llm",
                        lambda *a, **k: json.dumps({str(i): {"score": 95, "facts": ["producer"]} for i in range(3)}))
    ctx, scored = scorer.score_and_assemble(product, snippets, api_url="", model="")
    assert [s.dropped_reason for s in scored] == ["colour_conflict", "search_page", None]
    assert "Villages" in ctx and "Macabeo" not in ctx and "local price" not in ctx


def test_region_blurb_sentences_are_stripped():
    blurb = ("Cabernet, Merlot, Mourvedre, Grenache, and Syrah are some of the most important red grapes "
             "in the region. The name comes from a combination of two distinct regions.")
    assert searcher._clean_snippet_text(blurb) == ""
    mixed = blurb + " The Domaine Lafage Tessellae GSM Old Vines is a Grenache, Syrah, Mourvedre blend."
    assert searcher._clean_snippet_text(mixed) == (
        "The Domaine Lafage Tessellae GSM Old Vines is a Grenache, Syrah, Mourvedre blend.")
    rioja = "Rioja is classified as DOCa. Its two most important red grapes are Tempranillo and Garnacha. Grape Profile: x"
    assert searcher._clean_snippet_text(rioja) == "Rioja is classified as DOCa. Grape Profile: x"


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


# ---------------------------------------------------------------------------
# Engine answer-blobs (2026-09-15 accuracy review)
# ---------------------------------------------------------------------------

def _body(source, body, url):
    return Snippet(source=source, domain="*", body=body, url=url)


def _vocab(prefix: str, n: int) -> list[str]:
    """n distinct words. `searcher._word_set` keeps only [a-z]{3,}, so numbered
    tokens ("word1", "word2") would all fold to one word and every fixture would
    look like a perfect duplicate of itself."""
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    return [f"{prefix}{alphabet[i // 26]}{alphabet[i % 26]}" for i in range(n)]


def test_aggregate_body_is_trimmed_to_its_own_page():
    """Curator White: the 'grapewitches.com' snippet spliced in two other
    results, one of which named a different vintage's blend, and the tagger
    submitted the union of both grape lists."""
    own = ("Winemaker Adi Badenhorst's idea behind the Curator is unpretentious "
           "drinkability, mostly from plots of bush-vines in granite and slate soils. ") * 6
    seg_a = "The grapes for the Curator White are grown in the Swartland region on the West Coast of Southern Africa."
    seg_b = "Made from Semillon, Chardonnay, Chenin Blanc. This wine has 227 mentions of tree fruit notes."
    snips = [
        _body("Grapes Q #1", own + seg_a + " " + seg_b, "https://grapewitches.com/curator"),
        _body("Grapes Q #2", seg_a, "https://winegoddess.com/curator"),
        _body("Region Q #2", seg_b, "https://vivino.com/curator"),
    ]
    out, trimmed = searcher.split_aggregate_bodies(snips)
    assert trimmed == 1
    assert out[0].body == own.strip()
    assert "Semillon" not in out[0].body
    # the absorbed segments survive under their own URLs and source labels
    assert [s.source for s in out] == ["Grapes Q #1", "Grapes Q #2", "Region Q #2"]


def test_aggregate_with_nothing_of_its_own_is_dropped():
    seg_a = "A" * 120
    seg_b = "B" * 120
    snips = [
        _body("Region Q #3", seg_a + " " + seg_b + " tail " + "C" * 600, "https://falstaff.com/x"),
        _body("Region Q #1", seg_a, "https://vivino.com/x"),
        _body("Region Q #2", seg_b, "https://wine.com/x"),
    ]
    out, trimmed = searcher.split_aggregate_bodies(snips)
    assert trimmed == 1
    assert [s.source for s in out] == ["Region Q #1", "Region Q #2"]


def test_short_bodies_and_same_url_are_never_treated_as_aggregates():
    seg = "x" * 100
    short = _body("Wine.com #1", seg + seg, "https://wine.com/a")          # under the blob floor
    same_url = _body("Region Q #1", seg * 12, "https://vivino.com/w")
    other = _body("Region Q #2", seg, "https://vivino.com/w")               # same URL -> not foreign
    out, trimmed = searcher.split_aggregate_bodies([short, same_url, other])
    assert trimmed == 0 and len(out) == 3


def test_same_blob_under_different_urls_is_deduped_despite_low_jaccard():
    """Chocapalha Tinto: one merchant sentence came back from vivino.com,
    vivino.com/US and falstaff.com. Each copy was truncated at a different
    offset, so Jaccard stayed under SNIPPET_DEDUPE_JACCARD and all three were
    kept as separate evidence."""
    shared = " ".join(_vocab("shared", 400))
    a = shared + " " + " ".join(_vocab("taila", 40))
    b = shared + " " + " ".join(_vocab("tailb", 40))
    assert len(a) >= constants.SNIPPET_BLOB_MIN_CHARS
    snips = [_body("Region Q #1", a, "https://vivino.com/w"),
             _body("Region Q #2", b, "https://falstaff.com/w")]
    words = lambda t: searcher._word_set(t)
    jac = len(words(a) & words(b)) / len(words(a) | words(b))
    assert jac < constants.SNIPPET_DEDUPE_JACCARD          # the old rule misses it
    kept, dropped = searcher.dedupe_near_duplicates(snips)
    assert dropped == 1 and [s.source for s in kept] == ["Region Q #1"]


def test_containment_does_not_collapse_a_short_snippet_into_a_long_one():
    """A short body's words are routinely a subset of a long one's without the
    two being duplicates — containment is only applied between two long bodies."""
    long_body = " ".join(_vocab("long", 400))
    short = " ".join(_vocab("long", 20))
    assert len(short) < constants.SNIPPET_BLOB_MIN_CHARS
    kept, dropped = searcher.dedupe_near_duplicates(
        [_body("Region Q #1", long_body, "https://a.com/w"),
         _body("Wine.com #1", short, "https://b.com/w")]
    )
    assert dropped == 0 and len(kept) == 2


# ---------------------------------------------------------------------------
# Name-coverage note (2026-09-15 accuracy review)
# ---------------------------------------------------------------------------

_CURATOR = ("Badenhorst Curator White Blend 2020 from South Africa - Chenin Blanc, "
            "Chardonnay, and Viognier. Adi Badenhorst has the unique ability to "
            "fashion spectacular wines at all levels of the price spectrum.")
_PORTFOLIO = ("Chateau Coupe Roses Chateau De Caladroy Chateau De Lascaux Chateau "
              "Puech-Haut Domaine De La Baume Mont Gravet Domaine Lafage")


def test_coverage_note_fires_when_every_name_word_is_present():
    snip = Snippet(source="Wine.com #1", domain="wine.com", body=_CURATOR,
                   url="https://www.wine.com/product/badenhorst-curator-white-blend-2020/782236")
    note = scorer._name_coverage_note(_product("Curator White"), snip, ["curator"])
    assert '"curator"' in note and "every distinctive word" in note


def test_coverage_note_is_withheld_from_a_portfolio_index():
    """Winebow's index page contains both "mont" and "gravet" by accident;
    asserting coverage there promoted it from 0 to 70."""
    snip = Snippet(source="Winebow (distributor) #3", domain="winebow.com",
                   body=_PORTFOLIO, url="https://www.winebow.com/brands")
    assert scorer._is_list_page(_PORTFOLIO)
    assert scorer._name_coverage_note(_product("Mont Gravet Rose"), snip,
                                      ["mont", "gravet"]) == ""


def test_coverage_note_needs_every_token_not_just_one():
    snip = Snippet(source="Wine.com #1", domain="wine.com", body=_CURATOR, url="")
    assert scorer._name_coverage_note(_product("Curator White"), snip,
                                      ["curator", "tessellae"]) == ""


def test_short_bodies_are_never_called_list_pages():
    """A three-word title is trivially all-capitals; the ratio means nothing."""
    assert not scorer._is_list_page("Badenhorst Curator White")
    assert not scorer._is_list_page("")


def test_coverage_note_reaches_the_prompt_alongside_the_url_hint(monkeypatch):
    seen = {}
    monkeypatch.setattr(scorer, "_call_llm", lambda p, *a, **k: seen.setdefault("p", p) and "{}")
    snippets = [
        _snip(0, _CURATOR, url="https://www.wine.com/product/badenhorst-curator-white-blend-2020/1"),
        _snip(1, _PORTFOLIO, url="https://www.winebow.com/brands"),
    ]
    scorer._batch_match_score(_product("Curator White"), snippets, "u", "m")
    assert seen["p"].count("every distinctive word of the product name") == 1
