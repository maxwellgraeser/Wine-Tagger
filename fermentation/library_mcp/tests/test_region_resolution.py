"""Region resolution beyond an exact label match: classification words and
compound strings (against the built library.db), and region names shared
by two countries (against a small throwaway DB, since the checked-in
allowlist may not contain any yet)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

SCHEMA = Path(__file__).resolve().parents[1] / "schema.sql"


@pytest.mark.parametrize("given,canonical", [
    # classification words, either end, any case
    ("Barolo DOCG", "Barolo"),
    ("DOCG Barolo", "Barolo"),
    ("Kamptal DAC", "Kamptal"),
    ("W.O. Stellenbosch", "Stellenbosch"),
    ("Wine of Origin Stellenbosch", "Stellenbosch"),
    ("Appellation Margaux Contrôlée", "Margaux"),
    ("Rioja (DOCa)", "Rioja"),
    ("Mosel Qualitätswein", "Mosel"),
    ("Getariako Txakolina D.O", "Getariako Txakolina"),
    ("D.O.Ca. Rioja", "Rioja"),
    # compound strings: most specific part first, country parts skipped
    ("Coastal Region, Western Cape, South Africa", "Coastal Region"),
    ("Western Cape, South Africa", "Western Cape"),
    ("Napa Valley, California, USA", "Napa Valley"),
    ("Mendoza, Argentina", "Mendoza"),
    ("Côtes du Rhône - Villages", "Côtes du Rhône Villages"),
    # exact names that contain a stripped word still match whole
    ("Chianti Classico", "Chianti Classico"),
    ("Languedoc-Roussillon", "Languedoc-Roussillon"),
])
def test_fallback_variants(server, given, canonical):
    r = server.lookup_region(given)
    assert r["known"] and r["canonical"] == canonical, r


def test_country_alone_is_not_a_region(server):
    assert not server.lookup_region("South Africa")["known"]
    res = server.submit_tags("France", ["South Africa"], ["Merlot"], None, None, 50)
    assert "country_in_region_slot" in res["issues"]


def test_submit_accepts_compound_region(server):
    res = server.submit_tags("South Africa", ["Coastal Region, Western Cape, South Africa"],
                             ["Chenin Blanc"], None, None, 80)
    assert res["ok"], res
    assert res["normalized"]["region"] == ["Coastal Region", "Western Cape"]


# ---------- same name in two countries ----------

@pytest.fixture
def homonyms(server, monkeypatch, tmp_path):
    """Spain's Rioja carries the synonym "La Rioja"; Argentina has its own
    canonical La Rioja; the US has a Georgia region."""
    db = sqlite3.connect(tmp_path / "lib.db", check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA.read_text(encoding="utf-8"))
    db.executemany("INSERT INTO countries (id, name, iso_code, is_canonical) VALUES (?, ?, ?, 1)",
                   [(1, "Spain", "ES"), (2, "Argentina", "AR"), (3, "Georgia", "GE"), (4, "United States", "US")])
    db.executemany(
        "INSERT INTO regions (id, name, country_id, parent_region_id, is_canonical) VALUES (?, ?, ?, ?, 1)",
        [(1, "Rioja", 1, None), (2, "La Rioja", 2, None), (3, "Famatina", 2, 2),
         (4, "Mendoza", 2, None), (5, "Kakheti", 3, None), (6, "Georgia", 4, None)])
    db.execute("INSERT INTO region_synonyms (region_id, synonym) VALUES (1, 'La Rioja')")
    db.execute("INSERT INTO grapes (id, canonical_name, color, is_canonical) VALUES (1, 'Torrontés', 'white', 1)")
    db.execute("INSERT INTO region_grapes (region_id, grape_id) VALUES (2, 1)")
    db.commit()
    for attr, value in zip(("_COUNTRIES", "_REGIONS", "_GRAPES", "_C_IDX", "_R_IDX", "_G_IDX"),
                           server._load_index(db)):
        monkeypatch.setattr(server, attr, value)
    monkeypatch.setattr(server, "_CONN", db)
    yield server
    db.close()


def test_lookup_without_country_lists_alternatives(homonyms):
    # A region's own name ranks ahead of another region's synonym.
    r = homonyms.lookup_region("La Rioja")
    assert r["canonical"] == "La Rioja" and r["country"] == "Argentina"
    assert r["alternatives"] == ["Rioja (Spain)"]


@pytest.mark.parametrize("country,canonical", [("Argentina", "La Rioja"), ("AR", "La Rioja"),
                                               ("Spain", "Rioja"), ("ES", "Rioja")])
def test_lookup_with_country_picks_it(homonyms, country, canonical):
    r = homonyms.lookup_region("La Rioja", country=country)
    assert r["canonical"] == canonical
    assert "alternatives" not in r


def test_lookup_unambiguous_has_no_alternatives(homonyms):
    assert "alternatives" not in homonyms.lookup_region("Mendoza")


def test_submit_uses_submitted_country(homonyms):
    res = homonyms.submit_tags("Argentina", ["La Rioja"], ["Torrontés"], None, None, 80)
    assert res["ok"], res
    assert res["normalized"]["region"] == ["La Rioja"]
    res = homonyms.submit_tags("Spain", ["La Rioja"], ["Torrontés"], None, None, 80)
    assert res["ok"], res
    assert res["normalized"]["region"] == ["Rioja"]


def test_submit_infers_country_from_other_regions(homonyms):
    res = homonyms.submit_tags(None, ["La Rioja", "Mendoza"], ["Torrontés"], None, None, 80)
    assert res["ok"], res
    assert res["normalized"]["country"] == "Argentina"
    assert res["normalized"]["region"][0] == "La Rioja"


def test_submit_without_any_country_is_ambiguous(homonyms):
    res = homonyms.submit_tags(None, ["La Rioja"], ["Torrontés"], None, None, 80)
    assert not res["ok"] and "ambiguous_region" in res["issues"]
    assert "Rioja (Spain)" in res["hints"]["ambiguous_region"]


def test_child_of_homonym_expands_to_right_parent(homonyms):
    res = homonyms.submit_tags("Argentina", ["Famatina"], ["Torrontés"], None, None, 80)
    assert res["normalized"]["region"] == ["Famatina", "La Rioja"]


def test_list_grapes_by_region_uses_country(homonyms):
    assert homonyms.list_grapes(country="Argentina", region="La Rioja") == ["Torrontés"]
    assert homonyms.list_grapes(country="Spain", region="La Rioja") == []   # Spain's Rioja: no edges


def test_country_part_does_not_beat_region(homonyms):
    assert homonyms.lookup_region("Kakheti, Georgia")["canonical"] == "Kakheti"
    r = homonyms.lookup_region("Georgia, United States")
    assert r["canonical"] == "Georgia" and r["country"] == "United States"
