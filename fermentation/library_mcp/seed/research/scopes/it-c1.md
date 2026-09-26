# it-c1: Tuscany

**Country:** IT. **Slice:** Tuscany. Italy is split across five agents
(it-n, it-c1, it-c2, it-s1, it-s2).

**You own:** the existing entry for Tuscany and everything under it: every
DOCG, DOC and IGT in Tuscany.
- Chianti, with its sub-zones as children: Rufina, Colli Senesi, Colli
  Fiorentini, Colli Aretini, Colline Pisane, Montalbano, Montespertoli.
- Chianti Classico, which is its own DOCG, not a child of Chianti.
- Brunello and Rosso di Montalcino, Sant'Antimo.
- Vino Nobile and Rosso di Montepulciano.
- Bolgheri and Bolgheri Sassicaia; Morellino di Scansano, Maremma Toscana,
  Montecucco; Carmignano, Vernaccia di San Gimignano, the Vin Santo DOCs;
  Toscana IGT and Costa Toscana IGT.

**Names:**
- Canonical names follow the existing entries (Tuscany); the Italian form
  is a synonym (Toscana).
- "Montepulciano" is both a grape (Abruzzo) and a Tuscan town (Vino Nobile
  di Montepulciano). Do not add "Montepulciano" as a region synonym; flag
  it in the `.md`.

**Not yours:**
- it-n: Piedmont, Aosta, Liguria, Lombardy, Trentino-Alto Adige, Veneto,
  Friuli, Emilia-Romagna
- it-c2: Umbria, Marche, Lazio, Abruzzo, Molise
- it-s1: Campania, Puglia, Basilicata
- it-s2: Calabria, Sicily, Sardinia

**Official register:** MASAF's national register of denominations,
Federdoc, and eAmbrosia. Count against them. The existing convention is
`classification: DOCG` / `DOC` / `IGT`.

**`grapes:` field, yes, for every DOCG/DOC:** the principal varieties its
disciplinare names. For example, Brunello di Montalcino: Sangiovese. Skip
IGTs unless the disciplinare is variety-specific.

**Grapes file:** Tuscan natives and local names missing from `grapes.yaml`:
- Sangiovese clones and local names: Brunello, Prugnolo Gentile,
  Morellino, Sangioveto. Nielluccio is the Corsican name, which fr-rpl may
  add; skip it if present.
- Canaiolo, Colorino, Ciliegiolo, Foglia Tonda, Pugnitello, Mammolo.
- Vernaccia di San Gimignano, a distinct variety from the other
  Vernaccias.
- Trebbiano Toscano, a distinct variety from Trebbiano Abruzzese (it-c2's).

**Grapes already handled by it-n:** `Pignoletto` is a new grape (Grechetto
Gentile), and Albana was added.

Run `context --grape` on every grape before adding it, so nothing is
duplicated.
