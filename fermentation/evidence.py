"""Mechanical evidence checks on the tagger's output.

The tagger prompt says grapes must be named by a snippet and that confidence
is capped at 84 when only one snippet contributed. On the 2026-09-15 run the
model broke both rules (Bila Haut: three grapes at 89 from one snippet that
named none of them; Aster: Tempranillo from a context with no grape at all).
These helpers let `phases.decide_tag_status` enforce them in code.

Grape matching uses the library's own names and synonyms (Garnacha ≈
Grenache, Tinta Roriz ≈ Tempranillo), read once from library.db by
`library_text`, which the scorer shares to see what a snippet names. If the
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

from .constants import ROSE_FROM_PINK_SKINNED, WHITE_GRAPES_ONLY_CATEGORIES
from .library_text import LIBRARY_DB, fold, grape_aliases, grape_colours, mentioned, region_tree  # noqa: F401 (LIBRARY_DB: tests skip on it)
from .scorer import source_family

# Captures the source label so the same parse serves both counts below.
_CONTEXT_HEADER_RE = re.compile(r"^\[(.+?) \| match=\d+\]$", re.MULTILINE)


def _context_blocks(web_context: str) -> list[tuple[str, str]]:
    """(source family, folded body) for each `[label | match=N]` block. Text
    before the first header, or a context with no headers, counts as one
    block from an unnamed source."""
    parts = _CONTEXT_HEADER_RE.split(web_context or "")
    blocks = [("", fold(parts[0]))] if parts[0].strip() else []
    for label, body in zip(parts[1::2], parts[2::2]):
        blocks.append((source_family(label), fold(body)))
    return blocks


def grape_source_counts(grapes: list[str], web_context: str) -> dict[str, int]:
    """For each submitted grape, the number of distinct sources in
    `web_context` whose text names it, by canonical name or library synonym."""
    blocks = _context_blocks(web_context)
    aliases = grape_aliases()
    counts: dict[str, int] = {}
    for grape in grapes:
        key = fold(grape)
        names = aliases.get(key) or (key,)
        counts[grape] = len({fam for fam, body in blocks if any(mentioned(a, body) for a in names)})
    return counts


def unsupported_grapes(grapes: list[str], web_context: str) -> list[str]:
    """Return the submitted grapes that appear nowhere in `web_context`,
    neither by canonical name nor by any library synonym."""
    counts = grape_source_counts(grapes, web_context)
    return [g for g in grapes if counts[g] == 0]


def white_grapes_only(grapes: list[str], category: str | None) -> bool:
    """True when a red or rosé wine's grapes are all ones the library files as
    white. A grape with no colour on record counts as not white, so the check
    fires only when every grape is a known white."""
    cat = fold(category or "")
    if cat not in WHITE_GRAPES_ONLY_CATEGORIES or not grapes:
        return False
    colours = grape_colours()
    pink = {fold(g) for g in ROSE_FROM_PINK_SKINNED} if cat == "rose" else set()
    return all(colours.get(fold(g)) == "white" and fold(g) not in pink for g in grapes)


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
    by_name, nodes, children = region_tree()
    ids = [
        rid for r in regions for rid in by_name.get(r, [])
        if not country or nodes[rid][1] == country
    ]
    if not ids:
        return []
    submitted = set(ids)
    parents = {p for p, kids in children.items() for k in kids if k in submitted}
    hay = fold(web_context)
    name_words = _words(fold(product_name))
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
