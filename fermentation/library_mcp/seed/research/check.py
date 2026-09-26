"""Check one research slice before it is reviewed or merged.

    python -m fermentation.library_mcp.seed.research.check fr-lac
    python -m fermentation.library_mcp.seed.research.check fr-lac --tree

Prints problems only, then a one-line count; exits 1 on errors. Sibling
slugs of the same country count only when their `.md` says
`Status: complete`. The last error check runs the real validator on a
temp copy of the allowlists merged with this slug and its complete
siblings (merge.py --check), so nothing is written.

`--tree` prints the file's hierarchy for the reviewer:
`name [classification] (n synonyms, n grapes)`, with existing parents as
roots.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import shutil
import tempfile
from collections import defaultdict
from pathlib import Path

import yaml

from ...server import _fold as _fold_region, _strip_classification
from ..allowlist import AllowlistError, load_allowlists
from .context import labels, lines_of, research_files, siblings, status
from .merge import ALLOWLIST, HERE, Report, _fold, merge_grapes, merge_regions

COLORS = {"red", "white", "rose", "gris"}


class Findings:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def _load(path: Path, f: Findings) -> list[dict] | None:
    if not path.exists():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    except yaml.YAMLError as exc:
        f.error(f"{path.name}: YAML parse error: {exc}".replace("\n", " "))
        return None
    if not isinstance(data, list) or not all(isinstance(d, dict) for d in data):
        f.error(f"{path.name}: expected a list of mappings")
        return None
    return data


def _entries(path: Path) -> list[dict]:
    return [e for _, _, e in lines_of(path)]


# ---------- regions ----------

def check_regions(slug: str, regions: list[dict], done: list[str], f: Findings) -> None:
    fname = f"{slug}.regions.yaml"
    for d in regions:
        if not d.get("name") or not d.get("country"):
            f.error(f"{fname}: entry without name or country: {d}")
    regions = [d for d in regions if d.get("name") and d.get("country")]
    countries = {d["country"] for d in regions}

    existing = [e for e in _entries(ALLOWLIST / "regions.yaml") if e.get("country") in countries]
    sib = [(s, e) for s in done for e in _entries(HERE / f"{s}.regions.yaml") if e.get("country") in countries]

    # Parents
    for d in regions:
        p = d.get("parent")
        if p and not any(e["name"] == p and e.get("country") == d["country"] for e in [*regions, *existing]):
            f.error(f"{d['name']}: parent {p!r} is in neither this file nor regions.yaml ({d['country']})")

    # Duplicate labels within a country, over what the merge would produce:
    # this file, complete siblings, and the existing entries neither replaces.
    replaced = {(d["country"], x) for d in [*regions, *(e for _, e in sib)]
                for x in (d["name"], d.get("was")) if x}
    merged = [(fname, d) for d in regions] + [(f"{s}.regions.yaml", e) for s, e in sib] + \
             [("regions.yaml", e) for e in existing if (e["country"], e["name"]) not in replaced]
    by_label: dict[tuple[str, str], list[tuple[str, dict, bool]]] = defaultdict(list)
    for src, e in merged:
        for i, lab in enumerate(labels(e)):
            by_label[(e["country"], _fold(lab))].append((src, e, i == 0))
    for (iso, key), hits in by_label.items():
        owners = {(src, h["name"]) for src, h, _ in hits}
        if len(owners) < 2 or not any(src == fname for src, _, _ in hits):
            continue
        desc = [f"{'name' if is_name else 'synonym'} of {h['name']!r} ({src})" for src, h, is_name in hits]
        folded_in = any(n for _, _, n in hits) and not all(n for _, _, n in hits)
        label = next(l for l in labels(hits[0][1]) if _fold(l) == key)
        f.error(f"duplicate label {label!r} in {iso}: " + "; ".join(desc)
                + (" (sub-appellation folded in as a synonym?)" if folded_in else ""))

    # Grapes named on regions
    grape_labels = {_fold(x) for p in [ALLOWLIST / "grapes.yaml", *research_files("grapes")]
                    for e in _entries(p) for x in labels(e)}
    for d in regions:
        for g in d.get("grapes") or []:
            if _fold(g) not in grape_labels:
                f.error(f"{d['name']}: grape {g!r} is in neither grapes.yaml nor any research grapes file")

    # Warnings
    others = [(p.name, e) for p in research_files("regions") if p.name != fname
              and p.stem.split(".")[0] not in done for e in _entries(p) if e.get("country") in countries]
    for d in regions:
        for lab in labels(d):
            fl = _fold_region(lab)
            if _strip_classification(fl) != fl:
                f.warn(f"{d['name']}: {lab!r} has a classification word or (…) tail the lookup already strips")
        for syn in d.get("synonyms") or []:
            for src, e in others:
                if e["country"] == d["country"] and _fold(e["name"]) == _fold(syn):
                    f.warn(f"{d['name']}: synonym {syn!r} is an entry name in {src}")
        if not d.get("source"):
            f.warn(f"{d['name']}: no source")


# ---------- grapes ----------

def check_grapes(slug: str, grapes: list[dict], f: Findings) -> None:
    fname = f"{slug}.grapes.yaml"
    base = _entries(ALLOWLIST / "grapes.yaml")
    canon = {e["name"] for e in base}
    owner: dict[str, tuple[str, str]] = {}   # folded label -> (grape, file)
    for e in base:
        for lab in labels(e):
            owner.setdefault(_fold(lab), (e["name"], "grapes.yaml"))
    for p in research_files("grapes"):
        if p.name == fname:
            continue
        for e in _entries(p):
            for lab in labels(e):
                owner.setdefault(_fold(lab), (e["name"], p.name))

    region_labels: dict[str, str] = {}
    for p in [ALLOWLIST / "regions.yaml", *research_files("regions")]:
        for e in _entries(p):
            for lab in labels(e):
                region_labels.setdefault(_fold(lab), f"{e['name']} ({e.get('country')}, {p.name})")

    mine: dict[str, str] = {}
    for d in grapes:
        name = d.get("name")
        if not name:
            f.error(f"{fname}: entry without name: {d}")
            continue
        if d.get("existing"):
            if name not in canon:
                hint = owner.get(_fold(name))
                f.error(f"{name}: marked existing but not a canonical grapes.yaml name"
                        + (f" (did you mean {hint[0]!r}?)" if hint and hint[1] == "grapes.yaml" else ""))
        else:
            if d.get("color") not in COLORS:
                f.error(f"{name}: new grape needs color red, white, rose or gris (got {d.get('color')!r})")
            hit = owner.get(_fold(name))
            if hit:
                f.error(f"{name}: new grape already exists as {hit[0]!r} ({hit[1]})")
        for lab in labels(d) if not d.get("existing") else d.get("synonyms") or []:
            key = _fold(lab)
            hit = owner.get(key)
            if hit and hit[0] != name and lab != name:
                f.error(f"{name}: synonym {lab!r} already belongs to {hit[0]!r} ({hit[1]})")
            if mine.get(key, name) != name:
                f.error(f"{name}: label {lab!r} also used by {mine[key]!r} in this file")
            mine.setdefault(key, name)
        for syn in d.get("synonyms") or []:
            if _fold(syn) in region_labels:
                f.warn(f"{name}: synonym {syn!r} is also a region: {region_labels[_fold(syn)]}")
        if not d.get("source"):
            f.warn(f"{name}: no source")


# ---------- validator (merge --check in-process) ----------

def run_validator(slugs: list[str], f: Findings) -> None:
    rep = Report()
    tmp = Path(tempfile.mkdtemp(prefix="check-"))
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            grape_lines = merge_grapes(slugs, rep)
            region_lines = merge_regions(slugs, rep)
        for name in ("countries.yaml", "qids.lock.yaml"):
            shutil.copy(ALLOWLIST / name, tmp / name)
        (tmp / "grapes.yaml").write_text("\n".join(grape_lines) + "\n", encoding="utf-8")
        (tmp / "regions.yaml").write_text("\n".join(region_lines) + "\n", encoding="utf-8")
        load_allowlists(tmp, require_qids=False)
    except SystemExit as exc:
        f.error(f"merge ({' '.join(slugs)}): {exc}")
    except AllowlistError as exc:
        f.error(f"validator ({' '.join(slugs)}): " + str(exc).replace("\n", "\n    "))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------- tree ----------

def print_tree(regions: list[dict]) -> None:
    own = {(d["country"], d["name"]) for d in regions}
    kids: dict[tuple[str, str | None], list[dict]] = defaultdict(list)
    roots: dict[tuple[str, str | None], None] = {}
    for d in regions:
        key = (d["country"], d.get("parent"))
        kids[key].append(d)
        if (d["country"], d.get("parent")) not in own:
            roots.setdefault(key)

    def line(d: dict) -> str:
        cls = f" [{d['classification']}]" if d.get("classification") else ""
        return f"{d['name']}{cls} ({len(d.get('synonyms') or [])} synonyms, {len(d.get('grapes') or [])} grapes)"

    def walk(key: tuple[str, str | None], depth: int) -> None:
        for d in kids.get(key, []):
            print("  " * depth + line(d))
            walk((d["country"], d["name"]), depth + 1)

    for iso, parent in roots:
        if parent:
            print(f"{parent} (existing, {iso})")
            walk((iso, parent), 1)
        else:
            walk((iso, None), 0)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("slug")
    ap.add_argument("--tree", action="store_true", help="print the file's region hierarchy")
    args = ap.parse_args(argv)
    slug = args.slug

    f = Findings()
    done = [s for s in siblings(slug) if status(s).lower().startswith("complete")]
    regions = _load(HERE / f"{slug}.regions.yaml", f)
    grapes = _load(HERE / f"{slug}.grapes.yaml", f)
    if regions is not None:
        check_regions(slug, regions, done, f)
    if grapes is not None:
        check_grapes(slug, grapes, f)
    if regions is not None and grapes is not None and not f.errors:
        run_validator([slug, *done], f)

    if args.tree and regions:
        print_tree([d for d in regions if d.get("name") and d.get("country")])
        print()
    for e in f.errors:
        print(f"ERROR   {e}")
    for w in f.warnings:
        print(f"warning {w}")
    n_r, n_g = len(regions or []), len(grapes or [])
    print(f"{slug}: {n_r} regions, {n_g} grapes; {len(f.errors)} errors, {len(f.warnings)} warnings"
          + (f" (complete siblings: {', '.join(done)})" if done else ""))
    return 1 if f.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
