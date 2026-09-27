Status: complete

# Chile research notes

## Sources
- SAG, Decreto N° 464 "Zonificación Vitícola y Denominación de Origen" (as amended, text incorporating Decreto 56 and later amendments), https://www.sag.gob.cl/sites/default/files/decreto_ndeg_464.pdf — downloaded 2026-09-27, used for the full Region/Subregión/Zona/Área table (Art. 1), Secano Interior (Art. 3° bis) and Costa/Entre Cordilleras/Andes (Art. 5° bis).
- WIPO Lex consolidated text of Decreto 464 (as amended to Decreto 56), https://www.wipo.int/wipolex/en/legislation/details/18886 — cross-check.
- reporteagricola.cl / wip.cl on the 2026 Secano Interior expansion (Biobío comunas), for currency of the special DO.
- VIVC (vivc.de) passport pages for Pedro Ximénez (9080) and Torontel (15465), for grape identity.
- Wine-Searcher, Wine Enthusiast, WineWithSeth, Wines of Chile (winesofchile.org) for retail-facing area names and informal terms (Alto Maipo, Guarilihue, Panquehue, San Javier).

## Counts

Official Decreto 464 (Art. 1 table): 6 regions, 15 subregions, 8 zones, ~55 areas
(comuna-level), plus the special DO Secano Interior (Art. 3° bis, now 18 comuna/area
divisions after the 2026 Biobío expansion) and the 3 Costa/Entre Cordilleras/Andes
overlay terms (Art. 5° bis).

Produced: 61 region entries total (18 pre-existing kept, 43 new): 6 regions, 15
subregions, 8 zones (Cachapoal, Colchagua, Teno, Lontué, Claro, Loncomilla, Tutuvén,
Leyda), 26 areas, 1 informal locality (Guarilihue), 1 informal sub-area (Alto Maipo),
1 overlay DO (Secano Interior).

**Left out on purpose** (official but not on export labels, per scope's "aim 25-40,
prefer export labels"): most administrative-comuna areas of Atacama, Coquimbo,
Aconcagua Valley (beyond Panquehue), Maipo (Santiago, Melipilla, Alhué, María Pinto,
Colina, Calera de Tango, Til Til, Lampa), Cachapoal (Rancagua, Machalí, Coltauco),
Teno (Rauco, Romeral, Vichuquén), Claro (Talca, Pencahue, San Clemente, San Rafael,
Empedrado, Curepto), Loncomilla (Villa Alegre, Parral, Linares, Colbún, Longaví,
Retiro), Bío-Bío Valley's areas (Yumbel, Mulchén). These are legal DO areas but rarely
appear on retail labels; happy to add specific ones if the tagger later sees them.
Costa/Entre Cordilleras/Andes (Art. 5° bis) are qualifiers layered on an existing area,
not regions, per the scope note — not added as entries.

## Changes to existing entries

- **Aconcagua**: dropped synonyms "Aconcagua Valley" and "Valle de Aconcagua" — these
  belong to the narrower Subregión Valle del Aconcagua (Panquehue/San Felipe/Los
  Andes/Quillota), which excludes Casablanca and San Antonio. Added a separate
  "Aconcagua Valley" entry (new) as its child so the two levels don't collide.
- **Maipo Valley**: dropped "Alto Maipo" from its synonyms and gave it its own entry
  as a child area — it names the Puente Alto/Pirque cluster specifically (a
  sub-appellation-like trade term), not the whole Maipo Valley; folding it in was the
  "sub-appellation as synonym" mistake pattern.
- **Central Valley, Rapel Valley, Colchagua Valley, Curicó Valley, Maule Valley,
  Cachapoal Valley, Casablanca Valley, San Antonio Valley, Leyda Valley, Coquimbo,
  Limarí Valley, Elqui Valley, Choapa Valley, Southern Chile, Itata Valley, Bío-Bío
  Valley, Malleco Valley**: kept as-is (added `source`).

## Homonyms

- Central Valley: Chile and USA (California).
- Patagonia: Chile and Argentina (not in this scope's list but flagged per the brief).

## Uncertain calls

- **Zapallar / Marga-Marga**: the decree's Art. 1 prose lists these as an "Área" of
  Región Aconcagua, at the same level as the three named subregions (Valle del
  Aconcagua, Casablanca, San Antonio) — i.e. directly under the region, not nested in
  a subregion. The Art. 1 summary table places them inconsistently (once under no
  subregion, once seemingly under Valle del Aconcagua's area list). I parented both
  directly under "Aconcagua" (the region), matching the prose, not the table.
- **Pedro Jiménez**: scope note called it "a different variety from Pedro Ximénez:
  check VIVC." VIVC's Pedro Ximenez passport (9080) itself lists "PEDRO JIMENEZ" as a
  synonym (distinct from "PEDRO GIMENEZ", VIVC 24977, Argentina's separate criolla,
  already excluded per scope). Multiple secondary sources (wein.plus, Peñín) agree
  Chile's "Pedro Jiménez" name refers to true Pedro Ximénez. Treated it as a synonym of
  the existing Pedro Ximénez entry rather than a new grape; flagging in case the
  merge step's VIVC resolution disagrees.
- **Guarilihue**: an informal locality inside the Quillón comuna (Itata Valley), not a
  decree-listed area, but used on real labels/pisco-adjacent listings. Kept it as an
  informal area entry per the "trade relies on" rule; source is a single retailer
  listing, weaker than the rest.

## Label string -> canonical

| label string | kind | canonical | where seen |
|---|---|---|---|
| Valle del Maipo | region | Maipo Valley | https://www.sag.gob.cl/sites/default/files/decreto_ndeg_464.pdf |
| Alto Maipo | region | Alto Maipo | https://www.winewithseth.com/winewiki/maipo-sub-zones-alto-maipo-central-maipo-maipo-costa/ |
| Valle de Colchagua | region | Colchagua Valley | https://www.sag.gob.cl/sites/default/files/decreto_ndeg_464.pdf |
| Apalta, Colchagua | region | Apalta | https://www.wine-searcher.com/regions-apalta |
| Valle del Cachapoal | region | Cachapoal Valley | https://www.sag.gob.cl/sites/default/files/decreto_ndeg_464.pdf |
| Requinoa | region | Requínoa | https://www.sag.gob.cl/sites/default/files/decreto_ndeg_464.pdf |
| Valle de Casablanca | region | Casablanca Valley | https://www.sag.gob.cl/sites/default/files/decreto_ndeg_464.pdf |
| San Antonio Valley | region | San Antonio Valley | https://www.wine-searcher.com/regions-san+antonio+valley |
| Leyda | region | Leyda Valley | https://www.wine-searcher.com/regions-leyda |
| Valle de Aconcagua | region | Aconcagua Valley | https://www.sag.gob.cl/sites/default/files/decreto_ndeg_464.pdf |
| Panquehue | region | Panquehue | https://www.wine-searcher.com/regions-panquehue |
| Marga Marga | region | Marga-Marga | https://www.sag.gob.cl/sites/default/files/decreto_ndeg_464.pdf |
| Curico | region | Curicó Valley | https://www.wine-searcher.com/regions-curico+valley |
| Valle del Lontué | region | Lontué Valley | https://www.sag.gob.cl/sites/default/files/decreto_ndeg_464.pdf |
| Sagrada Familia, Curicó | region | Sagrada Familia | https://www.sag.gob.cl/sites/default/files/decreto_ndeg_464.pdf |
| Valle del Maule | region | Maule Valley | https://www.sag.gob.cl/sites/default/files/decreto_ndeg_464.pdf |
| San Javier, Maule | region | San Javier | https://www.sag.gob.cl/sites/default/files/decreto_ndeg_464.pdf |
| Cauquenes | region | Cauquenes | https://www.sag.gob.cl/sites/default/files/decreto_ndeg_464.pdf |
| Valle del Itata | region | Itata Valley | https://www.sag.gob.cl/sites/default/files/decreto_ndeg_464.pdf |
| Quillon | region | Quillón | https://www.sag.gob.cl/sites/default/files/decreto_ndeg_464.pdf |
| Bio Bio | region | Bío-Bío Valley | https://en.wikipedia.org/wiki/Chilean_wine |
| Secano Interior | region | Secano Interior | https://www.sag.gob.cl/sites/default/files/decreto_ndeg_464.pdf |
| Valle del Elqui | region | Elqui Valley | https://www.sag.gob.cl/sites/default/files/decreto_ndeg_464.pdf |
| Limari | region | Limarí Valley | https://www.wine-searcher.com/regions-limari+valley |
| Carmenere | grape | Carménère | https://en.wikipedia.org/wiki/Carm%C3%A9n%C3%A8re |
| Pais | grape | País | https://en.wikipedia.org/wiki/Pa%C3%ADs_(grape) |
| Pedro Jimenez | grape | Pedro Ximénez | https://www.sherrynotes.com/2022/background/pedro-ximenez-grape-history-characteristics/ |
| Torontel | grape | Torontel | https://vivc.de/index.php?id=15465&r=passport%2Fview |
| Moscatel de Alejandría | grape | Muscat of Alexandria | https://guiapenin.wine/en-pedro-ximenez |

## Checker

`.venv/bin/python -m fermentation.library_mcp.seed.research.check cl` reports 0 errors,
1 warning: "Central Valley: 'Central Valley (Chile)' has a classification word or (…)
tail the lookup already strips." This synonym pre-dates this run (it was already in
regions.yaml); left it in place since it does no harm (lookup strips the parenthetical)
but flagging per the brief's instruction to explain remaining warnings.

## Review (main session, 2026-09-27)
- **Dropped "Pedro Jiménez" as a Pedro Ximénez synonym.** Chile's Pedro Jiménez (Elqui/Limarí, pisco and white wine) is reported by DNA work to be a different variety from Spanish PX, related to Argentina's Pedro Giménez (a Muscat of Alexandria × Criolla Chica cross). VIVC listing the spelling under PX reflects the Spanish usage. An unknown grape beats a wrong one. Reconciliation: make it a synonym of Pedro Giménez if ar adds that grape.
- Hierarchy reviewed with `check --tree`: Aconcagua / Aconcagua Valley split, Alto Maipo as its own entry, Atacama and Austral additions and the Secano Interior overlay all accepted.

**Merge note (2026-09-27):** Chile and Argentina merged together (cl + ar). Dropped for lack of an own Wikidata grape item: Torontel (cl), Moscatel Rosado, Torrontés Mendocino (ar), and Torrontés Sanjuanino (its only QID was Torrontés itself). Lock nulled as homonyms: Buenos Aires (AR, the city), Entre Ríos (AR, a Brazilian municipality), La Pampa (AR, a place in Córdoba), Santa Cruz (CL, Philippines), San Javier (CL, Murcia), Portezuelo (CL, Cáceres). Added "Valle de Tulum" to Tulum Valley. Replay: bare "La Rioja" (no country; a Faustino query) now resolves to the Argentine province, with Spain's Rioja listed as the alternative; with country ES it still gives Rioja. 630 tests.
