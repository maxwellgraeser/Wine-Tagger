# it-c2: Umbria, Marche, Lazio, Abruzzo, Molise

**Country:** IT. **Slice:** Central Italy outside Tuscany. Italy is split
across five agents (it-n, it-c1, it-c2, it-s1, it-s2).

**You own:** the existing entries for Umbria, Marche, Lazio, Abruzzo and
Molise, and everything under them: every DOCG, DOC and IGT in these five
regions.
- **Umbria:** Montefalco Sagrantino, Montefalco, Torgiano, and Orvieto
  (straddles Lazio; parent Umbria, note the straddle).
- **Marche:** Verdicchio dei Castelli di Jesi and Verdicchio di Matelica,
  Conero / Rosso Conero, Offida, Rosso Piceno, Lacrima di Morro d'Alba.
- **Lazio:** Frascati, Cesanese del Piglio, Est! Est!! Est!!! di
  Montefiascone.
- **Abruzzo:** Montepulciano d'Abruzzo and its Colline Teramane DOCG,
  Trebbiano d'Abruzzo, Cerasuolo d'Abruzzo, Terre di Chieti IGT.
- **Molise:** Tintilia del Molise, Biferno.

**Names:**
- Canonical names follow the existing entries; the Italian form is a
  synonym where it differs.
- "Montepulciano" is both a grape (Abruzzo) and a Tuscan town (Vino Nobile
  di Montepulciano). Do not add "Montepulciano" as a region synonym; flag
  it in the `.md`.

**Not yours:**
- it-n: Piedmont, Aosta, Liguria, Lombardy, Trentino-Alto Adige, Veneto,
  Friuli, Emilia-Romagna
- it-c1: Tuscany
- it-s1: Campania, Puglia, Basilicata
- it-s2: Calabria, Sicily, Sardinia

**Official register:** MASAF's national register of denominations,
Federdoc, and eAmbrosia. Count against them. The existing convention is
`classification: DOCG` / `DOC` / `IGT`.

**`grapes:` field, yes, for every DOCG/DOC:** the principal varieties its
disciplinare names. For example, Montefalco Sagrantino: Sagrantino;
Verdicchio dei Castelli di Jesi: Verdicchio. Skip IGTs unless the
disciplinare is variety-specific.

**Grapes file:** natives and local names of these five regions missing
from `grapes.yaml`:
- Trebbiano Abruzzese, a distinct variety from Trebbiano Toscano (it-c1's).
- Malvasia Bianca di Candia and Malvasia del Lazio.
- Grechetto, Sagrantino, Verdicchio / Trebbiano di Soave / Turbiana,
  Pecorino, Passerina, Lacrima, Bellone, Cesanese, Montepulciano,
  Tintilia.

**Grapes already handled by it-n:**
- `Pignoletto` is a new grape (Grechetto Gentile).
- Albana was added.
- The existing canonical `Grechetto` should mean Umbria's Grechetto di
  Orvieto. Confirm that, and add synonyms accordingly. Do not map
  "Grechetto Gentile" to it.

Run `context --grape` on every grape before adding it, so nothing is
duplicated.
