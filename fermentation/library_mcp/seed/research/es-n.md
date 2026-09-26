Status: complete

# Northern Spain (ES-N) — ground-truth research notes

Scope: the existing ES entries in Galicia, Asturias, Cantabria, País Vasco,
Navarra, La Rioja, Aragón, Catalonia and Castilla y León, plus every
DOCa/DOQ/DO/VP/VC/IGP in them, per `seed/research/scopes/es-n.md`.

## Sources

- **MAPA, "Listado de Denominaciones de Origen Protegidas e Indicaciones
  Geográficas Protegidas de Vinos registradas en la Unión Europea," updated
  2 July 2026** — the primary authority for which DOPs/IGPs exist and which
  autonomous community each sits in.
  `https://www.mapa.gob.es/es/dam/jcr:f9643333-ef75-4a2f-8864-afd1ade63fd1/02_vinos.pdf`
  (downloaded with `curl` and read directly — a flat list, so it does not
  give subzones or grape rules). This list is materially newer than most
  wine-trade write-ups: it includes DOPs registered in 2021–2024 that
  Wikipedia and most retailer copy still miss (Urbezo, Bolandin, Dehesa
  Peñalba, Urueña, Cebreros, León's 2019 rename).
- Each DO/DOCa/DOQ/VP's own Consejo Regulador site or its pliego de
  condiciones (via MAPA's pliego archive) for subzones and principal
  grapes: DO Rías Baixas, DO Ribeira Sacra (`ribeirasacra.org`), DO
  Monterrei (Wikipedia + `domonterrei.wine`, cross-checked — see Uncertain
  calls), DOCa Rioja (`riojawine.com`), DO Navarra
  (`navarrawine.com`), DOP Arribes, DOP Tierra del Vino de Zamora, DOP
  Urbezo, DOP Pla de Bages (all via MAPA's pliego PDFs), DOP Penedès
  (`dopenedes.cat`), DO Costers del Segre (`incavi.gencat.cat`).
- Wikipedia, cross-checked case by case (Arlanza, Monterrei, León's rename,
  Parraleta, Priorat DOQ, Juan García, Pago Aylés, Pago de Arínzano/Otazu,
  Prado de Irache) — used only where a primary pliego was not readily
  available, per the brief's source-priority rule.
- Grape identity: VIVC (`vivc.de`) directly for Garnacha Peluda; secondary
  sources cross-checked against each other for Dona Branca/Malvasía
  Castellana identity (Wines of Galicia, wein.plus, Wine-Searcher) and for
  Albillo Mayor vs. Albillo Real (Bodega Pradorey's own explainer, which
  cites the parentage studies).

## Counts

| Tier | Official (MAPA, 2 Jul 2026) | Produced |
|---|---|---|
| Supraautonómico entries that touch my communities (Cava, Rioja, Ribera del Queiles) | 3 | 3 |
| La Rioja (community-level; Rioja DOCa itself is supraautonómico) | 1 (IGP Valles de Sadacia) | 1 |
| Aragón | 11 (6 DOP + 5 IGP) | 11 |
| Principado de Asturias | 1 | 1 |
| Cantabria | 2 | 2 |
| Castilla y León | 17 (16 DOP + 1 IGP) | 16 classified entries + the IGP folded into the existing "Castilla y León" synonym list (see below) |
| Cataluña | 11 | 11 |
| Galicia | 10 (5 DOP + 5 IGP) | 10 |
| Navarra | 6 (5 DOP + 1 IGP) | 6 |
| País Vasco | 3 | 3 |
| **Official DOP/IGP total** | **65** | **64 classified + 1 folded = 65** |
| Subzones (below MAPA's flat-list granularity: Rías Baixas ×5, Ribeira Sacra ×5, Monterrei ×2, Costers del Segre ×7) | n/a | 19 |
| Community/administrative placeholders (no DOP/IGP status themselves: Galicia, Asturias, Cantabria, Basque Country, Aragón, Castilla y León) | n/a | 6 |
| Rioja's 3 zones (Alta/Alavesa/Oriental — existing library entries, no `classification`, kept as-is) | n/a | 3 |
| **Total entries in `es-n.regions.yaml`** | | **92** |

**Left out, and why:**
- **Priorat's "Vi de Vila"** (12 municipality names — Gratallops, Porrera,
  Scala Dei, Torroja del Priorat, etc. — that DOQ Priorat has let producers
  add to labels since 2009). Not added as child regions: this is a
  labeling permission tied to municipality names within one appellation
  (like a village mention), not a separate registered appellation tier the
  way a Burgundy village AOC is. Flagged under Uncertain calls.
- **Clàssic Penedès.** Not a place — it is a quality-wine designation for
  organic, traditional-method sparkling Penedès (its own pliego requires
  the label to also carry "Penedès, Denominación de Origen"). Added as a
  synonym of Penedès instead of a child entry.
- **Penedès's three informal climate zones** (Superior/Central/Marítim) —
  tourism-board and importer copy describes them, but they are not
  sub-appellations in the DOP's own pliego de condiciones. Left out.
- **Ribeiro's informal river-valley names** ("Ribeiro do Avia," "do Miño,"
  "do Arnoia") — used descriptively by some producers, not officially
  demarcated subzones of DO Ribeiro. Left out.
- **Cava's "Paraje Calificado"** single-vineyard tier (e.g. Turó d'en Mota)
  — an ultra-premium single-vineyard mention layered on top of Cava, not a
  place hierarchy level (same category as Grand Cru vineyard names, which
  the brief already excludes). Left out.

## Changes to existing entries

1. **`Catalonia`: added `classification: DO`.** "DOP Cataluña / Catalunya"
   (PDO-ES-A1549) is a real registered regional DO, not just this file's
   administrative grouping entry — the same situation as `Navarra`, which
   already carries `classification: DO` for the same reason (the community
   name and a real appellation coincide). Left `grapes:` off it: its
   permitted-variety list is essentially every major Catalan grape, so it
   would not read as a distinguishing "principal" set the way Priorat's or
   Penedès's does. Flagged under Uncertain calls.
2. **New `León` entry uses the 2019 name, not the scope note's "Tierra de
   León."** DO Tierra de León renamed to plain DO León on 25 April 2019
   (`ileon.eldiario.es`), specifically to stop being confused with the
   lower-tier "Vino de la Tierra de Castilla y León." Used "León" as
   canonical with "Tierra de León" as a synonym. No `was:` — there was no
   existing library row under either name to rename; this is a new entry.
3. **New `Cebreros` (VC) collides with the existing `Sierra de Gredos`
   entry**, which lists `"Cebreros"` as one of its own synonyms
   (`{name: "Sierra de Gredos", country: ES, synonyms: ["Gredos",
   "Cebreros"]}`). Cebreros became its own EU-registered DOP in October
   2022 — exactly the bug pattern the brief names for Robertson: a real
   appellation folded into a broader informal region's synonym list.
   Sierra de Gredos is not in my scope (it spans Ávila/Madrid/Toledo with
   no community assigned in the library, so it likely belongs to es-s or
   is unowned), so I have not edited it, but the merge must drop
   `"Cebreros"` from `Sierra de Gredos`'s synonyms or the validator will
   reject the duplicate label.
4. **`Rioja` gained `grapes: [Tempranillo, Garnacha, Graciano, Mazuelo,
   Viura]`**, per the scope note's explicit list.
5. Every other existing entry I touched (Cava, Navarra, Aragón, Priorat,
   Montsant, Penedès, Costers del Segre, Empordà, Terra Alta, Conca de
   Barberà, Alella, Galicia's five DOs, the three Txakolis, Ribera del
   Duero, Toro, Rueda, Bierzo, Cigales, Arribes, Cariñena, Calatayud, Campo
   de Borja, Somontano) is unchanged in name/parent/synonyms — it only
   gained `grapes:` and, where applicable, child subzones. Verified by
   diffing every re-listed entry's synonyms/parent/classification against
   the current `regions.yaml` before finalizing this file.

## Homonyms

- **La Rioja** — Spain's Rioja DOCa/community vs. Argentina's La Rioja
  province, both real wine regions. Already known to the project (the
  scope note names it); confirmed allowed under Decision 1 of the
  ground-truth plan (country-scoped homonyms, picked by the wine's
  submitted country).
- **Cariñena** (DO, Aragón) is also the name of a grape (Mazuelo/Carignan's
  Aragonese name, already canonical in `grapes.yaml`). Not a cross-country
  region collision — `lookup_region` and `lookup_grape` are separate
  functions and separate namespaces — but worth flagging for the tagger
  prompt: a bare snippet mention of "Cariñena" is genuinely ambiguous
  between the place and the grape without more context.
- No other exact-string collisions found between my new/changed ES labels
  and non-Spanish regions elsewhere in `regions.yaml` (Toro, Bierzo, Rueda,
  Cigales, Alella, Somontano, Empordà/Ampurdán checked individually).

## Uncertain calls

- **`Torrontés` grape-identity collision (the biggest one).** Ribeiro,
  Ribeira Sacra and Monterrei's own pliegos name "Torrontés" as a permitted
  white grape. But the existing canonical `grapes.yaml` entry
  `{name: "Torrontés", synonyms: ["Torrontés Riojano"]}` is almost
  certainly the unrelated Argentine grape (Torrontés Riojano/Sanjuanino,
  DNA-confirmed as a Muscat of Alexandria × Criolla Chica cross). DNA
  studies (cited by Wine-Searcher/Wine Folly write-ups on the Torrontés
  family) show Galicia's Torrontés is actually **Fernão Pires** — already
  canonical in `grapes.yaml` under that name. I could not add "Torrontés"
  as a Fernão Pires synonym (it would collide with the existing entry's
  canonical name, which the validator forbids), so I left it out of every
  Galician DO's `grapes:` field rather than misattribute it. This means
  `lookup_grape("Torrontés")` on a Ribeiro wine currently resolves to the
  wrong (Argentine) grape and there is no clean fix at the data level —
  it needs either a country-scoped grape lookup (mirroring the region
  homonym fix) or renaming the existing entry to something unambiguous
  like "Torrontés Riojano" with "Torrontés" demoted to a shared/ambiguous
  label. Flagged for a human decision; included as a fixture row below.
- **`Cebreros`/`Sierra de Gredos`** — see Changes above; this is a merge-
  time conflict, not something I can resolve inside my own file.
- **Priorat's "Vi de Vila"** — left out as a labeling permission rather
  than a place tier; see Left out above. A human may disagree and want the
  12 village names added as children of Priorat.
- **`Catalonia`/DO Catalunya's `grapes:`** — left off due to breadth (see
  Changes #1). A human may want a short illustrative list anyway
  (Macabeo/Xarel·lo/Parellada/Tempranillo/Garnacha) even though it is not
  truly "principal" the way a smaller DO's list is.
- **Garnacha Peluda** — VIVC currently lists it as its own accession
  (id 27072), though ampelographers argue it is really a hairy-leaf clone
  of Grenache rather than a separate variety. Followed VIVC per the
  brief's identity rule and added it as a separate grape, not a Grenache
  synonym.
- **Albarín Blanco / Albarín Negro** — both are recommended Asturian
  varieties and share the "Albarín" name, but I found no ampelographic
  source confirming or denying a genetic relationship between them (unlike
  the confirmed-distinct Albillo Mayor/Albillo Real pair). Added both as
  separate grapes without asserting a relationship either way.
- **`Ladeira de Monterrei` vs. `Ladeiras de Monterrei`** — sources split
  between singular (Wikipedia, matching "Val de Monterrei" singular) and
  plural. Used the singular as canonical, kept the plural as a synonym.
- **Pago de Otazu** — one source also lists an estate-planted "Berués"
  variety alongside the DOP's core Tempranillo/Merlot/Cabernet
  Sauvignon/Chardonnay; I could not confirm it is part of the DOP's
  regulated variety list (vs. an experimental planting) and did not find
  it in `grapes.yaml`, so I left it out rather than add a low-confidence
  new grape.
- **Aylés (VP) grapes** — sourced from Wikipedia's "Pago Aylés" page, not
  the pliego itself (not readily found as a separate PDF from Urbezo's).
  Moderate confidence only.
- **`grapes:` omitted for VC entries** (Cangas, Cebreros, Sierra de
  Salamanca, Valles de Benavente, Valtiendas). My scope note says
  "`grapes:` field, yes, for every DOCa/DOQ/DO/VP," which does not list VC,
  even though VC pliegos do name regulated principal varieties (e.g.
  Cangas: Albarín Blanco, Godello, Carrasquín, Verdejo Negro, Albarín
  Negro, Mencía). Followed the scope note literally rather than the
  general brief's broader "and similar" wording; flagging in case the
  merge wants VC included after all.

## Label string → canonical

| Label string | Kind | Canonical | Where seen |
|---|---|---|---|
| "D.O.Ca. Rioja" | region | Rioja | `https://riojawine.com/` (Consejo Regulador self-description) |
| "Rioja Alavesa" | region | Rioja Alavesa | existing library entry |
| "Ribera del Duero" | region | Ribera del Duero | `https://www.mapa.gob.es/es/dam/jcr:f9643333-ef75-4a2f-8864-afd1ade63fd1/02_vinos.pdf` |
| "Rias Baixas" | region | Rías Baixas | common no-accent retailer spelling |
| "Priorato" | region | Priorat | Castilian spelling, widely used on US retailer sites |
| "Val do Salnés" | region | Val do Salnés | `https://www.doriasbaixas.com/en/subzones/` |
| "Txakoli" | region | Getariako Txakolina | existing library synonym |
| "Chacolí de Bizkaia" | region | Bizkaiko Txakolina | `https://www.mapa.gob.es/es/dam/jcr:f9643333-ef75-4a2f-8864-afd1ade63fd1/02_vinos.pdf` (official alt-name) |
| "Tierra de León" | region | León | pre-2019 name, `https://ileon.eldiario.es/actualidad/do-leon_1_9503513.html` |
| "Clàssic Penedès" | region | Penedès | `https://dopenedes.cat/en/dopenedes/` |
| "Ladeiras de Monterrei" | region | Ladeira de Monterrei | plural trade spelling vs. singular official name |
| "Ribera del Gállego - Cinco Villas" | region | Ribera del Gállego-Cinco Villas | MAPA's spaced-hyphen official form |
| "Tinto Fino" | grape | Tempranillo | existing library synonym, Ribera del Duero usage |
| "Garnatxa" | grape | Grenache | the tagger's exact failure case named in the scope note |
| "Mazuelo" | grape | Carignan | existing library synonym, Rioja usage |
| "Viura" | grape | Macabeo | existing library synonym |
| "Doña Blanca" | grape | Dona Branca | Castilian spelling of the Galician/Castilla y León grape, `https://winesofgalicia.com/dona-branca-the-grape-named-for-a-queen` |
| "Merenzao" | grape | Trousseau | Ribeira Sacra name, `https://en.wikipedia.org/wiki/Ribeira_Sacra_(DO)` |
| "Albillo" | grape | Albillo Real | bare "Albillo" on labels means Albillo Real, not Albillo Mayor, `https://pradorey.es/en/blog/what-is-albillo-mayor-or-real-we-clarify-it/` |
| "Moscatel de Grano Menudo" | grape | Muscat Blanc à Petits Grains | Navarra/Bolandin usage |
| "Sousón" | grape | Vinhão | Galician name; same grape as Portugal's Vinhão/Sousão |
| "Hondarribi Zuri" | grape | Hondarrabi Zuri | existing library synonym, alt Basque spelling |
| "Torrontés" (on a Ribeiro label) | grape | **not resolvable — flag, do not map to the existing "Torrontés" entry** | DNA studies show this is Fernão Pires, unrelated to the canonical "Torrontés" (Argentine); see Uncertain calls |

## Validation

```
$ .venv/bin/python -c "import yaml,sys; [print(f, len(yaml.safe_load(open(f)))) for f in sys.argv[1:]]" fermentation/library_mcp/seed/research/es-n.regions.yaml fermentation/library_mcp/seed/research/es-n.grapes.yaml
fermentation/library_mcp/seed/research/es-n.regions.yaml 92
fermentation/library_mcp/seed/research/es-n.grapes.yaml 22
```

Also checked by script (not part of the required command, but worth
recording): no duplicate `(name, country)` pairs, no region label collision
within the file, no parent left dangling (every `parent` resolves either
within this file or in the existing `regions.yaml`), every `grapes:` entry
resolves against the combined existing + new grape allowlist, no new grape
name or synonym collides with an existing canonical grape name or synonym,
and no duplicate grape names within the file — except the one deliberate,
documented `Cebreros`/`Sierra de Gredos` label collision above, which is a
merge-time fix, not a bug in this file.

## Review (main session, 2026-09-26)

- **Dropped bare `Albillo` as a synonym of Albillo Real.** Ribera del
  Duero labels say "Albillo" for Albillo Mayor, one of that DO's principal
  grapes, and the store carries a lot of Ribera. An ambiguous name should
  stay unresolved rather than resolve to the wrong grape.
- **Kept `Urbezo` as DO.** The EU registered it as a DOP in 2024. Spain may
  treat it as a Vino de Pago; the classification label does not affect
  lookups.
- **Sierra de Gredos still lists "Cebreros".** It belongs to es-s's scope,
  which was told to drop it. If it is still there at merge time, drop it
  by hand.

## Review addendum (main session, 2026-09-26, during es-s1 review)

- `Bruñal` removed as a new grape: it is Alfrocheiro. es-s1's grapes file
  now carries it as a synonym of the existing `Alfrocheiro`, along with
  `Brunal`, `Bastardillo Chico` and the Canarian `Baboso Negro`.
- Merge-time: `Maturana Tinta` and `Verdejo Negro` became Trousseau synonyms
  (Wikidata Q6160560 aliases). `Picapoll Negre` became a synonym of the
  existing `Piquepoul Noir`. `Asturias` is pinned to Q3934 (the resolver had
  picked a municipality in the Philippines). Added `Chacolí de Bizkaia`.
