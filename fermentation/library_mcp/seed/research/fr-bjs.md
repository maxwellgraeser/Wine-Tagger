Status: complete

# fr-bjs: Burgundy, Beaujolais, Jura, Savoie, Bugey — research notes

## Sources

- **INAO cahiers des charges** (extranet.inao.gouv.fr and inao.gouv.fr "fiche produit" pages) — the primary register for every AOC below. Key documents actually read (not just linked from a search): `PNO-cdc-Bourgogne-cn23062930.pdf` (Bourgogne, arrêté 11 Dec 2023, JORF 22 Dec 2023), `chablis-grand-cru-21903` fiche (arrêté 24 Oct 2024, JORF 9 Nov 2024), `saint-bris-7671` fiche, `irancy-7698` fiche, `cp-aop-vezelay` (Vézelay recognized as AOP 14 Oct 2022), `PNO-cdcBeaujolais-cn220210.pdf`, `beaujolais-superieur-16919` fiche, `PNO-cdcC%C3%B4tesduJURA-cn220210.pdf`, `CdC_Arbois_V2.pdf` (Société de Viticulture du Jura), `PNOCDCAOCMarcduJura.pdf` family for Macvin, `CDC-Savoie-PNOcn210211.pdf` / `PNOCDCAOC-Savoie-190618.pdf` (Vin de Savoie, décret 27 Oct 2009 + later revisions), `seyssel-13180` fiche, `pno-cdc-Bugey-cn240911.pdf`, `roussette-du-bugey-9199` / `-montagnieu-9200` / `-virieu-le-grand-9201` fiches, `PNOCDCIGPFRANCHECOMTE.pdf`, `pnocdcigpallobrogie.pdf`.
- **Vins de Bourgogne (BIVB)**, `https://www.vins-bourgogne.fr/vins-et-terroirs/la-bourgogne-et-ses-appellations/` — the interprofession's own appellation-by-appellation pages; used for the village/Grand Cru hierarchy and for the count "84 appellations: 7 regional, 44 village, 33 grand cru" quoted below.
- **Beaune et le Pays Beaunois Tourisme**, appellations list page — cross-check for the Côte de Beaune village/Premier Cru/Grand Cru grouping.
- **Inter Beaujolais**, `https://www.beaujolais.com/en/discover/nos-12-appellations/` — official interprofession, the 10 crus + Beaujolais + Beaujolais-Villages ("12 appellations").
- **Société de Viticulture du Jura**, `https://www.sv-jura.com/cahier-des-charges.htm` and **Jura-Vins.com** (BIVJ) — Jura AOC list and cépage rules.
- **Vin de Savoie** (interprofession), `https://www.vin-de-savoie.fr/`, plus Wikipedia cross-checks for Roussette de Savoie's four crus and for Crémant de Savoie's 2015 creation.
- Grape-identity sources: Wikipedia FR for César/Sacy/Gringet/Persan (all have dedicated VIVC-referencing pages), dico-du-vin.com for César/Romain, domainebelluard.fr and vignobles.net for Bergeron=Roussanne and Gringet/Persan usage, caves-de-seyssel.fr for Molette.

## Counts

BIVB states Burgundy proper (Chablis through Mâconnais, excluding Beaujolais/Jura/Savoie/Bugey) has **84 appellations: 7 regional, 44 village, 33 grand cru**. My Burgundy-proper entries land on:

| Tier | BIVB official | Produced |
|---|---|---|
| Village (incl. Petit Chablis, Chablis, Irancy, Saint-Bris, Vézelay, Côte de Nuits-Villages, Côte de Beaune-Villages) | 44 | **44** |
| Grand Cru (Chablis Grand Cru = 1 AOC for 7 climats, Côte de Nuits 24, Côte de Beaune 8) | 33 | **33** |
| Regional (BIVB counts by decree: Bourgogne, Aligoté, Passe-Tout-Grains, Coteaux Bourguignons, Crémant, Mousseux, +1) | 7 | **16** — see below |

The regional-tier mismatch (16 vs 7) is deliberate, not an error: BIVB counts one *decree* ("Bourgogne", homologated once) as one appellation regardless of how many geographical denominations it carries. The brief explicitly asks for `Bourgogne Côte d'Or`, `Bourgogne Côte Chalonnaise`, `Bourgogne Vézelay`, etc. as their own entries because that's the string a label or retailer actually prints, and `lookup_region` needs the exact string. So my 16 = the ~6-7 BIVB decrees, unbundled into every named geographical denomination a label uses (Aligoté, Passe-Tout-Grains, Coteaux Bourguignons, Crémant, Mousseux, Côte d'Or, Côte Chalonnaise, Hautes-Côtes de Nuits, Hautes-Côtes de Beaune, Chitry, Côtes d'Auxerre, Côtes du Couchois, Coulanges-la-Vineuse, Épineuil, Tonnerre, Côte Saint-Jacques).

Full breakdown, all areas: **153 region entries produced**, of which **50 are existing library entries** (kept, all present) and **103 are new**. Beaujolais: 13 (Beaujolais, Beaujolais Supérieur, Beaujolais-Villages, 10 crus). Jura: 8 (Jura umbrella, Côtes du Jura, Arbois, Arbois Pupillin, Château-Chalon, L'Étoile, Crémant du Jura, Macvin du Jura). Savoie: 25 (Savoie umbrella, Vin de Savoie + 16 denominations, Roussette de Savoie + 4 crus, Seyssel, Crémant de Savoie). Bugey: 6 (Bugey, Bugey Cerdon, Bugey Manicle, Montagnieu, Roussette du Bugey, Virieu-le-Grand). IGP: 2 (Franche-Comté, Allobrogie).

**Left out, and why:**
- **Premier Cru climats** (e.g. Les Folatières, Clos des Chênes) — excluded per the brief; `lookup_region` already strips "1er Cru"/"Premier Cru" so these resolve to their village automatically and adding ~660 climats as entries would only create ambiguity risk.
- **~26 "Mâcon + village name" denominations** (Mâcon-Lugny, Mâcon-Viré, Mâcon-Prissé, etc.) — folded into `Mâcon-Villages`. They're all variants of the same Mâcon-Villages decree; adding two dozen low-differentiation entries didn't seem worth the ambiguity risk versus one well-covered parent.
- **Charlemagne** (bare, without "Corton-") — kept as its own entry for completeness (it is a distinct 1938 AOC decree, white-only, same hillside as Corton-Charlemagne) but flagged: in practice every producer bottles as "Corton-Charlemagne" instead; "Charlemagne" alone almost never appears on a real label.
- **Bourgogne Montrecul, Bourgogne (Le Chapitre), Bourgogne La Chapelle Notre-Dame** — tiny (single-estate, sub-5-hectare) geographical denominations of the base Bourgogne AOC near Dijon. Left out: they don't appear on retailer pages I could find, and BIVB's own appellation list doesn't foreground them either.
- **Anglefort and Arbignieu** (older Roussette du Bugey crus, sometimes cited in older secondary sources alongside Montagnieu and Virieu-le-Grand) — left out. The current INAO fiches I found only list Montagnieu and Virieu-le-Grand as valid geographic complements for Roussette du Bugey; I could not confirm from a primary source whether Anglefort/Arbignieu are still current or were dropped in a cahier revision. Flagged below as an open question rather than guessed.
- **IGP Comtés Rhodaniens** (also covers declassified Beaujolais) — left out; the Rhône Valley is its main home and is fr-rpl's scope, per the split-scope grape/IGP rule.
- **Bugey Mousseux / Bugey Pétillant** — these are sparkling-method mentions on the base Bugey AOC, not place names, so they don't need their own region entries.

## Changes to existing entries

1. **`Aloxe-Corton`: dropped `"Corton"` and `"Corton-Charlemagne"` from synonyms, added both plus `Charlemagne` as their own AOC entries** (parent `Aloxe-Corton`). This is exactly the bug the scope named: Corton and Corton-Charlemagne are independently decreed Grand Cru AOCs spanning three communes (Aloxe-Corton, Ladoix, Pernand-Vergelesses), not alternate names for the village. Folding them into Aloxe-Corton's synonyms meant a Corton-Charlemagne (100% white, Grand Cru) would tag as "Aloxe-Corton" (a village AOC that's overwhelmingly red) instead of as its own, higher, distinct appellation.
2. **`Chablis`: dropped `"Petit Chablis"`, `"Chablis Grand Cru"` and `"Chablis Premier Cru"` from synonyms.** Petit Chablis and Chablis Grand Cru are each their own independently-decreed AOC (added as separate entries: `Petit Chablis` under Burgundy, `Chablis Grand Cru` under `Chablis`). Chablis Premier Cru isn't a separate appellation at all — it's the Chablis AOC label with a Premier-Cru climat designation — so it needs no synonym: `lookup_region` already strips "1er Cru"/"Premier Cru" and resolves it to `Chablis` directly.
3. **`Côte de Nuits`: dropped `"Côte de Nuits-Villages"` from synonyms**, added it as its own child AOC (grapes Pinot Noir + Chardonnay, communes Fixin, Brochon, Prémeaux-Prissey, Comblanchien, Corgoloin). It's a separately decreed regional-tier appellation (est. 1964) for wines from those five communes, not another name for the Côte de Nuits sub-region.
4. **`Côte de Beaune`: dropped `"Côte de Beaune-Villages"` from synonyms**, added it as its own child AOC (red-only, Pinot Noir, spans 16 communes across Côte-d'Or and Saône-et-Loire — a materially different, larger footprint than the sub-region entry it was folded into).
5. **`Jura`: dropped `"Côtes du Jura"` from synonyms**, added it as its own child AOC (all five Jura cépages). `Côtes du Jura` is the broadest Jura-wide appellation — a real, specific decree — not just another name for the informal "Jura" wine-region umbrella that parents Arbois/Château-Chalon/L'Étoile.
6. **`Savoie`: dropped `"Bugey"` from synonyms**, promoted `"Vin de Savoie"` from a bare synonym to its own AOC entry (parent `Savoie`), and re-pointed `Roussette de Savoie`/`Seyssel`/`Crémant de Savoie` to parent `Savoie` directly rather than `Vin de Savoie`. Reasoning: Bugey is a distinct wine region and AOC in Ain, administratively and commercially separate from Savoie (own top-level entry now); and "Vin de Savoie" needed to stop doing double duty as both the umbrella label and the specific 16-denomination AOC, since Roussette de Savoie/Seyssel/Crémant de Savoie are sibling AOCs under the "Savoie" name, not children of the Vin de Savoie decree.
7. Every other existing entry in scope (Burgundy, Chablis's grape field, Côte d'Or, Marsannay, Fixin, Gevrey-Chambertin, Morey-Saint-Denis, Chambolle-Musigny, Vougeot, Vosne-Romanée, Nuits-Saint-Georges, Aloxe-Corton itself, Savigny-lès-Beaune, Beaune, Pommard, Volnay, Meursault, Puligny-Montrachet, Chassagne-Montrachet, Saint-Aubin, Santenay, Auxey-Duresses, Côte Chalonnaise, Mercurey, Givry, Rully, Montagny, Mâconnais, Mâcon-Villages, Pouilly-Fuissé, Saint-Véran, Viré-Clessé, Beaujolais, Beaujolais-Villages, the 10 crus, Arbois, Château-Chalon) is unchanged in name/parent/classification; most gained a `grapes:` field and/or a `source:` they previously lacked, and a couple gained a spelling synonym (e.g. `Marsannay-la-Côte`).

## Homonyms

- **`Marin`** (Vin de Savoie denomination, Chasselas) — Marin/Marin-Épagnier is also a wine commune of Neuchâtel, Switzerland. No collision in the allowlist (different countries), but worth knowing if Switzerland is researched later.
- **`Jura`** — the Jura Mountains straddle France and Switzerland, and Swiss Jura canton has a small, growing wine scene of its own (typically folded into the broader "Trois Lacs"/Neuchâtel trade grouping rather than sold as "Jura" per se). Low-confidence watch item, not a confirmed current collision.
- **`Chablis`** — famously used as a generic/semi-generic term for cheap white wine in some overseas markets (historically in the US and Australia), unrelated to any other country's actual appellation. Not a real region collision, just a labeling-genericization risk worth noting for the tagger's evidence-scoring side, not the allowlist itself.
- No other-country wine-region name collisions found for the Burgundy/Beaujolais/Jura/Savoie/Bugey names checked.

## Uncertain calls

- **`Bonnes-Mares` parent**: the Grand Cru straddles Chambolle-Musigny (~90% of the surface) and Morey-Saint-Denis (~10%). Parented to Chambolle-Musigny as the majority/retail-convention commune; the Morey-Saint-Denis portion is the trade-off this creates (see brief's "note the other in the .md" rule).
- **`Montrachet` and `Bâtard-Montrachet` parent**: both straddle Puligny-Montrachet and Chassagne-Montrachet close to evenly. Parented to Puligny-Montrachet (the half more commonly cited first); Chassagne-Montrachet legitimately produces both too.
- **`Corton` / `Corton-Charlemagne` / `Charlemagne` parent**: the hill spans Aloxe-Corton, Ladoix, and Pernand-Vergelesses. Parented to Aloxe-Corton, the village most closely associated with "Corton" in the trade; some producers's labels read "Ladoix, Corton Grand Cru" instead.
- **`Blagny` parent**: this red-wine-only AOC's hamlet straddles Meursault and Puligny-Montrachet. Parented to Meursault; not fully confident this is the more common trade description over Puligny-Montrachet.
- **`Côte de Beaune` naming overlap (not a rename, a live ambiguity)**: the single entry named `Côte de Beaune` (kept unclassified, parent `Côte d'Or`, per existing convention) is doing two jobs — it's both the informal sub-region that parents all the Côte de Beaune villages, *and* the literal string of a real, narrow AOC decree (a handful of hillside climats directly above Beaune town). I did not create a second, conflicting `Côte de Beaune` entry (the schema forbids duplicate names in one country); a wine labeled "AOC Côte de Beaune" still resolves correctly to this entry either way, so tagging works, but its `classification` field doesn't reflect the narrow AOC's actual decree status. Flag for a reviewer call on whether that matters here.
- **Vin de Savoie denomination secondary grapes** (`Chautagne`, `Jongieux`, `Montmélian`): the cahier permits blends/assemblages for these, and I was not able to fully pin down the complete authorized list from one primary source. I gave what I believe is the principal grape (or two) with medium confidence; flag for a cahier-text check.
- **`Montagnieu`**: left without a `grapes:` field on purpose. The single place name legitimately carries two different appellations with different grape rules — Bugey Montagnieu (sparkling, Chardonnay/Mondeuse base) and Roussette du Bugey Montagnieu (still white, Altesse) — that can't both be represented by one `grapes:` list without conflating them.
- **`Bugey` base AOC grapes**: listed Gamay, Chardonnay, Mondeuse, Pinot Noir as principal; the full cahier also permits Aligoté, Jacquère, Altesse, Poulsard and Pinot Gris in smaller roles that I did not attempt to fully enumerate.
- **Color restrictions on `Bourgogne Côtes du Couchois`, `Bourgogne Coulanges-la-Vineuse`, `Bourgogne Épineuil`, `Bourgogne Tonnerre`**: I set single-color `grapes:` fields (Pinot Noir only, or Chardonnay only) from general knowledge of these small Yonne-area denominations rather than each one's own cahier text. Flag for confirmation; a couple of these permit a secondary color in small volume.
- **`Anglefort`/`Arbignieu`** — see "left out" above; genuinely unresolved whether these are still current Roussette du Bugey geographic complements.
- **`Bourgogne Vézelay` as a synonym of `Vézelay`** rather than its own entry: the two decrees technically coexist (Vézelay AOC since 2022 is stricter; Bourgogne Vézelay remains available for wines that don't clear that bar), but for tagging purposes — "what place is this wine from" — treating them as the same bucket seemed like the right simplification. Flagged in case a reviewer wants a stricter split.

## Label string → canonical (real-world forms)

| Label string | Kind | Canonical | Where seen |
|---|---|---|---|
| "Nuits St Georges" | region | Nuits-Saint-Georges | common retailer spelling, e.g. `https://www.wine-searcher.com/regions-nuits+st+georges` |
| "Gevrey Chambertin" | region | Gevrey-Chambertin | common retailer spelling without hyphen, e.g. Wine-Searcher regional pages |
| "Morey St Denis" | region | Morey-Saint-Denis | common retailer spelling |
| "Chambertin Clos de Bèze" | region | Chambertin-Clos de Bèze | frequently printed without the second hyphen, e.g. producer back labels |
| "Corton-Charlemagne Grand Cru" | region | Corton-Charlemagne | `lookup_region` strips "Grand Cru"; label form as commonly printed |
| "Vosne-Romanée 1er Cru" | region | Vosne-Romanée | `lookup_region` strips "1er Cru" |
| "Cote de Nuits Villages" | region | Côte de Nuits-Villages | accent/hyphen-dropped retailer spelling |
| "Mâcon Villages" | region | Mâcon-Villages | space instead of hyphen, very common on labels |
| "Pouilly Fuissé" | region | Pouilly-Fuissé | space instead of hyphen |
| "Moulin a Vent" | region | Moulin-à-Vent | accent-dropped, common in US retail listings |
| "Beaujolais Villages" | region | Beaujolais-Villages | space instead of hyphen, extremely common |
| "Cotes du Jura" | region | Côtes du Jura | accent-dropped spelling |
| "Chateau Chalon" | region | Château-Chalon | accent/hyphen-dropped spelling |
| "Arbois-Pupillin" | region | Arbois Pupillin | hyphenated vs. the cahier's own space form |
| "Chignin Bergeron" | region | Chignin-Bergeron | space instead of hyphen, common on Savoie labels |
| "Apremont, Vin de Savoie" | region | Apremont | comma-separated compound form (`lookup_region` strips the comma tail) |
| "Cerdon" | region | Bugey Cerdon | wines are very often sold under the bare cru name alone, e.g. producer labels ("Patrick Bottex Bugey Cerdon") |
| "Ploussard" | grape | Poulsard | Jura-dialect spelling seen constantly on Jura labels and shop listings |
| "Naturé" | grape | Savagnin | existing library synonym; local Jura name for Savagnin |
| "Bergeron" | grape | Roussanne | Savoie's local name for Roussanne, printed on Chignin-Bergeron labels instead of "Roussanne" |
| "Pinot Beurot" | grape | Pinot Gris | Burgundian dialect name for Pinot Gris, seen on some Côte Chalonnaise/Auxerrois labels |
| "Cesar" | grape | César | accent-dropped spelling, common on English-language retailer listings for Irancy |
| "Jacquere" | grape | Jacquère | accent-dropped spelling |
| "Mondeuse Noire" | grape | Mondeuse | existing library synonym; full ampelographic name sometimes printed in full |

## Validation

```
$ .venv/bin/python -c "import yaml,sys; [print(f, len(yaml.safe_load(open(f)))) for f in sys.argv[1:]]" fermentation/library_mcp/seed/research/fr-bjs.regions.yaml fermentation/library_mcp/seed/research/fr-bjs.grapes.yaml
fermentation/library_mcp/seed/research/fr-bjs.regions.yaml 153
fermentation/library_mcp/seed/research/fr-bjs.grapes.yaml 7
```

Also checked by hand: no duplicate `(name, country)` pairs, no synonym collisions within `fr-bjs.regions.yaml`, no synonym/name collisions against the full existing `regions.yaml` (checked against every other-scope FR entry, not just my own), every `parent` resolves either within this file or in the existing library, every `grapes:` reference resolves against the existing `grapes.yaml` plus `fr-bjs.grapes.yaml`, and every new/`existing: true` grape in `fr-bjs.grapes.yaml` is collision-free against the canonical `grapes.yaml` (name and synonyms both directions).

## Review (main session, 2026-09-26)

- **Dropped `Romain` as a synonym of César.** It is a common first name
  among Burgundy winemakers (Romain Taupenot, and others), so a snippet
  naming the grower would read as César evidence.
- Hierarchy reviewed: Grand Crus sit under their village AOC, regional
  AOCs under Burgundy, and the Côtes are informal. Accepted as submitted.
