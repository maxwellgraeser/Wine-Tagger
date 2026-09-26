# South Africa (ZA) — ground-truth research notes

## Sources

- **SAWIS, "Production Areas Defined in Terms of the Wine of Origin Scheme," June 2024** — the primary authority for the whole hierarchy in `za.regions.yaml`. `https://www.sawis.co.za/cert/download/Production_areas_-_June_2024.pdf`. This is SAWIS's own current production-area table (Overarching Region / Region / Subregion / District / Ward columns), and it is materially newer than the two secondary sources below (it includes the Cape Town district, Ceres Plateau, Prince Albert, Central Orange River as a district, Lower Duivenhoks River, Swellendam, and about a dozen wards proclaimed since ~2017 that neither secondary source has).
- **Wines of South Africa (WOSA), Wine of Origin scheme page** — `https://www.wosa.co.za/The-Industry/Wines-Of-Origin/Wine-Of-Origin-Scheme/` — used to corroborate the tier definitions and the Cape Coast/Cape West Coast overarching designations.
- **Wikipedia, "Wine regions of South Africa"** — `https://en.wikipedia.org/wiki/Wine_regions_of_South_Africa` — used only for cross-checking; its table predates the 2024 SAWIS update (no Cape Town district, still shows Lutzville Valley under Olifants River, is missing ~30 wards) and was not treated as authoritative where it conflicted with SAWIS.
- Winepaths, `https://www.winepaths.com/articles/editorial/south-africa/cape-town-s-new-wine-of-origin-region` — Cape Town district proclaimed June 2017, wards Constantia/Durbanville/Philadelphia/Hout Bay.
- Decanter regional profile, `https://www.decanter.com/premium/regional-profile-cape-west-coast-487766/` — confirms "Cape West Coast" and "Cape Coast(al)" as real trade-used overarching/subregion labels, not just table headers.
- Grape identity/synonym sources: southafrica.co.za grape pages (Cape Riesling, Colombar, Nouvelle, Roobernet, Muscadel), Wikipedia (Chenel, Weldra, Bukettraube), Stellenbosch Vineyards (Therona), Decanter (Cinsault/Hermitage), winemag.co.za Tim James column (Sémillon/Groendruif), wineanorak.com (Palomino/Fransdruif), wine-searcher.com (Crouchen/Cape Riesling VIVC identity).

## Counts

| Level | Official (SAWIS June 2024) | Produced |
|---|---|---|
| Geographical Unit | 7 (Western Cape, Northern Cape, Eastern Cape, KwaZulu-Natal, Free State, Limpopo, North West) | 7 |
| Region (incl. overarching/subregion) | Cape Coast, Cape South Coast, Coastal Region, Cape West Coast, Breede River Valley, Klein Karoo, Olifants River, Karoo-Hoogland = 8 | 8 |
| District | 30 named districts in the source table | 30 |
| Ward | 96 named wards in the source table (incl. wards with no district, sitting directly under a region or GU) | 96 |
| **Total** | | **145** |

**Left out, and why:**
- **Boberg** — a Region-level WO designation historically covering fortified wines from Paarl, Franschhoek, Tulbagh (and Wellington). Confirmed **repealed in 2019** (still visible on older Muscadel bottles, e.g. vintage KWV "WO Boberg Superior"). Not in the current SAWIS list; left out as no longer valid. If the merge wants historical/legacy names supported, this would need a deliberate decision, not a silent add.
- **Lanseria** — the SAWIS table lists one ward, "Lanseria," under a literal "GEOGRAPHICAL UNIT: NONE" heading — i.e. even SAWIS's own document does not attach it to any of the seven GUs. It's a tiny, non-Western-Cape vineyard near Johannesburg. Since our schema wants every ward parented to "its region or GU" and there is no GU to parent it to in the source itself, I left it out rather than guess. Flagged here for a human call.

## Changes to existing entries

1. **`Franschhoek`: reclassified Ward → District, re-parented `Paarl` → `Coastal Region`.** Both the 2024 SAWIS table and the older Wikipedia table list "Franschhoek / Franschhoek Valley" as its own district directly under Coastal Region, a sibling of Paarl — not a ward inside Paarl. Kept the "Franschhoek Valley" synonym (genuinely used on labels).
2. **`Wellington`: re-parented `Paarl` → `Coastal Region`.** Same correction: Wellington is a district in its own right under Coastal Region, not a sub-district of Paarl. It also now has five wards of its own (Blouvlei, Bovlei, Groenberg, Limietberg, Mid-Berg River) which only make sense once it's not nested under Paarl.
3. **`Stellenbosch`: dropped the synonym `"Simonsberg-Stellenbosch"`, added it as its own child ward** (`parent: Stellenbosch`, `classification: Ward`). This was exactly the bug pattern described in the brief — a sub-appellation had been folded into its parent's synonym list instead of being its own entry. Same fix applied to **`Constantia`**, which is not a sub-ward issue but see #4.
4. **`Constantia` and `Durbanville`: re-parented `Coastal Region` → `Cape Town`.** Both wards were absorbed into the new Cape Town district (proclaimed June 2017, per WinePaths) along with Hout Bay and Philadelphia. The pre-2017 parent (Coastal Region directly) is stale.
5. **`Hemel-en-Aarde` renamed to `Hemel-en-Aarde Valley`** (`was: "Hemel-en-Aarde"`), synonyms `["Hemel-en-Aarde", "Hemel en Aarde"]`. The broader valley was originally a single ward; it has since been split into three sibling wards — Hemel-en-Aarde Ridge, Hemel-en-Aarde Valley, and Upper Hemel-en-Aarde Valley — all under Walker Bay. "Hemel-en-Aarde Valley" is now the official name of one specific ward, not just a loose synonym for the district, so I promoted it to canonical and kept the bare "Hemel-en-Aarde" as a synonym since that's still how most people write it.
6. **Dropped all `"X WO"`-style synonyms** on Stellenbosch, Paarl, Robertson, Constantia (`"Stellenbosch WO"`, `"Paarl WO"`, `"Robertson WO"`, `"Constantia WO"`) per the instruction that the code strips classification suffixes before lookup.
7. **`Robertson`: added `"Robertson Valley"` and `"Robertson Wine Valley"`** as synonyms — this is the exact failure case named in the brief.
8. Every other existing entry (Western Cape, Coastal Region, Paarl, Swartland, Darling, Tulbagh, Breede River Valley, Breedekloof, Worcester, Cape South Coast, Walker Bay, Elgin, Overberg, Klein Karoo, Olifants River, Cape Town, Northern Cape) is unchanged in name/parent/classification; each gained child districts/wards it was previously missing.

## Homonyms (ZA name also used for a wine region elsewhere)

- **Wellington** — "Wellington" is used loosely for parts of New Zealand's wine country (Wairarapa/Martinborough area is sometimes marketed under the Wellington regional name), though the formal NZ GI is Wairarapa, not Wellington. Worth a cross-country disambiguation check when NZ is researched.
- **Napier** — Napier, New Zealand is a well-known town/wine-trade reference point for Hawke's Bay. ZA's Napier is an unrelated small ward in Cape South Coast.
- **Darling** — "Darling Downs" is a real, if minor, wine region in Queensland, Australia. Not an exact-string collision with ZA's "Darling" district, but close enough to flag.
- **Constantia** — no other-country wine-region collision found.
- **Durbanville, Elgin, Ceres, Worcester** — checked; no conflicting wine-region usage found for these exact strings in other countries (Elgin, Scotland is whisky, not wine; Worcester, England/Massachusetts have no formal wine appellation by that name).
- Ran a grep of every new/changed ZA name and synonym against the full existing multi-country `regions.yaml` — no exact-string collisions found (see validation below), so nothing was blocked at this stage; the above are "watch for later" items rather than confirmed current conflicts.

## Uncertain calls

- **"Cape Coast" and "Cape West Coast"** are real trade-used labels (confirmed via Decanter's regional profile and WOSA's own description of "Cape Coastal" as a maritime-climate blending designation), but they sit awkwardly in a 4-tier GU/Region/District/Ward model: SAWIS's own table treats "Cape Coast" as an *overarching region* one level above Region, and "Cape West Coast" as a *subregion* one level below Region and above District. I modeled both as `classification: Region` (Cape Coast under Western Cape; Cape West Coast under Coastal Region) since that's the closest fit the schema allows. Flag for review — a human may prefer a different placement.
- **Darling and Swartland's "Cape West Coast" tag**: per the SAWIS table, Darling district and Swartland's St Helena Bay ward are also tagged with the Cape West Coast subregion, but each already had a perfectly good more-specific parent (Coastal Region and Swartland district respectively) in the existing/new hierarchy. I left their parents as-is rather than re-parenting them under "Cape West Coast" too, to avoid a wine losing its more specific district on lookup. Only the units that had **no other district** (Lutzville Valley, Bamboes Bay, Lamberts Bay) were parented to Cape West Coast.
- **"Elandskloof/Kaaimansgat"**: SAWIS's table lists this as a single compound ward name. I used "Elandskloof" as canonical with "Kaaimansgat" as a synonym; I could not confirm from a second source which name is more commonly used on labels.
- **Ceres Plateau / Prince Albert / Nieuwoudtville / Cederberg / Leipoldtville-Sandveld**: SAWIS's table lists these with an explicit "Region: None," i.e. they sit directly under the Western Cape GU with no intervening Region — unusual compared to everything else in the Western Cape, which is nested one region deeper. I followed the source as given rather than guessing a region for them.
- **Muscadel identity**: confirmed "Muscadel" (and "Red Muscadel" / "White Muscadel," both common on SA dessert-wine labels, e.g. Robertson Winery, Van Loveren) map to Muscat Blanc à Petits Grains, with the red styles being a colour mutation of the same VIVC variety rather than a separate grape. I did not independently verify this against the VIVC database itself (only secondary sources); flag for a VIVC cross-check. Note this name is easy to confuse with the already-canonical, unrelated Bordeaux grape **Muscadelle** — the strings don't collide in the allowlist, but a human reviewer should know they're different grapes with very similar names.
- **"Hermitage" as a Cinsault synonym**: historically accurate (Cinsault was called Hermitage at the Cape from the 1850s until ampelographers correctly identified it in the 20th century, and it's the "Hermitage" in Pinotage = Pinot + Hermitage). But "Hermitage" is also the name of a French Rhône AOC already in `regions.yaml` (different file/namespace, so no schema collision), and on a modern label "Hermitage" overwhelmingly means the French appellation, not Cinsault. This synonym is essentially dead outside historical-label contexts (pre-1990s Cape wine); flag for a judgment call on whether it's worth the ambiguity risk.
- **"Weisser Riesling" / "Rhine Riesling"** added to the existing `Riesling` entry as SA-specific legacy qualifiers used to distinguish true Riesling from Cape Riesling before 2010 legislation reserved the bare name "Riesling" for the true variety. These qualifiers are now declining in use per southafrica.co.za, so may be lower-value synonyms than the others added here.

## Label string → canonical (20–25 pairs, real-world forms)

| Label string | Kind | Canonical | Where seen |
|---|---|---|---|
| "Robertson Valley" | region | Robertson | `https://www.wine-searcher.com/regions-robertson` (regional description) |
| "W.O. Stellenbosch" | region | Stellenbosch | `https://thewinestore.co.za/product-category/regions/stellenbosch/` |
| "Stellenbosch WO" | region | Stellenbosch | `https://www.nprwineclub.org/wines/chenin-blanc/stellenbosch-wo/_/N-1z14067Z1z13wws` |
| "Franschhoek Valley" | region | Franschhoek | existing library synonym, corroborated by Wikipedia district listing |
| "Constantia Valley" | region | Constantia | existing library synonym |
| "Hemel-en-Aarde Valley" | region | Hemel-en-Aarde Valley | `https://www.wine-searcher.com/regions-hemel-en-aarde+valley` |
| "Upper Hemel-en-Aarde Valley" | region | Upper Hemel-en-Aarde Valley | `https://www.wine-searcher.com/regions-upper+hemel-en-aarde+valley` |
| "Perdeberg" | region | Paardeberg | `https://perdeberg.co.za/` (winery named for the ward, modern Afrikaans spelling) |
| "Klein Rivier" | region | Klein River | older Afrikaans spelling of the Overberg ward |
| "Little Karoo" | region | Klein Karoo | existing library synonym |
| "North-West Province" | region | North West | SAWIS table heading vs. common English form |
| "Steen" | grape | Chenin Blanc | `https://www.empirewine.com/wine/man-family-vintners-steen-chenin-blanc-2025-h22193/` |
| "Hoe-Steen" | grape | Chenin Blanc | `https://www.skurnik.com/sku/chenin-blanc-hoe-steen-david-nadia-sadie-3-2-2/` (compound label, "Steen" is the grape half) |
| "Hanepoot" | grape | Muscat of Alexandria | existing library synonym |
| "Cape Riesling" | grape | Crouchen Blanc | `https://www.wine-searcher.com/grape-122-crouchen-cape-riesling` |
| "South African Riesling" | grape | Crouchen Blanc | `https://www.wine-searcher.com/grape-122-crouchen-cape-riesling` |
| "Colombar" | grape | Colombard | `https://southafrica.co.za/colombar.html` |
| "Red Muscadel" | grape | Muscat Blanc à Petits Grains | southafrica.co.za Muscadel page; common on dessert-wine labels (Robertson Winery, Van Loveren) |
| "Fransdruif" | grape | Palomino | `https://wineanorak.com/2021/09/12/an-ode-to-palomino-still-wines-made-from-old-vine-palomino-offer-a-new-narrative-for-this-neutral-industrialised-yet-historic-grape-variety/` |
| "Groendruif" | grape | Sémillon | `https://winemag.co.za/wine/opinion/tim-james-history-of-grape-varieties-in-the-cape/` |
| "Cinsaut" | grape | Cinsault | existing library synonym |
| "Hermitage" (pre-1990s Cape usage) | grape | Cinsault | `https://www.decanter.com/premium/cinsault-south-africas-new-star-from-old-vines-457581/` |
| "Weisser Riesling" | grape | Riesling | `https://southafrica.co.za/weisser-riesling.html` |
| "Shiraz" | grape | Syrah | existing library synonym (used throughout SA labeling, e.g. Robertson Winery Shiraz) |
| "Bukettrebe" | grape | Bukettraube | `https://vivc.de/index.php?amp=&id=1611&r=passport%2Fview` |

## Validation

```
$ .venv/bin/python -c "import yaml; [print(f, len(yaml.safe_load(open(f)))) for f in ['fermentation/library_mcp/seed/research/za.regions.yaml','fermentation/library_mcp/seed/research/za.grapes.yaml']]"
fermentation/library_mcp/seed/research/za.regions.yaml 145
fermentation/library_mcp/seed/research/za.grapes.yaml 13
```

Also checked by hand (not part of the required command, but worth recording): no duplicate names, no dangling/cyclical parents, no name/synonym collisions within `za.regions.yaml`, and no synonym collisions between `za.grapes.yaml` and the full canonical `grapes.yaml`.

## Review (main session, 2026-09-26)

Checked the hierarchy against the SAWIS June 2024 PDF directly. All
placements match, including Lutzville Valley (Coastal Region, Cape West
Coast subregion) and the Northern Cape rows under Karoo-Hoogland.

Changes made before the merge:
- **Dropped `Hermitage` as a Cinsault synonym.** On a modern page,
  "Hermitage" means the Rhône AOC. As a grape synonym it would make every
  Hermitage snippet count as Cinsault evidence in `evidence.py`, and a
  `lookup_grape("Hermitage")` on a Rhône wine would return Cinsault.
- **Moved Darling under Cape West Coast**, where SAWIS puts it (Coastal
  Region > Cape West Coast > Darling). Its chain still includes Coastal
  Region. St Helena Bay stays under Swartland: it can have only one parent,
  and the district is the more specific of the two.
- **Kept `Perdeberg` for Paardeberg.** The ward's official name is
  "Paardeberg/Perdeberg".
- **Kept Cape Coast without children**, as the agent did. Parenting Coastal
  Region under it would add "Cape Coast" to the region list of every
  Stellenbosch or Swartland wine.
- **Dropped Nouvelle from the merged allowlist.** Wikidata has no grape
  item for it, and the build requires a QID for every canonical grape. It
  stays in `za.grapes.yaml` as the record. To restore it, pin a `qid:` if
  Wikidata ever gets an item, or relax the QID rule.
