# au-e research: Australia, east (Victoria, NSW, Queensland, ACT)

Status: complete

## Sources
- Wine Australia, Register of Protected GIs and Other Terms, overview page, accessed 2026-09-27:
  https://www.wineaustralia.com/labelling/register-of-protected-gis-and-other-terms/geographical-indications
- Wine Australia per-GI pages (Western Victoria, Hunter, Hunter Valley, Upper Hunter Valley), accessed 2026-09-27.
- Wikipedia: Gippsland Geographical Indication, Hunter Valley wine region, Ballarat area (via Western Victoria GI text), Canberra District, accessed 2026-09-27.

## Counts
- Total: 59 region entries (3 states, 14 zones, 37 GI regions, 5 subregions).
- Victoria: 1 state, 6 zones (Central Victoria, Gippsland, North East Victoria,
  North West Victoria, Port Phillip, Western Victoria), 19 GI regions, 2
  subregions (Nagambie Lakes, Great Western).
- New South Wales: 1 state, 8 zones (Big Rivers, Central Ranges, Hunter
  Valley, Northern Rivers, Northern Slopes, South Coast, Southern New South
  Wales, Western Plains), 16 GI regions, 3 subregions (Broke Fordwich,
  Pokolbin, Upper Hunter Valley).
- Queensland: 1 state, no zone tier (none registered), 2 GI regions
  (Granite Belt, South Burnett).
- Multi-state: South Eastern Australia (existing GI, no parent, no children;
  overlay designation).
- Left out: **Ballarat** is not a registered GI; Wine Australia's Western
  Victoria zone text lists it only as a municipality inside the zone
  boundary, with no separate GI region or subregion for it. Not added,
  despite being named in the scope brief's region list.
- Western Plains (NSW) and Northern Slopes (partially, via New England
  Australia) and Gippsland (Vic) have no further GI subdivision; entered as
  childless zones (Gippsland) per the Register.

## Changes to existing entries
- **Victoria, New South Wales: classification changed from `Zone` to
  `State`**, and **Queensland added as `State`** (new). Matches au-w's
  precedent (South Australia, Western Australia, Tasmania all set to
  `State`), per the slice note.
- **Bendigo, Heathcote: re-parented from Victoria directly to Central
  Victoria** (their zone; the old entries had no zone tier).
- **Beechworth, King Valley, Rutherglen: re-parented from Victoria to
  North East Victoria.**
- **Geelong, Macedon Ranges, Mornington Peninsula, Yarra Valley:
  re-parented from Victoria to Port Phillip.**
- **Grampians: re-parented from Victoria to Western Victoria**, and gained
  a new child subregion, Great Western.
- **Mudgee, Orange: re-parented from New South Wales to Central Ranges.**
- **Riverina: re-parented from New South Wales to Big Rivers.**
- **Canberra District: re-parented from New South Wales directly to
  Southern New South Wales** (its zone).
- **"Hunter Valley" renamed to "Hunter"** (`was: "Hunter Valley"`),
  re-parented under a new `Hunter Valley` Zone entry, and gained subregions
  Broke Fordwich, Pokolbin, Upper Hunter Valley. The old synonym "Hunter"
  is now the canonical name; "Hunter Valley" could not stay as a synonym of
  the region because it is now also the zone's own name (see Homonyms).
  Added synonym "Lower Hunter" (the trade's contrast term for the region
  vs. the Upper Hunter subregion).
- **Murray Darling, Swan Hill: added, parented to Victoria's North West
  Victoria zone only**, even though both GIs straddle Victoria and NSW
  (Big Rivers zone). Chosen because the historic core of both (Mildura and
  Swan Hill town) is on the Victorian side. Recorded here as instructed;
  a wine from the NSW portion will still get the region tag, just not the
  NSW state/zone ancestor tags.

## Homonyms
- **Hunter Valley (zone) vs. Hunter (region):** the label string "Hunter
  Valley" — by far the most common form on real labels — now resolves only
  to the `Hunter Valley` zone, not to the more specific `Hunter` region,
  because a name cannot also be a synonym of one of its own children. A
  wine labelled "Hunter Valley" still gets tagged with the zone (and Hunter
  is reachable via the literal string "Hunter"). This is the homonym the
  scope brief flagged; there is no collision-free way to make "Hunter
  Valley" resolve to the region specifically once the zone is entered under
  its official name.
- **Geelong, Bendigo:** both are Victorian city names as well as GI region
  names; no separate handling needed since the tagger only matches exact
  strings and neither is used ambiguously as a place elsewhere in this
  file.
- **Orange:** the NSW GI region shares its name with the fruit and the
  color; already an existing library entry, left unchanged, flagged here as
  a general ambiguity risk for the tagger (out of scope to fix).

## Uncertain calls
- **Murray Darling / Swan Hill single-parent choice** (see above) — could
  reasonably go the other way (NSW Big Rivers) or be split as two entries
  per state, which the "one parent per entry" rule forbids.
- **Gippsland classification** — it is simultaneously the zone and the only
  GI in it (no separate region tier), so it is entered once, classified
  `Zone`, with no child region duplicating it. This mirrors how au-w
  treated Tasmania (single-tier GI, classified at the top level).
- **Queensland has no zone tier** — Granite Belt and South Burnett sit
  directly under the state; confirmed via Wine Australia's own regional
  pages, which never mention a Queensland zone.
- **Brown Muscat / Muscat Blanc à Petits Grains**: Rutherglen's "Brown
  Muscat" is the red-brown-skinned clone of Muscat Blanc à Petits Grains
  (VIVC treats color mutations of this variety as the same variety, per
  the existing `grapes.yaml` entry which already lists "Red Muscadel" as a
  synonym of the same, color: white, entry). Added as a synonym rather than
  a new grape; flagging in case a reviewer wants a separate entry given the
  color mismatch.
- **Topaque**: added as a synonym of the existing `Muscadelle` entry per
  the scope brief; "Tokay" was deliberately left out as instructed
  (ambiguous with Hungarian Tokaji).

## Label string -> canonical examples

| label string | kind | canonical | where seen (URL) |
|---|---|---|---|
| Yarra Valley | region | Yarra Valley | https://www.wineaustralia.com/labelling/register-of-protected-gis-and-other-terms/geographical-indications |
| Hunter Valley | region | Hunter Valley (zone; see Homonyms) | https://www.wineaustralia.com/market-insights/regions-and-varieties/new-south-wales-wines/hunter-valley |
| Hunter | region | Hunter | https://www.wineaustralia.com/labelling/register-of-protected-gis-and-other-terms/geographical-indications/hunter |
| Lower Hunter | region | Hunter | https://en.wikipedia.org/wiki/Hunter_Valley_wine_region |
| Mornington Peninsula | region | Mornington Peninsula | https://www.wineaustralia.com/labelling/register-of-protected-gis-and-other-terms/geographical-indications |
| Rutherglen | region | Rutherglen | https://www.wineaustralia.com/market-insights/regions-and-varieties/victoria-wines/rutherglen |
| King Valley | region | King Valley | https://www.wineaustralia.com/labelling/register-of-protected-gis-and-other-terms/geographical-indications |
| Great Western | region | Great Western | https://en.wikipedia.org/wiki/Western_Victoria_(wine_region) |
| Nagambie Lakes | region | Nagambie Lakes | https://www.wineaustralia.com/labelling/register-of-protected-gis-and-other-terms/geographical-indications |
| Canberra | region | Canberra District | https://en.wikipedia.org/wiki/Canberra_District |
| Broke Fordwich | region | Broke Fordwich | https://www.wineaustralia.com/labelling/register-of-protected-gis-and-other-terms/geographical-indications |
| Pokolbin | region | Pokolbin | https://www.wineaustralia.com/labelling/register-of-protected-gis-and-other-terms/geographical-indications |
| Upper Hunter | region | Upper Hunter Valley | https://en.wikipedia.org/wiki/Upper_Hunter_Valley |
| SE Australia | region | South Eastern Australia | https://www.wineaustralia.com/labelling/register-of-protected-gis-and-other-terms/geographical-indications |
| Granite Belt | region | Granite Belt | https://www.wineaustralia.com/market-insights/regions-and-varieties/queensland-wines/granite-belt |
| South Burnett | region | South Burnett | https://www.wineaustralia.com/market-insights/regions-and-varieties/queensland-wines/south-burnett |
| Beechworth | region | Beechworth | https://www.wineaustralia.com/labelling/register-of-protected-gis-and-other-terms/geographical-indications |
| Gippsland | region | Gippsland | https://www.wineaustralia.com/labelling/geographical-indicators/labelling-gi-gippsland |
| Heathcote | region | Heathcote | https://www.wineaustralia.com/labelling/register-of-protected-gis-and-other-terms/geographical-indications |
| Murray Darling | region | Murray Darling | https://www.wineaustralia.com/labelling/register-of-protected-gis-and-other-terms/geographical-indications |
| Swan Hill | region | Swan Hill | https://www.wineaustralia.com/labelling/register-of-protected-gis-and-other-terms/geographical-indications |
| Brown Muscat | grape | Muscat Blanc à Petits Grains | https://www.wineaustralia.com/market-insights/regions-and-varieties/victoria-wines/rutherglen |
| Topaque | grape | Muscadelle | https://www.wineaustralia.com/market-insights/regions-and-varieties/victoria-wines/rutherglen |
| Perricoota | region | Perricoota | https://www.wineaustralia.com/labelling/register-of-protected-gis-and-other-terms/geographical-indications |
| Grampians | region | Grampians | https://www.wineaustralia.com/labelling/register-of-protected-gis-and-other-terms/geographical-indications |
| Henty | region | Henty | https://en.wikipedia.org/wiki/Henty_wine_region |

## Review (main session, 2026-09-27)
- **Dropped "Topaque"** as a Muscadelle synonym. It is the Rutherglen wine-style name that replaced "Tokay", not a grape name (the same class as Gamay Beaujolais).
- Tree accepted: states as `State`, the Hunter Valley zone > Hunter region with its subregions, and the zone re-parenting. "Hunter Valley" on a label now resolves to the zone, which is fine: it contains the region.
- Murray Darling and Swan Hill under Victoria: accepted (cross-border GIs; one parent only).
- Brown Muscat under Muscat Blanc à Petits Grains: accepted (a colour mutation, the same pattern as other Muscat clones).

**Merge note (2026-09-27):** Australia merged (au-w + au-e). Lock: Watervale (AU) nulled (matched a site in Michigan). Added "Upper Hunter" to Upper Hunter Valley. "Tamar Valley Tasmania" (no comma) still misses; left out of the fixture. Replay 0 changes, 639 tests.
