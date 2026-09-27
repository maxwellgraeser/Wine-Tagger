# Switzerland (ch) research

Status: complete

## Sources

- fr.wikipedia.org "Liste des vins AOC en Suisse" (accessed 2026-09-27) — canton-by-canton AOC list, used as the master index of cantonal AOCs.
- swisswinevaud.ch/terroirs-aoc-vaudois (Office des Vins Vaudois, redirected from ovv.ch, accessed 2026-09-27) — Vaud's six sub-regions, eight AOCs, Lavaux/Chablais communal appellations.
- swisswine.com/en/swiss-wine-regions/geneva-wine-region (accessed 2026-09-27) — Geneva's three zones (Mandement, Entre Arve et Rhône, Entre Arve et Lac).
- swisswine.com/en/swiss-wine-regions/german-speaking-switzerland-wine-region (accessed 2026-09-27) — German-speaking Switzerland canton list.
- swisswine.com/en/swiss-wine-regions/ticino-wine-region (accessed 2026-09-27) — Ticino / Merlot del Ticino, Sopraceneri/Sottoceneri.
- wine-searcher.com regional pages for Valais, Chamoson, Neuchâtel, Bielersee, Vully (accessed 2026-09-27) — Grand Cru commune list, Three Lakes structure.
- museeduvin-valais.ch grape-variety pages (Lafnetscha/Himbertscha, Rèze) (accessed 2026-09-27) — grape parentage.
- en.wikipedia.org "Cornalin d'Aoste" and "Rouge du Pays" (accessed 2026-09-27) — Cornalin/Humagne Rouge identity.
- wine-searcher.com "Mara" and "Divico" grape pages, bkwine.com Divico article (accessed 2026-09-27).


## Counts

- Regions produced: 61 (2 new top-level regions — Three Lakes, German-speaking Switzerland — plus the 5 existing; 18 cantonal AOCs under German-speaking Switzerland/Three Lakes; 12 Vaud entries incl. 2 Grand Crus and 6 villages; 12 Valais Grand Cru communes; 3 Geneva zones; 2 Ticino sub-zones).
- Official units left out: Neuchâtel's ~21 communal AOCs and its two regional AOCs (Entre-Deux-Lacs, La Béroche) — the scope asked only for the canton-level Three Lakes AOCs (Neuchâtel, Bielersee, Vully), not Neuchâtel village detail. Geneva's ~22 premier cru village names — scope said "only if labels use them"; I could not confirm consistent retail use for any single one in the time available, so none added (flagged below). Appenzell — appears in some secondary lists as a wine-producing canton but I could not confirm an actual cantonal AOC for it from a reliable source, so it is left out.
- Grapes: 8 new (Amigne, Rèze, Lafnetscha, Himbertscha, Completer, Diolinoir, Mara, Divico), 3 existing grapes given new synonyms (Chasselas: Perlan; Cornalin: Rouge du Pays; Humagne Rouge: Cornalin d'Aoste).

## Changes to existing entries

- **Vaud**: removed `Lavaux` and `La Côte` from its synonyms list and added them as separate child AOC entries instead — they are each their own appellation, not names for Vaud itself (BRIEF rule: sub-appellations are never synonyms of a parent).
- **Neuchâtel**: re-parented under a new `Three Lakes` region (previously top-level with no parent) — it is a canton-level AOC within the Three Lakes group, matching Bielersee and Vully.
- Added `classification: AOC` (or `DOC` for Ticino) to the five pre-existing top-level entries (Valais, Vaud, Geneva, Ticino, Neuchâtel), which had none — these are literally cantonal AOC/DOC names, and the field was simply missing before.

## Homonyms (record only, not cross-referenced in YAML)

- Neuchâtel: canton, city and lake all share the name — one entry covers all, as before.
- Geneva: canton, city and lake (Lac Léman shore) share the name.
- Ticino: the canton and the river; also "Merlot del Ticino" is a wine name built from the DOC name plus the grape, not a separate sub-region — not added as its own entry (like Dôle/Salvagnin/Goron).
- Vully: one AOC that physically spans canton Fribourg and canton Vaud; Vaud's own regulations also count it as one of Vaud's six sub-regions. I parented it under Three Lakes (matching the scope's framing) rather than under Vaud; flagged here per the "one parent" rule.
- La Rioja-style homonym check: none of the CH names here duplicate another country's region in this batch.

## Uncertain calls

- **Bern / Thunersee**: added beyond the scope's explicit list because the source (fr.wikipedia "Liste des vins AOC en Suisse") treats Bern as a full cantonal AOC with Bielersee and Thunersee as its two named sub-zones. Bielersee is scoped explicitly; I added Bern (as Thunersee's parent) and Thunersee itself for completeness, since dropping the parent would have left Thunersee orphaned. Reviewer should confirm Bern/Thunersee are wanted, since the scope's own list of Three-Lakes items only named Bielersee.
- **German-speaking cantons beyond the scope's named seven** (Zürich, Schaffhausen, Graubünden, Aargau, Thurgau, St. Gallen, Basel-Landschaft): added Basel-Stadt, Luzern, Solothurn, Schwyz, Glarus, Zug, Nidwalden, Obwalden, Uri on the strength of "each canton has one" in the scope text and the Wikipedia AOC list. Some of these (Uri, Obwalden, Zug) have minimal recorded vineyard area and I could not independently verify their AOC status beyond that one list — flagging in case a stricter reading of "aim for 50-70" should trim them.
- **Dézaley / Calamin grapes**: the Office des Vins Vaudois page describes these Grand Crus as Chasselas in practice ("un Dézaley est un chasselas dans la très grande majorité des cas") but I did not find the Grand Cru ordinance itself stating a mandatory 100% Chasselas rule. Listed `grapes: ["Chasselas"]` on the strength of trade description; flagging the rule's exact wording as unconfirmed.
- **Villette source**: cited the ovv.ch page (pre-redirect) since the redirected swisswinevaud.ch page did not repeat "Villette" verbatim in the fetched excerpt, though it is the well-known Lavaux village between Lutry and Cully; treat as needing a second check.
- **Geneva premier cru villages**: not added at all (see Counts) — could not confirm any one of the ~22 names in current retail use within the research budget.

## Label string → canonical

| label string | kind | canonical | where seen (URL) |
|---|---|---|---|
| Fendant | grape | Chasselas | https://www.swisswine.com/en/swiss-wine-regions/geneva-wine-region |
| Perlan | grape | Chasselas | https://www.swisswine.com/en/swiss-wine-regions/geneva-wine-region |
| Heida | grape | Savagnin | https://www.museeduvin-valais.ch/en/history-of-wine/history-of-grape-varieties |
| Païen | grape | Savagnin | https://www.museeduvin-valais.ch/en/history-of-wine/history-of-grape-varieties |
| Rouge du Pays | grape | Cornalin | https://en.wikipedia.org/wiki/Rouge_du_Pays |
| Cornalin d'Aoste | grape | Humagne Rouge | https://en.wikipedia.org/wiki/Cornalin_d%27Aoste |
| Arvine | grape | Petite Arvine | https://www.wine-searcher.com/regions-valais |
| Räuschling | grape | Räuschling | https://wineguide.wein.plus/wine-regions/german-speaking-switzerland-zurich |
| Zürichsee | region | Zürich | https://fr.wikipedia.org/wiki/Liste_des_vins_AOC_en_Suisse |
| Salquenen | region | Salgesch | https://www.wine-searcher.com/regions-valais |
| Vetroz | region | Vétroz | https://www.wine-searcher.com/regions-valais |
| Dézaley-Marsens | region | Dézaley | https://www.swisswinevaud.ch/terroirs-aoc-vaudois |
| Lac de Bienne | region | Bielersee | https://www.wine-searcher.com/regions-bielersee |
| Lac de Thoune | region | Thunersee | https://fr.wikipedia.org/wiki/Liste_des_vins_AOC_en_Suisse |
| Wallis | region | Valais | https://fr.wikipedia.org/wiki/Liste_des_vins_AOC_en_Suisse |
| Waadt | region | Vaud | https://www.swisswinevaud.ch/terroirs-aoc-vaudois |
| Genève | region | Geneva | https://www.swisswine.com/en/swiss-wine-regions/geneva-wine-region |
| Tessin | region | Ticino | https://www.swisswine.com/en/swiss-wine-regions/ticino-wine-region |
| Neuchatel | region | Neuchâtel | https://fr.wikipedia.org/wiki/Liste_des_vins_AOC_en_Suisse |
| Drei-Seen-Land | region | Three Lakes | https://www.swisswine.com/en/swiss-wine-regions/three-lakes-wine-region |
| Deutschschweiz | region | German-speaking Switzerland | https://www.swisswine.com/en/swiss-wine-regions/german-speaking-switzerland-wine-region |
| St-Saphorin | region | Saint-Saphorin | https://www.swisswinevaud.ch/terroirs-aoc-vaudois |
| Epesses | region | Épesses | https://www.swisswinevaud.ch/terroirs-aoc-vaudois |
| Siders | region | Sierre | https://www.wine-searcher.com/regions-valais |
| Grisons | region | Graubünden | https://fr.wikipedia.org/wiki/Liste_des_vins_AOC_en_Suisse |

## Review (main session, 2026-09-27)
- Hierarchy accepted, including Bern/Thunersee and the smaller German-speaking cantonal AOCs, and Vully under Three Lakes.
- Dropped "Zürichsee" from Zürich (a sub-area, not a name for the canton AOC) and "Dézaley-Marsens" from Dézaley (a lieu-dit).
- Renamed "Saviese" to "Savièse", keeping the unaccented form as a synonym.

**Merge note (2026-09-27):** Merged. Mara dropped (no Wikidata item). Lock nulled as homonyms: Three Lakes (Florida), Villeneuve (Aveyron), Villette (Yvelines). Replay 0 changes.
