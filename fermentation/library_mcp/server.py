"""Wine library MCP server.

Stdio FastMCP server backed by the baked SQLite at `library.db`. The
tagger LLM browses canonical countries / regions / grapes via the
`lookup_*` / `list_*` tools, then commits a final tag set via
`submit_tags`. `submit_tags` is the canonicalization gate -- whatever it
emits on success is what `ferment.py` writes to the DB.

Run standalone for smoke testing:
    python -m fermentation.library_mcp.server
"""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

DB_PATH = Path(__file__).resolve().parent / "library.db"

# Generic phrases the model sometimes hallucinates as grape names.
_PLACEHOLDER_PATTERNS = (
    "blend",
    "unknown",
    "various",
    "varietal",
    "red wine",
    "white wine",
    "field blend",
    "proprietary",
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

def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", s).strip().lower()


def _is_placeholder_grape(name: str) -> bool:
    f = _fold(name)
    if not f:
        return True
    return any(p in f for p in _PLACEHOLDER_PATTERNS)


def _resolve_country(name: str) -> Optional[sqlite3.Row]:
    if not name:
        return None
    row = _CONN.execute(
        "SELECT * FROM countries WHERE name = ? COLLATE NOCASE", (name,)
    ).fetchone()
    if row:
        return row
    # Loose match: ignore accents/case.
    folded = _fold(name)
    for r in _CONN.execute("SELECT * FROM countries"):
        if _fold(r["name"]) == folded:
            return r
    return None


def _resolve_region(name: str) -> Optional[sqlite3.Row]:
    if not name:
        return None
    row = _CONN.execute(
        "SELECT * FROM regions WHERE name = ? COLLATE NOCASE", (name,)
    ).fetchone()
    if row:
        return row
    folded = _fold(name)
    for r in _CONN.execute("SELECT * FROM regions"):
        if _fold(r["name"]) == folded:
            return r
    return None


def _region_parents(region_id: int) -> tuple[list[str], Optional[str]]:
    """Walk parent chain (excluding the row itself) and return the
    country name pinned on the leaf region."""
    parents: list[str] = []
    country_name: Optional[str] = None
    seen: set[int] = set()
    cur = _CONN.execute(
        "SELECT id, name, country_id, parent_region_id FROM regions WHERE id = ?",
        (region_id,),
    ).fetchone()
    if not cur:
        return parents, None
    if cur["country_id"]:
        crow = _CONN.execute(
            "SELECT name FROM countries WHERE id = ?", (cur["country_id"],)
        ).fetchone()
        if crow:
            country_name = crow["name"]
    parent_id = cur["parent_region_id"]
    while parent_id and parent_id not in seen:
        seen.add(parent_id)
        row = _CONN.execute(
            "SELECT id, name, parent_region_id FROM regions WHERE id = ?", (parent_id,)
        ).fetchone()
        if not row:
            break
        parents.append(row["name"])
        parent_id = row["parent_region_id"]
    return parents, country_name


def _resolve_grape(name: str) -> Optional[sqlite3.Row]:
    if not name:
        return None
    row = _CONN.execute(
        "SELECT * FROM grapes WHERE canonical_name = ? COLLATE NOCASE", (name,)
    ).fetchone()
    if row:
        return row
    row = _CONN.execute(
        """SELECT g.* FROM grapes g
             JOIN grape_synonyms s ON s.grape_id = g.id
            WHERE s.synonym = ? COLLATE NOCASE""",
        (name,),
    ).fetchone()
    if row:
        return row
    folded = _fold(name)
    for r in _CONN.execute("SELECT * FROM grapes"):
        if _fold(r["canonical_name"]) == folded:
            return r
    return None


def _grape_synonyms(grape_id: int) -> list[str]:
    return [
        r["synonym"]
        for r in _CONN.execute(
            "SELECT synonym FROM grape_synonyms WHERE grape_id = ? ORDER BY synonym",
            (grape_id,),
        )
    ]


# ---------- server ----------

mcp = FastMCP("wine-library")


@mcp.tool()
def lookup_country(name: str) -> dict:
    """Resolve a country name to its canonical form.

    Returns {canonical, iso, known}. `known` is False if the input does
    not match any row; `canonical` is then None.
    """
    row = _resolve_country(name)
    if not row:
        return {"canonical": None, "iso": None, "known": False}
    return {"canonical": row["name"], "iso": row["iso_code"], "known": True}


@mcp.tool()
def lookup_region(name: str) -> dict:
    """Resolve a region. Returns {canonical, country, parents[], known}.

    `parents` is the broader region chain (Russian River Valley ->
    [Sonoma, California]).
    """
    row = _resolve_region(name)
    if not row:
        return {"canonical": None, "country": None, "parents": [], "known": False}
    parents, country = _region_parents(row["id"])
    return {
        "canonical": row["name"],
        "country": country,
        "parents": parents,
        "known": True,
    }


@mcp.tool()
def lookup_grape(name: str) -> dict:
    """Resolve a grape (or one of its synonyms) to its canonical name.

    Returns {canonical, color, origin, synonyms[], is_placeholder, known}.
    Placeholder phrases (Bordeaux Blend, unknown, ...) flip `is_placeholder`;
    the model should treat those as 'find real grape names'.
    """
    if _is_placeholder_grape(name):
        return {
            "canonical": None,
            "color": None,
            "origin": None,
            "synonyms": [],
            "is_placeholder": True,
            "known": False,
        }
    row = _resolve_grape(name)
    if not row:
        return {
            "canonical": None,
            "color": None,
            "origin": None,
            "synonyms": [],
            "is_placeholder": False,
            "known": False,
        }
    origin = None
    if row["origin_country_id"]:
        cr = _CONN.execute(
            "SELECT name FROM countries WHERE id = ?", (row["origin_country_id"],)
        ).fetchone()
        if cr:
            origin = cr["name"]
    return {
        "canonical": row["canonical_name"],
        "color": row["color"],
        "origin": origin,
        "synonyms": _grape_synonyms(row["id"]),
        "is_placeholder": False,
        "known": True,
    }


@mcp.tool()
def list_countries() -> list[str]:
    """Return every canonical country name."""
    return [r["name"] for r in _CONN.execute("SELECT name FROM countries ORDER BY name")]


@mcp.tool()
def list_regions(country: Optional[str] = None) -> list[str]:
    """Return canonical region names. If `country` is given (canonical
    form from `lookup_country`), filter to regions in that country."""
    if country is None:
        return [r["name"] for r in _CONN.execute("SELECT name FROM regions ORDER BY name")]
    crow = _resolve_country(country)
    if not crow:
        return []
    return [
        r["name"]
        for r in _CONN.execute(
            "SELECT name FROM regions WHERE country_id = ? ORDER BY name",
            (crow["id"],),
        )
    ]


@mcp.tool()
def list_grapes(country: Optional[str] = None, region: Optional[str] = None) -> list[str]:
    """Return canonical grape names. If `region` is provided, filter
    to grapes recorded as grown there (via `region_grapes`). If only
    `country` is provided, filter to grapes whose origin matches."""
    if region:
        rrow = _resolve_region(region)
        if not rrow:
            return []
        return [
            r["canonical_name"]
            for r in _CONN.execute(
                """SELECT g.canonical_name
                     FROM grapes g
                     JOIN region_grapes rg ON rg.grape_id = g.id
                    WHERE rg.region_id = ?
                    ORDER BY g.canonical_name""",
                (rrow["id"],),
            )
        ]
    if country:
        crow = _resolve_country(country)
        if not crow:
            return []
        return [
            r["canonical_name"]
            for r in _CONN.execute(
                """SELECT canonical_name FROM grapes
                    WHERE origin_country_id = ? ORDER BY canonical_name""",
                (crow["id"],),
            )
        ]
    return [
        r["canonical_name"]
        for r in _CONN.execute("SELECT canonical_name FROM grapes ORDER BY canonical_name")
    ]


# ---------- terminal tool: submit_tags ----------

_HINTS = {
    "placeholder_grapes": (
        "Generic phrases like 'Bordeaux Blend' or 'unknown' are not grapes. "
        "Submit the actual varieties; if truly unknown, leave grapes=[]."
    ),
    "no_grapes": (
        "Grape list is empty. If the source genuinely doesn't name grapes, "
        "submit anyway -- the row will route to needs_review."
    ),
    "non_canonical_grape": (
        "One or more grape names aren't in the canonical list. Call "
        "lookup_grape on each to find the canonical spelling, or list_grapes "
        "to browse."
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


@mcp.tool()
def submit_tags(
    country: Optional[str],
    region: list[str],
    grapes: list[str],
    is_blend: Optional[bool],
    organic: Optional[bool],
    confidence: Optional[int],
) -> dict:
    """Canonicalise and validate a proposed tag set.

    On success returns {ok: True, normalized: {...}} with canonical
    expanded values. On failure returns {ok: False, issues: [...],
    hints: {...}}.
    """
    region = list(region or [])
    grapes = list(grapes or [])
    issues: list[str] = []

    # --- country ---
    country_row = _resolve_country(country) if country else None
    canonical_country = country_row["name"] if country_row else (country or None)

    # --- regions ---
    normalized_regions: list[str] = []
    region_countries: set[str] = set()
    for r in region:
        if not r:
            continue
        if _resolve_country(r) and not _resolve_region(r):
            if "country_in_region_slot" not in issues:
                issues.append("country_in_region_slot")
            continue
        rrow = _resolve_region(r)
        if rrow:
            normalized_regions.append(rrow["name"])
            _, rc = _region_parents(rrow["id"])
            if rc:
                region_countries.add(rc)
        else:
            normalized_regions.append(r)

    if canonical_country and region_countries:
        if canonical_country not in region_countries:
            issues.append("region_country_mismatch")

    # --- grapes ---
    normalized_grapes: list[str] = []
    placeholder_seen = False
    non_canonical: list[str] = []
    for g in grapes:
        if not g:
            continue
        if _is_placeholder_grape(g):
            placeholder_seen = True
            continue
        grow = _resolve_grape(g)
        if grow:
            if grow["canonical_name"] not in normalized_grapes:
                normalized_grapes.append(grow["canonical_name"])
        else:
            non_canonical.append(g)

    if placeholder_seen:
        issues.append("placeholder_grapes")
    if non_canonical:
        issues.append("non_canonical_grape")
    if not normalized_grapes and not placeholder_seen and not non_canonical:
        issues.append("no_grapes")

    # --- is_blend ---
    if is_blend is not None and normalized_grapes:
        expected = len(normalized_grapes) >= 2
        if bool(is_blend) != expected:
            issues.append("is_blend_mismatch")

    if issues:
        hints = {code: _HINTS[code] for code in issues if code in _HINTS}
        if "non_canonical_grape" in hints and non_canonical:
            hints["non_canonical_grape"] = (
                f"These grape names aren't in the canonical list: {non_canonical}. "
                "Call lookup_grape on each, or list_grapes to browse."
            )
        return {"ok": False, "issues": issues, "hints": hints}

    return {
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
        },
    }


if __name__ == "__main__":
    mcp.run()  # stdio transport
