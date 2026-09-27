# hu: Hungary

**Country:** HU. **Slice:** all of Hungary, one agent.

**You own:** every existing HU entry and everything under it:
- **The wine regions (borrégiók)** as parents: Tokaj, Felső-Magyarország,
  Pannon, Balaton, Duna, Sopron (check the current six; the 22 historic
  districts sit under them). Classification: none for a borrégió.
- **The 22 wine districts (borvidékek)** and every **PDO (OEM)** in
  eAmbrosia, with classification `PDO`: Tokaj, Eger, Mátra, Bükk;
  Villány, Szekszárd, Pécs, Tolna; Badacsony, Balatonfüred-Csopak,
  Balaton-felvidék, Somló, Nagy-Somló, Zala, Balatonboglár, Balatonmelléke;
  Etyek-Buda, Mór, Neszmély, Pannonhalma; Kunság, Csongrád, Hajós-Baja;
  Sopron. Include the PDOs that are not districts (e.g. Debrői hárslevelű,
  Egri Bikavér is a wine name: see below).
- **The PGIs (OFJ)**: Duna-Tisza közi, Dunántúli, Felső-Magyarországi,
  Balatonmelléki, Zemplén, Balaton; classification `PGI`.
- **Tokaj detail:** the villages that appear on labels (Mád, Tarcal,
  Tállya, Tolcsva, Sárospatak, Erdőbénye, Mezőzombor, Bodrogkeresztúr,
  Sátoraljaújhely…), classification `Gemeinde`, children of Tokaj. Aim for
  10–15. No single dűlők (Szent Tamás, Úrágya, Betsek).

Not regions, keep them out: Aszú, Szamorodni, Eszencia, puttonyos
levels; Egri Bikavér and Szekszárdi Bikavér (wine styles; add them as
synonyms of Eger / Szekszárd only if labels use them as the place);
Superior, Grand Superior, Prémium tiers.

**Existing entries to fix:** Tokaj carries "Tokaji" (an adjective form:
keep, it is the label form), "Tokay" (the old English form: keep) and
"Tokaj-Hegyalja" (the historic name: keep). Check the other seven for
folded-in districts.

**Homonyms, record in the `.md`:** Tokaj (HU / SK: Slovakia's Vinohradnícka
oblasť Tokaj is not in scope; note it only).

**Not yours:** Slovakia. Nothing else in HU is split.

**Official register:** eAmbrosia (Hungary's PDOs and PGIs), then
winesofhungary.hu / the HNT list for the regions and districts. Count
PDOs against eAmbrosia.

**`grapes:` field, yes, where the PDO rules name grapes:** e.g. Tokaj:
Furmint, Hárslevelű, Sárgamuskotály, Zéta, Kövérszőlő, Kabar; Somló:
Juhfark, Furmint, Olaszrizling; Badacsony: Kéknyelű, Olaszrizling;
Villány: Cabernet Franc, Kékfrankos, Portugieser. Keep it to the grapes
the rules name as principal.

**Grapes file:** Hungarian names missing from `grapes.yaml`. Run
`context --grape` on each first; add only missing grapes and missing
synonyms: Sárgamuskotály (Muscat Blanc à Petits Grains: synonym, not a
new grape), Zéta (Oremus), Kövérszőlő, Kabar, Kövidinka, Ezerjó,
Budai Zöld, Királyleányka, Cserszegi Fűszeres, Irsai Olivér, Kadarka,
Bíborkadarka, Turán, Kékoportó (Portugieser synonym), Szürkebarát
(Pinot Gris synonym), Tramini (Traminer synonym). Furmint, Hárslevelű,
Kékfrankos, Olaszrizling, Juhfark and Kéknyelű exist: check only their
synonyms.
