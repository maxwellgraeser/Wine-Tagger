# BATON — Library reseed (allowlist + placeholder tiers)

Status: **implemented on 2026-09-15.** This file records what was built,
where the plan changed versus the first draft, and what is left. The
design of record is `fermentation/PLAN.md` → "Reseed plan"; the
"Revisions" subsection there mirrors the list below.

## What changed versus the first draft of this baton

The first draft keyed everything on hand-typed Wikidata QIDs. Before
executing, every sample QID in it was checked against Wikidata:
**all of them were wrong** (Q170545 = phenylalanine, Q146048 = European
larch, Q220675 = an asteroid, Q204754 — the class the v1 `regions.rq`
was built on — is a commune in the Dordogne). The plan was reworked so
that humans author *names* and a machine resolves QIDs:

1. **Allowlists are keyed by name, not QID.** `seed/allowlist/*.yaml`
   carry `name`, `color`/`country`/`parent`/`classification`, `synonyms`.
   `seed/resolve_qids.py` resolves names → QIDs through the SPARQL
   endpoint's MWAPI EntitySearch (batched; the plain REST search API
   rate-limits bursts) and writes `seed/allowlist/qids.lock.yaml` with
   label + description per pick so a wrong pick is visible in a diff.
   A `qid:` on a YAML entry pins/overrides the resolver.
2. **Grape QIDs are required; region QIDs are optional.** Wikidata types
   grape varieties consistently (`Q958314`) but types wine regions as
   anything from "wine" (Barolo DOCG) to "valley" (Bekaa) to the
   namesake commune. So region hierarchy, country and classification are
   authored in `regions.yaml`; the QID only serves dedup against the
   placeholder pass and may be `null`.
3. **Colour is authored, not fetched.** Only 2 of ~2,400 grape-variety
   items on Wikidata carry P462. `grapes.yaml` has a `color` per entry
   and the Italian Wikipedia parser back-fills colour for placeholders.
4. **Placeholder filter = "has an English Wikipedia article".** The
   draft's `P225 "Vitis vinifera"` / `P366 wine` filter matches almost
   nothing (P225 is a taxon-name property). enwiki sitelink presence
   selects ~680 of ~2,440 grape-variety items and they are the real
   ones (Viognier, Graciano, Counoise…). Same filter for regions, over
   `wine-producing region` (Q2140699) and `AVA` (Q166247) subclasses,
   pinned to an allowlisted country.
5. **Wikipedia parsers are not QID-aware** — Parsoid HTML carries no
   `data-wikidata-item-id`. Instead `ingest_wikipedia` resolves regions
   and grapes by name/synonym against already-inserted rows and **never
   mints rows**, which is what actually caused the v1 duplicates.
6. **`is_placeholder` split.** `lookup_grape` now returns `is_phrase`
   (filler like "Bordeaux Blend") and `is_placeholder` (real but
   non-canonical). `lookup_region` gained `is_placeholder` and
   `classification`.
7. **`submit_tags` is now a real gate.** New issue codes
   `unknown_country`, `unknown_region`, `non_canonical_region`,
   `placeholder_grape` (and `placeholder_grapes` → `phrase_grapes`).
   Unknown regions no longer pass through as free text. Hints name the
   offending values. Regions are expanded with their parent chain and
   country is inferred from regions when omitted.
8. **Server resolves from in-memory folded indexes** built at startup —
   closes the "full-table scan per miss" finding in `Tree.html`.
9. **Scope adds:** `country_synonyms` table (USA/US/U.S. …);
   `region_synonyms` as planned; validator enforces global uniqueness of
   region labels (it caught "WA" = Washington *and* Western Australia).
10. **Rebuild, don't migrate.** `build_db.py` writes to a temp file and
    renames over `library.db`; schema header says so.
11. **DDG import fixed** (`Tree.html` finding #1): `searcher.py` imports
    `ddgs` (pinned; the legacy `duckduckgo-search` fallback was removed
    because it emits a rename warning on every query) and raises loudly if
    it is missing.

## Files

```
fermentation/library_mcp/
  schema.sql                     is_canonical cols, country_synonyms, region_synonyms
  server.py                      in-memory index, canonical-first, new issue codes
  seed/build_db.py               allowlist-driven; placeholder pass; atomic rebuild
  seed/resolve_qids.py           name -> QID resolver, writes qids.lock.yaml
  seed/allowlist/__init__.py     loader + validator (AllowlistError lists every problem)
  seed/allowlist/countries.yaml  46, keyed by ISO (QID from P297 at build time)
  seed/allowlist/grapes.yaml     335, with colour + synonyms
  seed/allowlist/regions.yaml    675, with hierarchy + synonyms
  seed/allowlist/qids.lock.yaml  generated; review the `note:` fields
  seed/wikipedia/*.py            enrichment only (no minting)
  tests/test_allowlist.py        offline structural tests
  tests/test_combined_csv_coverage.py   24 test wines resolve canonically
  tests/test_server_gate.py      tiers, synonyms, issue codes
```
`seed/sparql/*.rq` (v1 firehose) are deleted.

## Build result (2026-09-15)

| table     | canonical | placeholder | synonyms |
|-----------|-----------|-------------|----------|
| countries | 46        | 0           | 223      |
| regions   | 675       | 275         | 674      |
| grapes    | 335       | 375         | 658      |

Plus 208 `region_grapes` edges from the Italian Wikipedia list, which
also filled colour on 87 placeholder grapes. Build time ~25 s. All 48
tests in `fermentation/library_mcp/tests/` pass; the 24-wine coverage
test resolves every country / region / grape canonically and passes
each row through `submit_tags`.

Four niche grapes were dropped from the canonical list because Wikidata
has no item for them (Tsitska, Voskehat, Melnik, Emir); Teran, Šipon,
Heida and Ormeasco became synonyms because Wikidata conflates them with
Refosco, Furmint, Savagnin and Dolcetto.

## How to re-seed

```bash
.venv/bin/python -m fermentation.library_mcp.seed.resolve_qids   # after editing grapes/regions YAML
.venv/bin/python -m fermentation.library_mcp.seed.resolve_qids --report
.venv/bin/python -m fermentation.library_mcp.seed.build_db        # ~2-3 min, needs network
.venv/bin/python -m pytest fermentation/library_mcp/tests
```
Commit the regenerated `library.db` and `qids.lock.yaml` together.

## Left open

- Review every `note: != ok` line in `qids.lock.yaml`
  (`resolve_qids.py --report` prints them). Wrong grape picks matter
  (they pull in the wrong altLabel synonyms); wrong region picks only
  affect dedup.
- Placeholder-region pass can still admit a placeholder that is the
  appellation twin of a canonical commune-keyed region (e.g. "Fixin AOC"
  next to canonical "Fixin"). Suffix-stripped collision check in
  `ingest_placeholder_regions` mitigates; watch `lookup_region` output.
- Tree.html findings not in this baton: confidence threshold (90 vs the
  prompt's 84 cap), snippet cache, MCP subprocess restart, `run.sh`,
  `tag_log` bloat, duplicated rubric text.
