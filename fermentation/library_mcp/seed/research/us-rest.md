Status: complete

# us-rest research notes

## Sources
- TTB Established AVAs by state: https://www.ttb.gov/regulated-commodities/beverage-alcohol/wine/established-avas (accessed 2026-09-26)
- 27 CFR Part 9 (eCFR) for individual AVA legal descriptions, consulted per-AVA via federalregister.gov establishment notices.
- Wikipedia AVA articles used for establishment dates, nesting and grape info (cross-checked against TTB where possible).

## Counts
- Regions produced: 113 (checker-confirmed, 0 errors, 0 warnings).
- States/territories with a state-level entry: 30 (all TTB single-state AVA hosts in my scope, plus Iowa, Oklahoma and Louisiana which have no single-state AVA of their own but participate in a multi-state AVA I own).
- Single-state AVAs against TTB's established-AVAs table (accessed 2026-09-26): every AVA listed under Arizona, Arkansas, Colorado, Connecticut, Georgia, Hawaii, Illinois, Indiana, Maryland, Massachusetts, Michigan, Minnesota, Missouri, New Jersey, New Mexico, New York, North Carolina, Ohio, Pennsylvania, Tennessee, Texas, Virginia, West Virginia and Wisconsin is included -- none left out.
- Multi-state AVAs against the same table, restricted to ones not touching CA/OR/WA/ID: Appalachian High Country, Central Delaware Valley, Cumberland Valley, Lake Erie, Loess Hills District, Mesilla Valley, Mississippi Delta, Ohio River Valley, Ozark Mountain, Shenandoah Valley, Southeastern New England, Upper Hiwassee Highlands, Upper Mississippi River Valley -- all 13 included.
- Nothing official left out. (Proposed-but-not-yet-established AVAs, e.g. any 2026 TTB NPRMs still in comment period, are excluded on purpose -- they are not yet AVAs.)
- Grapes produced: 16 new entries. Norton, Chambourcin, Vidal Blanc, Seyval Blanc and Traminette from the scope's example list were already in `grapes.yaml` with no missing synonyms, so they are not repeated here.

## Changes to existing entries
- Finger Lakes (NY): dropped synonyms "Seneca Lake" and "Cayuga Lake" -- these are separate, TTB-established sub-AVAs nested inside Finger Lakes, not synonyms of it (the exact "sub-appellation folded in as synonym" mistake). Added them as child entries. Also dropped "Keuka Lake" -- it is a lake within the Finger Lakes AVA but has no TTB AVA of its own and I found no evidence it is used as a stand-alone synonym for the whole Finger Lakes AVA on labels.
- Long Island (NY): dropped synonyms "North Fork of Long Island" and "Hamptons" -- both are separate TTB AVAs nested inside Long Island. Added as child entries "North Fork of Long Island" (synonym "North Fork") and "The Hamptons, Long Island" (synonyms "The Hamptons", "Hamptons") using TTB's exact registered names.
- Virginia: dropped synonym "Monticello" -- it is a separate AVA, added as its own child entry.
- Missouri: dropped synonym "Augusta (Missouri)" -- Augusta is a separate AVA. It is not a direct child of Missouri though: TTB/Wikipedia describe Ozark Mountain AVA as containing Ozark Highlands, Augusta, Hermann and (in Arkansas) Altus and Arkansas Mountain as nested sub-AVAs. Added Ozark Mountain as a new top-level multi-state entry (parent Missouri, see straddle note below) with Augusta, Hermann and Ozark Highlands as its children.
- Colorado: dropped synonym "Grand Valley" -- it is Colorado's AVA, added as its own child entry.
- Arizona: dropped synonyms "Willcox" and "Verde Valley" -- both are Arizona's AVAs, added as their own child entries (plus Sonoita, previously missing).
- North Carolina: dropped synonym "Yadkin Valley" -- added as its own child entry.
- Michigan: dropped synonyms "Leelanau Peninsula" and "Old Mission Peninsula" -- both are Michigan AVAs, added as their own child entries.

## Multi-state straddles (my call on primary parent)
- Lake Erie AVA (NY/PA/OH): parent set to Ohio because both of its nested sub-AVAs (Grand River Valley, Isle St. George) sit in Ohio, even though most Lake Erie AVA acreage and its historic Chautauqua core is in NY/PA. Flagging as uncertain.
- Ozark Mountain AVA (MO/AR/OK): parent set to Missouri (3 of its 5 sub-AVAs -- Ozark Highlands, Augusta, Hermann -- are in Missouri; Altus and Arkansas Mountain are in Arkansas).
- Shenandoah Valley AVA (VA/WV): parent set to Virginia (larger population/production side). Keeps the bare name per scope note; no California synonym added.
- Ohio River Valley AVA (OH/IN/KY/WV): parent set to Ohio (namesake state).
- Mississippi Delta AVA (MS/LA/TN): parent set to Mississippi (namesake state).
- Texoma AVA: TTB's current established-AVA table lists Texoma under Texas as a single-state AVA, not under a multi-state heading -- despite the name evoking the TX/OK border lake, the AVA boundary is entirely inside Texas. Parented under Texas; no straddle recorded.

## Homonyms
- Georgia (US state) vs. the country Georgia -- included per scope. Both now exist in `regions.yaml` as separate `country` values (US vs GE), which the validator allows.
- La Rioja-style case does not recur here, but note: "Texas Hill Country" / "Hill Country" style informal names are US-specific and don't collide with anything outside scope.

## Grapes: identity and color calls (flagging, not guessing)
- Scuppernong: added instead of "Muscadine" -- Muscadine (Vitis rotundifolia) is a species with many commercial cultivars (Scuppernong, Carlos, Noble, Magnolia...); "Muscadine" alone would merge distinct varieties the way "Malvasia di Schierano into Malvasia di Casorzo" was flagged as a mistake. Scuppernong is the one most commonly named alone on labels. Colored it `gris` (bronze-skinned), not `white` -- a judgment call, flagging it.
- Catawba and Delaware: colored `rose` rather than `red` -- both are pale pink/red-skinned Vitis labrusca-family grapes commonly used for blush/rosé-style wines, not full reds. Flagging as a judgment call.
- Kept Marechal Foch's name unaccented (matches the existing `grapes.yaml` convention seen for other hybrids like "Cayuga White"/"La Crescent" which carry no diacritics); added "Foch" as the shorthand label synonym.

## Uncertain calls
- Lake Erie AVA parent set to Ohio because its only two nested sub-AVAs (Grand River Valley, Isle St. George) are both in Ohio, even though Lake Erie's core historic production and most acreage sit in NY/PA (Chautauqua-Erie). A reviewer with better label-frequency data might prefer New York.
- Upper Mississippi River Valley AVA parent set to Wisconsin because its one nested sub-AVA (Lake Wisconsin) is there, even though the AVA's acreage is split across IL/IA/MN/WI fairly evenly.
- Loess Hills District parent set to Iowa (17 of its ~19 counties are in Iowa; only 2 Missouri counties).
- Texoma: TTB's current established-AVA table lists it as a single-state Texas AVA, not multi-state, despite the name referencing the Texas-Oklahoma border lake. Followed TTB's current classification (Texas only) rather than the scope note describing it as a straddle -- flagging this discrepancy for review.
- "Keuka Lake" dropped from Finger Lakes synonyms -- it names a real lake within the Finger Lakes AVA but has no TTB AVA of its own and I found no retailer/label evidence of it being used as a stand-alone synonym for the whole Finger Lakes region. Flagging in case a reviewer has label evidence for it.
- Georgia/Oklahoma/Iowa/Louisiana state entries have no children of their own in this file (Iowa's Loess Hills District and Oklahoma's/Louisiana's Ozark Mountain / Mississippi Delta shares are parented elsewhere per the straddle calls above) -- they exist only so `lookup_region("Georgia")` etc. resolve to the right country-state row, matching the "state-level entry for every state that has at least one AVA" instruction.

## Label string -> canonical examples

| label string | kind | canonical | where seen (URL) |
|---|---|---|---|
| Seneca Lake | region | Seneca Lake | https://en.wikipedia.org/wiki/Seneca_Lake_AVA |
| Cayuga Lake AVA | region | Cayuga Lake | https://en.wikipedia.org/wiki/Cayuga_Lake_AVA |
| North Fork | region | North Fork of Long Island | https://en.wikipedia.org/wiki/North_Fork_of_Long_Island_AVA |
| The Hamptons | region | The Hamptons, Long Island | https://en.wikipedia.org/wiki/Long_Island_AVA |
| Hudson Valley | region | Hudson River Region | https://en.wikipedia.org/wiki/Hudson_River_Region_AVA |
| Monticello AVA | region | Monticello | https://en.wikipedia.org/wiki/Monticello_AVA |
| Middleburg | region | Middleburg Virginia | https://en.wikipedia.org/wiki/Middleburg_Virginia_AVA |
| Fredericksburg, Texas Hill Country | region | Fredericksburg in the Texas Hill Country | https://en.wikipedia.org/wiki/Fredericksburg_in_the_Texas_Hill_Country_AVA |
| Texas Hill Country AVA | region | Texas Hill Country | https://en.wikipedia.org/wiki/Texas_Hill_Country_AVA |
| Leelanau Peninsula | region | Leelanau Peninsula | https://en.wikipedia.org/wiki/Leelanau_Peninsula_AVA |
| Old Mission Peninsula AVA | region | Old Mission Peninsula | https://en.wikipedia.org/wiki/Old_Mission_Peninsula_AVA |
| Augusta, Missouri | region | Augusta | https://en.wikipedia.org/wiki/Augusta_AVA |
| Ozark Mountain AVA | region | Ozark Mountain | https://en.wikipedia.org/wiki/Ozark_Mountain_AVA |
| Grand Valley, Colorado | region | Grand Valley | https://en.wikipedia.org/wiki/Grand_Valley_AVA |
| Willcox AVA | region | Willcox | https://en.wikipedia.org/wiki/Willcox_AVA |
| Yadkin Valley | region | Yadkin Valley | https://en.wikipedia.org/wiki/Yadkin_Valley_AVA |
| Lake Erie AVA | region | Lake Erie | https://en.wikipedia.org/wiki/Lake_Erie_AVA |
| Grand River Valley, Ohio | region | Grand River Valley | https://en.wikipedia.org/wiki/Grand_River_Valley_AVA |
| Outer Coastal Plain | region | Outer Coastal Plain | https://en.wikipedia.org/wiki/Outer_Coastal_Plain_AVA |
| Cape May Peninsula AVA | region | Cape May Peninsula | https://en.wikipedia.org/wiki/Cape_May_Peninsula_AVA |
| Martha's Vineyard | region | Martha's Vineyard | https://en.wikipedia.org/wiki/Martha%27s_Vineyard_AVA |
| Cynthiana | grape | Norton | https://en.wikipedia.org/wiki/Norton_(grape) |
| Vidal | grape | Vidal Blanc | https://en.wikipedia.org/wiki/Vidal_blanc |
| Ravat 51 | grape | Vignoles | https://en.wikipedia.org/wiki/Vignoles_(grape) |
| Foch | grape | Marechal Foch | https://en.wikipedia.org/wiki/Marechal_Foch |
| Moore's Diamond | grape | Diamond | https://en.wikipedia.org/wiki/Diamond_(grape) |
| Scuppernong | grape | Scuppernong | https://en.wikipedia.org/wiki/Scuppernong_(grape) |

## Review (main session, 2026-09-26)

- **Multi-state AVAs with children became parentless overlays** (the
  brief's overlay rule): Ozark Mountain, Southeastern New England, Lake
  Erie and Upper Mississippi River Valley. Under one state, children in
  another state picked up the wrong state as an ancestor: Altus and
  Arkansas Mountain got Missouri, and Martha's Vineyard got Rhode Island.
  Their sub-AVAs now sit under their own state: Altus and Arkansas
  Mountain < Arkansas; Augusta, Hermann and Ozark Highlands < Missouri;
  Martha's Vineyard < Massachusetts; Grand River Valley and Isle St.
  George < Ohio; Lake Wisconsin < Wisconsin. The AVA containment is
  recorded here rather than in `parent`.
- Childless multi-state AVAs keep the agent's primary-state call.
- `Scuppernong`: color `white`, not `gris` (VIVC lists this bronze
  muscadine as white).
- Noted: the canonical grape names `Delaware`, `Niagara` and `Concord` are
  also place names. They are the grapes' real names, so they stay; the
  tagger should treat a bare "Delaware" in a region context as the state.
- Accepted: the folded-in sub-AVAs broken out (Seneca Lake, Cayuga Lake,
  North Fork, The Hamptons, Grand Valley, Willcox, Verde Valley,
  Monticello, Yadkin Valley, Leelanau, Old Mission); Texoma as
  single-state Texas per TTB; Muscadine not added as a grape.
- Merge (2026-09-26): `Petite Pearl` dropped (no Wikidata item). The
  Chilean `Central Valley` and `San Antonio Valley` lock entries had been
  given the Californian QIDs; set to null.
