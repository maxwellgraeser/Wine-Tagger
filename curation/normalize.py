"""
Tag normalization orchestrator.

Runs after Phase 2 (tag inference) and before DB write. Applies the grape,
country, and region libraries to the parsed LLM output and reports any
data-quality issues that should bump the row to needs_review.

Issues currently surfaced:
  - "placeholder_grapes": LLM emitted a vague placeholder ("unknown",
    "Bordeaux Blend") instead of real grape names.
  - "region_country_mismatch": region maps to a country different from the
    one the LLM reported (catches e.g. region=Veneto, country=USA).
  - "country_in_region_slot": LLM put a country name in the region field
    (e.g. region="Portugal"); blanked out.
  - "no_grapes": grape list ended up empty after placeholder removal.
"""

from __future__ import annotations

from grape_library import is_placeholder_grape, normalize_grape, normalize_grapes
from country_library import normalize_country
from region_library import normalize_region


def normalize_tags(parsed: dict) -> tuple[dict, list[str]]:
    """Apply libraries to LLM output. Returns (normalized_parsed, issues).

    A non-empty issues list means the caller should mark the row needs_review.
    """
    issues: list[str] = []
    out = dict(parsed)

    # Country
    country_raw = (out.get("country") or "").strip()
    country = normalize_country(country_raw) if country_raw else ""
    out["country"] = country or None

    # Region (+ cross-check)
    region_raw = (out.get("region") or "").strip()
    if region_raw:
        canonical_region, expected_country = normalize_region(region_raw)
        if canonical_region == "" and expected_country is None and region_raw:
            # Country name was stuffed into region slot
            issues.append("country_in_region_slot")
            out["region"] = None
        else:
            out["region"] = canonical_region or None
            if expected_country and country and expected_country != country:
                issues.append("region_country_mismatch")
    else:
        out["region"] = None

    # Grapes
    raw_grapes = out.get("grapes") or []
    had_placeholder = any(is_placeholder_grape(g) for g in raw_grapes if g)
    cleaned = normalize_grapes(raw_grapes)
    out["grapes"] = cleaned

    if had_placeholder:
        issues.append("placeholder_grapes")
        # The wine almost certainly *is* a blend if the LLM said "Bordeaux Blend",
        # "Red Rhone Blend", etc. Preserve that signal.
        if not cleaned:
            out["is_blend"] = True

    if not cleaned:
        issues.append("no_grapes")

    return out, issues
