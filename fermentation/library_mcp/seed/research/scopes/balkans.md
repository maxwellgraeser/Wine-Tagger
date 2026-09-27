# balkans: Croatia, Slovenia, Bosnia and Herzegovina, North Macedonia

**Country:** HR, SI, BA, MK. **Slice:** four countries, one agent, because
they share grapes under different names.

**You own:** every existing HR, SI, BA and MK entry and everything under it.
- **Croatia (HR):** the four regions (Istra i Kvarner, Dalmacija, Središnja
  bregovita Hrvatska, Slavonija i hrvatsko Podunavlje), the subregions,
  and the eAmbrosia PDOs a label uses (e.g. Hrvatska Istra, Dingač,
  Postup, Pelješac, Hvar, Brač, Korčula, Komarna, Primošten, Plešivica,
  Kutjevo, Ilok…). Keep the existing English names (`Istria`, `Dalmatia`,
  `Slavonia`) and carry the Croatian as synonyms.
- **Slovenia (SI):** the three regions (Primorska, Podravje, Posavje) and
  their nine districts (Goriška Brda, Vipavska dolina, Kras, Slovenska
  Istra; Štajerska Slovenija, Prekmurje; Bizeljsko-Sremič, Dolenjska, Bela
  krajina). The traditional PDOs Teran (Kras), Cviček (Dolenjska) and
  Metliška črnina / Belokranjec are wine names: add them as synonyms of
  their district only if labels use them as the place; otherwise note them.
- **Bosnia and Herzegovina (BA):** Herzegovina (Mostar, Čitluk, Trebinje,
  Ljubuški, Međugorje as the label areas). No EU register; use the
  national list if one exists, and say what you used.
- **North Macedonia (MK):** the three regions (Povardarie / Vardar River
  Valley, Pčinja-Osogovo, Pelagonija-Polog) and the districts labels use
  (Tikveš, Skopje, Veles, Gevgelija-Valandovo, Ovče Pole, Ohrid, Prilep,
  Bitola…).

Aim for 60–80 entries in total.

**Existing entries to fix:** `Podravje` carries "Štajerska" / "Stajerska",
which is its district Štajerska Slovenija: make the district its own entry
and move the synonyms. Check `Istria` (HR) and `Goriška Brda` for the same.

**Homonyms, record in the `.md`:** Istria (HR Hrvatska Istra / SI
Slovenska Istra: name the SI one `Slovenska Istra`, with "Slovenian
Istria" as a synonym), Styria (AT Steiermark / SI Štajerska Slovenija),
Brda / Collio (SI / IT: Collio stays Italian), Macedonia (GR region /
MK country: do not add "Macedonia" as an MK region name).

**Not yours:** Serbia, Montenegro, Kosovo, Bulgaria, Romania (not in
Wave 3). Austria's Steiermark and Italy's Collio are merged; don't touch
them.

**Official register:** eAmbrosia for HR and SI PDOs, the Slovenian and
Croatian wine-law district lists, then national sources for BA and MK.

**`grapes:` field, yes, where the rules name grapes:** e.g. Dingač and
Postup: Plavac Mali; Teran (Kras): Refošk; Hrvatska Istra: Malvazija
Istarska, Teran; Tikveš: none unless the rules name them.

**Grapes file:** Balkan names and synonyms missing from `grapes.yaml`.
Run `context --grape` on each first; add only missing grapes and missing
synonyms. Most exist already (Graševina, Plavac Mali, Pošip, Malvazija
Istarska, Teran, Žilavka, Blatina, Vranec, Rebula, Zelen, Pinela, Babić,
Tribidrag): check the synonyms, e.g. Laški Rizling (Welschriesling),
Frankovka / Modra frankinja (Blaufränkisch), Šipon / Moslavac (Furmint),
Refošk (Refosco), Kraljevina, Grk, Debit, Maraština (already exists as
Malvasia Bianca Lunga's target: check), Crljenak Kaštelanski (Tribidrag),
Stanušina, Žametovka, Kratošija, Smederevka, Temjanika (Muscat Blanc).
Terrano / Teran vs Refosco is on the reconciliation list: add synonyms
only where VIVC agrees, and note the question.
