# us-rest: every other US state

**Country:** US. **Slice:** every state except California, Oregon,
Washington and Idaho. The US is split across three agents (us-ca, us-pnw,
us-rest).

**You own:**
- The existing US entries for these states (New York, Virginia, Texas,
  Michigan...) and everything under them.
- A state-level entry for every state that has at least one AVA.
- Every AVA in those states, nested properly. For example:
  - New York > Finger Lakes > Seneca Lake / Cayuga Lake.
  - Long Island > North Fork of Long Island / The Hamptons.
  - Texas > Texas High Plains / Texas Hill Country > Fredericksburg in the
    Texas Hill Country.
  - Virginia > Monticello, Middleburg...
- Multi-state AVAs outside the Pacific Northwest (Lake Erie, Shenandoah
  Valley, Ohio River Valley, Mississippi Delta, Upper Mississippi River
  Valley, Texoma). Give each one parent and record the straddle in the
  `.md`.

A US state named Georgia shares its name with the country Georgia. That is
allowed now: include the state if it has AVAs, and list it under homonyms.

**Not yours:** California (us-ca); Oregon, Washington, Idaho (us-pnw).

**Official register:** TTB's list of established AVAs (ttb.gov) and 27 CFR
part 9 (ecfr.gov). Count your AVAs against it.

**`grapes:` field:** none. AVAs have no grape rules.

**Grapes file, important for this slice:** North American native and
French-American hybrid grapes that appear on commercial labels. For
example: Norton (Cynthiana), Chambourcin, Vidal Blanc, Seyval Blanc,
Traminette, Vignoles, Chardonel, Catawba, Concord, Niagara, Delaware,
Noiret, Corot Noir, Maréchal Foch, Léon Millot, Petite Pearl, Itasca,
Brianna, Muscadine / Scuppernong, Diamond, Isabella.
- `grapes.yaml` already has Marquette, Frontenac, La Crescent, Baco Noir
  and Cayuga White. Add only missing grapes and missing synonyms.
- `color` must still be one of red, white, rose, gris.

**Shenandoah Valley:** the Virginia / West Virginia AVA keeps the bare name
"Shenandoah Valley". California's AVA is officially "California Shenandoah
Valley" (us-ca, already done). Do not add a California synonym.
