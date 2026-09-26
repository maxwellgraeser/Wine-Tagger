# it-s2: Calabria, Sicily, Sardinia

**Country:** IT. **Slice:** Calabria and the islands. Italy is split
across five agents (it-n, it-c1, it-c2, it-s1, it-s2).

**You own:** the existing entries for Calabria, Sicily and Sardinia, and
everything under them: every DOCG, DOC and IGT in these three regions.
- **Calabria:** Cirò, Greco di Bianco, Calabria IGT.
- **Sicily:** Etna, Cerasuolo di Vittoria, Vittoria, Marsala, Pantelleria /
  Passito di Pantelleria, Malvasia delle Lipari, Sicilia DOC, Terre
  Siciliane IGT, Noto, Faro, Menfi.
- **Sardinia:** Vermentino di Gallura, Vermentino di Sardegna, Cannonau di
  Sardegna and its sub-zones, Carignano del Sulcis, Monica di Sardegna,
  Isola dei Nuraghi IGT.

Canonical names follow the existing entries (Sicily, Sardinia); the
Italian form is a synonym (Sicilia, Sardegna).

**Not yours:**
- it-n: Piedmont, Aosta, Liguria, Lombardy, Trentino-Alto Adige, Veneto,
  Friuli, Emilia-Romagna
- it-c1: Tuscany
- it-c2: Umbria, Marche, Lazio, Abruzzo, Molise
- it-s1: Campania, Puglia, Basilicata

**Official register:** MASAF's national register of denominations,
Federdoc, and eAmbrosia. Count against them. The existing convention is
`classification: DOCG` / `DOC` / `IGT`.

**`grapes:` field, yes, for every DOCG/DOC:** the principal varieties its
disciplinare names. For example, Etna Rosso: Nerello Mascalese, Nerello
Cappuccio; Cirò Rosso: Gaglioppo. Skip IGTs unless the disciplinare is
variety-specific.

**Grapes file:** natives and local names of these regions missing from
`grapes.yaml`. Several exist already; add only missing grapes and missing
synonyms. Run `context --grape` on each one first.
- Calabria: Gaglioppo, Magliocco Canino and Magliocco Dolce (distinct),
  Mantonico, Greco Nero.
- Sicily: Nerello Mascalese, Nerello Cappuccio, Frappato, Nero d'Avola /
  Calabrese, Perricone, Carricante, Catarratto, Grillo, Inzolia /
  Ansonica, Zibibbo (Muscat of Alexandria), Malvasia di Lipari.
  **Malvasia di Lipari = Malvasia di Sardegna** already exists in the
  library as `Malvasía Aromática` (Q1887941, from es-s1). Add the Italian
  names as synonyms with `existing: true`. Don't create a new grape. If you
  think the Italian name should be canonical, say so in the `.md`.
- Sardinia: Cannonau (= Grenache), Bovale, Monica, Nasco, Nuragus,
  Torbato, Vernaccia di Oristano (distinct from the other Vernaccias),
  Girò.
