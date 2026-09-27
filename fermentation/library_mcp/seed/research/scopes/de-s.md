# de-s: Germany, south and west

**Country:** DE. **Slice:** Pfalz, Rheinhessen, Baden, Württemberg,
Franken, Hessische Bergstraße. Germany is split across two agents (de-n,
de-s).

**You own:** the existing `Pfalz`, `Rheinhessen`, `Baden`,
`Württemberg`, `Franken` and `Hessische Bergstraße` entries
(classification `Anbaugebiet`) and everything under them:
- **Bereiche** (e.g. Pfalz: Mittelhaardt-Deutsche Weinstraße, Südliche
  Weinstraße; Rheinhessen: Bingen, Nierstein, Wonnegau; Baden: Kaiserstuhl,
  Tuniberg, Breisgau, Markgräflerland, Ortenau, Kraichgau, Badische
  Bergstraße, Bodensee, Badisches Frankenland, Tauberfranken; Franken:
  Maindreieck, Mainviereck, Steigerwald; Württemberg: Remstal-Stuttgart,
  Württembergisch Unterland, Kocher-Jagst-Tauber, Oberer Neckar,
  Württembergischer Bodensee). Classification `Bereich`.
- **Label villages** (Gemeinden whose name leads the label), children of
  their Bereich: e.g. Forst, Deidesheim, Wachenheim, Bad Dürkheim,
  Ungstein, Kallstadt, Birkweiler, Siebeldingen, Schweigen; Nierstein,
  Nackenheim, Oppenheim, Westhofen, Flörsheim-Dalsheim, Bingen; Ihringen,
  Oberrotweil, Achkarren, Durbach; Würzburg, Randersacker, Escherndorf,
  Iphofen, Sommerhausen; Heppenheim. Classification `Gemeinde`. Add the
  adjectival label form as a synonym (`Forster`, `Niersteiner`,
  `Würzburger`). Aim for 35–55.
- **Landwein PGIs** whose area falls in your Anbaugebiete (Pfälzer
  Landwein, Rheinhessischer Landwein, Badischer Landwein, Taubertäler
  Landwein, Schwäbischer Landwein, Landwein Main, Regensburger Landwein,
  Starkenburger Landwein, Landwein Rhein-Neckar, …). Classification
  `Landwein`.

Not regions, keep them out: Prädikat levels, VDP tiers, Einzellagen
(Kirchenstück, Pechstein, Pettenthal…) and Großlagen ("Niersteiner
Gutes Domtal" is a Großlage). List any you consider in the `.md`, don't
add them. Bocksbeutel is a bottle, not a region.

**Existing entries to fix:** `Baden` carries "Kaiserstuhl" as a synonym.
Kaiserstuhl is a Bereich: make it its own entry under Baden and remove
the synonym. Check the others the same way.

**Not yours:** de-n: Mosel, Rheingau, Nahe, Mittelrhein, Ahr,
Saale-Unstrut, Sachsen, and their Landwein. Deutscher Wein / Deutscher
Sekt (generic), leave out.

**Official register:** eAmbrosia (PDOs = the 13 Anbaugebiete, PGIs = the
Landwein areas) first, then the BLE/Weinbergsrolle and the Deutsches
Weininstitut (deutscheweine.de) for Bereiche. Count Bereiche against the
official list for each Anbaugebiet.

**`grapes:` field:** none. Anbaugebiete and Bereiche have no grape rules.

**Grapes file:** German names and synonyms missing from `grapes.yaml`.
Run `context --grape` on each first; add only missing grapes and missing
synonyms:
- Silvaner / Grüner Silvaner, Dornfelder, Blauer Portugieser, Lemberger
  (Blaufränkisch), Trollinger (Schiava Grossa), Schwarzriesling / Müllerrebe
  (Pinot Meunier), Grauburgunder / Ruländer (Pinot Gris), Weißburgunder
  (Pinot Blanc), Gutedel (Chasselas), Scheurebe, Huxelrebe, Regent,
  Acolon, Samtrot, Muskateller, Auxerrois, Gewürztraminer / Traminer,
  Blauer Zweigelt, Cabernet Dorsa, Rotberger. Also the blend style
  Schillerwein / Rotling: a style, not a grape, keep it out.
- de-n owns Elbling, Rivaner / Müller-Thurgau, Frühburgunder, Goldriesling,
  Spätburgunder, Bacchus and Kerner. Don't add those.
