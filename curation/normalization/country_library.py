"""
Country name normalization.

The LLM emits "USA", "US", "United States", "United States of America"
interchangeably. This module collapses each variety-producing country to a
single canonical display form.
"""

from __future__ import annotations

import unicodedata


# Canonical display name -> list of synonyms (canonical itself included).
CANONICAL_COUNTRIES: dict[str, list[str]] = {
    "United States": ["United States", "USA", "U.S.A.", "U.S.", "US",
                       "America", "United States of America"],
    "United Kingdom": ["United Kingdom", "UK", "U.K.", "Great Britain", "Britain", "England"],
    "France": ["France"],
    "Italy": ["Italy", "Italia"],
    "Spain": ["Spain", "España", "Espana"],
    "Portugal": ["Portugal"],
    "Germany": ["Germany", "Deutschland"],
    "Austria": ["Austria", "Österreich", "Osterreich"],
    "Switzerland": ["Switzerland", "Suisse", "Schweiz"],
    "Greece": ["Greece", "Hellas"],
    "Hungary": ["Hungary", "Magyarország", "Magyarorszag"],
    "Romania": ["Romania", "România"],
    "Bulgaria": ["Bulgaria"],
    "Croatia": ["Croatia", "Hrvatska"],
    "Slovenia": ["Slovenia", "Slovenija"],
    "Georgia": ["Georgia"],
    "Lebanon": ["Lebanon"],
    "Israel": ["Israel"],
    "Turkey": ["Turkey", "Türkiye", "Turkiye"],
    "Australia": ["Australia"],
    "New Zealand": ["New Zealand", "NZ"],
    "South Africa": ["South Africa", "RSA"],
    "Argentina": ["Argentina"],
    "Chile": ["Chile"],
    "Uruguay": ["Uruguay"],
    "Brazil": ["Brazil", "Brasil"],
    "Mexico": ["Mexico", "México"],
    "Canada": ["Canada"],
    "China": ["China"],
    "Japan": ["Japan"],
    "India": ["India"],
}


def _norm_key(s: str) -> str:
    if not s:
        return ""
    decomposed = unicodedata.normalize("NFKD", s)
    ascii_only = "".join(c for c in decomposed if not unicodedata.combining(c))
    # Strip punctuation likely to appear in abbreviations (U.S.A.)
    cleaned = "".join(c for c in ascii_only if c.isalnum() or c.isspace())
    return " ".join(cleaned.lower().split())


_SYNONYM_TO_CANONICAL: dict[str, str] = {
    _norm_key(syn): canonical
    for canonical, synonyms in CANONICAL_COUNTRIES.items()
    for syn in synonyms
}


def normalize_country(raw: str) -> str:
    """Return the canonical country name, or title-cased input if unknown."""
    if not raw:
        return ""
    key = _norm_key(raw)
    if key in _SYNONYM_TO_CANONICAL:
        return _SYNONYM_TO_CANONICAL[key]
    return raw.strip().title()


def is_known_country(raw: str) -> bool:
    return _norm_key(raw) in _SYNONYM_TO_CANONICAL
