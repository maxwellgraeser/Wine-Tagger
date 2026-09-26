"""Offline structural tests for the allowlist loader/validator."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from fermentation.library_mcp.seed.allowlist import AllowlistError, load_allowlists


def test_checked_in_allowlists_are_structurally_valid():
    al = load_allowlists(require_qids=False)
    assert len(al.countries) >= 40
    assert len(al.grapes) >= 250
    assert len(al.regions) >= 400
    # single-region floor: every country has at least one region, except
    # the handful we deliberately list as country-only.
    country_only = {"BA", "ME", "AL", "MT", "UA", "SK"}
    isos_with_regions = {r.country for r in al.regions}
    for c in al.countries:
        if c.iso not in country_only:
            assert c.iso in isos_with_regions, f"{c.name} has no canonical region"


def test_test_set_regions_and_grapes_are_allowlisted():
    """The combined.csv test wines must be covered by the canonical tier."""
    al = load_allowlists(require_qids=False)
    region_labels = {n.lower() for r in al.regions for n in [r.name, *r.synonyms]}
    grape_labels = {n.lower() for g in al.grapes for n in [g.name, *g.synonyms]}
    for r in ["Russian River Valley", "Ribera del Duero", "Constantia", "Côtes du Roussillon",
              "Picpoul de Pinet", "Languedoc-Roussillon", "Lisboa", "Alenquer", "Willamette Valley",
              "Western Cape", "Mendoza", "Robertson", "Rioja", "Rioja Alta", "Salice Salentino",
              "Cirò", "Bekaa Valley", "Pays d'Oc", "Barolo", "Touraine", "Brouilly",
              "Getariako Txakolina", "Paarl", "delle Venezie"]:
        assert r.lower() in region_labels, r
    for g in ["Pinot Noir", "PN", "Tinto Fino", "Tempranillo", "Sauvignon Blanc", "Syrah",
              "Grenache", "Carignan", "Picpoul", "Touriga Nacional", "Tinta Roriz", "Castelao",
              "Chenin Blanc", "Chardonnay", "Viognier", "Malbec", "Bonarda", "Petite Verdot",
              "Garnacha", "Negroamaro", "Greco Bianco", "Cinsault", "Nebbiolo", "Gamay",
              "Mourvèdre", "Hondarrabi Zuri", "Hondarrabi Beltza", "Cabernet Sauvignon",
              "Merlot", "Cabernet Franc", "Pinot Grigio"]:
        assert g.lower() in grape_labels, g


def _write(tmp: Path, countries, grapes, regions, lock=None):
    (tmp / "countries.yaml").write_text(yaml.safe_dump(countries), encoding="utf-8")
    (tmp / "grapes.yaml").write_text(yaml.safe_dump(grapes), encoding="utf-8")
    (tmp / "regions.yaml").write_text(yaml.safe_dump(regions), encoding="utf-8")
    if lock is not None:
        (tmp / "qids.lock.yaml").write_text(yaml.safe_dump(lock), encoding="utf-8")


@pytest.fixture
def base(tmp_path):
    return tmp_path


def test_valid_minimal_allowlist(base):
    _write(base,
           [{"name": "Italy", "iso": "IT"}],
           [{"name": "Nebbiolo", "color": "red", "synonyms": ["Spanna"]}],
           [{"name": "Piedmont", "country": "IT"},
            {"name": "Barolo", "country": "IT", "parent": "Piedmont"}],
           {"grapes": {"Nebbiolo": {"qid": "Q12345"}}, "regions": {}})
    al = load_allowlists(base)
    assert al.grape_qid(al.grapes[0]) == "Q12345"
    assert al.region_qid(al.regions[0]) is None


def test_yaml_qid_pin_overrides_lock(base):
    _write(base, [{"name": "Italy", "iso": "IT"}],
           [{"name": "Nebbiolo", "qid": "Q1"}], [],
           {"grapes": {"Nebbiolo": {"qid": "Q2"}}, "regions": {}})
    al = load_allowlists(base)
    assert al.grape_qid(al.grapes[0]) == "Q1"


@pytest.mark.parametrize("grapes,regions,msg", [
    ([{"name": "Nebbiolo"}], [], "has no QID"),
    ([{"name": "Nebbiolo", "qid": "Q1"}, {"name": "Spanna", "qid": "Q2"}, {"name": "X", "qid": "Q3", "synonyms": ["Spanna"]}],
     [], "another grape's canonical name"),
    ([{"name": "A", "qid": "Q1", "synonyms": ["s"]}, {"name": "B", "qid": "Q2", "synonyms": ["s"]}], [], "claimed by both"),
    ([{"name": "A", "qid": "Q1"}, {"name": "B", "qid": "Q1"}], [], "share QID"),
    ([], [{"name": "Barolo", "country": "IT", "parent": "Piedmont"}], "is not in regions.yaml"),
    ([], [{"name": "Barolo", "country": "XX"}], "unknown country"),
    ([], [{"name": "A", "country": "IT", "parent": "B"}, {"name": "B", "country": "IT", "parent": "A"}], "cycle"),
    ([], [{"name": "A", "country": "IT", "synonyms": ["Z"]}, {"name": "B", "country": "IT", "synonyms": ["z"]}], "claimed by both"),
    ([{"name": "A", "qid": "Q1", "color": "purple"}], [], "color must be"),
])
def test_validation_errors(base, grapes, regions, msg):
    _write(base, [{"name": "Italy", "iso": "IT"}], grapes, regions, {"grapes": {}, "regions": {}})
    with pytest.raises(AllowlistError) as exc:
        load_allowlists(base)
    assert msg in str(exc.value)


def test_region_label_may_repeat_across_countries(base):
    _write(base, [{"name": "Spain", "iso": "ES"}, {"name": "Argentina", "iso": "AR"}],
           [{"name": "Torrontés", "qid": "Q1"}],
           [{"name": "Rioja", "country": "ES", "synonyms": ["La Rioja"]},
            {"name": "La Rioja", "country": "AR", "grapes": ["Torrontés"]},
            {"name": "Famatina", "country": "AR", "parent": "La Rioja"}],
           {"grapes": {}, "regions": {}})
    al = load_allowlists(base)
    assert al.region_by_name("La Rioja", "AR").grapes == ["Torrontés"]
    assert al.region_by_name("La Rioja", "ES") is None


@pytest.mark.parametrize("regions,msg", [
    # a parent is looked up in the child's own country only
    ([{"name": "La Rioja", "country": "ES"}, {"name": "Famatina", "country": "AR", "parent": "La Rioja"}],
     "has parent 'La Rioja' in ES"),
    # principal grapes must be allowlisted (name or synonym)
    ([{"name": "La Rioja", "country": "AR", "grapes": ["Torrontes Riojano"]}], "is not in grapes.yaml"),
])
def test_region_country_scoping_errors(base, regions, msg):
    _write(base, [{"name": "Spain", "iso": "ES"}, {"name": "Argentina", "iso": "AR"}],
           [{"name": "Torrontés", "qid": "Q1"}], regions, {"grapes": {}, "regions": {}})
    with pytest.raises(AllowlistError) as exc:
        load_allowlists(base)
    assert msg in str(exc.value)


def test_bad_qid_format_rejected(base):
    _write(base, [{"name": "Italy", "iso": "IT"}], [{"name": "A", "qid": "12"}], [])
    with pytest.raises(AllowlistError):
        load_allowlists(base)
