Status: complete

# es-s1: Andalucía, Balearics, Canaries

## Sources
- MAPA, "Listado de Denominaciones de Origen Protegidas e Indicaciones Geográficas Protegidas de vinos" (`02_vinos.pdf`, accessed 2026-09-26): official count and names for all three autonomous communities. https://www.mapa.gob.es/es/dam/jcr:f9643333-ef75-4a2f-8864-afd1ade63fd1/02_vinos.pdf
- Pliego de condiciones, DO Condado de Huelva (Junta de Andalucía, consolidated text). https://www.juntadeandalucia.es/export/drupaljda/V_DO_CONDADO_DE_HUELVA.pdf
- Pliego de condiciones, Vino de Calidad de Lebrija (MAPA, 2021-09-14). https://www.mapa.gob.es/dam/mapa/contenido/alimentacion/temas/calidad-agroalimentaria/2017-calidad-diferenciada/nuevo_denominaciones/pliegos-de-condiciones/pliego-condiciones-vinos/dops/lebrija_2021_09_14.pdf
- Pliego de condiciones, DO Málaga (MAPA, 2019-01-01), used for the Málaga/Sierras de Málaga split. https://www.mapa.gob.es/dam/mapa/contenido/alimentacion/temas/calidad-agroalimentaria/2017-calidad-diferenciada/nuevo_denominaciones/pliegos-de-condiciones/pliego-condiciones-vinos/dops/malaga_2019_01_01.pdf
- DO Granada grape rules and Contraviesa-Alpujarra subzone: bodegasmunana.com, alpujarraexperience.com (secondary; no consolidated pliego text found online).
- Canary Islands grape lists per DO: canarywine.com/varieties, ICIA "Variedades de vid cultivadas en Canarias" (PDF), saboreandocanarias.com (El Hierro), gobiernodecanarias.org (per-DO pages), vinoslagomera.com (La Gomera pliego summary).
- Balearics: binissalemdo.com, foodswinesfromspain.com "Mallorca's Native Wine Grapes" (2020), Wikipedia "Pla i Llevant (DO)".
- Grape identity: Gual = Malvasia Fina (Boal/Bual) per fringewine.blogspot.com and wein.plus; Negramoll = Tinta Negra per en.wikipedia.org/wiki/Listán_negro; Vijariego Blanco = Diego per wine-searcher.com.

## Counts
- Andalucía: MAPA lists 8 DOP + 16 IGP = 24. I produced all 24, plus the existing top-level "Andalusia" entry.
- Baleares: MAPA lists 2 DOP + 6 IGP = 8. I produced all 8, plus a new top-level "Balearic Islands" entry (parent for the archipelago, mirroring "Andalusia"/"Canary Islands").
- Canarias: MAPA lists 11 DOP (no IGP tier there) = 11. I produced all 11, plus the existing "Canary Islands" and "Tenerife" entries.
- Nothing official left out.

## Changes to existing entries
- **Jerez → Jerez-Xérès-Sherry**: renamed to the official register name (`was: "Jerez"`); dropped "Manzanilla-Sanlúcar de Barrameda"/"Manzanilla" as synonyms because MAPA registers Manzanilla as its own DO (PDO-ES-A1482) sharing the same Consejo Regulador but a distinct zone (Sanlúcar only) — folding it into Jerez would apply Jerez's whole zone to Manzanilla wines. Added it as a sibling entry instead.
- **Málaga**: dropped "Sierras de Málaga" as a synonym; MAPA registers it as a separate DO (PDO-ES-A1480, dry table wines) vs Málaga's own DOP (PDO-ES-A1481, fortified/sweet). Added Sierras de Málaga as a sibling entry.
- **Mallorca**: previously folded Binissalem, Pla i Llevant, "Balearic Islands" and "Islas Baleares" as synonyms. Split into a hierarchy: new top entry "Balearic Islands" (administrative/informal, mirrors "Andalusia"); "Mallorca" is now the island-wide IGP (Vi de la Terra Mallorca) with Binissalem and Pla i Llevant as DO children and Serra de Tramuntana-Costa Nord as a third IGP child.
- **Canary Islands**: added `classification: VC` — this name/synonym set already matches the archipelago-wide DOP Islas Canarias (PDO-ES-A1511), so no new entry was needed, just the classification.
- **Tenerife**: previously folded Tacoronte-Acentejo, Valle de la Orotava and Ycoden-Daute-Isora as synonyms. Split each into its own DO child, and added the two Tenerife DOs missing from the library (Abona, Valle de Güímar).

## Homonyms
- "La Palma" (DO, Canary Islands) — no other library country entry currently matches, but the name could collide with a place in the Americas (e.g. Panama's La Palma); flagging per BRIEF since it is a common place name.
- "Granada" (DO, Andalucía) also names a city/province; no other wine-region entry in the library currently uses it as a region name.

## Uncertain calls
- **Contraviesa-Alpujarra**: sources describe it as a subzone designation used on some DO Granada labels, not a separate MAPA-registered appellation and not the same thing as the IGP "Laujar-Alpujarra" (different scheme/list). I did not add it as a synonym of either, since it names only part of the DO Granada zone; flagging instead of guessing.
- **Baladí Verdejo, Romé, Doradilla, Zalema, Garrido Fino, Forastera Blanca**: added as new grapes because they are named as principal in their DO's pliego/consejo materials, but I did not find a VIVC page open-access to confirm identity codes; kept them as distinct entries per the "keep new grapes even without a Wikidata/VIVC hit" instruction.
- **Malvasía family**: kept Malvasía Volcánica, Malvasía Aromática and Malvasía Rosada as three separate new entries, distinct from the existing "Malvasía"→"Malvasia Bianca" mapping and from each other, per the BRIEF's Malvasia warning. Did not add a bare "Malvasía" synonym to any of them.
- **Gual = Malvasia Fina**: mainstream wine literature (Wine Grapes, wein.plus) treats Gual as the Canary/Madeira name for Malvasia Fina (Boal/Bual), but one source noted VIVC's own database listed "Gual" as a synonym of Albillo Mayor instead. Went with the literature consensus; flagging the VIVC discrepancy.
- **Baboso Negro**: some Canary sources use "Bastardo Negro" interchangeably with Baboso Negro locally, but "Bastardo" is already the grapes.yaml synonym for Trousseau — a genetically unrelated grape. Did not add "Bastardo Negro" as a synonym of Baboso Negro to avoid that confusion.
- **La Gomera / El Hierro / Gran Canaria DO grape lists**: these three DOs authorize a very wide list (dozens of varieties); I listed only the 2-4 most commonly cited principal/preferred ones per island, not the full authorized list.
- **DOP Islas Canarias ("Canary Islands" entry)**: left `grapes:` off deliberately — its pliego covers the archipelago's ~80 authorized varieties, too broad to call out "principal" ones without misrepresenting the rule.
- **Cross-file, not mine**: the checker reports an existing conflict between es-n's "Cebreros" and "Sierra de Gredos" entries (both claim the label "Cebreros"). This is entirely within es-n's file; not touched here.

## Label string → canonical

| label string | kind | canonical | where seen (URL) |
|---|---|---|---|
| Jerez | region | Jerez-Xérès-Sherry | https://www.sherry.wine/sherry-wine/dry-sherry-wines/manzanilla |
| Manzanilla Sanlúcar de Barrameda | region | Manzanilla-Sanlúcar de Barrameda | https://www.vinerra.com/sub-region/spain-andalucia-manzanilla-sanlucar-de-barrameda-do |
| Montilla-Moriles | region | Montilla-Moriles | https://vinosdo.wine/denominaciones/d-o-malaga-sierras-de-malaga/ |
| Sierras de Málaga | region | Sierras de Málaga | https://vinomalaga.com/en/consejo-regulador/d-o-sierras-de-malaga/ |
| Condado de Huelva | region | Condado de Huelva | https://docondadodehuelva.es/en/our-vineyards/ |
| Vino de Calidad de Lebrija | region | Lebrija | https://catatu.es/region-vinicola/denominacion-origen-lebrija |
| Cádiz (Vino de la Tierra) | region | Cádiz | https://www.mapa.gob.es/es/dam/jcr:f9643333-ef75-4a2f-8864-afd1ade63fd1/02_vinos.pdf |
| Binissalem-Mallorca | region | Binissalem | https://binissalemdo.com/en/wine-in-mallorca/ |
| Pla i Llevant | region | Pla i Llevant | https://en.wikipedia.org/wiki/Pla_i_Llevant_(DO) |
| Vi de la Terra Mallorca | region | Mallorca | https://www.winewithseth.com/winewiki/vi-de-la-terra-mallorca-igp-island-wide/ |
| Eivissa | region | Ibiza | https://www.mallorca.es/en/-/vino-0 |
| Illa de Menorca | region | Menorca | https://www.mapa.gob.es/es/dam/jcr:f9643333-ef75-4a2f-8864-afd1ade63fd1/02_vinos.pdf |
| Tacoronte Acentejo | region | Tacoronte-Acentejo | https://www.winetourism.com/wine-appellation/tacoronte-acentejo/ |
| Valle de Guimar | region | Valle de Güímar | https://en.wikipedia.org/wiki/Valle_de_G%C3%BC%C3%ADmar |
| DO Islas Canarias | region | Canary Islands | https://www.mrvinos.com/denominaciones-origen/35/do-islas-canarias |
| Lanzarote DO | region | Lanzarote | https://dolanzarote.com/en/vinos-de-lanzarote-blancos-de-malvasia/ |
| Vinos La Gomera | region | La Gomera | https://vinoslagomera.com/viticultura/ |
| Palomino Fino | grape | Palomino | https://docondadodehuelva.es/en/our-vineyards/ |
| Listán Blanco | grape | Palomino | https://www.canarywine.com/en/varieties/ |
| Moscatel de Alejandría | grape | Muscat of Alexandria | https://vinomalaga.com/en/consejo-regulador/d-o-sierras-de-malaga/ |
| Malvasia Volcanica | grape | Malvasía Volcánica | https://marcacanaria.com/malvasia-volcanica-la-uva-de-lanzarote/ |
| Diego | grape | Vijariego Blanco | https://wineshoplanzarote.com/products/vulcano-oak-aged-diego-dry |
| Tinta Negra | grape | Negramoll | https://en.wikipedia.org/wiki/List%C3%A1n_negro |
| Prensal Blanc | grape | Moll | https://www.foodswinesfromspain.com/en/wine/articles/2020/june/mallorcas-native-wine-grapes |
| Bermejuela | grape | Marmajuelo | https://saboreandocanarias.com/2016/10/16/las-denominaciones-de-origen-de-canarias-do-vino-el-hierro-4/ |
| Gual | grape | Malvasia Fina | https://www.foodswinesfromspain.com/en/wine/articles/2021/october/the-canary-islands-and-their-iconic-grape-varieties-an-exciting-world-to-explore |


## Review (main session, 2026-09-26)

- **Jerez** keeps its retail name as canonical (regions.yaml convention:
  the retail-facing form). `Jerez-Xérès-Sherry` is now a synonym, and the
  `was:` field is dropped. Manzanilla and Sierras de Málaga as sibling DOs
  are accepted.
- **Canary Islands**: classification `VC` → `DO`. Islas Canarias has been
  an island-wide DOP since 2011.
- **Vijariego Blanco**: dropped the synonym `Diego`, a person's name.
- **Baboso Negro** is Alfrocheiro (DNA; VIVC). It is now a synonym of the
  existing `Alfrocheiro`, not a new grape. es-n's `Bruñal` (also
  Alfrocheiro) moved here as a synonym too, with its `Brunal` and
  `Bastardillo Chico` spellings. `grapes:` fields that name Baboso Negro
  or Bruñal still resolve as synonyms.
- For the reconciliation pass: Gual = Malvasia Fina (Boal) is the
  literature call, and one source puts Gual under Albillo Mayor. Check VIVC.
- Hierarchy is fine: Mallorca IGP with the Binissalem and Pla i Llevant
  DOs as children, and the Tenerife DOs split out from synonyms.
- `check` is clean except the known `Cebreros` duplicate (es-n / Sierra de
  Gredos), which is fixed at merge.
- **Merge-time drops** (no Wikidata item; a grape needs one to build):
  `Malvasía Volcánica`, `Vijariego Negro`, `Giró Ros`, `Baladí Verdejo`.
  They were removed from `grapes:` fields too. Malvasía Volcánica is
  Lanzarote's signature grape, so it should come back if Wikidata gains an
  item.
- `Malvasía Aromática` is pinned to Q1887941 (Malvasia di Sardegna), the
  same variety as Malvasia di Lipari and Malvasía de Sitges. The resolver's
  pick, "Malvasia odorosissima", was wrong. `Malvasía Rosada` →
  "Malvasia di Sardegna Rosada" is right.
- Added `Binissalem-Mallorca` as a Binissalem synonym.
