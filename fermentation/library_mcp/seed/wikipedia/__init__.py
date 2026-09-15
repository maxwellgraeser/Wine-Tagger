"""Per-country Wikipedia list parsers.

Each module exposes:

    def parse(html: str) -> ParsedCountry

where ParsedCountry is the dataclass below. The orchestrator
(`build_db.py`) calls each parser with HTML fetched from the Wikipedia
REST API and merges the result into the SQLite seeded from Wikidata.

Parsers are an *enrichment* source only. `build_db.ingest_wikipedia`
resolves every region and grape they mention by name/synonym against rows
the canonical (allowlist) and placeholder passes already inserted, adds
`region_grapes` edges, and fills in missing grape colours. It never mints
new region or grape rows -- that was the v1 source of duplicate regions
("Emilia Romagna" vs "Emilia-Romagna"). Anything a parser names that the
allowlists don't know is silently skipped; add it to the YAML instead.

Note: Wikipedia REST HTML does NOT carry Wikidata QIDs on anchors, so
`wikidata_qid` on these rows is only ever a page slug hint, not a QID.
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
