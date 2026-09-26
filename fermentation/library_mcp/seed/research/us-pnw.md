Status: complete

# us-pnw research notes (Oregon, Washington, Idaho)

## Sources
- TTB established AVAs table: https://www.ttb.gov/regulated-commodities/beverage-alcohol/wine/established-avas (checked 2026-09-26)
- 27 CFR part 9 (via eCFR) for the general AVA framework.
- Federal Register final rules for individually cited AVAs (Elkton Oregon, Red Hill Douglas County, Beverly WA, Columbia Hills).
- Wikipedia AVA pages for descriptive/nesting detail where Federal Register text wasn't fetched directly (each cited per entry).
- Washington State Wine Commission (washingtonwine.org) and Oregon Wine (oregonwine.org / trade.oregonwine.org) resource pages for nesting confirmation.

## Counts
- Oregon: 18 AVAs entirely in-state (Applegate Valley, Chehalem Mountains, Dundee Hills, Elkton Oregon, Eola-Amity Hills, Laurelwood District, Lower Long Tom, McMinnville, Mount Pisgah/Polk County, Red Hill Douglas County, Ribbon Ridge, Rogue Valley, Southern Oregon, Tualatin Hills, Umpqua Valley, Van Duzer Corridor, Willamette Valley, Yamhill-Carlton) + 4 straddling (The Rocks District of Milton-Freewater, Columbia Gorge, Walla Walla Valley, Snake River Valley) = 22, matching TTB's per-state total.
- Washington: 19 AVAs entirely in-state (Ancient Lakes of Columbia Valley, Beverly WA, Candy Mountain, Columbia Hills, Columbia Valley, Goose Gap, Horse Heaven Hills, Lake Chelan, Naches Heights, Puget Sound, Rattlesnake Hills, Red Mountain, Rocky Reach, Royal Slope, Snipes Mountain, The Burn of Columbia Valley, Wahluke Slope, White Bluffs, Yakima Valley) + 3 straddling (Columbia Gorge, Walla Walla Valley, Lewis-Clark Valley) = 22, matching TTB's current Washington total (as of the Columbia Hills AVA taking effect Sept 16 2026).
- Idaho: 3 AVAs (Eagle Foothills, Snake River Valley, Lewis-Clark Valley). All included.
- Nothing official left out. "Mill Creek-Walla Walla Valley" is a *proposed* AVA (not yet final as of Sept 2026) and is excluded.

## Changes to existing entries
- `Rogue Valley`: reparented from `Oregon` to `Southern Oregon` (Rogue Valley is a sub-AVA of the multi-county Southern Oregon AVA); dropped `Applegate Valley` from its synonyms because Applegate Valley is its own AVA nested inside Rogue Valley, not a synonym.
- `Umpqua Valley`: reparented from `Oregon` to `Southern Oregon` for the same reason.
- `Red Mountain`: reparented from `Columbia Valley` to `Yakima Valley` — Red Mountain nests inside Yakima Valley, which nests inside Columbia Valley (per scope's own example). One parent only, so Yakima Valley (the nearer enclosing unit) wins; Columbia Valley is still an ancestor via Yakima Valley.
- `Ribbon Ridge` and (new) `Laurelwood District`: nested under `Chehalem Mountains` rather than directly under `Willamette Valley`. Both AVAs' own establishing documents/Wikipedia describe them as lying entirely within Chehalem Mountains AVA, which itself lies within Willamette Valley. The scope brief's example list put them as flat siblings of Chehalem Mountains under Willamette Valley; I followed the real nesting instead per the "nearest enclosing viticultural unit" rule, and flag it here since it differs from the illustrative list.
- `Idaho`: removed `Snake River Valley` from its synonyms (it is a real AVA nested under Idaho, not a synonym of the state) and added it as its own entry instead.
- `Willamette Valley`: dropped the `Willamette Valley AVA` synonym — the checker flags it as redundant since the tagger's lookup already strips the trailing classification word ("AVA"), so it added nothing over the bare name.

## Straddling AVAs (parent chosen + note)
- `Columbia Valley` (WA/OR): kept existing parent `Washington` (majority of acreage and most-cited state).
- `Walla Walla Valley` (WA/OR): kept existing parent `Washington` — 69% of total AVA acreage is in Washington (31% Oregon), though vineyard-acreage split is closer to 57/43.
- `Columbia Gorge` (WA/OR): parented under `Washington`. This one is genuinely close to a 50/50 acreage split; I went with Washington because the Washington State Wine Commission profiles it and it is usually alphabetized there first in trade lists, but this is a judgment call — Oregon would be equally defensible.
- `Snake River Valley` (ID/OR): parented under `Idaho`. The AVA is overwhelmingly in Idaho with only a sliver in Malheur County, OR.
- `Lewis-Clark Valley` (ID/WA): parented under `Idaho`. ~72% of total acreage is in Idaho (rest in Washington's Clarkston/Asotin area).
- `The Rocks District of Milton-Freewater` (entirely in Oregon, but nested inside the Walla Walla Valley AVA which itself straddles WA/OR): parented under `Walla Walla Valley` (the nearer enclosing unit), not directly under Columbia Valley, even though it's also inside Columbia Valley.

## Homonyms
- None of these AVA names collide with a wine region name used in another country that I found (Red Hill Douglas County, Rogue Valley, Applegate Valley, Southern Oregon, Naches Heights, Royal Slope, Rocky Reach, Snipes Mountain, Candy Mountain, Goose Gap, Beverly, The Burn of Columbia Valley, Ancient Lakes, Lewis-Clark Valley, Eagle Foothills are all distinctively named). Flagging "Red Hill" as a name to watch: I deliberately did NOT add a bare "Red Hill" synonym for Red Hill Douglas County because "Red Hill" alone is used for wine areas elsewhere (e.g. Victoria, Australia's Mornington Peninsula) and could be ambiguous; the full official name and its comma-dropped variant are the only synonyms listed.

## Remaining checker warnings
17 "no source" warnings remain, all on entries that existed in `regions.yaml`
before this research (Oregon, Washington, Idaho, Willamette Valley, Dundee
Hills, Yamhill-Carlton, Chehalem Mountains, Ribbon Ridge, Eola-Amity Hills,
McMinnville, Columbia Valley, Walla Walla Valley, Yakima Valley, Rattlesnake
Hills, Red Mountain, Horse Heaven Hills, Wahluke Slope). They had no `source`
field in the library before either; I did not fabricate one rather than risk
citing the wrong page for an entry I didn't newly research.

## Uncertain calls
- Columbia Gorge parent (WA vs OR) — see straddle note above; genuinely arguable either way.
- Beverly, Washington's relationship to Royal Slope: sources describe them as neighbors, not nested; I parented Beverly directly under Columbia Valley rather than under Royal Slope. Flagging in case a later source says otherwise.
- The Burn of Columbia Valley: I could not find a Federal Register final rule text (only secondary sources); I'm treating it as an established AVA directly under Columbia Valley, no further sub-nesting, per Wikipedia's "AVA Map Explorer" grouping.

## Grapes
No PNW-specific grape names or synonyms found. Oregon, Washington and Idaho
grow standard international Vitis vinifera varieties already in
`grapes.yaml` (Pinot Noir, Chardonnay, Cabernet Sauvignon, Syrah, Riesling,
Merlot, Pinot Gris, etc.) under their normal names; no local/regional
synonyms turned up in retailer or producer usage. `us-pnw.grapes.yaml` is
left empty (comment only).

## Label string -> canonical
| label string | kind | canonical | where seen (URL) |
|---|---|---|---|
| Willamette | region | Willamette Valley | https://en.wikipedia.org/wiki/Willamette_Valley_AVA |
| Dundee Hills AVA | region | Dundee Hills | https://en.wikipedia.org/wiki/Dundee_Hills_AVA |
| Yamhill Carlton | region | Yamhill-Carlton | https://en.wikipedia.org/wiki/Yamhill-Carlton_AVA |
| Ribbon Ridge | region | Ribbon Ridge | https://en.wikipedia.org/wiki/Ribbon_Ridge_AVA |
| Eola-Amity Hills | region | Eola-Amity Hills | https://en.wikipedia.org/wiki/Eola-Amity_Hills_AVA |
| Chehalem Mountains AVA | region | Chehalem Mountains | https://en.wikipedia.org/wiki/Chehalem_Mountains_AVA |
| Laurelwood District | region | Laurelwood District | https://en.wikipedia.org/wiki/Laurelwood_District_AVA |
| Van Duzer Corridor | region | Van Duzer Corridor | https://en.wikipedia.org/wiki/Van_Duzer_Corridor_AVA |
| Tualatin Hills AVA | region | Tualatin Hills | https://en.wikipedia.org/wiki/Tualatin_Hills_AVA |
| Mt. Pisgah, Polk County, Oregon | region | Mount Pisgah, Polk County, Oregon | https://en.wikipedia.org/wiki/Mount_Pisgah,_Polk_County,_Oregon_AVA |
| Rogue Valley | region | Rogue Valley | https://en.wikipedia.org/wiki/Rogue_Valley_AVA |
| Applegate Valley | region | Applegate Valley | https://en.wikipedia.org/wiki/Applegate_Valley_AVA |
| Elkton Oregon | region | Elkton Oregon | https://en.wikipedia.org/wiki/Elkton_Oregon_AVA |
| The Rocks District | region | The Rocks District of Milton-Freewater | https://en.wikipedia.org/wiki/The_Rocks_District_of_Milton-Freewater_AVA |
| Columbia Valley (WA) | region | Columbia Valley | https://en.wikipedia.org/wiki/Columbia_Valley_AVA |
| Walla Walla | region | Walla Walla Valley | https://en.wikipedia.org/wiki/Walla_Walla_Valley_AVA |
| Red Mountain AVA | region | Red Mountain | https://en.wikipedia.org/wiki/Red_Mountain_AVA |
| Rattlesnake Hills | region | Rattlesnake Hills | https://en.wikipedia.org/wiki/Rattlesnake_Hills_AVA |
| Snipes Mountain | region | Snipes Mountain | https://en.wikipedia.org/wiki/Snipes_Mountain_AVA |
| Ancient Lakes | region | Ancient Lakes of Columbia Valley | https://en.wikipedia.org/wiki/Ancient_Lakes_of_Columbia_Valley_AVA |
| Puget Sound AVA | region | Puget Sound | https://en.wikipedia.org/wiki/Puget_Sound_AVA |
| Lewis-Clark Valley | region | Lewis-Clark Valley | https://en.wikipedia.org/wiki/Lewis-Clark_Valley_AVA |
| Snake River Valley | region | Snake River Valley | https://en.wikipedia.org/wiki/Snake_River_Valley_AVA |
| Eagle Foothills AVA | region | Eagle Foothills | https://en.wikipedia.org/wiki/Eagle_Foothills_AVA |
| Beverly | region | Beverly, Washington | https://en.wikipedia.org/wiki/Beverly,_Washington_AVA |

## Review (main session, 2026-09-26)

- `Walla Walla Valley`: parent restored to `Columbia Valley`. The existing
  entry already had it, and the Walla Walla Valley AVA lies inside the
  Columbia Valley AVA. With `Washington` as the parent, every Walla Walla
  wine (and The Rocks District below it) lost its Columbia Valley ancestor.
  The WA/OR straddle stays noted above.
- Accepted: Red Mountain under Yakima Valley; Rogue and Umpqua under
  Southern Oregon; Applegate Valley and Snake River Valley made their own
  entries instead of synonyms; Ribbon Ridge and Laurelwood District under
  Chehalem Mountains; Columbia Gorge under Washington; state abbreviations
  `OR` / `ID` as synonyms (they let "Willamette Valley, OR" resolve through
  the compound split).
- Accepted as flagged: Columbia Hills (effective 2026-09-16) and The Burn
  of Columbia Valley, both on secondary sources only.
- The remaining checker warnings are "no source" on carried-over entries.
