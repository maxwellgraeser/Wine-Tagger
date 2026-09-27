# pt-s: Portugal, south and islands

**Country:** PT. **Slice:** Lisboa, Tejo, Península de Setúbal, Alentejo,
Algarve, Madeira, Açores. Portugal is split across two agents (pt-n,
pt-s).

**You own:** the existing `Lisboa`, `Alenquer`, `Bucelas`, `Colares`,
`Óbidos`, `Tejo`, `Alentejo`, `Península de Setúbal`, `Palmela`,
`Madeira`, `Algarve` and `Açores` entries and everything under them, plus
every DOC and IGP in the south and on the islands:
- **DOCs:** Lisboa region: Alenquer, Arruda, Bucelas, Carcavelos,
  Colares, Lourinhã, Óbidos, Torres Vedras; DoTejo; Palmela, Setúbal
  (Moscatel de Setúbal); Alentejo; Lagoa, Lagos, Portimão, Tavira;
  Madeira, Madeirense; Biscoitos, Graciosa, Pico.
- **Subregions that labels use:** Alentejo's eight (Borba, Évora,
  Granja-Amareleja, Moura, Portalegre, Redondo, Reguengos, Vidigueira);
  DoTejo's. Classification `Sub-região`, children of their DOC.
- **IGPs:** Lisboa, Tejo, Península de Setúbal, Alentejano, Algarve,
  Terras Madeirenses, Açores. Classification `IGP`. Where the IGP and the
  region share a name with an existing entry (Lisboa, Tejo, Algarve),
  keep one entry and say which in the `.md`.

Madeira styles (Sercial, Verdelho, Boal, Malmsey, Rainwater, Frasqueira)
are grape or style names, not regions.

**Not yours:** pt-n: Vinho Verde, Trás-os-Montes, Douro, Porto,
Távora-Varosa, Lafões, Dão, Bairrada, Beira Interior, Encostas d'Aire,
and their IGPs.

**Official register:** eAmbrosia (Portugal's PDOs and PGIs) first, then
IVV (ivv.gov.pt) and the regional commissions (CVR Lisboa, CVR Tejo,
CVRA Alentejo, CVR Península de Setúbal, IVBAM). Count DOCs, subregions
and IGPs against them.

**`grapes:` field, yes, for every DOC:** the principal varieties its
rules name. For example, Colares: Ramisco, Malvasia de Colares; Setúbal:
Moscatel de Setúbal, Moscatel Roxo.

**Grapes file:** southern and island natives and local names missing
from `grapes.yaml`. Run `context --grape` on each first; add only
missing grapes and missing synonyms:
- Castelão / Periquita, Trincadeira / Tinta Amarela, Alicante Bouschet,
  Moreto, Tinta Miúda (Graciano), Ramisco, Negra Mole, Tinta Negra
  (Negramoll: check what es-s1 merged).
- Arinto / Pedernã, Fernão Pires / Maria Gomes, Antão Vaz, Síria /
  Roupeiro (Doña Blanca: check VIVC), Vital, Malvasia de Colares,
  Moscatel de Setúbal (Muscat of Alexandria), Moscatel Roxo, Rabo de
  Ovelha, Crato Branco.
- Madeira: Sercial (Esgana Cão), Verdelho, Boal (Malvasia Fina? check
  VIVC; Bual is a label form), Malvasia Cândida, Terrantez, Bastardo is
  pt-n's. Azores: Arinto dos Açores (distinct from Arinto), Verdelho,
  Terrantez do Pico.
- pt-n owns Touriga Nacional, Tinta Roriz / Aragonez and the northern
  grapes. Don't add those.
