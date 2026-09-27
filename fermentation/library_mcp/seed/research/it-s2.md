Status: complete

# it-s2: Calabria, Sicily, Sardinia — research notes

## Sources
- MASAF elenchi e disciplinari (register): https://www.masaf.gov.it/flex/cm/pages/ServeBLOB.php/L/IT/IDPagina/4625
- MASAF regional summary PDF (2011, used only for sub-zone/synonym detail, cross-checked against current pages): https://www.masaf.gov.it/flex/files/8/8/c/D.c98d43be48c9b307022a/Vini_DOCG_DOC_IGT_suddivisi_per_regione.pdf
- Registro nazionale delle varietà di vite / disciplinari: catalogoviti.politicheagricole.it (per-denomination disciplinare pages, various `scheda_denom.php?q=` ids, accessed 2026-09-27)
- Quattrocalici (Sicilia, Sardegna, Calabria denominazioni and disciplinari pages), accessed 2026-09-27
- Disciplinare.it (disciplinare texts), accessed 2026-09-27
- sardegnaagricoltura.it official DOC/DOCG/IGT lists, accessed 2026-09-27
- Federdoc "I vini italiani a denominazione d'origine 2025": https://www.federdoc.com/new/wp-content/uploads/2025/06/Booklet-2025_WEB.pdf

## Counts

- **Calabria:** 1 DOCG (Cirò Classico, promoted from Cirò in 2023 — EU reg. 2025/1518), 9 base DOC (Bivongi, Cirò, Greco di Bianco, Lamezia, Melissa, Sant'Anna di Isola Capo Rizzuto, Savuto, Scavigna, Terre di Cosenza) + 6 Terre di Cosenza sub-zones (Donnici, Pollino, San Vito di Luzzi, Verbicaro, Esaro, Condoleo, Colline del Crati — 7 sub-zones), 10 IGT (Calabria + 9 named zones). All produced.
- **Sicily:** 1 DOCG (Cerasuolo di Vittoria), 23 base DOC (matches the official count) + 4 sub-zones (Pachino/Eloro, Feudo dei Fiori & Bonera/Menfi, Rayana/Sciacca), 7 IGT (Terre Siciliane folded into "Sicily" as a synonym per existing convention; 6 produced as separate entries: Avola, Camarro, Fontanarossa di Cerda, Salemi, Salina, Valle Belice). All produced.
- **Sardinia:** 1 DOCG (Vermentino di Gallura, existing), 17 base DOC (matches the official sardegnaagricoltura.it list) + 4 sub-zones (Oliena/Nepente di Oliena, Capo Ferrato, Jerzu under Cannonau di Sardegna; Mogoro under Sardegna Semidano), 15 IGT (Isola dei Nuraghi folded into "Sardinia" per existing convention; 14 produced as separate entries).
- Left out: Cerasuolo di Vittoria's own "Classico" sub-zone (Acate/Comiso/Vittoria) — kept as a synonym, not a separate entry, since it has no independent legal status (unlike Cirò Classico, which was promoted to a full DOCG). Same treatment for Alcamo Classico.
- Grapes file: 9 new grapes (Magliocco Canino, Magliocco Dolce, Mantonico, Greco Nero, Nasco, Vernaccia di Oristano, Girò, Semidano, Cagnulari) + 2 existing-grape synonym additions (Malvasía Aromática, Perricone).

## Changes to existing entries

1. **Cirò**: removed `Cirò Classico` from its synonyms — Cirò Classico became its own DOCG in 2023 (EU reg. 2025/1518), so it is now a separate child entry (parent: Cirò), not a synonym of the base DOC. This is the "sub-appellation folded as synonym" mistake pattern.
2. **Cerasuolo di Vittoria**: removed `Vittoria` from its synonyms — Vittoria DOC (varietal Frappato/Nero d'Avola wines) and Cerasuolo di Vittoria DOCG (the Frappato+Nero d'Avola blend) are two separate, currently-active denominations covering an overlapping zone; the scope notes list them separately for a reason. Added Vittoria as its own entry.
3. Added a `grapes:` field to the existing entries that lacked one: Cirò, Etna, Marsala, Cerasuolo di Vittoria, Pantelleria, Menfi, Noto, Faro, Cannonau di Sardegna, Carignano del Sulcis, Vermentino di Gallura, Vermentino di Sardegna.

## Homonyms

- No region name in this scope duplicates a wine region name in another country that I found (Cirò, Etna, Marsala, Pantelleria, Cannonau di Sardegna, etc. are all uniquely Italian). Flagging none.

## Uncertain calls

- **Sicilia DOC / Terre Siciliane IGT**: both are region-wide (whole-island) designations with their own disciplinari (Sicilia DOC even has grape-of-composition rules: white ≥50% Ansonica/Catarratto/Grillo/Grecanico, red ≥50% Nero d'Avola/Frappato/Nerello Mascalese/Perricone). I kept them folded as synonyms of "Sicily" rather than separate entries, following the existing library convention for whole-region DOC/IGT (Toscana IGT → Tuscany, Puglia IGT → Puglia, Veneto IGT → Veneto). This means Sicilia DOC's own grape rules are not recorded anywhere. Flag for review if the convention should change.
- Skipped `grapes:` for several small, multi-varietal west-Sicily DOCs where no single "principal" variety stood out in what I found: Contea di Sclafani, Contessa Entellina, Delia Nivolelli, Erice, Salaparuta, Sambuca di Sicilia, Santa Margherita di Belice.
- Considered but did **not** add as new grapes (all are secondary/blending components named in disciplinari I read, not principal, and not in the scope's explicit grape list): Nocera, Marsigliana Nera, Guarnaccia (bianca/nera), Pecorello, Grecanico Bianco, Corinto Nero, Damaschino, Pascale. Flag if any should be added.
- `Malvasía Aromática` synonym `Malvasia di Lipari` collides with the region name `Malvasia delle Lipari` (checker warning). This is an inherent overlap in Italian usage — the grape and the wine share the name — and the scope note explicitly asked for the Italian grape-name synonym to be added, so I kept it and dropped only the exact-duplicate form `Malvasia delle Lipari` from the grape's synonyms (kept as the region's own name).
- Canonical grape name chosen as `Mantonico` (bare form used in the scope note); `Mantonico Bianco` is the fuller ampelographic name and is listed as a synonym.
- `Cagliari` DOC absorbed the old separate `Malvasia di Cagliari`, `Monica di Cagliari` and `Moscato di Cagliari` DOCs in the 2011 reform (they no longer appear as independent denominations on sardegnaagricoltura.it); `Girò di Cagliari`, `Nasco di Cagliari` and `Nuragus di Cagliari` remained independent. I did not add the old absorbed names as synonyms of `Cagliari` since I could not confirm they are still used on current labels.
- `Terre di Cosenza` absorbed the pre-2011 independent DOCs `Donnici`, `Pollino`, `San Vito di Luzzi` and `Verbicaro` as sub-zones; I modeled these (plus `Esaro`, `Condoleo`, `Colline del Crati`) as child DOC entries of Terre di Cosenza rather than synonyms, per the sub-appellation rule. Note: IGT zones named `Condoleo` and `Esaro` also exist (informal-tier, same geographic name, coexisting with the stricter DOC sub-zone of the same name) — I did not add separate IGT entries for these two names to avoid a same-country name collision; the DOC sub-zone entry is kept as the sole match.

## 20-25 label string → canonical pairs

| label string | kind | canonical | where seen (URL) |
|---|---|---|---|
| Cirò Classico | region | Cirò Classico | https://www.disciplinare.it/ciro-classico-docg-proposta-disciplinare-di-produzione-2023.html |
| Ciro Rosso | region | Cirò | https://www.quattrocalici.it/tipologie-vino/ciro-doc-rosso-classico-superiore-riserva/ |
| Gaglioppo | grape | Gaglioppo | https://shop.zito.it/vini-pregiati/42-greco-nero-vino-Calabria-igt-rosso.html |
| Greco Nero | grape | Greco Nero | https://florwine.com/i-vitigni/greco-nero/ |
| Magliocco | grape | Magliocco Dolce | https://www.ilcalicediebe.com/2017/04/07/magliocco-lautoctono-sovrano-delle-terre-di-cosenza/ |
| Mantonico Bianco | grape | Mantonico | https://www.vivino.com/US/en/grisolia-calabria-mantonico-bianco/w/3137728 |
| Terre di Cosenza | region | Terre di Cosenza | https://www.topfooditaly.net/prodotto/terre-di-cosenza-doc/ |
| Etna Rosso | region | Etna | http://catalogoviti.politicheagricole.it/scheda_denom.php?t=dsc&q=2120 |
| Nerello Mascalese | grape | Nerello Mascalese | https://webdivino.it/it/blog/nerello-mascalese |
| Cerasuolo di Vittoria Classico | region | Cerasuolo di Vittoria | https://theconnectedtable.com/traveling-sicilys-cerasuolo-di-vittoria-docg-wine-trail/ |
| Frappato | grape | Frappato | https://en.wikipedia.org/wiki/Frappato |
| Nero d'Avola | grape | Nero d'Avola | https://www.quattrocalici.it/tipologie-vino/sicilia-doc-nero-d-avola/ |
| Calabrese | grape | Nero d'Avola | http://catalogoviti.politicheagricole.it/scheda_denom.php?t=dsc&q=2274 |
| Passito di Pantelleria | region | Pantelleria | https://www.quattrocalici.it/wp-content/uploads/2021/05/sicilia_doc.pdf |
| Zibibbo | grape | Muscat of Alexandria | https://www.italiaatavola.net (Pantelleria/Marsala usage) |
| Eloro Pachino | region | Pachino | https://www.assovini.it/italia/sicilia/item/2331-eloro-doc-sottozona-pachino |
| Inzolia | grape | Ansonica | https://www.disciplinare.it/sicilia-doc.html |
| Malvasia di Lipari | grape | Malvasía Aromática | https://consorziomalvasiadellelipari.it/la-malvasia/ |
| Malvasia delle Lipari | region | Malvasia delle Lipari | https://www.quattrocalici.it/denominazioni/malvasia-delle-lipari-doc/ |
| Cannonau | grape | Grenache | https://www.sardegnaagricoltura.it/documenti/14_43_20130321091725.pdf |
| Nepente di Oliena | region | Oliena | https://www.sardegnaagricoltura.it/documenti/14_43_20130321091725.pdf |
| Vermentino di Gallura | region | Vermentino di Gallura | https://www.sardegnaagricoltura.it/argomenti/prodottitipici/vini/docg.html |
| Girò di Cagliari | region | Girò di Cagliari | https://www.assovini.it/italia/sardegna/item/416-giro-di-cagliari-doc |
| Bovale Sardo | grape | Bovale | https://www.disciplinare.it/mandrolisai-doc.html |
| Nuragus di Cagliari | region | Nuragus di Cagliari | https://www.vinook.it/vino-bianco/vino-bianco-sardo/nasco-di-cagliari.asp |
| Vernaccia di Oristano | grape | Vernaccia di Oristano | https://it.wikipedia.org/wiki/Vernaccia_di_Oristano |


## Review (main session, 2026-09-27)

- `check it-s2 --tree`: 0 errors. The sub-zone parents are right: Donnici
  and the others under Terre di Cosenza, Feudo dei Fiori and Bonera under
  Menfi, Pachino under Eloro, Rayana under Sciacca, and Oliena, Capo
  Ferrato and Jerzu under Cannonau di Sardegna.
- Accepted the Cirò Classico DOCG and Vittoria DOC splits.
- The warning that "Malvasia di Lipari" is both a grape synonym and a
  region is accepted. It's the same grape-and-wine overlap as Vernaccia di
  San Gimignano.
- The "Sicilia DOC" folded into Sicily stays, following the Toscana
  convention.
- Merged 2026-09-27. Magliocco Dolce shared a QID with the existing `Magliocco` (Q17116350) and became its synonym, with Arvino and Guarnaccia Nera. Cagnulari is Graciano (Q119794) and became its synonym. Girò was dropped for lack of a Wikidata item, along with the Girò di Cagliari grape rule. Added "Eloro Pachino" as a synonym of Pachino.
