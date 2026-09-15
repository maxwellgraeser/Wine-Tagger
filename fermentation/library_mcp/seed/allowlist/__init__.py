"""Allowlist loader + validator for the canonical tier of library.db.

Three hand-edited YAMLs live next to this file:

    countries.yaml   -- {name, iso, synonyms[]}            keyed by ISO-3166-1 alpha-2
    grapes.yaml      -- {name, color, synonyms[], qid?}    keyed by name
    regions.yaml     -- {name, country, parent?, classification?, synonyms[], qid?}

plus one machine-generated lock file, `qids.lock.yaml`, written by
`seed/resolve_qids.py`. The lock maps grape / region names to the Wikidata
QID the resolver picked, with the label + description it saw so a human can
eyeball wrong picks in a diff. Build rules:

  * Countries resolve deterministically from ISO code (wdt:P297) at build
    time -- no lock entry needed.
  * Grapes MUST have a QID: either `qid:` in the YAML (manual pin) or a lock
    entry. Missing -> build fails. Wikidata supplies altLabel synonyms.
  * Regions MAY have a QID. Wikidata types wine regions inconsistently
    (Barolo is a "wine", Rioja a "wine-producing region", Napa an "AVA",
    Bekaa a "valley"), so the hierarchy, country and classification are
    authored here and the QID is only used for dedup against the
    placeholder pass. Missing -> region lands without a QID.

Why names, not QIDs, as the primary key: every hand-typed QID in the first
draft of this plan pointed at the wrong entity (phenylalanine, a larch,
an asteroid). Names are what humans can review; QIDs get resolved by
machine and reviewed via the lock file's label/description columns.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
LOCK_PATH = HERE / "qids.lock.yaml"

_QID_RE = re.compile(r"^Q\d+$")
_ISO_RE = re.compile(r"^[A-Z]{2}$")
_COLORS = {"red", "white", "rose", "gris"}


class AllowlistError(ValueError):
    """Raised for any structural problem in the YAMLs or the lock file."""


@dataclass
class CountryEntry:
    name: str
    iso: str
    synonyms: list[str] = field(default_factory=list)


@dataclass
class GrapeEntry:
    name: str
    color: str | None = None
    synonyms: list[str] = field(default_factory=list)
    qid: str | None = None          # manual pin; overrides the lock file


@dataclass
class RegionEntry:
    name: str
    country: str                    # ISO code, must exist in countries.yaml
    parent: str | None = None       # region name, must exist in regions.yaml
    classification: str | None = None
    synonyms: list[str] = field(default_factory=list)
    qid: str | None = None          # manual pin; overrides the lock file


@dataclass
class LockEntry:
    qid: str
    label: str | None = None
    description: str | None = None


@dataclass
class Allowlist:
    countries: list[CountryEntry]
    grapes: list[GrapeEntry]
    regions: list[RegionEntry]
    lock_grapes: dict[str, LockEntry] = field(default_factory=dict)
    lock_regions: dict[str, LockEntry] = field(default_factory=dict)

    # ---- resolved QIDs (YAML pin wins over lock) ----

    def grape_qid(self, entry: GrapeEntry) -> str | None:
        if entry.qid:
            return entry.qid
        lk = self.lock_grapes.get(entry.name)
        return lk.qid if lk else None

    def region_qid(self, entry: RegionEntry) -> str | None:
        if entry.qid:
            return entry.qid
        lk = self.lock_regions.get(_region_key(entry))
        return lk.qid if lk else None

    def region_by_name(self, name: str) -> RegionEntry | None:
        return self._regions_by_name.get(name)

    def __post_init__(self) -> None:
        self._regions_by_name = {r.name: r for r in self.regions}


def _region_key(entry: RegionEntry) -> str:
    """Lock key for a region: `name (ISO)` so homonyms across countries
    (e.g. two 'Valle Central') don't collide."""
    return f"{entry.name} ({entry.country})"


# ---------- YAML parsing ----------

def _read_yaml_list(path: Path) -> list[dict]:
    if not path.exists():
        raise AllowlistError(f"missing allowlist file: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    if not isinstance(data, list):
        raise AllowlistError(f"{path.name}: top level must be a list")
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise AllowlistError(f"{path.name}[{i}]: entry must be a mapping")
    return data


def _str_list(v, where: str) -> list[str]:
    if v is None:
        return []
    if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
        raise AllowlistError(f"{where}: synonyms must be a list of strings")
    return [x.strip() for x in v if x.strip()]


def _opt_str(v, where: str) -> str | None:
    if v is None:
        return None
    if not isinstance(v, str):
        raise AllowlistError(f"{where}: expected string, got {type(v).__name__}")
    v = v.strip()
    return v or None


def _opt_qid(v, where: str) -> str | None:
    q = _opt_str(v, where)
    if q is not None and not _QID_RE.match(q):
        raise AllowlistError(f"{where}: bad qid {q!r}")
    return q


def _load_countries(path: Path) -> list[CountryEntry]:
    out: list[CountryEntry] = []
    for i, d in enumerate(_read_yaml_list(path)):
        where = f"countries.yaml[{i}]"
        name = _opt_str(d.get("name"), where)
        iso = _opt_str(d.get("iso"), where)
        if not name or not iso:
            raise AllowlistError(f"{where}: name and iso are required")
        if not _ISO_RE.match(iso):
            raise AllowlistError(f"{where}: iso must be two uppercase letters, got {iso!r}")
        out.append(CountryEntry(name=name, iso=iso, synonyms=_str_list(d.get("synonyms"), where)))
    return out


def _load_grapes(path: Path) -> list[GrapeEntry]:
    out: list[GrapeEntry] = []
    for i, d in enumerate(_read_yaml_list(path)):
        where = f"grapes.yaml[{i}]"
        name = _opt_str(d.get("name"), where)
        if not name:
            raise AllowlistError(f"{where}: name is required")
        color = _opt_str(d.get("color"), where)
        if color is not None and color not in _COLORS:
            raise AllowlistError(f"{where} ({name}): color must be one of {sorted(_COLORS)}")
        out.append(
            GrapeEntry(
                name=name,
                color=color,
                synonyms=_str_list(d.get("synonyms"), where),
                qid=_opt_qid(d.get("qid"), where),
            )
        )
    return out


def _load_regions(path: Path) -> list[RegionEntry]:
    out: list[RegionEntry] = []
    for i, d in enumerate(_read_yaml_list(path)):
        where = f"regions.yaml[{i}]"
        name = _opt_str(d.get("name"), where)
        country = _opt_str(d.get("country"), where)
        if not name or not country:
            raise AllowlistError(f"{where}: name and country are required")
        out.append(
            RegionEntry(
                name=name,
                country=country,
                parent=_opt_str(d.get("parent"), where),
                classification=_opt_str(d.get("classification"), where),
                synonyms=_str_list(d.get("synonyms"), where),
                qid=_opt_qid(d.get("qid"), where),
            )
        )
    return out


def _load_lock(path: Path) -> tuple[dict[str, LockEntry], dict[str, LockEntry]]:
    if not path.exists():
        return {}, {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise AllowlistError(f"{path.name}: top level must be a mapping")

    def section(key: str) -> dict[str, LockEntry]:
        sec = data.get(key) or {}
        if not isinstance(sec, dict):
            raise AllowlistError(f"{path.name}: {key} must be a mapping")
        out: dict[str, LockEntry] = {}
        for k, v in sec.items():
            if v is None:
                continue                      # explicit "unresolved" marker
            if not isinstance(v, dict) or not _QID_RE.match(str(v.get("qid", ""))):
                raise AllowlistError(f"{path.name}: {key}[{k!r}] needs a valid qid")
            out[str(k)] = LockEntry(
                qid=str(v["qid"]),
                label=v.get("label"),
                description=v.get("description"),
            )
        return out

    return section("grapes"), section("regions")


# ---------- validation ----------

def validate(al: Allowlist) -> None:
    """Structural checks. Raises AllowlistError with every problem listed."""
    problems: list[str] = []

    # countries: unique name + iso
    seen_iso: set[str] = set()
    seen_name: set[str] = set()
    for c in al.countries:
        if c.iso in seen_iso:
            problems.append(f"countries: duplicate iso {c.iso}")
        if c.name.lower() in seen_name:
            problems.append(f"countries: duplicate name {c.name!r}")
        seen_iso.add(c.iso)
        seen_name.add(c.name.lower())

    # grapes: unique names, unique QIDs, synonyms must not collide with
    # another grape's canonical name or synonyms.
    gnames: dict[str, str] = {}
    gqids: dict[str, str] = {}
    for g in al.grapes:
        key = g.name.lower()
        if key in gnames:
            problems.append(f"grapes: duplicate name {g.name!r}")
        gnames[key] = g.name
        q = al.grape_qid(g)
        if q is None:
            problems.append(f"grapes: {g.name!r} has no QID (run resolve_qids.py or pin qid:)")
        elif q in gqids:
            problems.append(f"grapes: {g.name!r} and {gqids[q]!r} share QID {q}")
        else:
            gqids[q] = g.name
    syn_owner: dict[str, str] = {}
    for g in al.grapes:
        for s in g.synonyms:
            key = s.lower()
            if key in gnames and gnames[key] != g.name:
                problems.append(f"grapes: synonym {s!r} of {g.name!r} is another grape's canonical name")
            if key in syn_owner and syn_owner[key] != g.name:
                problems.append(f"grapes: synonym {s!r} claimed by both {syn_owner[key]!r} and {g.name!r}")
            syn_owner[key] = g.name

    # regions: unique (name, country), country must exist, parent must exist
    # (and be in the same country), no parent cycles, QIDs unique.
    isos = {c.iso for c in al.countries}
    rkeys: set[tuple[str, str]] = set()
    rqids: dict[str, str] = {}
    for r in al.regions:
        k = (r.name.lower(), r.country)
        if k in rkeys:
            problems.append(f"regions: duplicate {r.name!r} in {r.country}")
        rkeys.add(k)
        if r.country not in isos:
            problems.append(f"regions: {r.name!r} references unknown country {r.country!r}")
        q = al.region_qid(r)
        if q is not None:
            if q in rqids:
                problems.append(f"regions: {r.name!r} and {rqids[q]!r} share QID {q}")
            rqids[q] = r.name
    # region names + synonyms must be globally unambiguous: the server
    # resolves a bare string to ONE region, so "Styria" cannot mean both
    # Steiermark (AT) and Štajerska (SI).
    rlabel_owner: dict[str, str] = {}
    for r in al.regions:
        for label in [r.name, *r.synonyms]:
            key = label.lower()
            owner = f"{r.name} ({r.country})"
            if key in rlabel_owner and rlabel_owner[key] != owner:
                problems.append(f"regions: label {label!r} claimed by both {rlabel_owner[key]} and {owner}")
            rlabel_owner.setdefault(key, owner)
    by_name = {r.name: r for r in al.regions}
    for r in al.regions:
        if r.parent is None:
            continue
        p = by_name.get(r.parent)
        if p is None:
            problems.append(f"regions: {r.name!r} parent {r.parent!r} is not in regions.yaml")
            continue
        if p.country != r.country:
            problems.append(f"regions: {r.name!r} ({r.country}) has parent {r.parent!r} in {p.country}")
        # cycle check
        seen = {r.name}
        cur = p
        while cur is not None:
            if cur.name in seen:
                problems.append(f"regions: parent cycle through {r.name!r}")
                break
            seen.add(cur.name)
            cur = by_name.get(cur.parent) if cur.parent else None

    if problems:
        raise AllowlistError("allowlist validation failed:\n  " + "\n  ".join(problems))


# ---------- public entry point ----------

def load_allowlists(base: Path | None = None, *, require_qids: bool = True) -> Allowlist:
    """Parse + validate the three YAMLs and the lock file.

    `require_qids=False` skips the "grape has no QID" check -- used by
    resolve_qids.py, which exists precisely to fill those in.
    """
    base = base or HERE
    al = Allowlist(
        countries=_load_countries(base / "countries.yaml"),
        grapes=_load_grapes(base / "grapes.yaml"),
        regions=_load_regions(base / "regions.yaml"),
    )
    al.lock_grapes, al.lock_regions = _load_lock(base / "qids.lock.yaml")
    if require_qids:
        validate(al)
    else:
        # Run validation but tolerate missing grape QIDs.
        try:
            validate(al)
        except AllowlistError as exc:
            msgs = [m for m in str(exc).splitlines()[1:] if "has no QID" not in m]
            if msgs:
                raise AllowlistError("allowlist validation failed:\n" + "\n".join(msgs)) from None
    return al


__all__ = [
    "Allowlist", "AllowlistError", "CountryEntry", "GrapeEntry", "RegionEntry",
    "LockEntry", "LOCK_PATH", "load_allowlists", "validate", "region_lock_key",
]


def region_lock_key(entry: RegionEntry) -> str:
    return _region_key(entry)
