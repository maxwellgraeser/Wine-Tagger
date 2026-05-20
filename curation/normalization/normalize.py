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
  - "non_canonical_grape": LLM returned a grape name not in CANONICAL_GRAPES
    (e.g. "Pin Blanc", "Eigen") — usually a hallucination.
  - "is_blend_mismatch": declared is_blend disagreed with the cleaned grape
    count (single grape but is_blend=True, or multiple grapes but is_blend=False).
"""

from __future__ import annotations

from .grape_library import is_canonical_grape, is_placeholder_grape, normalize_grape, normalize_grapes
from .country_library import normalize_country
from .region_library import normalize_regions


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

    # Region (+ parent expansion + cross-check). `region` is a list of
    # strings; legacy single-string input is accepted by normalize_regions.
    region_raw = out.get("region")
    if region_raw:
        expanded, expected_country, country_in_slot = normalize_regions(region_raw)
        if country_in_slot:
            issues.append("country_in_region_slot")
        out["region"] = expanded or None
        if expected_country and country and expected_country != country:
            issues.append("region_country_mismatch")
    else:
        out["region"] = None

    # Grapes
    raw_grapes = out.get("grapes") or []
    had_placeholder = any(is_placeholder_grape(g) for g in raw_grapes if g)
    non_canonical = [
        g for g in raw_grapes
        if g and not is_placeholder_grape(g) and not is_canonical_grape(g)
    ]
    cleaned = normalize_grapes(raw_grapes)
    out["grapes"] = cleaned

    if had_placeholder:
        issues.append("placeholder_grapes")
        # The wine almost certainly *is* a blend if the LLM said "Bordeaux Blend",
        # "Red Rhone Blend", etc. Preserve that signal.
        if not cleaned:
            out["is_blend"] = True

    if non_canonical:
        # Grape name not in the canonical vocabulary — likely hallucinated
        # (e.g. "Pin Blanc", "Eigen") or a rare variety we don't track yet.
        issues.append("non_canonical_grape")

    if not cleaned:
        issues.append("no_grapes")

    # Mechanical is_blend reconciliation against the cleaned grape list.
    # A single varietal cannot be a blend; two or more grapes is a blend.
    # Disagreement with the LLM's value is a quality signal — flag it.
    declared_blend = out.get("is_blend")
    if len(cleaned) == 1:
        if declared_blend is True:
            issues.append("is_blend_mismatch")
        out["is_blend"] = False
    elif len(cleaned) >= 2:
        if declared_blend is False:
            issues.append("is_blend_mismatch")
        out["is_blend"] = True

    return out, issues
