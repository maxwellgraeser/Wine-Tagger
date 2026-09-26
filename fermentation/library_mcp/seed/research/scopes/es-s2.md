# es-s2: Castilla-La Mancha, Madrid, Valencia, Murcia, Extremadura

**Country:** ES. **Slice:** Central and south-eastern Spain. Spain is
split across three agents (es-n, es-s1, es-s2).

**You own:** the existing ES entries in these autonomous communities and
everything under them, plus every DO, Vino de Pago (VP), Vino de Calidad
(VC) and IGP / Vino de la Tierra in them:
- **Castilla-La Mancha:** La Mancha, Valdepeñas, Manchuela, Méntrida,
  Almansa, Ribera del Júcar, Uclés, Mondéjar; the many Vinos de Pago here
  (Dominio de Valdepusa, Finca Élez, Guijoso, Dehesa del Carrizal, Campo de
  la Guardia, Pago Florentino, Casa del Blanco, Calzadilla...); and IGP
  Vino de la Tierra de Castilla.
- **Madrid:** Vinos de Madrid and its sub-zones.
- **Valencia:** Valencia, Utiel-Requena, Alicante, and their VPs.
- **Murcia:** Jumilla (straddles Castilla-La Mancha), Yecla, Bullas.
- **Extremadura:** Ribera del Guadiana and its sub-zones.

**Not yours:**
- es-n: Galicia, Asturias, Cantabria, País Vasco, Navarra, La Rioja,
  Aragón, Catalonia, Castilla y León, and Cava.
- es-s1: Andalucía, Balearics, Canaries.

**Official register:** MAPA's list of DOPs/IGPs (mapa.gob.es) and
eAmbrosia. Count against them. The existing convention is
`classification: DO`; use `VP`, `VC` and `IGP` for the others.

**`grapes:` field, yes, for every DO/VP:** the principal varieties its
pliego names. For example, Jumilla: Monastrell; Utiel-Requena: Bobal.

**Grapes file:** natives and local names of these regions missing from
`grapes.yaml`. Several exist already; add only missing grapes and missing
synonyms. Run `context --grape` on each one first.
- Airén, Bobal, Monastrell aliases, Cencibel and Tinto de Madrid
  (Tempranillo aliases), Garnacha Tintorera.
- Pardina, Cayetana Blanca, Merseguera, Moravia Agria, Forcallat.

**Cebreros:** es-n (already finished) added Cebreros as its own DO/VC
under Castilla y León. If the existing `Sierra de Gredos` entry is yours
(it spans Madrid, Castilla-La Mancha and Castilla y León), drop "Cebreros"
from its synonyms.
