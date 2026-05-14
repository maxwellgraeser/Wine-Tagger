#!/usr/bin/env python3
"""
Unit tests for two guarantees:
  1. UPC SKUs (like those in combined.csv) are included in DDG search queries.
  2. Top-scoring snippets are passed into the tagging LLM prompt.

No network calls, no LLM calls — all external I/O is mocked.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

sys.path.insert(0, str(Path(__file__).parent.parent))
import curate
from curate import (
    _is_upc,
    build_web_context,
    gather_all_snippets,
    infer_tags,
    score_snippets,
)
from constants import SNIPPET_MATCH_THRESHOLD, TOP_N_SNIPPETS

# ---------------------------------------------------------------------------
# Real SKUs from combined.csv — these must be treated as UPCs
# ---------------------------------------------------------------------------
REAL_SKUS = [
    "703432000395",   # Annabella Pinot Noir
    "890841002109",   # Aster Ribera del Duero
    "6001398115868",  # Bayten Sauvignon Blanc
    "810047050032",   # Bila Haut Roussillon
]

SAMPLE_PRODUCT = {
    "id": "test-id-001",
    "name": "Annabella Pinot Noir",
    "sku": "703432000395",
    "brand_name": "",
    "product_category": "Red",
}


# ---------------------------------------------------------------------------
# 1. SKU detection
# ---------------------------------------------------------------------------
class TestIsUpc(unittest.TestCase):

    def test_real_skus_are_recognized_as_upc(self):
        for sku in REAL_SKUS:
            with self.subTest(sku=sku):
                self.assertTrue(_is_upc(sku), f"Expected {sku!r} to be treated as a UPC")

    def test_non_numeric_sku_is_not_upc(self):
        for sku in ["WW-1234", "AB-RED-001", "handle-slug", ""]:
            with self.subTest(sku=sku):
                self.assertFalse(_is_upc(sku), f"Expected {sku!r} NOT to be a UPC")


# ---------------------------------------------------------------------------
# 2. SKU appears in DDG queries for UPC products
# ---------------------------------------------------------------------------
class TestGatherAllSnippetsUsesSku(unittest.TestCase):

    def _run_gather(self, product):
        """Run gather_all_snippets with a mocked ddg_snippets, return all queries issued."""
        issued_queries = []

        def fake_ddg(query):
            issued_queries.append(query)
            return ["stub snippet"]

        with patch.object(curate, "ddg_snippets", side_effect=fake_ddg):
            with patch("time.sleep"):
                gather_all_snippets(product)

        return issued_queries

    def test_upc_sku_appears_in_at_least_one_query(self):
        queries = self._run_gather(SAMPLE_PRODUCT)
        sku = SAMPLE_PRODUCT["sku"]
        sku_queries = [q for q in queries if sku in q]
        self.assertTrue(
            len(sku_queries) > 0,
            f"SKU {sku!r} was never included in any DDG query.\nAll queries:\n" +
            "\n".join(f"  {q}" for q in queries),
        )

    def test_non_upc_sku_does_not_appear_in_queries(self):
        product = {**SAMPLE_PRODUCT, "sku": "WW-1234"}
        queries = self._run_gather(product)
        self.assertFalse(
            any("WW-1234" in q for q in queries),
            "Non-UPC SKU should not appear in any DDG query",
        )

    def test_product_name_always_appears_in_queries(self):
        queries = self._run_gather(SAMPLE_PRODUCT)
        name = SAMPLE_PRODUCT["name"]
        self.assertTrue(
            any(name in q for q in queries),
            f"Product name {name!r} should appear in at least one query",
        )


# ---------------------------------------------------------------------------
# 3. build_web_context selects top-N snippets above threshold
# ---------------------------------------------------------------------------
class TestBuildWebContext(unittest.TestCase):

    def _make_snippets(self, scores):
        return [
            {"source": f"src-{i}", "domain": "example.com",
             "snippet": f"snippet text {i}", "match_score": s}
            for i, s in enumerate(scores)
        ]

    def test_below_threshold_snippets_are_excluded(self):
        snippets = self._make_snippets([90, 40, 30])  # only first passes 85 threshold
        ctx = build_web_context(snippets)
        assert ctx is not None
        self.assertIn("snippet text 0", ctx)
        self.assertNotIn("snippet text 1", ctx)
        self.assertNotIn("snippet text 2", ctx)

    def test_top_n_limit_is_respected(self):
        # More passing snippets than TOP_N_SNIPPETS
        scores = [90, 88, 87, 86, 85]
        snippets = self._make_snippets(scores)
        ctx = build_web_context(snippets)
        assert ctx is not None
        # Count how many snippet bodies appear in context
        included = sum(1 for i in range(len(scores)) if f"snippet text {i}" in ctx)
        self.assertLessEqual(included, TOP_N_SNIPPETS)

    def test_snippets_ordered_by_score_descending(self):
        snippets = self._make_snippets([86, 95, 90])  # index 1 is highest
        ctx = build_web_context(snippets)
        assert ctx is not None
        pos_best = ctx.index("snippet text 1")   # score 95
        pos_second = ctx.index("snippet text 2")  # score 90
        self.assertLess(pos_best, pos_second, "Highest-scoring snippet should appear first")

    def test_no_passing_snippets_returns_none(self):
        snippets = self._make_snippets([10, 20, 30])
        self.assertIsNone(build_web_context(snippets))

    def test_match_score_label_present_in_context(self):
        snippets = self._make_snippets([92])
        ctx = build_web_context(snippets)
        assert ctx is not None
        self.assertIn("match=92", ctx)


# ---------------------------------------------------------------------------
# 4. Top snippets reach the tagging LLM prompt
# ---------------------------------------------------------------------------
class TestInferTagsReceivesSnippets(unittest.TestCase):

    SNIPPETS = [
        {"source": "Wine Searcher #1", "domain": "wine-searcher.com",
         "snippet": "Annabella Pinot Noir from California Napa Valley", "match_score": 95},
        {"source": "Vivino #1", "domain": "vivino.com",
         "snippet": "Rich Pinot Noir with dark cherry notes", "match_score": 88},
    ]

    def test_snippet_text_appears_in_llm_prompt(self):
        web_context = build_web_context(self.SNIPPETS)
        captured_prompts = []

        def fake_llm(prompt, api_url, model, timeout=60):
            captured_prompts.append(prompt)
            return '{"country": "USA", "region": "Napa Valley", "grapes": ["Pinot Noir"], "is_blend": false, "organic": false, "confidence": 90}'

        with patch.object(curate, "call_llm", side_effect=fake_llm):
            parsed, prompt, raw = infer_tags(SAMPLE_PRODUCT, web_context,
                                             api_url="http://localhost:8080/v1/chat/completions",
                                             model="test-model")

        self.assertTrue(len(captured_prompts) > 0, "LLM was never called")
        tagging_prompt = captured_prompts[0]

        # The actual snippet text must be in the prompt
        self.assertIn("Annabella Pinot Noir from California", tagging_prompt,
                      "Top snippet text not found in tagging LLM prompt")

    def test_no_web_context_reaches_llm_as_none_string(self):
        captured_prompts = []

        def fake_llm(prompt, api_url, model, timeout=60):
            captured_prompts.append(prompt)
            return '{"country": "USA", "region": "Napa", "grapes": ["Pinot Noir"], "is_blend": false, "organic": false, "confidence": 30}'

        with patch.object(curate, "call_llm", side_effect=fake_llm):
            infer_tags(SAMPLE_PRODUCT, None,
                       api_url="http://localhost:8080/v1/chat/completions",
                       model="test-model")

        self.assertIn("none", captured_prompts[0].lower(),
                      "When web_context is None, prompt should indicate no context")


if __name__ == "__main__":
    unittest.main(verbosity=2)
