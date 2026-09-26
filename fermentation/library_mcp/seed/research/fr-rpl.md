Status: complete

# fr-rpl: Rhône, Provence, Corsica, Languedoc-Roussillon — research notes

## Sources

Primary register throughout: INAO cahiers des charges (extranet.inao.gouv.fr
PDFs and inao.gouv.fr "fiche produit" pages), all accessed September 2026.
Used directly for: Côte-Rôtie, Saint-Joseph, Crozes-Hermitage, Cornas,
Côtes du Rhône, Côtes du Rhône Villages (+ all named villages, PNO2024),
Gigondas, Vacqueyras, Rasteau, Cairanne, Vinsobres, Lirac, Luberon,
Grignan-les-Adhémar, Costières de Nîmes, Clairette de Die, Châtillon-en-Diois,
Bellet, Corbières, Corbières-Boutenac/Boutenac (renamed by decree 2022-09-02),
Languedoc, Pierrevert, Muscat de Beaumes-de-Venise, Ventoux.
Condrieu, Château-Grillet and Hermitage cited via the consolidated
Légifrance decree (2010) that also covers Châteauneuf-du-Pape, since INAO's
own per-appellation fiches redirect there.
Where no INAO PDF could be located quickly: Inter Rhône (vins-rhone.com,
official interprofession, for Laudun, Muscat de Beaumes-de-Venise overview),
Vins du Roussillon (roussillon.wine, official interprofession, for
Côtes Catalanes, Maury Sec, Muscat de Rivesaltes), Vie d'Oc / Vins IGP de
France interprofession pages for several small IGPs, and French Wikipedia
(fr.wikipedia.org) for the remaining Languedoc AOC denominations, the
Muscat AOCs of Hérault, Malepère, Limoux/Blanquette/Crémant de Limoux,
Banyuls/Banyuls Grand Cru, and most grape-identity checks. These are
flagged per entry in `source:`.

## Counts

- **Rhône, Provence, Corsica**: unchanged from the earlier pass in this file
  (see prior entries above the Languedoc-Roussillon section); not recounted
  here.
- **Languedoc-Roussillon section** (this session): 61 entries added, against
  an official INAO/eAmbrosia scheme that includes roughly: Languedoc AOC +
  9 current dénominations géographiques complémentaires (Cabrières, La
  Méjanelle, Quatourze, Saint-Christol, Saint-Drézéry, Saint-Georges-
  d'Orques, Saint-Saturnin, Sommières, Pézenas) + Picpoul de Pinet, plus
  Grès de Montpellier (its own AOP since May 2024, so given a standalone
  entry rather than folded into the Languedoc denominations); Corbières,
  Boutenac, Minervois, Minervois-La Livinière, Faugères, Saint-Chinian,
  Fitou, Limoux, Blanquette de Limoux, Crémant de Limoux, Cabardès,
  Malepère, Clairette du Languedoc, the four Muscat AOCs (Frontignan,
  Lunel, Mireval, Saint-Jean-de-Minervois); Roussillon, Côtes du
  Roussillon, Côtes du Roussillon Villages + 5 named villages (Caramany,
  Latour-de-France, Les Aspres, Lesquerde, Tautavel), Collioure, Banyuls,
  Banyuls Grand Cru, Maury, Maury Sec, Rivesaltes, Muscat de Rivesaltes;
  plus 12 IGPs (Pays d'Oc, Méditerranée, Côtes Catalanes, Vaucluse, Gard,
  Hérault, Aude, Côtes de Thongue, Collines Rhodaniennes, Comtés
  Rhodaniens, Ardèche, Alpilles).
- **Left out on purpose**: very small/rare Languedoc AOC denominations that
  I could not confirm are still active on the current INAO register within
  the time available beyond the 9 listed (I did not add speculative ones);
  the many single-department "IGP Pays de ..." zone-level IGPs beyond the
  ones named in the scope note (there are dozens across these departments,
  most too fine-grained for retail labels); Vin de Pays / IGP zones inside
  Vaucluse/Gard/Hérault that overlap the department-level IGP already
  listed (e.g. IGP Sable de Camargue, IGP Coteaux de Peyriac) — flagged as
  uncertain below rather than added blind.
- **Fixed a gap**: `Châteauneuf-du-Pape` was an existing library entry
  (regions.yaml line 123) that had not yet been carried into this file —
  added with its full cahier grape list.
- Total this file: 140 region entries, 10 grape entries (9 new grapes + 1
  new synonym on an existing grape).

## Changes to existing entries

- **`Côtes du Roussillon` promoted from synonym to its own entry** (the
  scope's flagged fix): it is its own AOC, distinct from `Roussillon`
  (which is now an unclassified umbrella, parent of both `Côtes du
  Roussillon` and `Côtes du Roussillon Villages`).
- **`Corbières-Boutenac` split into its own entry**, renamed `Boutenac`
  (INAO decree of 2022-09-02 dropped "Corbières-" from the official name);
  kept `Corbières-Boutenac` as a synonym since that is still the name most
  retail listings use. `was: "Corbières-Boutenac"` recorded.
- **`Minervois La Livinière` split into its own entry** `Minervois-La
  Livinière`, parented under `Minervois` (it is its own AOC — red only,
  15-month aging — not a synonym of the broader Minervois AOC).
- **`Blanquette de Limoux` and `Crémant de Limoux` split out** from being
  synonyms of `Limoux` into their own entries, parented under `Limoux`:
  both are separate sparkling-wine AOCs (different grape rules, different
  method) from the still-wine `Limoux` AOC, not alternate names for it.
- **`Muscat de Rivesaltes` split out** from being a synonym of `Rivesaltes`
  into its own entry: same production zone, but a separate AOC (Muscat
  grapes only, vs. Rivesaltes' broader Grenache-based VDN blend) — same
  pattern as the existing `Muscat de Beaumes-de-Venise` / `Beaumes-de-
  Venise` split in the Rhône section.
- **`Coteaux du Languedoc Picpoul-de-Pinet` added as a synonym of
  `Picpoul de Pinet`** per the scope note (it is the former label form the
  tagger had actually searched for, not a form of the Languedoc AOC
  itself).
- **Added `Maury Sec`** as a standalone entry (parent `Roussillon`, not a
  child of `Maury`): it is a separate dry-red AOC created in 2011 alongside
  the fortified `Maury` VDN, covering the same communes but different
  wine styles and rules — treating it as a child of `Maury` would make
  every dry Maury Sec inherit "Maury" as an ancestor incorrectly implying
  VDN lineage, so I gave both entries the same parent instead.
- **Added `Grès de Montpellier` as a standalone AOC** (parent
  `Languedoc-Roussillon`, not a child of `Languedoc`): it graduated from
  Languedoc dénomination to its own AOP in May 2024.

## Homonyms

- **`La Livinière`**: no known homonym found outside Minervois.
- No other same-name collisions with other countries were found for this
  slice's new entries (Malepère, Boutenac, Grès de Montpellier, the Muscat
  AOCs, and the IGPs are all France-specific place names).

## Uncertain calls

- **`Braquet` vs `Brachetto`**: historically conflated (Braquet grown at
  Bellet was long assumed to be the same as Piedmont's Brachetto), but
  current ampelography treats them as distinct varieties with different
  VIVC numbers (Braquet VIVC 1657, Brachetto VIVC 15630). Kept as a
  separate new grape rather than merging into the existing `Brachetto`
  entry.
- **`Nielluccio` = `Sangiovese`**: already merged correctly in
  `grapes.yaml` (as a synonym) — confirmed, added nothing new.
- **`Lledoner Pelut`**: ampelographically the same as `Garnacha Peluda` /
  "Grenache Poilu", and already listed as a synonym of `Garnacha Peluda`
  in the `es-n` slice's *research* file — but that file is not yet merged
  into `grapes.yaml`, so the validator rejects it today. It is only an
  accessory (not principal) grape in Côtes du Roussillon / Côtes du
  Roussillon Villages / Minervois-La Livinière, so I dropped it from those
  `grapes:` lists rather than add a duplicate grape entry; whoever merges
  `es-n` first should let the other pick it up automatically.
- **`Grès de Montpellier` parenting**: parented directly under
  `Languedoc-Roussillon` rather than `Languedoc`, since since May 2024 it
  is a standalone AOP rather than a Languedoc denomination; flagged in
  case reviewers prefer `Languedoc` as parent for continuity with its
  history.
- **Département-level IGPs (Gard, Hérault, Aude, Vaucluse)**: these
  overlap Rhône and Languedoc-Roussillon department boundaries. I parented
  Vaucluse under `Southern Rhône` (it is the Vaucluse département, core of
  southern Rhône) and Gard/Hérault/Aude under `Languedoc-Roussillon`
  (their vineyard area is overwhelmingly Languedoc); a retailer view might
  put Gard under Rhône instead since Costières de Nîmes/Duché d'Uzès sit
  in the Gard. Flagging for review.
- **`Méditerranée` (IGP) left without a parent**: it spans Provence, both
  Rhône halves, Languedoc-Roussillon and Corsica departments; per the
  brief's rule on overlay designations that cut across the main hierarchy,
  I gave it no parent rather than pick one sub-region.

## Warnings left unresolved (checker output)

All remaining `check fr-rpl` warnings are the harmless "already stripped by
lookup" kind for synonyms that keep a classification word inside them
(`IGP Île de Beauté`, `Corse (AOC)`, `Languedoc AOC`, `Picpoul de Pinet
AOC`, `Banyuls Grand Cru`, the `Pays d'Oc` variants, `Vin de Pays des
Alpilles`). Kept because each is a form actually seen on retail listings;
the checker itself notes the lookup already handles the classification-word
tail, so no functional risk.

## Label string → canonical (25 pairs)

| label string | kind | canonical | where seen (URL) |
|---|---|---|---|
| Côtes du Rhône | region | Côtes du Rhône | https://www.vins-rhone.com/ |
| CDR Villages | region | Côtes du Rhône Villages | https://www.wine-searcher.com/regions-cotes+du+rhone+villages |
| Chateauneuf du Pape | region | Châteauneuf-du-Pape | https://www.wine-searcher.com/regions-chateauneuf+du+pape |
| Cote-Rotie | region | Côte-Rôtie | https://www.wine-searcher.com/regions-cote+rotie |
| Crozes Hermitage | region | Crozes-Hermitage | https://www.wine-searcher.com/regions-crozes+hermitage |
| Beaumes de Venise | region | Beaumes-de-Venise | https://www.beaumesdevenise-aoc.fr/ |
| Cotes de Provence | region | Côtes de Provence | https://www.vinsdeprovence.com/ |
| Coteaux d'Aix | region | Coteaux d'Aix-en-Provence | https://fr.wikipedia.org/wiki/Coteaux_d%27Aix-en-Provence |
| Vin de Bellet | region | Bellet | https://www.wine-searcher.com/regions-bellet |
| Vin de Corse | region | Vin de Corse | https://www.inao.gouv.fr/node/8730 |
| Ile de Beaute | region | Île de Beauté | https://extranet.inao.gouv.fr/fichier/IGPIledeBeautePNO2022.pdf |
| Coteaux du Languedoc | region | Languedoc | https://fr.wikipedia.org/wiki/Languedoc_(AOC) |
| Languedoc Pezenas | region | Languedoc Pézenas | https://les5duvin.wordpress.com/2023/12/20/denominations-geographiques-complementaires-de-laoc-languedoc-3-languedoc-pezenas/ |
| Corbieres-Boutenac | region | Boutenac | https://www.inao.gouv.fr/produit/boutenac-18976 |
| Minervois La Liviniere | region | Minervois-La Livinière | https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000021231626/2011-10-11 |
| Blanquette de Limoux | region | Blanquette de Limoux | https://fr.wikipedia.org/wiki/Blanquette_de_limoux |
| Cotes du Roussillon Villages Latour de France | region | Côtes du Roussillon Villages Latour-de-France | https://fr.wikipedia.org/wiki/C%C3%B4tes_du_Roussillon_Villages |
| Muscat de Rivesaltes | region | Muscat de Rivesaltes | https://en.wikipedia.org/wiki/Muscat_de_Rivesaltes_AOC |
| Maury Sec | region | Maury Sec | https://www.roussillon.wine/vins-et-terroirs/nos-aoc-et-igp/aop-maury-sec/ |
| Pays d'Oc | region | Pays d'Oc | https://fr.wikipedia.org/wiki/Pays-d%27oc_(IGP) |
| Vin de Pays des Alpilles | region | Alpilles | https://fr.wikipedia.org/wiki/Alpilles_(IGP) |
| Tibouren | grape | Tibouren | https://fr.wikipedia.org/wiki/Tibouren |
| Braquet | grape | Braquet | https://en.wikipedia.org/wiki/Braquet |
| Vermentinu | grape | Vermentino | https://fr.wikipedia.org/wiki/Vermentino |
| Muscat d'Alexandrie | grape | Muscat of Alexandria | https://en.wikipedia.org/wiki/Muscat_of_Alexandria |

## Review (main session, 2026-09-26)

- `Boutenac`: parent `Corbières`, not `Languedoc-Roussillon`. It is the
  Corbières-Boutenac cru, and labels read "Corbières-Boutenac".
- `Grès de Montpellier`: parent `Languedoc`, the same as Pic Saint-Loup,
  Terrasses du Larzac and La Clape, which also left the Languedoc AOC to
  become their own AOCs.
- Accepted: Côtes du Roussillon as its own AOC under an unclassified
  Roussillon; Blanquette/Crémant de Limoux and Muscat de Rivesaltes split
  out; Boutenac rename; Méditerranée IGP as a parentless overlay; the
  department IGPs' parents; Braquet kept distinct from Brachetto.
- Grape reconciliation list: **Tibouren** was added as a new grape, but
  DNA work reports it identical to Rossese di Dolceacqua (`Rossese` is in
  grapes.yaml). Check VIVC before the QID run. **Lledoner Pelut** was
  dropped from the `grapes:` fields because es-n's Garnacha Peluda owns it;
  it can come back after the es-n merge.
- The 10 checker warnings are all classification words the lookup
  already strips.
- Merge (2026-09-26): `Folle Noire` (Fuella Nera) dropped, and removed
  from Bellet's `grapes:` field: no Wikidata item, so it would block the
  build.
