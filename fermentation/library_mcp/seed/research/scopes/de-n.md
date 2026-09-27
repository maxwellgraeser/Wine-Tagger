# de-n: Germany, north and east

**Country:** DE. **Slice:** Mosel, Rheingau, Nahe, Mittelrhein, Ahr,
Saale-Unstrut, Sachsen. Germany is split across two agents (de-n, de-s).

**You own:** the existing `Mosel`, `Rheingau`, `Nahe`, `Mittelrhein`,
`Ahr`, `Saale-Unstrut` and `Sachsen` entries (classification
`Anbaugebiet`) and everything under them:
- **Bereiche** (e.g. Mosel: Bernkastel, Burg Cochem, Obermosel, Moseltor,
  Ruwertal, Saar; Rheingau: Johannisberg; Nahe: Nahetal). Classification
  `Bereich`. Saar and Ruwer are what labels say; make sure they resolve.
- **Label villages** (Gemeinden whose name leads the label), children of
  their Bereich: e.g. Piesport, Bernkastel-Kues, Wehlen, Graach, Ürzig,
  Erden, Brauneberg, Trittenheim, Zeltingen, Kanzem, Wiltingen, Ockfen,
  Serrig, Saarburg, Kasel; Rüdesheim, Hochheim, Johannisberg, Erbach,
  Hattenheim, Kiedrich, Rauenthal, Eltville, Oestrich, Winkel,
  Geisenheim; Schlossböckelheim, Niederhausen, Monzingen, Bad Kreuznach;
  Mayschoß, Dernau, Bad Neuenahr-Ahrweiler; Bacharach, Boppard; Freyburg;
  Meißen, Radebeul. Classification `Gemeinde`. Add the adjectival label
  form as a synonym (`Piesporter`, `Rüdesheimer`), since labels read
  "Piesporter Goldtröpfchen". Keep this to villages that lead labels in
  export markets; aim for 40–60.
- **Landwein PGIs** whose area falls in your Anbaugebiete (e.g.
  Landwein der Mosel, Landwein der Saar, Landwein der Ruwer, Rheinischer
  Landwein, Nahegauer Landwein, Ahrtaler Landwein, Mitteldeutscher
  Landwein, Sächsischer Landwein). Classification `Landwein`.

Not regions, keep them out: Prädikat levels (Kabinett, Spätlese…),
VDP tiers (Grosse Lage, Erste Lage, GG, Ortswein, Gutswein), Einzellagen
(Goldtröpfchen, Sonnenuhr, Doctor…) and Großlagen (Michelsberg,
Kurfürstlay). Großlagen are a trap: "Piesporter Michelsberg" is a
Großlage, not the village. List any you consider in the `.md`, don't add
them.

**Existing entries to fix:** check for sub-appellations folded in as
synonyms and move them to entries of their own.

**Not yours:** de-s: Pfalz, Rheinhessen, Baden, Württemberg, Franken,
Hessische Bergstraße, and their Landwein. Deutscher Wein / Deutscher
Sekt (generic), leave out.

**Official register:** eAmbrosia (PDOs = the 13 Anbaugebiete, PGIs = the
Landwein areas) first, then the BLE/Weinbergsrolle and the Deutsches
Weininstitut (deutscheweine.de) for Bereiche. Count Bereiche against the
official list for each Anbaugebiet.

**`grapes:` field:** none. Anbaugebiete and Bereiche have no grape rules.

**Grapes file:** German names and synonyms missing from `grapes.yaml`.
Run `context --grape` on each first; add only missing grapes and missing
synonyms:
- Weißer Riesling / Rheinriesling (Riesling), Elbling (Weißer and Roter),
  Müller-Thurgau / Rivaner, Frühburgunder (Pinot Noir Précoce: check VIVC
  whether it is its own variety), Goldriesling, Spätburgunder (Pinot
  Noir), Bacchus, Kerner.
- de-s owns Silvaner, Dornfelder, Portugieser, Lemberger, Trollinger,
  Schwarzriesling, Grau-/Weißburgunder, Gutedel, Scheurebe and the other
  southern names. Don't add those.
