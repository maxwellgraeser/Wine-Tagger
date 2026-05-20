"""
Grape name normalization.

Collapses synonyms and casing/diacritic drift to a canonical display form so
that downstream tags (and any grape filter) treat the same variety as one
entity. See curation/LIBRARY.md for the spec.
"""

from __future__ import annotations

import unicodedata


# Canonical display name -> list of synonyms (canonical itself included).
# Spelling chosen for an Australian retail audience; when tied, prefer the
# French form for international varieties.
CANONICAL_GRAPES: dict[str, list[str]] = {
    # Reds
    "Syrah": ["Shiraz", "Syrah"],
    "Cabernet Sauvignon": ["Cabernet Sauvignon", "Cab Sauv", "Cab", "Cabernet Sauv"],
    "Cabernet Franc": ["Cabernet Franc", "Cab Franc"],
    "Merlot": ["Merlot"],
    "Pinot Noir": ["Pinot Noir", "PN", "Pinot Nero", "Spätburgunder", "Spatburgunder"],
    "Grenache": ["Grenache", "Garnacha", "Garnacha Tinta", "Cannonau"],
    "Mourvèdre": ["Mourvèdre", "Mourvedre", "Monastrell", "Mataro"],
    "Tempranillo": ["Tempranillo", "Tinto Fino", "Tinta Fina", "Tinta de Toro",
                    "Tinta del País", "Tinta del Pais", "Tinta Roriz", "Aragonez",
                    "Aragonês", "Cencibel"],
    "Malbec": ["Malbec", "Côt", "Cot", "Auxerrois"],
    "Carmenère": ["Carmenère", "Carmenere"],
    "Sangiovese": ["Sangiovese", "Brunello", "Prugnolo Gentile", "Sangioveto",
                   "Morellino"],
    "Nebbiolo": ["Nebbiolo", "Spanna", "Chiavennasca"],
    "Barbera": ["Barbera"],
    "Dolcetto": ["Dolcetto"],
    "Montepulciano": ["Montepulciano"],
    "Aglianico": ["Aglianico"],
    "Negroamaro": ["Negroamaro", "Negro Amaro"],
    "Primitivo": ["Primitivo", "Zinfandel", "Zin"],
    "Nero d'Avola": ["Nero d'Avola", "Nero dAvola", "Calabrese"],
    "Gamay": ["Gamay", "Gamay Noir"],
    "Touriga Nacional": ["Touriga Nacional"],
    "Touriga Franca": ["Touriga Franca", "Touriga Francesa"],
    "Castelão": ["Castelão", "Castelao", "Periquita"],
    "Alicante Bouschet": ["Alicante Bouschet", "Alicante"],
    "Tannat": ["Tannat"],
    "Petit Verdot": ["Petit Verdot", "Petite Verdot"],
    "Bonarda": ["Bonarda", "Bonarda Argentina", "Charbono"],
    "Petite Sirah": ["Petite Sirah", "Durif"],
    "Cinsault": ["Cinsault", "Cinsaut"],
    "Carignan": ["Carignan", "Cariñena", "Carinena", "Mazuelo", "Mazuela"],
    "Pinotage": ["Pinotage"],
    "Zweigelt": ["Zweigelt"],
    "Blaufränkisch": ["Blaufränkisch", "Blaufrankisch", "Lemberger", "Kékfrankos"],
    "Xinomavro": ["Xinomavro"],
    "Agiorgitiko": ["Agiorgitiko", "St. George"],

    # Whites
    "Chardonnay": ["Chardonnay", "Chard"],
    "Sauvignon Blanc": ["Sauvignon Blanc", "Sauv Blanc", "SB", "Blanc Fumé",
                         "Fumé Blanc", "Fume Blanc"],
    "Pinot Gris": ["Pinot Gris", "Pinot Grigio", "Grauburgunder", "Ruländer", "Rulander"],
    "Riesling": ["Riesling", "Johannisberg Riesling", "White Riesling", "Rheinriesling"],
    "Gewürztraminer": ["Gewürztraminer", "Gewurztraminer", "Traminer"],
    "Chenin Blanc": ["Chenin Blanc", "Chenin", "Steen"],
    "Sémillon": ["Sémillon", "Semillon"],
    "Viognier": ["Viognier"],
    "Marsanne": ["Marsanne"],
    "Roussanne": ["Roussanne"],
    "Grenache Blanc": ["Grenache Blanc", "Garnacha Blanca"],
    "Picpoul": ["Picpoul", "Picpoul Blanc", "Piquepoul", "Piquepoul Blanc"],
    "Albariño": ["Albariño", "Albarino", "Alvarinho"],
    "Verdejo": ["Verdejo"],
    "Verdicchio": ["Verdicchio"],
    "Vermentino": ["Vermentino", "Rolle"],
    "Garganega": ["Garganega", "Grecanico"],
    "Trebbiano": ["Trebbiano", "Ugni Blanc"],
    "Greco Bianco": ["Greco Bianco", "Greco"],
    "Fiano": ["Fiano"],
    "Falanghina": ["Falanghina"],
    "Cortese": ["Cortese"],
    "Grüner Veltliner": ["Grüner Veltliner", "Gruner Veltliner", "Gruner"],
    "Assyrtiko": ["Assyrtiko"],
    "Moschofilero": ["Moschofilero"],
    "Hondarrabi Zuri": ["Hondarrabi Zuri", "Hondarribi Zuri"],
    "Loureiro": ["Loureiro"],
    "Arinto": ["Arinto"],
    "Antão Vaz": ["Antão Vaz", "Antao Vaz"],
    "Muscadet": ["Muscadet", "Melon de Bourgogne", "Melon"],
    "Muscat": ["Muscat", "Moscato", "Moscatel"],

    # Rosé-leaning / dual purpose handled above (Cinsault, Grenache, etc.)
}


# Vague placeholders the LLM sometimes returns instead of actual grape names.
# Stored normalized (lowercased, ASCII).
PLACEHOLDER_GRAPES: set[str] = {
    "unknown",
    "n/a",
    "na",
    "none",
    "blend",
    "red blend",
    "white blend",
    "rose blend",
    "red rhone blend",
    "white rhone blend",
    "rhone blend",
    "bordeaux blend",
    "red bordeaux blend",
    "white bordeaux blend",
    "gsm",
    "field blend",
    "proprietary blend",
    "various",
    "mixed",
}


def _norm_key(s: str) -> str:
    """Lowercase, strip diacritics, collapse whitespace, drop punctuation noise."""
    if not s:
        return ""
    decomposed = unicodedata.normalize("NFKD", s)
    ascii_only = "".join(c for c in decomposed if not unicodedata.combining(c))
    # Collapse whitespace
    return " ".join(ascii_only.lower().split())


_SYNONYM_TO_CANONICAL: dict[str, str] = {
    _norm_key(syn): canonical
    for canonical, synonyms in CANONICAL_GRAPES.items()
    for syn in synonyms
}


def is_placeholder_grape(raw: str) -> bool:
    """True if the LLM emitted a vague placeholder instead of a real grape name."""
    return _norm_key(raw) in PLACEHOLDER_GRAPES


def is_canonical_grape(raw: str) -> bool:
    """True if the grape name resolves to an entry in CANONICAL_GRAPES."""
    return _norm_key(raw) in _SYNONYM_TO_CANONICAL


def normalize_grape(raw: str) -> str:
    """Return the canonical spelling for a single grape.

    Falls back to a title-cased version of the input if no match is found,
    so unknown grapes pass through cleanly rather than being dropped.
    """
    if not raw:
        return ""
    key = _norm_key(raw)
    if key in _SYNONYM_TO_CANONICAL:
        return _SYNONYM_TO_CANONICAL[key]
    return raw.strip().title()


def normalize_grapes(raw: list[str]) -> list[str]:
    """Normalize a list of grapes; drop placeholders; dedupe preserving order."""
    seen: set[str] = set()
    out: list[str] = []
    for g in raw:
        if not g or is_placeholder_grape(g):
            continue
        canonical = normalize_grape(g)
        key = _norm_key(canonical)
        if key in seen:
            continue
        seen.add(key)
        out.append(canonical)
    return out
