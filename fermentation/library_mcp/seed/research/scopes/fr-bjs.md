# fr-bjs: Burgundy, Beaujolais, Jura, Savoie, Bugey

**Country:** FR. **Slice:** Burgundy, Beaujolais, Jura, Savoie, Bugey.
France is split across four agents (fr-bsw, fr-bjs, fr-rpl, fr-lac).

**You own:** the existing `Burgundy`, `Beaujolais`, `Jura`, `Savoie` and
Bugey entries and everything under them, plus:
- **Burgundy, every AOC:**
  - Chablis and the Grand Auxerrois: Petit Chablis, Chablis, Chablis
    Premier Cru, Chablis Grand Cru, Irancy, Saint-Bris, Vézelay...
  - the village AOCs of the Côte de Nuits, Côte de Beaune, Côte
    Chalonnaise and Mâconnais;
  - the regional AOCs: Bourgogne, Bourgogne Aligoté, Coteaux
    Bourguignons, Bourgogne Passe-Tout-Grains, Crémant de Bourgogne, the
    Hautes-Côtes, Bourgogne Côte d'Or, Bourgogne Côte Chalonnaise...
- **Every Grand Cru AOC as its own entry**, parented to its village or
  Côte: Chambertin, Clos de Vougeot, Musigny, Romanée-Conti, La Tâche,
  Échezeaux, Corton, Corton-Charlemagne, Montrachet, Bâtard-Montrachet...
  - Today Corton and Corton-Charlemagne are wrongly synonyms of
    Aloxe-Corton. Fix that.
  - Do NOT add Premier Cru climats as entries; the lookup already strips
    "1er Cru".
- **Beaujolais:** Beaujolais, Beaujolais-Villages, and all ten crus.
- **Jura:** Arbois (+ Pupillin), Château-Chalon, L'Étoile, Côtes du Jura,
  Crémant du Jura, Macvin du Jura.
- **Savoie and Bugey:** Vin de Savoie and its crus (Apremont, Abymes,
  Chignin, Chignin-Bergeron, Jongieux, Arbin, Cruet...), Roussette de
  Savoie, Seyssel, Crémant de Savoie, Bugey (+ Cerdon, Manicle,
  Montagnieu).
- **The IGPs of these areas.**

**Not yours:**
- fr-bsw: Bordeaux, South West
- fr-rpl: Rhône, Provence, Corsica, Languedoc-Roussillon
- fr-lac: Loire, Alsace, Champagne, national IGPs, Vin de France

**Official register:** INAO (inao.gouv.fr: the appellation list and each
cahier des charges) and eAmbrosia. Count against them. The existing
convention is `classification: AOC` and `IGP`. Côtes and sub-areas without
their own AOC get no classification.

**`grapes:` field, yes, for every AOC:** the principal varieties its
cahier names. For example:
- Burgundy reds: Pinot Noir
- Chablis: Chardonnay
- Beaujolais: Gamay
- Jura: Savagnin, Chardonnay, Poulsard, Trousseau, Pinot Noir
- Savoie: Jacquère, Altesse, Mondeuse

**Grapes file:** local grapes and names missing from `grapes.yaml`. Check
Savagnin / Naturé, Altesse / Roussette, Jacquère, Bergeron (= Roussanne),
Gringet, Persan, Molette, Aligoté, César, Sacy, Melon, and Pinot Beurot (=
Pinot Gris).
