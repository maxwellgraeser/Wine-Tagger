Status: complete

# it-c2: Umbria, Marche, Lazio, Abruzzo, Molise

## Sources
- Federdoc production-area pages (DOCG/DOC lists), https://www.federdoc.com/en/production-areas/{umbria,marche,lazio,abruzzo,molise}/ (accessed 2026-09-27).
- IGT lists cross-checked against agraria.org "Vini Italiani IGT" pages and Wikipedia "List of Italian IGT wines" (accessed 2026-09-27).
- Wikipedia region/denomination pages for grape-rule detail (Abruzzo_wine_region, Montefalco_DOC, Orvieto_DOC, Marino_DOC, Lacrima_di_Morro_d'Alba) (accessed 2026-09-27).
- Grape identity cross-checked against Wine-Searcher grape pages, Vinorandum, Quattrocalici, italianwinegirl.com (accessed 2026-09-27).

## Counts (running)

- Umbria: 2 DOCG + 13 DOC + 6 IGT (region-wide Umbria IGT + 5 sub-IGT) per Federdoc/agraria.org, all produced.
- Marche: 5 DOCG + 15 DOC + region-wide IGT only, all produced.
- Lazio: 3 DOCG + 27 DOC (26 here, Orvieto counted under Umbria since it straddles) + 6 IGT, all produced.
- Abruzzo: 3 DOCG + 7 DOC + 8 IGT, all produced.
- Molise: 4 DOC + 2 IGT, all produced.
- Total: 101 region entries, 8 new grapes + 1 existing-grape update (Grechetto).
- Left out: no official unit knowingly omitted. The region-wide catch-all denominations "Abruzzo DOC" and "Molise DOC" are not separate entries: their names equal the region name, and the lookup already strips the trailing "DOC", so they resolve to the existing bare "Abruzzo" / "Molise" entries.

## Changes to existing entries
1. **Split "Montefalco"** (was a single DOCG entry with synonyms "Sagrantino di Montefalco", "Montefalco Sagrantino", "Montefalco Rosso") into two real denominations: "Montefalco" DOC (base red/white, synonym "Montefalco Rosso") and a new child "Montefalco Sagrantino" DOCG. These are legally separate appellations over the same zone, not synonyms of one wine.
2. **Split "Rosso Conero"** (previously carried synonym "Conero") into "Rosso Conero" DOC and a new child "Conero" DOCG (the Riserva-style promotion), since Conero DOCG is its own denomination with stricter rules, not a synonym.
3. **Split "Montepulciano d'Abruzzo"**: removed "Colline Teramane" as a synonym and gave it its own entry "Colline Teramane" DOCG (parent Montepulciano d'Abruzzo), and added the sibling DOCG "Casauria". Colline Teramane and Casauria are sub-zone DOCGs, not alternate names of the base DOC.

## Homonyms
- "Roma" (Lazio DOC) — could clash conceptually with "Rome" as a place name generally, but no other wine region in the library is named Roma.
- "Marino" (Lazio DOC) is also a common surname/place name elsewhere, no other region entry conflicts.
- "Terracina" and "Cori" are also Lazio town names with no homonym collision found in other countries' entries.

## "Montepulciano" ambiguity
Per scope: "Montepulciano" is both the Abruzzo grape and the Tuscan town (Vino Nobile di Montepulciano, owned by it-c1). Not added as a region synonym anywhere in this file. The Abruzzo/Lazio/Marche region entries here use grape "Montepulciano" only in the `grapes:` field of DOCs whose disciplinare names it, never as a place synonym.

## Uncertain calls
- **Cesanese identity**: the disciplinari for Cesanese del Piglio, Cesanese di Affile and Cesanese di Olevano Romano name "Cesanese" generically, which in practice covers two distinct clones (Cesanese d'Affile and Cesanese Comune). The existing library canonical "Cesanese" is generic; I did not split it, following the disciplinare's own generic wording, but flag this as unresolved identity granularity.
- **Malvasia Puntinata**: the prized Frascati-zone Malvasia biotype, sometimes labelled by name. Not added — unclear if VIVC treats it as distinct from Malvasia Bianca di Candia (already a synonym of "Malvasia Bianca"). Left unresolved rather than guessed.
- **Aprilia, Castelli Romani, Cerveteri, Circeo, Colli della Sabina, Colli Etruschi Viterbesi, Genazzano, Montecompatri Colonna, Nettuno, Roma, Tarquinia, Velletri, Vignanello, Zagarolo (all Lazio DOC), and "I Terreni di Sanseverino" (Marche DOC)**: these permit varietal or multi-varietal wines without one clearly dominant grape in the disciplinare as summarized by secondary sources; left without a `grapes:` field rather than guess a principal variety. Reviewer should double check against the actual disciplinare text if grape tagging for these is wanted.
- **Rosso Orvietano / Lago di Corbara parent**: both cover red blends in territory overlapping Orvieto DOC, but are separate legal DOCs; parented directly to Umbria rather than nested under Orvieto since they are not sub-appellations of it.
- **Colli del Trasimeno "Gamay"**: sources call a local red variety "Gamay del Trasimeno", but ampelographers identify it as a Grenache Noir biotype, not true Gamay. Not added as a grape or synonym; flagged here only.
- **Terre di Offida, I Terreni di Sanseverino**: recent (post-2010) Marche DOCs with sparse English-language documentation of their exact permitted varieties; entries added without `grapes:`.

## Label string → canonical

| label string | kind | canonical | where seen (URL) |
|---|---|---|---|
| Sagrantino di Montefalco | region | Montefalco Sagrantino | https://en.wikipedia.org/wiki/Montefalco_DOC |
| Torgiano Rosso Riserva DOCG | region | Torgiano Rosso Riserva | https://www.federdoc.com/en/production-areas/umbria/ |
| Trasimeno | region | Colli del Trasimeno | https://www.federdoc.com/en/production-areas/umbria/ |
| Colli Amerini | region | Amelia | https://en.wikipedia.org/wiki/Umbria_wine_region |
| Jesi | region | Verdicchio dei Castelli di Jesi | https://www.wine-searcher.com/regions-marche |
| Cònero | region | Conero | https://www.federdoc.com/en/production-areas/marche/ |
| Piceno | region | Rosso Piceno | https://www.federdoc.com/en/production-areas/marche/ |
| Falerio dei Colli Ascolani | region | Falerio | https://www.federdoc.com/en/production-areas/marche/ |
| Piglio | region | Cesanese del Piglio | https://www.wine-searcher.com/regions-cesanese+del+piglio |
| Olevano Romano | region | Cesanese di Olevano Romano | https://www.federdoc.com/en/production-areas/lazio/ |
| Moscato di Terracina | region | Terracina | https://www.federdoc.com/en/production-areas/lazio/ |
| del Frusinate | region | Frusinate | https://www.assovini.it/italia/lazio/item/2044-frusinate-o-del-frusinate-igt |
| Osco | region | Terre degli Osci | https://www.quattrocalici.it/denominazioni/osco-o-terra-degli-osci-igt/ |
| Pentro | region | Pentro d'Isernia | https://www.federdoc.com/en/production-areas/molise/ |
| Colline Teramane Montepulciano d'Abruzzo | region | Colline Teramane | https://www.federdoc.com/en/production-areas/abruzzo/ |
| Terre di Casauria | region | Casauria | https://www.federdoc.com/en/production-areas/abruzzo/ |
| Histonium | region | Vastese | https://en.wikipedia.org/wiki/Abruzzo_wine_region |
| Tullum | region | Terre Tollesi | https://www.federdoc.com/en/production-areas/abruzzo/ |
| Cannellino | grape/style-adjacent (region) | Cannellino di Frascati | https://www.federdoc.com/en/production-areas/lazio/ |
| Ribona | grape | Maceratino | https://en.wikipedia.org/wiki/Maceratino |
| Biancame | grape | Bianchello | https://en.wikipedia.org/wiki/Biancame |
| Nero Buono di Cori | grape | Nero Buono | https://savortheharvest.com/a-lazio-winning-wine-grape-nero-buono/ |
| Trebbiano d'Abruzzo (grape on Cerasuolo labels) | grape | Trebbiano Abruzzese | https://en.wikipedia.org/wiki/Abruzzo_wine_region |
| Spoletino | grape | Trebbiano Spoletino | https://theitalianwinegirl.com/trebbiano-spoletino-the-white-side-of-umbria/ |
| Grechetto di Orvieto | grape | Grechetto | https://en.wikipedia.org/wiki/Grechetto |

Status: complete

## Review (main session, 2026-09-27)

- `check it-c2 --tree`: 0 errors. The 3 warnings are the inherited
  "Umbria/Marche/Lazio IGT" synonyms. They're harmless, so they stay.
- Accepted the splits: Montefalco DOC with its child Montefalco Sagrantino
  DOCG ("Sagrantino di Montefalco" kept as a synonym), Rosso Conero with
  its child Conero DOCG, and Montepulciano d'Abruzzo with its children
  Colline Teramane and Casauria. The Verdicchio Riserva DOCGs are children
  of their base DOCs.
- The 15 multi-varietal Lazio/Marche DOCs with no `grapes:` field are fine.
- For the reconciliation pass: `Malvasia Bianca` still carries "Malvasia
  del Lazio" (= Malvasia Puntinata, a separate VIVC variety) as a synonym.
  Split them or drop the synonym. The Cesanese d'Affile vs Comune question
  stays open.
- `merge it-n it-c1 it-c2 --check` passes.
- Merged 2026-09-27. Added "Colline Teramane Montepulciano d'Abruzzo" (the DOCG's official name) as a synonym of Colline Teramane.
