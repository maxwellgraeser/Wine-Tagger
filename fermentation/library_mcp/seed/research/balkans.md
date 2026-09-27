Status: complete

# Balkans (HR, SI, BA, MK) research notes

## Sources
- Croatia: Pravilnik o vinogradarstvu (NN 81/2022), FAOLEX copy https://faolex.fao.org/docs/pdf/cro234935.pdf — official region/subregion/vinogorje hierarchy (Art. 4, Annex I), consulted 2026-09-27.
- Croatia PDOs: eAmbrosia register entries for Hrvatska Istra (EUGI00000010725) and related Croatian wine PDOs, https://ec.europa.eu/agriculture/eambrosia/geographical-indications-register/
- Croatia background: https://en.wikipedia.org/wiki/Croatian_wine ; https://total-croatia-news.com/wine/wine-regions/four-croatian-wine-regions-2/ ; https://www.winewithseth.com/winewiki/zoi-zozp-croatian-protected-designations-of-origin/
- Slovenia: TTB list of Slovenian protected wine names (derived from EU/national register), https://www.ttb.gov/system/files/images/pdfs/slovenia.pdf ; https://www.tasteslovenia.si/en/taste-slovenia/wine/ ; https://en.wikipedia.org/wiki/Slovenian_wine
- Bosnia and Herzegovina: no EU/national wine-law register found; used trade sources: https://www.decanter.com/wine/herzegovina-a-wine-lovers-guide-527465/ , https://wine.ba/wine-routes , https://en.wikipedia.org/wiki/Bosnia_and_Herzegovina_wine
- North Macedonia: no EU register (non-EU); used https://www.jancisrobinson.com/articles/north-macedonia-new-wine-story , https://wineguide.wein.plus/wine-regions/north-macedonia , https://balkanwines.org/north-macedonia/
- Grape identity checks: VIVC-derived facts via Wikipedia/wein.plus/wine-searcher pages cited inline below.


## Counts
- Croatia (HR): 26 entries — 4 regions, 6 podregija/subregions, 12 named PDOs (Ilok, Kutjevo, Istria/Hrvatska Istra, Primošten, Pelješac, Dingač, Postup, Komarna, Hvar, Brač, Korčula, Plešivica), plus the existing Slavonia and Croatian Danube podregija entries. Left out: the ~40 finer "vinogorje" units in the Pravilnik (e.g. Zapadna Istra, Knin, Zaprešić) — too granular for what labels use, per scope's "levels labels use". Also left out Croatia's separate broad PGI zones (Kontinentalna Hrvatska / Primorska Hrvatska) since the scope named the four Pravilnik regions specifically, not this older three-zone PGI scheme; flagging in case a later pass wants them.
- Slovenia (SI): 12 entries — 3 regions + 9 districts, all confirmed as TTB/EU-protected names. Full official set, nothing left out.
- Bosnia and Herzegovina (BA): 6 entries — Herzegovina plus the five label towns named in the scope. No official register exists; used trade/wine-route sources.
- North Macedonia (MK): 11 entries — 3 regions + 8 districts named in the scope. Left out Kočani-Vinica, Strumica-Radoviško (mentioned in some sources as further Vardar-area districts) since they weren't in the scope's named list and are less commercially seen; can be added later if needed.
- Grapes: 13 entries — 3 existing-grape synonym additions (Furmint/Moslavac, Muscat Blanc à Petits Grains/Temjanika, Malvasia Bianca Lunga/Maraština+Rukatac) and 10 new grapes (Kraljevina, Grk, Debit, Žlahtina, Škrlet, Bogdanuša, Vugava, Žametovka, Stanušina, Smederevka).

## Changes to existing entries
- `Pelješac`: re-parented from `Dalmatia` to `Central and South Dalmatia` (the podregija the law places it in) and its `Dingač` synonym removed — Dingač is a separate registered PDO nested inside Pelješac, not a synonym of it.
- `Hvar`: re-parented from `Dalmatia` to `Central and South Dalmatia` for the same reason (Dalmatia now only holds the three podregija as direct children).
- `Podravje`: dropped the `Štajerska`/`Stajerska` synonyms; `Štajerska Slovenija` is now its own child entry (per the scope's fix instruction) carrying those forms as its own name/synonym.
- `Istria`: re-parented under a new `Istria and Kvarner` region entry (previously top-level with no parent) and given `synonyms: ["Istra", "Hrvatska Istra", "Croatian Istria"]` plus `classification: PDO` and `grapes`, since it is the registered "Hrvatska Istra" PDO.

## Homonyms
- Istria: Croatian `Istria` (Hrvatska Istra) vs Slovenian `Slovenska Istra` — kept distinct names per the scope's instruction; "Slovenian Istria" is a synonym only of the Slovenian entry.
- Styria: Slovenia's `Štajerska Slovenija` vs Austria's `Steiermark` — separate countries, not touched (Austria is another slice's scope).
- Brda/Collio: Slovenia's `Goriška Brda` (synonym `Brda`) is adjacent to Italy's `Collio`, which stays under its Italian name in Italy's own file; not merged.
- Macedonia: the MK region names deliberately avoid the bare word "Macedonia" (used instead: `Vardar River Valley`, `Pelagonia-Polog`, `Pčinja-Osogovo`) to avoid collision with the Greek region of the same name.
- Kras / Karst: Slovenia's `Kras` (synonym `Karst`) is the cross-border karst plateau also present on the Italian side (as `Carso` DOC, not in this file).

## Uncertain calls
- Teran / Refosco: `grapes.yaml` already merges Teran and Refošk into `Refosco`. The scope flags this as an open reconciliation question (Slovenian Teran and Friulian Refosco are treated by some ampelographers as the same clone, by others as distinct populations). Left the existing merge untouched; not adding further Balkan Teran synonyms beyond what already exists.
- Tribidrag / Kratošija / Zinfandel: `grapes.yaml` already lists Kratošija as a synonym of the Tribidrag/Zinfandel/Primitivo cluster. Some Montenegrin/Balkan sources treat Kratošija as a genetically distinct old variety rather than identical to Tribidrag. Flagging only; did not change the existing merge.
- Smederevka vs Dimyat: some sources treat Smederevka (Serbia/Macedonia) as the same variety as Bulgaria's Dimyat (already in `grapes.yaml`). Kept Smederevka as its own new entry rather than merging, since the identity claim is inconsistent across sources and Dimyat's home is outside this scope.
- Kraljevina: one glossary source lists "Piros Oporto"/"Roter Portugieser" among its synonyms, which would imply identity with Blauer Portugieser — this looks like a source error (Kraljevina is white, Portugieser lines are red) and was not carried over as a synonym.
- Traditional Slovenian PDO wine-names (`Cviček`, `Belokranjec`, `Metliška črnina`, `Bizeljčan`, and `Teran, Kras` as an EU-registered compound name) are themselves EU-protected designations of origin, but they name a wine style/blend tied to a district, not the place itself, and `Teran`/`Cviček` collide with grape/wine-style meanings — left them out of `synonyms` per the scope's instruction and noted here instead.
- Croatia's broader PGI-style zones (`Kontinentalna Hrvatska`, `Primorska Hrvatska`, and their `Istočna`/`Zapadna kontinentalna` split) were not added — the scope named the four Pravilnik regions specifically; flagging in case broad-zone label strings are wanted later.

## Label string -> canonical examples

| label string | kind | canonical | where seen (URL) |
|---|---|---|---|
| Hrvatska Istra | region | Istria | https://ec.europa.eu/agriculture/eambrosia/geographical-indications-register/details/EUGI00000010725 |
| Peljesac | region | Pelješac | https://croatianwinetrails.com/komarna-region-the-peljesac-peninsula/ |
| Dingac | region | Dingač | https://en.wikipedia.org/wiki/Dinga%C4%8D_(wine) |
| Korcula | region | Korčula | https://www.wineandmore.com/stories/korcula-black-island-for-white-wines/ |
| Vrbnička Žlahtina | grape | Žlahtina | https://krk.hr/en/gastronomy/vrbnicka-zlahtina/ |
| Posip | grape | Pošip | https://en.wikipedia.org/wiki/Po%C5%A1ip |
| Plavac Mali | grape | Plavac Mali | https://sunandsoilshop.com/blogs/news/dalmatian-wine-guide |
| Babic | grape | Babić | https://total-croatia-news.com |
| Grasevina | grape | Welschriesling | (existing grapes.yaml synonym) |
| Sremič-Bizeljsko | region | Bizeljsko-Sremič | https://www.ttb.gov/system/files/images/pdfs/slovenia.pdf |
| Vipavska dolina | region | Vipava Valley | https://www.tasteslovenia.si/en/taste-slovenia/wine/primorska-wine-growing-region/ |
| Slovenian Istria | region | Slovenska Istra | https://www.ttb.gov/system/files/images/pdfs/slovenia.pdf |
| Karst | region | Kras | https://wineguide.wein.plus/wine-regions/primorska |
| Modra Frankinja | grape | Blaufränkisch | (existing grapes.yaml synonym) |
| Sipon | grape | Furmint | (existing grapes.yaml synonym) |
| Moslavac | grape | Furmint | https://en.wikipedia.org/wiki/Furmint |
| Rukatac | grape | Malvasia Bianca Lunga | https://en.wikipedia.org/wiki/Mara%C5%A1tina |
| Maraština | grape | Malvasia Bianca Lunga | https://en.wikipedia.org/wiki/Mara%C5%A1tina |
| Medjugorje | region | Međugorje | https://en.wikipedia.org/wiki/Medjugorje |
| Citluk | region | Čitluk | https://wine.ba/wine-routes |
| Zilavka | grape | Žilavka | (existing grapes.yaml synonym) |
| Tikves | region | Tikveš | https://wineguide.wein.plus/wine-regions/north-macedonia |
| Vranac | grape | Vranac | (existing grapes.yaml canonical) |
| Kratosija | grape | Zinfandel | (existing grapes.yaml synonym) |
| Temjanika | grape | Muscat Blanc à Petits Grains | https://en.wikipedia.org/wiki/Tamjanika |
| Skrlet | grape | Škrlet | https://total-croatia-news.com/wine/grapes/the-indigenous-grapes-of-croatia-skrlet/ |

## Review (main session, 2026-09-27)
- `Štajerska Slovenija`: its synonym "Slovenske Gorice" is a sub-area (vinorodni okoliš) inside the district, so it's removed. "Štajerska" / "Stajerska" (moved off Podravje) and "Slovenian Styria" added, as the scope asked.
- `Primorska`: dropped the bare synonym "Primorje", which also names Croatia's Hrvatsko primorje.
- `Goriška Brda` `grapes:` trimmed to Ribolla Gialla; the PDO rules don't single out Merlot or Cabernet Sauvignon.
- Primorska, Podravje and Posavje are Slovenia's PGIs (eAmbrosia), not PDOs; reclassified.
- Hierarchy otherwise accepted (Croatia per NN 81/2022; Dingač and Postup under Pelješac).

**Merge note (2026-09-27):** Merged. Smederevka → synonym of the existing `Dimyat` (they share a Wikidata item; VIVC lists Smederevka as a Dimiat synonym). Dropped for lack of a Wikidata item: Grk, Debit, Škrlet. Lock nulled as homonyms: Prilep (MK; a village in Kosovo), Trebinje (BA; Albania), Čitluk (BA; Serbia). Replay 0 changes.
