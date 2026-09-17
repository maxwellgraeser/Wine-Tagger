# Scoring prompt verification — 2026-09-16/17

This checks the **uncommitted** scorer changes listed in `BATON-2026-09-16.md`:
- the "ABBREVIATED POS name" paragraph in `BATCH_MATCH_SCORE_PROMPT`
- the per-snippet `_name_coverage_note`, which is suppressed on list pages

Every replay below uses the logged snippets from run `20260915-221614`, scored in real batches through
`scorer._batch_match_score`. The model is local `llama-server` on :8080
(`bartowski/Qwen2.5-7B-Instruct-GGUF`, temperature 0). The threshold is 85 and the producer gate is on.
Blob splitting and containment dedupe run in `searcher.py`, so replaying logged snippets does not test
them.

**Nothing is committed.** `constants.py` has no net edits from this work; every prompt experiment was
reverted, and all 31 tests pass. The only repo edits are to `BATON-2026-09-16.md` and this note.

## Verdict

**Tags are accurate, so leave the scoring prompt as it is.** The new prompt drops a few correct
sources, but the tags on those wines didn't change. What did change is confidence: the tagger now gives
85 to most wines, which is exactly the review cutoff, so more correct tags land in `needs_review`. If
that becomes a burden, look at the confidence threshold or the tagger's confidence rubric. Don't tune
the scoring prompt further.

## 1. Baton edits

Under "Known-broken" in `BATON-2026-09-16.md`:
- **Cuvée conflicts.** Added a *Possible improvement*:
  - Flag a source that carries a qualifier the searched name lacks. Lower confidence or route the wine
    to `needs_review`. If the searched name contains the qualifier too, the source is fine.
  - Qualifier groups, where translations within a group count as a match: reserve, grand reserve,
    crianza/aging, cru/classification, old vines, site/selection, ripeness/sweetness, style variants.
  - Ignore qualifiers that are part of the producer's name (e.g. "Clos …"). Match regardless of
    accents and case.
  - Suggested implementation: a deterministic per-snippet note, like `_name_coverage_note`.
- **Score reproducibility and grape corroboration.** Added *Possible improvement: (none yet)*.

## 2. Snippet-score replay (24 wines)

A snippet counts as up or down when it crosses the 70 threshold. Result: **44 up, 7 down, 258
unchanged.**

**Bad promotion.** Neirano Barolo, Wine Searcher #2 is the Barolo *Riserva* page and went 0 → 90.
Wine Searcher #1 mixes the regular Barolo and the Riserva. Both wines are 100 % Nebbiolo, so the tag
is unaffected.

**Real regressions:**

| Wine | Snippet | Logged | New |
|---|---|---|---|
| Paul Buisse Touraine | CellarTracker #1, #2 | 90 | 50 |
| La Rioja Alta Ardanza | Region Q #1 | 85 | 65 |

**Acceptable drops:**
- Chapelle Bastion UPC #3 is a homepage (88 → 0).
- Li Veli Region Q is generic (70 → 55).
- Massaya UPC #2 mixes two rosés (70 → 60).
- Librandi CellarTracker #1 is a page covering several wines (70 → 65).

**Largest recoveries:**
- Bayten: 8 snippets
- Aster: 4
- Massaya: 4
- Cloudline: 3
- Curator White: 3
- Chocapalha: 3
- Li Veli, Urruzola, Bila Haut, Pav Chavannes and Chapelle Bastion: 2 each

## 3. Diagnosing the two regressions

- **Reproducible.** Repeated runs gave the same scores.
- **Caused by the new paragraph.** The committed HEAD code (`git archive HEAD`) reproduces the logged
  85 / 90 / 90.
- **The coverage note partly helps.** With the note turned off, Paul Buisse drops from 50 to 0.
- **Asking the model why is useless.** The 7B model's explanations of its scores are after-the-fact
  rationalizations.
- **Rewording the vintage clause made it worse, so it was reverted.**
  - Adding a "vintage report" sentence took Paul Buisse to 30; without that sentence it went to 0.
  - Other wordings gave Paul Buisse 55 or 30 and La Rioja Alta 65 or 70.
  - After the revert the scores were back at 65 / 50 / 50.

### Paragraph bisection

The paragraph split into four sentences:
1. The product name is abbreviated POS shorthand that drops the producer.
2. The three examples (Bila Haut, Bayten, Curator White).
3. A snippet naming a producer, a fuller cuvée name or a vintage is not thereby a different wine.
4. Treat it as a different wine only when something actually CONFLICTS.

The name-coverage note was on for every variant.

| Sentences kept | Rioja RQ #1 | Buisse CT #1 | Buisse CT #2 |
|---|---|---|---|
| none | 90 | 50 | 50 |
| 1 | 85 | 100 | 100 |
| 1, 2 | 85 | 95 | 95 |
| 1, 2, 3 | 75 | 55 | 55 |
| 1, 2, 3, 4 (one line) | 65 | 55 | 55 |
| 2, 3, 4 | 65 | 55 | 55 |
| 1, 3, 4 | 70 | 30 | 30 |
| 1, 2, 4 | 85 | 55 | 55 |
| 4 only | 90 | 0 | 0 |
| 3 only | 75 | 50 | 50 |

- **Sentences 1 and 2 help.** On their own they bring back roughly the committed scores.
- **Sentences 3 and 4 cause the drop.** Adding either one pulls Paul Buisse down to 55. Sentence 4 on
  its own scores Paul Buisse 0, and including it also lowers La Rioja Alta.
- **Formatting matters.** The full paragraph joined onto one line gives 55, while the real wrapped
  paragraph gives 50.
- **Some noise within one session.** Two variant names sent the identical prompt, and La Rioja Alta
  scored 75 once and 65 the other time.
- **Sentences 1 + 2 were not tested on the other 22 wines.** Sentences 3 and 4 may be what recovered
  wines such as Aster, Li Veli and Txakolina.

## 4. Tag replay (24 wines)

This re-ran scoring and tagging end to end with the current code: `score_and_assemble`, then
`tagger.infer_tags`, then `apply_evidence_rules` and `decide_tag_status`. It was a dry run with no
store writes, compared against `20260915-221614/final`.

**Same grapes (19 wines):**
- Vajra, Aster, Annabella, Chocapalha, Curator White, Neirano, Li Veli, Faustino VII, Tessellae
- La Rioja Alta (Tempranillo, Grenache), Paul Buisse (Sauvignon Blanc), Pav Chavannes, Bayten
- Librandi, Cloudline, Chapelle Bastion, Zenato, Massaya
- Vilafonte (same four grapes, different order)

**Different grapes:**

| Wine | Logged | New | Assessment |
|---|---|---|---|
| Bila Haut Roussillon | Carignan, Grenache, Cinsault; `needs_review`, all three unsupported | Syrah, Grenache, Carignan; `needs_review` (`single_source`), all supported | Better |
| Urruzola Txakolina Rosé | Hondarrabi Zuri, Hondarrabi Beltza; `needs_review` | No grapes, conf 50; `needs_review` | Worse, but it was already going to review |
| Mont Gravet Rosé | Cinsault | Cinsault, Carignan | Check it. Believed to be 100 % Cinsault; not verified |
| DV Catena Tinto | Malbec, Bonarda, Petit Verdot | adds Cabernet Franc | Plausible (vintage blends vary); not verified |

**Status changes, all caused by confidence and not by grapes:**

| Wine | Logged | New |
|---|---|---|
| Massaya Rosé | model, 86 | needs_review, 70 |
| Vilafonte Seriously Old Dirt | model, 88 | needs_review, 84 |
| Librandi Cirò Bianco | model, 88 | needs_review, 80 |
| Li Veli Passamante | needs_review, 80 | model, 90 |

**Confidence has collapsed toward 85.** These wines logged 95–98 and now score 85, right at the
threshold:
- Annabella
- Neirano
- Excelsior
- Cloudline
- Chapelle Bastion
- Zenato

Every wine except Bila Haut had 4–5 snippets in context.

## Follow-ups

- **Revise the draft commit message** in `BATON-2026-09-16.md` before committing. Its claims about
  regressions are out of date.
- **Check Mont Gravet Rosé (Carignan) and DV Catena Tinto (Cabernet Franc)** against a producer tech
  sheet.
- **If the extra reviews matter,** look at why the tagger now settles on 85 and at the threshold. Leave
  the scoring prompt alone.
- **Optional:** trim the paragraph to sentences 1 + 2 and replay all 24 wines. This is not
  recommended, given the verdict above.

The replay scripts (`verify.py`, `para_split.py`, `tagrun.py`) and their logs were in this session's
temporary scratchpad and are not kept in the repo.
