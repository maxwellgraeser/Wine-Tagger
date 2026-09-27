# ch: Switzerland

**Country:** CH. **Slice:** all of Switzerland, one agent. (The plan's
SMALL agent is split in two: ch, and uy-ca. Switzerland alone reaches
about 60 entries.)

**You own:** every existing CH entry and everything under it:
- **The six wine regions** as parents: Valais, Vaud, Geneva, Three Lakes
  (Drei-Seen-Land: Neuchâtel, Bielersee, Vully), German-speaking
  Switzerland (Deutschschweiz), Ticino. Keep the existing names (`Geneva`
  in English, `Valais`, `Vaud`, `Ticino`, `Neuchâtel`) and carry the other
  languages as synonyms (Genève, Wallis, Waadt, Tessin).
- **Cantonal AOCs** (each canton has one), classification `AOC`, children
  of their region: e.g. Neuchâtel, Bielersee, Vully, Zürich, Schaffhausen,
  Graubünden, Aargau, Thurgau, St. Gallen, Basel-Landschaft…
- **Vaud's appellations:** Chablais, Lavaux, La Côte, Côtes de l'Orbe,
  Bonvillars, Vully (Vaud side); the Grands Crus Dézaley and Calamin (under
  Lavaux); and the Lavaux and Chablais villages labels use (Épesses,
  Villette, Saint-Saphorin, Chardonne, Yvorne, Aigle, Ollon, Bex…).
- **Valais's communes** that labels use (Fully, Chamoson, Vétroz, Salgesch
  / Salquenen, Sion, Leytron, Conthey, Visperterminen…), classification
  `Gemeinde`. Aim for 10–15.
- **Geneva's areas:** Mandement (Satigny, Dardagny), Entre Arve et Rhône,
  Entre Arve et Lac; its premier cru villages only if labels use them.

Aim for 50–70 entries.

Not regions, keep them out: Dôle, Salvagnin, Goron (wine names), Grand Cru
levels other than the named Vaud Grands Crus, Premier Grand Cru.

**Homonyms, record in the `.md`:** Neuchâtel (canton / lake / city: one
entry), Geneva, Ticino / Italian Canton Ticino (Merlot del Ticino).

**Not yours:** nothing else.

**Official register:** the Federal Office for Agriculture's list of
cantonal AOCs, then swisswine.ch and the cantonal regulations (Vaud's
Règlement sur les vins vaudois) for the lower levels.

**`grapes:` field:** only where the cantonal rules name grapes for an
appellation (e.g. Dézaley and Calamin: Chasselas). Otherwise none.

**Grapes file:** Swiss names missing from `grapes.yaml`. Run
`context --grape` on each first; add only missing grapes and missing
synonyms. Chasselas, Petite Arvine, Humagne, Cornalin, Heida and Gamaret
exist: check synonyms (Fendant and Perlan for Chasselas; Païen and
Savagnin Blanc for Heida; Humagne Blanche vs Humagne Rouge are different
varieties). Candidates: Amigne, Rèze, Lafnetscha, Himbertscha, Completer,
Garanoir, Diolinoir, Mara, Divico, Räuschling, Humagne Rouge if missing.
Cornalin (Rouge du Pays) vs Cornalin d'Aoste (Humagne Rouge): check VIVC.
