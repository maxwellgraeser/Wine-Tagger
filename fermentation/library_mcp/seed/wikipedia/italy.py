"""Italian wine grape / region list parser.

Source pages:
  https://en.wikipedia.org/wiki/Italian_wine        (region overview)
  https://en.wikipedia.org/wiki/List_of_Italian_grape_varieties

The Italian grape list is one of the cleaner per-country tables on
Wikipedia: three columns (Grape | Color | Region). We treat each row as
authoritative for the (region -> grape) edge; the orchestrator resolves
both ends by name/synonym against the allowlist-seeded tables.
"""

from __future__ import annotations

import re
from urllib.parse import unquote

from bs4 import BeautifulSoup

from . import GrapeRow, ParsedCountry, RegionRow

COUNTRY = "Italy"

# Map Italian color labels onto our canonical buckets.
_COLOR_MAP = {
    "red": "red",
    "rosso": "red",
    "white": "white",
    "bianco": "white",
    "rose": "rose",
    "rosato": "rose",
    "pink": "rose",
}


def _qid_from_href(href: str | None) -> str | None:
    """Wikipedia anchors don't carry the QID (Parsoid HTML has no
    data-wikidata-item-id). Return the page slug as a hint only; the
    orchestrator matches by name/synonym, never by this value."""
    if not href or not href.startswith("/wiki/"):
        return None
    return unquote(href[len("/wiki/"):])


def parse(html: str) -> ParsedCountry:
    soup = BeautifulSoup(html, "html.parser")
    out = ParsedCountry(country=COUNTRY)

    # Find the main grape table. Wikipedia uses class="wikitable" for
    # structured lists.
    for table in soup.find_all("table", class_="wikitable"):
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        if not any("grape" in h or "variety" in h for h in headers):
            continue
        for row in table.find_all("tr")[1:]:
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            name_cell = cells[0]
            name = name_cell.get_text(strip=True)
            if not name:
                continue
            link = name_cell.find("a")
            slug = _qid_from_href(link.get("href") if link else None)
            color_text = cells[1].get_text(strip=True).lower() if len(cells) > 1 else ""
            color = _COLOR_MAP.get(color_text)
            region_text = cells[2].get_text(strip=True) if len(cells) > 2 else ""

            grape = GrapeRow(canonical_name=name, color=color, wikidata_qid=slug)
            out.grapes.append(grape)

            for region in _split_regions(region_text):
                out.region_grapes.setdefault(region, []).append(name)
                if region and region not in {r.name for r in out.regions}:
                    out.regions.append(RegionRow(name=region))

    return out


def _split_regions(text: str) -> list[str]:
    if not text:
        return []
    parts = re.split(r"[,;]| and ", text)
    return [p.strip() for p in parts if p.strip()]
