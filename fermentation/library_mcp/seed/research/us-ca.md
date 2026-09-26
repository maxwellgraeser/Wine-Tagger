Status: complete

# United States — California (us-ca) — ground-truth research notes

## Sources

- **TTB, "Established American Viticultural Areas"** —
  `https://www.ttb.gov/regulated-commodities/beverage-alcohol/wine/established-avas`
  — the official roster (154 California AVAs as of the current list; matched
  exactly by this file's AVA-classified entry count, see Counts below). TTB's
  own list is a flat roster with no encoded hierarchy, so it was used to
  confirm existence/count, not nesting.
- **Wikipedia, "List of American Viticultural Areas"** —
  `https://en.wikipedia.org/wiki/List_of_American_Viticultural_Areas` —
  page states "As of 2026 ... Over half (154) of the AVAs are in California,"
  last TTB-sourced update noted August 18, 2026 on that page. Used for the
  complete California roster, grouped into the informal clusters (North
  Coast, Central Coast, Central Valley, Sierra Foothills, South Coast, Klamath
  Mountains, Cascade Foothills) that this file's comment headers follow.
- **Individual AVA Wikipedia pages** (each fetched and read directly, not
  summarized secondhand, specifically for their infobox "Part of" / "Sub-regions"
  / "Other regions" fields, which is the only place nesting is stated
  explicitly): Napa Valley, Sonoma Coast, Clear Lake, Mendocino, Monterey, San
  Benito, San Francisco Bay, San Luis Obispo Coast, Paso Robles, Fair Play,
  California Shenandoah Valley, Alisos Canyon, Los Olivos District, San Ysidro
  District, South Coast, Malibu Coast, Antelope Valley of the California High
  Desert, Lodi, Clarksburg, Squaw Valley-Miramonte, Diablo Grande, Tracy
  Hills, Salado Creek, Paulsell Valley. URLs are on each entry's `source:`.
- **Federal Register / reginfo.gov** — confirmed two San Diego County AVAs
  (Rancho Santa Fe, Rancho Guejito) are still at the *proposed* stage, not
  established, and that a rename of Squaw Valley-Miramonte to "Yokuts Valley"
  is proposed but not yet finalized. See "Left out" and "Uncertain calls."

## Counts

| Level | Official (TTB, current) | Produced |
|---|---|---|
| California AVAs | 154 | 154 |
| Non-AVA container entries (state, counties used as label regions, and the informal "Central Valley") | — | 11 |
| **Total entries in `us-ca.regions.yaml`** | | **165** |

The 154 figure is an exact match to Wikipedia's current TTB-sourced count,
verified by counting every AVA name in each of the seven informal groupings
on the "List of American Viticultural Areas" page against this file — nothing
from the California section of that list was dropped.

**Left out, and why:**
- **Rancho Santa Fe** (San Diego County) — proposed August 2026
  (`federalregister.gov/documents/2026/08/14/2026-16671`), not yet an
  established AVA.
- **Rancho Guejito** (San Diego County) — proposed August 2024, would overlap
  the existing San Pasqual Valley AVA; not yet established.
- Both would belong under South Coast if/when finalized.

## Changes to existing entries

The single biggest pattern, repeated eight times, is the same bug the brief
calls out for South Africa's "Robertson"/"Robertson Valley": a real,
separately-established AVA had been folded into its parent's `synonyms:`
list instead of getting its own entry. Each of these is a distinct legal
appellation with its own TTB rulemaking, not a nickname:

1. **`Monterey County`** had `synonyms: ["Monterey", "Monterey AVA"]`. But
   "Monterey" is itself a real AVA (est. 1984) covering only the eastern part
   of the county — it excludes Carmel Valley, Chalone, Gabilan Mountains and
   San Antonio Valley, which sit elsewhere in the county. Split into
   `Monterey County` (plain county label, no classification) → `Monterey`
   (AVA) → its real sub-AVAs (Arroyo Seco, Hames Valley, San Bernabe, San
   Lucas, Santa Lucia Highlands, all reparented from Monterey County to
   Monterey). Source: `en.wikipedia.org/wiki/Monterey_AVA`.
2. **`Mendocino County`** had `synonyms: ["Mendocino"]`. Same pattern:
   "Mendocino" AVA (est. 1984) is a real sub-area of the county with its own
   8 sub-AVAs. Split the same way; `Anderson Valley` reparented from
   Mendocino County to Mendocino. Source: `en.wikipedia.org/wiki/Mendocino_AVA`.
3. **`Sonoma Coast`** had `synonyms: ["West Sonoma Coast", "Fort
   Ross-Seaview"]`. Both are real, separately-established AVAs explicitly
   carved out of Sonoma Coast's boundary (Fort Ross-Seaview 2011, West
   Sonoma Coast 2023) — Sonoma Coast's own Wikipedia history section names
   them as the two areas "recognized"/"established" out of it. Promoted both
   to children of Sonoma Coast. (Sonoma Coast's infobox also lists Chalk
   Hill, Los Carneros, Northern Sonoma, Petaluma Gap, Russian River Valley
   and Sonoma Valley as "sub-regions" — these merely *overlap* Sonoma
   Coast's very large boundary and are not described anywhere as
   subordinate to it, so they keep Sonoma County as their direct parent.
   Recorded as an overlap, not a nesting, per the brief's Sonoma
   Coast/Russian River Valley example.)
4. **`Lake County`** had `synonyms: ["Clear Lake"]`. "Clear Lake" AVA (est.
   1984) has 5 of its own sub-AVAs. Promoted to a child of Lake County, with
   Big Valley District-Lake County, High Valley, Kelsey Bench-Lake County,
   Red Hills Lake County and Upper Lake Valley as its children.
5. **`San Luis Obispo County`** had `synonyms: [..., "SLO Coast"]`. "San Luis
   Obispo Coast" AVA (est. 2022, "SLO Coast" is its official other name) has
   its own two sub-AVAs. Promoted; `Edna Valley` and `Arroyo Grande Valley`
   reparented from San Luis Obispo County to San Luis Obispo Coast.
6. **`Amador County`** had `synonyms: ["Shenandoah Valley (California)",
   "Fiddletown"]`. Both are real AVAs. Per California Shenandoah Valley's own
   page, neither nests under a county-level AVA — both attach directly to
   Sierra Foothills (Shenandoah Valley spans Amador *and* El Dorado
   counties, so it can't have a single-county parent anyway). Promoted both
   to siblings of Amador County under Sierra Foothills.
7. **`Paso Robles`** had `synonyms: ["Paso Robles AVA", "Adelaida District",
   "Willow Creek District"]`. Adelaida District and Willow Creek District are
   2 of Paso Robles' 11 official 2014 sub-appellations (the other 9 were
   simply missing). All 11 promoted to children: Adelaida District, Creston
   District, El Pomar District, Paso Robles Estrella District, Paso Robles
   Geneseo District, Paso Robles Highlands District, Paso Robles Willow
   Creek District, San Juan Creek, San Miguel District, Santa Margarita
   Ranch, Templeton Gap District.

Other reparents (not renames — each existing entry keeps its name, only
`parent` changes) made because the correct containing AVA is now in this
file where it wasn't before:

8. **`Livermore Valley`** and **`Santa Cruz Mountains`**: California →
   `San Francisco Bay` (a real AVA, est. 1999, whose boundary was expanded in
   2024 to include both; previously absent from the library entirely).
9. **`Temecula Valley`**: California → `South Coast` (Temecula Valley is one
   of only four AVAs actually nested inside South Coast's boundary; South
   Coast itself is new to this file).
10. **`Paso Robles`** itself: `Central Coast` → `San Luis Obispo County`,
    matching the convention already used for Monterey/Mendocino/Santa
    Barbara (county node between the coast-wide AVA and the town-level AVA).

No entry's `name` changed (no `was:` needed) — every fix above is either a
promotion of a hidden synonym to its own entry, or a `parent` correction.

## Homonyms

- **"Central Valley"** — this file adds it as an informal (non-AVA) parent
  for California's Central Valley AVAs (Lodi, Clarksburg, Madera, etc.),
  following the wording of Lodi's and Clarksburg's own Wikipedia infoboxes
  ("Part of: California, Central Valley, ..."). Chile's "Central Valley" (ES:
  Valle Central) is already in `regions.yaml` as its own CL entry. Same
  string, different country — allowed per the brief, flagged here as
  instructed.
- **"Shenandoah Valley"** — California's is added only as `"Shenandoah
  Valley (California)"` (disambiguated, matching the Wikipedia page title),
  specifically so the bare name stays free for us-rest's Virginia/West
  Virginia "Shenandoah Valley AVA" (a real, different, shared-state AVA not
  yet in the library). Do not add bare "Shenandoah Valley" to either without
  checking the other first.
- **"Red Hills Lake County"** vs. Oregon's **"Red Hill Douglas County,
  Oregon AVA"** — not an exact string match (Hills/Hill, and the Oregon name
  keeps "Douglas County, Oregon" inline), so no actual collision, but close
  enough in form to flag for us-pnw.
- **"Willow Creek"** (a standalone Klamath Mountains AVA, Humboldt/Trinity
  counties) vs. **"Paso Robles Willow Creek District"** — both California,
  different exact strings (no collision), but worth knowing these are
  unrelated appellations 400 miles apart that happen to share a common
  place-name element.

## Uncertain calls

- **"Central Valley" as an added informal parent tier.** It is not an AVA
  and had no entry in the library before. I added it because Lodi's and
  Clarksburg's own Wikipedia infoboxes literally list "Central Valley" as
  part of their "Part of" chain, and because the brief invites informal
  trade names (Uco Valley, Sonoma Coast). But unlike Uco Valley, "Central
  Valley" wines are rarely marketed with that term on premium labels (it
  connotes bulk wine); a reviewer may prefer these AVAs attach directly to
  `California` instead. Affects: Lodi, Clarksburg, Madera, Dunnigan Hills,
  Capay Valley, Winters Highlands, Diablo Grande, Tracy Hills, River
  Junction, Salado Creek, Paulsell Valley, Squaw Valley-Miramonte (12
  entries would need re-parenting to `California` if this call is reversed).
- **Chalone, Gabilan Mountains, Pacheco Pass parented to `San Benito
  County`.** All three straddle the Monterey/San Benito (Pacheco Pass also
  Santa Clara) county line. San Benito AVA's own Wikipedia page lists all
  three under "Other regions in ... San Benito County," which is the source
  I followed, but Monterey AVA's page lists the same three under "Other
  regions in ... Monterey County." Since an entry can have only one parent,
  I picked San Benito County; a reviewer with access to the actual TTB
  boundary descriptions could confirm which county holds the larger share.
- **Squaw Valley-Miramonte** kept under its current official name. TTB has
  a *proposed* (not final, per reginfo.gov RIN 1513-AD18, last agenda entry
  April 2025) rule to rename it "Yokuts Valley" — the surrounding
  unincorporated community was already renamed from "Squaw Valley" to
  "Yokuts Valley" under a 2022 California state law. If the AVA rename
  finalizes before this is merged, this entry needs `was: "Squaw
  Valley-Miramonte"` added.
- **Los Carneros** kept parented directly to `North Coast` (unchanged),
  because it spans both Napa and Sonoma counties and so cannot sit under
  either county node — even though both Napa Valley's and Sonoma Coast's own
  infoboxes list it as a "sub-region."
- **"Northern Sonoma"** modeled as a leaf AVA (no children) under Sonoma
  County. It is a real, established (1990) AVA, but its purpose is to let a
  handful of large Sonoma County producers (historically Gallo) blend across
  Alexander Valley/Dry Creek Valley/Knights Valley/Chalk Hill/Russian River
  Valley without an overlay-designation problem, per the brief's Cape Coast
  guidance — giving it children would double-count every wine from those
  five AVAs.

## Label string → canonical (real-world forms)

| Label string | Kind | Canonical | Where seen |
|---|---|---|---|
| "RRV" | region | Russian River Valley | common trade abbreviation, e.g. wine-searcher.com and retailer shorthand for Russian River Valley |
| "Santa Rita Hills" | region | Sta. Rita Hills | existing library synonym, confirmed on many retailer pages (the winery-preferred "Sta. Rita Hills" form avoids a trademark conflict with a Chilean producer) |
| "Paso" | region | Paso Robles | existing library synonym; ubiquitous shorthand in trade coverage |
| "SLO Coast" | region | San Luis Obispo Coast | `https://en.wikipedia.org/wiki/San_Luis_Obispo_Coast_AVA` ("Other names: SLO Coast") |
| "Willow Creek District" | region | Paso Robles Willow Creek District | `https://en.wikipedia.org/wiki/Paso_Robles_AVA` (short form used throughout, e.g. Saxum's James Berry Vineyard listing) |
| "Mt. Veeder" | region | Mount Veeder | `https://en.wikipedia.org/wiki/Napa_Valley_AVA` infobox spells the sub-region "Mt. Veeder AVA" |
| "Stag's Leap District" | region | Stags Leap District | existing library synonym (apostrophe variant seen on older labels) |
| "Carneros" | region | Los Carneros | existing library synonym; near-universal shorthand on labels |
| "Fort Ross Seaview" (no hyphen) | region | Fort Ross-Seaview | common retailer typo/simplification of the official hyphenated name |
| "Shenandoah Valley, Amador County" | region | California Shenandoah Valley | disambiguated form used by producers to distinguish from Virginia's Shenandoah Valley |
| "El Dorado County" | region | El Dorado | existing library synonym |
| "Monterey AVA" | region | Monterey | `https://en.wikipedia.org/wiki/Monterey_AVA` |
| "SF Bay" | region | San Francisco Bay | informal trade shorthand seen on retailer category pages |
| "Oak Knoll District" | region | Oak Knoll District of Napa Valley | `https://en.wikipedia.org/wiki/Napa_Valley_AVA` — commonly shortened on labels (e.g. Trefethen) |
| "Moon Mountain District" | region | Moon Mountain District Sonoma County | shortened form used on most producer labels (e.g. Moon Mountain Vineyard Estate) |
| "Estrella District" | region | Paso Robles Estrella District | `https://en.wikipedia.org/wiki/Paso_Robles_AVA` reference citations (Taranto, "Estrella District") |
| "Green Valley, Russian River" | region | Green Valley of Russian River Valley | common retailer disambiguation from Solano County's Green Valley |
| "Napa Gamay" | grape | Valdiguié | historic California varietal name; DNA-identified as Valdiguié, not true Gamay — `https://en.wikipedia.org/wiki/Valdigui%C3%A9` |
| "Gray Riesling" | grape | Trousseau Gris | `https://en.wikipedia.org/wiki/Trousseau_(grape)`; historic California name for this grey-berry Trousseau mutation, still on some Livermore Valley/Central Coast labels |
| "Gamay Beaujolais" | grape | Pinot Noir | `https://en.wikipedia.org/wiki/Gamay_Beaujolais`; DNA-confirmed to be a Pinot Noir clone, not Gamay — used on California labels for decades before the name was retired |
| "Charbono" | grape | Bonarda | existing library synonym; confirmed still on active California labels (e.g. Tofanelli, Turley) |
| "Mission" | grape | País | existing library synonym; historic California mission-grape name |
| "Tinta Cao" | grape | Tinto Cão | `https://en.wikipedia.org/wiki/Monterey_AVA` and `https://en.wikipedia.org/wiki/Lodi_AVA` grape lists both spell it this way (vs. the Portuguese "Tinto Cão") |
| "Souzao" | grape | Vinhão | `https://en.wikipedia.org/wiki/Lodi_AVA` grape list; California port-style producers' (Ficklin, Quady) standard spelling of Sousão |
| "Rubired" | grape | Rubired | `https://en.wikipedia.org/wiki/Lodi_AVA`; UC Davis teinturier crossing grown almost exclusively in the Central Valley for color/blending, occasionally varietally labeled |

## Validation

```
$ .venv/bin/python -c "import yaml; [print(f, len(yaml.safe_load(open(f)))) for f in ['fermentation/library_mcp/seed/research/us-ca.regions.yaml','fermentation/library_mcp/seed/research/us-ca.grapes.yaml']]"
fermentation/library_mcp/seed/research/us-ca.regions.yaml 165
fermentation/library_mcp/seed/research/us-ca.grapes.yaml 6
```

Also checked by script (not part of the required command):
- No duplicate `(name)` within `us-ca.regions.yaml`; no dangling `parent`
  references (every parent is either in this file or an existing US entry in
  the base `regions.yaml`); no parent cycles.
- Every "label collision" the script found is a *stale synonym still sitting
  in the current, unedited base `regions.yaml`* that this file's corresponding
  new/promoted entry is meant to replace at merge time (the 8 entries listed
  under "Changes to existing entries" above: Green Valley of Russian River
  Valley, Fort Ross-Seaview, West Sonoma Coast, Mendocino, Clear Lake,
  California Shenandoah Valley, Fiddletown, Monterey, San Luis Obispo Coast,
  Adelaida District, Paso Robles Willow Creek District). The merge step needs
  to strip those synonyms from the base allowlist's Monterey County,
  Mendocino County, Lake County, Amador County, San Luis Obispo County,
  Sonoma Coast and Paso Robles entries when it adds this file's replacements.
- `us-ca.grapes.yaml`'s three `existing: true` entries (Pinot Noir, Tinto
  Cão, Vinhão) all match a canonical name already in `grapes.yaml`, and none
  of the new synonyms (Napa Gamay, Gamay Beaujolais, Tinta Cao, Souzao, Gray
  Riesling/Grey Riesling) collide with any existing grape name or synonym.

## Review (main session, 2026-09-26)

- **Dropped `Gamay Beaujolais` as a Pinot Noir synonym.** It is a
  historical California label term, but it embeds a place name, and
  `lookup_grape("Gamay Beaujolais")` on a Beaujolais snippet would return
  Pinot Noir.
- **Kept the informal Central Valley tier** and the official name
  `California Shenandoah Valley`. The bare "Shenandoah Valley" goes to the
  Virginia/West Virginia AVA (us-rest), since region labels must be
  unique within a country.
