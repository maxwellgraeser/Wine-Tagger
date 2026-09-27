Status: complete

# emed: Turkey, Georgia, Lebanon — research notes

## Sources

- Georgian appellations: https://en.wikipedia.org/wiki/List_of_Georgian_wine_appellations (accessed 2026-09-27) — cross-checked against https://www.winesgeorgia.com/appellations/ (National Wine Agency data reproduced, accessed 2026-09-27). The National Wine Agency's own site (wine.gov.ge) returned 403/JS-only content to automated fetch; used the two secondary sources above, which both cite the Agency's PDO register and agree except for one appellation ("Akhoebi", see Uncertain calls).
- Georgian administrative/viticultural regions: https://en.wikipedia.org/wiki/Georgian_wine (accessed 2026-09-27).
- Turkey: https://en.wikipedia.org/wiki/Turkish_wine (accessed 2026-09-27) for regions/sub-areas; TÜRKPATENT geographical-indication portal (turkpatent.gov.tr, ci.turkpatent.gov.tr) searched for wine GIs — as of 2026-09-27 the only wine-adjacent GI hits found are Bozcaada Çavuş (grape) and Avşa Adakarası Şarabı (a specific wine, registered 2025); no GI covers a broad appellation area the way DOC/AOC does elsewhere. Turkish areas below are therefore all informal (no `classification`) unless noted.
- Lebanon: no formal appellation register exists. Used https://en.wikipedia.org/wiki/Lebanese_wine and general trade usage (Wine-Searcher regional pages, producer back-labels) for the areas actually printed on labels. Union Vinicole du Liban's own site did not publish a region list as of 2026-09-27.

## Counts

(filled in as sections complete)

## Changes to existing entries

- `Thrace` (TR): dropped `Marmara` as a synonym and added `Marmara` as its own sibling region. Marmara is the larger administrative/wine region that contains Thrace (European side) plus the Sea-of-Marmara islands and Yalova/Bursa area on the Anatolian side; Thrace is not a synonym for it. `Marmara` has no parent (it is a top-level TR region like Aegean); `Thrace` keeps no parent either, since in wine-trade usage "Thrace" is used on its own and is not consistently nested under "Marmara" on labels. Noted as a decision to revisit if reviewers disagree.
- `Racha` (GE): dropped `Khvanchkara` as a synonym. Khvanchkara is itself a PDO appellation (a place and a semi-sweet red wine style), so per the scope note it gets its own entry, parented to `Racha`. Added `Racha-Lechkhumi and Kvemo Svaneti` (the official administrative-region name) as a synonym instead.

## Homonyms

- Thrace: also a region of Greece (GR) and Bulgaria (BG). Not this scope's concern beyond noting it.
- Cappadocia/Kapadokya: unique to Turkey, no clash found.
- Mediterranean: used here as a broad TR wine-region label; "Mediterranean" as a bare word is not a protected or exclusive name and could plausibly appear for other countries' coastal zones, but no existing library entry collides.

## Uncertain calls

- Georgian PDO count: sources report "29" or "30" PDOs but only ~28 distinct names could be confirmed by name across two independent sources. One source (foodfuntravel.com) lists "Akhoebi" as a Kakheti red-Saperavi PDO, but this does not appear in the Wikipedia appellations list or in the National Wine Agency's own site metadata found via search; likely a mis-transcription of "Akhasheni" or "Napareuli". Left out; flagging here rather than guessing.
- Kisi Magrani: the Wikipedia appellations list gives this as a PDO name (white, Kisi grape) but the geography (village Magraani/Manavi area, Kakheti) is thin in secondary sources; kept as a Kakheti child appellation on the strength of the one detailed source, `grapes: [Kisi]`.
- Shida Kartli / Kvemo Kartli: these are Kartli's own administrative sub-divisions and the natural parents for Atenuri/Okami/Asuretuli Shala (Shida Kartli) and Bolnisi (Kvemo Kartli). To keep the hierarchy shallow and match how labels are actually described (rarely naming these sub-divisions), all four appellations are parented directly to `Kartli` rather than adding two more region levels. Flagging in case reviewers prefer the fuller hierarchy.
- Bozcaada: administratively part of Çanakkale (Marmara region) but wine trade often groups it with the Aegean/North Aegean islands. Parented to `Marmara` here since that is its administrative and touristic grouping; noting the Aegean-trade convention as an alternative.
- Turkey's "Eastern Anatolia" here also absorbs label references to south-eastern towns (Diyarbakır, Mardin-adjacent) since the country-wide split given in the scope has no separate "Southeastern Anatolia" region; flagging in case a future slice wants that split.


## Counts (final)

- Georgia: 9 top-level regions (Kakheti, Kartli, Imereti, Racha, Guria, Samegrelo, Adjara, Meskheti, Abkhazia) + 27 PDO appellations (19 Kakheti, 3 Racha-Lechkhumi, 4 Kartli, 1 Imereti, 1 Samegrelo) = 36 region entries. Official sources report "29" or "30" total PDOs; 27 confirmed by name across two independent sources (see Uncertain calls for the gap).
- Turkey: 7 top-level regions + 17 sub-areas (Şarköy, Mürefte, Gelibolu, Kırklareli, Tekirdağ, Bozcaada, Denizli, Manisa, Izmir, Urla, Çeşme, Cappadocia, Kalecik, Elazığ, Diyarbakır, Malatya, Tokat) = 24 region entries. All informal (no legal appellation-wide GI exists in Turkey as of 2026-09-27).
- Lebanon: 7 region entries (Bekaa Valley, West Bekaa, Zahlé, Baalbek, Mount Lebanon, Batroun, Jezzine). No formal register.
- Total: 67 region entries, 0 errors/warnings from the checker.
- Grapes: 19 new (11 Georgian, 6 Turkish, 2 Lebanese), 0 "existing" entries needed new synonyms — the grapes named in the scope (Mtsvane Kakhuri, Okuzgozu, Bogazkere, Kalecik Karasi) were already present in `grapes.yaml`.

## Homonyms (full list)

- Thrace: also GR and BG.
- Cappadocia/Kapadokya: unique.
- Mediterranean (TR): generic descriptive name, no clash with an existing library entry, but could recur for other Mediterranean-coast countries in future work.
- Georgia (country) vs. Georgia (US state): explicitly not added per scope instruction.
- Macedonia: not in this scope, not touched.

## 20–25 label string → canonical pairs

| label string | kind | canonical | where seen (URL) |
|---|---|---|---|
| Kakhetia | region | Kakheti | https://en.wikipedia.org/wiki/Georgian_wine |
| Racha-Lechkhumi | region | Racha | https://en.wikipedia.org/wiki/Georgian_wine |
| Khvanchkara | region | Khvanchkara | https://en.wikipedia.org/wiki/List_of_Georgian_wine_appellations |
| Kindzmarauli | region | Kindzmarauli | https://en.wikipedia.org/wiki/List_of_Georgian_wine_appellations |
| Tsinandali | region | Tsinandali | https://en.wikipedia.org/wiki/List_of_Georgian_wine_appellations |
| Mtsvane Kakhuri | grape | Mtsvane | grapes.yaml (existing synonym) |
| Okuzgozu | grape | Öküzgözü | grapes.yaml (existing synonym) |
| Bogazkere | grape | Boğazkere | grapes.yaml (existing synonym) |
| Kalecik Karasi | grape | Kalecik Karası | grapes.yaml (existing synonym) |
| Mujuretuli | grape | Mujuretuli | https://en.wikipedia.org/wiki/List_of_Georgian_wine_appellations |
| Tsitska | grape | Tsitska | https://en.wikipedia.org/wiki/Georgian_wine |
| Turkish Thrace | region | Thrace | https://en.wikipedia.org/wiki/Turkish_wine |
| Kapadokya | region | Cappadocia | https://en.wikipedia.org/wiki/Turkish_wine |
| Tenedos | region | Bozcaada | https://en.wikipedia.org/wiki/Turkish_wine |
| Güney (Denizli) | region | Denizli | https://en.wikipedia.org/wiki/Turkish_wine |
| Urla | region | Urla | https://en.wikipedia.org/wiki/Turkish_wine |
| Elazig | region | Elazığ | https://en.wikipedia.org/wiki/Turkish_wine |
| Kalecik | region | Kalecik | https://en.wikipedia.org/wiki/Turkish_wine |
| Emir | grape | Emir | https://en.wikipedia.org/wiki/Turkish_wine |
| Sultaniye | grape | Sultaniye | https://en.wikipedia.org/wiki/Turkish_wine |
| Papazkarasi | grape | Papazkarası | https://en.wikipedia.org/wiki/Turkish_wine |
| Bornova Misketi | grape | Bornova Misketi | https://en.wikipedia.org/wiki/Turkish_wine |
| Beqaa Valley | region | Bekaa Valley | https://en.wikipedia.org/wiki/Lebanese_wine |
| Zahle | region | Zahlé | https://en.wikipedia.org/wiki/Lebanese_wine |
| Obeideh | grape | Obeidi | https://en.wikipedia.org/wiki/Lebanese_wine |
| Merwah | grape | Merwah | https://en.wikipedia.org/wiki/Lebanese_wine |

## Review (main session, 2026-09-27)
- Hierarchy accepted (Marmara split from Thrace, Khvanchkara under Racha, Kartli without the Shida/Kvemo level).
- Denizli: dropped "Güney", "Çal" and the bare "Cal" (districts inside the province, not names for it). Eastern Anatolia: dropped "Southeastern Anatolia" (a different region).
- Bornova Misketi is a synonym of Muscat Blanc à Petits Grains, not a new grape. Removed Mujuretuli's self-synonym.
- Sultaniye keeps "Sultana" (the same variety as Thompson Seedless; no other entry claims it).

**Merge note (2026-09-27):** Merged. Dropped for lack of a Wikidata grape item, and removed from the PDO `grapes:` fields: Asuretuli Shavi, Chkhaveri, Krakhuna, Otskhanuri Sapere, Takveri, Tsitska, Usakhelouri (GE), Emir (TR), Merwah (LB). Candidates for the reconciliation pass. No lock homonyms. Replay 0 changes.
