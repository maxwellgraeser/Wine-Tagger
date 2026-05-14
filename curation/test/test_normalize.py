#!/usr/bin/env python3
"""
Unit tests for the normalization libraries (grape, country, region) and the
`normalize_tags` orchestrator. No network or LLM calls.

Covers the cases suggested in LIBRARY.md § Testing.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from normalization.grape_library import normalize_grape, normalize_grapes, is_placeholder_grape
from normalization.country_library import normalize_country
from normalization.region_library import normalize_region
from normalization import normalize_tags


class TestNormalizeGrape(unittest.TestCase):

    def test_syrah_collapses_to_shiraz(self):
        self.assertEqual(normalize_grape("syrah"), "Shiraz")

    def test_uppercase_shiraz(self):
        self.assertEqual(normalize_grape("SHIRAZ"), "Shiraz")

    def test_diacritics_reinjected(self):
        self.assertEqual(normalize_grape("carmenere"), "Carmenère")

    def test_unknown_grape_title_cased_passthrough(self):
        self.assertEqual(normalize_grape("Assyrtiko"), "Assyrtiko")

    def test_empty_string(self):
        self.assertEqual(normalize_grape(""), "")


class TestIsPlaceholderGrape(unittest.TestCase):

    def test_bordeaux_blend_is_placeholder(self):
        self.assertTrue(is_placeholder_grape("Bordeaux Blend"))

    def test_red_rhone_blend_is_placeholder(self):
        self.assertTrue(is_placeholder_grape("Red Rhone Blend"))

    def test_unknown_is_placeholder(self):
        self.assertTrue(is_placeholder_grape("unknown"))

    def test_real_grape_not_placeholder(self):
        self.assertFalse(is_placeholder_grape("Cabernet Sauvignon"))


class TestNormalizeGrapes(unittest.TestCase):

    def test_syrah_and_shiraz_dedupe(self):
        self.assertEqual(
            normalize_grapes(["Syrah", "Shiraz", "Grenache"]),
            ["Shiraz", "Grenache"],
        )

    def test_placeholders_dropped(self):
        self.assertEqual(
            normalize_grapes(["Bordeaux Blend", "Cabernet Sauvignon"]),
            ["Cabernet Sauvignon"],
        )

    def test_empty_list(self):
        self.assertEqual(normalize_grapes([]), [])


class TestNormalizeCountry(unittest.TestCase):

    def test_usa_to_united_states(self):
        self.assertEqual(normalize_country("USA"), "United States")

    def test_us_to_united_states(self):
        self.assertEqual(normalize_country("US"), "United States")

    def test_america_to_united_states(self):
        self.assertEqual(normalize_country("America"), "United States")


class TestNormalizeRegion(unittest.TestCase):

    def test_veneto_pinned_to_italy(self):
        self.assertEqual(normalize_region("Veneto"), ("Veneto", "Italy"))

    def test_coastal_region_paarl_substring_match(self):
        canonical, country = normalize_region("Coastal Region Paarl")
        self.assertEqual(country, "South Africa")
        self.assertTrue(canonical)  # non-empty canonical region

    def test_country_name_in_region_slot_blanks_out(self):
        self.assertEqual(normalize_region("Portugal"), ("", None))

    def test_languedoc_no_hyphen(self):
        canonical, country = normalize_region("Languedoc Roussillon")
        self.assertEqual(canonical, "Languedoc-Roussillon")
        self.assertEqual(country, "France")


class TestNormalizeTags(unittest.TestCase):

    def test_region_country_mismatch_detected(self):
        parsed, issues = normalize_tags({
            "country": "USA",
            "region": "Veneto",
            "grapes": ["Pinot Grigio"],
            "is_blend": False,
        })
        self.assertIn("region_country_mismatch", issues)
        # USA → United States; Veneto stays Veneto pinned to Italy
        self.assertEqual(parsed["country"], "United States")
        self.assertEqual(parsed["region"], "Veneto")
        # Pinot Grigio → Pinot Gris
        self.assertEqual(parsed["grapes"], ["Pinot Gris"])

    def test_country_in_region_slot_flagged(self):
        parsed, issues = normalize_tags({
            "country": "Portugal",
            "region": "Portugal",
            "grapes": ["Touriga Nacional"],
        })
        self.assertIn("country_in_region_slot", issues)
        self.assertIsNone(parsed["region"])

    def test_placeholder_grapes_flagged_and_blend_preserved(self):
        parsed, issues = normalize_tags({
            "country": "France",
            "region": "Bordeaux",
            "grapes": ["Bordeaux Blend"],
            "is_blend": False,
        })
        self.assertIn("placeholder_grapes", issues)
        self.assertEqual(parsed["grapes"], [])
        self.assertTrue(parsed["is_blend"])

    def test_no_grapes_flagged(self):
        parsed, issues = normalize_tags({
            "country": "France",
            "region": "Bordeaux",
            "grapes": [],
        })
        self.assertIn("no_grapes", issues)

    def test_clean_input_produces_no_issues(self):
        parsed, issues = normalize_tags({
            "country": "France",
            "region": "Burgundy",
            "grapes": ["Pinot Noir"],
            "is_blend": False,
        })
        self.assertEqual(issues, [])
        self.assertEqual(parsed["country"], "France")
        self.assertEqual(parsed["region"], "Burgundy")
        self.assertEqual(parsed["grapes"], ["Pinot Noir"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
