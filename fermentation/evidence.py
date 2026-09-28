"""Mechanical evidence checks on the tagger's output.

The tagger prompt says grapes must be named by a snippet and that confidence
is capped at 84 when only one snippet contributed. On the 2026-09-15 run the
model broke both rules (Bila Haut: three grapes at 89 from one snippet that
named none of them; Aster: Tempranillo from a context with no grape at all).
These helpers let `phases.decide_tag_status` enforce them in code.

Grape matching uses the library's own names and synonyms (Garnacha ≈
Grenache, Tinta Roriz ≈ Tempranillo), read once from library.db. If the
library is not built the check degrades to the canonical name only.

`context_source_count` answers the other half of the question — how many
*distinct sites* the context rests on, not how many snippets — which is what
the single-source rule gates on. `grape_source_counts` asks the same per
grape: on the 2026-09-27 run every wrong grape set but one rested on a grape
that a single source named (Curator's Sémillon, Bila Haut's Mourvèdre).

`finer_regions_named` catches the other common miss on that run: the context
names Barolo but the model submitted Piedmont. It walks the library's region
tree, read once from library.db like the grape synonyms.
"""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from functools import lru_cache
from pathlib import Path

from .scorer import source_family

LIBRARY_DB = Path(__file__).resolve().parent / "library_mcp" / "library.db"

# Captures the source label so the same parse serves both counts below.
_CONTEXT_HEADER_RE = re.compile(r"^\[(.+?) \| match=\d+\]$", re.MULTILINE)

# Library synonyms that are ordinary wine words, not evidence of a grape:
# "Tinto" is listed for Tempranillo and would match "Chocapalha Tinto".
_GENERIC_SYNONYMS = {
    "tinto", "tinta", "tinta fina", "blanco", "bianco", "branco", "rosso", "negro", "nero",
    "melon", "ideal", "nature", "gordo", "gras", "giro", "fer", "cot", "cab",
}
_MIN_SYNONYM_LEN = 5


def _fold(text: str) -> str:
    """Lowercase, strip diacritics, collapse whitespace — same idea as the
    library server's `_fold`, so a synonym matches the way the server would."""
    nfkd = unicodedata.normalize("NFKD", text or "")
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", stripped).strip().lower()


@lru_cache(maxsize=1)
def _grape_aliases() -> dict[str, tuple[str, ...]]:
    """canonical folded name -> every folded name/synonym that means that grape."""
    aliases: dict[str, set[str]] = {}
    if not LIBRARY_DB.exists():
        return {}
    try:
        conn = sqlite3.connect(f"file:{LIBRARY_DB}?mode=ro", uri=True)
    except sqlite3.Error:
        return {}
    try:
        by_id: dict[int, str] = {}
        for gid, name in conn.execute("SELECT id, canonical_name FROM grapes"):
            key = _fold(name)
            by_id[gid] = key
            aliases.setdefault(key, set()).add(key)
        for gid, syn in conn.execute("SELECT grape_id, synonym FROM grape_synonyms"):
            key = by_id.get(gid)
            folded = _fold(syn)
            if key and len(folded) >= _MIN_SYNONYM_LEN and folded not in _GENERIC_SYNONYMS:
                aliases[key].add(folded)
    except sqlite3.Error:
        return {}
    finally:
        conn.close()
    return {k: tuple(sorted(v, key=len, reverse=True)) for k, v in aliases.items()}


def _mentioned(alias: str, haystack: str) -> bool:
    """Whole-word match of a folded alias inside folded text. Short aliases
    (< 4 chars, e.g. "pn") are too easy to hit by accident and are ignored."""
    if len(alias) < 4:
        return False
    return re.search(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])", haystack) is not None


def _context_blocks(web_context: str) -> list[tuple[str, str]]:
    """(source family, folded body) for each `[label | match=N]` block. Text
    before the first header, or a context with no headers, counts as one
    block from an unnamed source."""
    parts = _CONTEXT_HEADER_RE.split(web_context or "")
    blocks = [("", _fold(parts[0]))] if parts[0].strip() else []
    for label, body in zip(parts[1::2], parts[2::2]):
        blocks.append((source_family(label), _fold(body)))
    return blocks


def grape_source_counts(grapes: list[str], web_context: str) -> dict[str, int]:
    """For each submitted grape, the number of distinct sources in
    `web_context` whose text names it, by canonical name or library synonym."""
    blocks = _context_blocks(web_context)
    aliases = _grape_aliases()
    counts: dict[str, int] = {}
    for grape in grapes:
        key = _fold(grape)
        names = aliases.get(key) or (key,)
        counts[grape] = len({fam for fam, body in blocks if any(_mentioned(a, body) for a in names)})
    return counts


def unsupported_grapes(grapes: list[str], web_context: str) -> list[str]:
    """Return the submitted grapes that appear nowhere in `web_context`,
    neither by canonical name nor by any library synonym."""
    counts = grape_source_counts(grapes, web_context)
    return [g for g in grapes if counts[g] == 0]


@lru_cache(maxsize=1)
def _region_tree() -> tuple[dict[str, list[int]], dict[int, tuple[str, str, bool, tuple[str, ...]]], dict[int, list[int]]]:
    """(canonical name -> ids, id -> (name, country, canonical, folded aliases),
    parent id -> child ids). Empty when library.db is missing."""
    by_name: dict[str, list[int]] = {}
    nodes: dict[int, tuple[str, str, bool, tuple[str, ...]]] = {}
    children: dict[int, list[int]] = {}
    if not LIBRARY_DB.exists():
        return by_name, nodes, children
    try:
        conn = sqlite3.connect(f"file:{LIBRARY_DB}?mode=ro", uri=True)
    except sqlite3.Error:
        return by_name, nodes, children
    try:
        synonyms: dict[int, list[str]] = {}
        for rid, syn in conn.execute("SELECT region_id, synonym FROM region_synonyms"):
            folded = _fold(syn)
            if len(folded) >= _MIN_SYNONYM_LEN:
                synonyms.setdefault(rid, []).append(folded)
        rows = conn.execute(
            "SELECT r.id, r.name, r.parent_region_id, r.is_canonical, c.name "
            "FROM regions r LEFT JOIN countries c ON c.id = r.country_id"
        )
        for rid, name, parent, canonical, country in rows:
            nodes[rid] = (name, country or "", bool(canonical), (_fold(name), *synonyms.get(rid, ())))
            if canonical:
                by_name.setdefault(name, []).append(rid)
            if parent is not None:
                children.setdefault(parent, []).append(rid)
    except sqlite3.Error:
        return {}, {}, {}
    finally:
        conn.close()
    return by_name, nodes, children


def _words(folded: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", folded)


def _phrase_re(words: list[str]) -> re.Pattern:
    """Whole-word match of a word sequence, whatever separates the words
    ("Côtes-du-Roussillon" and "Cotes du Roussillon" both match)."""
    return re.compile(r"(?<![a-z0-9])" + r"[^a-z0-9]+".join(map(re.escape, words)) + r"(?![a-z0-9])")


# A winery's address is not the wine's appellation: "Bodegas Faustino, located
# in Oyon, Rioja Alavesa" (the wine is DOCa Rioja), "38 km from Baalbek".
_LOCATION_CUE_RE = re.compile(
    r"(?:\b(?:located|based|situated|headquartered|near)\b[^.;]{0,25}"
    r"|\b(?:km|kilometers|kilometres|miles) from\s*)$"
)


def _named_as_origin(alias: str, hay: str, name_words: list[str]) -> bool:
    """True when `alias` occurs in `hay` as where the wine comes from.

    A mention inside a longer phrase taken from the product name does not
    count: "La Rioja Alta Ardanza" makes "la rioja alta" such a phrase, so the
    producer's name is not a mention of the Rioja Alta sub-zone, while
    "Vajra Barolo Albe" still lets "from Barolo, Piedmont" count. Nor does a
    mention right after a location cue (_LOCATION_CUE_RE)."""
    words = _words(alias)
    if len(alias) < 4 or not words:
        return False
    k = len(words)
    for n in range(len(name_words), k, -1):
        for i in range(len(name_words) - n + 1):
            gram = name_words[i:i + n]
            if any(gram[j:j + k] == words for j in range(n - k + 1)):
                hay = _phrase_re(gram).sub(" ", hay)
    return any(
        not _LOCATION_CUE_RE.search(hay[max(0, m.start() - 40):m.start()])
        for m in _phrase_re(words).finditer(hay)
    )


def finer_regions_named(
    regions: list[str], web_context: str, *, country: str | None = None, product_name: str = "",
) -> list[str]:
    """Canonical regions that `web_context` names and that sit below the most
    specific submitted region: Barolo when the model submitted Piedmont.

    `regions` is the normalized list, parents included, so the most specific
    entries are the ones that are no other entry's parent. `country` narrows
    same-named regions to the submitted country.
    """
    by_name, nodes, children = _region_tree()
    ids = [
        rid for r in regions for rid in by_name.get(r, [])
        if not country or nodes[rid][1] == country
    ]
    if not ids:
        return []
    submitted = set(ids)
    parents = {p for p, kids in children.items() for k in kids if k in submitted}
    hay = _fold(web_context)
    name_words = _words(_fold(product_name))
    found: list[str] = []
    for leaf in (rid for rid in ids if rid not in parents):
        stack = list(children.get(leaf, []))
        while stack:
            rid = stack.pop()
            stack.extend(children.get(rid, []))
            name, _country, canonical, aliases = nodes[rid]
            if not canonical or rid in submitted or name in found:
                continue
            if any(_named_as_origin(a, hay, name_words) for a in aliases):
                found.append(name)
    return found


def context_snippet_count(web_context: str) -> int:
    """Number of `[source | match=N]` blocks the scorer pasted into the context."""
    return len(_CONTEXT_HEADER_RE.findall(web_context or ""))


def context_source_count(web_context: str) -> int:
    """Number of *distinct sources* behind those blocks.

    `_pick_diverse` only enforces source diversity while filling the first
    slots; its final pass tops the context up from any survivor, so five
    Wine-Searcher results are five snippets but one source. Confidence rules
    care about corroboration, which is what this counts.
    """
    labels = _CONTEXT_HEADER_RE.findall(web_context or "")
    return len({source_family(label) for label in labels})
