"""
Region name normalization + region→country pinning.

Two jobs:
  1. Collapse region spelling drift to a canonical form ("Languedoc Roussillon"
     → "Languedoc-Roussillon", "Piemonte" → "Piedmont").
  2. Cross-check country against the region's known country, so we can catch
     errors like the LLM tagging "Veneto" as country=United States.

Coverage is the regions we've actually seen in the catalog; unknown regions
pass through unmodified and skip the country check.
"""

from __future__ import annotations

import unicodedata


# Canonical region -> {"country": ..., "synonyms": [...]}
# Synonyms include the canonical form. Sub-regions are listed as separate
# entries that pin to the same country (e.g. "Barolo" → Italy).
REGIONS: dict[str, dict] = {
    # ---------------- France ----------------
    "Bordeaux":              {"country": "France", "synonyms": ["Bordeaux"]},
    "Burgundy":              {"country": "France", "synonyms": ["Burgundy", "Bourgogne"]},
    "Champagne":             {"country": "France", "synonyms": ["Champagne"]},
    "Loire Valley":          {"country": "France", "synonyms": ["Loire Valley", "Loire", "Vallée de la Loire", "Val de Loire"]},
    "Touraine":              {"country": "France", "synonyms": ["Touraine"]},
    "Rhône Valley":          {"country": "France", "synonyms": ["Rhône Valley", "Rhone Valley", "Rhône", "Rhone", "Vallée du Rhône"]},
    "Provence":              {"country": "France", "synonyms": ["Provence"]},
    "Languedoc-Roussillon":  {"country": "France", "synonyms": ["Languedoc-Roussillon", "Languedoc Roussillon", "Languedoc"]},
    "Roussillon":            {"country": "France", "synonyms": ["Roussillon", "Côtes du Roussillon", "Cotes du Roussillon", "Côtes du Roussillon Villages"]},
    "Beaujolais":            {"country": "France", "synonyms": ["Beaujolais", "Brouilly"]},
    "Alsace":                {"country": "France", "synonyms": ["Alsace"]},
    "Jura":                  {"country": "France", "synonyms": ["Jura"]},
    "Savoie":                {"country": "France", "synonyms": ["Savoie", "Savoy"]},
    "Corsica":               {"country": "France", "synonyms": ["Corsica", "Corse"]},
    "South West France":     {"country": "France", "synonyms": ["South West France", "Sud-Ouest"]},

    # ---------------- Italy ----------------
    "Piedmont":              {"country": "Italy", "synonyms": ["Piedmont", "Piemonte"]},
    "Barolo":                {"country": "Italy", "synonyms": ["Barolo"]},
    "Barbaresco":            {"country": "Italy", "synonyms": ["Barbaresco"]},
    "Veneto":                {"country": "Italy", "synonyms": ["Veneto", "delle Venezie", "Venezie", "Valpolicella", "Soave", "Prosecco"]},
    "Tuscany":               {"country": "Italy", "synonyms": ["Tuscany", "Toscana", "Chianti", "Chianti Classico", "Montalcino", "Brunello di Montalcino"]},
    "Lombardy":              {"country": "Italy", "synonyms": ["Lombardy", "Lombardia", "Franciacorta"]},
    "Friuli":                {"country": "Italy", "synonyms": ["Friuli", "Friuli-Venezia Giulia", "Friuli Venezia Giulia"]},
    "Trentino-Alto Adige":   {"country": "Italy", "synonyms": ["Trentino-Alto Adige", "Trentino Alto Adige", "Alto Adige", "Südtirol", "Sudtirol", "Trentino"]},
    "Emilia-Romagna":        {"country": "Italy", "synonyms": ["Emilia-Romagna", "Emilia Romagna"]},
    "Marche":                {"country": "Italy", "synonyms": ["Marche", "Marches"]},
    "Abruzzo":               {"country": "Italy", "synonyms": ["Abruzzo"]},
    "Campania":              {"country": "Italy", "synonyms": ["Campania"]},
    "Puglia":                {"country": "Italy", "synonyms": ["Puglia", "Apulia", "Salice Salentino", "Salento"]},
    "Sicily":                {"country": "Italy", "synonyms": ["Sicily", "Sicilia", "Etna"]},
    "Sardinia":              {"country": "Italy", "synonyms": ["Sardinia", "Sardegna"]},
    "Calabria":              {"country": "Italy", "synonyms": ["Calabria", "Cirò", "Ciro"]},

    # ---------------- Spain ----------------
    "Rioja":                 {"country": "Spain", "synonyms": ["Rioja", "La Rioja"]},
    "Ribera del Duero":      {"country": "Spain", "synonyms": ["Ribera del Duero"]},
    "Rías Baixas":           {"country": "Spain", "synonyms": ["Rías Baixas", "Rias Baixas"]},
    "Priorat":               {"country": "Spain", "synonyms": ["Priorat", "Priorato"]},
    "Penedès":               {"country": "Spain", "synonyms": ["Penedès", "Penedes"]},
    "Catalonia":             {"country": "Spain", "synonyms": ["Catalonia", "Cataluña", "Catalunya"]},
    "Toro":                  {"country": "Spain", "synonyms": ["Toro"]},
    "Rueda":                 {"country": "Spain", "synonyms": ["Rueda"]},
    "Jumilla":               {"country": "Spain", "synonyms": ["Jumilla"]},
    "Jerez":                 {"country": "Spain", "synonyms": ["Jerez", "Sherry"]},
    "País Vasco":            {"country": "Spain", "synonyms": ["País Vasco", "Pais Vasco", "Basque", "Basque Country", "Getariako Txakolina", "Txakolina", "Txakoli"]},

    # ---------------- Portugal ----------------
    "Douro":                 {"country": "Portugal", "synonyms": ["Douro"]},
    "Lisboa":                {"country": "Portugal", "synonyms": ["Lisboa", "Lisbon", "Estremadura"]},
    "Alentejo":              {"country": "Portugal", "synonyms": ["Alentejo"]},
    "Vinho Verde":           {"country": "Portugal", "synonyms": ["Vinho Verde"]},
    "Dão":                   {"country": "Portugal", "synonyms": ["Dão", "Dao"]},
    "Bairrada":              {"country": "Portugal", "synonyms": ["Bairrada"]},

    # ---------------- Germany / Austria ----------------
    "Mosel":                 {"country": "Germany", "synonyms": ["Mosel", "Mosel-Saar-Ruwer"]},
    "Rheingau":              {"country": "Germany", "synonyms": ["Rheingau"]},
    "Rheinhessen":           {"country": "Germany", "synonyms": ["Rheinhessen"]},
    "Pfalz":                 {"country": "Germany", "synonyms": ["Pfalz", "Palatinate"]},
    "Baden":                 {"country": "Germany", "synonyms": ["Baden"]},
    "Wachau":                {"country": "Austria", "synonyms": ["Wachau"]},
    "Kamptal":               {"country": "Austria", "synonyms": ["Kamptal"]},
    "Burgenland":            {"country": "Austria", "synonyms": ["Burgenland"]},

    # ---------------- USA ----------------
    "California":            {"country": "United States", "synonyms": ["California", "CA"]},
    "Napa Valley":           {"country": "United States", "synonyms": ["Napa Valley", "Napa"]},
    "Sonoma":                {"country": "United States", "synonyms": ["Sonoma", "Sonoma County", "Russian River Valley"]},
    "Paso Robles":           {"country": "United States", "synonyms": ["Paso Robles"]},
    "Santa Barbara":         {"country": "United States", "synonyms": ["Santa Barbara", "Santa Barbara County", "Sta. Rita Hills", "Santa Rita Hills"]},
    "Willamette Valley":     {"country": "United States", "synonyms": ["Willamette Valley", "Willamette"]},
    "Oregon":                {"country": "United States", "synonyms": ["Oregon"]},
    "Washington":            {"country": "United States", "synonyms": ["Washington", "Washington State", "Columbia Valley", "Walla Walla"]},
    "Finger Lakes":          {"country": "United States", "synonyms": ["Finger Lakes"]},

    # ---------------- South America ----------------
    "Mendoza":               {"country": "Argentina", "synonyms": ["Mendoza", "Uco Valley"]},
    "Salta":                 {"country": "Argentina", "synonyms": ["Salta", "Cafayate"]},
    "Patagonia":             {"country": "Argentina", "synonyms": ["Patagonia"]},
    "Maipo Valley":          {"country": "Chile", "synonyms": ["Maipo Valley", "Maipo"]},
    "Colchagua":             {"country": "Chile", "synonyms": ["Colchagua", "Colchagua Valley"]},
    "Casablanca":            {"country": "Chile", "synonyms": ["Casablanca", "Casablanca Valley"]},
    "Aconcagua":             {"country": "Chile", "synonyms": ["Aconcagua", "Aconcagua Valley"]},

    # ---------------- South Africa ----------------
    "Western Cape":          {"country": "South Africa", "synonyms": ["Western Cape"]},
    "Coastal Region":        {"country": "South Africa", "synonyms": ["Coastal Region"]},
    "Stellenbosch":          {"country": "South Africa", "synonyms": ["Stellenbosch"]},
    "Paarl":                 {"country": "South Africa", "synonyms": ["Paarl"]},
    "Swartland":             {"country": "South Africa", "synonyms": ["Swartland"]},
    "Robertson":             {"country": "South Africa", "synonyms": ["Robertson"]},
    "Walker Bay":            {"country": "South Africa", "synonyms": ["Walker Bay", "Hemel-en-Aarde"]},
    "Cape Peninsula":        {"country": "South Africa", "synonyms": ["Cape Peninsula"]},

    # ---------------- Australia / NZ ----------------
    "Barossa Valley":        {"country": "Australia", "synonyms": ["Barossa Valley", "Barossa"]},
    "McLaren Vale":          {"country": "Australia", "synonyms": ["McLaren Vale"]},
    "Clare Valley":          {"country": "Australia", "synonyms": ["Clare Valley"]},
    "Eden Valley":           {"country": "Australia", "synonyms": ["Eden Valley"]},
    "Coonawarra":            {"country": "Australia", "synonyms": ["Coonawarra"]},
    "Margaret River":        {"country": "Australia", "synonyms": ["Margaret River"]},
    "Yarra Valley":          {"country": "Australia", "synonyms": ["Yarra Valley"]},
    "Hunter Valley":          {"country": "Australia", "synonyms": ["Hunter Valley"]},
    "Tasmania":              {"country": "Australia", "synonyms": ["Tasmania"]},
    "Marlborough":           {"country": "New Zealand", "synonyms": ["Marlborough"]},
    "Central Otago":         {"country": "New Zealand", "synonyms": ["Central Otago"]},
    "Hawke's Bay":           {"country": "New Zealand", "synonyms": ["Hawke's Bay", "Hawkes Bay"]},

    # ---------------- Other ----------------
    "Bekaa Valley":          {"country": "Lebanon", "synonyms": ["Bekaa Valley", "Bekaa"]},
    "Tokaj":                 {"country": "Hungary", "synonyms": ["Tokaj", "Tokaji"]},
    "Santorini":             {"country": "Greece", "synonyms": ["Santorini"]},
    "Nemea":                 {"country": "Greece", "synonyms": ["Nemea"]},
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


def normalize_region(raw: str) -> tuple[str, str | None]:
    """Return (canonical_region, expected_country).

    - If the input matches a known region/synonym, returns the canonical form
      and the country pinned to that region.
    - If the input is actually a country name in the region slot, returns
      ("", None) so the caller can blank it out.
    - Otherwise returns (title-cased input, None) — unknown region, no
      country constraint.
    """
    if not raw:
        return "", None
    key = _norm_key(raw)

    if key in COUNTRY_AS_REGION:
        return "", None

    if key in _SYNONYM_TO_REGION:
        canonical = _SYNONYM_TO_REGION[key]
        return canonical, _REGION_TO_COUNTRY[canonical]

    # Try a loose match: some LLM outputs jam region + sub-region together,
    # e.g. "Coastal Region Cape Peninsula" or "Coastal Region Paarl".
    # Look for any known synonym appearing as a substring of the input.
    for syn_key, region in _SYNONYM_TO_REGION.items():
        if syn_key and syn_key in key:
            return region, _REGION_TO_COUNTRY[region]

    return raw.strip(), None


def is_known_region(raw: str) -> bool:
    return _norm_key(raw) in _SYNONYM_TO_REGION
