# AT: Austria — research notes

Status: complete

## Sources
- Österreich Wein (austrianwine.com), "DAC" and "Wine with protected geographical indication Landwein" pages, accessed 2026-09-27.
- oesterreichwein.at region pages (Wachau, Kamptal, Kremstal, Carnuntum, Weststeiermark), accessed 2026-09-27.
- BMLUK / Bundeskellereiinspektion DAC-Verordnungen (dac_vo_wachau.pdf, dac_vo_kamptal.pdf), current consolidated versions, accessed 2026-09-27.
- Vinea Wachau, "Wachau DAC" page, accessed 2026-09-27.
- steiermark.wine, "Ortsweine" page (Südsteiermark/Vulkanland/Weststeiermark village lists), accessed 2026-09-27.
- Wikipedia: Kremstal DAC, Zierfandler, Rotgipfler, Frühroter Veltliner, Wildbacher — used only to cross-check grape identity, not for the appellation list itself.
- eAmbrosia (EU GI register) confirmed as source of record for Landwein PGI zones (Weinland Österreich, Steirerland, Bergland Österreich); direct eAmbrosia fetch was blocked (403), so the austrianwine.com Landwein page was used as the citable secondary source. Flagged as an open question below.

## Counts
- 18 DACs officially in force (per austrianwine.com/oesterreichwein.at): Weinviertel, Mittelburgenland, Traisental, Kremstal, Kamptal, Leithaberg, Eisenberg, Neusiedlersee, Wiener Gemischter Satz, Rosalia, Vulkanland Steiermark, Südsteiermark, Weststeiermark, Carnuntum, Wachau, Ruster Ausbruch, Wagram, Thermenregion. All 18 produced (16 already existed in regions.yaml; Rosalia and Ruster Ausbruch added).
- 3 Landwein PGI zones (Weinland Österreich, Steirerland, Bergland Österreich): all 3 added, none existed before.
- 4 Bundesland-level regional entries (Niederösterreich, Burgenland, Steiermark, Wien): all pre-existing, kept.
- Ortswein/Gemeinde villages: produced 31 across the six DACs that have them (Wachau 8, Kamptal 6, Kremstal 5, Südsteiermark 5, Vulkanland Steiermark 4, Weststeiermark 3). Official counts are larger in places (Wachau has 22 defined Ortswein communities, Kamptal 12, Kremstal 9); I selected the villages that actually appear on retail labels/producer sites rather than the full administrative list, per the "aim for 20-35" guidance and the scope's own example list. Left out: the remaining ~35 smaller Wachau/Kamptal/Kremstal hamlets (e.g. Wachau's Gut am Steg, Viessling, Elsarn, Mühldorf, Spitzer Graben, Arnsdorf, Mauternbach; Kamptal's Engabrunn, Grafenegg, Mittelberg, Schiltern, Lengenfeld; Kremstal's Furth, Höbenbach, Krustetten) and Vulkanland's Oststeiermark/Gleichenberg/Kapfenstein/St. Peter/Tieschen — these exist in the DAC regulations but are rarely seen as standalone label strings.
- Named Rieden, Großlagen, Prädikat levels, Wachau's Steinfeder/Federspiel/Smaragd, and ÖTW tiers: excluded per scope.

## Changes to existing entries
- None of the 16 pre-existing AT entries were renamed or re-parented. Wien's existing synonym "Wiener Gemischter Satz" kept as-is (it is the DAC's own alternate name, not a separate appellation).
- Added `grapes:` to all 16 pre-existing DAC entries that lacked it (they had none in the library before), plus to the 2 new DACs.

## Homonyms
- Steiermark ("Styria") — Slovenia has a Štajerska wine region (Wave 3's scope, not this file). Noted per instructions.
- No other AT region name collides with a region name in another country that I found.

## Uncertain calls
- **Ruster Ausbruch DAC grapes**: sources list up to 6-7 permitted varieties for this sweet-wine DAC (Furmint, Welschriesling, Neuburger, Weißburgunder/Pinot Blanc, Chardonnay, Pinot Gris, Traminer/Gewürztraminer). I listed only Furmint and Welschriesling as "principal" since Furmint is the historically defining variety of Ruster Ausbruch and Welschriesling is the most commonly cited base wine; the others are permitted but not distinguishing. Flagging for review.
- **Wiener Gemischter Satz DAC grapes**: this is a field-blend DAC (≥3 white varieties co-planted, no variety >50%, third variety ≥10%) rather than a fixed varietal list. I listed the four most commonly cited component varieties (Grüner Veltliner, Riesling, Pinot Blanc, Neuburger) as `grapes:`, but the regulation does not name a fixed set the way Kamptal or Mittelburgenland do. Flagging in case `grapes:` should be omitted here instead.
- **Leithaberg DAC** has separate white and red regulations (white: Grüner Veltliner, Pinot Blanc, Chardonnay, Neuburger; red: Blaufränkisch only). I combined both into one `grapes:` list since the entry is one region; flagging in case the reviewer wants only Blaufränkisch (the region's calling-card grape).
- **Frühroter Veltliner** color: it is a pink/red-skinned grape used to make white wine (like Grauburgunder). I used `color: gris` by analogy with Pinot Gris' treatment in this library; flagging in case `white` is preferred instead, since oesterreichwein.at classifies it under "Weißwein" (white wine) varieties.
- Landwein PGI sourcing: could not fetch eAmbrosia directly (403); used austrianwine.com as the citable source instead. If a reviewer has eAmbrosia access, worth confirming the exact registered zone names.

## Grape notes
- `Schilcher` deliberately **not** added as a synonym of Blauer Wildbacher, per scope: it names the rosé wine style made from the grape, not the grape itself, even though some ampelographic sources (Wikipedia/Jancis Robinson) list it as a berry synonym.
- `Muskat-Sylvaner` and `Morillon` added as existing synonyms (Sauvignon Blanc and Chardonnay respectively) rather than new grapes, per scope.
- `Traminer` already exists as a synonym of Gewürztraminer in grapes.yaml; not duplicated here even though it appears on Klöch (Vulkanland Steiermark) labels.


## Label string → canonical examples

| label string | kind | canonical | where seen (URL) |
|---|---|---|---|
| Wachau DAC | region | Wachau | https://www.vinea-wachau.at/en/the-wine-region/wachau-dac |
| Weißenkirchen in der Wachau | region | Weißenkirchen | https://www.vinorama.at/Weingueter/Domaene-Wachau-Duernstein/Riesling-Smaragd-Weissenkirchen-Wachau-DAC-2023.html |
| Zöbinger | region | Zöbing | https://www.falstaff.com/en/wines/weingut-schloss-gobelsburg-2021-riesling-kamptal-dac-zoebing |
| Kamptal DAC Reserve | region | Kamptal | https://www.weinshop24.cc/dac/kamptal-dac-kamptal-dac-reserve |
| Stadt Krems | region | Krems | https://www.winebow.com/our-brands/stadt-krems |
| Neusiedler See | region | Neusiedlersee | https://www.wine-searcher.com/regions-neusiedlersee |
| Südburgenland | region | Eisenberg | https://www.austrianwine.com/our-wine/winegrowing-regions/burgenland/eisenberg |
| Wiener Gemischter Satz | region | Wien | https://wien-erleben.com/wiener-gemischter-satz/ |
| Vulkanland | region | Vulkanland Steiermark | https://steiermark.wine/en/original/winegrowing-regions/vulkanland-steiermark/ |
| South Styria | region | Südsteiermark | https://en.wikipedia.org/wiki/Styria |
| Schilcherland | region | Weststeiermark | https://magazine.wein.plus/in-the-land-of-the-schilcher-wine-growing-regions-in-austria-weststeiermark |
| Ruster Ausbruch DAC | region | Ruster Ausbruch | https://www.falstaff.com/nordics/wines/weingut-heidi-schroeck-soehne-2023-furmint-ruster-ausbruch-dac |
| Rosalia DAC | region | Rosalia | https://burgenland.orf.at/stories/3004156/ |
| Gumpoldskirchen | region | Thermenregion | https://www.grapeguru.de/en/knowledge/wine-regions/thermenregion |
| Leutschach an der Weinstraße | region | Leutschach | https://steiermark.wine/wein/ortsweine/ |
| Ehrenhausen an der Weinstraße | region | Ehrenhausen | https://steiermark.wine/wein/ortsweine/ |
| Klöch | region | Klöch | https://steiermark.wine/wein/ortsweine/ |
| Grüner Veltliner | grape | Grüner Veltliner | https://www.austrianwine.com/our-wine/grape-varieties/white-wine/gruener-veltliner |
| Blauer Zweigelt | grape | Zweigelt | https://en.wikipedia.org/wiki/Zweigelt |
| Rotburger | grape | Zweigelt | https://en.wikipedia.org/wiki/Zweigelt |
| Kékfrankos | grape | Blaufränkisch | https://en.wikipedia.org/wiki/Blaufr%C3%A4nkisch |
| Morillon | grape | Chardonnay | https://www.austrianwine.com/our-wine/grape-varieties/white-wine/morillon-chardonnay |
| Muskat-Sylvaner | grape | Sauvignon Blanc | https://www.austrianwine.com/our-wine/grape-varieties/white-wine/sauvignon-blanc |
| Spätrot | grape | Zierfandler | https://en.wikipedia.org/wiki/Zierfandler |
| Weißer Burgunder | grape | Pinot Blanc | https://www.austrianwine.com/our-wine/grape-varieties/white-wine/pinot-blanc |
| Blauer Wildbacher | grape | Blauer Wildbacher | https://en.wikipedia.org/wiki/Wildbacher |


## Review (main session, 2026-09-27)
- `Wien` was classified DAC with "Wiener Gemischter Satz" as a synonym.
  Wien is the Weinbaugebiet; the DAC is now its own child entry
  `Wiener Gemischter Satz` (no `grapes:`: it is a field-blend rule).
- Removed "Malvasier" from Frühroter Veltliner: a bare German name for
  Malvasia, ambiguous. `color: gris` accepted (existing convention).
- Accepted the curated Ortswein villages, the DAC grape lists, and
  Eisenberg's pre-existing "Südburgenland" synonym (a label fallback).
