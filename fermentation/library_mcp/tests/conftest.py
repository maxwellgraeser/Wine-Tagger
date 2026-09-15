"""Shared fixtures. Tests that need a populated library.db skip when the
DB is missing or empty (i.e. build_db.py has not been run in this checkout).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

DB_PATH = Path(__file__).resolve().parents[1] / "library.db"


def _db_populated() -> bool:
    if not DB_PATH.exists():
        return False
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(grapes)")}
        if "is_canonical" not in cols:
            return False
        n = conn.execute("SELECT COUNT(*) FROM grapes WHERE is_canonical = 1").fetchone()[0]
        return n > 0
    except sqlite3.Error:
        return False
    finally:
        conn.close()


@pytest.fixture(scope="session")
def server():
    if not _db_populated():
        pytest.skip("library.db not built (run python -m fermentation.library_mcp.seed.build_db)")
    from fermentation.library_mcp import server as srv
    return srv
