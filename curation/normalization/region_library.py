"""
Region name normalization + region→country pinning + parent expansion.

Three jobs:
  1. Collapse region spelling drift to a canonical form ("Languedoc Roussillon"
     → "Languedoc-Roussillon", "Piemonte" → "Piedmont").
  2. Expand a region into its parent hierarchy. Tagging a wine "Willamette
     Valley" implicitly tags it "Oregon" as well; tagging "Russian River
     Valley" implies "Sonoma" and "California". `normalize_regions` returns
     the full list from most-specific to broadest, deduped.
  3. Cross-check country against the regions' known countries, so we can catch
     errors like the LLM tagging "Veneto" as country=United States.

Coverage is the regions we've actually seen in the catalog; unknown regions
pass through unmodified and skip the country check.
"""

from __future__ import annotations

import unicodedata


# Canonical region -> {"country": ..., "synonyms": [...], "parents": [...]}
# Synonyms include the canonical form. `parents` lists broader canonical
# regions (most-specific → broadest order) that should be tagged alongside
# this one. Top-level regions have an empty parents list.
REGIONS: dict[str, dict] = {
    # ---------------- France ----------------
    "Bordeaux":              {"country": "France", "synonyms": ["Bordeaux"], "parents": []},
    "Burgundy":              {"country": "France", "synonyms": ["Burgundy", "Bourgogne"], "parents": []},
    "Champagne":             {"country": "France", "synonyms": ["Champagne"], "parents": []},
    "Loire Valley":          {"country": "France", "synonyms": ["Loire Valley", "Loire", "Vallée de la Loire", "Val de Loire"], "parents": []},
    "Touraine":              {"country": "France", "synonyms": ["Touraine"], "parents": ["Loire Valley"]},
    "Rhône Valley":          {"country": "France", "synonyms": ["Rhône Valley", "Rhone Valley", "Rhône", "Rhone", "Vallée du Rhône"], "parents": []},
    "Provence":              {"country": "France", "synonyms": ["Provence"], "parents": []},
    "Languedoc-Roussillon":  {"country": "France", "synonyms": ["Languedoc-Roussillon", "Languedoc Roussillon", "Languedoc"], "parents": []},
    "Roussillon":            {"country": "France", "synonyms": ["Roussillon", "Côtes du Roussillon", "Cotes du Roussillon", "Côtes du Roussillon Villages"], "parents": ["Languedoc-Roussillon"]},
    "Beaujolais":            {"country": "France", "synonyms": ["Beaujolais", "Brouilly"], "parents": []},
    "Alsace":                {"country": "France", "synonyms": ["Alsace"], "parents": []},
    "Jura":                  {"country": "France", "synonyms": ["Jura"], "parents": []},
    "Savoie":                {"country": "France", "synonyms": ["Savoie", "Savoy"], "parents": []},
    "Corsica":               {"country": "France", "synonyms": ["Corsica", "Corse"], "parents": []},
    "South West France":     {"country": "France", "synonyms": ["South West France", "Sud-Ouest"], "parents": []},

    # ---------------- Italy ----------------
    "Piedmont":              {"country": "Italy", "synonyms": ["Piedmont", "Piemonte"], "parents": []},
    "Barolo":                {"country": "Italy", "synonyms": ["Barolo"], "parents": ["Piedmont"]},
    "Barbaresco":            {"country": "Italy", "synonyms": ["Barbaresco"], "parents": ["Piedmont"]},
    "Veneto":                {"country": "Italy", "synonyms": ["Veneto", "delle Venezie", "Venezie", "Valpolicella", "Soave", "Prosecco"], "parents": []},
    "Tuscany":               {"country": "Italy", "synonyms": ["Tuscany", "Toscana", "Chianti", "Chianti Classico", "Montalcino", "Brunello di Montalcino"], "parents": []},
    "Lombardy":              {"country": "Italy", "synonyms": ["Lombardy", "Lombardia", "Franciacorta"], "parents": []},
    "Friuli":                {"country": "Italy", "synonyms": ["Friuli", "Friuli-Venezia Giulia", "Friuli Venezia Giulia"], "parents": []},
    "Trentino-Alto Adige":   {"country": "Italy", "synonyms": ["Trentino-Alto Adige", "Trentino Alto Adige", "Alto Adige", "Südtirol", "Sudtirol", "Trentino"], "parents": []},
    "Emilia-Romagna":        {"country": "Italy", "synonyms": ["Emilia-Romagna", "Emilia Romagna"], "parents": []},
    "Marche":                {"country": "Italy", "synonyms": ["Marche", "Marches"], "parents": []},
    "Abruzzo":               {"country": "Italy", "synonyms": ["Abruzzo"], "parents": []},
    "Campania":              {"country": "Italy", "synonyms": ["Campania"], "parents": []},
    "Puglia":                {"country": "Italy", "synonyms": ["Puglia", "Apulia", "Salice Salentino", "Salento"], "parents": []},
    "Sicily":                {"country": "Italy", "synonyms": ["Sicily", "Sicilia", "Etna"], "parents": []},
    "Sardinia":              {"country": "Italy", "synonyms": ["Sardinia", "Sardegna"], "parents": []},
    "Calabria":              {"country": "Italy", "synonyms": ["Calabria", "Cirò", "Ciro"], "parents": []},

    # ---------------- Spain ----------------
    "Rioja":                 {"country": "Spain", "synonyms": ["Rioja", "La Rioja"], "parents": []},
    "Ribera del Duero":      {"country": "Spain", "synonyms": ["Ribera del Duero"], "parents": []},
    "Rías Baixas":           {"country": "Spain", "synonyms": ["Rías Baixas", "Rias Baixas"], "parents": []},
    "Priorat":               {"country": "Spain", "synonyms": ["Priorat", "Priorato"], "parents": ["Catalonia"]},
    "Penedès":               {"country": "Spain", "synonyms": ["Penedès", "Penedes"], "parents": ["Catalonia"]},
    "Catalonia":             {"country": "Spain", "synonyms": ["Catalonia", "Cataluña", "Catalunya"], "parents": []},
    "Toro":                  {"country": "Spain", "synonyms": ["Toro"], "parents": []},
    "Rueda":                 {"country": "Spain", "synonyms": ["Rueda"], "parents": []},
    "Jumilla":               {"country": "Spain", "synonyms": ["Jumilla"], "parents": []},
    "Jerez":                 {"country": "Spain", "synonyms": ["Jerez", "Sherry"], "parents": []},
    "País Vasco":            {"country": "Spain", "synonyms": ["País Vasco", "Pais Vasco", "Basque", "Basque Country", "Getariako Txakolina", "Txakolina", "Txakoli"], "parents": []},

    # ---------------- Portugal ----------------
    "Douro":                 {"country": "Portugal", "synonyms": ["Douro"], "parents": []},
    "Lisboa":                {"country": "Portugal", "synonyms": ["Lisboa", "Lisbon", "Estremadura"], "parents": []},
    "Alentejo":              {"country": "Portugal", "synonyms": ["Alentejo"], "parents": []},
    "Vinho Verde":           {"country": "Portugal", "synonyms": ["Vinho Verde"], "parents": []},
    "Dão":                   {"country": "Portugal", "synonyms": ["Dão", "Dao"], "parents": []},
    "Bairrada":              {"country": "Portugal", "synonyms": ["Bairrada"], "parents": []},

    # ---------------- Germany / Austria ----------------
    "Mosel":                 {"country": "Germany", "synonyms": ["Mosel", "Mosel-Saar-Ruwer"], "parents": []},
    "Rheingau":              {"country": "Germany", "synonyms": ["Rheingau"], "parents": []},
    "Rheinhessen":           {"country": "Germany", "synonyms": ["Rheinhessen"], "parents": []},
    "Pfalz":                 {"country": "Germany", "synonyms": ["Pfalz", "Palatinate"], "parents": []},
    "Baden":                 {"country": "Germany", "synonyms": ["Baden"], "parents": []},
    "Wachau":                {"country": "Austria", "synonyms": ["Wachau"], "parents": []},
    "Kamptal":               {"country": "Austria", "synonyms": ["Kamptal"], "parents": []},
    "Burgenland":            {"country": "Austria", "synonyms": ["Burgenland"], "parents": []},

    # ---------------- USA ----------------
    "California":            {"country": "United States", "synonyms": ["California", "CA"], "parents": []},
    "Napa Valley":           {"country": "United States", "synonyms": ["Napa Valley", "Napa"], "parents": ["California"]},
    "Sonoma":                {"country": "United States", "synonyms": ["Sonoma", "Sonoma County"], "parents": ["California"]},
    "Russian River Valley":  {"country": "United States", "synonyms": ["Russian River Valley", "Russian River"], "parents": ["Sonoma", "California"]},
    "Carneros":              {"country": "United States", "synonyms": ["Carneros", "Los Carneros"], "parents": ["California"]},
    "Paso Robles":           {"country": "United States", "synonyms": ["Paso Robles"], "parents": ["California"]},
    "Santa Barbara":         {"country": "United States", "synonyms": ["Santa Barbara", "Santa Barbara County", "Sta. Rita Hills", "Santa Rita Hills"], "parents": ["California"]},
    "Oregon":                {"country": "United States", "synonyms": ["Oregon"], "parents": []},
    "Willamette Valley":     {"country": "United States", "synonyms": ["Willamette Valley", "Willamette"], "parents": ["Oregon"]},
    "Washington":            {"country": "United States", "synonyms": ["Washington", "Washington State", "Columbia Valley", "Walla Walla"], "parents": []},
    "Finger Lakes":          {"country": "United States", "synonyms": ["Finger Lakes"], "parents": []},

    # ---------------- South America ----------------
    "Mendoza":               {"country": "Argentina", "synonyms": ["Mendoza", "Uco Valley"], "parents": []},
    "Salta":                 {"country": "Argentina", "synonyms": ["Salta", "Cafayate"], "parents": []},
    "Patagonia":             {"country": "Argentina", "synonyms": ["Patagonia"], "parents": []},
    "Maipo Valley":          {"country": "Chile", "synonyms": ["Maipo Valley", "Maipo"], "parents": []},
    "Colchagua":             {"country": "Chile", "synonyms": ["Colchagua", "Colchagua Valley"], "parents": []},
    "Casablanca":            {"country": "Chile", "synonyms": ["Casablanca", "Casablanca Valley"], "parents": []},
    "Aconcagua":             {"country": "Chile", "synonyms": ["Aconcagua", "Aconcagua Valley"], "parents": []},

    # ---------------- South Africa ----------------
    "Western Cape":          {"country": "South Africa", "synonyms": ["Western Cape"], "parents": []},
    "Coastal Region":        {"country": "South Africa", "synonyms": ["Coastal Region"], "parents": ["Western Cape"]},
    "Stellenbosch":          {"country": "South Africa", "synonyms": ["Stellenbosch"], "parents": ["Coastal Region", "Western Cape"]},
    "Paarl":                 {"country": "South Africa", "synonyms": ["Paarl"], "parents": ["Coastal Region", "Western Cape"]},
    "Swartland":             {"country": "South Africa", "synonyms": ["Swartland"], "parents": ["Coastal Region", "Western Cape"]},
    "Constantia":            {"country": "South Africa", "synonyms": ["Constantia"], "parents": ["Coastal Region", "Western Cape"]},
    "Robertson":             {"country": "South Africa", "synonyms": ["Robertson"], "parents": ["Western Cape"]},
    "Walker Bay":            {"country": "South Africa", "synonyms": ["Walker Bay", "Hemel-en-Aarde"], "parents": ["Western Cape"]},
    "Cape Peninsula":        {"country": "South Africa", "synonyms": ["Cape Peninsula"], "parents": ["Western Cape"]},

    # ---------------- Australia / NZ ----------------
    "Barossa Valley":        {"country": "Australia", "synonyms": ["Barossa Valley", "Barossa"], "parents": []},
    "McLaren Vale":          {"country": "Australia", "synonyms": ["McLaren Vale"], "parents": []},
    "Clare Valley":          {"country": "Australia", "synonyms": ["Clare Valley"], "parents": []},
    "Eden Valley":           {"country": "Australia", "synonyms": ["Eden Valley"], "parents": []},
    "Coonawarra":            {"country": "Australia", "synonyms": ["Coonawarra"], "parents": []},
    "Margaret River":        {"country": "Australia", "synonyms": ["Margaret River"], "parents": []},
    "Yarra Valley":          {"country": "Australia", "synonyms": ["Yarra Valley"], "parents": []},
    "Hunter Valley":         {"country": "Australia", "synonyms": ["Hunter Valley"], "parents": []},
    "Tasmania":              {"country": "Australia", "synonyms": ["Tasmania"], "parents": []},
    "Marlborough":           {"country": "New Zealand", "synonyms": ["Marlborough"], "parents": []},
    "Central Otago":         {"country": "New Zealand", "synonyms": ["Central Otago"], "parents": []},
    "Hawke's Bay":           {"country": "New Zealand", "synonyms": ["Hawke's Bay", "Hawkes Bay"], "parents": []},

    # ---------------- Other ----------------
    "Bekaa Valley":          {"country": "Lebanon", "synonyms": ["Bekaa Valley", "Bekaa"], "parents": []},
    "Tokaj":                 {"country": "Hungary", "synonyms": ["Tokaj", "Tokaji"], "parents": []},
    "Santorini":             {"country": "Greece", "synonyms": ["Santorini"], "parents": []},
    "Nemea":                 {"country": "Greece", "synonyms": ["Nemea"], "parents": []},
}


# Regions that are really country names — the LLM sometimes fills the region
# slot with the country (e.g. region="Portugal"). Treat as "no region".
COUNTRY_AS_REGION: set[str] = {
    "france", "italy", "spain", "portugal", "germany", "austria",
    "united states", "usa", "us", "australia", "new zealand",
    "south africa", "argentina", "chile", "greece", "lebanon",
}


def _norm_key(s: str) -> str:
    if not s:
        return ""
    decomposed = unicodedata.normalize("NFKD", s)
    ascii_only = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(ascii_only.lower().split())


_SYNONYM_TO_REGION: dict[str, str] = {
    _norm_key(syn): canonical
    for canonical, info in REGIONS.items()
    for syn in info["synonyms"]
}

_REGION_TO_COUNTRY: dict[str, str] = {
    canonical: info["country"] for canonical, info in REGIONS.items()
}

_REGION_TO_PARENTS: dict[str, list[str]] = {
    canonical: info.get("parents", []) for canonical, info in REGIONS.items()
}


def _resolve_one(raw: str) -> tuple[str, str | None]:
    """Resolve a single raw region string to (canonical, expected_country).

    - Returns ("", None) if the input is a country name in the region slot.
    - Returns (canonical, country) when matched (incl. substring fallback).
    - Returns (title-cased input, None) when unknown.
    """
    if not raw:
        return "", None
    key = _norm_key(raw)
    if key in COUNTRY_AS_REGION:
        return "", None
    if key in _SYNONYM_TO_REGION:
        canonical = _SYNONYM_TO_REGION[key]
        return canonical, _REGION_TO_COUNTRY[canonical]
    # Loose match: some LLM outputs jam region + sub-region together,
    # e.g. "Coastal Region Cape Peninsula" or "Coastal Region Paarl".
    for syn_key, region in _SYNONYM_TO_REGION.items():
        if syn_key and syn_key in key:
            return region, _REGION_TO_COUNTRY[region]
    return raw.strip(), None


def normalize_region(raw: str) -> tuple[list[str], str | None]:
    """Single-region normalize that also expands parents.

    Returns (regions_list, expected_country). The list is the canonical
    region followed by its parents, most-specific → broadest. Empty list
    means the input was blank or a country name in the region slot. An
    unknown region passes through as a single-item list with country=None.
    """
    canonical, country = _resolve_one(raw)
    if not canonical:
        return [], country
    if canonical in _REGION_TO_PARENTS:
        return [canonical, *_REGION_TO_PARENTS[canonical]], country
    return [canonical], country


def normalize_regions(raw: list[str] | str) -> tuple[list[str], str | None, bool]:
    """List-aware normalize with parent expansion and country resolution.

    Accepts a list of raw region strings (or a single string for legacy
    callers) and returns (expanded_regions, expected_country, country_in_slot).

    - `expanded_regions` is the union of each entry's expansion, deduped,
      preserving most-specific → broadest order (parents come after their
      children, unknown regions appended at the end).
    - `expected_country` is taken from the most-specific known region; None
      if no entry was matched.
    - `country_in_slot` is True iff at least one entry was a bare country
      name in the region slot — the caller should flag `country_in_region_slot`.
    """
    if isinstance(raw, str):
        raw = [raw]
    if not raw:
        return [], None, False

    expanded: list[str] = []
    seen: set[str] = set()
    expected_country: str | None = None
    country_in_slot = False

    for entry in raw:
        if entry is None:
            continue
        if not str(entry).strip():
            continue
        canonical, country = _resolve_one(entry)
        if not canonical and country is None and _norm_key(entry) in COUNTRY_AS_REGION:
            country_in_slot = True
            continue
        if not canonical:
            continue
        # First known region wins the country pin (most specific in the
        # caller's order — and entries the LLM emits are usually
        # specific-first too).
        if country and expected_country is None:
            expected_country = country
        # Push canonical first, then parents.
        chain = [canonical, *_REGION_TO_PARENTS.get(canonical, [])]
        for r in chain:
            k = _norm_key(r)
            if k in seen:
                continue
            seen.add(k)
            expanded.append(r)

    return expanded, expected_country, country_in_slot


def is_known_region(raw: str) -> bool:
    return _norm_key(raw) in _SYNONYM_TO_REGION
