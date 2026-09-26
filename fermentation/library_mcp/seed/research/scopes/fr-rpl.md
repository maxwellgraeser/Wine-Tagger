# fr-rpl: Rhône, Provence, Corsica, Languedoc-Roussillon

**Country:** FR. **Slice:** Rhône, Provence, Corsica, Languedoc-Roussillon.
France is split across four agents (fr-bsw, fr-bjs, fr-rpl, fr-lac).

**You own:** the existing `Rhône Valley`, `Provence`, `Corsica`,
`Languedoc-Roussillon` (with `Languedoc` and `Roussillon`) and `Pays d'Oc`
entries and everything under them, plus:
- **Rhône:**
  - the northern crus: Côte-Rôtie, Condrieu, Château-Grillet, Saint-Joseph,
    Crozes-Hermitage, Hermitage, Cornas, Saint-Péray;
  - the southern AOCs: Côtes du Rhône, Côtes du Rhône Villages with its
    named villages, Gigondas, Vacqueyras, Châteauneuf-du-Pape, Lirac,
    Tavel, Vinsobres, Rasteau, Cairanne, Beaumes de Venise, Muscat de
    Beaumes-de-Venise, Ventoux, Luberon, Grignan-les-Adhémar, Costières de
    Nîmes, Clairette de Die, Crémant de Die, Duché d'Uzès, Côtes du
    Vivarais...
- **Provence:** Côtes de Provence and its terroir designations, Coteaux
  d'Aix-en-Provence, Coteaux Varois, Bandol, Cassis, Bellet, Palette, Les
  Baux-de-Provence, Pierrevert.
- **Corsica:** Patrimonio, Ajaccio, Vin de Corse and its sub-areas, Muscat
  du Cap Corse.
- **Languedoc:** the Languedoc AOC and its crus and sub-appellations: Pic
  Saint-Loup, Terrasses du Larzac, La Clape, Faugères, Saint-Chinian,
  Minervois, Minervois-La Livinière, Corbières, Corbières-Boutenac, Fitou,
  Limoux, Blanquette de Limoux, Crémant de Limoux, Cabardès, Malepère,
  Picpoul de Pinet, Grès de Montpellier, Pézenas, Clairette du Languedoc,
  the Muscats...
- **Roussillon:** Côtes du Roussillon, Côtes du Roussillon Villages and its
  named villages, Collioure, Banyuls, Banyuls Grand Cru, Maury, Rivesaltes,
  Muscat de Rivesaltes.
- **The IGPs of these areas:** Pays d'Oc, Méditerranée, Côtes Catalanes,
  Vaucluse, Gard, Hérault, Aude, Côtes de Thongue, Collines Rhodaniennes,
  Comtés Rhodaniens, Ardèche, Alpilles, Île de Beauté...

**Known fixes:**
- Today `Côtes du Roussillon` is a synonym of `Roussillon`, but it is its
  own AOC. Make it an entry.
- Keep `Côtes du Rhône Villages` reachable as written.
- The tagger has searched "Coteaux du Languedoc Picpoul-de-Pinet". Former
  names like "Coteaux du Languedoc" (now the Languedoc AOC) belong as
  synonyms.

**Not yours:**
- fr-bsw: Bordeaux, South West
- fr-bjs: Burgundy, Beaujolais, Jura, Savoie
- fr-lac: Loire, Alsace, Champagne, national IGPs, Vin de France

**Official register:** INAO (inao.gouv.fr) and eAmbrosia. Count against
them. The existing convention is `classification: AOC` and `IGP`.

**`grapes:` field, yes, for every AOC:** the principal varieties its
cahier names. For example, Châteauneuf-du-Pape: Grenache, Syrah,
Mourvèdre...; Côtes du Roussillon: Grenache, Syrah, Carignan, Mourvèdre.

**Grapes file:** local grapes and names missing from `grapes.yaml`. Check
Nielluccio (= Sangiovese), Sciaccarellu, Vermentinu / Rolle (=
Vermentino), Tibouren, Braquet, Folle Noire, Calitor, Piquepoul,
Bourboulenc, Macabeu, Muscat à Petits Grains names, Grenache Gris,
Lladoner Pelut, Aspiran, Terret Blanc, Picardan, Vaccarèse and Muscardin.
