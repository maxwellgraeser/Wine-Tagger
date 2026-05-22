-- library_mcp canonical schema
-- Wine countries / regions / grapes baked into a SQLite file the MCP server
-- opens read-only. Keyed on Wikidata QIDs to keep dedup robust against
-- synonyms.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS countries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL UNIQUE,
    iso_code        TEXT,                              -- ISO-3166-1 alpha-2
    wikidata_qid    TEXT    UNIQUE
);

CREATE INDEX IF NOT EXISTS idx_countries_name_nocase
    ON countries (name COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS regions (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    name               TEXT    NOT NULL,
    country_id         INTEGER REFERENCES countries(id) ON DELETE CASCADE,
    parent_region_id   INTEGER REFERENCES regions(id)   ON DELETE SET NULL,
    classification     TEXT,                            -- AOC, DOC, AVA, Anbaugebiet, etc.
    wikidata_qid       TEXT    UNIQUE,
    UNIQUE (name, country_id)
);

CREATE INDEX IF NOT EXISTS idx_regions_name_nocase
    ON regions (name COLLATE NOCASE);

CREATE INDEX IF NOT EXISTS idx_regions_country
    ON regions (country_id);

CREATE INDEX IF NOT EXISTS idx_regions_parent
    ON regions (parent_region_id);

CREATE TABLE IF NOT EXISTS grapes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name      TEXT    NOT NULL UNIQUE,
    color               TEXT,                            -- red, white, rose, gris, ...
    species             TEXT,                            -- vinifera, labrusca, hybrid
    origin_country_id   INTEGER REFERENCES countries(id) ON DELETE SET NULL,
    wikidata_qid        TEXT    UNIQUE
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
