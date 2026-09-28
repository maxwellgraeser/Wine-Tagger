"""Library grape and region names, and finding them in snippet text.

Shared by `evidence` (checks on the tagger's output) and `scorer` (which
snippets go into the context). It lives apart from both because `evidence`
imports `scorer.source_family`, so `scorer` cannot import `evidence`.

Names come from library.db, read once. If the library is not built the
loaders return empty maps and callers degrade (evidence to canonical grape
names only, `text_facts` to nothing found).
"""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from functools import lru_cache
from pathlib import Path

LIBRARY_DB = Path(__file__).resolve().parent / "library_mcp" / "library.db"

# Library synonyms that are ordinary wine words, not evidence of a grape:
# "Tinto" is listed for Tempranillo and would match "Chocapalha Tinto".
_GENERIC_SYNONYMS = {
    "tinto", "tinta", "tinta fina", "blanco", "bianco", "branco", "rosso", "negro", "nero",
    "melon", "ideal", "nature", "gordo", "gras", "giro", "fer", "cot", "cab",
}
_MIN_SYNONYM_LEN = 5

# Region names that are ordinary words in tasting notes ("Mediterranean
# herbs"), not a place the wine is from. Uruguay's Central and Turkey's
# Mediterranean regions are never named this way in a snippet.
_GENERIC_REGION_NAMES = {"central", "mediterranean"}

# Grape names and synonyms that are ordinary words in shop and review text,
# skipped by `text_facts` only. On the 2026-09 logs "Italia" matched Vivino's
# Italian blurb ("Piemonte, northern Italy, Italia") and País matched "mission
# fig" in a tasting note. The rest are the same kind of word: "debit" on a
# checkout line, "Vega" Sicilia, "calabrese" (Calabrian) on a Cirò page.
_NOT_GRAPE_WORDS = {
    "italia", "mission", "debit", "president", "diamond", "cardinal", "emperor", "regent",
    "symphony", "coronation", "singleton", "vital", "vega", "bacchus", "calabrese",
    "concord", "delaware", "rome", "orleans",
}

# Aliases shorter than this are too easy to hit by accident ("pn", "ay").
_MIN_MATCH_LEN = 4


def fold(text: str) -> str:
    """Lowercase, strip diacritics, collapse whitespace — same idea as the
    library server's `_fold`, so a synonym matches the way the server would."""
    nfkd = unicodedata.normalize("NFKD", text or "")
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", stripped).strip().lower()


def _connect() -> sqlite3.Connection | None:
    if not LIBRARY_DB.exists():
        return None
    try:
        return sqlite3.connect(f"file:{LIBRARY_DB}?mode=ro", uri=True)
    except sqlite3.Error:
        return None


@lru_cache(maxsize=1)
def _grapes() -> tuple[dict[str, tuple[str, ...]], dict[str, str]]:
    """(canonical folded name -> every folded name/synonym that means that
    grape, canonical folded name -> canonical name as the library spells it)."""
    aliases: dict[str, set[str]] = {}
    display: dict[str, str] = {}
    conn = _connect()
    if conn is None:
        return {}, {}
    try:
        by_id: dict[int, str] = {}
        for gid, name in conn.execute("SELECT id, canonical_name FROM grapes"):
            key = fold(name)
            by_id[gid] = key
            display[key] = name
            aliases.setdefault(key, set()).add(key)
        for gid, syn in conn.execute("SELECT grape_id, synonym FROM grape_synonyms"):
            key = by_id.get(gid)
            folded = fold(syn)
            if key and len(folded) >= _MIN_SYNONYM_LEN and folded not in _GENERIC_SYNONYMS:
                aliases[key].add(folded)
    except sqlite3.Error:
        return {}, {}
    finally:
        conn.close()
    return {k: tuple(sorted(v, key=len, reverse=True)) for k, v in aliases.items()}, display


def grape_aliases() -> dict[str, tuple[str, ...]]:
    """canonical folded name -> every folded name/synonym that means that grape."""
    return _grapes()[0]


@lru_cache(maxsize=1)
def grape_colours() -> dict[str, str]:
    """canonical folded name -> colour as the library records it (red, white,
    rose, gris). Grapes with no colour are left out."""
    conn = _connect()
    if conn is None:
        return {}
    try:
        return {
            fold(name): color
            for name, color in conn.execute("SELECT canonical_name, color FROM grapes")
            if color
        }
    except sqlite3.Error:
        return {}
    finally:
        conn.close()


def mentioned(alias: str, haystack: str) -> bool:
    """Whole-word match of a folded alias inside folded text. Short aliases
    (< 4 chars, e.g. "pn") are too easy to hit by accident and are ignored."""
    if len(alias) < _MIN_MATCH_LEN:
        return False
    return re.search(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])", haystack) is not None


RegionNode = tuple[str, str, bool, tuple[str, ...]]


@lru_cache(maxsize=1)
def region_tree() -> tuple[dict[str, list[int]], dict[int, RegionNode], dict[int, list[int]]]:
    """(canonical name -> ids, id -> (name, country, canonical, folded aliases),
    parent id -> child ids). Empty when library.db is missing."""
    by_name: dict[str, list[int]] = {}
    nodes: dict[int, RegionNode] = {}
    children: dict[int, list[int]] = {}
    conn = _connect()
    if conn is None:
        return by_name, nodes, children
    try:
        synonyms: dict[int, list[str]] = {}
        for rid, syn in conn.execute("SELECT region_id, synonym FROM region_synonyms"):
            folded = fold(syn)
            if len(folded) >= _MIN_SYNONYM_LEN:
                synonyms.setdefault(rid, []).append(folded)
        rows = conn.execute(
            "SELECT r.id, r.name, r.parent_region_id, r.is_canonical, c.name "
            "FROM regions r LEFT JOIN countries c ON c.id = r.country_id"
        )
        for rid, name, parent, canonical, country in rows:
            nodes[rid] = (name, country or "", bool(canonical), (fold(name), *synonyms.get(rid, ())))
            if canonical:
                by_name.setdefault(name, []).append(rid)
            if parent is not None:
                children.setdefault(parent, []).append(rid)
    except sqlite3.Error:
        return {}, {}, {}
    finally:
        conn.close()
    return by_name, nodes, children


# ---------------------------------------------------------------------------
# Names found in a snippet
# ---------------------------------------------------------------------------

_WORD_RE = re.compile(r"[a-z0-9]+")
# What may sit between the words of one name: "Côtes-du-Roussillon",
# "Barbera d'Asti", "St. Emilion". A comma ends the name, so "Cabernet,
# Sauvignon Blanc" on a list page is not Cabernet Sauvignon.
_JOINER_RE = re.compile(r"[ \-'’.]+")

# first word -> [(words, is_region, display name)], longest first; at equal
# length a region comes before a grape.
_Index = dict[str, list[tuple[tuple[str, ...], bool, str]]]


@lru_cache(maxsize=1)
def _name_index() -> _Index:
    aliases, display = _grapes()
    _by_name, nodes, _children = region_tree()
    entries: set[tuple[tuple[str, ...], bool, str]] = set()
    for name, _country, _canonical, folded_aliases in nodes.values():
        for alias in folded_aliases:
            if len(alias) >= _MIN_MATCH_LEN and alias not in _GENERIC_REGION_NAMES:
                entries.add((tuple(_WORD_RE.findall(alias)), True, name))
    for key, names in aliases.items():
        for alias in names:
            if len(alias) >= _MIN_MATCH_LEN and alias not in _NOT_GRAPE_WORDS:
                entries.add((tuple(_WORD_RE.findall(alias)), False, display.get(key, key)))
    index: _Index = {}
    for entry in entries:
        if entry[0]:
            index.setdefault(entry[0][0], []).append(entry)
    for candidates in index.values():
        candidates.sort(key=lambda e: (-len(e[0]), not e[1], e[2]))
    return index


def text_facts(body: str) -> dict[str, list[str]]:
    """The library grapes and regions a snippet's text names, as
    `{"grapes": [...], "regions": [...]}` in order of first mention.

    Read left to right, the longest name starting at each word wins and its
    words are used up, so "Cabernet Sauvignon" is one grape (not also
    Sauvignon Blanc) and "Picpoul de Pinet" is a region, not the grape. When
    a region and a grape are spelled the same ("Txakoli", "Brunello") the
    region wins: a place name alone does not say which grapes went in.
    """
    index = _name_index()
    folded = fold(body)
    words = list(_WORD_RE.finditer(folded))
    grapes: list[str] = []
    regions: list[str] = []
    i = 0
    while i < len(words):
        match = None
        for names, is_region, name in index.get(words[i].group(), ()):
            end = i + len(names)
            if end > len(words):
                continue
            if all(words[i + j].group() == names[j] for j in range(1, len(names))) and all(
                _JOINER_RE.fullmatch(folded[words[j].end():words[j + 1].start()])
                for j in range(i, end - 1)
            ):
                match = (end, is_region, name)
                break
        if match is None:
            i += 1
            continue
        end, is_region, name = match
        found = regions if is_region else grapes
        if name not in found:
            found.append(name)
        i = end
    return {"grapes": grapes, "regions": regions}

