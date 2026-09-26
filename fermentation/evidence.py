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
the single-source rule gates on.
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


def unsupported_grapes(grapes: list[str], web_context: str) -> list[str]:
    """Return the submitted grapes that appear nowhere in `web_context`,
    neither by canonical name nor by any library synonym."""
    hay = _fold(web_context)
    aliases = _grape_aliases()
    missing: list[str] = []
    for grape in grapes:
        key = _fold(grape)
        names = aliases.get(key) or (key,)
        if not any(_mentioned(a, hay) for a in names):
            missing.append(grape)
    return missing


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
