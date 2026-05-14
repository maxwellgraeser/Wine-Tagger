# Phase 3 — LLM Review Pass

## Purpose

The grape / country / region libraries (see LIBRARY.md) catch the bulk of
data-quality issues deterministically: synonym drift, placeholder grapes, and
hard region/country mismatches. They cannot catch errors that need
*judgement* — an appellation mistaken for a grape (e.g. `Cirò Bianco` as a
varietal), a vague region that's technically valid but too coarse
(`Portugal` as a region, `California` for a wine that's clearly Napa), or a
grape that's plausible-but-wrong for the region.

Phase 3 is a separate, optional pass that runs the local LLM as a *reviewer*
over rows the deterministic layer flagged for review (or, in batch mode, over
the entire current curation run). The reviewer sees the canonical lists from
LIBRARY.md and is constrained to either confirm the existing tags or propose
corrections drawn from those lists.

This document is the plan for that pass. The script does **not** exist yet.

## Scope

In scope:
- Re-tagging rows where `tag_status = 'needs_review'`.
- Surfacing region/country mismatches the library couldn't auto-resolve.
- Replacing appellations-as-grapes (Cirò Bianco → Greco Bianco) when the
  appellation pins a known grape.
- Tightening too-coarse regions when the web context supports it.

Out of scope:
- Re-querying the web. Phase 3 uses the existing `web_context` stored in
  `wines.db` — same evidence the Phase 2 LLM saw, different prompt.
- Changing `confidence` upward. The reviewer can lower it, never raise it.
- Touching `tag_status = 'manual'` rows. They are owned by a human.

## Inputs

- `curation/output/wines.db` — read products + the `web_context` they were
  tagged from.
- The canonical lists from `grape_library.py`, `country_library.py`,
  `region_library.py` — serialized into the prompt as a constrained vocabulary.

## Selection of rows

By default: every row where `tag_status = 'needs_review'`.

CLI overrides:
- `--all` — review every `'auto'` and `'reviewed'` row too.
- `--issue <name>` — limit to rows whose last normalization left a specific
  issue tag (e.g. `--issue region_country_mismatch`). Requires the issue list
  to be persisted alongside the row (see Schema change below).
- `--limit N` — cap the run (consistent with curate.py).

## LLM prompt strategy

One call per row. The prompt has four sections:

1. **The product** — name, brand, category, current tags
   (`country`, `region`, `grapes`, `is_blend`).
2. **The evidence** — the `web_context` block stored in `products.web_context`.
3. **The vocabulary** — compact dumps of the three libraries:
   ```
   Allowed countries: United States, France, Italy, Spain, Portugal, ...
   Allowed regions (region → country):
     Barolo → Italy
     Veneto → Italy
     Rioja → Spain
     ...
   Allowed grapes: Shiraz, Cabernet Sauvignon, Pinot Noir, ...
   ```
4. **The task**:
   > Decide whether the current tags are correct given the evidence. If they
   > are, return them unchanged. If they are wrong, return corrected tags
   > drawn **only** from the allowed lists above. If the evidence is
   > insufficient, set `verdict = "abstain"` and leave the tags as-is. Return
   > JSON only.

Response schema:

```json
{
  "verdict": "confirm" | "correct" | "abstain",
  "country": "...",
  "region": "...",
  "grapes": ["...", "..."],
  "is_blend": true | false,
  "reasoning": "one short sentence; goes into tag_log only"
}
```

Hard rules baked into the prompt:
- A region implies its country; if you choose `Veneto`, `country` must be `Italy`.
- Never invent a grape outside the allowed list. If the true grape isn't in
  the list, return `verdict = "abstain"`.
- An appellation is not a grape. If the current grape is the same string as
  the current region, this is almost certainly an appellation-as-grape bug —
  replace it.

## Output

For each row:

- `verdict = "confirm"` → update `tag_status = 'reviewed'`. No tag changes.
- `verdict = "correct"` → overwrite `country / region / grapes / is_blend /
  tags_raw`. Set `tag_status = 'reviewed'`. Log the diff and reasoning to
  `tag_log` with a marker (`source = 'review'`).
- `verdict = "abstain"` → leave `tag_status = 'needs_review'`. Log the
  abstention so the human reviewer can see Phase 3 also gave up.

The reviewer's output is itself piped through `normalize_tags` before commit,
so it can't reintroduce drift.

## Schema change

To filter by issue (`--issue region_country_mismatch`), the issue list from
`normalize_tags` needs to live alongside the row:

```sql
ALTER TABLE products ADD COLUMN review_issues TEXT;  -- JSON array, NULL if clean
```

Written from `curate.py` at the same point `tag_status` is set. Cleared when
`tag_status` becomes `'reviewed'` or `'manual'`.

The `tag_log` table gains a column to distinguish phases:

```sql
ALTER TABLE tag_log ADD COLUMN phase TEXT DEFAULT 'tag';  -- 'tag' | 'review'
```

## Alternative: batch consistency pass

Instead of one review call per row, gather every distinct `(country, region,
grape)` tuple in the DB and send them to the LLM as a single audit list:

> Here are the (country, region, grape) tuples in our catalog. Flag any that
> are internally inconsistent or wildly unusual. Suggest a fix per flag.

One call covers hundreds of rows; the model's response drives a follow-up
per-row update.

Trade-off: a per-row pass uses each row's `web_context` (more evidence per
decision); a batch pass uses no evidence but is dramatically cheaper. Likely
direction: per-row for `needs_review`, batch for the wider `auto` population
when we want a sanity sweep.

## Open questions

| # | Question | Tentative answer |
|---|----------|------------------|
| 1 | Should the reviewer be allowed to change `confidence`? | Lower only. Phase 3 is conservative — it never inflates LLM certainty. |
| 2 | Re-query the web for `needs_review` rows where `web_context` is empty? | Not in Phase 3 — that's a Phase 1 concern. Phase 3 abstains on missing evidence. |
| 3 | Per-row or batch as the default? | Per-row for the first cut. Add batch as a `--mode batch` flag if cost becomes an issue. |
| 4 | What if the reviewer disagrees with itself across runs? | Persist the last `verdict` + `reasoning` in `tag_log`; surface flapping rows during human review. |
