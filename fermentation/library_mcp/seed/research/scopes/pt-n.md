# pt-n: Portugal, north and centre

**Country:** PT. **Slice:** Minho, Trás-os-Montes, Douro, Beiras.
Portugal is split across two agents (pt-n, pt-s).

**You own:** the existing `Vinho Verde`, `Trás-os-Montes`, `Douro`,
`Porto`, `Dão`, `Bairrada` and `Beira Interior` entries and everything
under them, plus every DOC and IGP in the north and centre:
- **DOCs:** Vinho Verde, Trás-os-Montes, Douro, Porto, Távora-Varosa,
  Lafões, Dão, Bairrada, Beira Interior, Encostas d'Aire.
- **Subregions that labels use:** Vinho Verde's nine (Monção e Melgaço,
  Lima, Cávado, Ave, Basto, Sousa, Baião, Paiva, Amarante); Douro's three
  (Baixo Corgo, Cima Corgo, Douro Superior); Dão's seven (Alva, Besteiros,
  Castendo, Serra da Estrela, Silgueiros, Terras de Azurara, Terras de
  Senhorim); Trás-os-Montes' three (Chaves, Valpaços, Planalto
  Mirandês); Beira Interior's and Encostas d'Aire's. Classification
  `Sub-região`, children of their DOC.
- **IGPs:** Minho, Transmontano, Duriense, Terras de Cister, Terras do
  Dão, Terras da Beira, Beira Atlântico. Classification `IGP`.

Port styles (Tawny, Ruby, LBV, Colheita, Vintage) are not regions; keep
them out.

**Existing entries to fix:** `Douro` carries "Cima Corgo", "Baixo Corgo"
and "Douro Superior" as synonyms. Make them entries under Douro and
remove the synonyms. "Alto Douro" and "Douro Valley" stay as synonyms.

**Not yours:** pt-s: Lisboa (and its DOCs), Tejo, Península de Setúbal,
Alentejo, Algarve, Madeira, Açores, and their IGPs.

**Official register:** eAmbrosia (Portugal's PDOs and PGIs) first, then
IVV (ivv.gov.pt) and the regional commissions (CVRVV, IVDP, CVR Dão,
CVR Bairrada). Count DOCs, subregions and IGPs against them.

**`grapes:` field, yes, for every DOC:** the principal varieties its
rules name. For example, Vinho Verde: Alvarinho, Loureiro, Arinto,
Avesso, Azal, Trajadura; Dão: Touriga Nacional, Encruzado, Jaen,
Alfrocheiro, Tinta Roriz.

**Grapes file:** northern and central natives and local names missing
from `grapes.yaml`. Run `context --grape` on each first; add only
missing grapes and missing synonyms:
- Touriga Nacional, Touriga Franca, Tinta Roriz and Aragonez (both are
  Tempranillo; you own both synonyms), Tinta Barroca, Tinto Cão, Sousão /
  Vinhão, Rufete, Bastardo (Trousseau), Tinta Francisca.
- Alvarinho (Albariño), Loureiro, Avesso, Azal, Trajadura (Treixadura),
  Encruzado, Jaen (Mencía), Alfrocheiro, Baga, Bical, Rabigato, Gouveio
  (Godello: check VIVC), Viosinho, Malvasia Fina, Códega do Larinho, Cerceal.
- pt-s owns Arinto / Pedernã, Fernão Pires / Maria Gomes, Síria /
  Roupeiro, Trincadeira / Tinta Amarela, Castelão and the Madeira and
  Azores grapes. Don't add those.
