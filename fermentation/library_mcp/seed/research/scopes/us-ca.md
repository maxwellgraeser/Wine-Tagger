# us-ca: California

**Country:** US. **Slice:** California. The US is split across three agents
(us-ca, us-pnw, us-rest).

**You own:** the existing `California` entry and everything under it in
`regions.yaml`. You also own every AVA that lies wholly within California,
nested properly. For example:
- California > North Coast > Sonoma County > Russian River Valley > Green
  Valley of Russian River Valley
- Napa Valley > Oakville / Rutherford / Stags Leap District / ...
- Central Coast > Paso Robles > its 11 sub-AVAs, such as Adelaida District
  and Willow Creek District. Today these are wrongly folded into Paso
  Robles' synonyms.
- Lodi and its 7 sub-AVAs; Sierra Foothills; South Coast; and so on.

Include the county appellations that labels use as regions (Sonoma County,
Mendocino County, Santa Barbara County...). Follow the existing US
convention in `regions.yaml` for `classification`: AVAs get
`classification: AVA`; counties and states follow what the existing
entries do.

**Not yours:** Oregon, Washington, Idaho (us-pnw) and every other state
(us-rest).

**Official register:** TTB's list of established AVAs (ttb.gov) and 27 CFR
part 9 (ecfr.gov). Count California AVAs against it. Many AVAs overlap
(Sonoma Coast vs Russian River Valley; Central Coast vs San Francisco Bay).
Pick one parent per the brief and record the overlaps in the `.md`.

**`grapes:` field:** none. AVAs have no grape rules.

**Grapes file:** California-relevant grapes or names missing from
`grapes.yaml`. Check Mission / Listán Prieto, Charbono, and any US-specific
synonyms of existing grapes. Keep it short; most California grapes are
already there.

This slice is large, well over 100 AVAs. A complete AVA list and real-world
synonyms ("Russian River", "RRV", "Sta. Rita Hills" / "Santa Rita Hills",
"Paso") matter more than prose.
