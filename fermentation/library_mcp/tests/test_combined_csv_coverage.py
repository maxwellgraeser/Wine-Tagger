"""CI smoke test: every wine in curation/test/combined.csv must resolve its
country / region(s) / grape(s) against the built library.db, canonical
tier, via the same code paths the MCP server exposes.

The expected values are reference assertions (hand-derived from the wines,
cross-checked with curation/test/ground_truth.json), not derived from web
snippets. Each row: input strings the tagger is likely to emit -> expected
canonical outputs.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

CSV_PATH = Path(__file__).resolve().parents[3] / "curation" / "test" / "combined.csv"

# name -> (country_input, [(region_input, canonical_region, expected_parents_subset)],
#          [(grape_input, canonical_grape)])
EXPECTED: dict[str, tuple] = {
    "Annabella Pinot Noir": ("USA",
        [("Russian River Valley", "Russian River Valley", ["Sonoma County", "California"])],
        [("Pinot Noir", "Pinot Noir")]),
    "Aster Ribera del Duero": ("Spain",
        [("Ribera del Duero", "Ribera del Duero", ["Castilla y León"])],
        [("Tinto Fino", "Tempranillo"), ("Tempranillo", "Tempranillo")]),
    "Bayten Sauvignon Blanc": ("South Africa",
        [("Constantia", "Constantia", ["Coastal Region", "Western Cape"])],
        [("Sauvignon Blanc", "Sauvignon Blanc")]),
    "Bila Haut Roussillon": ("France",
        [("Côtes du Roussillon", "Roussillon", ["Languedoc-Roussillon"]),
         ("Roussillon", "Roussillon", [])],
        [("Syrah", "Syrah"), ("Grenache", "Grenache"), ("Carignan", "Carignan")]),
    "Chapelle Bastion Picpoul": ("France",
        [("Picpoul de Pinet", "Picpoul de Pinet", ["Languedoc", "Languedoc-Roussillon"]),
         ("Languedoc-Roussillon", "Languedoc-Roussillon", [])],
        [("Picpoul", "Picpoul Blanc"), ("Piquepoul", "Picpoul Blanc")]),
    "Chocapalha Tinto": ("Portugal",
        [("Lisboa", "Lisboa", []), ("Alenquer", "Alenquer", ["Lisboa"])],
        [("Touriga Nacional", "Touriga Nacional"), ("Tinta Roriz", "Tempranillo"),
         ("Castelao", "Castelão")]),
    "Cloudline PN": ("United States",
        [("Willamette Valley", "Willamette Valley", ["Oregon"])],
        [("PN", "Pinot Noir")]),
    "Curator White": ("South Africa",
        [("Western Cape", "Western Cape", [])],
        [("Chenin Blanc", "Chenin Blanc"), ("Chardonnay", "Chardonnay"), ("Viognier", "Viognier")]),
    "DV Catena Tinto": ("Argentina",
        [("Mendoza", "Mendoza", [])],
        [("Malbec", "Malbec"), ("Bonarda", "Bonarda"), ("Petite Verdot", "Petit Verdot")]),
    "Excelsior Chardonnay": ("South Africa",
        [("Robertson", "Robertson", ["Breede River Valley", "Western Cape"])],
        [("Chardonnay", "Chardonnay")]),
    "Faustino VII Rioja": ("Spain",
        [("Rioja", "Rioja", [])],
        [("Tempranillo", "Tempranillo")]),
    "La Rioja Alta Ardanza": ("Spain",
        [("Rioja Alta", "Rioja Alta", ["Rioja"])],
        [("Tempranillo", "Tempranillo"), ("Garnacha", "Grenache")]),
    "Li Veli Passamante": ("Italy",
        [("Salice Salentino", "Salice Salentino", ["Salento", "Puglia"])],
        [("Negroamaro", "Negroamaro")]),
    "Librandi Ciro Bianco": ("Italy",
        [("Cirò", "Cirò", ["Calabria"]), ("Ciro DOC", "Cirò", [])],
        [("Greco Bianco", "Greco Bianco")]),
    "Massaya Rose": ("Lebanon",
        [("Bekaa Valley", "Bekaa Valley", []), ("Bekaa", "Bekaa Valley", [])],
        [("Cinsault", "Cinsault"), ("Grenache", "Grenache")]),
    "Mont Gravet Rose": ("France",
        [("Pays d'Oc", "Pays d'Oc", ["Languedoc-Roussillon"]), ("IGP Pays d'Oc", "Pays d'Oc", [])],
        [("Cinsault", "Cinsault")]),
    "Neirano Barolo": ("Italy",
        [("Barolo", "Barolo", ["Langhe", "Piedmont"]), ("Piemonte", "Piedmont", [])],
        [("Nebbiolo", "Nebbiolo")]),
    "Paul Buisse Touraine": ("France",
        [("Touraine", "Touraine", ["Loire Valley"])],
        [("Sauvignon Blanc", "Sauvignon Blanc")]),
    "Pav Chavannes Brouilly": ("France",
        [("Brouilly", "Brouilly", ["Beaujolais"])],
        [("Gamay", "Gamay")]),
    "Tessellae Old Vines": ("France",
        [("Côtes du Roussillon", "Roussillon", [])],
        [("Grenache", "Grenache"), ("Syrah", "Syrah"), ("Mourvèdre", "Mourvèdre"),
         ("Carignane", "Carignan")]),
    "Urruzola Txakolina Rose": ("Spain",
        [("Getariako Txakolina", "Getariako Txakolina", ["Basque Country"]),
         ("Txakoli", "Getariako Txakolina", [])],
        [("Hondarrabi Zuri", "Hondarrabi Zuri"), ("Hondarrabi Beltza", "Hondarrabi Beltza")]),
    "Vajra Barolo Albe": ("Italy",
        [("Barolo", "Barolo", ["Piedmont"])],
        [("Nebbiolo", "Nebbiolo")]),
    "Vilafonte Seriously Old Dirt": ("South Africa",
        [("Paarl", "Paarl", ["Coastal Region", "Western Cape"])],
        [("Cabernet Sauvignon", "Cabernet Sauvignon"), ("Merlot", "Merlot"),
         ("Malbec", "Malbec"), ("Cabernet Franc", "Cabernet Franc")]),
    "Zenato Pinot Grigio": ("Italy",
        [("delle Venezie", "delle Venezie", [])],
        [("Pinot Grigio", "Pinot Gris")]),
}


def _csv_names() -> list[str]:
    with CSV_PATH.open(newline="", encoding="utf-8") as fh:
        return [row["name"] for row in csv.DictReader(fh)]


def test_every_csv_wine_has_expectations():
    names = _csv_names()
    assert names, "combined.csv is empty"
    missing = [n for n in names if n not in EXPECTED]
    assert not missing, f"add EXPECTED entries for: {missing}"


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_wine_resolves_canonically(server, name):
    country_in, regions, grapes = EXPECTED[name]

    c = server.lookup_country(country_in)
    assert c["known"], f"{name}: country {country_in!r} unknown"

    for region_in, canonical, parents in regions:
        r = server.lookup_region(region_in)
        assert r["known"], f"{name}: region {region_in!r} unknown"
        assert r["canonical"] == canonical, f"{name}: {region_in!r} -> {r['canonical']!r}"
        assert not r["is_placeholder"], f"{name}: {region_in!r} is placeholder, expected canonical"
        assert r["country"] == c["canonical"], f"{name}: {region_in!r} pinned to {r['country']!r}"
        for p in parents:
            assert p in r["parents"], f"{name}: {region_in!r} parents {r['parents']} lack {p!r}"

    for grape_in, canonical in grapes:
        g = server.lookup_grape(grape_in)
        assert g["known"], f"{name}: grape {grape_in!r} unknown"
        assert g["canonical"] == canonical, f"{name}: {grape_in!r} -> {g['canonical']!r}"
        assert not g["is_placeholder"], f"{name}: {grape_in!r} is placeholder, expected canonical"
        assert not g["is_phrase"]
        assert g["color"] in {"red", "white", "rose"}, f"{name}: {canonical} has no colour"

    # And the whole row passes the gate.
    result = server.submit_tags(
        country=country_in,
        region=[r[0] for r in regions],
        grapes=[g[0] for g in grapes],
        is_blend=None, organic=False, confidence=80,
    )
    assert result["ok"], f"{name}: submit_tags rejected: {result}"
    norm = result["normalized"]
    assert norm["country"] == c["canonical"]
    assert set(g[1] for g in grapes) == set(norm["grapes"])
    for _, canonical, parents in regions:
        assert canonical in norm["region"]
        for p in parents:
            assert p in norm["region"]
