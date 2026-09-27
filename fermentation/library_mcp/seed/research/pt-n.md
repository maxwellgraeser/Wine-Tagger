Status: complete

# pt-n: Portugal, north and centre — research notes

## Sources
- IVV (Instituto da Vinha e do Vinho) region pages, ivv.gov.pt (accessed 2026-09-27).
- CVRVV (Comissão de Viticultura da Região dos Vinhos Verdes), vinhoverde.pt.
- IVDP (Instituto dos Vinhos do Douro e do Porto), ivdp.pt.
- CVR Dão, cvrdao.pt.
- eAmbrosia (EU register of PDO/PGI), ec.europa.eu/agriculture/eambrosia.
- Wikipedia region pages used only to cross-check sub-region names and grapes
  where official-body pages did not enumerate them (Encostas d'Aire, Lafões,
  Távora-Varosa sub-structure).

## Grapes


## Counts

- DOCs: 10 official (Vinho Verde, Trás-os-Montes, Douro, Porto, Távora-Varosa,
  Lafões, Dão, Bairrada, Beira Interior, Encostas d'Aire) — all 10 produced.
- Sub-regions (labels use `Sub-região`): Vinho Verde 9, Douro 3,
  Trás-os-Montes 3, Dão 7, Beira Interior 3, Encostas d'Aire 2 (Alcobaça,
  Ourém) = 27 produced, matching the scope's list exactly.
- IGPs: 7 official in scope (Minho, Transmontano, Duriense, Terras de
  Cister, Terras do Dão, Terras da Beira, Beira Atlântico) — all 7 produced.
- Total: 44 region entries (10 DOC + 27 sub-region + 7 IGP).
- Grapes file: 3 new grapes (Tinta Francisca, Códega do Larinho, Cerceal).
  All other grapes named in the scope already exist in `grapes.yaml` under
  their canonical name or a synonym that already covers the Portuguese form
  (Alvarinho/Albariño, Trajadura/Treixadura, Gouveio/Godello, Jaen/Mencía,
  Tinta Roriz+Aragonez/Tempranillo, Sousão/Vinhão, Bastardo/Trousseau), so
  no `existing: true` entries were needed.

## Changes to existing entries

- **Douro**: removed "Cima Corgo", "Baixo Corgo", "Douro Superior" as
  synonyms and added them as child `Sub-região` entries under Douro, per
  the scope instruction (they are named sub-appellations, not alternate
  names for the whole DOC). Kept "Alto Douro" and "Douro Valley" as
  synonyms.
- **Vinho Verde**: dropped "Minho" as a synonym. It collided with the new
  IGP "Minho" entry (a different, broader classification covering the same
  geography) — a synonym can't equal another entry's name in the same
  country. "Minho" now names the IGP only.
- **Trás-os-Montes**: dropped "Transmontano" as a synonym for the same
  reason — it now names the IGP "Transmontano".
- **Beira Interior**: dropped "Beira Atlântico" as a synonym — it now names
  its own IGP entry. Also dropped "Beiras" as a synonym: on retailer pages
  "Beiras" refers to the whole macro-region (Dão + Bairrada + Beira
  Interior + Távora-Varosa + Lafões), not specifically the Beira Interior
  DOC, so keeping it as a synonym of one DOC would misroute wines from the
  others.

## Homonyms

- None identified for this scope's names against other countries (Douro,
  Porto/Port, Dão, Bairrada, Vinho Verde, Trás-os-Montes, Beira Interior,
  Távora-Varosa, Lafões, Encostas d'Aire, and their sub-regions/IGPs are
  all Portugal-specific).

## Uncertain calls

- **Cerceal / Cercial / Sercial**: sources agree mainland "Cerceal"/
  "Cercial" (Dão, Bairrada, Beiras, Távora-Varosa, Lafões) is a distinct
  grape from Madeira's Sercial, despite the near-identical name and the
  frequent "Sercial da Madeira" cross-reference in trade literature. Added
  as a new grape "Cerceal" with "Cercial" as a synonym; did not touch the
  existing "Sercial" entry. Flagging for review since VIVC identity could
  not be independently confirmed here.
- **Douro / Porto grape lists**: IVDP materials give slightly different
  "recommended" lists depending on end use (still Douro wine vs. Port).
  I used the broader Douro-wine list for the Douro DOC entry and the
  narrower "5 red + 5 white" traditional Port list for the Porto DOC entry;
  both are drawn from IVDP's own castas page.
- **Lafões / Rabo de Ovelha, Amaral**: sources name "Amaral" (red) and
  "Rabo de Ovelha" (white) as commonly used in Lafões, but neither is in
  the scope's grapes list and neither is in `grapes.yaml`. Left both out of
  Lafões's `grapes:` field and did not add them as new grapes, to stay
  within the scope's grape list; flagging in case that was an oversight
  rather than a deliberate exclusion.
- **Beira Interior grapes**: the DOC's rules list red and white varieties
  without a strict "principal vs minor" split in the sources found; I
  included the varieties that recur across multiple independent sources
  (Arinto, Fernão Pires, Síria, Malvasia Fina, Alfrocheiro, Tinta Roriz,
  Touriga Nacional, Rufete) and left out clearly minor/heritage ones
  (Fonte Cal, Terrantez) that only appeared in a single old-vine survey.

## Label string → canonical

| label string | kind | canonical | where seen (URL) |
|---|---|---|---|
| Vinho Verde | region | Vinho Verde | https://www.vinhoverde.pt/pt/ |
| Monção e Melgaço | region | Monção e Melgaço | https://www.vinhoverde.pt/pt/regiao/sub-regioes |
| Alvarinho | grape | Albariño | https://www.reversewinesnob.com/grapes-of-vinho-verde |
| Loureiro | grape | Loureiro | https://barcoswines.com/en/castas-vinho-verde/ |
| Alto Douro | region | Douro | https://en.wikipedia.org/wiki/Douro_DOC |
| Cima Corgo | region | Cima Corgo | https://www.ivdp.pt/pt/vinha/regiao/regiao-caracteristicas/ |
| Douro Superior | region | Douro Superior | https://www.ivdp.pt/pt/vinha/regiao/regiao-caracteristicas/ |
| Vinho do Porto | region | Porto | https://www.ivdp.pt/ |
| Tinta Roriz | grape | Tempranillo | https://www.ivdp.pt/pt/vinha/castas/ |
| Touriga Nacional | grape | Touriga Nacional | https://www.ivdp.pt/pt/vinha/castas/ |
| Sousão | grape | Vinhão | https://www.ivdp.pt/pt/vinha/castas/ |
| Dão DOC | region | Dão | https://www.cvrdao.pt/media/1/documentos/1709/6500131928851O.pdf |
| Encruzado | grape | Encruzado | http://www.infovini.com/pagina.php?codNode=3897 |
| Jaen | grape | Mencía | https://heldercunha.com/dao-doc-e-suas-sub-regioes-o-berco-de-vinhos-elegantes-e-complexos/ |
| Serra da Estrela | region | Serra da Estrela | https://rotavinhosdao.pt/o-dao/a-regiao |
| Bairrada | region | Bairrada | https://heldercunha.com/bairrada-doc/ |
| Baga | grape | Baga | https://heldercunha.com/castas-autoctones-da-bairrada-doc/ |
| Maria Gomes | grape | Fernão Pires | https://reserva85.com.br/vinho/indicacao-geografica-ig-denominacao-de-origem-do/regioes-demarcadas-de-portugal/bairrada/ |
| Cova da Beira | region | Cova da Beira | https://www.clubevinhosportugueses.pt/vinhos/vinhos-doc-da-beira-interior-e-sub-regiao-da-cova-da-beira/ |
| Síria | grape | Síria | https://www.velvetbull.pt/regiao-vitivinicola-da-beira-interior |
| Terras da Beira | region | Terras da Beira | https://www.publico.pt/2023/10/13/terroir/noticia/indicacao-geografica-terras-beira-tambem-proteccao-ue-2066664 |
| Terras de Cister | region | Terras de Cister | https://www.winetourism.com/wine-region/terras-de-cister/ |
| Távora-Varosa | region | Távora-Varosa | https://winesofportugal.com/pt/descobrir/regioes-vitivinicolas/tavora-varosa/ |
| Cerceal | grape | Cerceal | https://bubblyprofessor.com/2021/06/20/confusion-corner-sercial-cerceal-cercial/ |
| Ourém | region | Ourém | https://www.vinhosdelisboa.com.br/denominacoes/encostas-daire |
| Códega do Larinho | grape | Códega do Larinho | https://www.antoniomacanita.com/en/all-about-wines/grape-list/codega-do-larinho |

Status: complete

## Review (main session, 2026-09-27)
- Hierarchy checked with `check --tree`: Douro's three subregions split
  out of its synonyms; IGP overlays (Minho, Transmontano, Duriense…) kept
  as roots rather than parents of DOCs. Accepted.
- The four "X DOC" warnings are pre-existing, harmless synonyms; left.
- Cerceal kept distinct from Madeira's Sercial pending the QID check.
- Dropped Cerceal at merge (no Wikidata item); removed from grapes: fields.
