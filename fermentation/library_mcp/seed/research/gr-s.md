Status: complete

# gr-s: Greece, south and Aegean — research notes

## Sources

- **eAmbrosia** (EU register, agriculture.ec.europa.eu/geographical-indications-register) —
  the register itself is a JS single-page app that neither `curl` nor
  WebFetch can render, so it could not be scraped directly. Counts below
  are cross-checked instead against **Wines of Greece**
  (winesofgreece.org), the Greek national wine body and the source the
  scope note names as the fallback; every PDO/PGI page cited below was
  fetched individually and returned HTTP 200 on 2026-09-27.
- Wines of Greece, "PDO" pages for each appellation (one URL per entry,
  see `gr-s.regions.yaml`), fetched 2026-09-27.
- Wines of Greece, "PGI Wines of Greece" overview article and individual
  PGI pages (Pisatis, Letrina, Trifilia, Pylia, Tegea, Klimenti,
  Slopes of Egialia, Kissamos, Kos, Thapsana), fetched 2026-09-27.
- Wikipedia (Peloponnese, Crete) for the plain geographic parent entries
  that carry no appellation source of their own.
- wein.plus glossary and Wikipedia for individual grape pages (Thrapsathiri,
  Dafni, Plyto, Monemvasia).

## Counts

- **PDOs: 22 of 22** in scope, per the scope note's own PDO list (which
  matches Wines of Greece's PDO pages): Nemea, Mantinia, Patras,
  Mavrodaphne of Patras, Muscat of Patras, Muscat of Rio Patras,
  Monemvasia-Malvasia, Santorini, Paros, Malvasia Paros, Rhodes, Muscat of
  Rhodes, Samos, Lemnos, Muscat of Lemnos, Archanes, Dafnes, Peza, Sitia,
  Chandakas-Candia, Malvasia Chandakas-Candia, Malvasia Sitia. All present.
- **PGIs: 24** — 4 regional (Peloponnese, Crete, Aegean Sea; Central
  Greece/Macedonia/Epirus/Thessalia/Thrace are gr-n's) + 20 district/area
  in scope: Argolida, Arkadia, Achaia, Ilia, Korinthos, Lakonia, Messinia,
  Heraklion, Lasithi, Chania, Rethymno, Cyclades, Dodecanese, Lesvos,
  Chios, Ikaria, plus the finer area-tier PGIs found while cross-checking
  the coverage note ("41 regions looks low"): Slopes of Aigialia (Achaia),
  Pisatis and Letrinoi (Ilia), Trifilia and Pylia (Messinia), Tegea
  (Arkadia), Klimenti (Korinthos), Kissamos (Chania), Kos (Dodecanese),
  Thapsana (Cyclades). That brings the file from 41 to **51 regions**.
- Left out: **"Slopes of Ampelos"** (Samos) — this phrase turned up in one
  search-engine summary as if it were a PGI, but every attempt to find an
  official page or Greek-language source for a distinct "ΠΓΕ Πλαγιές
  Αμπέλου" failed; all sources instead describe Mount Ampelos as a
  physical feature of the (already-listed) PDO Samos vineyard. Treated as
  a probable hallucination and not added — flagged here instead of
  guessed.
- Muscat of Alexandria for Lemnos: confirmed distinct from the Muscat
  Blanc à Petits Grains used for Samos/Patras/Rhodes, per the scope note's
  own instruction; both already existed correctly split in the earlier
  draft.

## Changes to existing entries

- **Santorini**: added `parent: "Cyclades"` (was parentless in
  `regions.yaml`) and removed the synonym `"Santorini PDO"` — a
  classification-word tail the lookup already strips, flagged by `check`.
- **Samos**: added `parent: "Aegean Sea"` (was parentless) — Samos sits
  under the PGI Aegean Sea regional tier the same way Lemnos does.
- **Peloponnese** and **Crete**: added a `source` (Wikipedia) to clear a
  `check` warning; these are plain geographic entries with no
  appellation register of their own.
- No renames.

## Homonyms

- **Peloponnese, Crete, Rhodes, Paros** and similar Greek place names are
  not known to collide with regions in other countries in this library.
- **Malvasia** (as a grape, not a region) is a name shared by several
  distinct varieties worldwide (Malvasia di Candia, Malvasia Bianca,
  Malvasia Fina, etc.) — see the grape notes below; none of the "Malvasia
  X" PDO names here were added to `grapes.yaml` since they refer to place
  names (Malvasia Paros, Malvasia Sitia) rather than a single grape called
  "Malvasia."

## Uncertain calls

- **Monemvasia the grape vs. "Malvasia" PDO names**: PDO Monemvasia-Malvasia,
  Malvasia Paros, Malvasia Chandakas-Candia and Malvasia Sitia are all
  built on the white grape locally called **Monemvasia** (itself possibly
  ancestral to the "Malvasia" family name), blended with Assyrtiko, Athiri,
  Vidiano, Thrapsathiri and Liatiko depending on the PDO. Used "Monemvasia"
  as the grape name throughout rather than guessing it is identical to any
  specific Italian/Spanish Malvasia — flagged per the brief's identity
  rule rather than merged.
- **Area-tier PGI grapes**: Pisatis, Letrinoi, Trifilia, Pylia, Tegea,
  Klimenti, Kissamos, Kos and Thapsana all have named permitted varieties
  in their Wines of Greece pages (e.g. Thapsana: ≥70% Monemvasia white /
  ≥60% Mandilaria red; Kissamos: Romeiko-dominant). Per the scope note
  ("`grapes:` field, yes, for every PDO") and the existing convention in
  this file (no PGI entry carries a `grapes:` list), these were left
  without a `grapes:` field even though rules exist — flagging in case
  the convention should extend to PGIs.
- **Romeiko, Volitsa, Lagorthi**: local grapes named in the Kissamos and
  Slopes of Aigialia research (Romeiko dominant in Kissamos; Volitsa and
  Lagorthi native to Aigialia) are not in `grapes.yaml` and not in the
  scope's grape list, and were not added to `gr-s.grapes.yaml` since no
  region entry here references them in a `grapes:` field. Left as an open
  question rather than added speculatively.
- **Letrinoi vs. Letrini vs. Letrina**: Wines of Greece's own URL slug is
  "letrina," the page heading reads "Letrini," and the transliteration of
  Greek Λετρίνοι is "Letrinoi." Used "Letrinoi" as the canonical name
  (closest direct transliteration) with "Letrini" and "Letrina" as
  synonyms.

## Label string → canonical pairs

| label string | kind | canonical | where seen (URL) |
|---|---|---|---|
| Nemea | region | Nemea | https://winesofgreece.org/pdo/pdo-nemea/ |
| Mantineia | region | Mantinia | https://winesofgreece.org/pdo/pdo-mantinia/ |
| Patra | region | Patras | https://winesofgreece.org/pdo/pdo-patras/ |
| Mavrodafni of Patras | region | Mavrodaphne of Patras | https://winesofgreece.org/articles/production-of-mavrodaphne-of-patras/ |
| Santorini PDO | region | Santorini | https://winesofgreece.org/pdo/pdo-santorini/ |
| Thira | region | Santorini | https://winesofgreece.org/pdo/pdo-santorini/ |
| Kriti | region | Crete | https://en.wikipedia.org/wiki/Crete |
| Handakas-Candia | region | Chandakas-Candia | https://winesofgreece.org/pdo/pdo-handakas-candia/ |
| Malvassia Sitia | region | Malvasia Sitia | https://amazinggreekwines.com/glossary/greek-wine-regions/pdo-malvassia-sitia/ |
| Rodos | region | Rhodes | https://winesofgreece.org/pdo/pdo-rhodes/ |
| Limnos | region | Lemnos | https://winesofgreece.org/pdo/pdo-lemnos/ |
| Icaria | region | Ikaria | https://winesofgreece.org/pgi/pgi-ikaria/ |
| Corinthia | region | Korinthos | https://winesofgreece.org/articles/pgi-wines-of-greece/ |
| Arcadia | region | Arkadia | https://winesofgreece.org/articles/pgi-wines-of-greece/ |
| Hania | region | Chania | https://winesofgreece.org/articles/pgi-wines-of-greece/ |
| Iraklio | region | Heraklion | https://winesofgreece.org/articles/pgi-wines-of-greece/ |
| Slopes of Egialia | region | Slopes of Aigialia | https://winesofgreece.org/pgi/slopes-of-egialia/ |
| Letrini | region | Letrinoi | https://winesofgreece.org/pgi/letrina/ |
| Dodekanese | region | Dodecanese | https://winesofgreece.org/pgi/pgi-dodekanese/ |
| Aegean Islands | region | Aegean Sea | https://winesofgreece.org/pgi/pgi-aegean-sea/ |
| St. George | grape | Agiorgitiko | https://en.wikipedia.org/wiki/Agiorgitiko |
| Moscofilero | grape | Moschofilero | https://en.wikipedia.org/wiki/Moschofilero |
| Rhoditis | grape | Roditis | https://en.wikipedia.org/wiki/Roditis |
| Mavrodafni | grape | Mavrodaphne | https://winesofgreece.org/pdo/pop-muscat-of-lemnos/ |
| Amorgiano | grape | Mandilaria | https://winesofgreece.org/pdo/pdo-rhodes/ |
| Moschato Aspro | grape | Muscat Blanc à Petits Grains | https://winesofgreece.org/pdo/pdo-samos/ |
| Asyrtiko | grape | Assyrtiko | https://en.wikipedia.org/wiki/Assyrtiko |
| Monemvassia | grape | Monemvasia | https://glossary.wein.plus/monemvasia-grape-variety |

## Checker

`.venv/bin/python -m fermentation.library_mcp.seed.research.check gr-s` →
`gr-s: 51 regions, 10 grapes; 0 errors, 0 warnings (complete siblings: gr-n)`

## Review (main session, 2026-09-27)
- Tree, synonyms and grapes reviewed; accepted as written. The 10 added area PGIs, Santorini under Cyclades and Samos under Aegean Sea are fine.
- PGI-tier `grapes:` fields stay off, matching the rest of the library.
- "Monemvasia" as a grape and "Monemvasia-Malvasia" as a PDO are separate namespaces, so there is no clash.

**Merge note (2026-09-27):** Greece merged (gr-n + gr-s). Dropped for lack of a Wikidata grape item: Stavroto, Tsaoussi, Goustolidi, Mavro Messenikola (gr-n); Dafni, Plyto, Kydonitsa, Fokiano, Begleri (its only QID is a fidget toy), Mavrothiriko (gr-s). They were also removed from the Rapsani, Messenikola and other PDO `grapes:` fields. gr-s's Wikipedia sources for Dafni and Plyto return 404. Lock: Thrace (GR) nulled (shared the historical-region QID with Thrace (TR)), Epirus (GR) nulled (matched the Roman province). "PGE Halkidiki" misses because "PGE" is not a stripped classification word (lookup-code idea: add PGE/POP). Replay 0 changes, 590 tests.
