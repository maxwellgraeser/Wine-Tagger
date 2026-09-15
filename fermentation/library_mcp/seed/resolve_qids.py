"""Resolve allowlist names to Wikidata QIDs and write `allowlist/qids.lock.yaml`.

Dev-time tool, run when grapes.yaml / regions.yaml change:

    python -m fermentation.library_mcp.seed.resolve_qids            # fill missing
    python -m fermentation.library_mcp.seed.resolve_qids --all      # re-resolve everything
    python -m fermentation.library_mcp.seed.resolve_qids --report   # print unresolved / low-confidence

Resolution goes through the SPARQL endpoint's MWAPI EntitySearch service
(batched, ~30 names per query) rather than the wbsearchentities REST API,
which rate-limits bursts hard. Each candidate is scored by its P31 class:

  grapes  : must be an instance of grape variety (Q958314); exact label match
            beats prefix match; plain varieties beat sports/mutations.
  regions : wine-typed classes (wine-producing region, AVA, appellation,
            AOC/DOC/DOCG-as-wine, vineyard) beat administrative units, which
            beat plain valleys; exact label match (with or without an
            "AVA"/"DOC"/"AOC" suffix) is required. Regions that cannot be
            matched are written as `null` in the lock -- that is allowed.

The lock records label + description for every pick so a wrong choice is
visible in a `git diff`. Pin `qid:` in the YAML to override the resolver.
"""

from __future__ import annotations

import argparse
import sys
import time
import unicodedata
from pathlib import Path

import requests
import yaml

from .allowlist import (
    Allowlist,
    GrapeEntry,
    LOCK_PATH,
    RegionEntry,
    load_allowlists,
    region_lock_key,
)

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "WineWarehouseDDD/0.1 (library_mcp seed; github.com/maxwellgraeser) python-requests"
HEADERS = {"Accept": "application/sparql-results+json", "User-Agent": USER_AGENT}
BATCH = 24
PAUSE = 1.5  # seconds between SPARQL calls

GRAPE_VARIETY = "Q958314"
SPORT = "Q1751160"                      # bud sport / mutation
WINE_REGION_CLASSES = {
    "Q2140699",   # wine-producing region
    "Q166247",    # American Viticultural Area
    "Q2858704",   # appellation
    "Q1565828",   # appellation d'origine contrôlée
    "Q654824",    # DOC
    "Q2305591",   # DOCG
    "Q282",       # wine (Italian DOC/DOCG and many AOCs are modelled as wines)
    "Q22715",     # vineyard
}
ADMIN_HINTS = ("region", "province", "state", "county", "department", "comune",
               "commune", "municipality", "district", "canton", "prefecture",
               "autonomous community", "comarca", "historical province")
REGION_SUFFIXES = (" ava", " aoc", " aop", " doc", " docg", " do", " dop", " igt",
                   " igp", " wine region", " wine", " (wine)", " (wine region)")


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return " ".join(s.lower().split())


def _sparql(query: str) -> list[dict]:
    delay = 3.0
    for _ in range(5):
        r = requests.get(WIKIDATA_ENDPOINT, params={"query": query}, headers=HEADERS, timeout=180)
        if r.status_code == 200:
            return r.json()["results"]["bindings"]
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(delay)
            delay *= 2
            continue
        r.raise_for_status()
    raise RuntimeError(f"SPARQL failed after retries (last status {r.status_code})")


def _search_batch(terms: list[str]) -> dict[str, list[dict]]:
    """term -> [{qid, label, description, classes:[qid...], class_labels:[...]}]"""
    values = " ".join('"%s"' % t.replace('"', '\\"') for t in terms)
    q = f"""
SELECT ?term ?item ?itemLabel ?itemDescription ?ord
       (GROUP_CONCAT(DISTINCT ?cls; SEPARATOR="|") AS ?classes)
       (GROUP_CONCAT(DISTINCT ?clsLabel; SEPARATOR="|") AS ?classLabels)
WHERE {{
  VALUES ?term {{ {values} }}
  SERVICE wikibase:mwapi {{
    bd:serviceParam wikibase:endpoint "www.wikidata.org" ;
                    wikibase:api "EntitySearch" ;
                    mwapi:search ?term ;
                    mwapi:language "en" ;
                    mwapi:limit "8" .
    ?item wikibase:apiOutputItem mwapi:item .
    ?ord wikibase:apiOrdinal true .
  }}
  OPTIONAL {{ ?item wdt:P31 ?cls .
             OPTIONAL {{ ?cls rdfs:label ?clsLabel . FILTER(LANG(?clsLabel)="en") }} }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}} GROUP BY ?term ?item ?itemLabel ?itemDescription ?ord
"""
    out: dict[str, list[dict]] = {t: [] for t in terms}
    for b in _sparql(q):
        term = b["term"]["value"]
        qid = b["item"]["value"].rsplit("/", 1)[1]
        strip = lambda s: [x.rsplit("/", 1)[1] for x in s.split("|") if x]  # noqa: E731
        out.setdefault(term, []).append({
            "qid": qid,
            "label": (b.get("itemLabel") or {}).get("value", ""),
            "description": (b.get("itemDescription") or {}).get("value", ""),
            "classes": strip((b.get("classes") or {}).get("value", "")),
            "class_labels": [x for x in (b.get("classLabels") or {}).get("value", "").split("|") if x],
            "supers": [],
            "ord": int((b.get("ord") or {}).get("value", "99")),
        })
    for v in out.values():
        v.sort(key=lambda c: c["ord"])
    return out


def _exact_grape_matches(names: list[str]) -> dict[str, dict]:
    """folded name -> {qid,label,description} for names that equal (case-
    and accent-insensitively) the English label or an altLabel of an item
    typed grape variety. Deterministic; preferred over ranked search."""
    values = " ".join('"%s"' % n.replace('"', '\\"') for n in names)
    rows = _sparql(f"""
SELECT ?g ?gLabel ?gDescription ?l WHERE {{
  VALUES ?want {{ {values} }}
  ?g wdt:P31/wdt:P279* wd:{GRAPE_VARIETY} .
  ?g rdfs:label|skos:altLabel ?l . FILTER(LANG(?l) = "en")
  FILTER(LCASE(STR(?l)) = LCASE(?want))
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
""")
    out: dict[str, dict] = {}
    for b in rows:
        key = _fold(b["l"]["value"])
        cand = {"qid": b["g"]["value"].rsplit("/", 1)[1],
                "label": (b.get("gLabel") or {}).get("value", ""),
                "description": (b.get("gDescription") or {}).get("value", ""),
                "is_label": _fold((b.get("gLabel") or {}).get("value", "")) == key}
        prev = out.get(key)
        # prefer an item whose *label* is the name over an altLabel hit
        if prev is None or (cand["is_label"] and not prev["is_label"]):
            out[key] = cand
    return out


# ---------- scoring ----------

def _is_grape_candidate(c: dict) -> bool:
    if GRAPE_VARIETY in c["classes"] or GRAPE_VARIETY in c["supers"]:
        return True
    cl = " ".join(c["class_labels"]).lower()
    desc = c["description"].lower()
    return ("grape" in cl or "vitis" in cl) or ("grape" in desc and "wine" in desc) \
        or desc.endswith("grape variety") or desc.startswith("grape variety") \
        or desc in ("varietal", "variety of grape", "wine grape")


def _pick_grape(entry: GrapeEntry, cands: list[dict]) -> tuple[dict | None, str]:
    want = _fold(entry.name)
    syns = {_fold(s) for s in entry.synonyms}
    scored: list[tuple[int, dict]] = []
    for c in cands:
        if not _is_grape_candidate(c):
            continue
        lab = _fold(c["label"])
        s = 10
        if lab == want:
            s += 20
        elif lab in syns:
            s += 15            # Wikidata's preferred label is one of OUR synonyms
        elif lab.startswith(want + " ") or lab.endswith(" " + want):
            s += 3
        if SPORT in c["classes"] or "mutation" in c["description"].lower():
            s -= 5
        scored.append((s, c))
    if not scored:
        return None, "no grape-variety candidate"
    scored.sort(key=lambda x: (-x[0], x[1]["ord"]))
    best = scored[0]
    if best[0] < 25:
        return best[1], "inexact label match -- review"
    return best[1], "ok"


def _pick_region(entry: RegionEntry, cands: list[dict]) -> tuple[dict | None, str]:
    want = _fold(entry.name)
    scored: list[tuple[int, dict]] = []
    for c in cands:
        lab = _fold(c["label"])
        exact = lab == want
        suffixed = any(lab == want + suf for suf in REGION_SUFFIXES) or any(
            lab.endswith(suf) and lab[: -len(suf)] == want for suf in REGION_SUFFIXES
        )
        if not (exact or suffixed):
            continue
        classes = set(c["classes"]) | set(c["supers"])
        desc = c["description"].lower()
        cl = " ".join(c["class_labels"]).lower()
        s = 0
        if classes & WINE_REGION_CLASSES or "wine" in cl or "vineyard" in cl or "appellation" in cl \
                or "wine" in desc or "viticultural" in desc:
            s += 30
        elif entry.classification is None and (any(h in cl for h in ADMIN_HINTS) or "valley" in cl):
            # A top-level/administrative region (Piedmont, California, Bekaa
            # Valley) legitimately IS the admin entity. An appellation
            # (AOC/DOC/AVA...) is not its namesake commune -> require wine class.
            s += 15
        else:
            continue  # family names, ships, asteroids, namesake communes...
        if "wine" in desc or "appellation" in desc or "viticultural" in desc:
            s += 5
        if suffixed and not exact:
            s += 3   # "Napa Valley AVA" over "Napa Valley (valley)"
        scored.append((s, c))
    if not scored:
        return None, "no plausible candidate"
    scored.sort(key=lambda x: (-x[0], x[1]["ord"]))
    best = scored[0]
    return best[1], ("ok" if best[0] >= 30 else "non-wine class -- review")


# ---------- driver ----------

def _search_terms_for_region(r: RegionEntry) -> list[str]:
    terms = [r.name, f"{r.name} wine region"]
    if r.classification and r.classification.isupper() and len(r.classification) <= 4:
        terms.append(f"{r.name} {r.classification}")       # "Fixin AOC", "Napa Valley AVA"
    return terms


def _search_terms_for_grape(g: GrapeEntry) -> list[str]:
    return [g.name, f"{g.name} grape"]


def resolve(al: Allowlist, *, redo_all: bool, log=print) -> dict:
    lock_path = LOCK_PATH
    existing = yaml.safe_load(lock_path.read_text(encoding="utf-8")) if lock_path.exists() else {}
    existing = existing or {}
    lock = {"grapes": dict(existing.get("grapes") or {}), "regions": dict(existing.get("regions") or {})}

    # ---- grapes: pass 1, exact label/altLabel match among grape varieties ----
    todo_g = [g for g in al.grapes if not g.qid and (
        redo_all or g.name not in lock["grapes"] or lock["grapes"].get(g.name) is None
        or (lock["grapes"][g.name] or {}).get("note") != "ok")]
    if todo_g:
        log(f"[grapes] exact-label pass over {len(todo_g)} entries")
        try:
            exact = _exact_grape_matches([n for g in todo_g for n in [g.name, *g.synonyms]])
        except Exception as exc:  # noqa: BLE001
            log(f"  !! exact-label pass failed ({exc}); falling back to search")
            exact = {}
        for g in todo_g:
            hit = exact.get(_fold(g.name))
            if hit is None:                     # a synonym may be Wikidata's label
                for syn in g.synonyms:
                    hit = exact.get(_fold(syn))
                    if hit:
                        break
            if hit:
                lock["grapes"][g.name] = {"qid": hit["qid"], "label": hit["label"],
                                          "description": hit["description"], "note": "ok"}
        write_lock(_pruned(lock, al))

    # ---- grapes: pass 2, entity search for whatever is still not ok ----
    todo_g = [g for g in al.grapes if not g.qid and (
        redo_all or g.name not in lock["grapes"] or lock["grapes"].get(g.name) is None
        or (lock["grapes"][g.name] or {}).get("note") != "ok")]
    log(f"[grapes] {len(todo_g)} to resolve")
    for i in range(0, len(todo_g), BATCH // 2):
        chunk = todo_g[i:i + BATCH // 2]
        terms: list[str] = []
        for g in chunk:
            terms.extend(_search_terms_for_grape(g))
        try:
            res = _search_batch(list(dict.fromkeys(terms)))
        except Exception as exc:  # noqa: BLE001
            log(f"  !! batch failed ({exc}); leaving {[g.name for g in chunk]} unresolved")
            res = {}
        for g in chunk:
            cands: list[dict] = []
            seen: set[str] = set()
            for t in _search_terms_for_grape(g):
                for c in res.get(t, []):
                    if c["qid"] not in seen:
                        seen.add(c["qid"])
                        cands.append(c)
            pick, note = _pick_grape(g, cands)
            if pick is None:
                lock["grapes"][g.name] = None
                log(f"  !! {g.name}: {note}")
            else:
                lock["grapes"][g.name] = {
                    "qid": pick["qid"], "label": pick["label"],
                    "description": pick["description"], "note": note,
                }
                if note != "ok":
                    log(f"  ?? {g.name} -> {pick['qid']} {pick['label']!r}: {note}")
        write_lock(_pruned(lock, al))
        time.sleep(PAUSE)

    # ---- regions ----
    todo_r = [r for r in al.regions if not r.qid and (redo_all or region_lock_key(r) not in lock["regions"])]
    log(f"[regions] {len(todo_r)} to resolve")
    for i in range(0, len(todo_r), BATCH // 2):
        chunk = todo_r[i:i + BATCH // 2]
        terms: list[str] = []
        for r in chunk:
            terms.extend(_search_terms_for_region(r))
        try:
            res = _search_batch(list(dict.fromkeys(terms)))
        except Exception as exc:  # noqa: BLE001
            log(f"  !! batch failed ({exc}); leaving {[r.name for r in chunk]} unresolved")
            res = {}
        for r in chunk:
            cands: list[dict] = []
            seen: set[str] = set()
            for t in _search_terms_for_region(r):
                for c in res.get(t, []):
                    if c["qid"] not in seen:
                        seen.add(c["qid"])
                        cands.append(c)
            pick, note = _pick_region(r, cands)
            key = region_lock_key(r)
            if pick is None:
                lock["regions"][key] = None
                log(f"  -- {key}: {note}")
            else:
                lock["regions"][key] = {
                    "qid": pick["qid"], "label": pick["label"],
                    "description": pick["description"], "note": note,
                }
                if note != "ok":
                    log(f"  ?? {key} -> {pick['qid']} {pick['label']!r}: {note}")
        write_lock(_pruned(lock, al))
        time.sleep(PAUSE)

    return _pruned(lock, al)


def _pruned(lock: dict, al: Allowlist) -> dict:
    """Drop lock entries for names no longer in the YAMLs; sort for stable diffs."""
    gnames = {g.name for g in al.grapes if not g.qid}          # pinned entries need no lock row
    rkeys = {region_lock_key(r) for r in al.regions if not r.qid}
    return {
        "grapes": {k: v for k, v in sorted(lock["grapes"].items()) if k in gnames},
        "regions": {k: v for k, v in sorted(lock["regions"].items()) if k in rkeys},
    }


def write_lock(lock: dict, path: Path = LOCK_PATH) -> None:
    header = (
        "# GENERATED by seed/resolve_qids.py -- do not hand-edit values here.\n"
        "# To override a pick, set `qid:` on the entry in grapes.yaml / regions.yaml.\n"
        "# `null` = resolver found nothing plausible (allowed for regions, fatal for grapes).\n"
    )
    body = yaml.safe_dump(lock, allow_unicode=True, sort_keys=True, width=100)
    path.write_text(header + body, encoding="utf-8")


def report(al: Allowlist) -> int:
    bad = 0
    for g in al.grapes:
        if al.grape_qid(g) is None:
            print(f"grape unresolved: {g.name}")
            bad += 1
    for r in al.regions:
        if al.region_qid(r) is None:
            print(f"region unresolved (allowed): {region_lock_key(r)}")
    import yaml as _y
    raw = _y.safe_load(LOCK_PATH.read_text(encoding="utf-8")) if LOCK_PATH.exists() else {}
    for sec in ("grapes", "regions"):
        for k, v in sorted(((raw or {}).get(sec) or {}).items()):
            if v and v.get("note") != "ok":
                print(f"{sec[:-1]} review: {k} -> {v['qid']} {v.get('label')!r} ({v.get('description')!r}): {v['note']}")
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--all", action="store_true", help="re-resolve every entry, not just missing ones")
    ap.add_argument("--report", action="store_true", help="only print unresolved entries")
    args = ap.parse_args(argv)

    al = load_allowlists(require_qids=False)
    if args.report:
        return report(al)
    lock = resolve(al, redo_all=args.all, log=lambda m: print(m, file=sys.stderr))
    write_lock(lock)
    print(f"[ok] wrote {LOCK_PATH}", file=sys.stderr)
    al = load_allowlists(require_qids=False)
    return report(al)


if __name__ == "__main__":
    raise SystemExit(main())
