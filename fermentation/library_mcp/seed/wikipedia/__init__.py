"""Per-country Wikipedia list parsers.

Each module exposes:

    def parse(html: str) -> ParsedCountry

where ParsedCountry is the dataclass below. The orchestrator
(`build_db.py`) calls each parser with HTML fetched from the Wikipedia
REST API and merges the result into the SQLite seeded from Wikidata.

Rows whose Wikidata QID cannot be resolved are dropped — the database is
QID-keyed and un-keyed rows would create silent duplicates.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GrapeRow:
    canonical_name: str
    color: str | None = None
    synonyms: list[str] = field(default_factory=list)
    wikidata_qid: str | None = None        # required to actually insert


@dataclass
class RegionRow:
    name: str
    parent: str | None = None
    classification: str | None = None
    wikidata_qid: str | None = None


@dataclass
class ParsedCountry:
    country: str
    grapes: list[GrapeRow] = field(default_factory=list)
    regions: list[RegionRow] = field(default_factory=list)
    # region_name -> list of grape canonical names (or synonyms; resolve
    # against the grapes table by lower-cased lookup against canonical_name
    # then grape_synonyms.synonym).
    region_grapes: dict[str, list[str]] = field(default_factory=dict)
