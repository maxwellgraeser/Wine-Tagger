# NZ research

Status: complete

## Sources

- IPONZ geographical indications register, individual entries fetched 2026-09-27
  (register.../northland/, auckland/, matakana/, kumeu/, waiheke-island/,
  gisborne/, hawkes-bay/, central-hawkes-bay/, wairarapa/, martinborough/,
  gladstone/, nelson/, marlborough/, canterbury/, north-canterbury/,
  waipara-valley/, waitaki-valley-north-otago/, central-otago/, bannockburn/).
  This is the current official register under the Geographical Indications
  (Wine and Spirits) Registration Act 2006.
- nzwine.com regions pages and winewithseth.com GI summary, for confirming
  hierarchy and current status as of 2026.
- wine-searcher.com Marlborough page, centralotagowine.co/place-subregions,
  winefolly.com Hawke's Bay and Nelson guides, wine-searcher.com Bridge Pa
  Triangle page, for informal label subregions (no GI status).

## Counts

Official register: 20 registered wine GIs confirmed by direct lookup (IP
numbers 1004–1022, 1028; some secondary reporting says "23 by 2024" but I
could not find named entries for the 3 extra beyond these 20 via direct
IPONZ page lookups, so I produced the 20 I could confirm). Produced: 20 GI
entries, matching the register, plus 12 informal label subregions
(Wairau Valley, Southern Valleys, Awatere Valley under Marlborough;
Gibbston, Bendigo, Cromwell, Lowburn, Pisa, Alexandra, Wanaka under Central
Otago; Bridge Pa Triangle under Hawke's Bay; Moutere Hills, Waimea Plains
under Nelson; Gimblett Gravels already existed). Total 32 region entries,
matching all 12 pre-existing library entries plus 20 new ones.

I did not find a "Wellington" GI (404 on IPONZ, and the Wellington
references in secondary sources are the administrative region containing
Wairarapa/Martinborough/Gladstone, not a separate wine GI). I left it out;
flagged as uncertain below.

## Changes to existing entries

- **Canterbury**: dropped synonym "North Canterbury" because North
  Canterbury is now its own registered GI (IP 1016) and must be a child
  entry, not a synonym, per the brief's rule that sub-appellations are
  never folded into their parent.
- **Waipara → Waipara Valley**: renamed to match the GI's registered form
  ("Waipara Valley / Waipara"); kept "Waipara" as a synonym. Added
  `was: "Waipara"`.
- **Waipara Valley re-parented**: IPONZ registers Waipara Valley as a
  direct child of Canterbury (sibling of North Canterbury), but I nested
  it under North Canterbury per the scope note and because that is how
  retailers describe it (Waipara Valley is the wine-producing part of the
  North Canterbury district). Flagged as uncertain below.
- **Hawke's Bay, Central Otago, Auckland, Wairarapa, Nelson, Marlborough**:
  unchanged, only gained children.

## Homonyms

None noted for NZ region names against other countries in this pass
(Waiheke, Bannockburn, Gladstone, etc. are not common wine-region names
elsewhere).

## Uncertain calls

- **Wellington GI**: scope note lists "Wellington" as a registered GI; I
  could not confirm this on IPONZ (404) or in any secondary source beyond
  it being the administrative region name for Wairarapa. Left out; flag
  for review in case a "Wellington" GI was registered very recently and
  not yet reflected in the pages I fetched.
- **Waipara Valley parent**: see above — official register has it as a
  Canterbury child, not a North Canterbury child. I followed the scope's
  requested nesting (retail convention) over the literal IPONZ sibling
  relationship.
- **23 vs 20 GIs**: several secondary sources (WineSearcher summaries,
  general web search answers) say NZ has "23" registered wine GIs as of
  2024, but I could only confirm 20 named, distinct GIs via direct IPONZ
  page lookups. The extra 3 may be recent additions I didn't find, or the
  count may include renewals/duplicates. Left as open question.
- **Central Otago sub-basin nesting**: some sources describe Cromwell
  Basin as containing Pisa and Lowburn as sub-areas, rather than all four
  being siblings. I listed Gibbston, Bendigo, Cromwell, Lowburn, Pisa,
  Alexandra, Wanaka all as flat children of Central Otago per the scope's
  flat list; a stricter hierarchy would nest Pisa/Lowburn under Cromwell.
- **NZ grapes file**: no NZ-specific grape names or synonyms found; NZ
  labels use standard international variety names.

## Label string → canonical

| label string | kind | canonical | where seen (URL) |
|---|---|---|---|
| Marlborough Sauvignon Blanc | region | Marlborough | https://www.nzwine.com/en/regions/marlborough/ |
| Wairau Valley | region | Wairau Valley | https://www.wine-searcher.com/regions-marlborough |
| Awatere Valley | region | Awatere Valley | https://www.wine-searcher.com/regions-marlborough |
| Southern Valleys | region | Southern Valleys | https://www.wine-searcher.com/regions-marlborough |
| Central Otago Pinot Noir | region | Central Otago | https://www.nzwine.com/en/regions/centralotago/ |
| Bannockburn | region | Bannockburn | https://www.iponz.govt.nz/get-ip/geographical-indications/register/bannockburn/ |
| Gibbston Valley | region | Gibbston | https://appellationwinetours.nz/about-appellation-wine-tours/the-central-otago-wine-region/ |
| Cromwell Basin | region | Cromwell | https://www.centralotagowine.co/place-subregions |
| Bendigo, Central Otago | region | Bendigo | https://www.centralotagowine.co/place-subregions |
| Wanaka | region | Wanaka | https://appellationwinetours.nz/about-appellation-wine-tours/the-central-otago-wine-region/ |
| Hawke's Bay | region | Hawke's Bay | https://www.nzwine.com/en/regions/hawkesbay/ |
| Hawkes Bay | region | Hawke's Bay | https://en.wikipedia.org/wiki/Hawke%27s_Bay_wine_region |
| Central Hawke's Bay | region | Central Hawke's Bay | https://www.iponz.govt.nz/get-ip/geographical-indications/register/central-hawkes-bay/ |
| Gimblett Gravels | region | Gimblett Gravels | https://winefolly.com/deep-dive/guide-to-hawkes-bay/ |
| Bridge Pa Triangle | region | Bridge Pa Triangle | https://www.wine-searcher.com/regions-bridge+pa+triangle |
| Waiheke Island | region | Waiheke Island | https://en.wikipedia.org/wiki/Waiheke_Island_wine_region |
| Waiheke | region | Waiheke Island | https://en.wikipedia.org/wiki/Waiheke_Island_wine_region |
| Matakana | region | Matakana | https://www.iponz.govt.nz/get-ip/geographical-indications/register/matakana/ |
| Kumeu | region | Kumeu | https://www.iponz.govt.nz/get-ip/geographical-indications/register/kumeu/ |
| Martinborough | region | Martinborough | https://www.iponz.govt.nz/get-ip/geographical-indications/register/martinborough/ |
| Gladstone, Wairarapa | region | Gladstone | https://www.iponz.govt.nz/get-ip/geographical-indications/register/gladstone/ |
| Waipara Valley | region | Waipara Valley | https://www.iponz.govt.nz/get-ip/geographical-indications/register/waipara-valley/ |
| North Canterbury | region | North Canterbury | https://www.iponz.govt.nz/get-ip/geographical-indications/register/north-canterbury/ |
| Waitaki Valley North Otago | region | Waitaki Valley | https://www.iponz.govt.nz/get-ip/geographical-indications/register/waitaki-valley-north-otago/ |
| Moutere Hills | region | Moutere Hills | https://winefolly.com/deep-dive/guide-to-nelson-wine-region/ |
| Waimea Plains | region | Waimea Plains | https://winefolly.com/deep-dive/guide-to-nelson-wine-region/ |

## Review (main session, 2026-09-27)
- Hierarchy checked with `check --tree`: GIs nested as the scope asked;
  North Canterbury correctly split out of Canterbury's synonyms.
- Accepted Waipara Valley under North Canterbury (label nesting) and the
  flat Central Otago sub-basins. No Wellington GI: accepted.
- Merge: QID picks for Bendigo, Cromwell and Pisa were homonyms elsewhere (AU, US, IT); nulled in the lock.
