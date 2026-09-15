"""Behavioural tests for the MCP server against the built library.db:
canonical-first resolution, placeholder semantics, and submit_tags issue
codes. Skipped when the DB has not been built."""

from __future__ import annotations

import pytest


def test_tiers_present(server):
    n_canon = server._CONN.execute("SELECT COUNT(*) FROM grapes WHERE is_canonical = 1").fetchone()[0]
    n_place = server._CONN.execute("SELECT COUNT(*) FROM grapes WHERE is_canonical = 0").fetchone()[0]
    assert n_canon >= 250
    assert n_place > 0, "placeholder pass produced no grapes (build with placeholders)"
    r_canon = server._CONN.execute("SELECT COUNT(*) FROM regions WHERE is_canonical = 1").fetchone()[0]
    assert r_canon >= 400
    assert server._CONN.execute("SELECT COUNT(*) FROM countries WHERE is_canonical = 0").fetchone()[0] == 0


def test_canonical_grapes_have_colour(server):
    missing = [r[0] for r in server._CONN.execute(
        "SELECT canonical_name FROM grapes WHERE is_canonical = 1 AND color IS NULL")]
    assert not missing, missing


def test_list_tools_return_canonical_only(server):
    grapes = set(server.list_grapes())
    regions = set(server.list_regions())
    placeholder_g = server._CONN.execute(
        "SELECT canonical_name FROM grapes WHERE is_canonical = 0 LIMIT 1").fetchone()
    if placeholder_g:
        assert placeholder_g[0] not in grapes
    placeholder_r = server._CONN.execute(
        "SELECT name FROM regions WHERE is_canonical = 0 LIMIT 1").fetchone()
    if placeholder_r:
        assert placeholder_r[0] not in regions
    assert "Pinot Noir" in grapes and "Barolo" in regions
    assert "Barolo" in server.list_regions("Italy")
    assert "Barolo" in server.list_regions("IT")
    assert server.list_regions("Narnia") == []


def test_placeholder_grape_semantics(server):
    row = server._CONN.execute(
        "SELECT canonical_name FROM grapes WHERE is_canonical = 0 LIMIT 1").fetchone()
    if not row:
        pytest.skip("no placeholder grapes in this build")
    g = server.lookup_grape(row[0])
    assert g["known"] and g["is_placeholder"] and not g["is_phrase"]
    res = server.submit_tags("France", [], [row[0]], None, None, 50)
    assert not res["ok"] and "placeholder_grape" in res["issues"]


def test_placeholder_region_semantics(server):
    row = server._CONN.execute(
        "SELECT name FROM regions WHERE is_canonical = 0 LIMIT 1").fetchone()
    if not row:
        pytest.skip("no placeholder regions in this build")
    r = server.lookup_region(row[0])
    assert r["known"] and r["is_placeholder"]
    res = server.submit_tags(None, [row[0]], ["Merlot"], None, None, 50)
    assert not res["ok"] and "non_canonical_region" in res["issues"]


def test_phrase_grape(server):
    g = server.lookup_grape("Bordeaux Blend")
    assert g["is_phrase"] and not g["known"]
    res = server.submit_tags("France", ["Bordeaux"], ["Bordeaux Blend"], None, None, 50)
    assert not res["ok"] and "phrase_grapes" in res["issues"]


def test_synonyms_and_accent_folding(server):
    assert server.lookup_grape("garnacha")["canonical"] == "Grenache"
    assert server.lookup_grape("Shiraz")["canonical"] == "Syrah"
    assert server.lookup_grape("Mourvedre")["canonical"] == "Mourvèdre"
    assert server.lookup_region("Bourgogne")["canonical"] == "Burgundy"
    assert server.lookup_region("piemonte")["canonical"] == "Piedmont"
    assert server.lookup_region("Emilia Romagna")["canonical"] == "Emilia-Romagna"
    assert server.lookup_region("Napa")["canonical"] == "Napa Valley"
    assert server.lookup_country("USA")["canonical"] == "United States"
    assert server.lookup_country("us")["canonical"] == "United States"


def test_submit_issue_codes(server):
    res = server.submit_tags("Italy", ["Napa Valley"], ["Merlot"], None, None, 50)
    assert "region_country_mismatch" in res["issues"]
    res = server.submit_tags("France", ["France"], ["Merlot"], None, None, 50)
    assert "country_in_region_slot" in res["issues"]
    res = server.submit_tags("France", ["Atlantis Hills"], ["Merlot"], None, None, 50)
    assert "unknown_region" in res["issues"]
    res = server.submit_tags("Narnia", [], ["Merlot"], None, None, 50)
    assert "unknown_country" in res["issues"]
    res = server.submit_tags("France", ["Bordeaux"], ["Merlot", "Cabernet Sauvignon"], False, None, 50)
    assert "is_blend_mismatch" in res["issues"]
    res = server.submit_tags("France", ["Bordeaux"], ["Merlotz"], None, None, 50)
    assert "non_canonical_grape" in res["issues"]
    assert "Merlotz" in res["hints"]["non_canonical_grape"]
    res = server.submit_tags("France", ["Bordeaux"], [], None, None, 50)
    assert res["issues"] == ["no_grapes"]


def test_submit_expands_parents_and_infers_country(server):
    res = server.submit_tags(None, ["Russian River Valley"], ["Pinot Noir"], None, None, 90)
    assert res["ok"], res
    norm = res["normalized"]
    assert norm["country"] == "United States"
    assert norm["region"][:1] == ["Russian River Valley"]
    assert "California" in norm["region"]
    assert norm["is_blend"] is False
    res = server.submit_tags("US", ["Willamette", "Oregon"], ["PN", "Pinot Noir"], None, True, 90)
    assert res["ok"]
    assert res["normalized"]["region"] == ["Willamette Valley", "Oregon"]
    assert res["normalized"]["grapes"] == ["Pinot Noir"]
    assert res["normalized"]["organic"] is True
