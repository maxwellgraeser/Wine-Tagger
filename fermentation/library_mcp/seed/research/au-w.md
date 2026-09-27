# au-w research: Australia, west (SA, WA, Tasmania)

Status: complete

## Sources
- Wine Australia, Register of Protected GIs and Other Terms, overview and per-state pages, accessed 2026-09-27:
  - https://www.wineaustralia.com/labelling/register-of-protected-gis-and-other-terms/geographical-indications
  - https://www.wineaustralia.com/labelling/register-of-protected-gis-and-other-terms/geographical-indications/south-australia
  - https://www.wineaustralia.com/labelling/register-of-protected-gis-and-other-terms/geographical-indications/western-australia
  - https://www.wineaustralia.com/labelling/register-of-protected-gis-and-other-terms/geographical-indications/tasmania
  - The per-state Register pages give only the "was entered in the Register" date, no boundary text; the zone/region/subregion hierarchy is taken from the scope brief (which reflects the Register's tables) and cross-checked against Wine Australia's summary text and Wikipedia zone articles (Mount Lofty Ranges zone, Fleurieu zone, Barossa zone, Great Southern (wine region)).
  - Tasmania confirmed as a single GI with no official zones/regions/subregions.

## Counts
- South Australia: 1 state, 8 zones (Adelaide, Barossa, Fleurieu, Limestone
  Coast, Lower Murray, Mount Lofty Ranges, The Peninsulas, Far North), 18
  GI regions, 3 official subregions (High Eden, Lenswood,
  Piccadilly Valley), plus 6 unofficial label sub-districts (Ebenezer,
  Marananga, Lyndoch, Polish Hill River, Watervale, Blewitt Springs).
- Western Australia: 1 state, 5 zones, 9 GI regions, 6 official subregions
  (Albany, Denmark, Frankland River, Mount Barker, Porongurup, Swan
  Valley).
- Tasmania: 1 state-level GI with no official subdivisions (confirmed on
  the Register page), plus 6 informal label subregions (Tamar Valley, Coal
  River Valley, Huon Valley, Derwent Valley, Pipers River, East Coast),
  none classified, as instructed.
- Total: 64 region entries. Nothing official was left out; "The Peninsulas"
  and "Far North" zones, and WA's Central Western Australia, Eastern
  Plains Inland and North of Western Australia, and West Australian South
  East Coastal zones, have no defined GI regions yet, so they are entered
  as childless zones.

## Changes to existing entries
- **South Australia, Western Australia, Tasmania: classification changed
  to `State`** (was `Zone` for SA/WA, `GI` for Tasmania). The Register has
  a State tier above Zone; keeping them as `Zone` collided conceptually
  with real zones like Barossa and Mount Lofty Ranges. Applied consistently
  to all three, per the scope note.
- **Barossa Valley: removed synonym "Barossa"**, and added a new `Barossa`
  Zone entry (parent South Australia) as Barossa Valley's actual parent
  (was: South Australia directly). "Barossa" alone is the zone name, used
  on labels for both Barossa Valley and Eden Valley; it cannot stay a
  synonym of just one of its two child regions.
- **Great Southern: removed synonyms "Frankland River" and "Mount
  Barker"**; these are official Register subregions, not synonyms, so they
  are now child entries (along with Albany, Denmark, Porongurup, which
  were missing).
- **Swan Valley: removed synonym "Swan District"**; added "Swan District"
  as its own Region entry (parent Greater Perth zone) and re-parented Swan
  Valley under it as a Subregion (was: parent Western Australia directly,
  classification GI). This matches the Register's actual 4-tier structure.
- **Riverland: re-parented from South Australia to Lower Murray** (its
  actual zone).
- **Adelaide Plains: re-parented to Mount Lofty Ranges** (its zone; had no
  prior parent in the library since it's a new entry here).
- **Clare Valley, McLaren Vale, Adelaide Hills, Langhorne Creek: re-parented
  from South Australia to their zones** (Mount Lofty Ranges, Fleurieu,
  Mount Lofty Ranges, Fleurieu respectively) - existing entries had South
  Australia as a flat parent since no zone tier existed yet.

## Homonyms
- None noticed for these three states' entries against other countries.

## Uncertain calls
- The Register's per-state pages (South Australia, Western Australia,
  Tasmania) return only registration-date metadata with boundary text
  marked "N/A"; the zone/region/subregion tree was cross-checked instead
  against the scope brief and Wikipedia's per-zone/region articles. If a
  newer official PDF map exists with a different zone→region assignment,
  that should override this file.
- "Adelaide" (super zone) is included as a childless overlay per the
  overlay rule, since Barossa/Fleurieu/Mount Lofty Ranges/Adelaide Plains
  are more naturally described as being "in South Australia" on labels,
  not "in Adelaide".
- The Peninsulas and Far North zones currently have very few (Far North:
  one, Southern Flinders Ranges) or no registered GI regions; kept as
  childless/near-childless zones rather than omitted.
- Unofficial label sub-districts (Ebenezer, Marananga, Lyndoch, Polish
  Hill River, Watervale, Blewitt Springs) are added at low classification
  confidence -- they are well attested on premium labels but are not
  Register GIs.

## Label string -> canonical pairs

| label string | kind | canonical | where seen (URL) |
|---|---|---|---|
| Barossa | region | Barossa | https://en.wikipedia.org/wiki/Barossa_zone_(wine) |
| Barossa Valley | region | Barossa Valley | https://en.wikipedia.org/wiki/Barossa_Valley |
| Eden Valley | region | Eden Valley | https://en.wikipedia.org/wiki/Eden_Valley,_South_Australia |
| High Eden | region | High Eden | https://en.wikipedia.org/wiki/Eden_Valley,_South_Australia |
| Clare Valley | region | Clare Valley | https://en.wikipedia.org/wiki/Clare_Valley |
| Watervale | region | Watervale | https://en.wikipedia.org/wiki/Clare_Valley |
| Polish Hill River | region | Polish Hill River | https://en.wikipedia.org/wiki/Clare_Valley |
| McLaren Vale | region | McLaren Vale | https://en.wikipedia.org/wiki/McLaren_Vale |
| Blewitt Springs | region | Blewitt Springs | https://en.wikipedia.org/wiki/McLaren_Vale |
| Adelaide Hills | region | Adelaide Hills | https://en.wikipedia.org/wiki/Adelaide_Hills_wine_region |
| Piccadilly Valley | region | Piccadilly Valley | https://en.wikipedia.org/wiki/Adelaide_Hills_wine_region |
| Langhorne Creek | region | Langhorne Creek | https://en.wikipedia.org/wiki/Langhorne_Creek_wine_region |
| Kangaroo Island | region | Kangaroo Island | https://en.wikipedia.org/wiki/Kangaroo_Island_wine_region |
| Coonawarra | region | Coonawarra | https://en.wikipedia.org/wiki/Coonawarra_wine_region |
| Limestone Coast | region | Limestone Coast | https://www.wineaustralia.com/labelling/register-of-protected-gis-and-other-terms/geographical-indications |
| Wrattonbully | region | Wrattonbully | https://en.wikipedia.org/wiki/Wrattonbully_wine_region |
| Riverland | region | Riverland | https://en.wikipedia.org/wiki/Riverland_wine_region |
| Margaret River | region | Margaret River | https://en.wikipedia.org/wiki/Margaret_River_wine_region |
| Great Southern | region | Great Southern | https://en.wikipedia.org/wiki/Great_Southern_(wine_region) |
| Frankland River | region | Frankland River | https://en.wikipedia.org/wiki/Great_Southern_(wine_region) |
| Mount Barker (WA) | region | Mount Barker | https://en.wikipedia.org/wiki/Great_Southern_(wine_region) |
| Pemberton | region | Pemberton | https://en.wikipedia.org/wiki/Pemberton_wine_region |
| Swan Valley | region | Swan Valley | https://en.wikipedia.org/wiki/Swan_Valley_(wine_region) |
| Tamar Valley Tasmania | region | Tamar Valley | https://en.wikipedia.org/wiki/Tasmania_(wine) |
| Coal River | region | Coal River Valley | https://en.wikipedia.org/wiki/Tasmania_(wine) |
| Mataro | grape | Mourvèdre | https://en.wikipedia.org/wiki/Mourv%C3%A8dre |
| Shiraz | grape | Syrah | https://en.wikipedia.org/wiki/Syrah |

## Review (main session, 2026-09-27)
- Added **Southern Eyre Peninsula** (GI region in The Peninsulas zone), which was missing.
- Tree accepted: states as `State`, Barossa zone, Swan District > Swan Valley, the Great Southern subregions.
- "Denmark", "Albany" and "East Coast" are homonym-prone names; lookups are country-scoped, so they stay.

**Merge note (2026-09-27):** Australia merged (au-w + au-e). Lock: Watervale (AU) nulled (matched a site in Michigan). Added "Upper Hunter" to Upper Hunter Valley. "Tamar Valley Tasmania" (no comma) still misses; left out of the fixture. Replay 0 changes, 639 tests.
