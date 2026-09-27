Status: complete

# it-c1: Tuscany — research notes

## Sources
- https://www.disciplinare.it/vini-toscana.html — master list of Tuscany DOCG (11) / DOC (40) / IGT (6), consulted 2026-09-27. Used as the primary register for coverage and as fallback source for entries without a more specific citation below.
- https://www.regione.toscana.it/documents/10180/11927265/elenco_doc.pdf — Region of Tuscany official DOC/DOCG/IGT list (dated 2016, cross-checked against disciplinare.it for currency).
- https://www.chianticlassico.com/en/projects/le-unita-geografiche-aggiuntive-uga/ — Chianti Classico UGA (Additional Geographic Units), 2021.
- https://www.disciplinare.it/val-di-cornia-rosso-o-rosso-della-val-di-cornia-docg.html — Val di Cornia Rosso DOCG grapes.
- https://www.disciplinare.it/montecucco-sangiovese-docg-disciplinare-2024.html — Montecucco Sangiovese DOCG grapes, 2024 disciplinare.
- https://vernaccia.it/il-san-gimignano-doc/disciplinare/ and https://vernaccia.it/la-vernaccia-di-san-gimignano/disciplinare-vernaccia-san-gimignano/ — Consorzio del Vino Vernaccia di San Gimignano, showing Vernaccia di San Gimignano DOCG and San Gimignano DOC are two separate appellations of the same zone.
- https://italianwinecentral.com/denomination/santantimo-doc/ and https://wineandtravelitaly.com/wines/santantimo-doc/ — Sant'Antimo DOC grapes.
- https://en.wikipedia.org/wiki/Elba_DOC — Elba DOC and Elba Aleatico Passito DOCG.
- https://www.quattrocalici.it/tipologie-vino/vin-santo-del-chianti-doc/ and https://www.disciplinare.it/vin-santo-del-chianti-doc.html — Vin Santo del Chianti DOC grapes.

## Uncertain calls / left out
- Chianti Classico's 11 UGAs (Castellina, Castelnuovo Berardenga, Gaiole, Greve, Lamole, Montefioralle, Panzano, Radda, San Casciano, San Donato in Poggio, Vagliagli), introduced 2021 for Gran Selezione labels: left out. They are not separate appellations (no own DOCG status), just additional geographic units usable on one DOCG's label, closer to a Burgundy climat than a sub-appellation. Flagging as open question in case the tagger should treat them as regions later.
- "Chianti Superiore" (a quality tier, min. aging/yield rule inside the base Chianti DOCG, usable region-wide not tied to one subzone) is not a place and was left out as a region entry.
- Colli di Luni DOC and Val di Magra IGT touch Massa-Carrara (Tuscany) but their production area and history are centred on La Spezia (Liguria), owned by it-n. Left out of this file to avoid a duplicate/conflicting entry; flagging here so it-n's file is the authority.
- Alta Valle della Greve IGT, Colli della Toscana Centrale IGT, Montecastelli IGT: left out. These are legally registered IGTs but are not names seen on retail pages/labels in practice; only Toscana IGT and Costa Toscana IGT are.
- "Montepulciano" is both an Abruzzo grape and the Tuscan town; per scope instructions it is not added as a region synonym anywhere in this file (not on Vino Nobile di Montepulciano, Rosso di Montepulciano, or Vin Santo di Montepulciano).
- Homonyms: "Orcia" (Tuscany DOC) is unrelated to any other country's regions found so far. "Cortona" and "Carmignano" are unique names as far as searched. Will note more if found in later passes.

## Changes to existing entries
- Bolgheri: dropped "Bolgheri Sassicaia" from its synonyms. Bolgheri Sassicaia is its own DOC (Tenuta San Guido's single estate, Cabernet Sauvignon 80-100%), not a synonym of Bolgheri — added as its own child entry. Kept "Bolgheri Superiore" as a synonym since that is an ageing category inside Bolgheri DOC, not a separate place.
- Vernaccia di San Gimignano: dropped "San Gimignano" from its synonyms. San Gimignano DOC is a separate appellation covering red/rosé/Vin Santo from the same zone (Vernaccia di San Gimignano DOCG is white-only) — added "San Gimignano" as its own entry instead.
- Maremma: renamed to "Maremma Toscana" (was: "Maremma"), matching the DOC's actual registered name; "Maremma" kept as a synonym. "Maremma" alone is a much larger historic geographic area (spans into Lazio) than the DOC zone, so the DOC's own compound name is the safer canonical form.
- Morellino di Scansano: re-parented from "Maremma" to "Maremma Toscana" to follow the rename above.

## Grape identity note
- "Malvasia Bianca Lunga" (used for Vin Santo across Tuscany) is added as its own grape, distinct from the existing "Malvasia Bianca" entry (synonym "Malvasia Bianca di Candia"). These are different VIVC varieties despite the shared "Malvasia Bianca" wording; flagging in case a reviewer wants to double check.
- "Moscadello" (Moscadello di Montalcino) added as a new synonym of the existing "Muscat Blanc à Petits Grains" entry — it is the same variety as Moscato Bianco under a local name, not a distinct grape.

## Homonyms
- "Orcia" — no other-country match found.
- No other homonyms with other countries' regions found in this pass; Tuscany's DOC/DOCG names are largely unique compound names.

## Counts
- DOCG: 11 official (Brunello di Montalcino, Carmignano, Chianti, Chianti Classico, Elba Aleatico Passito, Montecucco Sangiovese, Morellino di Scansano, Suvereto, Val di Cornia Rosso, Vernaccia di San Gimignano, Vino Nobile di Montepulciano) — all 11 produced, plus Chianti's 7 named sub-zones as DOCG-level children (Rufina, Colli Senesi, Colli Fiorentini, Colli Aretini, Colline Pisane, Montalbano, Montespertoli), matching the existing library convention of giving each sub-zone `classification: DOCG`.
- DOC: 40 official — 39 produced. Left out: Colli di Luni DOC (home is Liguria/it-n; see above).
- IGT: 6 official — 2 produced (Toscana IGT, folded into Tuscany per existing convention; Costa Toscana IGT as its own entry). Left out 4 minor sub-IGTs rarely seen on labels (Alta Valle della Greve, Colli della Toscana Centrale, Montecastelli, Val di Magra — the last also cross-border with Liguria).
- New grapes: 4 (Foglia Tonda, Pugnitello, Vernaccia di San Gimignano, Malvasia Bianca Lunga). Existing-grape synonym additions: 1 (Moscadello → Muscat Blanc à Petits Grains).

## Biggest changes to existing entries
1. Bolgheri Sassicaia split out of Bolgheri's synonyms into its own DOC entry (it is a single-estate appellation, not a synonym).
2. San Gimignano split out of Vernaccia di San Gimignano's synonyms into its own DOC entry (red/rosé/Vin Santo DOC vs. the white-only DOCG).
3. Maremma renamed to Maremma Toscana (was: "Maremma") to match the DOC's actual name; Morellino di Scansano re-parented accordingly.

## Label string → canonical

| label string | kind | canonical | where seen |
|---|---|---|---|
| Chianti Rufina | region | Chianti Rufina | https://www.chiantirufina.com/en/the-consortium/specification/ |
| Rufina | region | Chianti Rufina | https://www.chiantirufina.com/en/the-consortium/specification/ |
| Colli Senesi | region | Chianti Colli Senesi | https://www.wineshop.it/it/blog/che-cose-il-chianti-colli-senesi.html |
| Gran Selezione | region | Chianti Classico | https://www.chianticlassico.com/en/ |
| Brunello | region | Brunello di Montalcino | https://www.agraria.org/vini/disciplinarechianti.htm |
| Brunello | grape | Sangiovese | grapes.yaml (existing synonym) |
| Vino Nobile | region | Vino Nobile di Montepulciano | https://www.disciplinare.it/vini-toscana.html |
| Bolgheri Superiore | region | Bolgheri | https://www.bolgheridoc.com/en/wines/ |
| Sassicaia | region | Bolgheri Sassicaia | https://www.tenutasanguido.com/en/sassicaia-2021-en |
| Scansano | region | Morellino di Scansano | https://www.disciplinare.it/vini-toscana.html |
| Maremma | region | Maremma Toscana | https://en.wikipedia.org/wiki/Maremma_Toscana |
| Barco Reale | region | Barco Reale di Carmignano | https://www.disciplinare.it/vini-toscana.html |
| San Gimignano | region | San Gimignano | https://vernaccia.it/il-san-gimignano-doc/disciplinare/ |
| Sant Antimo | region | Sant'Antimo | https://italianwinecentral.com/denomination/santantimo-doc/ |
| Val d'Arno di Sopra | region | Valdarno di Sopra | https://www.disciplinare.it/vini-toscana.html |
| Bianco Pisano di San Torpè | region | San Torpè | https://www.disciplinare.it/vini-toscana.html |
| Bianco Vergine della Valdichiana | region | Valdichiana Toscana | https://www.disciplinare.it/vini-toscana.html |
| Costa Toscana | region | Costa Toscana | https://www.disciplinare.it/costa-toscana-igt.html |
| Aleatico dell'Elba | region | Elba Aleatico Passito | https://en.wikipedia.org/wiki/Elba_DOC |
| Vinsanto del Chianti | region | Vin Santo del Chianti | https://www.disciplinare.it/vin-santo-del-chianti-doc.html |
| Prugnolo Gentile | grape | Sangiovese | grapes.yaml (existing synonym) |
| Sangioveto | grape | Sangiovese | grapes.yaml (existing synonym) |
| Moscadello | grape | Muscat Blanc à Petits Grains | https://www.disciplinare.it/vini-toscana.html |
| Vermentinu | grape | Vermentino | grapes.yaml (existing synonym) |

## Review (main session, 2026-09-27)

- `check it-c1 --tree`: 0 errors, 0 warnings. Hierarchy is sound: Bolgheri
  Sassicaia under Bolgheri, Suvereto and Val di Cornia Rosso under Val di
  Cornia, Montecucco Sangiovese under Montecucco, Morellino di Scansano
  under Maremma Toscana. Montalcino is an unclassified town parent.
- Accepted: the Bolgheri Sassicaia and San Gimignano splits, and the
  Maremma → Maremma Toscana rename ("Maremma" kept as a synonym).
- Colli di Luni is left to it-n, which has it under Liguria.
- Sangiovese local names were already canonical synonyms, so no grape
  change was needed there. Malvasia Bianca Lunga stays a separate grape.
- For the reconciliation pass: the existing `Malvasia Bianca` lists
  "Malvasia del Lazio" (Malvasia Puntinata, a different variety) and a
  bare "Malvasia" as synonyms. it-c2 was scoped to handle this; check at
  the Italy merge.
- `merge it-n it-c1 --check` passes.
- Merged 2026-09-27. `resolve_qids` found the new grape Vernaccia di San Gimignano to be the existing `Vernaccia` (Q1361955), so it became a synonym. Malvasia Bianca Lunga resolved to Maraština (Q1887929), which is the same variety by DNA; accepted.
