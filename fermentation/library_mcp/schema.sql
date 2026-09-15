-- library_mcp canonical schema
-- Wine countries / regions / grapes baked into a SQLite file the MCP server
-- opens read-only. Keyed on Wikidata QIDs to keep dedup robust against
-- synonyms.
--
-- Two tiers per entity table (see fermentation/PLAN.md "Reseed plan"):
--   is_canonical = 1  -> on the checked-in allowlist (seed/allowlist/*.yaml);
--                        human-reviewed, what submit_tags validates against
--                        and what list_* returns by default.
--   is_canonical = 0  -> placeholder: long-tail entry from the filtered
--                        Wikidata pass. Resolves via lookup_* (flagged
--                        is_placeholder) but cannot pass submit_tags.
--
-- MIGRATION NOTE: this file is applied with executescript and every
-- statement is IF NOT EXISTS, so it is safe to re-run on an existing DB --
-- but it will NOT add columns to tables that already exist. Schema changes
-- are rolled out by rebuilding library.db from scratch:
--     python -m fermentation.library_mcp.seed.build_db
-- (build_db deletes the old file before seeding). There are no ALTER TABLE
-- migrations.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS countries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL UNIQUE,
    iso_code        TEXT,                              -- ISO-3166-1 alpha-2
    wikidata_qid    TEXT    UNIQUE,
    is_canonical    INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_countries_name_nocase
    ON countries (name COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS country_synonyms (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    country_id  INTEGER NOT NULL REFERENCES countries(id) ON DELETE CASCADE,
    synonym     TEXT    NOT NULL,
    UNIQUE (country_id, synonym)
);

CREATE INDEX IF NOT EXISTS idx_country_synonyms_nocase
    ON country_synonyms (synonym COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS regions (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    name               TEXT    NOT NULL,
    country_id         INTEGER REFERENCES countries(id) ON DELETE CASCADE,
    parent_region_id   INTEGER REFERENCES regions(id)   ON DELETE SET NULL,
    classification     TEXT,                            -- AOC, DOC, AVA, Anbaugebiet, etc.
    wikidata_qid       TEXT    UNIQUE,
    is_canonical       INTEGER NOT NULL DEFAULT 0,
    UNIQUE (name, country_id)
);

CREATE INDEX IF NOT EXISTS idx_regions_name_nocase
    ON regions (name COLLATE NOCASE);

CREATE INDEX IF NOT EXISTS idx_regions_country
    ON regions (country_id);

CREATE INDEX IF NOT EXISTS idx_regions_parent
    ON regions (parent_region_id);

-- Twin of grape_synonyms: Piemonte -> Piedmont, Bourgogne -> Burgundy,
-- "Emilia Romagna" -> "Emilia-Romagna".
CREATE TABLE IF NOT EXISTS region_synonyms (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id  INTEGER NOT NULL REFERENCES regions(id) ON DELETE CASCADE,
    synonym    TEXT    NOT NULL,
    UNIQUE (region_id, synonym)
);

CREATE INDEX IF NOT EXISTS idx_region_synonyms_nocase
    ON region_synonyms (synonym COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS grapes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name      TEXT    NOT NULL UNIQUE,
    color               TEXT,                            -- red, white, rose, gris, ...
    species             TEXT,                            -- vinifera, labrusca, hybrid
    origin_country_id   INTEGER REFERENCES countries(id) ON DELETE SET NULL,
    wikidata_qid        TEXT    UNIQUE,
    is_canonical        INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_grapes_name_nocase
    ON grapes (canonical_name COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS grape_synonyms (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    grape_id    INTEGER NOT NULL REFERENCES grapes(id) ON DELETE CASCADE,
    synonym     TEXT    NOT NULL,
    UNIQUE (grape_id, synonym)
);

CREATE INDEX IF NOT EXISTS idx_grape_synonyms_nocase
    ON grape_synonyms (synonym COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS region_grapes (
    region_id   INTEGER NOT NULL REFERENCES regions(id) ON DELETE CASCADE,
    grape_id    INTEGER NOT NULL REFERENCES grapes(id)  ON DELETE CASCADE,
    PRIMARY KEY (region_id, grape_id)
);

CREATE INDEX IF NOT EXISTS idx_region_grapes_grape
    ON region_grapes (grape_id);
