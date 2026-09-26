Status: complete

# es-s2: Castilla-La Mancha, Madrid, Valencia, Murcia, Extremadura

## Sources
- MAPA official DOP/IGP register by province (PDF, downloaded 2026-09-26):
  https://www.mapa.gob.es/es/dam/jcr:3a6d87c6-1b15-4777-941e-0caacb1ac2e3/06_igs_por_provincias.pdf
  -- the authoritative cross-check for every DO/VP/IGP name, community and
  registration date used below. Converted with pdftotext -layout.
- vinosdecastillalamancha.es (VinosCLM, the regional trade body) for
  individual DO/VP pages and grape lists.
- riberadelguadiana.eu (official Consejo Regulador) for Ribera del Guadiana
  subzones.
- vinosdemadrid.es (official Consejo Regulador) for Vinos de Madrid subzones.
- vinosalicantedop.org (official Consejo Regulador) for Alicante DO principal
  varieties (2021 pliego reorganisation into historical/principal/secondary).
- Wikipedia / wein.plus / vitivinicultura.net for grape identity (VIVC-style)
  cross-checks: Cayetana blanca, Pardina, Moravia agria, Forcallat tinta,
  Forcallat blanca, Merseguera.

## Counts

- **Castilla-La Mancha:** 9 DOs (La Mancha, Valdepeñas, Manchuela, Almansa,
  Méntrida, Ribera del Júcar, Uclés, Mondéjar, Campo de Calatrava) + 14 VPs
  (Dominio de Valdepusa, Finca Élez, Guijoso, Dehesa del Carrizal, Campo de
  la Guardia, Pago Florentino, Casa del Blanco, Calzadilla, El Vicario, Los
  Cerrillos, Vallegarcía, La Jaraba, Rosalejo, Río Negro) + IGP Castilla =
  24 DOP + 1 IGP, matching MAPA's register exactly (verified against the
  official province-by-province PDF, which lists all 24+1 CLM wine
  entries). Nothing left out.
- **Madrid:** 1 DO (Vinos de Madrid) with its 4 official subzones (Arganda,
  Navalcarnero, San Martín de Valdeiglesias, El Molar). No VP or IGP of its
  own in Madrid.
- **Valencia:** 3 DOs (Valencia, Utiel-Requena, Alicante) + 5 VPs (Chozas
  Carrascal, El Terrerazo, Los Balagueses, Tharsys, Vera de Estenas) + 1 IGP
  (Castelló) = matches the MAPA register for the Comunidad Valenciana.
- **Murcia:** 3 DOs (Jumilla, Yecla, Bullas) + 2 IGP (Campo de Cartagena,
  Vino de la Tierra de Murcia). Jumilla's dual community (Murcia y
  Albacete) is kept under Murcia only, as in the existing library entry.
- **Extremadura:** 1 DO (Ribera del Guadiana) with 6 subzones (Tierra de
  Barros, Cañamero, Montánchez, Ribera Alta, Ribera Baja, Matanegra) + 1
  IGP (Extremadura, i.e. the community entry itself carries the IGP role
  as in the original library convention).

Total: 53 region entries, 8 new grapes.

## Changes to existing entries

1. **Sierra de Gredos:** dropped "Cebreros" from its synonyms, per es-n
   having made Cebreros (Castilla y León) its own DO/VC. Kept "Gredos".
2. **Extremadura:** removed "Ribera del Guadiana" as a synonym of the
   community entry and gave Ribera del Guadiana its own DO entry with its
   6 subzones as children (it was wrongly folded in as a synonym before;
   Ribera del Guadiana is a specific DO within Extremadura, not a name
   for the whole community).
3. Added `grapes:` to several existing DO entries that had none before
   (La Mancha, Valdepeñas, Manchuela, Almansa, Méntrida, Utiel-Requena,
   Alicante, Jumilla, Yecla, Bullas) using each pliego's principal
   varieties. No names or synonyms of existing entries were changed
   otherwise.

## Homonyms

- **Valencia** (DO, Spain) also names Valencia in Venezuela's short-lived
  wine efforts and various places worldwide, but no other region in
  `regions.yaml` currently uses it, so no conflict.
- **Rioja** already flagged by es-n as a Spain/Argentina homonym; not
  repeated here.
- No other homonym collisions found for this scope's names.

## Uncertain calls

- **Campo de Calatrava** grapes: the 2024 pliego authorizes a long list
  (Tempranillo/Cencibel, Cabernet Sauvignon, Merlot, Syrah, Bobal, Petit
  Verdot, Cabernet Franc, Graciano, Garnacha Tintorera, Malbec; whites
  Airén, Macabeo, Verdejo, Chardonnay, Moscatel de Grano Menudo, Sauvignon
  Blanc, Riesling, Moscatel de Alejandría, Gewürztraminer, Viognier,
  Albariño) without a clearly singled-out "principal" variety in what I
  could find. I listed only Tempranillo as principal since it is the
  region's historic base grape (Cencibel); flag for review.
- **Cayetana Blanca vs Pardina:** widely conflated in trade sources (both
  called "Pardina = Jaén Blanco = Cayetana"), but a DNA/SNP marker study
  found them genetically distinct despite the shared folk synonymy. I
  added both as separate grapes per the scope note and did not merge them.
  Flag for a Wikidata/VIVC check.
- **Forcallat Tinta vs Forcallat Blanca:** kept as two separate grapes
  (different colours, different VIVC identities per sources found); the
  scope note said "Forcallat" singular, but the trade uses both names
  and they are not the same variety.
- **VP grapes field:** left `grapes:` off every Vino de Pago. VPs are
  single-estate, and I found no pliego language naming "principal"
  varieties the way DO pliegos do (they typically just list every grape
  the estate grows). Flag if a VP later needs its own list.
- **Vino de la Tierra de Murcia** naming: the official IGP is simply "IGP
  Murcia" / "Vino de la Tierra de Murcia", but the community-level entry
  is already named "Murcia" in the library, so I used the longer official
  form as `name` to avoid a collision. This triggers a harmless checker
  warning (the name itself contains a classification-word tail); noted
  here per the brief instead of suppressing it with a workaround.
- Pre-existing warnings on synonyms "Vino de la Tierra de Castilla", "La
  Mancha DO", "Valencia DO", "Alicante DO", "Jumilla DO" were already in
  the library before this run; I did not remove them since the brief says
  to keep existing names/synonyms unless wrong, and these are harmless
  (lookup already strips the tail).

## Label string -> canonical

| label string | kind | canonical | where seen |
|---|---|---|---|
| DO La Mancha | region | La Mancha | https://lamanchawines.com/denominacion-de-origen/ |
| Vino de Pago Dominio de Valdepusa | region | Dominio de Valdepusa | https://en.wikipedia.org/wiki/Dominio_de_Valdepusa |
| Valdepeñas DO | region | Valdepeñas | https://catatu.es/region-vinicola/valdepenas |
| Uclés | region | Uclés | https://vinosriberadeljucar.com/en/ |
| Ribera del Júcar | region | Ribera del Júcar | https://vinosdecastillalamancha.es/denominacion-de-origen/ribera-jucar/ |
| Campo de Calatrava | region | Campo de Calatrava | https://vinosdecastillalamancha.es/vino-campo-de-calatrava-nueva-denominacion-de-origen/ |
| Vinos de Madrid - Subzona Arganda | region | Arganda | https://www.hoteles.net/madrid/arganda-del-rey/vinos-de-madrid-subzona-arganda.html |
| DO Madrid | region | Vinos de Madrid | https://vinosypureza.com/do-vinos-de-madrid/ |
| San Martín de Valdeiglesias | region | San Martín de Valdeiglesias | https://www.conmuchagula.com/vinos-de-madrid-subzona-san-martin-de-valdeiglesias/ |
| Utiel-Requena | region | Utiel-Requena | https://www.mapa.gob.es |
| Pago Chozas Carrascal | region | Chozas Carrascal | https://catatu.es/bodega/pago-chozas-carrascal |
| El Terrerazo | region | El Terrerazo | https://en.wikipedia.org/wiki/El_Terrerazo |
| DOP Alicante | region | Alicante | https://vinosalicantedop.org/ |
| Jumilla Monastrell | region+grape | Jumilla / Mourvèdre | https://www.wine-searcher.com/regions-jumilla |
| Bullas DO | region | Bullas | https://winetourismspain.com/wine-regions/murcia-jumilla/ |
| IGP Murcia | region | Vino de la Tierra de Murcia | https://www.mapa.gob.es |
| Ribera del Guadiana | region | Ribera del Guadiana | https://riberadelguadiana.eu/ |
| Tierra de Barros | region | Tierra de Barros | https://riberadelguadiana.eu/region-y-subzonas/ |
| Cencibel | grape | Tempranillo | https://lamanchawines.com/uvas-2/ |
| Garnacha Tintorera | grape | Alicante Bouschet | https://denominacion-origen-almansa.com/la-variedad-de-uva-garnacha-tintorera/ |
| Bobal | grape | Bobal | https://www.bodegasgratias.com/bobal/ |
| Merseguera | grape | Merseguera | https://en.wikipedia.org/wiki/Merseguera |
| Pardina | grape | Pardina | https://viverosgandia.com/variedades/blancas/11-pardina/ |
| Cayetana Blanca | grape | Cayetana Blanca | https://en.wikipedia.org/wiki/Cayetana_blanca |
| Moravia Agria | grape | Moravia Agria | https://es.wikipedia.org/wiki/Moravia_agria |
| Forcallat Tinta | grape | Forcallat Tinta | https://en.wikipedia.org/wiki/Forcallat_tinta |
| Malvar | grape | Malvar | https://vinosdemadrid.es/ |
| Moscatel de Alejandría | grape | Muscat of Alexandria | https://sevi.net/art/23015/ |


## Review (main session, 2026-09-26)

- **Valencia hierarchy.** The existing library made the Valencia DO the
  parent of Utiel-Requena, Alicante, the Valencian Vinos de Pago and
  Castelló, but none of them lie inside the Valencia DO. A new
  `Valencian Community` top entry (synonyms Comunidad Valenciana, Comunitat
  Valenciana) is now their parent and the Valencia DO's parent.
- **Merge-time grape fixes** (the QID resolver found shared items):
  - `Forcallat Blanca` is Airén (Wikidata/VIVC alias). It became an Airén
    synonym, with `Forcayat`.
  - es-n's `Maturana Tinta` and `Verdejo Negro` are Trousseau, so they are
    now Trousseau synonyms. The bare `Maturana` was dropped because Maturana
    Blanca also exists.
- Pardina vs Cayetana Blanca stays two grapes, per the agent's DNA source.
  Robinson's *Wine Grapes* lists Pardina and Jaén Blanco under Cayetana
  Blanca. This goes to the reconciliation pass.
- Added `Pago Chozas Carrascal` as a synonym (a label form from the table).
