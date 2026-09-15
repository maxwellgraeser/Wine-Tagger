"""Seed orchestrator for library.db.

Pipeline (see fermentation/PLAN.md, "Reseed plan"):

    1. Load + validate the allowlists (seed/allowlist/*.yaml + qids.lock.yaml).
       Any structural problem or a grape without a QID aborts before any
       network call.
    2. Build into a temp file next to library.db, from an empty schema.
    3. Canonical tier (is_canonical=1):
         countries -- one VALUES-bound SPARQL over ISO codes (P297)
         grapes    -- VALUES-bound SPARQL over the locked QIDs
                      (altLabel synonyms + origin country); color from YAML
         regions   -- straight from YAML (hierarchy/country/classification
                      are authored, not fetched); QID attached when locked
    4. Placeholder tier (is_canonical=0, skipped with --no-placeholders):
         grapes    -- every Wikidata grape variety that has an English
                      Wikipedia article and isn't already canonical
         regions   -- wine-producing regions / AVAs with an enwiki article,
                      pinned to an allowlisted country, not already canonical
    5. Wikipedia enrichment: per-country parsers contribute region_grapes
       edges and fill missing grape colours. They never mint regions.
    6. Atomic rename over library.db.

Re-running always rebuilds from scratch -- there are no migrations. The
Wikidata endpoint occasionally rate-limits; queries are paced and 429s are
retried with backoff.

Usage:
    python -m fermentation.library_mcp.seed.build_db [--offline] [--no-placeholders]
"""

from __future__ import annotations

import argparse
import importlib
import os
import pkgutil
import re
import sqlite3
import sys
import time
import unicodedata
from pathlib import Path
from typing import Iterable

try:
    import requests
except ImportError:  # offline-only mode
    requests = None  # type: ignore[assignment]

from .allowlist import Allowlist, AllowlistError, load_allowlists

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # library_mcp/
SCHEMA_PATH = PKG_ROOT / "schema.sql"
DB_PATH = PKG_ROOT / "library.db"
WIKIPEDIA_PKG = "fermentation.library_mcp.seed.wikipedia"

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIPEDIA_REST = "https://en.wikipedia.org/api/rest_v1/page/html/{title}"
USER_AGENT = (
    "WineWarehouseDDD/0.1 (library_mcp seed; github.com/maxwellgraeser) "
    "python-requests"
)
SPARQL_HEADERS = {
    "Accept": "application/sparql-results+json",
    "User-Agent": USER_AGENT,
}
WIKIPEDIA_HEADERS = {"User-Agent": USER_AGENT, "Accept": "text/html"}
SPARQL_PAUSE = 1.0          # seconds between SPARQL calls
VALUES_CHUNK = 150          # QIDs per VALUES block

GRAPE_VARIETY = "Q958314"
SOVEREIGN_STATE = "Q3624078"
COUNTRY = "Q6256"
PLACEHOLDER_REGION_CLASSES = ("Q2140699", "Q166247")   # wine-producing region, AVA


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


# ---------- schema ----------

def ensure_schema(conn: sqlite3.Connection) -> None:
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()


# ---------- helpers ----------

def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", s).strip().lower()


def _qid(uri: str | None) -> str | None:
    if not uri:
        return None
    if uri.startswith("http://www.wikidata.org/entity/"):
        return uri.rsplit("/", 1)[-1]
    return uri


def _val(b: dict, key: str) -> str | None:
    v = b.get(key)
    return v.get("value") if v else None


def _split_alts(s: str | None) -> list[str]:
    return [x.strip() for x in (s or "").split("||") if x and x.strip()]


def run_sparql(query: str, *, retries: int = 5) -> list[dict]:
    if requests is None:
        raise RuntimeError("requests is not available; cannot reach Wikidata")
    delay = 3.0
    for _ in range(retries):
        resp = requests.get(
            WIKIDATA_ENDPOINT,
            params={"query": query},
            headers=SPARQL_HEADERS,
            timeout=180,
        )
        if resp.status_code == 200:
            time.sleep(SPARQL_PAUSE)
            return resp.json()["results"]["bindings"]
        if resp.status_code in (429, 502, 503, 504):
            time.sleep(delay)
            delay *= 2
            continue
        resp.raise_for_status()
    raise RuntimeError(f"Wikidata SPARQL failed after {retries} retries")


def _chunks(items: list, n: int) -> Iterable[list]:
    for i in range(0, len(items), n):
        yield items[i:i + n]


class _SynonymGuard:
    """Tracks which folded labels are already taken (as canonical names or
    synonyms) so Wikidata altLabels can't silently alias one canonical
    entity to another. First claim wins; YAML claims are registered before
    any Wikidata data."""

    def __init__(self) -> None:
        self.owner: dict[str, int] = {}

    def claim(self, label: str, owner_id: int) -> bool:
        key = _fold(label)
        if not key:
            return False
        cur = self.owner.get(key)
        if cur is None:
            self.owner[key] = owner_id
            return True
        return cur == owner_id


# ---------- canonical: countries ----------

def ingest_countries(conn: sqlite3.Connection, al: Allowlist) -> dict[str, int]:
    """Insert allowlisted countries; returns {iso: country_id}."""
    isos = [c.iso for c in al.countries]
    values = " ".join(f'"{iso}"' for iso in isos)
    rows = run_sparql(f"""
SELECT ?c ?iso ?cLabel
       (GROUP_CONCAT(DISTINCT ?alt; SEPARATOR="||") AS ?alts)
       (GROUP_CONCAT(DISTINCT ?cls; SEPARATOR="||") AS ?classes)
WHERE {{
  VALUES ?iso {{ {values} }}
  ?c wdt:P297 ?iso .
  OPTIONAL {{ ?c wdt:P31 ?cls }}
  OPTIONAL {{ ?c skos:altLabel ?alt . FILTER(LANG(?alt) = "en") }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}} GROUP BY ?c ?iso ?cLabel
""")
    by_iso: dict[str, dict] = {}
    for b in rows:
        iso = _val(b, "iso")
        classes = set(_split_alts(_val(b, "classes")))
        classes = {_qid(c) for c in classes}
        cand = {"qid": _qid(_val(b, "c")), "label": _val(b, "cLabel"),
                "alts": _split_alts(_val(b, "alts")), "classes": classes}
        prev = by_iso.get(iso)
        # Prefer the sovereign-state item when an ISO code is shared.
        if prev is None or (SOVEREIGN_STATE in classes and SOVEREIGN_STATE not in prev["classes"]):
            by_iso[iso] = cand

    missing = [iso for iso in isos if iso not in by_iso]
    if missing:
        raise RuntimeError(f"countries: no Wikidata item for ISO codes {missing}")

    cur = conn.cursor()
    guard = _SynonymGuard()
    ids: dict[str, int] = {}
    for c in al.countries:
        cur.execute(
            "INSERT INTO countries (name, iso_code, wikidata_qid, is_canonical) VALUES (?, ?, ?, 1)",
            (c.name, c.iso, by_iso[c.iso]["qid"]),
        )
        ids[c.iso] = cur.lastrowid
        guard.claim(c.name, ids[c.iso])
    for c in al.countries:                     # YAML synonyms first
        for s in c.synonyms:
            if guard.claim(s, ids[c.iso]) and _fold(s) != _fold(c.name):
                cur.execute("INSERT OR IGNORE INTO country_synonyms (country_id, synonym) VALUES (?, ?)",
                            (ids[c.iso], s))
    for c in al.countries:                     # then Wikidata altLabels
        info = by_iso[c.iso]
        for s in [info["label"], *info["alts"]]:
            if not s or _fold(s) == _fold(c.name) or len(s) > 40:
                continue
            if guard.claim(s, ids[c.iso]):
                cur.execute("INSERT OR IGNORE INTO country_synonyms (country_id, synonym) VALUES (?, ?)",
                            (ids[c.iso], s))
    conn.commit()
    log(f"[countries] {len(ids)} canonical")
    return ids


# ---------- canonical: grapes ----------

def ingest_grapes(conn: sqlite3.Connection, al: Allowlist, country_ids: dict[str, int]) -> _SynonymGuard:
    qid_to_entry = {al.grape_qid(g): g for g in al.grapes}
    fetched: dict[str, dict] = {}
    for chunk in _chunks(list(qid_to_entry), VALUES_CHUNK):
        values = " ".join(f"wd:{q}" for q in chunk)
        rows = run_sparql(f"""
SELECT ?g ?gLabel ?origin
       (GROUP_CONCAT(DISTINCT ?alt; SEPARATOR="||") AS ?alts)
       (GROUP_CONCAT(DISTINCT ?cls; SEPARATOR="||") AS ?classes)
WHERE {{
  VALUES ?g {{ {values} }}
  OPTIONAL {{ ?g wdt:P31/wdt:P279* ?cls }}
  OPTIONAL {{ ?g wdt:P495 ?origin }}
  OPTIONAL {{ ?g skos:altLabel ?alt . FILTER(LANG(?alt) = "en") }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}} GROUP BY ?g ?gLabel ?origin
""")
        for b in rows:
            q = _qid(_val(b, "g"))
            fetched[q] = {
                "label": _val(b, "gLabel"),
                "origin": _qid(_val(b, "origin")),
                "alts": _split_alts(_val(b, "alts")),
                "classes": {_qid(c) for c in _split_alts(_val(b, "classes"))},
            }

    missing = [q for q in qid_to_entry if q not in fetched or (fetched[q]["label"] or "").startswith("Q")]
    if missing:
        raise RuntimeError(
            "grapes: these locked QIDs have no English label on Wikidata "
            f"(typo or wrong pick): {[(q, qid_to_entry[q].name) for q in missing]}"
        )
    not_grape = [q for q in qid_to_entry if GRAPE_VARIETY not in fetched[q]["classes"]]
    if not_grape:
        log("[grapes] WARNING these QIDs are not typed 'grape variety' on Wikidata: "
            + ", ".join(f"{qid_to_entry[q].name}={q}" for q in not_grape))

    qid_to_country = {row[1]: row[0] for row in conn.execute("SELECT id, wikidata_qid FROM countries")}

    cur = conn.cursor()
    guard = _SynonymGuard()
    ids: dict[str, int] = {}
    for g in al.grapes:
        q = al.grape_qid(g)
        origin_id = qid_to_country.get(fetched[q]["origin"])
        cur.execute(
            """INSERT INTO grapes (canonical_name, color, origin_country_id, wikidata_qid, is_canonical)
               VALUES (?, ?, ?, ?, 1)""",
            (g.name, g.color, origin_id, q),
        )
        ids[g.name] = cur.lastrowid
        guard.claim(g.name, ids[g.name])
    for g in al.grapes:                        # YAML synonyms first
        for s in g.synonyms:
            if guard.claim(s, ids[g.name]) and _fold(s) != _fold(g.name):
                cur.execute("INSERT OR IGNORE INTO grape_synonyms (grape_id, synonym) VALUES (?, ?)",
                            (ids[g.name], s))
    for g in al.grapes:                        # then Wikidata label + altLabels
        info = fetched[al.grape_qid(g)]
        for s in [info["label"], *info["alts"]]:
            if not s or _fold(s) == _fold(g.name) or len(s) > 40:
                continue
            if guard.claim(s, ids[g.name]):
                cur.execute("INSERT OR IGNORE INTO grape_synonyms (grape_id, synonym) VALUES (?, ?)",
                            (ids[g.name], s))
    conn.commit()
    log(f"[grapes] {len(ids)} canonical")
    return guard


# ---------- canonical: regions ----------

def ingest_regions(conn: sqlite3.Connection, al: Allowlist, country_ids: dict[str, int]) -> _SynonymGuard:
    cur = conn.cursor()
    guard = _SynonymGuard()
    ids: dict[str, int] = {}
    for r in al.regions:
        cur.execute(
            """INSERT INTO regions (name, country_id, classification, wikidata_qid, is_canonical)
               VALUES (?, ?, ?, ?, 1)""",
            (r.name, country_ids[r.country], r.classification, al.region_qid(r)),
        )
        ids[r.name] = cur.lastrowid
        guard.claim(r.name, ids[r.name])
    for r in al.regions:
        if r.parent:
            cur.execute("UPDATE regions SET parent_region_id = ? WHERE id = ?",
                        (ids[r.parent], ids[r.name]))
        for s in r.synonyms:
            if guard.claim(s, ids[r.name]) and _fold(s) != _fold(r.name):
                cur.execute("INSERT OR IGNORE INTO region_synonyms (region_id, synonym) VALUES (?, ?)",
                            (ids[r.name], s))
    conn.commit()
    with_qid = sum(1 for r in al.regions if al.region_qid(r))
    log(f"[regions] {len(ids)} canonical ({with_qid} with QID)")
    return guard


# ---------- placeholder tier ----------

def ingest_placeholder_grapes(conn: sqlite3.Connection, guard: _SynonymGuard) -> None:
    rows = run_sparql("""
SELECT ?g ?gLabel ?origin
       (GROUP_CONCAT(DISTINCT ?alt; SEPARATOR="||") AS ?alts)
WHERE {
  ?g wdt:P31 wd:Q958314 .
  ?wp schema:about ?g ; schema:isPartOf <https://en.wikipedia.org/> .
  OPTIONAL { ?g wdt:P495 ?origin }
  OPTIONAL { ?g skos:altLabel ?alt . FILTER(LANG(?alt) = "en") }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
} GROUP BY ?g ?gLabel ?origin
""")
    have = {row[0] for row in conn.execute("SELECT wikidata_qid FROM grapes WHERE wikidata_qid IS NOT NULL")}
    qid_to_country = {row[1]: row[0] for row in conn.execute("SELECT id, wikidata_qid FROM countries")}
    cur = conn.cursor()
    added = 0
    for b in rows:
        q = _qid(_val(b, "g"))
        name = _val(b, "gLabel")
        if not q or not name or name.startswith("Q") or q in have:
            continue
        if _fold(name) in guard.owner:          # would shadow a canonical name/synonym
            continue
        origin_id = qid_to_country.get(_qid(_val(b, "origin")))
        try:
            cur.execute(
                """INSERT INTO grapes (canonical_name, color, origin_country_id, wikidata_qid, is_canonical)
                   VALUES (?, NULL, ?, ?, 0)""",
                (name, origin_id, q),
            )
        except sqlite3.IntegrityError:
            continue
        gid = cur.lastrowid
        guard.claim(name, gid)
        added += 1
        for s in _split_alts(_val(b, "alts")):
            if len(s) > 40 or _fold(s) == _fold(name):
                continue
            if guard.claim(s, gid):
                cur.execute("INSERT OR IGNORE INTO grape_synonyms (grape_id, synonym) VALUES (?, ?)", (gid, s))
    conn.commit()
    log(f"[grapes] {added} placeholder")


def ingest_placeholder_regions(conn: sqlite3.Connection, guard: _SynonymGuard) -> None:
    qid_to_country = {row[1]: row[0] for row in conn.execute("SELECT id, wikidata_qid FROM countries")}
    have = {row[0] for row in conn.execute("SELECT wikidata_qid FROM regions WHERE wikidata_qid IS NOT NULL")}
    cur = conn.cursor()
    added = 0
    for cls in PLACEHOLDER_REGION_CLASSES:
        rows = run_sparql(f"""
SELECT DISTINCT ?r ?rLabel ?country WHERE {{
  ?r wdt:P31/wdt:P279* wd:{cls} .
  ?r wdt:P17 ?country .
  ?wp schema:about ?r ; schema:isPartOf <https://en.wikipedia.org/> .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
""")
        for b in rows:
            q = _qid(_val(b, "r"))
            name = _val(b, "rLabel")
            country_id = qid_to_country.get(_qid(_val(b, "country")))
            if not q or not name or name.startswith("Q") or q in have or country_id is None:
                continue
            # "Fixin AOC" / "Napa Valley AVA" must not land as a placeholder twin
            # of canonical "Fixin" / "Napa Valley".
            bare = re.sub(r"\s+(AOC|AOP|AVA|DOC|DOCG|DO|DOP|IGT|IGP|GI|WO)$", "", name, flags=re.I)
            if _fold(name) in guard.owner or _fold(bare) in guard.owner:
                continue
            try:
                cur.execute(
                    """INSERT INTO regions (name, country_id, wikidata_qid, is_canonical)
                       VALUES (?, ?, ?, 0)""",
                    (name, country_id, q),
                )
            except sqlite3.IntegrityError:
                continue
            have.add(q)
            guard.claim(name, cur.lastrowid)
            added += 1
    conn.commit()
    log(f"[regions] {added} placeholder")


# ---------- wikipedia enrichment ----------

def _fetch_wikipedia(title: str) -> str | None:
    if requests is None:
        return None
    url = WIKIPEDIA_REST.format(title=title.replace(" ", "_"))
    resp = requests.get(url, headers=WIKIPEDIA_HEADERS, timeout=60)
    if resp.status_code == 200:
        return resp.text
    log(f"[wikipedia] {title}: HTTP {resp.status_code}")
    return None


# Each country module names the Wikipedia article it wants pulled.
WIKIPEDIA_SOURCES: dict[str, str] = {
    "italy": "List_of_Italian_grape_varieties",
    "germany": "German_wine",
}


def _discover_parsers() -> Iterable[tuple[str, object]]:
    pkg = importlib.import_module(WIKIPEDIA_PKG)
    for mod_info in pkgutil.iter_modules(pkg.__path__):
        if mod_info.name.startswith("_"):
            continue
        try:
            module = importlib.import_module(f"{WIKIPEDIA_PKG}.{mod_info.name}")
        except ImportError as exc:
            log(f"[warn] skipping parser {mod_info.name}: {exc}")
            continue
        if hasattr(module, "parse"):
            yield mod_info.name, module


def _find_region(conn: sqlite3.Connection, name: str, country_id: int) -> int | None:
    row = conn.execute(
        """SELECT id FROM regions WHERE country_id = ? AND name = ? COLLATE NOCASE
           UNION
           SELECT r.id FROM regions r JOIN region_synonyms s ON s.region_id = r.id
            WHERE r.country_id = ? AND s.synonym = ? COLLATE NOCASE
           LIMIT 1""",
        (country_id, name, country_id, name),
    ).fetchone()
    return row[0] if row else None


def _find_grape(conn: sqlite3.Connection, name: str) -> int | None:
    row = conn.execute(
        """SELECT id FROM grapes WHERE canonical_name = ? COLLATE NOCASE
           UNION
           SELECT grape_id FROM grape_synonyms WHERE synonym = ? COLLATE NOCASE
           LIMIT 1""",
        (name, name),
    ).fetchone()
    return row[0] if row else None


def ingest_wikipedia(conn: sqlite3.Connection) -> None:
    """Add region_grapes edges and fill missing grape colours from the
    per-country parsers. Regions and grapes are resolved by name/synonym
    against what the canonical + placeholder passes already inserted;
    nothing new is minted (that was the v1 source of duplicate regions)."""
    cur = conn.cursor()
    for slug, module in _discover_parsers():
        article = WIKIPEDIA_SOURCES.get(slug)
        if not article:
            continue
        html = _fetch_wikipedia(article)
        if not html:
            continue
        parsed = module.parse(html)
        country_row = cur.execute(
            "SELECT id FROM countries WHERE name = ? COLLATE NOCASE", (parsed.country,)
        ).fetchone()
        if not country_row:
            continue
        country_id = country_row[0]

        edges = 0
        colored = 0
        for grape in parsed.grapes:
            gid = _find_grape(conn, grape.canonical_name)
            if gid and grape.color:
                cur.execute("UPDATE grapes SET color = ? WHERE id = ? AND color IS NULL", (grape.color, gid))
                colored += cur.rowcount
        for region_name, grape_names in parsed.region_grapes.items():
            rid = _find_region(conn, region_name, country_id)
            if not rid:
                continue
            for grape_name in grape_names:
                gid = _find_grape(conn, grape_name)
                if not gid:
                    continue
                cur.execute("INSERT OR IGNORE INTO region_grapes (region_id, grape_id) VALUES (?, ?)", (rid, gid))
                edges += cur.rowcount
        log(f"[wikipedia] {slug}: {edges} region_grapes edges, {colored} colours filled")
    conn.commit()


# ---------- main ----------

def build(db_path: Path, *, offline: bool, placeholders: bool) -> int:
    tmp = db_path.with_suffix(".db.tmp")
    if tmp.exists():
        tmp.unlink()
    conn = sqlite3.connect(tmp)
    try:
        ensure_schema(conn)
        if offline:
            conn.close()
            os.replace(tmp, db_path)
            log(f"[offline] empty schema written to {db_path}")
            return 0

        al = load_allowlists()               # raises AllowlistError on problems
        country_ids = ingest_countries(conn, al)
        grape_guard = ingest_grapes(conn, al, country_ids)
        region_guard = ingest_regions(conn, al, country_ids)
        if placeholders:
            ingest_placeholder_grapes(conn, grape_guard)
            ingest_placeholder_regions(conn, region_guard)
        ingest_wikipedia(conn)

        stats = {
            t: conn.execute(f"SELECT COUNT(*), SUM(is_canonical) FROM {t}").fetchone()
            for t in ("countries", "regions", "grapes")
        }
        conn.close()
        os.replace(tmp, db_path)
        for t, (n, canon) in stats.items():
            log(f"[ok] {t}: {n} rows ({canon} canonical)")
        log(f"[ok] library.db built at {db_path}")
        return 0
    except AllowlistError as exc:
        log(str(exc))
        return 3
    except Exception as exc:  # noqa: BLE001
        log(f"[error] seed failed mid-run: {type(exc).__name__}: {exc}")
        return 2
    finally:
        try:
            conn.close()
        except Exception:  # noqa: BLE001
            pass
        if tmp.exists():
            tmp.unlink()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build library.db from the allowlists + Wikidata")
    parser.add_argument("--offline", action="store_true",
                        help="Skip all network ingestion; write an empty schema-valid DB.")
    parser.add_argument("--no-placeholders", action="store_true",
                        help="Skip the filtered Wikidata placeholder pass (canonical tier only).")
    parser.add_argument("--out", type=Path, default=DB_PATH, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    return build(args.out, offline=args.offline, placeholders=not args.no_placeholders)


if __name__ == "__main__":
    raise SystemExit(main())
