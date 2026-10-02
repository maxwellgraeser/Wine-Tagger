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

`blend_named_whole` is the exception to that per-grape count: one snippet that
names a whole blend ("45% Tinta Roriz, 25% Touriga Nacional, 15% Castelão…")
is the composition as a source states it, and a second site rarely lists the
minor grapes too.

`finer_regions_named` catches the other common miss on that run: the context
names Barolo but the model submitted Piedmont. `longer_regions_named` catches
its sibling: the context says Côte de Brouilly and the model looked up the
product name's "Brouilly". Both walk the library's region tree, read once
from library.db like the grape synonyms, and both count sources, so a single
mention in a list of the producer's other wines does not outweigh the region
the rest of the context names.

`unsupported_regions` is the region-side twin of `unsupported_grapes`: a
submitted region that nothing in the text names, nor anything below it.
"""

from __future__ import annotations

import re
from functools import lru_cache

from .constants import FINER_REGION_MIN_SOURCES, ROSE_FROM_PINK_SKINNED, WHITE_GRAPES_ONLY_CATEGORIES
from .library_text import (  # noqa: F401 (LIBRARY_DB: tests skip on it)
    LIBRARY_DB, fold, grape_aliases, grape_colours, mentioned, region_tree, text_facts,
)
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


# A share next to a grape name: "86% Cabernet Sauvignon", "Merlot 8%",
# "Grenache (60%)", "20% of Garnacha".
_SHARE = r"\d{1,3}(?:[.,]\d+)?\s?%"


def _has_share(grape: str, body: str) -> bool:
    """True when the folded `body` gives `grape`, by any library name, a percentage."""
    for alias in grape_aliases().get(fold(grape)) or (fold(grape),):
        name = re.escape(alias)
        if re.search(_SHARE + r"\s*(?:of\s+)?" + name + r"(?![a-z0-9])", body) or re.search(
                r"(?<![a-z0-9])" + name + r"\s*[:(]?\s*" + _SHARE, body):
            return True
    return False


# A list that says it is not the whole blend: "Grenache, Carignan, and touches
# of a couple other grapes", "…among others".
_PARTIAL_LIST_RE = re.compile(
    r"\b(?:and|with|plus)\s+(?:touches|a touch|a few|some|a couple|a little|small amounts?|other)\b"
    r"[^.]{0,40}?\b(?:grapes|varieties|varietals)\b|\bamong others\b"
)


def blend_named_whole(grapes: list[str], web_context: str) -> bool:
    """True when one snippet names every grape of a blend (two or more), as
    that wine's composition: it names no other grape, or it gives each of
    these a share.

    The share test lets La Rioja Alta's "20% Grenache / Garnacha 5% Mazuelo
    75% Tempranillo" (an older vintage) back Tempranillo and Grenache. Without
    it, a region blurb that lists the local grapes would back any three of
    them: Bila Haut's "Cabernet, Merlot, Mourvedre, Grenache, and Syrah are
    some of the most important red grapes in the region".

    A snippet that says its list is partial (_PARTIAL_LIST_RE) never names a
    whole blend: Bila Haut's "Grenache, Carignan, and touches of a couple other
    grapes" passed on 2026-10-01 with its Syrah missing."""
    if len(grapes) < 2:
        return False
    want = {fold(g) for g in grapes}
    for _family, body in _context_blocks(web_context):
        if _PARTIAL_LIST_RE.search(body):
            continue
        named = {fold(g) for g in text_facts(body)["grapes"]}
        if want <= named and (named == want or all(_has_share(g, body) for g in grapes)):
            return True
    return False


_BLEND_WORD_RE = re.compile(r"\b(?:blend|blended|assemblage)\b")


def context_calls_it_a_blend(web_context: str) -> bool:
    """True when any snippet uses the word blend (or assemblage). Crude on
    purpose: it is the guard on the single-grape exemption from
    uncorroborated_grape, so a false hit only keeps today's stricter check.
    Chocapalha's "a blend of indigenous Portuguese varietals" (2026-09-27,
    submitted as Touriga Nacional alone) is the row it keeps in review."""
    return _BLEND_WORD_RE.search(fold(web_context or "")) is not None


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
    mention right after a location cue (_LOCATION_CUE_RE).

    A region that ends the product name is left unmasked: a POS name that
    ends in a region is producer + appellation ("Neirano Barolo", "Faustino
    VII Rioja"), and the snippets name the wine that way ("Tenute Neirano
    Barolo"). Masking it hid Barolo from the 2026-10-01 Neirano check."""
    words = _words(alias)
    if len(alias) < 4 or not words:
        return False
    k = len(words)
    ends_name = len(name_words) > k and name_words[-k:] == words
    for n in range(len(name_words) if not ends_name else 0, k, -1):
        for i in range(len(name_words) - n + 1):
            gram = name_words[i:i + n]
            if any(gram[j:j + k] == words for j in range(n - k + 1)):
                hay = _phrase_re(gram).sub(" ", hay)
    return any(
        not _LOCATION_CUE_RE.search(hay[max(0, m.start() - 40):m.start()])
        for m in _phrase_re(words).finditer(hay)
    )


def _source_count(aliases, blocks: list[tuple[str, str]], name_words: list[str]) -> int:
    """Distinct sources whose block names one of `aliases` as the wine's origin."""
    return len({fam for fam, body in blocks if any(_named_as_origin(a, body, name_words) for a in aliases)})


def _outweighs(n: int, submitted_n: int) -> bool:
    """A region `n` sources name counts against one `submitted_n` sources name."""
    return n > 0 and (n >= FINER_REGION_MIN_SOURCES or n >= submitted_n)


def _submitted_leaves(regions: list[str], country: str | None) -> tuple[set[int], list[int]]:
    """(ids of every submitted region, ids of the most specific ones).
    `regions` is the normalized list, parents included, so the most specific
    entries are the ones that are no other entry's parent. `country` narrows
    same-named regions to the submitted country."""
    by_name, nodes, children = region_tree()
    ids = [rid for r in regions for rid in by_name.get(r, []) if not country or nodes[rid][1] == country]
    submitted = set(ids)
    parents = {p for p, kids in children.items() for k in kids if k in submitted}
    return submitted, [rid for rid in ids if rid not in parents]


def _descendants(rid: int, children: dict[int, list[int]]) -> list[int]:
    out: list[int] = []
    stack = list(children.get(rid, []))
    while stack:
        kid = stack.pop()
        out.append(kid)
        stack.extend(children.get(kid, []))
    return out


def finer_regions_named(
    regions: list[str], web_context: str, *, country: str | None = None, product_name: str = "",
) -> list[str]:
    """Canonical regions that `web_context` names and that sit below the most
    specific submitted region: Barolo when the model submitted Piedmont.

    A finer region counts when FINER_REGION_MIN_SOURCES sources name it, or
    at least as many as name the submitted region (see `_outweighs`).
    """
    _by_name, nodes, children = region_tree()
    submitted, leaves = _submitted_leaves(regions, country)
    blocks = _context_blocks(web_context)
    name_words = _words(fold(product_name))
    found: list[str] = []
    for leaf in leaves:
        leaf_n = _source_count(nodes[leaf][3], blocks, name_words)
        for rid in _descendants(leaf, children):
            name, _country, canonical, aliases = nodes[rid]
            if not canonical or rid in submitted or name in found:
                continue
            if _outweighs(_source_count(aliases, blocks, name_words), leaf_n):
                found.append(name)
    return found


def _contains(longer: list[str], shorter: list[str]) -> bool:
    k = len(shorter)
    return len(longer) > k and any(longer[i:i + k] == shorter for i in range(len(longer) - k + 1))


def longer_regions_named(
    regions: list[str], web_context: str, *, country: str | None = None, product_name: str = "",
) -> list[str]:
    """Canonical regions that `web_context` names whose name contains the
    submitted region's, and that are neither above nor below it: Côte de
    Brouilly when the model submitted Brouilly, Côtes du Roussillon Villages
    for Côtes du Roussillon. The model tends to look up the product name's
    word. Counted like `finer_regions_named`, against the sources that name
    the submitted region on its own, outside the longer name."""
    _by_name, nodes, children = region_tree()
    parent_of = {kid: p for p, kids in children.items() for kid in kids}
    _submitted, leaves = _submitted_leaves(regions, country)
    blocks = _context_blocks(web_context)
    name_words = _words(fold(product_name))
    found: list[str] = []
    for leaf in leaves:
        leaf_name, leaf_country, _canonical, leaf_aliases = nodes[leaf]
        related = {leaf, *_descendants(leaf, children)}
        rid = leaf
        while rid in parent_of:
            rid = parent_of[rid]
            related.add(rid)
        leaf_words = [_words(a) for a in leaf_aliases]
        for rid, (name, rcountry, canonical, aliases) in nodes.items():
            if (not canonical or rcountry != leaf_country or rid in related or name in found
                    or not any(_contains(_words(a), w) for a in aliases for w in leaf_words)):
                continue
            n = _source_count(aliases, blocks, name_words)
            if not n:
                continue
            masked = [(fam, _mask(body, aliases)) for fam, body in blocks]
            if _outweighs(n, _source_count(leaf_aliases, masked, name_words)):
                found.append(name)
    return found


def _mask(body: str, aliases) -> str:
    for alias in aliases:
        body = _phrase_re(_words(alias)).sub(" ", body)
    return body


def unsupported_regions(
    regions: list[str], web_context: str, *, country: str | None = None, product_name: str = "",
) -> list[str]:
    """The most specific submitted regions that neither the context nor the
    product name names, by any library spelling (Piemonte for Piedmont), and
    that have no region below them named either (Barolo backs Piedmont).

    The region-side twin of `unsupported_grapes`: it catches a region taken
    from the library rather than the text, such as a sub-region picked off a
    `lookup_sub_regions` list that no snippet mentions. Any mention counts,
    a winery's address included: this asks whether the text names the place
    at all, not whether it is the wine's origin."""
    _by_name, nodes, children = region_tree()
    _submitted, leaves = _submitted_leaves(regions, country)
    hay = fold(f"{product_name}\n{web_context}")
    found: list[str] = []
    for leaf in leaves:
        aliases = [a for rid in (leaf, *_descendants(leaf, children)) for a in nodes[rid][3]
                   if len(a) >= 4 and _words(a)]
        name = nodes[leaf][0]
        if aliases and name not in found and not any(_phrase_re(_words(a)).search(hay) for a in aliases):
            found.append(name)
    return found


@lru_cache(maxsize=1)
def _parent_of() -> dict[int, int]:
    _by_name, _nodes, children = region_tree()
    return {kid: p for p, kids in children.items() for kid in kids}


def _ancestors(rid: int) -> list[int]:
    parent_of = _parent_of()
    out: list[int] = []
    while rid in parent_of:
        rid = parent_of[rid]
        out.append(rid)
    return out


def _chain_names(rid: int) -> list[str]:
    """The region and its parents, most specific first: the normalized form."""
    _by_name, nodes, _children = region_tree()
    return [nodes[r][0] for r in (rid, *_ancestors(rid))]


def _region_id(name: str, country: str | None) -> int | None:
    by_name, nodes, _children = region_tree()
    ids = [rid for rid in by_name.get(name, []) if not country or nodes[rid][1] == country]
    return ids[0] if len(ids) == 1 else None


@lru_cache(maxsize=512)
def name_region(product_name: str) -> int | None:
    """The canonical region the product name names ("Neirano Barolo" →
    Barolo), or None.

    Every region the name matches must sit on one branch of the tree, and the
    most specific is returned. A name that matches regions on two branches is
    left alone: "La Rioja Alta Ardanza" names Rioja Alta and Argentina's La
    Rioja, because the producer's name is a place name. Note the POS name can
    still be wrong in its own way: "Pav Chavannes Brouilly" is a Côte de
    Brouilly (see `region_from_name`)."""
    _by_name, nodes, _children = region_tree()
    hay = fold(product_name)
    hits = [rid for rid, (_n, _c, canonical, aliases) in nodes.items()
            if canonical and any(mentioned(a, hay) for a in aliases)]
    if not hits:
        return None
    deepest = max(hits, key=lambda rid: len(_ancestors(rid)))
    on_branch = {deepest, *_ancestors(deepest)}
    return deepest if all(rid in on_branch for rid in hits) else None


def region_from_name(
    regions: list[str], *, country: str | None, product_name: str,
) -> tuple[str | None, str | None]:
    """Compare the submitted region with the one the product name names.

    Returns ("upgrade", name) when the submission is that region's parent, or
    empty (Piedmont for "Neirano Barolo"); ("conflict", name) when it sits on
    another branch; (None, None) when the name names no region, the region is
    in another country, or the submission agrees (the same region, or one
    below it: Rioja Alavesa for "Faustino VII Rioja"). A submission whose name
    contains the name's region is not a conflict: the POS abbreviates Côte de
    Brouilly to "Brouilly"."""
    rid = name_region(product_name)
    if rid is None:
        return None, None
    _by_name, nodes, _children = region_tree()
    name, rcountry, _canonical, aliases = nodes[rid]
    if country and rcountry != country:
        return None, None
    _submitted, leaves = _submitted_leaves(regions, country)
    if not leaves:
        return "upgrade", name
    above = set(_ancestors(rid))
    if any(leaf == rid or rid in _ancestors(leaf) for leaf in leaves):
        return None, None
    if all(leaf in above for leaf in leaves):
        return "upgrade", name
    name_words = [_words(a) for a in aliases]
    if any(_contains(_words(a), w) for leaf in leaves for a in nodes[leaf][3] for w in name_words):
        return None, None
    return "conflict", name


def region_from_sources(
    regions: list[str], web_context: str, *, country: str | None = None, product_name: str = "",
) -> str | None:
    """The one finer region the sources name, if there is exactly one.

    The candidates are what `finer_regions_named` and `longer_regions_named`
    report (Barolo for Piedmont, Côte de Brouilly for Brouilly). Any that is
    the parent of another is dropped; when one is left it is returned, and
    when two or more are left (two sub-zones of one region) nothing is.

    The one left must also be named by at least as many sources as the
    submitted region (outside the finer name). The review checks let two
    sources outweigh any number, which is right for a flag but not for a
    replacement: on 2026-10-01, three sources named Rioja Oriental (the
    Garnacha's origin) and five named La Rioja Alta's Rioja.

    A region below the submitted one also needs FINER_REGION_MIN_SOURCES
    sources: one snippet naming both is too thin. On 2026-10-02 Curator
    White's "sourced from … the Paardeberg area" (where the vines grow, not
    the appellation) turned the right Swartland into Paardeberg, 1 source to
    1. A longer name (Côte de Brouilly for Brouilly) may still win on a tie:
    the POS shortened it and the model looked up the short form."""
    where = dict(country=country, product_name=product_name)
    longer = longer_regions_named(regions, web_context, **where)
    names = [*finer_regions_named(regions, web_context, **where), *longer]
    ids = [rid for n in dict.fromkeys(names) if (rid := _region_id(n, country)) is not None]
    above = {a for rid in ids for a in _ancestors(rid)}
    left = [rid for rid in ids if rid not in above]
    if len(left) != 1:
        return None
    _by_name, nodes, _children = region_tree()
    name, _country, _canonical, aliases = nodes[left[0]]
    blocks = _context_blocks(web_context)
    name_words = _words(fold(product_name))
    masked = [(fam, _mask(body, aliases)) for fam, body in blocks]
    _submitted, leaves = _submitted_leaves(regions, country)
    submitted_n = max((_source_count(nodes[leaf][3], masked, name_words) for leaf in leaves), default=0)
    if name not in longer:
        submitted_n = max(submitted_n, FINER_REGION_MIN_SOURCES)
    return name if _source_count(aliases, blocks, name_words) >= submitted_n else None


def replace_region(regions: list[str], new: str, *, country: str | None) -> list[str]:
    """`regions` with `new` and its parents in front. A submitted region whose
    name `new` contains (Brouilly, for Côte de Brouilly) is dropped; the rest
    is kept as it was."""
    rid = _region_id(new, country)
    if rid is None:
        return regions
    _by_name, nodes, _children = region_tree()
    chain = _chain_names(rid)
    new_words = [_words(a) for a in nodes[rid][3]]
    _submitted, leaves = _submitted_leaves(regions, country)
    replaced = {nodes[leaf][0] for leaf in leaves
                if any(_contains(w, _words(a)) for a in nodes[leaf][3] for w in new_words)}
    return chain + [r for r in regions if r not in chain and r not in replaced]


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
