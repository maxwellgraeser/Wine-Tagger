"""Seed orchestrator for library.db.

Pipeline:
    1. Build the schema (idempotent).
    2. Run the three Wikidata SPARQL queries -> countries, grapes, regions.
    3. Run per-country Wikipedia parsers, fold their output into the DB
       (synonyms appended, region_grapes upserted).
    4. Dedup by Wikidata QID (UNIQUE constraints + INSERT OR IGNORE).
    5. Commit. Re-runnable: existing rows are upserted, not duplicated.

The Wikidata endpoint occasionally rate-limits; we pace queries and ride
out 429s with exponential backoff. Wikipedia HTML is fetched via the REST
API. If the network is unavailable the script still produces an empty,
schema-valid `library.db` and exits non-zero so CI can flag it.

Usage:
    python -m fermentation.library_mcp.seed.build_db [--offline]
"""

from __future__ import annotations

import argparse
import importlib
import pkgutil
import sqlite3
import sys
import time
from pathlib import Path
from typing import Iterable

try:
    import requests
except ImportError:  # offline-only mode
    requests = None  # type: ignore[assignment]

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent                       # library_mcp/
SCHEMA_PATH = PKG_ROOT / "schema.sql"
DB_PATH = PKG_ROOT / "library.db"
SPARQL_DIR = HERE / "sparql"
WIKIPEDIA_PKG = "fermentation.library_mcp.seed.wikipedia"

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIPEDIA_REST = "https://en.wikipedia.org/api/rest_v1/page/html/{title}"
USER_AGENT = (
    "WineWarehouseDDD/0.1 (https://example.invalid; library_mcp seed) "
    "python-requests"
)
SPARQL_HEADERS = {
    "Accept": "application/sparql-results+json",
    "User-Agent": USER_AGENT,
}
WIKIPEDIA_HEADERS = {"User-Agent": USER_AGENT, "Accept": "text/html"}


# ---------- schema ----------

def ensure_schema(conn: sqlite3.Connection) -> None:
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()


# ---------- wikidata helpers ----------

def _qid(uri: str | None) -> str | None:
    if not uri:
        return None
    if uri.startswith("http://www.wikidata.org/entity/"):
        return uri.rsplit("/", 1)[-1]
    return uri


def run_sparql(query: str, *, retries: int = 4) -> list[dict]:
    if requests is None:
        raise RuntimeError("requests is not available; cannot reach Wikidata")
    delay = 2.0
    for attempt in range(retries):
        resp = requests.get(
            WIKIDATA_ENDPOINT,
            params={"query": query},
            headers=SPARQL_HEADERS,
            timeout=120,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["results"]["bindings"]
        if resp.status_code in (429, 502, 503, 504):
            time.sleep(delay)
            delay *= 2
            continue
        resp.raise_for_status()
    raise RuntimeError(f"Wikidata SPARQL failed after {retries} retries")


def _read_query(name: str) -> str:
    return (SPARQL_DIR / f"{name}.rq").read_text(encoding="utf-8")


# ---------- ingest: countries ----------

def ingest_countries(conn: sqlite3.Connection) -> None:
    rows = run_sparql(_read_query("countries"))
    cur = conn.cursor()
    for r in rows:
        qid = _qid(r.get("country", {}).get("value"))
        name = (r.get("countryLabel") or {}).get("value")
        iso = (r.get("iso") or {}).get("value")
        if not name or not qid or name.startswith("Q"):
            continue
        try:
            cur.execute(
                """INSERT INTO countries (name, iso_code, wikidata_qid)
                   VALUES (?, ?, ?)
                   ON CONFLICT(wikidata_qid) DO UPDATE SET
                     name = excluded.name,
                     iso_code = COALESCE(excluded.iso_code, countries.iso_code)
                """,
                (name, iso, qid),
            )
        except sqlite3.IntegrityError:
            continue
    conn.commit()


# ---------- ingest: grapes ----------

def ingest_grapes(conn: sqlite3.Connection) -> None:
    rows = run_sparql(_read_query("grapes"))
    cur = conn.cursor()
    for r in rows:
        qid = _qid(r.get("grape", {}).get("value"))
        name = (r.get("grapeLabel") or {}).get("value")
        color = (r.get("colorLabel") or {}).get("value")
        origin_qid = _qid((r.get("origin") or {}).get("value"))
        synonyms = (r.get("synonyms") or {}).get("value", "")
        if not name or not qid or name.startswith("Q"):
            continue

        origin_id = None
        if origin_qid:
            row = cur.execute(
                "SELECT id FROM countries WHERE wikidata_qid = ?", (origin_qid,)
            ).fetchone()
            origin_id = row[0] if row else None

        # canonical_name has UNIQUE; Wikidata labels can collide across QIDs.
        # Try to upsert by QID first; if that's a NEW row and the name clashes,
        # skip (we'd rather keep the first-seen QID for that name and treat the
        # later one as a synonym we drop).
        try:
            cur.execute(
                """INSERT INTO grapes (canonical_name, color, origin_country_id, wikidata_qid)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(wikidata_qid) DO UPDATE SET
                     canonical_name = excluded.canonical_name,
                     color = COALESCE(excluded.color, grapes.color),
                     origin_country_id = COALESCE(excluded.origin_country_id, grapes.origin_country_id)
                """,
                (name, color, origin_id, qid),
            )
        except sqlite3.IntegrityError:
            # canonical_name collision with a different QID; skip this row.
            continue
        row = cur.execute(
            "SELECT id FROM grapes WHERE wikidata_qid = ?", (qid,)
        ).fetchone()
        if not row:
            continue
        grape_id = row[0]
        for syn in filter(None, (s.strip() for s in synonyms.split("||"))):
            cur.execute(
                "INSERT OR IGNORE INTO grape_synonyms (grape_id, synonym) VALUES (?, ?)",
                (grape_id, syn),
            )
    conn.commit()


# ---------- ingest: regions ----------

def ingest_regions(conn: sqlite3.Connection) -> None:
    rows = run_sparql(_read_query("regions"))
    cur = conn.cursor()
    # Two-pass so parent links resolve.
    staged: list[tuple[str, str | None, str | None, str]] = []
    for r in rows:
        qid = _qid(r.get("region", {}).get("value"))
        name = (r.get("regionLabel") or {}).get("value")
        country_qid = _qid((r.get("country") or {}).get("value"))
        parent_qid = _qid((r.get("parent") or {}).get("value"))
        if not qid or not name or name.startswith("Q"):
            continue
        staged.append((name, country_qid, parent_qid, qid))

    for name, country_qid, _, qid in staged:
        country_id = None
        if country_qid:
            row = cur.execute(
                "SELECT id FROM countries WHERE wikidata_qid = ?", (country_qid,)
            ).fetchone()
            country_id = row[0] if row else None
        try:
            cur.execute(
                """INSERT INTO regions (name, country_id, wikidata_qid)
                   VALUES (?, ?, ?)
                   ON CONFLICT(wikidata_qid) DO UPDATE SET
                     name = excluded.name,
                     country_id = COALESCE(excluded.country_id, regions.country_id)
                """,
                (name, country_id, qid),
            )
        except sqlite3.IntegrityError:
            continue

    for _, _, parent_qid, qid in staged:
        if not parent_qid:
            continue
        cur.execute(
            """UPDATE regions
                  SET parent_region_id = (SELECT id FROM regions WHERE wikidata_qid = ?)
                WHERE wikidata_qid = ?""",
            (parent_qid, qid),
        )
    conn.commit()


# ---------- wikipedia enrichment ----------

def _fetch_wikipedia(title: str) -> str | None:
    if requests is None:
        return None
    url = WIKIPEDIA_REST.format(title=title.replace(" ", "_"))
    resp = requests.get(url, headers=WIKIPEDIA_HEADERS, timeout=60)
    if resp.status_code == 200:
        return resp.text
    return None


# Each country module names the Wikipedia article it wants pulled.
# Add entries here as new parsers are written.
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
            print(f"[warn] skipping parser {mod_info.name}: {exc}", file=sys.stderr)
            continue
        if hasattr(module, "parse"):
            yield mod_info.name, module


def ingest_wikipedia(conn: sqlite3.Connection) -> None:
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
            "SELECT id FROM countries WHERE name = ? COLLATE NOCASE",
            (parsed.country,),
        ).fetchone()
        if not country_row:
            continue
        country_id = country_row[0]

        # Region rows -- by (name, country); skip if no QID and unknown.
        for region in parsed.regions:
            cur.execute(
                """INSERT OR IGNORE INTO regions (name, country_id, classification)
                   VALUES (?, ?, ?)""",
                (region.name, country_id, region.classification),
            )

        # region_grapes edges.
        for region_name, grape_names in parsed.region_grapes.items():
            r = cur.execute(
                "SELECT id FROM regions WHERE name = ? COLLATE NOCASE AND country_id = ?",
                (region_name, country_id),
            ).fetchone()
            if not r:
                continue
            region_id = r[0]
            for grape_name in grape_names:
                g = cur.execute(
                    """SELECT id FROM grapes WHERE canonical_name = ? COLLATE NOCASE
                       UNION
                       SELECT grape_id FROM grape_synonyms WHERE synonym = ? COLLATE NOCASE
                       LIMIT 1""",
                    (grape_name, grape_name),
                ).fetchone()
                if not g:
                    continue
                cur.execute(
                    "INSERT OR IGNORE INTO region_grapes (region_id, grape_id) VALUES (?, ?)",
                    (region_id, g[0]),
                )
    conn.commit()


# ---------- main ----------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build library.db")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip all network ingestion; only ensure the schema exists.",
    )
    args = parser.parse_args(argv)

    conn = sqlite3.connect(DB_PATH)
    try:
        ensure_schema(conn)
        if args.offline:
            print(f"[offline] schema written to {DB_PATH}", file=sys.stderr)
            return 0
        try:
            ingest_countries(conn)
            ingest_grapes(conn)
            ingest_regions(conn)
            ingest_wikipedia(conn)
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] seed failed mid-run: {exc}", file=sys.stderr)
            return 2
        print(f"[ok] library.db built at {DB_PATH}", file=sys.stderr)
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
