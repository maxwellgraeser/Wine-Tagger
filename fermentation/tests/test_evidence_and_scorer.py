"""Offline tests for the scorer's missing-index handling and fact-first
selection, and for the tagger evidence rules. No LLM, no network."""

from __future__ import annotations

import json

import pytest

from fermentation import constants, evidence, library_text, phases, scorer, searcher
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

needs_library = pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")


def _ss(i, score, body, source, facts=()):
    return ScoredSnippet(snippet=_snip(i, body, source=source), match_score=score,
                         cleaned_body=body, facts=list(facts))


@needs_library
def test_context_prefers_snippets_that_name_grapes_over_price_pages():
    scored = [
        _ss(0, 98, "Buy now, $14.99, free shipping over $100.", "Wine Searcher"),
        _ss(1, 98, "In stock. Add to cart.", "Total Wine"),
        _ss(2, 90, "A white wine from Languedoc, made from Picpoul Blanc.", "Wine.com"),
        _ss(3, 95, "A white wine from Languedoc, France.", "Vivino"),
        _ss(4, 98, "Community score 88 from 12 notes.", "CellarTracker"),
        _ss(5, 97, "Great value white.", "fallback"),
    ]
    ctx = scorer._build_web_context(scored, threshold=85, top_n=2)
    chosen = [s for s in scored if s.in_context]
    assert [s.snippet.source for s in chosen] == ["Wine.com #2", "Vivino #3"]
    assert ctx.startswith("[Wine.com #2 | match=90]")


@needs_library
def test_llm_facts_no_longer_decide_the_pick():
    # Chapelle Bastion Picpoul, 2026-09-28: the scorer gave every survivor the
    # same score and facts, so the tie went to result #1, a listing line.
    # Result #2 names the grape in its text and must win.
    rubber_stamp = ["grape", "producer", "region"]
    scored = [
        _ss(1, 95, "Top 25 Languedoc whites under $20: Chapelle Bastion Picpoul de Pinet.",
            "Vivino", rubber_stamp),
        _ss(2, 95, "Chapelle Bastion Picpoul de Pinet. A white wine from Languedoc, France. "
                   "Made from Picpoul Blanc.", "Vivino", rubber_stamp),
    ]
    scorer._build_web_context(scored, threshold=85, top_n=1)
    assert [s.snippet.source for s in scored if s.in_context] == ["Vivino #2"]


@needs_library
def test_text_facts_region_name_alone_is_not_the_grape():
    facts = library_text.text_facts("Chapelle Bastion Picpoul de Pinet 2023")
    assert facts == {"grapes": [], "regions": ["Picpoul de Pinet"]}
    facts = library_text.text_facts("Made from Picpoul grapes from Picpoul-de-Pinet.")
    assert facts == {"grapes": ["Picpoul Blanc"], "regions": ["Picpoul de Pinet"]}


@needs_library
def test_text_facts_longest_grape_name_wins():
    # Massaya's producer sheet: "Sauvignon" inside "Cabernet Sauvignon" is not
    # Sauvignon Blanc, so the sheet names three grapes and keeps its credit.
    facts = library_text.text_facts("Cinsault, Cabernet Sauvignon and Syrah from the Bekaa Valley.")
    assert facts["grapes"] == ["Cinsault", "Cabernet Sauvignon", "Syrah"]
    assert library_text.text_facts("Cabernet Sauvignon")["grapes"] == ["Cabernet Sauvignon"]
    # A comma ends a name: a list's "Cabernet, Sauvignon Blanc" is not Cabernet Sauvignon.
    assert library_text.text_facts("Cabernet, Sauvignon Blanc")["grapes"] == ["Sauvignon Blanc"]


@needs_library
def test_text_facts_skips_generic_words():
    # Library synonyms and region names that are ordinary words.
    assert library_text.text_facts("Quinta de Chocapalha Tinto, Mediterranean herbs, central palate") \
        == {"grapes": [], "regions": []}
    # "Italia" and "Mission" are library grapes, but not here.
    assert library_text.text_facts("Un vino rosso da Piemonte, Italia. Da uve Nebbiolo.")["grapes"] == ["Nebbiolo"]
    assert library_text.text_facts("Toasty oak and a hint of mission fig.")["grapes"] == []


@needs_library
def test_grape_list_page_gets_no_grape_credit():
    listing = _ss(1, 95, "Shop Piedmont reds: Nebbiolo, Barbera, Dolcetto, Freisa.", "Wine Searcher (UPC)")
    blend = _ss(2, 90, "A red from Piedmont, 100% Nebbiolo.", "Wine Searcher (UPC)")
    assert len(library_text.text_facts(listing.snippet.body)["grapes"]) == constants.SNIPPET_GRAPE_LIST_MIN
    scorer._build_web_context([listing, blend], threshold=85, top_n=1)
    assert blend.in_context and not listing.in_context


@needs_library
def test_every_scored_snippet_logs_its_text_facts(monkeypatch):
    snippets = [_snip(0, "Made from Tempranillo in Ribera del Duero."), _snip(1, "Bodegas Aster Crianza.")]
    monkeypatch.setattr(scorer, "_call_llm", lambda *a, **k: json.dumps({"0": {"score": 95}}))
    _ctx, scored = scorer.score_and_assemble(_product(), snippets, api_url="", model="")
    assert scored[0].text_facts == {"grapes": ["Tempranillo"], "regions": ["Ribera del Duero"]}
    assert scored[1].dropped_reason == "unscored" and scored[1].text_facts == {"grapes": [], "regions": []}


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
    # Two sources in context, but only Vivino names Tempranillo, and one calls the wine a blend.
    assert evidence.grape_source_counts(["Tempranillo", "Cinsault"], CTX_TWO) == {"Tempranillo": 1, "Cinsault": 0}
    ctx = CTX_TWO + "\n\n[Wine.com #1 | match=90]\nA red blend from Rioja."
    tags = ParsedTags(country="Spain", grapes=["Tempranillo"], confidence=90)
    reasons = apply_evidence_rules(tags, ctx)
    assert reasons == ["uncorroborated_grape:Tempranillo"]
    assert decide_tag_status(normalized=tags, confidence_threshold=85, review_reasons=reasons) == "needs_review"


def test_single_varietal_needs_one_source_unless_the_context_calls_it_a_blend():
    # Aster, Mont Gravet, Librandi: one grape, one source naming it, and right every time.
    tags = ParsedTags(country="Spain", grapes=["Tempranillo"], is_blend=False, confidence=90)
    assert apply_evidence_rules(tags, CTX_TWO) == []
    # Chocapalha (2026-09-27): Touriga Nacional alone, from "a blend of indigenous Portuguese varietals".
    for word in ("a blend of indigenous varietals", "Blended in concrete.", "Assemblage of the best lots."):
        ctx = CTX_TWO + f"\n\n[Wine.com #1 | match=90]\n{word}"
        assert evidence.context_calls_it_a_blend(ctx)
        assert apply_evidence_rules(tags, ctx) == ["uncorroborated_grape:Tempranillo"]
    assert not evidence.context_calls_it_a_blend(CTX_TWO + "\n\n[Wine.com #1 | match=90]\nBlenheim Vineyards.")
    # A blend with one named grape keeps the check, next to incomplete_blend.
    tags = ParsedTags(country="Spain", grapes=["Tempranillo"], is_blend=True, confidence=90)
    assert apply_evidence_rules(tags, CTX_TWO) == ["uncorroborated_grape:Tempranillo", "incomplete_blend"]
    # A grape no source names is still unsupported.
    tags = ParsedTags(country="Spain", grapes=["Cinsault"], is_blend=False, confidence=90)
    assert apply_evidence_rules(tags, CTX_TWO) == ["unsupported_grape:Cinsault"]


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


URRUZOLA_CTX = ("[Grapes Q #2 | match=95]\nA pale pink Getariako Txakolina rosé, a blend of "
                "Hondarrabi Zuri and Hondarrabi Beltza.\n\n"
                "[Wine.com #1 | match=95]\nInazio Urruzola rosé from Hondarrabi Zuri and Hondarrabi Beltza.")


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_rose_with_only_white_grapes_routes_to_review():
    # Urruzola: the tagger dropped Hondarrabi Beltza "since it is a red grape and the wine is a rose".
    tags = ParsedTags(country="Spain", grapes=["Hondarrabi Zuri"], is_blend=False, confidence=85)
    reasons = apply_evidence_rules(tags, URRUZOLA_CTX, category="Rose")
    assert reasons == ["white_grapes_only"]
    assert decide_tag_status(normalized=tags, confidence_threshold=85, review_reasons=reasons) == "needs_review"
    tags = ParsedTags(country="Spain", grapes=["Hondarrabi Zuri", "Hondarrabi Beltza"], is_blend=True,
                      confidence=85)
    assert apply_evidence_rules(tags, URRUZOLA_CTX, category="Rose") == []


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_white_grapes_only_by_category():
    assert evidence.white_grapes_only(["Chardonnay"], "Red")
    assert evidence.white_grapes_only(["Macabeo", "Malvasia Bianca"], "Rosé")
    assert not evidence.white_grapes_only(["Macabeo", "Tempranillo"], "Red")
    # A white wine from red grapes is a blanc de noirs; sparkling says nothing about colour.
    assert not evidence.white_grapes_only(["Pinot Noir"], "White")
    assert not evidence.white_grapes_only(["Chardonnay"], "Sparkling")
    assert not evidence.white_grapes_only([], "Rose")
    # Pink-skinned grapes make a rosé on their own, never a red.
    assert not evidence.white_grapes_only(["Pinot Gris"], "Rose")
    assert evidence.white_grapes_only(["Pinot Gris"], "Red")


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_white_grapes_only_uses_inferred_category_when_product_has_none():
    tags = ParsedTags(country="Spain", grapes=["Hondarrabi Zuri"], confidence=85, category="Rose")
    assert apply_evidence_rules(tags, URRUZOLA_CTX) == ["white_grapes_only"]
    # The product's own category wins over the model's.
    assert apply_evidence_rules(tags, URRUZOLA_CTX, category="White") == []


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
def test_coarse_region_when_context_names_a_finer_one(monkeypatch):
    # The upgrade's reason shows only with REGION_UPGRADE_NEEDS_REVIEW on.
    monkeypatch.setattr(phases, "REGION_UPGRADE_NEEDS_REVIEW", True)
    ctx = ("[Wine.com #1 | match=100]\nG.D. Vajra Barolo Albe 2021 from Barolo, Piedmont, Italy.\n\n"
           "[Wine Searcher #3 | match=90]\nFind the best local price for 2021 G.D. Vajra Albe, Barolo DOCG, Italy.\n\n"
           "[Vivino #1 | match=90]\nA Red wine from Piemonte, Italy. Made from Nebbiolo.")
    assert evidence.finer_regions_named(["Piedmont"], ctx, country="Italy",
                                        product_name="Vajra Barolo Albe") == ["Barolo"]
    # The gate puts the finer region in place (the product name names it too) and, with
    # review on, routes the row instead of flagging coarse_region.
    tags = ParsedTags(country="Italy", region=["Piedmont"], grapes=["Nebbiolo"], confidence=85)
    reasons = apply_evidence_rules(tags, ctx, product_name="Vajra Barolo Albe")
    assert reasons == ["region_from_name:Piedmont→Barolo"]
    assert tags.region == ["Barolo", "Langhe", "Piedmont"]
    # The precise answer, parents included, has nothing finer to point at.
    assert evidence.finer_regions_named(["Barolo", "Langhe", "Piedmont"], ctx, country="Italy",
                                        product_name="Vajra Barolo Albe") == []


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_coarse_region_from_one_source_does_not_outweigh_the_submitted_one():
    # DV Catena Tinto Historico: CellarTracker lists the producer's other bottlings,
    # one of them "…Apelacion Paraje Altamira"; two sources say Uco Valley.
    name = "DV Catena Tinto"
    ctx = ("[Grapes Q #3 | match=100]\n77% Malbec, 20% Bonarda and 3% Petit Verdot sourced from the "
           "Uco Valley and Lujan de Cuyo.\n\n"
           "[Region Q | match=100]\nA Red wine from Uco Valley, Mendoza, Argentina.\n\n"
           "[CellarTracker #2 | match=98]\nCommunity wine reviews and ratings on 2023 Bodega Catena Zapata "
           "D.V. Catena Tinto Historico Apelacion Paraje Altamira, plus professional notes.")
    regions = ["Uco Valley", "Mendoza"]
    assert evidence.finer_regions_named(regions, ctx, country="Argentina", product_name=name) == []
    # A second source for it is enough.
    ctx += "\n\n[Wine.com #1 | match=90]\nD.V. Catena Tinto Historico from Paraje Altamira, Mendoza."
    assert evidence.finer_regions_named(regions, ctx, country="Argentina", product_name=name) == ["Paraje Altamira"]


VILAFONTE_CTX = (
    "[Grapes Q #1 | match=95]\nSeriously Old Dirt, a Cabernet Sauvignon-led blend.\n\n"
    "[Vivino #1 | match=95]\nSeriously Old Dirt 2019 South Africa · Paarl · Red wine · Cabernet Sauvignon\n\n"
    "[UPC #1 | match=90]\nSeriously Old Dirt Region : Paarl Grape : Cabernet Sauvignon 86%, Merlot 8%, "
    "Malbec 4%, Cabernet Franc 2%")


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_one_snippet_naming_the_whole_blend_corroborates_it():
    grapes = ["Cabernet Sauvignon", "Merlot", "Malbec", "Cabernet Franc"]
    assert evidence.blend_named_whole(grapes, VILAFONTE_CTX)
    tags = ParsedTags(country="South Africa", region=["Paarl"], grapes=grapes, is_blend=True, confidence=85)
    assert apply_evidence_rules(tags, VILAFONTE_CTX, product_name="Vilafonte Seriously Old Dirt") == []
    # Not when no other source names any of its grapes: nothing ties the list to this wine.
    ctx = "[UPC #1 | match=90]\nCabernet Sauvignon 86%, Merlot 8%, Malbec 4%, Cabernet Franc 2%\n\n[Wine.com #1 | match=90]\nA red blend."
    tags = ParsedTags(country="South Africa", grapes=grapes, is_blend=True, confidence=85)
    assert apply_evidence_rules(tags, ctx) == [f"uncorroborated_grape:{g}" for g in grapes]


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_blend_named_whole_needs_this_blend_or_its_shares():
    # La Rioja Alta: an older vintage adds 5% Mazuelo, but each grape has its share.
    ctx = ("[Grapes Q #2 | match=100]\nGrapes 20% Grenache / Garnacha 5% Mazuelo 75% Tempranillo\n\n"
           "[Vivino #3 | match=90]\nA Red wine from Rioja, Spain. Made from Tempranillo.")
    assert evidence.blend_named_whole(["Tempranillo", "Grenache"], ctx)
    # A region blurb lists the local grapes, with no shares: it backs no blend.
    blurb = ("[Grapes Q #1 | match=90]\nCabernet, Merlot, Mourvedre, Grenache, and Syrah are some of the "
             "most important red grapes in the region.\n\n[UPC #1 | match=90]\nGrenache, Carignan.")
    assert not evidence.blend_named_whole(["Grenache", "Syrah", "Mourvèdre"], blurb)
    # Two lists that disagree do not add up to their union (Curator's Sémillon).
    curator = ("[Vivino #1 | match=89]\nMade from Sémillon, Chardonnay, Chenin Blanc.\n\n"
               "[Wine.com #1 | match=95]\nChenin Blanc, Chardonnay, and Viognier.")
    grapes = ["Chenin Blanc", "Chardonnay", "Viognier", "Sémillon"]
    assert not evidence.blend_named_whole(grapes, curator)
    tags = ParsedTags(country="South Africa", grapes=grapes, is_blend=True, confidence=89)
    assert apply_evidence_rules(tags, curator) == ["uncorroborated_grape:Viognier", "uncorroborated_grape:Sémillon"]
    # One grape is not a blend.
    assert not evidence.blend_named_whole(["Tempranillo"], ctx)


# 2026-10-01, Bila Haut: Syrah missing, accepted because the UPC line passed for the whole blend.
BILA_HAUT_CTX = (
    "[Region Q #2 | match=95]\nBila-Haut V.I.T. 2022 Côtes du Roussillon Villages Latour de France Mostly "
    "Grenache. Fermented in concrete and aged in Clayver (600 litres).\n\n"
    "[UPC #1 | match=90]\nFrom the famous Rhone winemaker Chapoutier comes this organic-grapes wine from "
    "Roussillon. Grenache, Carignan, and touches of a couple other grapes make this powerful with blackberry, "
    "herb, black cherry and coffee flavors.\n\n"
    "[Wine.com #1 | match=90]\nThe 2023 Bila-Haut by Michel Chapoutier Côtes du Roussillon Villages is an "
    "outstanding value.")


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_a_list_that_says_it_is_partial_is_not_the_whole_blend():
    grapes = ["Grenache", "Carignan"]
    assert not evidence.blend_named_whole(grapes, BILA_HAUT_CTX)
    tags = ParsedTags(country="France", region=["Côtes du Roussillon Villages"], grapes=grapes, is_blend=True,
                      confidence=89)
    assert apply_evidence_rules(tags, BILA_HAUT_CTX, product_name="Bila Haut Roussillon") == [
        "uncorroborated_grape:Carignan"]
    # The same list without the tail names the whole blend.
    whole = BILA_HAUT_CTX.replace(", and touches of a couple other grapes", "")
    assert evidence.blend_named_whole(grapes, whole)
    for tail in ("among others", "with a few other varieties", "and some other grapes"):
        assert not evidence.blend_named_whole(grapes, whole.replace("Carignan make", f"Carignan {tail} make"))
    # "and other red and black berries" is a tasting note, not a partial grape list.
    assert evidence.blend_named_whole(grapes, whole.replace("flavors.", "and other red and black berries."))


PAV_CTX = ("[Region Q #1 | match=95]\nPavillon de Chavannes, a Côte de Brouilly from the slopes of Mont Brouilly.\n\n"
           "[Wine.com #1 | match=90]\nChateau du Pavillon de Chavannes Cote de Brouilly 2022 from Beaujolais.")


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_longer_region_when_context_names_a_region_containing_the_submitted_one(monkeypatch):
    # The upgrade's reason shows only with REGION_UPGRADE_NEEDS_REVIEW on.
    monkeypatch.setattr(phases, "REGION_UPGRADE_NEEDS_REVIEW", True)
    name = "Pav Chavannes Brouilly"
    assert evidence.longer_regions_named(["Brouilly", "Beaujolais"], PAV_CTX, country="France",
                                         product_name=name) == ["Côte de Brouilly"]
    tags = ParsedTags(country="France", region=["Brouilly", "Beaujolais"], grapes=["Gamay"], confidence=85)
    assert "region_from_sources:Brouilly→Côte de Brouilly" in apply_evidence_rules(tags, PAV_CTX, product_name=name)
    assert tags.region == ["Côte de Brouilly", "Beaujolais"]
    # The right answer has nothing longer to point at.
    assert evidence.longer_regions_named(["Côte de Brouilly", "Beaujolais"], PAV_CTX, country="France",
                                         product_name=name) == []


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_longer_region_is_weighed_against_the_submitted_region_on_its_own():
    # More sources say Brouilly on its own than Côte de Brouilly.
    ctx = ("[Region Q #1 | match=95]\nA Brouilly from Pavillon de Chavannes.\n\n"
           "[Wine.com #1 | match=90]\nPavillon de Chavannes Brouilly, Beaujolais.\n\n"
           "[Vivino #1 | match=90]\nA Red wine from Brouilly, Beaujolais. The family also farms Côte de Brouilly.")
    assert evidence.longer_regions_named(["Brouilly"], ctx, country="France") == []
    # A region below the submitted one is coarse_region's business, not this check's.
    ctx = ("[Wine.com #1 | match=95]\nBila-Haut Côtes du Roussillon Villages Latour-de-France 2022.\n\n"
           "[Region Q #1 | match=90]\nDomaine de Bila-Haut, Côtes du Roussillon Villages Latour de France.")
    assert evidence.longer_regions_named(["Côtes du Roussillon Villages"], ctx, country="France") == []


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_coarse_region_ignores_a_region_inside_the_producer_name():
    name = "La Rioja Alta Ardanza"
    ctx = "[Vivino #1 | match=95]\nLa Rioja Alta S.A. Vina Ardanza Reserva, a Red wine from Rioja."
    assert evidence.finer_regions_named(["Rioja"], ctx, country="Spain", product_name=name) == []
    # A mention of the sub-zone on its own still counts.
    ctx += "\n\n[Wine.com #1 | match=90]\nFruit from the Rioja Alta sub-zone."
    assert evidence.finer_regions_named(["Rioja"], ctx, country="Spain", product_name=name) == ["Rioja Alta"]


# 2026-10-01, Neirano: accepted at Piedmont. Every "Barolo" but Ellis's sits in "Tenute Neirano Barolo".
NEIRANO_CTX = (
    "[CellarTracker #2 | match=90]\nAverage of 90 points in 5 community wine reviews on 2017 Tenute Neirano "
    "Barolo. Red 2018 Tenute Neirano Barolo (view label images) Nebbiolo Drink 2024-2030\n\n"
    "[Vivino #1 | match=89]\nA Red wine from Piemonte, Northern Italy, Italy. Made from Nebbiolo.\n\n"
    "[Wine Searcher #1 | match=95]\nFind the best local price for Tenute Neirano Barolo DOCG, Piedmont, Italy.\n\n"
    "[Grape variety #2 | match=90]\nBarolo is the classic red wine of Piedmont, produced from the best "
    "vineyards on the hills around the town of Barolo. Before release Neirano Barolo spends three years in "
    "large oak 'botti'.")


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_a_region_that_ends_the_product_name_is_not_masked(monkeypatch):
    # The upgrade's reason shows only with REGION_UPGRADE_NEEDS_REVIEW on.
    monkeypatch.setattr(phases, "REGION_UPGRADE_NEEDS_REVIEW", True)
    assert evidence.finer_regions_named(["Piedmont"], NEIRANO_CTX, country="Italy",
                                        product_name="Neirano Barolo") == ["Barolo"]
    tags = ParsedTags(country="Italy", region=["Piedmont"], grapes=["Nebbiolo"], confidence=89)
    assert apply_evidence_rules(tags, NEIRANO_CTX, product_name="Neirano Barolo") == [
        "region_from_name:Piedmont→Barolo"]
    # A region inside the name is still masked (the producer La Rioja Alta), and so is one at
    # its start: only the end of a POS name is the appellation.
    ctx = ("[Vivino #1 | match=95]\nLa Rioja Alta Vina Ardanza, a Red wine from Rioja.\n\n"
           "[Wine.com #1 | match=90]\nLa Rioja Alta Ardanza Reserva, Rioja.")
    assert evidence.finer_regions_named(["Rioja"], ctx, country="Spain", product_name="La Rioja Alta Ardanza") == []
    # A name that is only the region masks nothing to begin with.
    assert evidence.finer_regions_named(["Piedmont"], NEIRANO_CTX, country="Italy", product_name="Barolo") == ["Barolo"]


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_name_region_is_the_one_branch_the_product_name_names():
    nodes = library_text.region_tree()[1]
    assert nodes[evidence.name_region("Neirano Barolo")][0] == "Barolo"
    assert nodes[evidence.name_region("Aster Ribera del Duero")][0] == "Ribera del Duero"
    assert evidence.name_region("Annabella Pinot Noir") is None
    # The producer's name is a place name: Rioja Alta (Spain) and La Rioja (Argentina).
    assert evidence.name_region("La Rioja Alta Ardanza") is None


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_region_from_name():
    name = "Neirano Barolo"
    assert evidence.region_from_name(["Piedmont"], country="Italy", product_name=name) == ("upgrade", "Barolo")
    assert evidence.region_from_name([], country="Italy", product_name=name) == ("upgrade", "Barolo")
    assert evidence.region_from_name(["Barolo", "Langhe", "Piedmont"], country="Italy",
                                     product_name=name) == (None, None)
    # Another branch: a sibling under Langhe.
    assert evidence.region_from_name(["Barbaresco", "Langhe", "Piedmont"], country="Italy",
                                     product_name=name) == ("conflict", "Barolo")
    # A region in another country than the one submitted is not this wine's.
    assert evidence.region_from_name(["Rhône"], country="France", product_name=name) == (None, None)
    # Finer than the name is fine (Faustino's Rioja Alavesa), and so is a name the submission
    # contains: the POS shortens Côte de Brouilly to "Brouilly".
    assert evidence.region_from_name(["Rioja Alavesa", "Rioja"], country="Spain",
                                     product_name="Faustino VII Rioja") == (None, None)
    assert evidence.region_from_name(["Côte de Brouilly", "Beaujolais"], country="France",
                                     product_name="Pav Chavannes Brouilly") == (None, None)


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_name_region_conflict_routes_and_changes_nothing():
    tags = ParsedTags(country="Italy", region=["Barbaresco", "Langhe", "Piedmont"], grapes=["Nebbiolo"],
                      confidence=89)
    assert "name_region_conflict:Barolo" in apply_evidence_rules(tags, NEIRANO_CTX, product_name="Neirano Barolo")
    assert tags.region == ["Barbaresco", "Langhe", "Piedmont"]


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_region_from_sources_needs_as_many_sources_as_the_submitted_region():
    # 2026-10-01, La Rioja Alta: Rioja Oriental is the Garnacha's origin, named by fewer
    # sources than Rioja. It is still flagged, but not put in place.
    ctx = ("[Vivino #1 | match=95]\nVina Ardanza Reserva, a Red wine from Rioja.\n\n"
           "[Wine.com #1 | match=90]\nArdanza Reserva, Rioja. Garnacha from Rioja Oriental.\n\n"
           "[Wine Searcher #1 | match=90]\nArdanza, Rioja DOCa, Spain. Its Garnacha grows in Rioja Oriental.")
    name = "La Rioja Alta Ardanza"
    assert evidence.finer_regions_named(["Rioja"], ctx, country="Spain", product_name=name) == ["Rioja Oriental"]
    assert evidence.region_from_sources(["Rioja"], ctx, country="Spain", product_name=name) is None
    tags = ParsedTags(country="Spain", region=["Rioja"], grapes=["Tempranillo", "Grenache"], is_blend=True,
                      confidence=90)
    assert "coarse_region:Rioja Oriental" in apply_evidence_rules(tags, ctx, product_name=name)
    assert tags.region == ["Rioja"]


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_region_from_sources_needs_two_sources_for_a_region_below():
    # 2026-10-02, Curator White: one snippet names Swartland and, as where the vines grow,
    # Paardeberg. 1 to 1 is a tie; a sub-region needs FINER_REGION_MIN_SOURCES to replace.
    ctx = ("[Grape variety #2 | match=90]\nChenin blanc, Chardonnay, Viognier, Swartland, South Africa. "
           "Sourced from multiple sites across the Swartland district, specifically from mountain slopes "
           "in the Paardeberg area.\n\n"
           "[CellarTracker #1 | match=90]\n2021 Badenhorst Family Wines The Curator White.")
    regions = ["Swartland", "Coastal Region", "Western Cape"]
    assert evidence.region_from_sources(regions, ctx, country="South Africa", product_name="Curator White") is None
    ctx += "\n\n[Wine.com #1 | match=90]\nThe Curator White, from the Paardeberg, Swartland."
    assert evidence.region_from_sources(regions, ctx, country="South Africa",
                                        product_name="Curator White") == "Paardeberg"
    # A longer name wins on a tie: one source each.
    assert evidence.region_from_sources(["Brouilly", "Beaujolais"], PAV_CTX.split("\n\n")[0], country="France",
                                        product_name="Pav Chavannes Brouilly") == "Côte de Brouilly"


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_region_upgrade_without_review(monkeypatch):
    monkeypatch.setattr(phases, "REGION_UPGRADE_NEEDS_REVIEW", False)
    tags = ParsedTags(country="Italy", region=["Piedmont"], grapes=["Nebbiolo"], confidence=89)
    assert apply_evidence_rules(tags, NEIRANO_CTX, product_name="Neirano Barolo") == []
    assert tags.region == ["Barolo", "Langhe", "Piedmont"]


@pytest.mark.skipif(not evidence.LIBRARY_DB.exists(), reason="library.db not built")
def test_unsupported_region_when_nothing_in_the_text_names_it():
    ctx = ("[Vivino #1 | match=95]\nA Red wine from Piemonte, Italy. Made from Nebbiolo.\n\n"
           "[Wine.com #1 | match=90]\nA firm Nebbiolo from Italy.")
    # Barolo picked off a lookup_sub_regions list: no snippet names it.
    assert evidence.unsupported_regions(["Barolo", "Piedmont"], ctx, country="Italy") == ["Barolo"]
    tags = ParsedTags(country="Italy", region=["Barolo", "Piedmont"], grapes=["Nebbiolo"], confidence=90)
    assert apply_evidence_rules(tags, ctx, product_name="Vajra Albe") == ["unsupported_region:Barolo"]
    # The product name counts, and so does a library synonym (Piemonte).
    assert apply_evidence_rules(tags, ctx, product_name="Vajra Barolo Albe") == []
    assert evidence.unsupported_regions(["Piedmont"], ctx, country="Italy") == []
    # A region below the submitted one backs it (coarse_region is a separate question).
    assert evidence.unsupported_regions(["Piedmont"], NEIRANO_CTX.replace("Piemonte", "Italy").replace(
        "Piedmont", "Italy"), country="Italy") == []
    # Separators do not matter: "Cotes-du-Roussillon" names Côtes du Roussillon.
    ctx = "[Wine.com #1 | match=90]\nA Cotes-du-Roussillon red.\n\n[Vivino #1 | match=90]\nGrenache."
    assert evidence.unsupported_regions(["Côtes du Roussillon"], ctx, country="France") == []


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
