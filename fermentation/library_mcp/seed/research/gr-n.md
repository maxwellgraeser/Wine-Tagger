Status: complete

# gr-n: Greece, north, centre and Ionian — research notes

## Sources
- eAmbrosia (EU GI register) — https://ec.europa.eu/agriculture/eambrosia/geographical-indications-register/ (searched by product name; the DB has no browsable per-country list export, cross-checked each PDO/PGI individually).
- Wines of Greece (national body), Appellations & Classifications — https://winesofgreece.org/regions-wineries/appellations-and-classifications/ (accessed 2026-09-27).
- Wines of Greece, PGI Wines of Greece article — https://winesofgreece.org/articles/pgi-wines-of-greece/ (accessed 2026-09-27; "58 PGI area wines in 28 districts").
- Wines of Greece grape variety pages (Krassato, Stavroto, Asproudes, Batiki, Muscat of Cephalonia, Mesenikola) — winesofgreece.org, accessed 2026-09-27.
- greeceandgrapes.com variety pages (Vlachiko, Tsaoussi) — accessed 2026-09-27.


## Counts
- PDOs produced: 10 (Naoussa, Amyndeon, Goumenissa, Slopes of Meliton, Zitsa, Rapsani, Messenikola, Anchialos, Robola of Cephalonia, Mavrodaphne of Cephalonia, Muscat of Cephalonia) — matches the scope's named list exactly.
- Regional PGIs (macro, no children other than local zones): Macedonia, Thrace, Epirus, Thessaly, Central Greece, Attica, Ionian Islands = 7 (Macedonia and Attica already existed; the other 5 are new top-level entries).
- Local PGIs: Macedonia 23, Thrace 3, Epirus 2, Thessaly 7, Central Greece 10, Attica 9, Ionian Islands 7 = 61 total.
- Total regions in file: 80 (7 macro + 10 PDO + 61 local PGI + 2 unclassified: Attica already existed unclassified as a macro name, Cephalonia as an island grouping under Ionian Islands).
- Wines of Greece's own PGI article states "58 PGI area wines in 28 districts" nationwide (both slices combined), which is fewer than my 61 for this slice alone. I could not find a single browsable eAmbrosia export to reconcile this; my list follows the per-region breakdown on winesofgreece.org's Appellations & Classifications page, which is more granular and more recently updated than the "58" figure in the older PGI article. Flagged as an open question.
- Left out: I did not add "Verdea of Zakynthos" — Verdea is a traditional term/style (sun-dried straw wine) associated with Zakynthos, not itself a separate registered PGI zone; it would need confirmation as a distinct GI before inclusion.

## Changes to existing entries
- **Cephalonia**: dropped the synonym "Robola of Cephalonia" (it is now its own PDO entry, a child of Cephalonia, not a synonym of the island) and re-parented Cephalonia under new "Ionian Islands" (previously had no parent).
- **Rapsani**: added parent "Thessaly" (previously had no parent at all, which is the same bug pattern the brief calls out for Robertson) and added its grapes rule (Xinomavro, Krasato, Stavroto).
- **Attica**: unchanged in content, but now sits under the same file as a sibling to the new "Central Greece" macro region rather than absorbing its PGIs (Attica's own local PGIs like Markopoulo/Pallini stay children of Attica, not of Central Greece).

## Homonyms
- Macedonia (GR) vs North Macedonia — kept the GR entry named "Macedonia" per instructions.
- Thrace (GR) also names regions in Turkey and Bulgaria — kept the GR entry named "Thrace".
- Corfu's synonym "Kerkyra" and Zakynthos's synonym "Zante" are place names only, not shared with any grape.

## Uncertain calls
- **Central Greece as parent for Attica's PGIs**: winesofgreece.org's own prose groups Attiki, Markopoulo, Pallini etc. under "Sterea Ellada" in one place, but elsewhere and in general trade usage Attica is treated as its own top-level wine region (matching the existing library entry). I kept Attica separate per the scope's explicit instruction and put only Sterea-Ellada-proper zones (Evia, Thiva, Fthiotida, etc.) under "Central Greece".
- **Atalanti Valley / Opountia Locris/Lokrida**: sources give both names for what appears to be the same PGI zone in Fthiotida; I merged them as name + synonyms rather than two entries, but could not confirm from a primary register that they are identical rather than adjacent zones.
- **Krania vs Krannonas**: both appear as separate Thessaly PGI names in different secondary sources; kept as two separate entries since I found no evidence they are the same zone, but did not verify against eAmbrosia directly.
- **Batiki, Asproudes**: both are described as loosely-defined/umbrella names for one or more indistinct local white varieties (per Wines of Greece's own "Discover More" pages) rather than single VIVC-clean varieties. Added them as single new grapes per the scope's explicit list, but flagging the identity uncertainty here per the brief's guidance.
- **Halikouna, Slopes of Ainos, Metaxata, Mantzavinata**: these are small PGI zones physically within Corfu (Halikouna) or Cephalonia (the other three); I kept them as flat children of "Ionian Islands" rather than nesting under Corfu/Cephalonia, consistent with the two-level "regional > local" instruction, but noting the geographic nesting is deeper in reality.

## Label string -> canonical examples
| label string | kind | canonical | where seen (URL) |
|---|---|---|---|
| Naoussa PDO | region | Naoussa | https://winesofgreece.org/pdo/pdo-naoussa/ |
| Náoussa | region | Naoussa | https://winesofgreece.org/pdo/pdo-naoussa/ |
| Amyntaio | region | Amyndeon | https://winesofgreece.org/pdo/pdo-amynteo/ |
| Amynteo AOC | region | Amyndeon | https://winesofgreece.org/pdo/pdo-amynteo/ |
| Côtes de Meliton | region | Slopes of Meliton | https://winesofgreece.org/pdo/pdo-slopes-of-meliton/ |
| Plagies Melitona | region | Slopes of Meliton | https://winesofgreece.org/pdo/pdo-slopes-of-meliton/ |
| PGE Halkidiki | region | Halkidiki | https://winesofgreece.org/regions-wineries/appellations-and-classifications/ |
| Chalkidiki | region | Halkidiki | https://www.grapeguru.de/en/knowledge/wine-regions/chalkidiki |
| Agio Oros | region | Mount Athos | https://winesofgreece.org/pgi/mount-athos/ |
| Rapsani Reserve | region | Rapsani | https://grecianpurveyor.com/products/rapsani-pdo-reserve-2010-xinomavro-krassato-stavroto-blend |
| Mesenikola | region | Messenikola | https://winesofgreece.org/pdo/pdo-messenikola/ |
| Robola of Kefalonia | region | Robola of Cephalonia | https://winesofgreece.org/pdo/pdo-robola-of-cephalonia/ |
| Kefalonia | region | Cephalonia | https://thegreekwineexperience.com/index.php/kefalonia-and-its-grapes/ |
| Muscat of Kefalonia | region | Muscat of Cephalonia | https://winesofgreece.org/pdo/pdo-muscat-of-cephalonia/ |
| Zante | region | Zakynthos | https://www.winetourismgreece.com/greek-wine-regions/ionian-islands/ |
| Kerkyra | region | Corfu | https://exploringworldsoldandnew.com/world-cities/taste-world/taste-europe/taste-greece/greek-cuisine/greek-wines/ionian-wine/ |
| Thiva | region | Thiva | https://winesofgreece.org/regions-wineries/appellations-and-classifications/ |
| Evvia | region | Evia | https://winesofgreece.org/regions-wineries/appellations-and-classifications/ |
| Xynomavro | grape | Xinomavro | https://en.wikipedia.org/wiki/Xinomavro |
| Krassato | grape | Krasato | https://winesofgreece.org/articles/krassato/ |
| Vlahiko | grape | Vlachiko | https://gargantuanwine.com/2015/10/vlahiko/ |
| Tsaousi | grape | Tsaoussi | https://www.wine-searcher.com/grape-662-tsaoussi |
| Mavro Messenikola | grape | Mavro Messenikola | https://winesofgreece.org/pdo/pdo-messenikola/ |
| Asprouda | grape | Asproudes | https://winesofgreece.org/articles/asproudes/ |
| Vertzami | grape | Vertzami | https://www.winetourismgreece.com/greek-wine-regions/ionian-islands/ |


## Review (main session, 2026-09-27)
- **Atalanti Valley and Opountia Locris are separate PGIs** (Wines of Greece: the Atalanti Valley zone partly overlaps Slopes of Knimida and Opountia Lokridos). Split into two entries under Central Greece; "Valley of Atalanti" added as a synonym.
- **Asproudes dropped**: an umbrella name for several local white varieties ("the whites"), not one variety. Batiki kept provisionally; it goes if `resolve_qids` finds no grape-variety item.
- **Krania and Krannonas** kept as two PGIs.
- **PGI count:** not over-split. eAmbrosia registers far more than 58 Greek PGIs; Wines of Greece's "58" counts something narrower.
- Macedonia/Thrace homonyms are fine: lookups are country-scoped.

**Merge note (2026-09-27):** Greece merged (gr-n + gr-s). Dropped for lack of a Wikidata grape item: Stavroto, Tsaoussi, Goustolidi, Mavro Messenikola (gr-n); Dafni, Plyto, Kydonitsa, Fokiano, Begleri (its only QID is a fidget toy), Mavrothiriko (gr-s). They were also removed from the Rapsani, Messenikola and other PDO `grapes:` fields. gr-s's Wikipedia sources for Dafni and Plyto return 404. Lock: Thrace (GR) nulled (shared the historical-region QID with Thrace (TR)), Epirus (GR) nulled (matched the Roman province). "PGE Halkidiki" misses because "PGE" is not a stripped classification word (lookup-code idea: add PGE/POP). Replay 0 changes, 590 tests.
