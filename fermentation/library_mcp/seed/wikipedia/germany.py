"""German wine region parser.

Source: https://en.wikipedia.org/wiki/German_wine

German regions nest as Anbaugebiet -> Bereich -> Grosslage -> Einzellage.
This parser is intentionally minimal: it pulls the 13 Anbaugebiete (the
top-level officially recognised quality wine regions) plus their
classification label. The deeper nesting belongs in a follow-up pass
once the schema is exercised against real product strings.
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from . import ParsedCountry, RegionRow

COUNTRY = "Germany"

# The thirteen Anbaugebiete. All of them are on the region allowlist
# (regions.yaml), so this parser contributes nothing new today; it stays
# as the landing spot for a future Bereich/Grosslage -> Anbaugebiet pass.
ANBAUGEBIETE = [
    "Ahr",
    "Baden",
    "Franken",
    "Hessische Bergstrasse",
    "Mittelrhein",
    "Mosel",
    "Nahe",
    "Pfalz",
    "Rheingau",
    "Rheinhessen",
    "Saale-Unstrut",
    "Sachsen",
    "Wurttemberg",
]


def parse(html: str) -> ParsedCountry:
    # We still parse the HTML so future enrichment (Bereich/Grosslage)
    # has a place to land; for now we just emit the canonical list.
    BeautifulSoup(html or "", "html.parser")
    out = ParsedCountry(country=COUNTRY)
    for name in ANBAUGEBIETE:
        out.regions.append(RegionRow(name=name, classification="Anbaugebiet"))
    return out
