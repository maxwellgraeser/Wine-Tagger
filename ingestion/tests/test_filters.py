"""Filter rules (ingestion/filters.toml) and an end-to-end ingest run."""

import csv
import json
import uuid
from pathlib import Path

import pytest

from ingestion import ingest
from ingestion.filters import FILTERS_PATH, Filters, word_regex

F = Filters.load(FILTERS_PATH)


def decide(name, category="", supplier="Winebow"):
    return F.decide(category, supplier, name)


# -- filter 1: category -------------------------------------------------------

@pytest.mark.parametrize("cat", ["Red", "White", "Rose", "Sparkling", "Orange/Amber", "red", "ROSE"])
def test_whitelisted_category_is_kept_regardless_of_vendor_or_name(cat):
    d = decide("Boulevard Tank 7 IPA", cat, "Progressive")
    assert d.keep and d.stage == "category"


@pytest.mark.parametrize("cat", ["Beer", "Accessories", "Dessert", "Sherry", "Aperitif", "Cider", "Food", "Tasting"])
def test_other_category_is_excluded(cat):
    d = decide("Anything", cat)
    assert not d.keep and d.stage == "category" and d.match == cat


# -- filter 2: vendor ----------------------------------------------------------

@pytest.mark.parametrize("supplier", [
    "Cavalier Distributing Florida", "Progressive", "North Fl Sales", "Champion",
    "True", "Lottie Dottie Cards", "Warehouse", "warehouse ", "TRUE",
])
def test_blacklisted_vendor_excludes_uncategorized_rows(supplier):
    d = decide("Some Wine", "", supplier)
    assert not d.keep and d.stage == "vendor"


def test_vendor_match_is_leading_words_not_substring():
    assert decide("Some Wine", "", "Winebow").keep
    assert decide("Some Wine", "", "Truett-Hurst").keep          # "True" is not a leading word
    assert decide("Some Wine", "", "Cavalier Distributing Florida").stage == "vendor"
    assert decide("Some Wine", "", "Lottie Dottie Cards").stage == "vendor"


def test_blank_vendor_passes():
    assert decide("Boschendal Brut", "", "").keep


# -- filter 3: keywords --------------------------------------------------------

@pytest.mark.parametrize("name", [
    "Hollywood Mango IPA", "3 Sons Hazy Thing", "Left Hand Milk Stout", "Boulevard Tropical Tank 7",
    "Cliffton Cider", "Soto Sake Junmai", "Heiwa Kid Daiginjo", "Heiwa Nigori", "Akashi-Tai Honjozo",
    "Fonseca Ruby Port", "Kopke 10yr White Porto", "Taylor Fladgate 20yr Tawny", "Warre's LBV",
    "Warre's 1994 Vintage", "Lustau Amontillado", "Alvear Fino", "Santini Marsala Dry",
    "Antica Torino Vermouth 375ml", "Bertrand Banyuls", "Durban Beaumes de Venise", "Durban Muscat",
    "Bava Moscato", "Dorgo Tokaji Aszu", "d'Yquem Sauternes", "Bergweiler Eiswein", "Casadimonte Vin Santo",
    "Chermette Creme Cassis", "Cocchi Americano", "Savoy Lever Corkscrew", "Spiegelau Bordeaux 4pk Wine Glass",
    "Delivery", "AB Tasting", "Devil's Peak N/A 6pk",
])
def test_non_wine_names_are_excluded(name):
    d = decide(name)
    assert not d.keep and d.stage == "keyword", d


@pytest.mark.parametrize("name", [
    "Casa Santos Lima Red",          # Portuguese wine: "port" must not match inside other words
    "Quinta do Portal Douro",
    "Portugal Ramos Vinho Verde",
    "Clos Ste Magdeleine Cassis",    # Cassis the appellation, not creme de cassis
    "Dorgo Furmint",                 # dry Tokaji
    "Royal Tokaji Dry Furmint",
    "Madonna Spatlese", "Dr Loosen Pralat Auslese", "Graff Riesling Kabinett",
    "Zaccagnini 0.0",
    "Lena Cabernet Box",
    "Caposaldo Bellini", "Zonin Coastal Lemon Spritz",   # the store files these as Sparkling
    "Bonny Doon Take Me Liter",      # "liter" ≠ "licor"
    "Ginestet Bordeaux",             # "gin" must not match inside "Ginestet"
    "Rumor Rose",                    # "rum" inside "Rumor"
    "Alesia Pinot Noir",             # "ale" inside "Alesia"
])
def test_wine_names_pass(name):
    d = decide(name)
    assert d.keep and d.stage == "uncategorized", d


def test_exact_name_exclusions():
    assert decide("Kai Lychee 4pk").stage == "name"
    assert decide("kai  lychee 4PK").stage == "name"
    assert decide("Kai Lychee").keep


def test_word_regex_is_accent_insensitive_and_bounded():
    rx = word_regex("aszú")
    assert rx.search("dorgo tokaji aszu")
    assert not word_regex("port").search("portugal")
    assert word_regex("port").search("fonseca ruby port")
    assert word_regex("beaumes de venise").search("durban beaumes   de venise")


# -- end to end ----------------------------------------------------------------

HEADERS = ["id", "handle", "sku", "composite_name", "name", "description", "product_category",
           "variant_option_one_name", "tags", "supply_price", "retail_price", "brand_name",
           "supplier_name", "active", "inventory_Atlantic_Beach_Wine_Warehouse"]


def _row(name, cat, sup, price="9.99"):
    return [str(uuid.uuid4()), name.lower().replace(" ", "-"), "123", "", name, "", cat, "", "",
            "5", price, "", sup, "1", "12"]


def test_ingest_end_to_end(tmp_path: Path):
    src = tmp_path / "export.csv"
    with open(src, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(HEADERS)
        w.writerow(_row("Annabella Pinot Noir", "Red", "Winebow"))
        w.writerow(_row("3 Sons OP Pils", "Beer", "Progressive"))
        w.writerow(_row("Sunny Cat", "", "Progressive"))
        w.writerow(_row("Kai Lychee 4pk", "", "Mexcor"))
        w.writerow(_row("Kopke 50yr Old Tawny", "", "Maverick"))
        w.writerow(_row("Dorgo Furmint", "", "Maverick"))
        w.writerow(["not-a-uuid"] + _row("Broken", "Red", "Winebow")[1:])
    out = tmp_path / "out"
    summary = ingest.run(src, FILTERS_PATH, out, ingest.Emitter(False))

    assert summary["kept"] == {"total": 2, "by_category": 1, "uncategorized": 1, "categories": {"Red": 1}}
    assert summary["excluded"]["by"] == {"category": 1, "vendor": 1, "name": 1, "keyword": 1}
    assert summary["excluded"]["breakdown"]["keyword"] == {"tawny": 1}
    assert summary["input"]["invalid_rows"] == 1

    combined = list(csv.DictReader(open(out / "combined.csv", encoding="utf-8")))
    assert [r["name"] for r in combined] == ["Annabella Pinot Noir", "Dorgo Furmint"]
    assert [r["ingest_pass"] for r in combined] == ["category", "uncategorized"]
    assert "composite_name" not in combined[0] and "variant_option_one_name" not in combined[0]
    assert combined[0]["inventory_atlantic_beach_wine_warehouse"] == "12.0"

    excluded = list(csv.DictReader(open(out / "excluded.csv", encoding="utf-8")))
    assert [(r["name"], r["excluded_by"]) for r in excluded] == [
        ("3 Sons OP Pils", "category"), ("Sunny Cat", "vendor"),
        ("Kai Lychee 4pk", "name"), ("Kopke 50yr Old Tawny", "keyword"),
    ]
    assert json.load(open(out / "summary.json"))["kept"]["total"] == 2


def test_ingest_rejects_wrong_format(tmp_path: Path):
    src = tmp_path / "inventory.csv"
    src.write_text("Product,SKU,Supplier\nA,1,B\n", encoding="utf-8")
    with pytest.raises(ingest.InputError, match="missing column"):
        ingest.run(src, FILTERS_PATH, tmp_path / "out", ingest.Emitter(False))


def test_fixture_test_wines_all_pass():
    fixture = Path(ingest.FIXTURES_DIR) / "test-wines.csv"
    rows = list(csv.DictReader(open(fixture, encoding="utf-8")))
    assert len(rows) == 24
    assert all(F.decide_row(r).keep for r in rows)
