"""Fold per-country research files into the canonical allowlists.

Research agents write `<slug>.regions.yaml` / `<slug>.grapes.yaml` here
(format: journal/2026-09-26-LIBRARY-GROUND-TRUTH-PLAN.md, "Agent brief").
This script merges them into `../allowlist/regions.yaml` and `grapes.yaml`
and prints what changed, so the diff can be reviewed before a rebuild.

Regions. Every country that appears in the given research files is
REPLACED by the union of their entries for that country, in research file
order, at the position of that country's first existing line. Existing
entries the research did not return are kept and listed ("kept, not in
research"), unless a research entry names them in `was:` (a rename).
`source`, `was` and any other research-only keys are dropped.

Grapes. `existing: true` entries add their synonyms to that grape's line.
Other entries are appended under a `research: <slug>` header. Labels that
would collide with another grape's name or synonym are skipped and listed.

After writing, the allowlists are re-validated (QIDs not required: run
resolve_qids.py next). Default is a dry run.

    python -m fermentation.library_mcp.seed.research.merge za            # report only
    python -m fermentation.library_mcp.seed.research.merge za --check    # report + validate a temp copy
    python -m fermentation.library_mcp.seed.research.merge za --write
    python -m fermentation.library_mcp.seed.research.merge us-ca us-pnw us-rest --write
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ...server import _fold
from ..allowlist import AllowlistError, load_allowlists

HERE = Path(__file__).resolve().parent
ALLOWLIST = HERE.parent / "allowlist"
REGION_KEYS = ("name", "country", "parent", "classification", "synonyms", "grapes", "qid")
GRAPE_KEYS = ("name", "color", "synonyms", "qid")




# ---------- one-line flow YAML, in the allowlists' own style ----------

_YAML_BOOLS = {"y", "n", "yes", "no", "on", "off", "true", "false"}   # bare NO (Norway) would load as False


def _q(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _flow(entry: dict, keys: tuple[str, ...]) -> str:
    parts = []
    for k in keys:
        v = entry.get(k)
        if v in (None, "", []):
            continue
        if isinstance(v, list):
            parts.append(f"{k}: [{', '.join(_q(x) for x in v)}]")
        elif (k in ("country", "color", "qid") or (k == "classification" and v.replace(" ", "").isalnum())) \
                and v.lower() not in _YAML_BOOLS:
            parts.append(f"{k}: {v}")
        else:
            parts.append(f"{k}: {_q(str(v))}")
    return "- {" + ", ".join(parts) + "}"


def _parse_line(line: str) -> dict | None:
    s = line.strip()
    if not s.startswith("- {"):
        return None
    item = yaml.safe_load(s)
    return item[0] if isinstance(item, list) and item and isinstance(item[0], dict) else None


def _read_research(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    if not isinstance(data, list) or not all(isinstance(d, dict) for d in data):
        sys.exit(f"{path.name}: expected a list of mappings")
    return data


# ---------- regions ----------

@dataclass
class Report:
    lines: list[str] = field(default_factory=list)

    def add(self, text: str = "") -> None:
        self.lines.append(text)

    def section(self, title: str, items: list[str]) -> None:
        if items:
            self.add(f"\n## {title} ({len(items)})")
            self.lines.extend(f"- {i}" for i in items)


def merge_regions(slugs: list[str], rep: Report) -> list[str]:
    path = ALLOWLIST / "regions.yaml"
    lines = path.read_text(encoding="utf-8").splitlines()
    parsed = [(i, _parse_line(l)) for i, l in enumerate(lines)]
    existing = [(i, e) for i, e in parsed if e]

    research: dict[str, list[dict]] = {}
    unsourced: list[str] = []
    for slug in slugs:
        for d in _read_research(HERE / f"{slug}.regions.yaml"):
            if not d.get("name") or not d.get("country"):
                sys.exit(f"{slug}.regions.yaml: entry without name/country: {d}")
            research.setdefault(d["country"], []).append(d)
            if not d.get("source"):
                unsourced.append(f"{d['name']} ({d['country']})")

    new_countries: list[str] = []
    for iso, entries in research.items():
        old = {e["name"]: (i, e) for i, e in existing if e.get("country") == iso}
        names = [d["name"] for d in entries]
        dupes = sorted({n for n in names if names.count(n) > 1})
        if dupes:
            sys.exit(f"{iso}: research lists these regions twice: {dupes}")
        renamed = {d["was"]: d["name"] for d in entries if d.get("was")}
        added, reparented, syn_changes, kept, renames, reclass = [], [], [], [], [], []
        out_entries: list[dict] = []
        for d in entries:
            prev = old.get(d.get("was") or d["name"]) or old.get(d["name"])
            entry = {k: d.get(k) for k in REGION_KEYS}
            entry["synonyms"] = list(dict.fromkeys(d.get("synonyms") or []))
            entry["grapes"] = list(dict.fromkeys(d.get("grapes") or []))
            if prev is None:
                added.append(f"{d['name']}" + (f" < {d['parent']}" if d.get("parent") else ""))
            else:
                pe = prev[1]
                entry["qid"] = entry["qid"] or pe.get("qid")
                if d.get("was") and d["was"] != d["name"]:
                    renames.append(f"{d['was']} -> {d['name']}")
                if (pe.get("parent") or None) != (d.get("parent") or None):
                    reparented.append(f"{d['name']}: {pe.get('parent')} -> {d.get('parent')}")
                if (pe.get("classification") or None) != (d.get("classification") or None):
                    reclass.append(f"{d['name']}: {pe.get('classification')} -> {d.get('classification')}")
                before, after = set(pe.get("synonyms") or []), set(entry["synonyms"])
                if before != after:
                    plus = sorted(after - before)
                    minus = sorted(before - after)
                    syn_changes.append(f"{d['name']}: " + ", ".join(
                        [f"+{s!r}" for s in plus] + [f"-{s!r}" for s in minus]))
            out_entries.append(entry)
        research_names = set(names)
        for name, (_, pe) in old.items():
            if name in research_names or name in renamed:
                continue
            kept.append(name)
            out_entries.append({k: pe.get(k) for k in REGION_KEYS})

        rep.add(f"\n# Regions: {iso} — {len(old)} before, {len(out_entries)} after")
        rep.section("Added", added)
        rep.section("Renamed", renames)
        rep.section("Re-parented", reparented)
        rep.section("Classification changed", reclass)
        rep.section("Synonyms changed", syn_changes)
        rep.section("Kept, not in research (check)", kept)

        block = [_flow(e, REGION_KEYS) for e in out_entries]
        old_idx = sorted(i for i, _ in old.values())
        if old_idx:
            first = old_idx[0]
            drop = set(old_idx)
            lines = [l for i, l in enumerate(lines) if i < first and i not in drop] + block + \
                    [l for i, l in enumerate(lines) if i > first and i not in drop]
        else:
            new_countries.append(iso)
            lines += ["", f"# ======================= {iso} (research) ======================="] + block
        existing = [(i, e) for i, e in ((i, _parse_line(l)) for i, l in enumerate(lines)) if e]

    rep.section("Regions without a source", unsourced)
    if new_countries:
        rep.section("Countries with no previous regions (appended at the end; move the block by hand)",
                    new_countries)
    return lines


# ---------- grapes ----------

def merge_grapes(slugs: list[str], rep: Report) -> list[str]:
    path = ALLOWLIST / "grapes.yaml"
    lines = path.read_text(encoding="utf-8").splitlines()
    index = {e["name"]: i for i, e in ((i, _parse_line(l)) for i, l in enumerate(lines)) if e}
    owner: dict[str, str] = {}
    for i in index.values():
        e = _parse_line(lines[i])
        for label in [e["name"], *(e.get("synonyms") or [])]:
            owner.setdefault(_fold(label), e["name"])

    added_syn, new_grapes, skipped, unknown, unsourced = [], [], [], [], []
    for slug in slugs:
        appended: list[str] = []
        for d in _read_research(HERE / f"{slug}.grapes.yaml"):
            name = d.get("name")
            if not name:
                sys.exit(f"{slug}.grapes.yaml: entry without name: {d}")
            if not d.get("source"):
                unsourced.append(name)
            if d.get("existing"):
                if name not in index:
                    unknown.append(f"{name} (marked existing, not in grapes.yaml)")
                    continue
                e = _parse_line(lines[index[name]])
                syns = list(e.get("synonyms") or [])
                for s in d.get("synonyms") or []:
                    o = owner.get(_fold(s))
                    if o is None:
                        syns.append(s)
                        owner[_fold(s)] = name
                        added_syn.append(f"{name}: +{s!r}")
                    elif o != name:
                        skipped.append(f"{s!r} for {name}: already {o}")
                e["synonyms"] = syns
                lines[index[name]] = _flow(e, GRAPE_KEYS)
            else:
                if _fold(name) in owner:
                    skipped.append(f"new grape {name!r}: already {owner[_fold(name)]}")
                    continue
                syns = []
                for s in d.get("synonyms") or []:
                    o = owner.get(_fold(s))
                    if o is None or o == name:
                        syns.append(s)
                    else:
                        skipped.append(f"{s!r} for new grape {name}: already {o}")
                entry = {"name": name, "color": d.get("color"), "synonyms": syns, "qid": d.get("qid")}
                for label in [name, *syns]:
                    owner[_fold(label)] = name
                appended.append(_flow(entry, GRAPE_KEYS))
                new_grapes.append(f"{name} ({d.get('color')})")
        if appended:
            lines += ["", f"# ---------------- research: {slug} ----------------", *appended]
            index.update({_parse_line(l)["name"]: len(lines) - len(appended) + k
                          for k, l in enumerate(appended)})

    rep.add("\n# Grapes")
    rep.section("New grapes", new_grapes)
    rep.section("Synonyms added", added_syn)
    rep.section("Skipped (label already belongs to another grape)", skipped)
    rep.section("Problems", unknown)
    rep.section("Grapes without a source", unsourced)
    return lines


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("slugs", nargs="+", help="research file prefixes, e.g. za or us-ca us-pnw")
    ap.add_argument("--write", action="store_true", help="write the allowlists (default: report only)")
    ap.add_argument("--check", action="store_true",
                    help="validate the merged result in a temp copy; the allowlists are not touched")
    args = ap.parse_args(argv)

    rep = Report()
    rep.add(f"Merge of {', '.join(args.slugs)}" + ("" if args.write else " (dry run)"))
    grape_lines = merge_grapes(args.slugs, rep)
    region_lines = merge_regions(args.slugs, rep)
    print("\n".join(rep.lines))
    if args.check:
        tmp = Path(tempfile.mkdtemp(prefix="merge-check-"))
        for name in ("countries.yaml", "qids.lock.yaml"):
            shutil.copy(ALLOWLIST / name, tmp / name)
        (tmp / "grapes.yaml").write_text("\n".join(grape_lines) + "\n", encoding="utf-8")
        (tmp / "regions.yaml").write_text("\n".join(region_lines) + "\n", encoding="utf-8")
        try:
            load_allowlists(tmp, require_qids=False)
        except AllowlistError as exc:
            print(f"\nCheck FAILED (allowlists untouched):\n{exc}")
            return 1
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        print("\nCheck passed: the merged allowlists validate (allowlists untouched).")
        return 0
    if not args.write:
        return 0

    paths = {ALLOWLIST / "grapes.yaml": grape_lines, ALLOWLIST / "regions.yaml": region_lines}
    backup = {p: p.read_text(encoding="utf-8") for p in paths}
    for p, ls in paths.items():
        p.write_text("\n".join(ls) + "\n", encoding="utf-8")
    try:
        load_allowlists(require_qids=False)
    except AllowlistError as exc:
        for p, text in backup.items():
            p.write_text(text, encoding="utf-8")
        print(f"\nValidation failed; allowlists restored.\n{exc}")
        return 1
    print("\nWritten and validated. Next: resolve_qids.py, review the lock diff, build_db.py.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
