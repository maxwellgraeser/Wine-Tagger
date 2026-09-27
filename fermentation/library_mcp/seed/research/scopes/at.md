# at: Austria

**Country:** AT. **Slice:** all of Austria, one agent.

**You own:** every existing AT entry and everything under it:
- **Weinbaugebiete / Bundesländer** as regional entries: Niederösterreich,
  Burgenland, Steiermark, Wien, and the Bergland (Weinland and Steirerland
  are the generic PGIs: Weinland Österreich covers NÖ, Burgenland and
  Wien; Steirerland covers Steiermark; Bergland Österreich the rest).
  Classification `Landwein` for those three PGIs.
- **All DACs** (18 or more), with their classification `DAC`: Weinviertel,
  Mittelburgenland, Traisental, Kremstal, Kamptal, Leithaberg, Eisenberg,
  Neusiedlersee, Wiener Gemischter Satz, Schilcherland (Weststeiermark),
  Südsteiermark, Vulkanland Steiermark, Rosalia, Wachau, Wagram,
  Carnuntum, Thermenregion, Ruster Ausbruch. Check the current list; it
  grew in 2020–2024.
- **Named Rieden and Großlagen are out**, except the few that act as
  label regions: the Steiermark DAC "Ortswein" villages and the Wachau,
  Kamptal and Kremstal **Ortsweine** (e.g. Spitz, Weißenkirchen, Dürnstein,
  Joching, Loiben, Langenlois, Zöbing, Gobelsburg, Krems, Stein; Gamlitz,
  Kitzeck-Sausal, Leutschach, Ehrenhausen; Klöch, St. Anna). Classification
  `Gemeinde`, children of their DAC. Aim for 20–35.

Not regions, keep them out: Wachau's Steinfeder / Federspiel /
Smaragd, Prädikat levels (Ausbruch is a DAC only as Ruster Ausbruch),
ÖTW tiers, single Rieden (Ried Achleiten, Ried Heiligenstein…).

**Not yours:** Styria's homonym in Slovenia (Štajerska) belongs to Wave 3;
note the collision in the `.md` if you see one. Nothing else in AT is
split.

**Official register:** eAmbrosia (Austria's PDOs and PGIs), then
Österreich Wein (austrianwine.com) for the DAC rules and the Ortswein
lists. Count DACs against the official list.

**`grapes:` field, yes, for every DAC:** the grapes its DAC regulation
names. For example, Kamptal DAC: Grüner Veltliner, Riesling;
Mittelburgenland DAC: Blaufränkisch.

**Grapes file:** Austrian natives and names missing from `grapes.yaml`.
Run `context --grape` on each first; add only missing grapes and missing
synonyms: Grüner Veltliner, Zweigelt (Rotburger), Blaufränkisch,
St. Laurent, Blauer Wildbacher (Schilcher is the rosé style, not a
grape: keep it out), Rotgipfler, Zierfandler (Spätrot), Neuburger,
Roter Veltliner, Welschriesling, Sauvignon Blanc as Muskat-Sylvaner,
Morillon (Chardonnay in Steiermark), Gelber Muskateller, Traminer,
Blauburger, Blauer Portugieser, Frühroter Veltliner.
