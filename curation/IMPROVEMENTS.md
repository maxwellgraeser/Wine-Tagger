# Curation Accuracy — Improvement Backlog

Ranked by likely ROI based on the 24-wine `test/test2.txt` run. Items 1 and 2 from the original brainstorm are already implemented:

- **Done** — grapes are constrained to `CANONICAL_GRAPES` in the inference prompt; any non-canonical grape returned by the model triggers a `non_canonical_grape` normalization issue and forces `needs_review`.
- **Done** — `is_blend` is reconciled mechanically against the cleaned grape list (1 grape → False, 2+ → True). When the LLM's declared value disagrees with the count, `is_blend_mismatch` is added to the issues list and the row is flagged for review.

The remaining ideas are tracked here.

---

## 3. Producer-name verification gate (high ROI)

**Problem.** The Zenato Pinot Grigio failure: a `cellartracker.com` UPC-scoped DDG result returned a snippet whose preview text was actually about *La Rioja Alta* (likely because the UPC didn't map cleanly on CellarTracker and the page rendered an unrelated recent review). The scoring LLM gave it `match=95` because the snippet "looked wine-shaped" (vintage, score, region words), even though it contained zero tokens from the product name. That bogus context then drove the tag inference for an unrelated wine.

**Fix.** Before accepting any snippet's match score, run a deterministic post-check: at least one significant token from the product name OR the `brand_name` column must appear in the snippet body (case-insensitive, after stripping accents). If not, override the score to 0 (or drop the snippet outright). This is cheap, requires no extra LLM call, and would have killed the Zenato/Rioja contamination instantly.

Implementation sketch: in `score_snippets`, after the LLM returns scores, loop again and zero out scores for snippets missing the producer/brand token. Add a CLI flag to disable for debugging.

## 4. Snippet boilerplate stripping (high ROI)

**Problem.** Many "match=95" snippets in `test2.txt` are mostly navigation or CMS boilerplate, not wine information:
- `"Sort by Default Sort by Name Sort by Vintage..."` (Chapelle Bastion)
- `"NOTE: Some content is property of JancisRobinson.com and Vinous. Add a Pro Review..."` (Aster Ribera)
- `"Add Your Own Reviews: Wi..."` (Tessellae Old Vines)
- `"$ 39.99 ex. sales tax 2019 Bottle (750ml)..."` (Vajra Barolo)

These crowd the top-3 context pool and starve the tag-inference LLM of real evidence.

**Fix.** Add a `clean_snippet` step before scoring that:
- Strips known boilerplate phrases (`"Add Your Own Reviews"`, `"Sort by"`, `"NOTE: Some content"`, `"Add a Pro Review"`, etc.).
- Drops snippets where >60% of the text is the cleaned-out boilerplate (so the remaining content is too thin to score).
- Optionally rejects snippets whose only "wine" content is a price tag.

A blocklist of phrases per source (CellarTracker, Vivino, Wine Searcher have distinct UI chrome) would catch most of it.

## 5. Pass brand into the inference prompt body, not just the search query (medium ROI)

**Problem.** The prompt already takes `brand` as a `{brand}` slot, but the search-side use of brand is fine — what's worth checking is whether the producer-absent confidence cap (max 69) is actually firing. Several wines (DV Catena, Curator White) appear to have shipped at `confidence=95` with implausible grape lists, suggesting the model is treating the brand as "present" via the prompt header even when no snippet actually mentions it.

**Fix.** Move the producer-absent check out of the LLM's hands and into normalization: after `infer_tags`, scan `web_context` for the brand token; if absent, cap `confidence` at 69 deterministically and add a `producer_absent_from_context` issue. The current rubric relies on the model to self-police, and it does not.

## 6. Two-tier model (medium ROI, low effort to A/B)

**Problem.** `gemma3n:e4b` is small. The silent failures (Curator White "Pin Blanc", La Rioja Alta "Eigen", Mont Gravet "Other", DV Catena's improbable five-grape blend) are reasoning-side errors that a larger model would likely avoid.

**Fix.** Keep `gemma3n:e4b` for snippet match scoring — it's a high-volume, low-reasoning task and the current model is fine there. For the single tag-inference call per wine, try `gemma3:12b` or `qwen2.5:14b` as a one-line `--inference-model` override. Cost is one bigger forward pass per wine, ~5–15s extra; quality lift on hallucinated grapes should be large.

## 7. Few-shot examples in PROMPT_TEMPLATE (medium ROI)

**Problem.** The rubric tells the model when to be uncertain but doesn't *show* it. Conservative behavior ("leave grapes empty if unclear") is easier to elicit by example than by rule.

**Fix.** Add 2–3 anchored examples to `PROMPT_TEMPLATE`:
- One clean case (strong producer match, two corroborating snippets) → high-confidence full tags.
- One ambiguous case (snippet mentions region but no grape) → `grapes: []`, `confidence: 55`.
- One contaminated case (snippet text doesn't mention the producer at all) → `grapes: []`, `confidence: 35`.

Risk: prompt length grows. Worth measuring whether the local model latency is still acceptable.

## 8. Phase 3 — LLM review pass (already planned in REVIEW.md)

**Problem.** Even with items 1–7, some rows will land in `needs_review`. Manually triaging every flag does not scale.

**Fix.** Implement `REVIEW.md` as designed: a second LLM call, constrained to the canonical vocabulary, fed the stored `web_context` and the specific normalization issues, asked to re-produce tags. Items 1–2 already make this safer because the canonical vocab is now enforced on both passes.

---

## Investigation note — Zenato/Rioja Alta mixup

Filing here because it was the proximate trigger for this audit:

- **Mechanism.** Not LLM context bleed. Every `call_llm` invocation in `curate.py` sends a fresh `messages=[{"role":"user", "content": prompt}]` payload with no conversation history, no `session_id`, no system message. Ollama's `/v1/chat/completions` is stateless. There is no path by which the prior wine's content can leak into the next wine's inference.
- **Actual cause.** A site-scoped UPC DDG query (`site:cellartracker.com "{zenato_upc}"`) returned a CellarTracker page whose DDG preview text happened to be the most recent community review on that page, which was about *La Rioja Alta* — not Zenato. The 300-char scoring snippet contained no producer token at all, so there was nothing for the scoring LLM to anchor against. It scored the snippet 95 anyway because the text was vintage-and-points shaped.
- **Why the existing safeguards missed it.** The `producer absent → max 69 confidence` rule lives in the *tag-inference* prompt, not in scoring. The snippet entered the top-3 pool before that rule applied. Items 3 (producer gate) and 5 (deterministic confidence cap) are the direct fixes.
