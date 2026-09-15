# BATON — Library reseed implementation

Pick this up by re-reading `fermentation/PLAN.md` (esp. the "Reseed plan
— Hybrid allowlist + filtered firehose" section near the bottom). This
file is the working state of the implementation. Tasks 1–8 already
exist in the task list (`TaskList` to see them).

## What's done

- Plan written and appended to `PLAN.md` (the "Reseed plan" section +
  "Coverage notes — `curation/test/combined.csv`" subsection).
- Tasks 1–8 created for tracking the implementation.
- Read the current state of:
  - `fermentation/library_mcp/schema.sql`
  - `fermentation/library_mcp/server.py` (full)
  - `fermentation/library_mcp/seed/build_db.py` (full)
  - `fermentation/library_mcp/seed/wikipedia/__init__.py`
  - `fermentation/library_mcp/seed/wikipedia/italy.py`
  - `fermentation/library_mcp/seed/wikipedia/germany.py`
  - `fermentation/library_mcp/seed/sparql/{countries,regions,grapes}.rq`
  - `requirements.txt`

## What's NOT done — execution plan

Work in this order. Each phase is one of the existing tasks.

### Task 1 — Schema + region_synonyms (start here)

Edit `fermentation/library_mcp/schema.sql`:

- Add `is_canonical INTEGER NOT NULL DEFAULT 0` to `countries`,
  `regions`, `grapes`.
- Add new table:

```sql
CREATE TABLE IF NOT EXISTS region_synonyms (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id  INTEGER NOT NULL REFERENCES regions(id) ON DELETE CASCADE,
    synonym    TEXT    NOT NULL,
    UNIQUE (region_id, synonym)
);
CREATE INDEX IF NOT EXISTS idx_region_synonyms_nocase
    ON region_synonyms (synonym COLLATE NOCASE);
```

The schema is idempotent (`CREATE TABLE IF NOT EXISTS`), but
`ALTER TABLE ADD COLUMN` is not — so for `is_canonical` columns, do
NOT rely on `executescript` to add them to an existing DB. The seed
process will delete the existing `library.db` and rebuild from scratch
(simpler than migrations). Document this in the schema header comment.

### Task 2 — Allowlist loader + validator

New file: `fermentation/library_mcp/seed/allowlist/__init__.py`.

Responsibilities:

- Parse `allowlist/{countries,grapes,regions}.yaml` from the same dir.
- Dataclasses:
  ```python
  @dataclass
  class CountryEntry:  qid: str; iso: str | None = None; name_override: str | None = None
  @dataclass
  class GrapeEntry:    qid: str; name: str | None = None; color: str | None = None;
                       synonyms: list[str] = field(default_factory=list)
  @dataclass
  class RegionEntry:   qid: str; name: str; country_qid: str;
                       parent_qid: str | None = None; classification: str | None = None;
                       synonyms: list[str] = field(default_factory=list)
  ```
- Validator:
  - QID must match `r"^Q\d+$"`.
  - Country QIDs in regions must exist in countries allowlist.
  - Parent QIDs in regions must exist in regions allowlist OR be None.
  - Duplicates within a file → error.
- Public entry point: `load_allowlists(base: Path) -> tuple[list, list, list]`.

Add `PyYAML==6.0.2` (or similar) to `requirements.txt`.

### Task 3 — Populate YAMLs (the long pole)

Three files under `fermentation/library_mcp/seed/allowlist/`:

- `countries.yaml` — ~50 entries. Use the OIV wine-producing country
  list as the source of truth. Each entry: `qid`, `iso`.
  - High-confidence QIDs to start with: Q142 (France), Q38 (Italy),
    Q29 (Spain), Q183 (Germany), Q45 (Portugal), Q414 (Argentina),
    Q298 (Chile), Q258 (South Africa), Q408 (Australia), Q664 (NZ),
    Q30 (USA), Q41 (Greece), Q40 (Austria), Q43 (Turkey),
    Q224 (Croatia), Q215 (Slovenia), Q36 (Poland — has wine industry),
    Q252 (Indonesia? skip), Q822 (Lebanon), Q801 (Israel), Q77 (Uruguay),
    Q155 (Brazil), Q96 (Mexico), Q159 (Russia), Q212 (Ukraine),
    Q218 (Romania), Q33 (Finland — no, skip), Q219 (Bulgaria),
    Q229 (Cyprus), Q236 (Montenegro), Q403 (Serbia), Q224 (Croatia),
    Q237 (Vatican — skip), Q347 (Liechtenstein — skip),
    Q39 (Switzerland), Q31 (Belgium — minor), Q55 (Netherlands — skip),
    Q145 (UK — England yes), Q34 (Sweden — skip), Q20 (Norway — skip),
    Q35 (Denmark — skip), Q230 (Georgia), Q399 (Armenia),
    Q227 (Azerbaijan), Q232 (Kazakhstan — minor), Q801 (Israel),
    Q794 (Iran — historically), Q668 (India — minor), Q148 (China),
    Q884 (South Korea — skip), Q17 (Japan), Q865 (Taiwan — skip),
    Q833 (Malaysia — skip), Q928 (Philippines — skip),
    Q1014 (Lesotho — skip), Q1033 (Nigeria — skip),
    Q1029 (Mozambique — skip), Q1036 (Uganda — skip),
    Q1042 (Seychelles — skip), Q117 (Ghana — skip),
    Q241 (Cuba — skip), Q414 (Argentina — dup).
  - **Verify each QID on Wikidata before committing**. The validator
    will catch typos at build time but only if `build_db.py` runs.

- `grapes.yaml` — ~500 entries. Use Jancis Robinson / Wine Grapes as
  the canonical source. Group by color in the file for human-readable
  diffs (YAML comments are fine). Critical entries the test CSV
  exercises (verify QIDs):
  - **Reds:** Pinot Noir (Q170545), Cabernet Sauvignon (Q146048),
    Merlot (Q104448), Syrah (Q173997), Grenache (Q165264),
    Sangiovese (Q146045), Tempranillo (Q220675), Nebbiolo (Q486587),
    Malbec (Q207679), Carignan (Q207697), Cinsault (Q170562),
    Gamay (Q173997 — verify), Negroamaro (Q1342283),
    Touriga Nacional (Q1505213), Castelão (?), Cabernet Franc (Q207688),
    Picpoul Noir / Piquepoul (Q207704).
  - **Whites:** Chardonnay (Q146049), Sauvignon Blanc (Q146049 — verify),
    Riesling (Q165280), Pinot Gris (Q207751), Pinot Grigio (synonym),
    Picpoul Blanc (Q207704 — both colors share root QID? verify),
    Greco Bianco, Vermentino (Q1496400), Trebbiano (Q207826).
  - Synonyms to wire up for the test CSV:
    - `Aragonez`, `Aragonês`, `Tinta Roriz` → Tempranillo
    - `Tinto Fino`, `Tinto del País` → Tempranillo
    - `Pinot Grigio` → Pinot Gris (or vice-versa; pick canonical)
    - `Piquepoul`, `Picpoul` synonym pair
    - `Garnacha` → Grenache
    - `Shiraz` → Syrah
  - Long tail: aim for ~500 covering classical wine grapes from
    France/Italy/Spain/Portugal/Germany/Austria/Greece/US. Skip every
    American hybrid (Concord, Niagara, Catawba) unless the user asks
    for those.

- `regions.yaml` — ~300 entries. Hierarchy via `parent_qid`. Must-have
  buckets:
  - France (~50): Bordeaux + Médoc + Margaux + Pauillac + St-Émilion +
    Pomerol + Sauternes; Burgundy + Côte de Nuits + Côte de Beaune +
    Chablis + Beaujolais + Brouilly + Morgon + Fleurie + Moulin-à-Vent;
    Rhône + Côte-Rôtie + Hermitage + Châteauneuf-du-Pape +
    Côtes du Rhône; Champagne; Loire + Sancerre + Pouilly-Fumé +
    Touraine + Vouvray + Muscadet; Alsace; Provence; Roussillon +
    Côtes du Roussillon; Languedoc + Picpoul de Pinet + Corbières +
    Minervois; **Pays d'Oc IGP**; Jura; Savoie; Cahors.
  - Italy (~50): Piedmont + Barolo + Barbaresco + Asti + Gavi;
    Tuscany + Chianti + Chianti Classico + Brunello di Montalcino +
    Vino Nobile di Montepulciano + Bolgheri; Veneto + Valpolicella +
    Amarone + Soave + Prosecco + delle Venezie IGT; Friuli;
    Trentino-Alto Adige; Lombardy + Franciacorta; Emilia-Romagna +
    Lambrusco; Marche; Umbria; Abruzzo + Montepulciano d'Abruzzo;
    Campania + Taurasi; Puglia + Salice Salentino + Primitivo di
    Manduria; Basilicata + Aglianico del Vulture; Calabria + Cirò;
    Sicily + Etna; Sardinia + Vermentino di Gallura.
  - Spain (~30): Rioja + Rioja Alavesa + Rioja Alta + Rioja Oriental;
    Ribera del Duero; Priorat; Penedès; Cava; Rías Baixas;
    Ribeiro; Bierzo; Toro; Rueda; Jerez/Sherry; Montilla-Moriles;
    Navarra; **Getariako Txakolina**; Empordà.
  - Portugal (~15): Douro; Porto; Vinho Verde; Dão; Bairrada; Alentejo;
    **Lisboa**; **Alenquer**; Tejo; Madeira; Setúbal; Bucelas.
  - Germany (~15): Mosel; Rheingau; Rheinhessen; Pfalz; Ahr; Baden;
    Franken; Nahe; Mittelrhein; Hessische Bergstrasse; Saale-Unstrut;
    Sachsen; Württemberg.
  - Austria (~10): Wachau; Kamptal; Kremstal; Burgenland; Wien;
    Steiermark.
  - USA (~25): California + Napa + Sonoma + Russian River + Dry Creek +
    Alexander Valley + Paso Robles + Santa Barbara + Santa Rita Hills +
    Mendocino + Lodi + Carneros; Oregon + Willamette Valley + Dundee
    Hills; Washington + Columbia Valley + Walla Walla; New York +
    Finger Lakes; Texas Hill Country.
  - Argentina (~5): Mendoza + Uco Valley + Luján de Cuyo; Salta + Cafayate.
  - Chile (~8): Maipo; Colchagua; Casablanca; Maule; Aconcagua; Itata;
    Bío-Bío; Limarí.
  - South Africa (~10): Stellenbosch; **Paarl**; **Constantia**;
    **Robertson**; Franschhoek; Swartland; Walker Bay; Elgin;
    Hemel-en-Aarde.
  - Australia (~12): Barossa Valley; Eden Valley; McLaren Vale; Coonawarra;
    Clare Valley; Adelaide Hills; Yarra Valley; Margaret River;
    Mornington Peninsula; Hunter Valley; Tasmania.
  - NZ (~6): Marlborough; Central Otago; Hawke's Bay; Martinborough;
    Wairarapa; Nelson.
  - Greece (~6): Nemea; Santorini; Naoussa; Mantinia; Patras; Crete.
  - Lebanon (~2): **Bekaa Valley**; Mount Lebanon. (single-region-floor rule)
  - Israel (~3): Galilee; Judean Hills; Negev.
  - Hungary (~5): Tokaj; Eger; Villány; Szekszárd.
  - Georgia (~4): Kakheti; Imereti; Kartli; Racha.
  - Add `parent_qid` to nest. Example: Barolo's `parent_qid` is
    Piedmont's QID; Piedmont's `parent_qid` is null (country-direct).
  - Add synonyms for: Piedmont/Piemonte, Tuscany/Toscana,
    Burgundy/Bourgogne, Sicily/Sicilia, Sardinia/Sardegna.

**Looking up QIDs:** the validator should hit Wikidata via SPARQL with
the YAML's QIDs in a `VALUES` block — if any return no label, fail
the build with the offending QIDs. Add this as part of Task 2's
validator.

### Task 4 — Rewrite ingest_* in build_db.py

Replace the three `ingest_*` functions with allowlist-driven equivalents:

1. Drop `seed/sparql/{countries,regions,grapes}.rq` files. Move SPARQL
   templates inline into Python (they're now parameterized by QID list).
2. New flow:
   ```
   allowlist = load_allowlists(HERE / "allowlist")
   ingest_countries(conn, allowlist.countries)  # VALUES SPARQL
   ingest_regions(conn, allowlist.regions)      # VALUES SPARQL, two-pass for parent
   ingest_grapes(conn, allowlist.grapes)        # VALUES SPARQL + synonyms merge
   ingest_wikipedia(conn)                       # unchanged behavior, QID-aware (Task 6)
   ingest_placeholders(conn, allowlist)         # Task 5
   ```
3. All canonical inserts: `is_canonical=1`.
4. Synonym merge order: Wikidata altLabels first, then allowlist YAML
   `synonyms:` field (so manual entries override duplicates).
5. Region synonyms (new) → `region_synonyms` table.

### Task 5 — Filtered placeholder pass

New function `ingest_placeholders(conn, allowlist)`. Two SPARQL queries:

- **Grapes:** `?g wdt:P31/wdt:P279* wd:Q10978 .` + filter
  `{ ?g wdt:P225 "Vitis vinifera" } UNION { ?g wdt:P366 wd:Q282 }`.
  Skip QIDs already in allowlist. Insert with `is_canonical=0`.
- **Regions:** broaden to union over wine-region subclasses (loose-end
  #4 in PLAN.md). Skip allowlisted QIDs. Insert with `is_canonical=0`.

### Task 6 — QID-aware Wikipedia parsers

In `seed/wikipedia/italy.py` and `germany.py`:

- Wikipedia REST HTML carries `data-wikidata-item-id="Q…"` on linked
  entity anchors. Extract that in `_qid_from_href` (currently returns
  slugs).
- `build_db.ingest_wikipedia` should look up grapes/regions by QID
  first, then fall back to name match. This prevents the parser
  minting duplicate region rows that compete with allowlist entries.

### Task 7 — Server canonical-first

In `server.py`:

- `_resolve_grape`, `_resolve_region`, `_resolve_country`: prefer rows
  where `is_canonical=1`. Two-pass: canonical match first, then
  placeholder.
- `lookup_grape` already returns `is_placeholder` — wire it to the new
  `is_canonical=0` semantic (was previously only true for phrases like
  "Bordeaux Blend"; now also true for non-canonical resolved entries).
  Keep the phrase-based placeholder check as a separate sentinel — it
  means "this isn't a grape at all," distinct from "this is a niche
  grape." Maybe introduce a separate field: `is_phrase` for the
  hallucination case, `is_placeholder` for non-canonical real entries.
- `lookup_region`: add synonym join against `region_synonyms`.
- `list_*`: filter `WHERE is_canonical=1` by default.
- `submit_tags`: add `non_canonical_region` issue code + hint.
  Trigger when a region resolves but `is_canonical=0`.

### Task 8 — CI smoke test

New file: `fermentation/library_mcp/tests/test_combined_csv_coverage.py`.

For every row in `curation/test/combined.csv`, derive the expected
country / grape(s) / region(s) (hardcoded mapping in the test — these
are reference assertions, not derived from snippets). Then assert each
resolves against `library.db` with the expected `is_canonical` /
`is_placeholder` status. The PLAN's "Coverage notes" subsection has
the expected canonical vs placeholder split — use that.

Run: `pytest fermentation/library_mcp/tests/`.

## Decisions already made

- **Hybrid C** approach: allowlist canonical + filtered placeholder. The
  user explicitly chose this in the question I asked.
- **Bundled scope:** grapes + countries + regions all in one plan, not
  staged.
- **Full canonical pass now:** user wants me to draft the YAMLs (not
  scaffold-only). Risk of QID typos accepted; validator catches at
  build time.

## Risks to flag when resuming

1. **QID accuracy on the long tail.** I'm confident on ~150 grapes and
   ~80 regions; the next 350 grapes and 220 regions need careful
   Wikidata lookup. The Task 2 validator must run successfully before
   Task 4 can produce a valid `library.db`.
2. **Re-seeding takes a Wikidata round-trip.** Don't try to run
   `build_db.py` without network. The output `library.db` must be
   committed as a binary diff.
3. **Schema migration.** `ALTER TABLE` for new columns is non-trivial.
   Easier path: delete `library.db` and let `build_db.py` rebuild from
   scratch. State this in the schema header.
4. **`is_placeholder` semantic split.** Today it means "you submitted
   a non-grape phrase." Under the new plan it also could mean "real
   grape, not canonical." These are different and the tagger needs
   to know which. Recommend splitting into `is_phrase` (hallucination)
   and `is_placeholder` (non-canonical real entry). See Task 7.

## Resume command

When you pick this up:

1. `TaskList` to see the 8 tasks.
2. Set Task 1 in_progress and start with the schema edit.
3. Work tasks in order 1 → 8. Tasks 1, 2, 7 can be done without
   network; Tasks 3, 4, 5 need Wikidata access at build time but the
   code can be written offline.
