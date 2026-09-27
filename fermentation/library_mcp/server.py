"""Wine library MCP server.

Stdio FastMCP server backed by the baked SQLite at `library.db`. The
tagger LLM browses countries / regions / grapes via the `lookup_*` /
`list_*` tools, then commits a final tag set via `submit_tags`.
`submit_tags` is the canonicalization gate -- whatever it emits on success
is what `ferment.py` writes to the DB.

Two tiers (schema.sql): canonical rows (allowlist, `is_canonical=1`) and
placeholder rows (filtered Wikidata long tail, `is_canonical=0`). Lookups
resolve canonical first and flag placeholders with `is_placeholder=true`;
`list_*` return canonical rows only; `submit_tags` rejects placeholders
and unknowns so the model is steered back to the canonical vocabulary.

All name resolution runs against in-memory accent-folded indexes built
once at startup (the DB is a few thousand rows) -- no per-call table scans.

Region names can repeat across countries (La Rioja in Spain and
Argentina); `lookup_region`, `list_grapes` and `submit_tags` use the
wine's country to pick one. A region string that misses exactly is
retried without classification words ("Barolo DOCG", "W.O. Stellenbosch")
and split on commas ("Coastal Region, Western Cape, South Africa").

Run standalone for smoke testing:
    python -m fermentation.library_mcp.server
"""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import Field

DB_PATH = Path(__file__).resolve().parent / "library.db"

# Generic phrases the model sometimes hallucinates as grape names.
_PHRASE_PATTERNS = (
    "blend",
    "unknown",
    "various",
    "varietal",
    "red wine",
    "white wine",
    "field blend",
    "proprietary",
    "n/a",
    "none",
    "mixed",
    "gsm",
)


# ---------- connection (read-only) ----------

def _connect_ro() -> sqlite3.Connection:
    if not DB_PATH.exists():
        # Build an empty schema-valid DB so the server still starts; the
        # seed orchestrator should be run to populate it.
        from .seed import build_db  # local import; only on cold start

        conn = sqlite3.connect(DB_PATH)
        build_db.ensure_schema(conn)
        conn.close()
    uri = f"file:{DB_PATH}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


_CONN = _connect_ro()


# ---------- normalisation helpers ----------

# Label spellings that fold to one key: a hyphen inside a word is a space
# ("Nuits-Saint-Georges" = "Nuits Saint Georges"), and "St"/"St."/"Ste"
# abbreviate Saint/Sainte ("Morey St Denis", "St.-Émilion"). A spaced dash
# is kept: it separates compound parts ("Napa Valley - California").
_INNER_HYPHEN = re.compile(r"(?<=\S)[-\u2010\u2011](?=\S)")
_SAINT = re.compile(r"\b(st|ste)\b\.?")


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = _INNER_HYPHEN.sub(" ", s.lower())
    s = _SAINT.sub(lambda m: "saint" if m.group(1) == "st" else "sainte", s)
    return re.sub(r"\s+", " ", s).strip()


def _is_phrase(name: str) -> bool:
    """True for non-grape filler ('Bordeaux Blend', 'unknown', 'GSM')."""
    f = _fold(name)
    if not f:
        return True
    return any(p in f for p in _PHRASE_PATTERNS)


# Classification words that labels and web pages attach to a region name.
# Folded (lowercase, no accents). Stripped from either end of a region
# string only after the exact lookup misses, so names that contain one
# ("Chianti Classico", "Saint-Émilion Grand Cru") still match first.
_CLASS_TOKENS = sorted({
    "appellation d'origine controlee", "appellation d'origine protegee",
    "appellation controlee", "appellation", "aoc", "aop", "ac",
    "denominazione di origine controllata e garantita",
    "denominazione di origine controllata", "indicazione geografica tipica",
    "docg", "doc", "igt", "igp", "dop",
    "denominacion de origen calificada", "denominacion de origen",
    "vino de la tierra", "vino de pago", "doca", "doq", "do", "vp",
    "denominacao de origem controlada", "vinho regional", "vr",
    "vin de pays", "indication geographique protegee",
    "american viticultural area", "ava",
    "wine of origin", "w.o.", "wo",
    "qualitatswein", "pradikatswein", "dac",
    "geographical indication", "gi", "ig", "pdo", "pgi", "vqa",
    "premier cru", "1er cru", "grand cru",
    "pge", "pop",                    # Greek PGI / PDO
    # dotted label forms: "D.O. Rioja", "D.O.Ca.", "A.O.C."
    "d.o.", "d.o", "d.o.ca.", "d.o.ca", "d.o.c.", "d.o.c", "d.o.c.g.", "d.o.c.g",
    "a.o.c.", "a.o.c", "a.o.p.", "a.o.p", "a.v.a.", "a.v.a", "i.g.t.", "i.g.t",
    "i.g.p.", "i.g.p", "w.o", "p.g.e.", "p.g.e", "p.o.p.", "p.o.p",
}, key=len, reverse=True)
_CLASS_ALT = "|".join(re.escape(t) for t in _CLASS_TOKENS)
_CLASS_LEAD = re.compile(rf"^(?:{_CLASS_ALT})(?:\s+|$)")
_CLASS_TRAIL = re.compile(rf"(?:^|\s+)(?:{_CLASS_ALT})$")
_PAREN_TAIL = re.compile(r"\s*\([^()]*\)$")
# "Appellation Margaux Contrôlée" puts the name in the middle.
_APPELLATION_WRAP = re.compile(r"^appellation (.+?) (?:controlee|protegee)$")
# Commas, semicolons, slashes, and a dash with spaces round it; a bare
# hyphen is part of names (Languedoc-Roussillon).
_REGION_SPLIT = re.compile(r"\s*(?:[,;/]|\s-\s)\s*")


def _strip_classification(folded: str) -> str:
    s = folded
    prev = None
    while s != prev:
        prev = s
        m = _APPELLATION_WRAP.match(s)
        if m:
            s = m.group(1)
        s = _PAREN_TAIL.sub("", s)
        s = _CLASS_LEAD.sub("", s)
        s = _CLASS_TRAIL.sub("", s)
        s = s.strip(" -–")
    return s


def _region_variants(name: str) -> list[str]:
    """Folded strings to try for a region, in order: as given, without
    classification words, then each comma-separated part (most specific
    first in the usual "Swartland, Western Cape, South Africa" order)."""
    base = _fold(name)
    out = [base]

    def add(v: str) -> None:
        if v and v not in out:
            out.append(v)

    add(_strip_classification(base))
    add(re.sub(r"\s[-\u2013]\s", " ", base))       # "Côtes du Rhône - Villages"
    parts = [p for p in _REGION_SPLIT.split(base) if p]
    if len(parts) > 1:
        for part in parts:
            add(part)
            add(_strip_classification(part))
    return out


# ---------- in-memory index ----------

@dataclass
class Country:
    id: int
    name: str
    iso: Optional[str]
    canonical: bool


@dataclass
class Region:
    id: int
    name: str
    country_id: Optional[int]
    parent_id: Optional[int]
    classification: Optional[str]
    canonical: bool


@dataclass
class Grape:
    id: int
    name: str
    color: Optional[str]
    origin_country_id: Optional[int]
    canonical: bool
    synonyms: list[str] = field(default_factory=list)


class _Index:
    """Folded label -> candidate ids. Canonical rows are listed before
    placeholders for the same label (insertion order within each tier), so
    `first()` is canonical-first. A label can name several rows: region
    names repeat across countries."""

    def __init__(self) -> None:
        self._map: dict[str, tuple[list[int], list[int]]] = {}

    def add(self, label: str, row_id: int, canonical: bool) -> None:
        key = _fold(label)
        if not key:
            return
        canon, place = self._map.setdefault(key, ([], []))
        if row_id in canon or row_id in place:
            return
        (canon if canonical else place).append(row_id)

    def all(self, label: str) -> list[int]:
        canon, place = self._map.get(_fold(label), ((), ()))
        return [*canon, *place]

    def first(self, label: str) -> Optional[int]:
        ids = self.all(label)
        return ids[0] if ids else None


def _load_index(conn: sqlite3.Connection):
    countries: dict[int, Country] = {}
    regions: dict[int, Region] = {}
    grapes: dict[int, Grape] = {}
    c_idx, r_idx, g_idx = _Index(), _Index(), _Index()

    for r in conn.execute("SELECT id, name, iso_code, is_canonical FROM countries"):
        countries[r["id"]] = Country(r["id"], r["name"], r["iso_code"], bool(r["is_canonical"]))
    for r in conn.execute("SELECT id, name, country_id, parent_region_id, classification, is_canonical FROM regions"):
        regions[r["id"]] = Region(r["id"], r["name"], r["country_id"], r["parent_region_id"],
                                  r["classification"], bool(r["is_canonical"]))
    for r in conn.execute("SELECT id, canonical_name, color, origin_country_id, is_canonical FROM grapes"):
        grapes[r["id"]] = Grape(r["id"], r["canonical_name"], r["color"], r["origin_country_id"],
                                bool(r["is_canonical"]))

    # Canonical names first so they win ties against placeholder synonyms.
    for c in countries.values():
        c_idx.add(c.name, c.id, True)
    for r in regions.values():
        r_idx.add(r.name, r.id, r.canonical)
    for g in grapes.values():
        g_idx.add(g.name, g.id, g.canonical)
    for row in conn.execute("SELECT country_id, synonym FROM country_synonyms"):
        c_idx.add(row["synonym"], row["country_id"], True)
    for row in conn.execute("SELECT region_id, synonym FROM region_synonyms"):
        reg = regions.get(row["region_id"])
        if reg:
            r_idx.add(row["synonym"], reg.id, reg.canonical)
    for row in conn.execute("SELECT grape_id, synonym FROM grape_synonyms ORDER BY synonym"):
        g = grapes.get(row["grape_id"])
        if g:
            g.synonyms.append(row["synonym"])
            g_idx.add(row["synonym"], g.id, g.canonical)
    # ISO codes resolve too ("US", "FR").
    for c in countries.values():
        if c.iso:
            c_idx.add(c.iso, c.id, True)
    return countries, regions, grapes, c_idx, r_idx, g_idx


_COUNTRIES, _REGIONS, _GRAPES, _C_IDX, _R_IDX, _G_IDX = _load_index(_CONN)


def _resolve_country(name: str) -> Optional[Country]:
    if not name:
        return None
    cid = _C_IDX.first(name)
    return _COUNTRIES.get(cid) if cid is not None else None


def _region_candidates(name: str) -> list[Region]:
    """Regions for the first variant of `name` that matches anything.
    Fallback variants that are country names ("Kakheti, Georgia", "Napa,
    CA") are tried only after every other variant has missed, so they can't
    beat the real region; "Georgia, United States" still finds a Georgia
    region that way."""
    if not name:
        return []
    variants = _region_variants(name)
    countryish = {v for v in variants[1:] if _C_IDX.first(v) is not None}
    for v in [*(v for v in variants if v not in countryish), *(v for v in variants if v in countryish)]:
        ids = _R_IDX.all(v)
        if ids:
            return [_REGIONS[r] for r in ids if r in _REGIONS]
    return []


def _pick_region(cands: list[Region], country_id: Optional[int]) -> tuple[Optional[Region], list[Region]]:
    """Choose one candidate. With a country: that country's rows first
    (canonical, then placeholder), then the rest. Returns (choice,
    alternatives), where alternatives are canonical candidates in OTHER
    countries that the choice was made over without a country to go on."""
    if not cands:
        return None, []
    if country_id is not None:
        local = [r for r in cands if r.country_id == country_id]
        if local:
            return local[0], []
    choice = cands[0]
    alts = [r for r in cands if r.canonical and r.country_id != choice.country_id]
    return choice, alts


def _resolve_region(name: str, country_id: Optional[int] = None) -> Optional[Region]:
    return _pick_region(_region_candidates(name), country_id)[0]


def _resolve_grape(name: str) -> Optional[Grape]:
    if not name:
        return None
    gid = _G_IDX.first(name)
    return _GRAPES.get(gid) if gid is not None else None


def _region_chain(region: Region) -> list[Region]:
    """Parent chain excluding the region itself, nearest first."""
    out: list[Region] = []
    seen = {region.id}
    pid = region.parent_id
    while pid is not None and pid not in seen:
        seen.add(pid)
        parent = _REGIONS.get(pid)
        if not parent:
            break
        out.append(parent)
        pid = parent.parent_id
    return out


def _region_country(region: Region) -> Optional[str]:
    c = _COUNTRIES.get(region.country_id) if region.country_id else None
    return c.name if c else None


# ---------- server ----------

mcp = FastMCP("wine-library")


@mcp.tool()
def lookup_country(name: str) -> dict:
    """Resolve a country name (or ISO code / common abbreviation like USA)
    to its canonical form. Returns {canonical, iso, known}."""
    row = _resolve_country(name)
    if not row:
        return {"canonical": None, "iso": None, "known": False}
    return {"canonical": row.name, "iso": row.iso, "known": True}


@mcp.tool()
def lookup_region(name: str, country: Optional[str] = None) -> dict:
    """Resolve a wine region (or a synonym: Piemonte, Bourgogne, Napa).

    Pass `country` when you know it: a few names exist in more than one
    country (La Rioja: Spain and Argentina). Without it, the answer may
    carry `alternatives` ("La Rioja (Argentina)") -- look up again with the
    country if the first answer is in the wrong one.

    Returns {canonical, country, parents[], classification, is_placeholder,
    known}. `parents` is the broader chain, nearest first (Russian River
    Valley -> [Sonoma County, North Coast, California]). `is_placeholder`
    is true for real but non-canonical regions: they will NOT pass
    submit_tags -- pick the nearest canonical parent or a region from
    list_regions(country) instead.
    """
    crow = _resolve_country(country) if country else None
    row, alts = _pick_region(_region_candidates(name), crow.id if crow else None)
    if not row:
        return {"canonical": None, "country": None, "parents": [], "classification": None,
                "is_placeholder": False, "known": False}
    out = {
        "canonical": row.name,
        "country": _region_country(row),
        "parents": [p.name for p in _region_chain(row)],
        "classification": row.classification,
        "is_placeholder": not row.canonical,
        "known": True,
    }
    if alts:
        out["alternatives"] = [f"{a.name} ({_region_country(a)})" for a in alts]
    return out


@mcp.tool()
def lookup_grape(name: str) -> dict:
    """Resolve a grape (or one of its synonyms: Garnacha, Shiraz, PN) to
    its canonical name.

    Returns {canonical, color, origin, synonyms[], is_phrase,
    is_placeholder, known}. `is_phrase` flips for non-grape filler
    ('Bordeaux Blend', 'unknown') -- submit real varieties or an empty
    list. `is_placeholder` flips for real but niche grapes outside the
    canonical list; those will not pass submit_tags.
    """
    empty = {"canonical": None, "color": None, "origin": None, "synonyms": [],
             "is_phrase": False, "is_placeholder": False, "known": False}
    if _is_phrase(name):
        return {**empty, "is_phrase": True}
    row = _resolve_grape(name)
    if not row:
        return empty
    origin = None
    if row.origin_country_id:
        c = _COUNTRIES.get(row.origin_country_id)
        origin = c.name if c else None
    return {
        "canonical": row.name,
        "color": row.color,
        "origin": origin,
        "synonyms": row.synonyms,
        "is_phrase": False,
        "is_placeholder": not row.canonical,
        "known": True,
    }


@mcp.tool()
def list_countries() -> list[str]:
    """Return every canonical country name."""
    return sorted(c.name for c in _COUNTRIES.values() if c.canonical)


@mcp.tool()
def list_regions(country: Optional[str] = None) -> list[str]:
    """Return canonical region names. If `country` is given, filter to
    regions in that country (any spelling lookup_country accepts)."""
    if country is None:
        return sorted(r.name for r in _REGIONS.values() if r.canonical)
    crow = _resolve_country(country)
    if not crow:
        return []
    return sorted(r.name for r in _REGIONS.values() if r.canonical and r.country_id == crow.id)


@mcp.tool()
def list_grapes(country: Optional[str] = None, region: Optional[str] = None) -> list[str]:
    """Return canonical grape names. If `region` is provided, filter to
    grapes recorded as grown there. If only
    `country` is provided, filter to grapes whose origin matches."""
    if region:
        crow = _resolve_country(country) if country else None
        rrow = _resolve_region(region, crow.id if crow else None)
        if not rrow:
            return []
        ids = [r["grape_id"] for r in _CONN.execute(
            "SELECT grape_id FROM region_grapes WHERE region_id = ?", (rrow.id,))]
        return sorted(_GRAPES[i].name for i in ids if i in _GRAPES and _GRAPES[i].canonical)
    if country:
        crow = _resolve_country(country)
        if not crow:
            return []
        return sorted(g.name for g in _GRAPES.values() if g.canonical and g.origin_country_id == crow.id)
    return sorted(g.name for g in _GRAPES.values() if g.canonical)


# ---------- terminal tool: submit_tags ----------

_HINTS = {
    "unknown_country": (
        "The country name did not resolve. Call lookup_country (ISO codes and "
        "common abbreviations work) or list_countries, then resubmit."
    ),
    "phrase_grapes": (
        "Generic phrases like 'Bordeaux Blend' or 'unknown' are not grapes. "
        "Submit the actual varieties; if truly unknown, leave grapes=[]."
    ),
    # Not an issue: a submission with no grapes is ACCEPTED (ok: true) and
    # reported under `warnings` so the country/region survive; the empty
    # grape list is what routes the row to needs_review downstream.
    "unknown_category": (
        "category must be one of Red, White, Rose, Sparkling (or null when the "
        "product already has one). Pick the one the snippets support and resubmit."
    ),
    "no_grapes": (
        "Grape list is empty; accepted as-is. The row will route to "
        "needs_review. Only add grapes if a source actually names them."
    ),
    "non_canonical_grape": (
        "One or more grape names aren't in the canonical list. Call "
        "lookup_grape on each to find the canonical spelling, or list_grapes "
        "to browse."
    ),
    "placeholder_grape": (
        "One or more grapes resolved to a real but non-canonical (niche) "
        "variety. If the source names it under a more common name, use that; "
        "otherwise drop it from the list."
    ),
    "unknown_region": (
        "One or more regions did not resolve at all. Call lookup_region to "
        "check spelling/synonyms, or list_regions(country) to browse; if it "
        "isn't there, drop it and keep the broadest region you are sure of."
    ),
    "non_canonical_region": (
        "One or more regions resolved to a real but non-canonical entry. Use "
        "lookup_region on it and submit the nearest canonical parent from "
        "its `parents` list instead (or another region from list_regions)."
    ),
    "ambiguous_region": (
        "A region name exists in more than one country. Pass `country` so "
        "the right one is used."
    ),
    "region_country_mismatch": (
        "A region resolves to a different country than the one you submitted. "
        "Re-check with lookup_region; either fix the country or pick a region "
        "in the country you intended."
    ),
    "country_in_region_slot": (
        "A country name appeared in the region list. Region must be a wine "
        "region (e.g. 'Veneto'), not a country."
    ),
    "is_blend_mismatch": (
        "is_blend disagrees with the grape count. One grape -> is_blend=false; "
        "two or more -> is_blend=true."
    ),
}


_CATEGORY_OPTIONS = ("Red", "White", "Rose", "Sparkling")
_CATEGORY_ALIASES = {
    "red": "Red", "rouge": "Red", "tinto": "Red", "rosso": "Red",
    "white": "White", "blanc": "White", "blanco": "White", "bianco": "White",
    "rose": "Rose", "rosado": "Rose", "rosato": "Rose",
    "sparkling": "Sparkling", "champagne": "Sparkling", "prosecco": "Sparkling", "cava": "Sparkling",
}


def _resolve_category(name: str) -> Optional[str]:
    return _CATEGORY_ALIASES.get(_fold(name))


def _add_issue(issues: list[str], code: str) -> None:
    if code not in issues:
        issues.append(code)


@mcp.tool()
def submit_tags(
    country: Optional[str],
    region: Annotated[list[str], Field(description=(
        "Canonical region names, most-specific first; parents are added "
        "automatically. Do not include the country name."))],
    grapes: Annotated[list[str], Field(description=(
        "Canonical grape names. An empty list is accepted (ok: true with a "
        "no_grapes warning) when no source names the grapes -- never guess."))],
    is_blend: Optional[bool],
    organic: Optional[bool],
    confidence: Optional[int],
    category: Annotated[Optional[str], Field(description=(
        "Only when the product Category is (unknown): one of Red, White, "
        "Rose, Sparkling, from the snippets' description of the wine. "
        "Otherwise null."))] = None,
) -> dict:
    """Canonicalise and validate a proposed tag set.

    `category` is optional: one of Red / White / Rose / Sparkling (accents and
    case ignored, "rosé"/"rosado"/"rosato" accepted). Fill it only when the
    product had no category; anything else is `unknown_category`.

    On success returns {ok: True, normalized: {...}} with canonical values;
    `normalized.region` is expanded with each region's parent chain
    (Willamette Valley -> [Willamette Valley, Oregon]) and `country` is
    inferred from the regions when omitted. On failure returns
    {ok: False, issues: [...], hints: {...}} -- read the hints, fix, and
    call again. Placeholder (non-canonical) grapes/regions and unknown
    names never pass.
    """
    region = list(region or [])
    grapes = list(grapes or [])
    issues: list[str] = []
    detail: dict[str, list[str]] = {}

    # --- country ---
    country_row = _resolve_country(country) if country else None
    canonical_country: Optional[str] = country_row.name if country_row else None
    if country and not country_row:
        _add_issue(issues, "unknown_country")
        detail["unknown_country"] = [country]

    # --- regions ---
    # Which country picks between same-named regions: the submitted one, or
    # else the single country of the regions that aren't ambiguous.
    pick_country_id = country_row.id if country_row else None
    if pick_country_id is None:
        sure = {
            row.country_id
            for row, alts in (_pick_region(_region_candidates(r), None) for r in region if r)
            if row is not None and row.canonical and not alts
        }
        if len(sure) == 1:
            pick_country_id = next(iter(sure))

    normalized_regions: list[str] = []
    region_countries: set[str] = set()
    for r in region:
        if not r or not str(r).strip():
            continue
        rrow, alts = _pick_region(_region_candidates(r), pick_country_id)
        if rrow is not None and alts and pick_country_id is None:
            _add_issue(issues, "ambiguous_region")
            detail.setdefault("ambiguous_region", []).append(
                f"{r} -> {', '.join(f'{x.name} ({_region_country(x)})' for x in [rrow, *alts])}"
            )
            continue
        if rrow is None:
            if _resolve_country(r):
                _add_issue(issues, "country_in_region_slot")
                detail.setdefault("country_in_region_slot", []).append(r)
            else:
                _add_issue(issues, "unknown_region")
                detail.setdefault("unknown_region", []).append(r)
            continue
        if not rrow.canonical:
            _add_issue(issues, "non_canonical_region")
            detail.setdefault("non_canonical_region", []).append(
                f"{r} -> {rrow.name} (parents: {[p.name for p in _region_chain(rrow)]})"
            )
            continue
        for node in [rrow, *_region_chain(rrow)]:
            if node.name not in normalized_regions:
                normalized_regions.append(node.name)
        rc = _region_country(rrow)
        if rc:
            region_countries.add(rc)

    if canonical_country and region_countries and canonical_country not in region_countries:
        _add_issue(issues, "region_country_mismatch")
        detail["region_country_mismatch"] = sorted(region_countries)
    if canonical_country is None and not country and len(region_countries) == 1:
        canonical_country = next(iter(region_countries))

    # --- grapes ---
    normalized_grapes: list[str] = []
    phrase_seen: list[str] = []
    non_canonical: list[str] = []
    placeholder: list[str] = []
    for g in grapes:
        if not g or not str(g).strip():
            continue
        if _is_phrase(g):
            phrase_seen.append(g)
            continue
        grow = _resolve_grape(g)
        if grow is None:
            non_canonical.append(g)
        elif not grow.canonical:
            placeholder.append(f"{g} -> {grow.name}")
        elif grow.name not in normalized_grapes:
            normalized_grapes.append(grow.name)

    if phrase_seen:
        _add_issue(issues, "phrase_grapes")
        detail["phrase_grapes"] = phrase_seen
    if non_canonical:
        _add_issue(issues, "non_canonical_grape")
        detail["non_canonical_grape"] = non_canonical
    if placeholder:
        _add_issue(issues, "placeholder_grape")
        detail["placeholder_grape"] = placeholder
    warnings: list[str] = []
    if not normalized_grapes and not phrase_seen and not non_canonical and not placeholder:
        # Empty grapes are allowed (the tagger prompt tells the model to submit
        # [] rather than guess). Surface it as a warning, never a rejection --
        # rejecting here made the model retry until it gave up and lost the
        # country/region it had already found.
        warnings.append("no_grapes")

    # --- category ---
    canonical_category: Optional[str] = None
    if category is not None and str(category).strip():
        canonical_category = _resolve_category(category)
        if canonical_category is None:
            _add_issue(issues, "unknown_category")
            detail["unknown_category"] = [category]

    # --- is_blend ---
    if is_blend is not None and normalized_grapes:
        expected = len(normalized_grapes) >= 2
        if bool(is_blend) != expected:
            _add_issue(issues, "is_blend_mismatch")

    if issues:
        hints = {}
        for code in issues:
            hint = _HINTS.get(code, "")
            if code in detail:
                hint = f"{hint} Offending: {detail[code]}"
            hints[code] = hint
        return {"ok": False, "issues": issues, "hints": hints}

    out: dict = {
        "ok": True,
        "normalized": {
            "country": canonical_country,
            "region": normalized_regions,
            "grapes": normalized_grapes,
            "is_blend": (
                bool(is_blend) if is_blend is not None else (len(normalized_grapes) >= 2)
            ),
            "organic": bool(organic) if organic is not None else False,
            "confidence": confidence,
            "category": canonical_category,
        },
    }
    if warnings:
        out["warnings"] = warnings
        out["hints"] = {w: _HINTS.get(w, "") for w in warnings}
    return out


if __name__ == "__main__":
    mcp.run()  # stdio transport
