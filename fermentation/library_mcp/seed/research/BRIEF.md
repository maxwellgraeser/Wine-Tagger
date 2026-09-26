# Research brief: wine regions and grapes for one scope

You are building reference data for a wine-tagging library. Your scope,
slug and any scope notes are in your prompt. Read this whole brief first.

## Context

Repo root: `/Users/mgraeser/Documents/Wine Warehouse DDD`. The library is a
SQLite DB built from hand-curated YAML allowlists
(`seed/allowlist/regions.yaml` and `grapes.yaml`). Don't read those files,
the validator or the journal. Two helper scripts give you what you need
(run them from the repo root):

- `.venv/bin/python -m fermentation.library_mcp.seed.research.context <slug>`
  prints the conventions header of `regions.yaml`, every existing entry for
  your country or countries (one line each), and the other research slices
  for the same country with their status.
- `.venv/bin/python -m fermentation.library_mcp.seed.research.context --grape NAME…`
  and `--region NAME…` look names up (ignoring case and accents) across the
  allowlists and every research file, and print each match with its file,
  or "not found". Use them before adding a grape or a synonym.

A tagger LLM reads web snippets about a wine and calls
`lookup_region("Robertson Valley")`. That call matches exactly, ignoring
only case, accents and extra spaces, against region names and synonyms.
If nothing matches, the wine loses its region. Before this work the
library had `Robertson` but not "Robertson Valley", and that is exactly how
a wine lost its region. **The names people actually write on labels and
retailer pages matter as much as the list of regions itself.**

The lookup code already handles these cases, so do not add them as
synonyms:

- Classification words at either end: DOC, DOCG, DO, DOCa, AOC, AOP, AVA,
  DAC, WO, GI, IGT, IGP, PDO, PGI, VQA, "Vinho Regional", "Vin de Pays",
  "Vino de la Tierra", "Wine of Origin", "Qualitätswein", "Grand Cru",
  "Premier Cru" / "1er Cru", and "Appellation X Contrôlée".
- Comma-separated compounds ("Napa Valley, California, USA").
- Case, accents and repeated spaces.

## When a country is split across agents

The US, France, Italy and Spain are each split into slices that run at the
same time. If your prompt names a slice:

- Produce entries **only for the areas your slice owns**. Include the
  existing library entries in those areas, and nothing from other slices.
- You may use a region owned by another slice as a `parent` if it is
  already in `regions.yaml` (Burgundy, Piedmont, Castilla y León). Use its
  exact existing name. Never re-list it.
- Grapes: add the grapes whose home is in your areas. If a grape is shared
  with another slice's area, add it only if your areas are its main home.
  The merge keeps the first entry and reports duplicates.

## What to produce

Write exactly three files into `fermentation/library_mcp/seed/research/`,
named with your slug. Do not edit any other file in the repo, do not run
the build, and do not touch the allowlists. Other agents are writing their
own files in the same folder at the same time.

### 1. `<slug>.regions.yaml`

A YAML list, one flow-style mapping per line, in the `regions.yaml` format
plus research-only keys:

```yaml
- {name: "Robertson", country: ZA, parent: "Breede River Valley", classification: District, synonyms: ["Robertson Valley", "Robertson Wine Valley"], source: "https://..."}
- {name: "Chinon", country: FR, parent: "Touraine", classification: AOC, synonyms: [], grapes: ["Cabernet Franc", "Chenin Blanc"], source: "https://..."}
```

**Coverage**
- Include every appellation of the official scheme in your scope, at the
  levels labels use.
- Then add the protected regional tier (IGP / IGT / Vino de la Tierra /
  Vinho Regional).
- Then add informal names the trade relies on (Uco Valley, Sonoma Coast,
  Bekaa).
- Include every existing library entry for your scope, so your file is the
  complete set for that scope. Keep existing names unless they are wrong.
- If you rename an entry, add `was: "<old name>"`. Explain every rename or
  re-parent in the `.md`.

**Names**
- Use the retail-facing English form where one exists (Burgundy, Piedmont,
  Tuscany). Otherwise use the official local name with its diacritics.

**Hierarchy**
- `parent` is the nearest enclosing viticultural unit, not an
  administrative one.
- It must name another entry in your file, or an existing library region
  in the same country.
- A sub-appellation is always a child entry, never a synonym of its
  parent.
- Separate AOCs are separate entries: a Grand Cru that is its own
  appellation is not a synonym of its village.
- **One parent per entry.** When units overlap, pick the nesting a
  retailer would describe (Russian River Valley < Sonoma County < North
  Coast < California) and note the other in the `.md`.
- **Overlay designations** (blending or overarching zones that cut across
  the main hierarchy, such as WO Cape Coast) get **no children** unless
  labels treat them as the parent. The tagger adds every ancestor to a
  wine's region list, so a wrong parent pollutes every wine below it.
- Where the official name is a compound ("Paardeberg/Perdeberg"), use one
  part as `name` and the other as a synonym.

**`classification`**
- Use the scheme's own term: AOC, IGP, DOCG, DOC, IGT, DO, DOCa, VP, AVA,
  DAC, GI, PDO, PGI, and so on. Follow the existing convention for your
  country in `regions.yaml`.
- Leave it out for informal areas.

**`synonyms`**
- Only names someone would actually write for this place:
  - the local-language form and the English form
  - the form without diacritics, and hyphen / space variants
  - transliterations
  - former names
  - "X Valley" / "Valle de X" forms, only where the trade uses them
- Every synonym must be one you have seen used. Do not generate
  permutations.
- Do not use a synonym that is also a producer or brand name on labels.
  The tagger would read the producer as a place.
- Within one country, a synonym may not equal another entry's name or
  synonym.
- The same name may exist in another country (La Rioja: Spain and
  Argentina). That is allowed, but list it in the `.md`.

**`grapes`**
- Only for appellations whose rules name the permitted or principal grapes
  (AOC/AOP, DOC/DOCG, DO/DOCa, DAC, PDO, and similar).
- List the principal varieties the rules name, not every minor permitted
  one.
- Use names that exist in `grapes.yaml` (canonical or synonym), or a grape
  you add in your grapes file.
- Leave it out for AVAs, WO units, Australian/NZ GIs and informal areas,
  which have no grape rules.

**`source`**
- The URL you used for that entry. Use the official register first, then
  the national wine body, then Wikipedia.

**No `qid:`**
- Wikidata IDs are resolved later by a script. Hand-typed ones were all
  wrong last time.

### 2. `<slug>.grapes.yaml`

The same flow-style format as `grapes.yaml`, plus `source:`.

**New grapes** go in as `{name, color, synonyms, source}`:
- These are grapes not in `grapes.yaml` under any name or synonym, that
  are native to or important in your scope, and appear on commercial
  labels.
- `color` is one of red, white, rose, gris.

**Existing grapes that have local names not yet listed** go in as
`{name: "<canonical name exactly as in grapes.yaml>", existing: true, synonyms: [<only the new ones>], source: "..."}`.

**Identity**
- Grape identity follows VIVC (Vitis International Variety Catalogue,
  vivc.de).
- A shared name does not mean a shared grape. The Malvasias, Muscats,
  Trebbianos and "Riesling"s are several distinct varieties. When in
  doubt, flag it in the `.md` instead of guessing.

**Collisions**
- A synonym must not collide with another grape's name or synonym in
  `grapes.yaml`. Check this.
- **No place names as grape synonyms**, even historically correct ones.
  "Hermitage" was once the Cape name for Cinsault, but on a modern page it
  means the Rhône AOC, and it would make every Hermitage snippet look like
  Cinsault evidence. List such names in the `.md` instead.
- Keep new grapes even if you suspect Wikidata has no item for them. The
  merge step drops the ones it can't resolve and records that.

**Scope**
- International grapes belong in this file only to record a local synonym
  (Spätburgunder, Tinta Roriz).

### 3. `<slug>.md`

- The sources you used (URLs), with the date or version of each official
  list. **Read the official register itself** where one exists, not a
  summary of it. The pilot found Wikipedia's South African table about 30
  wards out of date. For a PDF, download it with `curl` into your download
  folder, convert it with `pdftotext -layout`, then `grep` for what you
  need. Never open a PDF with the Read tool.
- **Counts:** official units per level vs how many you produced, and
  anything official you left out, with the reason.
- **Changes to existing entries:** renames, re-parents, and dropped or
  changed synonyms, each with a one-line reason.
- **Homonyms:** names in your scope that also name a wine region in another
  country.
- **Uncertain calls:** parent, identity or grape-rule decisions you are
  not sure about, with what you found.
- **20–25 "label string → canonical" pairs**, as they actually appear on
  real retailer pages or labels. Mix regions and grapes, and prefer messy
  real-world forms. Each label string must be a name someone could pass to
  `lookup_region` or `lookup_grape` on its own: a region or grape name,
  not a wine or cuvée name. "Hoe-Steen" is a wine; "Steen" is the grape. Format them as a markdown table with the columns:
  label string | kind (region/grape) | canonical | where seen (URL).

## Saving progress

Runs can be cut off by usage limits.
- **Write early.** Create your three files as soon as you have the first
  sub-area done, then append sub-area by sub-area. Never hold everything
  for one write at the end.
- **Resume if files exist.** If files for your slug are already in the
  research folder from an earlier interrupted run, read them first and
  continue from where they stop. Do not start over.
- Add a line `Status: in progress (<what is done>)` at the top of your
  `.md` while you work. Change it to `Status: complete` when you finish.

## Mistakes reviewers have removed

Check your files for these patterns; each one was caught in review.

- A place name as a grape synonym: `Hermitage` (Cinsault).
- A wine or style name as a grape synonym: `Gamay Beaujolais` (Pinot Noir).
- A person's name as a grape synonym: `Romain` (César).
- An ambiguous bare name: `Albillo` (on Ribera labels it means Albillo
  Mayor, not Albillo Real).
- Distinct varieties merged: `Malvasia di Schierano` as a synonym of
  Malvasia di Casorzo.
- Classification words in a name: `delle Venezie IGT`, `IGP Val de Loire`.
- Sub-appellations folded in as synonyms of their parent, and overlay zones
  given children.

## Before you finish

Run the checker from the repo root:

```sh
.venv/bin/python -m fermentation.library_mcp.seed.research.check <slug>
```

It must report no errors. Explain in the `.md` any warning that remains.

End with a short report:
- the counts you produced
- the three biggest changes to existing entries
- the open questions you flagged
