Status: complete

# Northern Italy (it-n) — research notes

Scope: Piedmont, Valle d'Aosta, Liguria, Lombardy, Trentino-Alto Adige,
Veneto, Friuli-Venezia Giulia, Emilia-Romagna, plus the interregional
delle Venezie DOC/IGT and Prosecco DOC.

## Sources

- **MASAF (Ministero dell'Agricoltura, della Sovranità Alimentare e delle Foreste), "Numero dei vini a D.O.C.G. - D.O.C. - I.G.T. al 5 luglio 2011"** — `https://www.masaf.gov.it/flex/files/8/8/c/D.c98d43be48c9b307022a/Vini_DOCG_DOC_IGT_suddivisi_per_regione.pdf`, downloaded to the scratchpad and read directly with the PDF reader (WebFetch cannot render it). This is the official national register broken down by region. It is dated 2011, so its region-by-region *totals* undercount today's DOCG list (Nizza, Terre Alfieri, Canelli, Rosazzo, Bagnoli Friularo, Colli di Conegliano, Colli Euganei Fior d'Arancio, Montello Rosso, Piave Malanotte and Recioto di Gambellara were all promoted to DOCG after 2011). I used it for structure that doesn't change often: sottozone names, alternative/dialect names, and the pre-2011 IGT rename of "Golfo dei Poeti" to "Liguria di Levante" it happens to predate. I did **not** use its 2011 totals for the counts table below.
- **Quattrocalici, per-region "Le Denominazioni di Origine" pages** — `quattrocalici.it/regione/<region>/denominazioni/` for piemonte, valle-d-aosta, liguria, lombardia, trentino-alto-adige, veneto, friuli-venezia-giulia, emilia-romagna. A current (not archival) wine encyclopedia; used as the primary source for the present-day DOCG/DOC/IGT roster and counts in each region, cross-checked item-by-item against the MASAF list for structure.
- **Wikipedia (EN), "List of Italian DOCG wines"** — `https://en.wikipedia.org/wiki/List_of_Italian_DOCG_wines` — cross-check for the current national DOCG roster (78 nationally at fetch time), used to confirm Quattrocalici's per-region DOCG counts.
- **Wikipedia (EN), "Valle d'Aosta DOC"** — `https://en.wikipedia.org/wiki/Valle_d%27Aosta_DOC` — sub-zone grape composition (Donnas, Arnad-Montjovet, Torrette, Enfer d'Arvier, Nus incl. "Malvoisie", Chambave, Blanc de Morgex et de la Salle).
- **disciplinare.it** — `calosso-doc.html` and `valsusa-doc.html` — read the actual production-rule grape lists for two small Piedmont DOCs I wasn't confident about guessing (Calosso: Gamba Rossa, not Barbera as I first assumed from the name; Valsusa: Avanà/Barbera/Becuet/Dolcetto/Neretta Cuneese).
- **Wine-Searcher region/grape pages** and **Wikipedia** for individual label-string and grape-identity checks, cited inline in the label-string table and the grape entries.
- **it.wikipedia.org, "Golfo della Spezia"** — confirms the Liguria IGT "Golfo dei Poeti (La Spezia)" was renamed "Liguria di Levante" in November 2011 (which is why the July-2011 MASAF list still shows the old name).

## Counts

| Region | Official DOCG | Official DOC | Official IGT | Notes |
|---|---|---|---|---|
| Piedmont | 19 | 41 | 0 | All 19 DOCG and 40 of 41 DOC are separate rows; the 41st, the catch-all "Piemonte" DOC, is folded into the `Piedmont` macro-entry's synonyms (same pattern the existing library already used for "Toscana IGT" on Tuscany). Piedmont has had 0 IGT since its former IGT tier became the "Piemonte" DOC in 2011. |
| Valle d'Aosta | 0 | 1 | 0 | The single DOC plus its 7 sottozone (Donnas, Arnad-Montjovet, Torrette, Enfer d'Arvier, Chambave, Nus, Blanc de Morgex et de la Salle) — all 7 added as child rows since labels use the sottozona name, not "Valle d'Aosta" alone. |
| Liguria | 0 | 8 | 4 | All produced. |
| Lombardy | 5 | 22 (Quattrocalici's own numbered list under that "(22)" header actually contains 23 named DOCs — I produced all 23 named) | 15 (same mismatch: the "(15)" header's list names 16 IGTs — I produced all 16) | Quattrocalici's stated counts and its own lists disagree by one in both tiers; I went with what's actually named rather than the header number. Plus 5 bonus Valtellina Superiore sottozone (Grumello, Inferno, Maroggia, Sassella, Valgella). |
| Veneto | 14 | 29 | 9 (list itself only names 8 — same header/list mismatch) | 5 of the 29 DOC are filed under Lombardy (Garda, Lugana, San Martino della Battaglia) or Trentino-Alto Adige (Valdadige, Valdadige Terradeiforti) above/below, since those are interregional and I only wrote each once; see Homonyms/straddles. |
| Trentino-Alto Adige | 0 | 9 | 4 | delle Venezie DOC (1 of the 9) is filed under Veneto; Trevenezie IGT (1 of the 4) likewise. Alto Adige's 6 named sub-zones and Trentino's internal sottozone mentions are additional child rows beyond the 9. |
| Friuli-Venezia Giulia | 4 | 12 | 3 | Lison DOCG (1 of 4) and delle Venezie/Lison Pramaggiore/Prosecco DOC (3 of 12) and Alto Livenza/delle Venezie IGT (2 of 3) are filed under Veneto, since their larger area is there and I own both regions in this slice. Plus bonus Colli Orientali del Friuli sub-zones (Cialla, Schioppettino di Prepotto). |
| Emilia-Romagna | 2 | 18 | 9 | All produced, plus 4 bonus Colli Piacentini sottozone (Monterosso Val d'Arda, Trebbianino Val Trebbia, Val Nure, Vigoleno). |
| **Total** | **44** | **~141** (per-list) | **~45** (per-list, before removing cross-region duplicates) | it-n.regions.yaml has 250 rows total: 44 DOCG + ~5 bonus DOCG-sottozone, ~141 DOC + ~16 bonus DOC-sottozone, ~41 distinct IGT (fewer than the per-region sum because shared IGTs like Trevenezie/Alto Livenza/delle Venezie are written once), plus 8 unclassified macro-region/umbrella rows (the 7 region names plus the "Valtellina" umbrella — see below). |

**Left out, and why:**
- **Menzioni Geografiche Aggiuntive (MGA)** — Barolo's ~181 MGA crus and the equivalent commune/vineyard mentions in other DOCGs (Barbaresco, Conegliano-Valdobbiadene's "Rive", etc.) are explicitly out of scope per the brief and my scope note.
- **Historical, absorbed DOCs** — the pre-~2011 Romagna-area DOCs "Sangiovese di Romagna", "Trebbiano di Romagna", "Pagadebit di Romagna" and "Cagnina di Romagna" no longer appear as separate denominations in Quattrocalici's current Emilia-Romagna list; they appear to have been folded into the single current "Romagna DOC" as typology suffixes (e.g. "Romagna Sangiovese"). Not added as separate entries.
- **Rive/vineyard-level mentions** inside Conegliano Valdobbiadene, and single-commune "geographical mention" options inside e.g. Barbera d'Asti Superiore (Tinella, Colli Astiani) — left out as MGA-equivalent, not separate appellations.

## Changes to existing entries

The existing library's Italy entries repeatedly folded a real, separately-registered sub-appellation into its parent's `synonyms:` list instead of giving it its own entry (the same bug pattern the brief's Robertson/Simonsberg example describes). I found and fixed six instances of it, plus one straightforward re-tiering and a round of classification-suffix cleanup:

1. **`Valtellina` (was DOCG with `Sforzato di Valtellina` and `Valtellina Superiore` folded in as synonyms) → split into an unclassified umbrella `Valtellina` (matching the existing `Montalcino` pattern) with three real children: `Valtellina Superiore` (DOCG, plus its 5 named sottozone Grumello/Inferno/Maroggia/Sassella/Valgella), `Sforzato di Valtellina` (DOCG), and `Valtellina Rosso` (DOC, was a synonym before, now the base tier).** These are three legally distinct denominations with different rules, not three names for one wine.
2. **`Soave`'s synonym `"Soave Classico"` → its own child DOC `Soave Classico`.** Also added `Soave Superiore` (DOCG) and `Recioto di Soave` (DOCG) as children, since neither existed at all.
3. **`Valpolicella`'s synonym `"Valpolicella Classico"` → its own child DOC `Valpolicella Classico`**, plus a new `Valpantena` child DOC (another named sub-zone) and a new `Recioto della Valpolicella` DOCG child (the sweet passito tier didn't exist as an entry).
4. **`Barbera d'Asti`'s synonym `"Nizza"` → its own child DOCG `Nizza`.** Nizza has been a fully independent DOCG (its own disciplinare) since 2019; it is not just a synonym for "Barbera d'Asti Superiore from Nizza."
5. **`Asti`: added a new child DOCG `Canelli`** (2020), the equivalent elevated-subzone case for the Moscato d'Asti side of the family.
6. **`delle Venezie`'s synonym `"delle Venezie IGT"` → its own entry, `delle Venezie IGT`.** The DOC (Pinot Grigio) and the IGT are two separate registrations sharing a name, the same situation as "La Rioja" (ES/AR) but within one country.
7. **`Emilia-Romagna`'s synonyms `"Emilia"` and `"Romagna"` → split into their own entries: `Romagna` (DOC, parent of the new `Romagna Albana` DOCG and `Colli Romagna Centrale` DOC) and `Emilia` (IGT).** These are real, separately-registered appellations covering only part of the region, not alternate names for the whole region.
8. **Classification-suffix synonym cleanup**: dropped `"Piemonte DOC"`, `"Barolo DOCG"`, `"Barbaresco DOCG"`, `"Gavi DOCG"`, `"Amarone DOCG"`, `"Langhe DOC"`, `"Valpolicella DOC"`, `"Soave DOC"`, `"Prosecco DOC"` (kept `"Prosecco Treviso"`, a real geo-mention), `"Friuli DOC"`, `"Delle Venezie DOC"`, and `"Valle d'Aosta DOC"` from various existing entries, since the lookup code already strips DOCG/DOC/IGT/etc. before matching and the brief says not to add them — the existing ones were noise left over before that rule, per the same cleanup za did for "X WO" synonyms.
9. **Added `grapes:` to every existing DOCG/DOC entry that was missing it** (all of them were missing it before this pass) — Barolo/Barbaresco/Gattinara/Ghemme/Nebbiolo d'Alba/Roero → Nebbiolo(+Arneis for Roero); Barbera d'Asti/Barbera d'Alba → Barbera; Dolcetto d'Alba/Dogliani → Dolcetto; Asti → Moscato Bianco; Gavi → Cortese; Franciacorta → Chardonnay/Pinot Nero/Pinot Bianco; Lugana → Turbiana; Valpolicella/Amarone/Ripasso → Corvina/Corvinone/Rondinella; Soave → Garganega; Bardolino → Corvina/Rondinella; Prosecco/Conegliano Valdobbiadene → Glera; Custoza → Garganega/Trebbiano; delle Venezie → Pinot Grigio; Trento → Chardonnay/Pinot Nero/Pinot Bianco/Pinot Meunier; Teroldego Rotaliano (new entry) → Teroldego.
10. **`Colli Tortonesi`, `Monferrato`, `Langhe`, `Alto Adige`, `Trentino`, `Collio`, `Colli Orientali del Friuli`, `Friuli Grave`, `Friuli Isonzo`, `Colli Bolognesi`, `Colli Piacentini`, `Oltrepò Pavese` — no `grapes:` added.** Each covers many single-varietal typologies under one catch-all disciplinare with no single "principal" variety, the same reason the existing `Langhe` entry had none.

## Homonyms and interregional straddles

- **Collio (IT) / Goriška Brda (SI)** — one continuous cross-border wine district split by the Italy–Slovenia border, using different names on each side. Not an exact-string collision (different names), but worth knowing when Slovenia is researched.
- **Prosecco DOC (Veneto, filed here) reaches into Friuli-Venezia Giulia** (Trieste, Gorizia, Pordenone are among its 9 provinces) — kept as one entry under Veneto per the brief's explicit instruction, noted here for the FVG side.
- **delle Venezie DOC/IGT** span Veneto, Friuli-Venezia Giulia *and* Trentino — filed under Veneto, per the brief.
- **Valdadige / Valdadige Terradeiforti DOC** span Trentino-Alto Adige and Veneto (Verona) — filed under Trentino-Alto Adige as the larger, more historic part.
- **Garda DOC, Lugana DOC, San Martino della Battaglia DOC** span Lombardy and Veneto around Lake Garda — filed under Lombardy (matching the existing library's pre-existing choice for Lugana).
- **Lison DOCG / Lison Pramaggiore DOC** span Veneto and Friuli-Venezia Giulia (Pordenone) — filed under Veneto (2 of 3 provinces).
- **Colli di Luni DOC** spans Liguria (La Spezia) and Tuscany (Massa-Carrara, it-c's scope) — filed under Liguria as the historically larger part; it-c should not re-add it.
- **Alto Livenza IGT / Trevenezie IGT** are shared by Veneto, Friuli-Venezia Giulia and (Trevenezie only) Trentino-Alto Adige — written once, under Veneto.
- **"Romagna"** is also the name of the historical/cultural region; as a wine name it is unambiguous within Italy but note that "Romagna" alone is not a wine-region name in any other country I'm aware of.
- **"Modena"** and **"Reggiano"** are city/province names with no other-country wine-region collision found.
- **"Carso"** collides with no other country's registered wine region as far as I found; the Slovenian side of the same limestone plateau is the Kras/Karst wine district (see Teran, below, for the grape-identity side of this same border).

## Uncertain calls

- **The "Bonarda" name is genuinely three or four different grapes across northern Italy**, and I deliberately avoided using the bare word "Bonarda" anywhere in `grapes:` fields to prevent a mislabel: (1) the existing canonical `grapes.yaml` "Bonarda" entry (qid Q136078247) is the Charbono/Douce Noir grape used in Argentina, not native here; (2) "Bonarda" on an Oltrepò Pavese or Gutturnio (Emilia) label is ampelographically **Croatina** — I used `Croatina` in those `grapes:` fields instead; (3) "Bonarda Novarese", used in Alto Piemonte (Boca/Fara/Sizzano/Bramaterra blends), is ampelographically **Uva Rara**, which I added as its own new grape with "Bonarda Novarese" as a synonym; (4) there is also a distinct, rarer "Bonarda Piemontese." I did not touch the existing canonical "Bonarda" entry — flagging this for a human to decide whether it needs a disambiguating rename, since as it stands a tagger reading "Bonarda" on an Oltrepò Pavese label would resolve to the wrong (Argentine) grape.
- **Terrano / Refosco dal Peduncolo Rosso**: the existing canonical `grapes.yaml` "Refosco" entry already lists "Teran"/"Refošk"/"Refosk"/"Terrano" as synonyms, treating them as one grape. Wine-Searcher, by contrast, lists "Teran" as its own distinct "Croatian Red Grape" (`wine-searcher.com/grape-2278-teran`), and several ampelographers treat the Kras/Carso "Teran"/Refosco d'Istria as a different clone/variety from Refosco dal Peduncolo Rosso proper. I used "Terrano" in the new `Carso` DOC's `grapes:` field since that's the existing canonical label, but flag this identity question for a human — I did not add a competing grape entry since that would just collide.
- **Lambrusco is at least four distinct VIVC varieties** (di Sorbara, Grasparossa, Salamino, Maestri) folded into one canonical "Lambrusco" grape with the others as mere synonyms. I used the specific compound labels ("Lambrusco Grasparossa", "Lambrusco Salamino") in the new Emilia-Romagna DOC `grapes:` fields, which are valid existing synonym strings, but did not try to split the canonical grape entry — that's a bigger change than a research file should make unasked, and I'd rather flag it.
- **Pignoletto / Grechetto Gentile vs. the existing canonical "Grechetto"**: I added `Pignoletto` as a brand-new grape (not as a synonym of the existing `Grechetto`) because I could not confirm whether the existing "Grechetto" entry is meant to represent Umbria's "Grechetto di Orvieto" (= Pulcinculo, a different variety) or Emilia's Pignoletto/Grechetto Gentile — these are two different grapes that happen to share the word "Grechetto." Safer to add new than guess which one the existing entry means.
- **Moscato di Scanzo**: added as its own new (red) grape rather than a synonym of Moscato Bianco. Scanzo is unusually a *red* sweet Moscato; sources are not fully consistent on whether it's ampelographically distinct from Moscato Bianco or a red-berried clone of it, so I kept it separate rather than guess.
- **Malvasia di Casorzo**: added as a new (red, aromatic) grape distinct from the existing canonical "Malvasia Nera," used by both `Malvasia di Casorzo` and `Malvasia di Castelnuovo Don Bosco` DOCs — another case of "Malvasia" naming several unrelated grapes, per the brief's warning.
- **Colli Romagna Centrale**'s parent: I filed it under `Emilia-Romagna` directly rather than under the new `Romagna` DOC, since I could not confirm from a secondary source whether it is legally a sub-zone of Romagna DOC or an independent, older registration that predates the 2011 Romagna-DOC consolidation. Flagging for a human check against the actual disciplinare.
- **Reno DOC's `grapes:`**: I tentatively listed `Pignoletto`, since that's Reno DOC's best-known current typology, but the disciplinare also covers other varietals; medium confidence only.
- **Valsusa DOC's `grapes:`**: the disciplinare names five varieties collectively (Avanà, Barbera, Becuet, Dolcetto, Neretta Cuneese, min. 60% combined). I listed only the three genuinely local ones (Avanà, Becuet, Neretta Cuneese) as "principal" and left out Barbera/Dolcetto, which are common Piedmont grapes covered elsewhere — a judgment call about what counts as this DOC's defining variety, worth a second look.
- **Prié Blanc's existing grapes.yaml synonym "Blanc de Morgex"** and my new region entry "Blanc de Morgex et de la Salle" are close but not identical strings, so no validator collision — but a human should note the grape synonym and the region name are two names for closely related things (the grape is named after the place), which is exactly the pattern the brief warns about for producer/place names as grape synonyms. I did not change the existing grape entry.

## Label string → canonical (real-world forms)

| Label string | Kind | Canonical | Where seen |
|---|---|---|---|
| "Moscato d'Asti" | region | Asti | `https://www.wine-searcher.com/regions-moscato+d'asti` |
| "Gavi di Gavi" | region | Gavi | `https://www.wine-searcher.com/regions-gavi+-+cortese+di+gavi` |
| "Prosecco di Valdobbiadene" | region | Conegliano Valdobbiadene | `https://www.quattrocalici.it/regione/veneto/denominazioni/` |
| "Ripasso" | region | Valpolicella Ripasso | `https://www.wine-searcher.com/regions-valpolicella+ripasso` |
| "Soave Classico" | region | Soave Classico | `https://www.quattrocalici.it/regione/veneto/denominazioni/` |
| "Südtirol" | region | Alto Adige | `https://www.quattrocalici.it/regione/trentino-alto-adige/denominazioni/` |
| "Kalterersee" | region | Lago di Caldaro | `https://www.quattrocalici.it/regione/trentino-alto-adige/denominazioni/` |
| "Sfursat" | region | Sforzato di Valtellina | `https://www.quattrocalici.it/regione/lombardia/denominazioni/` |
| "Trentodoc" | region | Trento | `https://www.wine-searcher.com/regions-trentodoc` |
| "Weinberg Dolomiten" | region | Vigneti delle Dolomiti | `https://www.quattrocalici.it/regione/trentino-alto-adige/denominazioni/` |
| "Terradeiforti" | region | Valdadige Terradeiforti | `https://www.quattrocalici.it/regione/trentino-alto-adige/denominazioni/` |
| "Grumello" | region | Grumello | `https://www.wine-searcher.com/regions-valtellina+superiore+grumello` |
| "Cartizze" | region | Cartizze | `https://www.wine-searcher.com/regions-superiore+di+cartizze` |
| "Chiavennasca" | grape | Nebbiolo | existing library synonym, corroborated by `https://www.wine-searcher.com/regions-valtellina+superiore+grumello` |
| "Spanna" | grape | Nebbiolo | existing library synonym |
| "Vernatsch" | grape | Schiava | existing library synonym |
| "Malvoisie" (Nus) | grape | Pinot Gris | `https://en.wikipedia.org/wiki/Valle_d%27Aosta_DOC` |
| "Friularo" | grape | Raboso | `https://www.quattrocalici.it/regione/veneto/denominazioni/` |
| "Fior d'Arancio" | grape | Moscato Giallo | `https://www.quattrocalici.it/regione/veneto/denominazioni/` |
| "Prunent" | grape | Nebbiolo | `https://www.quattrocalici.it/regione/piemonte/denominazioni/` |
| "Grechetto Gentile" | grape | Pignoletto (new grape) | `https://www.quattrocalici.it/regione/emilia-romagna/denominazioni/` |
| "Turbiana" | grape | Verdicchio | existing library synonym (used on Lugana labels) |
| "Rebula" | grape | Ribolla Gialla | `https://www.wine-searcher.com/grape-406-ribolla-gialla` (existing library synonym; Slovenian spelling) |
| "Teran" | grape | Refosco | `https://www.wine-searcher.com/grape-2278-teran` — see Uncertain calls above; Wine-Searcher itself treats this as a separate grape |
| "Bonarda Novarese" | grape | Uva Rara (new grape) | `https://glossary.wein.plus/bonarda-novarese` |

## Validation

```
$ .venv/bin/python -c "import yaml,sys; [print(f, len(yaml.safe_load(open(f)))) for f in sys.argv[1:]]" fermentation/library_mcp/seed/research/it-n.regions.yaml fermentation/library_mcp/seed/research/it-n.grapes.yaml
fermentation/library_mcp/seed/research/it-n.regions.yaml 250
fermentation/library_mcp/seed/research/it-n.grapes.yaml 21
```

Also checked by hand (not part of the required command): no duplicate (name, country) pairs, no dangling or cyclical parents, no name/synonym collisions within `it-n.regions.yaml`, no new synonym collides with a *different* canonical entry (the 8 flagged collisions were all the deliberate un-foldings described above), no new grape or grape-synonym collides with canonical `grapes.yaml`, and every `grapes:` reference in `it-n.regions.yaml` resolves to a label in canonical `grapes.yaml` or the new `it-n.grapes.yaml` (this caught one real gap: **Albana was missing from canonical `grapes.yaml` entirely** despite being a well-known DOCG-namesake grape — added as new).

## Review (main session, 2026-09-26)

- **Removed the separate `delle Venezie IGT` entry.** Its name carries the
  classification. The lookup strips "IGT" from either end and resolves to
  the `delle Venezie` DOC, and Trevenezie IGT stays as its own entry.
- **Removed `Malvasia di Schierano` as a synonym of Malvasia di Casorzo.**
  VIVC lists them as distinct varieties. Removed the `grapes:` of Malvasia
  di Castelnuovo Don Bosco too (its grape is Schierano, which is not in the
  library), rather than point it at the wrong grape.
- Open grape-identity questions (Bonarda, Terrano/Refosco, the
  Lambruscos, Grechetto) are carried to a later grape-reconciliation pass;
  the Grechetto note was passed to it-c.
- Merged 2026-09-27. Added the synonyms "Sfursat" (Sforzato di Valtellina) and "Prosecco di Valdobbiadene" (Conegliano Valdobbiadene, the name before 2009).
