Status: complete

# de-n: Germany, north and east — sources and notes

## Sources
- eAmbrosia GI register (DE PDOs/PGIs): https://ec.europa.eu/geographical-indications-register/eambrosia-public-api (Anbaugebiete = 13 PDOs; Landwein = 26 PGIs), consulted 2026-09.
- BLE / Weinverordnung (Landweingebiete list, § 2 WeinV): https://www.buzer.de/gesetz/6206/a86414.htm
- Deutsches Weininstitut (deutscheweine.de) Anbaugebiet pages for Bereiche and villages.
- German Wikipedia per-Bereich articles (Bereich Johannisberg, Bereich Walporzheim/Ahrtal, Mosel_(Weinanbaugebiet), Mittelrhein_(Weinanbaugebiet), Nahe_(Weinanbaugebiet), Sachsen_(Weinanbaugebiet), Saale-Unstrut-Region), consulted 2026-09.
- eAmbrosia technical files (PDF) for Ahrtaler Landwein and Rheinburgen-Landwein confirming registration and delimited area.

## Counts
- Anbaugebiete in scope: 7 (Mosel, Rheingau, Nahe, Mittelrhein, Ahr, Saale-Unstrut, Sachsen) — all pre-existing, kept.
- Bereiche: Mosel 6 (Bernkastel, Burg Cochem, Obermosel, Moseltor, Saar, Ruwertal); Rheingau 1 (Johannisberg); Nahe 1 (Nahetal); Mittelrhein 2 (Loreley, Siebengebirge); Ahr 1 (Walporzheim/Ahrtal); Saale-Unstrut 2 (Schloss Neuenburg, Thüringen); Sachsen 2 (Meißen, Elstertal). All included — full official set for the 7 Anbaugebiete.
- Landwein: included Landwein der Mosel, Landwein der Saar, Landwein der Ruwer, Rheinburgen-Landwein, Rheingauer Landwein, Nahegauer Landwein, Ahrtaler Landwein, Mitteldeutscher Landwein, Sächsischer Landwein (9). Left out "Rheinischer Landwein": its spec area is Rheinhessen (de-s), not the Rhine banks in my Anbaugebiete — despite the name, so it is not mine even though the scope note listed it as an example.
- Villages: 43 across the 7 Anbaugebiete, within the 40–60 target.

## Changes to existing entries
- **Mosel**: dropped `Saar` and `Ruwer` from its synonym list. Both are now separate Bereich entries (`Saar`, `Ruwertal`, the latter synonym `Ruwer`) per the scope note ("Saar and Ruwer are what labels say; make sure they resolve"); leaving them as Mosel synonyms would collide with the new Bereich names/synonyms. `Mosel-Saar-Ruwer` and `Moselle` are kept as Mosel synonyms since they name the whole Anbaugebiet, not a sub-area.
- Rheingau, Nahe, Mittelrhein, Ahr, Saale-Unstrut, Sachsen entries kept unchanged (no folded-in sub-appellations found).

## Homonyms
- None yet flagged for Mosel/Rheingau/Nahe sub-areas checked so far (continuing).

## Uncertain calls
- `Goldriesling`: new grape, VIVC 4884, Riesling × (probably extinct/unidentified) Courtillier Musqué Précoce-type parent. Added as a new grape, not a Riesling synonym.
- `Elbling`: existing entry (`grapes.yaml`, white) has no synonym for the red-berried mutation. Wikidata carries it as a distinct item ("Elbling Blau"/"Elbling Rot", VIVC id separate from white Elbling), so per the "distinct varieties merged" caution I am NOT adding "Roter Elbling"/"Elbling Blau" as a synonym of Elbling — flagging here instead of guessing.
- Rheinischer Landwein: excluded from my file for the reason above; if de-s's research doesn't cover it, it may need to be added by whichever slice's Anbaugebiete its registered communes actually touch.

## Name-collision fixes (village name = Bereich name)
- **Johannisberg**: the Rheingau Bereich and the village (an Ortsteil of Geisenheim) share the exact name. Parenthetical disambiguation (`Johannisberg (Ort)`) is stripped by the lookup and would collide again, so there is one entry (`Johannisberg`, the Bereich) with `Johannisberger` added as a synonym; no separate village entry.
- **Meißen**: same clash between the Bereich and the town. One entry (`Meißen`, classification `Bereich`) carries `Meißner`/`Meissen` as synonyms; `Radebeul` is its only village child.
- **Thüringen**: renamed from a working `Thüringen (Bereich)` to plain `Thüringen` (no collision exists, parens just triggered the same lookup-stripping warning). `Freyburg`'s redundant `Freyburg (Unstrut)` synonym (identical to the name once parens strip) was dropped.

## Großlagen considered and excluded
Per the scope note, Großlagen are not regions. Considered and left out: Piesporter Michelsberg, Bereich-wide Großlagen Klosterberg (Ahr), Burgweg/Rosengarten/Paradiesgarten (Nahe), Deutelsberg (Rheingau), Nussberg (Mittelrhein), Schwarze Katz — none added.

## Homonyms
- "Meißen"/"Meissen" and "Freyburg" are not aware of same-named wine regions elsewhere.
- No other country has a "Mosel", "Rheingau", "Nahe", "Ahr", "Sachsen" wine region as far as I found.

## Label string → canonical

| label string | kind | canonical | where seen |
|---|---|---|---|
| Piesporter Goldtröpfchen | region | Piesport | https://www.bernkastel-kues.de/verwaltung-buergerdienste/gemeinden-der-verbandsgemeinde/piesport/ |
| Bernkasteler Doctor | region | Bernkastel-Kues | https://de.wikipedia.org/wiki/Bernkastel-Kues |
| Wehlener Sonnenuhr | region | Wehlen | https://de.wikipedia.org/wiki/Wehlen_(Bernkastel-Kues) |
| Graacher Himmelreich | region | Graach | https://de.wikipedia.org/wiki/Graach_an_der_Mosel |
| Ürziger Würzgarten | region | Ürzig | https://de.wikipedia.org/wiki/%C3%9Crzig |
| Erdener Prälat | region | Erden | https://de.wikipedia.org/wiki/Erden_(Mosel) |
| Brauneberger Juffer | region | Brauneberg | https://de.wikipedia.org/wiki/Brauneberg_(Mosel) |
| Zeltinger Sonnenuhr | region | Zeltingen-Rachtig | https://de.wikipedia.org/wiki/Zeltingen-Rachtig |
| Saarburger Rausch | region | Saarburg | https://de.wikipedia.org/wiki/Saarburg |
| Wiltinger Braune Kupp | region | Wiltingen | https://de.wikipedia.org/wiki/Wiltingen |
| Ockfener Bockstein | region | Ockfen | https://de.wikipedia.org/wiki/Ockfen |
| Kaseler Nies'chen | region | Kasel | https://de.wikipedia.org/wiki/Kasel |
| Rüdesheimer Berg Schlossberg | region | Rüdesheim | https://de.wikipedia.org/wiki/R%C3%BCdesheim_am_Rhein |
| Hochheimer Domdechaney | region | Hochheim | https://de.wikipedia.org/wiki/Hochheim_am_Main |
| Assmannshäuser Höllenberg | region | Assmannshausen | https://de.wikipedia.org/wiki/Assmannshausen |
| Kiedricher Gräfenberg | region | Kiedrich | https://de.wikipedia.org/wiki/Kiedrich |
| Schlossböckelheimer Kupfergrube | region | Schlossböckelheim | https://de.wikipedia.org/wiki/Schlo%C3%9Fb%C3%B6ckelheim |
| Niederhäuser Hermannshöhle | region | Niederhausen | https://de.wikipedia.org/wiki/Niederhausen_(Nahe) |
| Bacharacher Hahn | region | Bacharach | https://de.wikipedia.org/wiki/Bacharach |
| Bopparder Hamm | region | Boppard | https://de.wikipedia.org/wiki/Boppard |
| Mayschosser Mönchberg | region | Mayschoß | https://de.wikipedia.org/wiki/Mayschoß |
| Ahrweiler Rosenthal | region | Bad Neuenahr-Ahrweiler | https://de.wikipedia.org/wiki/Bad_Neuenahr-Ahrweiler |
| Meissner Kapitelberg | region | Meißen | https://de.wikipedia.org/wiki/Sachsen_(Weinanbaugebiet) |
| Rivaner | grape | Müller-Thurgau | https://de.wikipedia.org/wiki/M%C3%BCller-Thurgau |
| Spätburgunder | grape | Pinot Noir | https://de.wikipedia.org/wiki/Sp%C3%A4tburgunder |
| Weißer Riesling | grape | Riesling | https://de.wikipedia.org/wiki/Riesling |
| Goldriesling | grape | Goldriesling | https://en.wikipedia.org/wiki/Goldriesling |
| Kleinberger | grape | Elbling | https://glossary.wein.plus/elbling |

## Review (main session, 2026-09-27)
- Hierarchy checked with `check --tree`; Saar and Ruwer moved out of
  Mosel's synonyms correctly. Accepted Johannisberg and Meißen as
  Bereich entries carrying the village adjectives.
- Added the third Saale-Unstrut Bereich, Mansfelder Seen.
- Rheinischer Landwein is in de-s (as a root).
