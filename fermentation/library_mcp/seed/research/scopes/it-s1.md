# it-s1: Campania, Puglia, Basilicata

**Country:** IT. **Slice:** Southern mainland Italy. Italy is split across
five agents (it-n, it-c1, it-c2, it-s1, it-s2).

**You own:** the existing entries for Campania, Puglia and Basilicata, and
everything under them: every DOCG, DOC and IGT in these three regions.
- **Campania:** Taurasi, Fiano di Avellino, Greco di Tufo, Aglianico del
  Taburno, Falanghina del Sannio, Irpinia, Campi Flegrei, Costa d'Amalfi,
  Lacryma Christi / Vesuvio, Campania IGT, Beneventano IGT.
- **Puglia:** Primitivo di Manduria and its Dolce Naturale DOCG, Gioia del
  Colle, Salice Salentino, Castel del Monte and its DOCGs, Brindisi,
  Copertino, Squinzano, Salento IGT, Puglia IGT.
- **Basilicata:** Aglianico del Vulture and its Superiore DOCG.

Canonical names follow the existing entries; the Italian or English form
is a synonym where it differs.

**Not yours:**
- it-n: Piedmont, Aosta, Liguria, Lombardy, Trentino-Alto Adige, Veneto,
  Friuli, Emilia-Romagna
- it-c1: Tuscany
- it-c2: Umbria, Marche, Lazio, Abruzzo, Molise
- it-s2: Calabria, Sicily, Sardinia

**Official register:** MASAF's national register of denominations,
Federdoc, and eAmbrosia. Count against them. The existing convention is
`classification: DOCG` / `DOC` / `IGT`.

**`grapes:` field, yes, for every DOCG/DOC:** the principal varieties its
disciplinare names. For example, Taurasi: Aglianico; Primitivo di
Manduria: Primitivo. Skip IGTs unless the disciplinare is
variety-specific.

**Grapes file:** natives and local names of these regions missing from
`grapes.yaml`. Several exist already; add only missing grapes and missing
synonyms. Run `context --grape` on each one first.
- Campania: Piedirosso / Per'e Palummo, Coda di Volpe, Asprinio,
  Pallagrello Bianco and Nero, Casavecchia, Biancolella, Forastera,
  Sciascinoso.
- Puglia: Uva di Troia / Nero di Troia, Bombino Bianco and Nero,
  Susumaniello, Verdeca, and Malvasia Nera di Brindisi and di Lecce
  (distinct varieties).
