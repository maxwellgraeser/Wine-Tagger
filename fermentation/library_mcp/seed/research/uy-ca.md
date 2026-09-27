# uy-ca research: Uruguay and Canada

Status: complete

## Sources

- INAVI, "Las regiones" (official register): https://www.inavi.com.uy/regiones/ — fetched 2026-09-27. Current site text
  lists 7 named zones (Litoral Norte, Litoral Sur, Metropolitana, Central, Oceánica, Norte, Centro-Este) with a
  leftover sentence "Existen seis regiones diferentes" (a stale count from before Centro-Este was added). I used the
  7 zones actually named and mapped to departments as given.
- The scope note's six zone names (Costa Oceánica, Metropolitana, Sur Oeste, Centro Sur, Litoral Norte, Noreste) do
  not match INAVI's current published names. I used INAVI's own current terms (Oceánica not "Costa Oceánica",
  Litoral Sur not "Sur Oeste", Central not "Centro Sur", Norte not "Noreste") since the brief says to follow the
  official register, and noted the mismatch here rather than inventing a mapping.
- Department-level label areas (Garzón, Las Violetas, Progreso, Juanicó, Carmelo, Atlántida): South America Wine
  Guide https://southamericawineguide.com/a-guide-to-canelones-montevideo-wine-regions/ and
  https://southamericawineguide.com/uruguay-wine-regions-guide/, Wine Enthusiast
  https://www.wineenthusiast.com/culture/wine/uruguay-wine-country/, SevenFifty Daily
  https://daily.sevenfifty.com/exploring-the-wines-of-uruguay/.

## Sources (Canada)

- VQA Ontario / Ontario Wine Appellation Authority, "Ontario Appellations": https://vqaontario.ca/ontario-appellations/
  and the Niagara Peninsula, Niagara Escarpment, Niagara-on-the-Lake and West Niagara sub-pages (fetched 2026-09-27).
  West Niagara is a **newer regional appellation** (added after Vinemount Ridge, Creek Shores and Lincoln Lakeshore
  were moved out from under Niagara Escarpment) — the scope note's grouping of those three under "Niagara Escarpment"
  is out of date; current VQA Ontario groups them under West Niagara instead.
- BC Wine Authority, "Wine Regions" (official register): https://bcvqa.ca/wine-regions/ and
  https://bcvqa.ca/geo_indication/okanagan-valley/ (fetched 2026-09-27). Six Okanagan sub-GIs (East Kelowna Slopes,
  Skaha Bench, South Kelowna Slopes, Lake Country, Summerland Bench, Summerland Lakefront, Summerland Valleys,
  Golden Mile Slopes) were approved in 2022, confirmed via BC government release:
  https://news.gov.bc.ca/releases/2022AF0045-001014.
- Wine Growers Nova Scotia, "Nova Scotia Wine Regions": https://winesofnovascotia.ca/nova-scotia-wine-regions/ and
  Wikipedia "Annapolis Valley": https://en.wikipedia.org/wiki/Annapolis_Valley.
- Conseil des vins d'appellation du Québec, "IGP Vin du Québec": https://vinsduquebec.com/en/quebec-wines/igp/.

## Counts

- UY: 7 INAVI zones + 17 departments + 6 informal label areas = 30 entries.
- CA Ontario: province + 3 DVAs (Niagara Peninsula, Lake Erie North Shore, Prince Edward County) + 3 regional
  appellations (Niagara Escarpment, Niagara-on-the-Lake, West Niagara) + 10 sub-appellations = 17 entries.
- CA British Columbia: province + 9 GIs + 10 Okanagan sub-GIs + 1 Vancouver Island sub-GI (Cowichan Valley) = 21
  entries. Cowichan Valley is BC's only sub-GI outside Okanagan Valley; no others found on the official register.
- CA Nova Scotia / Québec: Nova Scotia + Annapolis Valley + Québec + Vin du Québec IGP = 4 entries. Tidal Bay is
  Nova Scotia's one official wine standard/appellation but it names a *style* (dry aromatic white blend), not a
  place, so per the scope note it is not added as a region.
- Total: 73 regions (matches the checker output), 2 grapes.
- Left out: Ontario's "emerging regions" (Norfolk & Haldimand, Central Ontario/Georgian Bay, Huron Shores, Eastern
  Ontario) are vineyard areas without a defined DVA/appellation yet — wines from them are just labelled "VQA
  Ontario", so there is no place name to add.

## Changes to existing entries

- `Canelones` (existing, no parent) → gave `parent: "Metropolitana"`. It is INAVI's own department-zone mapping.
- `Maldonado` (existing, synonyms `["Garzón", "Garzon"]`) → gave `parent: "Oceánica"` and **removed** the `Garzón`
  synonyms. Garzón is a specific wine area within Maldonado department (its own label area, home of Bodega
  Garzón/Bulgheroni vineyards), not another name for the whole department. Folding it in as a synonym would make
  every "Garzón" mention resolve only to the department and never let a wine be tagged with the more specific area.
  Added `Garzón` as its own entry with `parent: "Maldonado"` instead.
- `Niagara Peninsula` (existing, synonyms `["Niagara", "Niagara-on-the-Lake", "Niagara Escarpment"]`) → **removed**
  the `Niagara-on-the-Lake` and `Niagara Escarpment` synonyms and added them as their own child entries
  (`parent: "Niagara Peninsula"`, classification `Regional appellation`), each with its own sub-appellations. Both
  are separate VQA regional appellations with their own delimited areas and sub-appellations, not alternate names
  for the whole Niagara Peninsula DVA — the same mistake pattern as folding a sub-appellation into its parent.
  Kept `Niagara` as an informal synonym of Niagara Peninsula, since that is how the whole DVA is casually named on
  labels.
- `Nova Scotia` (existing, synonym `["Annapolis Valley"]`) → **removed** the `Annapolis Valley` synonym and added it
  as its own child entry (`parent: "Nova Scotia"`). Annapolis Valley is a specific wine-growing valley within Nova
  Scotia (with Gaspereau Valley as a named sub-valley within it), not another name for the whole province.

## Overlaps / uncertain calls

- Lavalleja is listed by INAVI under both `Central` (with Durazno, Florida) and `Centro-Este` (with Treinta y Tres).
  One parent per entry: I used `Central` (listed first, and Durazno/Florida/Lavalleja is the more established
  grouping). Noted here per the one-parent rule.
- Golden Mile Bench and Golden Mile Slopes are adjacent, similarly-named Okanagan sub-GIs (Slopes approved 2022,
  Bench in 2015) — kept as two separate entries since the register treats them as distinct, non-overlapping GIs,
  not variants of one name.
- West Niagara is not named in the scope note (which listed Niagara Escarpment and Niagara-on-the-Lake as the "two
  regional" appellations with all ten sub-appellations split between them). I added it because the current VQA
  Ontario register names three regional appellations, and Vinemount Ridge/Creek Shores/Lincoln Lakeshore no longer
  sit under Niagara Escarpment there. Flagging in case the scope intended the older two-way split.

## Homonyms

- Niagara: this Ontario DVA (`Niagara Peninsula`/`Niagara`) vs. the existing `Niagara Escarpment` AVA in New York,
  USA (`regions.yaml:2504`). Distinct place names in different countries; both entries already coexist.
- Niagara Escarpment: the CA regional appellation added here is a same-name, different-country match for the
  existing US `Niagara Escarpment` AVA (New York) — the escarpment itself crosses the border.
- Lake Erie: the existing `Lake Erie` AVA is in the US (Ohio/NY/PA); `Lake Erie North Shore` here is the Ontario,
  Canada DVA on the opposite (Canadian) shore of the same lake. Different entries, no collision, but same body of
  water.
- Colonia: the UY department `Colonia` here vs. Colonia in other Spanish-speaking wine countries (e.g. La Rioja
  and various "Colonia" place names elsewhere) — no matching library entry found via `context --region`, so no
  actual conflict, just flagging the common name.

## Label string → canonical

| label string | kind | canonical | where seen |
|---|---|---|---|
| Garzón | region | Garzón | https://www.wineenthusiast.com/culture/wine/uruguay-wine-country/ |
| Carmelo | region | Carmelo | https://southamericawineguide.com/uruguay-wine-regions-guide/ |
| Juanicó | region | Juanicó | https://southamericawineguide.com/a-guide-to-canelones-montevideo-wine-regions/ |
| Atlantida | region | Atlántida | https://daily.sevenfifty.com/exploring-the-wines-of-uruguay/ |
| Canelones | region | Canelones | https://southamericawineguide.com/a-guide-to-canelones-montevideo-wine-regions/ |
| Tannat | grape | Tannat | https://daily.sevenfifty.com/exploring-the-wines-of-uruguay/ |
| Harriague | grape | Tannat | https://en.wikipedia.org/wiki/Tannat |
| Niagara-on-the-Lake | region | Niagara-on-the-Lake | https://www.wineriesofniagaraonthelake.com/appellations |
| Niagara Escarpment | region | Niagara Escarpment | https://vqaontario.ca/ontario-appellations/niagara-peninsula/niagara-escarpment/ |
| Beamsville Bench | region | Beamsville Bench | https://vqaontario.ca/ontario-appellations/niagara-peninsula/ |
| Twenty Mile Bench | region | Twenty Mile Bench | https://vqaontario.ca/ontario-appellations/niagara-peninsula/twenty-mile-bench/ |
| Short Hills Bench | region | Short Hills Bench | https://vqaontario.ca/ontario-appellations/niagara-peninsula/ |
| St. David's Bench | region | St. David's Bench | https://vqaontario.ca/ontario-appellations/niagara-peninsula/niagara-on-the-lake/ |
| Four Mile Creek | region | Four Mile Creek | https://vqaontario.ca/ontario-appellations/niagara-peninsula/four-mile-creek/ |
| West Niagara VQA | region | West Niagara | https://winewitandwisdomswe.com/2025/04/24/welcome-to-the-world-west-niagara-vqa/ |
| Okanagan | region | Okanagan Valley | https://www.winewithseth.com/winewiki/okanagan-valley/ |
| Golden Mile Bench | region | Golden Mile Bench | https://bcvqa.ca/geo_indication/okanagan-valley/ |
| Naramata Bench | region | Naramata Bench | https://bcvqa.ca/geo_indication/okanagan-valley/ |
| Okanagan Falls | region | Okanagan Falls | https://bcvqa.ca/geo_indication/okanagan-valley/ |
| Skaha Bench | region | Skaha Bench | https://news.gov.bc.ca/releases/2022AF0045-001014 |
| Cowichan Valley | region | Cowichan Valley | https://bcvqa.ca/wine-regions/ |
| Annapolis Valley | region | Annapolis Valley | https://en.wikipedia.org/wiki/Annapolis_Valley |
| Tidal Bay | (style, not added) | — | https://novascotiawinerylist.ca/guides/nova-scotia-wineries-guide |
| IGP Vin du Québec | region | Vin du Québec | https://vinsduquebec.com/en/quebec-wines/igp/ |
| Vin du Quebec | region | Vin du Québec | https://www.protegez-vous.ca/outils-et-services/le-decodeur/vin-du-quebec |
| Vidal Blanc | grape | Vidal Blanc | (existing entry, checked via context --grape) |
| Maréchal Foch | grape | Marechal Foch | (existing entry, checked via context --grape) |

## Review (main session, 2026-09-27)
- Hierarchy accepted: INAVI's seven current zones, Niagara's three regional appellations (West Niagara included), BC GIs and sub-GIs. Folded-in synonyms on Niagara Peninsula, Maldonado and Nova Scotia correctly split out.
- The bare zone names Norte, Central and Metropolitana are generic; kept because INAVI uses them and lookup is exact-match.

**Merge note (2026-09-27):** Merged. Lock nulled as homonyms: Central (Hong Kong), Florida (the US state), Garzón (Colombia), Montevideo (Minnesota), Rivera (Ticino), Río Negro (Colombia), Salto (Brazil), San José (California), Litoral Norte (empty description), and Niagara Escarpment (CA), which took the US AVA's item. Replay 0 changes, 732 tests.
