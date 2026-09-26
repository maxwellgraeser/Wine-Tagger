# es-s1: Andalucía, Balearics, Canaries

**Country:** ES. **Slice:** Andalucía and the islands. Spain is split
across three agents (es-n, es-s1, es-s2).

**You own:** the existing ES entries in these autonomous communities and
everything under them, plus every DO, Vino de Pago (VP), Vino de Calidad
(VC) and IGP / Vino de la Tierra in them:
- **Andalucía:** Jerez-Xérès-Sherry, Manzanilla-Sanlúcar de Barrameda,
  Montilla-Moriles, Málaga, Sierras de Málaga, Condado de Huelva, Granada,
  Lebrija; VT Cádiz and the other IGPs.
- **Balearics:** Binissalem, Pla i Llevant; IGP Mallorca and the others.
- **Canaries:** Tacoronte-Acentejo, Valle de la Orotava,
  Ycoden-Daute-Isora, Abona, Valle de Güímar, Lanzarote, La Palma, El
  Hierro, La Gomera, Gran Canaria, and the Islas Canarias DO.

Sherry styles (Fino, Manzanilla, Oloroso, Amontillado, Palo Cortado) are
not regions; keep them out. Manzanilla-Sanlúcar de Barrameda is a region.

**Not yours:**
- es-n: Galicia, Asturias, Cantabria, País Vasco, Navarra, La Rioja,
  Aragón, Catalonia, Castilla y León, and Cava.
- es-s2: Castilla-La Mancha, Madrid, Valencia, Murcia, Extremadura.

**Official register:** MAPA's list of DOPs/IGPs (mapa.gob.es) and
eAmbrosia. Count against them. The existing convention is
`classification: DO`; use `VP`, `VC` and `IGP` for the others.

**`grapes:` field, yes, for every DO/VP:** the principal varieties its
pliego names. For example, Jerez: Palomino, Pedro Ximénez, Moscatel.

**Grapes file:** Andalusian and island natives and local names missing
from `grapes.yaml`. Several exist already; add only missing grapes and
missing synonyms. Run `context --grape` on each one first.
- Andalucía: Palomino Fino / Listán Blanco (check VIVC), Pedro Ximénez
  (PX), Moscatel de Alejandría / Moscatel (= Muscat of Alexandria),
  Moscatel de Grano Menudo, Tintilla de Rota.
- Canaries: Listán Negro, Negramoll / Tinta Negra, Vijariego, Baboso
  Negro, Malvasía Volcánica, Marmajuelo, Gual.
- Balearics: Manto Negro, Callet, Prensal Blanc / Moll, Giró Ros.
