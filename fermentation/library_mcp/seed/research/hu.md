Status: complete

# Hungary (hu) research notes

## Sources
- eAmbrosia (EU GI register) — spot-checked via national implementing pages; the EU's central UI is a JS app not fetchable directly, so used the Hungarian government's own wine-law portal (boraszat.kormany.hu / gi.kormany.hu) and TTB's mirror of the EU wine PDO/PGI name list, https://www.ttb.gov/system/files/images/pdfs/hungary.pdf (undated but reflects the pre-2020s EU-notified list; used as a base and cross-checked against current Hungarian sources for post-2020 changes).
- https://bor.hu/en/ (Magyar Bor / Wines of Hungary, official trade body) — six borrégiók and 22 borvidékek, current structure.
- https://en.wikipedia.org/wiki/Hungarian_wine — cross-check of the 22-district list.
- https://boraszat.kormany.hu/ (Hungarian wine law portal) — product descriptions (termékleírás) for Nagy-Somló/Somló merger, Debrői Hárslevelű, Csopak.
- https://somloiborvidek.hu/uj-eredetvedelmi-valtozasok/ — Nagy-Somló PDO withdrawn 1 Aug 2024, merged into Somló.
- Web searches for Tokaj villages, PGI (OFJ) list, and Felső-Pannon borrégió composition (accessed 2026-09-27).

## Borrégiók (6) — corrected from scope draft
The scope's six-region list named "Sopron" as a borrégió; the current official
grouping (2021 reform) instead uses **Felső-Pannon** ("Upper Pannon") as the
borrégió name, containing Sopron, Etyek-Buda, Mór, Neszmély and Pannonhalma.
Sopron itself is only a borvidék (district), same level as Eger or Villány,
so it stays a plain entry (matches the existing library row) and is not used
as a parent. The six borrégiók produced: Tokaj, Felső-Magyarország, Felső-Pannon,
Balaton, Duna, Pannon. Left without `classification` (informal groupings, not
themselves an EU PDO/PGI name), matching the existing convention for Balaton
and Sopron in the library (no classification).

## Homonyms
- Tokaj (HU) / Tokaj (SK, "Vinohradnícka oblasť Tokaj") — Slovak part out of scope, noted only.
- Balaton — the borrégió name and the OFJ/PGI "Balatoni" designation share the
  same word. Kept as one entry (existing library row) rather than a duplicate,
  see Uncertain calls.

## Counts
- Borrégiók: 6 official (Tokaj, Felső-Magyarország, Felső-Pannon, Balaton, Duna, Pannon) — 6 produced.
- Borvidékek (districts): 22 official — 22 produced (Tokaj; Eger, Mátra, Bükk; Sopron, Etyek-Buda, Mór, Neszmély, Pannonhalma; Badacsony, Balatonfüred-Csopak, Balaton-felvidék, Somló, Zala, Balatonboglár; Kunság, Csongrád, Hajós-Baja; Villány, Szekszárd, Pécs, Tolna).
- Extra PDOs that are not districts: Debrői Hárslevelű (Eger), Csopak (carved out of Balatonfüred-Csopak, 2017) — 2 produced. Left out: Egri Bikavér, Egri Bikavér Superior, Somlói Arany, Somlói Nászéjszakák bora, Izsáki Arany Sárfehér, Egerszóláti Olaszrizling, Villányi védett eredetű classicus — these are wine/style names layered on top of a district or village (grape blend + quality tier), not places; Egri Bikavér is already an existing synonym of Eger per scope, kept as-is.
- Nagy-Somló: TTB list still shows it as a separate PDO, but the Somló wine-region council withdrew the "Nagy-Somló" designation on 1 Aug 2024, merging it into "Somló". Kept only as a synonym of Somló (former name still likely to appear on older bottlings), not a separate entry.
- PGI (OFJ): 6 official (Balatonmelléki, Duna-Tisza közi, Dunántúli, Felső-Magyarországi, Zemplén, Balaton) — 5 produced as distinct entries + Balaton (see Uncertain calls, kept merged with the borrégió entry rather than duplicated).
- Tokaj villages: 11 of the historic 22 produced (target 10-15): Mád, Tarcal, Tállya, Tolcsva, Sárospatak, Erdőbénye, Mezőzombor, Bodrogkeresztúr, Sátoraljaújhely, Bodrogkisfalud, Rátka.
- Grapes file: 8 new grapes (Zéta, Kövérszőlő, Kabar, Kövidinka, Ezerjó, Budai Zöld, Bíborkadarka, Turán) + 4 existing grapes with added Hungarian synonyms (Fetească Regală/Királyleányka, Muscat Blanc à Petits Grains/Sárgamuskotály, Pinot Gris/Szürkebarát, Gewürztraminer/Tramini).
- Not added (no missing info found): Cserszegi Fűszeres, Irsai Olivér, Kadarka, Kékoportó/Portugieser, Furmint, Hárslevelű, Kékfrankos/Blaufränkisch, Olaszrizling/Welschriesling, Juhfark, Kéknyelű — all already fully covered in grapes.yaml.

## Changes to existing entries
- **Balaton**: dropped "Balatonfüred-Csopak" as a synonym (it is a separate PDO district, not a synonym of the whole Balaton borrégió) and gave it its own entry, parented to Balaton. Reason: scope flagged this as the folded-in-district pattern to fix.
- **Somló**: added classification PDO and synonyms "Somlói" and "Nagy-Somló" (former, now-withdrawn separate PDO — see Counts).
- **Eger, Villány, Szekszárd, Sopron, Badacsony, Tokaj**: added classification PDO (all are EU-registered PDO names; the existing rows had no classification) and added the adjectival label forms as synonyms where missing (Villányi, Szekszárdi, Soproni, Badacsonyi).
- No renames or re-parents beyond the Balatonfüred-Csopak split above.

## Homonyms
- Tokaj (HU) / Tokaj (SK) — Slovakia's "Vinohradnícka oblasť Tokaj" is out of scope, noted only, not touched.
- Balaton — used both as the informal borrégió (umbrella of six districts) and as one of the six PGI/OFJ names. See Uncertain calls.

## Uncertain calls
- **Balaton name collision**: the borrégió "Balaton" and the OFJ "Balaton" are the same string. Rather than duplicate the name (which the validator forbids) or classify the existing umbrella entry as PGI (which would be wrong for its role as a parent for Badacsony etc.), I kept a single unclassified "Balaton" entry serving both roles, matching the existing no-classification convention already used for this row and for Sopron. Flagging for review in case the two should be split with disambiguated names.
- **Csopak parent**: Csopak PDO's five constituent villages (Csopak, Paloznak, Lovas, Alsóörs, Felsőörs) sit inside the Balatonfüred-Csopak district's area but Csopak is independently registered. I parented Csopak under Balatonfüred-Csopak rather than directly under Balaton, matching how a retailer would nest it, but the two PDOs are legally siblings, not parent/child; if this reads wrong, Csopak could instead be a direct child of Balaton.
- **Fetească Regală / Királyleányka**: I added Királyleányka as a synonym of the existing "Fetească Regală" row rather than a new grape, since VIVC treats them as the same variety (Romanian Fetească Regală = Hungarian Királyleányka = German Königliche Mädchentraube). Flagging because this is a cross-border identity call, not a pure Hungarian one.
- **Debrői Hárslevelű grapes**: rules require both a minimum sugar/botrytis threshold and Hárslevelű as the base variety; I listed only Hárslevelű as the principal grape rather than adding minor blending varieties.

## 20-25 label string -> canonical pairs

| label string | kind | canonical | where seen |
|---|---|---|---|
| Tokaji | region | Tokaj | https://winesofhungary.hu/wine-regions/tokaj-wine-region/tokaj-wine-district |
| Tokay | region | Tokaj | https://www.ttb.gov/system/files/images/pdfs/hungary.pdf |
| Egri | region | Eger | https://boraszat.kormany.hu/eger |
| Egri Bikavér | region | Eger | https://en.wikipedia.org/wiki/Egri_Bikav%C3%A9r |
| Villányi | region | Villány | https://boraszat.kormany.hu/villany |
| Szekszárdi | region | Szekszárd | https://boraszat.kormany.hu/szekszard |
| Badacsonyi | region | Badacsony | https://boraszat.kormany.hu/badacsony |
| Somlói | region | Somló | https://somloiborvidek.hu/ |
| Nagy-Somló | region | Somló | https://somloiborvidek.hu/uj-eredetvedelmi-valtozasok/ |
| Soproni | region | Sopron | https://boraszat.kormany.hu/sopron |
| Balatonfüred-Csopaki | region | Balatonfüred-Csopak | https://boraszat.kormany.hu/balatonfured-csopak |
| Csopaki | region | Csopak | https://boraszat.kormany.hu/csopak |
| Mátrai | region | Mátra | https://bor.hu/en/ |
| Bükki | region | Bükk | https://bor.hu/en/ |
| Etyek-Budai | region | Etyek-Buda | https://bor.hu/en/etyek-budai-wine-district/ |
| Zalai | region | Zala | https://bor.hu/en/ |
| Kunsági | region | Kunság | https://bor.hu/en/ |
| Hajós-Bajai | region | Hajós-Baja | https://bor.hu/en/ |
| Zempléni | region | Zemplén | https://gi.kormany.hu/foldrajzi-arujelzok |
| Duna-Tisza-közi | region | Duna-Tisza közi | https://boraszat.kormany.hu/duna-tisza |
| Kékfrankos | grape | Blaufränkisch | https://bor.hu/en/ |
| Olaszrizling | grape | Welschriesling | https://boraszat.kormany.hu/badacsony |
| Kékoportó | grape | Portugieser | https://boraszat.kormany.hu/villany |
| Szürkebarát | grape | Pinot Gris | https://bor.hu/en/ |
| Sárgamuskotály | grape | Muscat Blanc à Petits Grains | https://boraszat.kormany.hu/tokaj |
| Tramini | grape | Gewürztraminer | https://bor.hu/en/ |
| Királyleányka | grape | Fetească Regală | https://en.wikipedia.org/wiki/Feteasc%C4%83_Regal%C4%83 |

## Review (main session, 2026-09-27)
- Hierarchy accepted: six borrégiók (Felső-Pannon replaces the scope's "Sopron"), 22 districts, Csopak nested under Balatonfüred-Csopak, the borrégió and PGI "Balaton" kept as one entry.
- Hungarian adjectival forms (Egri, Villányi, Tokaji…) are real label forms, not invented; kept. "Egri Bikavér" kept on Eger as the place labels name.
- Királyleányka → Fetească Regală accepted (VIVC).

**Merge note (2026-09-27):** Merged. Eight new grapes all resolved (Kövidinka via the "Dinka" item). No lock homonyms. Replay 0 changes.
