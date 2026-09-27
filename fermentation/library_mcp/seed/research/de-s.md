Status: complete

# de-s: Germany south/west — sources and notes

## Sources
- eAmbrosia (EU GI register) — PDOs = 13 Anbaugebiete, PGIs = Landwein areas.
- deutscheweine.de (Deutsches Weininstitut) — Bereiche per Anbaugebiet.
- de.wikipedia.org region pages (Baden, Pfalz, Rheinhessen, Württemberg, Franken) — Bereiche and label villages, cross-checked, accessed 2026-09-27.

- buzer.de, "§ 2 WeinV Landweingebiete" (official statutory list of the 26 German Landwein areas), consolidated text accessed 2026-09-27.
- BLE (Bundesanstalt für Landwirtschaft und Ernährung) product specification PDF for "Rheinischer Landwein".
- bergstraesser-wein.de (Weinbauverband Hessische Bergstraße) — Bereiche and villages for Hessische Bergstraße.
- rheinhessen.de/bereich — Bereiche and villages for Rheinhessen.
- deutsche-weinstrasse.de and pfalz.de — label villages for Pfalz.

## Counts
- Baden: 9 official Bereiche (Badische Bergstraße, Bodensee, Breisgau, Kaiserstuhl, Kraichgau, Markgräflerland, Ortenau, Tauberfranken, Tuniberg). All 9 produced.
- Pfalz: 2 official Bereiche (Mittelhaardt-Deutsche Weinstraße, Südliche Weinstraße). Both produced.
- Rheinhessen: 3 official Bereiche (Bingen, Nierstein, Wonnegau). All 3 produced.
- Franken: 3 official Bereiche (Maindreieck, Mainviereck, Steigerwald). All 3 produced.
- Württemberg: 5 official Bereiche (Remstal-Stuttgart, Württembergisch Unterland, Kocher-Jagst-Tauber, Oberer Neckar, Württembergischer Bodensee). All 5 produced.
- Hessische Bergstraße: 2 official Bereiche (Starkenburg, Umstadt). Both produced.
- Label villages: 42 across all six Anbaugebiete (9 Mittelhaardt, 7 Südliche Weinstraße, 6 Rheinhessen, 5 Baden, 6 Franken, 4 Württemberg, 2 Hessische Bergstraße), within the scope's 35–55 aim. Left out: full Gemeinde rolls (hundreds of villages per Anbaugebiet) — only the trade-relevant/label-leading ones above were added, per scope.
- Landwein: 10 entries covering my Anbaugebiete out of the 26 statutory Landweingebiete nationwide — the other 16 are outside my scope (Mosel/Saar/Ruwer, Ahr, Rheingau, Nahe, Mittelrhein, Sachsen, Saale-Unstrut and non-wine-growing states) or de-n's.
- Grapes: 4 new (Acolon, Samtrot, Cabernet Dorsa, Rotberger) + 1 existing-grape synonym addition (Müllerrebe → Pinot Meunier). Everything else on the scope's grape list already existed in `grapes.yaml` with the needed German synonym present (checked with `context --grape`, see list below), so nothing further was added for: Silvaner, Dornfelder, Blauer Portugieser, Lemberger/Blaufränkisch, Trollinger/Schiava Grossa, Schwarzriesling/Pinot Meunier, Grauburgunder/Ruländer/Pinot Gris, Weißburgunder/Pinot Blanc, Gutedel/Chasselas, Scheurebe, Huxelrebe, Regent, Muskateller, Auxerrois, Gewürztraminer/Traminer, Blauer Zweigelt. Schillerwein and Rotling excluded as styles, not grapes, per scope.

## Changes to existing entries
- Baden: removed "Kaiserstuhl" as a synonym of Baden per scope instruction; added Kaiserstuhl as its own Bereich entry, child of Baden.
- Franken, Hessische Bergstraße, Württemberg, Pfalz, Rheinhessen: kept all existing synonyms unchanged.
- No other renames or re-parents to existing entries.

## Homonyms
- "Bergstraße" / "Bergstrasse" wording: Hessische Bergstraße (mine) and Badische Bergstraße (Baden Bereich, also mine, but a distinct place). Not a cross-country homonym, but flagged since the two names are easy to confuse in snippets.
- No cross-country homonyms found among this file's names (Nierstein, Bingen, Kaiserstuhl, Ortenau, Durbach, Würzburg, etc. are not used as wine-region names elsewhere as far as I found).

## Uncertain calls
- "Badisches Frankenland" is the historical/older name for the Bereich now officially called "Tauberfranken" (per de.wikipedia). Treated as a former-name synonym of Tauberfranken, not a separate Bereich, since current official sources list only one Bereich there.
- **Nierstein and Bingen name collisions.** The Bereich Nierstein and the Gemeinde Nierstein (and likewise Bereich Bingen / Gemeinde Bingen am Rhein) share the same bare name. Since a country may not have two regions with the same name/synonym, I did not create separate Gemeinde entries for Nierstein or Bingen; instead their adjectival label forms ("Niersteiner", "Binger") are synonyms on the Bereich entry. This means a snippet that names the village "Nierstein" bare (not adjectival) resolves to the Bereich, which is the closest available match and still correct at the Anbaugebiet/Bereich level, but loses the finer Gemeinde-level precision. Flagging for reviewer judgment.
- Landwein parents: Pfälzer Landwein, Badischer Landwein, Landwein Main, Schwäbischer Landwein, Landwein Neckar, and Starkenburger Landwein each map closely enough to one Anbaugebiet that I gave them that Anbaugebiet as `parent`. Rheinischer Landwein, Landwein Oberrhein, Landwein Rhein-Neckar and Taubertäler Landwein cross Anbaugebiet and/or Land borders (e.g. Landwein Oberrhein spans Baden and Pfalz; Taubertäler Landwein spans Baden's Tauberfranken and Württemberg's Kocher-Jagst-Tauber; Rheinischer Landwein covers Rheinhessen and areas outside my scope) so I left them without a `parent`. A reviewer with the full statutory area maps could reconsider.
- Umstadt (Hessische Bergstraße's second Bereich) has almost no commercial label presence found in this research pass; included for coverage completeness per the official register but I could not confirm a widely used label village within it, so none is listed.

## 20–25 "label string → canonical" pairs

| label string | kind | canonical | where seen (URL) |
|---|---|---|---|
| Forster | region | Forst | https://www.pfalz.de/de/pfalz-geniessen/pfaelzer-wein/weinanbaugebiet-pfalz/mittelhaardt |
| Niersteiner | region | Nierstein | https://www.rheinhessen.de/bereich |
| Dürkheimer | region | Bad Dürkheim | https://www.pfalz.de/de/pfalz-geniessen/pfaelzer-wein/weinanbaugebiet-pfalz/mittelhaardt |
| Württembergisch Unterland | region | Württembergisch Unterland | https://www.deutscheweine.de/anbaugebiet/71/wuerttemberg |
| Mittelhaardt/Deutsche Weinstraße | region | Mittelhaardt-Deutsche Weinstraße | https://de.wikipedia.org/wiki/Pfalz_(Weinbaugebiet) |
| Rheinpfalz | region | Pfalz | https://www.deutscheweine.de/anbaugebiet/68/pfalz |
| Rhenish Hesse | region | Rheinhessen | https://www.deutscheweine.de/anbaugebiet/69/rheinhessen |
| Wachenheimer | region | Wachenheim | https://www.pfalz.de/de/pfalz-geniessen/pfaelzer-wein/weinanbaugebiet-pfalz/mittelhaardt |
| Kallstadter | region | Kallstadt | https://www.pfalz.de/de/pfalz-geniessen/pfaelzer-wein/weinanbaugebiet-pfalz/mittelhaardt |
| Ihringer | region | Ihringen | https://www.wine-searcher.com/regions-ihringen |
| Oberrotweiler | region | Oberrotweil | https://en.wikipedia.org/wiki/Vogtsburg |
| Durbacher | region | Durbach | https://www.durbach.de/weindorf/natur-landschaft/ortenau |
| Randersackerer | region | Randersacker | https://de.wikipedia.org/wiki/Franken_(Weinbaugebiet) |
| Iphöfer | region | Iphofen | https://de.wikipedia.org/wiki/Franken_(Weinbaugebiet) |
| Würzburger | region | Würzburg | https://de.wikipedia.org/wiki/Franken_(Weinbaugebiet) |
| Franconia | region | Franken | https://www.deutscheweine.de/anbaugebiet/66/franken |
| Badische Bergstrasse | region | Badische Bergstraße | https://de.wikipedia.org/wiki/Baden_(Weinbaugebiet) |
| Heppenheimer | region | Heppenheim | https://www.bergstraesser-wein.de/hessische-bergstrasse/anbaugebiet/weinorte |
| Pfälzer Landwein | region | Pfälzer Landwein | https://www.buzer.de/gesetz/6206/a86414.htm |
| Schwäbischer Landwein | region | Schwäbischer Landwein | https://de.wikipedia.org/wiki/Schw%C3%A4bischer_Landwein |
| Sämling 88 | grape | Scheurebe | https://en.wikipedia.org/wiki/Scheurebe |
| Ruländer | grape | Pinot Gris | https://en.wikipedia.org/wiki/Pinot_gris |
| Müllerrebe | grape | Pinot Meunier | https://www.lwg.bayern.de/weinbau/rebe_weinberg/070516/index.php |
| Weissburgunder | grape | Pinot Blanc | https://en.wikipedia.org/wiki/Pinot_blanc |
| Lemberger | grape | Blaufränkisch | https://en.wikipedia.org/wiki/Blaufr%C3%A4nkisch |
| Blauer Portugieser | grape | Portugieser | https://en.wikipedia.org/wiki/Portugieser |
| Rotberger | grape | Rotberger | https://en.wikipedia.org/wiki/Rotberger |


## Review (main session, 2026-09-27)
- Hierarchy checked with `check --tree`: Bereich counts match, Kaiserstuhl
  moved out of Baden's synonyms, no overlay zone given children.
- Fixed invented adjectival forms: villages ending in -er take no suffix
  on labels ("Birkweiler Kastanienbusch"), so removed Birkweilerer,
  Frankweilerer, Leinsweilerer, Maikammerer. Achkarrener → Achkarrer,
  Sommerhausener → Sommerhäuser.
- Accepted: Nierstein and Bingen as Bereich entries carrying the
  adjectival village forms; cross-border Landwein left as roots.
- Dropped Samtrot at merge: no Wikidata item (it is a Pinot Meunier mutation).
