"""What a research agent needs to know, without reading the allowlists whole.

    python -m fermentation.library_mcp.seed.research.context it-c1
    python -m fermentation.library_mcp.seed.research.context --grape Prugnolo "Uva di Troia"
    python -m fermentation.library_mcp.seed.research.context --region Cebreros "La Rioja"

`<slug>` prints the conventions header of regions.yaml, every existing
entry for the slice's countries (the `**Country:**` line of its scope), and
the other research slugs for those countries with their `Status:` line.
`--grape` / `--region` match names and synonyms, ignoring case and accents,
across the allowlist and every research file.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from .merge import ALLOWLIST, HERE, _fold, _parse_line

SCOPES = HERE / "scopes"


def lines_of(path: Path) -> list[tuple[int, str, dict]]:
    """(line number, raw line, entry) for every parseable one-line entry.

    Parsed line by line so a half-written research file still yields what
    it has.
    """
    out = []
    if not path.exists():
        return out
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            e = _parse_line(line)
        except Exception:
            continue
        if e:
            out.append((n, line.strip(), e))
    return out


def labels(e: dict) -> list[str]:
    return [e.get("name") or "", *(e.get("synonyms") or [])]


def scope_countries(slug: str) -> list[str]:
    path = SCOPES / f"{slug}.md"
    if not path.exists():
        return []
    m = re.search(r"\*\*Country:\*\*\s*([^.*\n]+)", path.read_text(encoding="utf-8"))
    return re.findall(r"\b[A-Z]{2}\b", m.group(1)) if m else []


def status(slug: str) -> str:
    md = HERE / f"{slug}.md"
    if not md.exists():
        return "not started"
    for line in md.read_text(encoding="utf-8").splitlines()[:5]:
        if line.startswith("Status:"):
            return line[len("Status:"):].strip()
    return "no Status line"


def siblings(slug: str) -> list[str]:
    """Other scoped slugs that share a country with `slug`."""
    mine = set(scope_countries(slug))
    return [p.stem for p in sorted(SCOPES.glob("*.md"))
            if p.stem != slug and mine & set(scope_countries(p.stem))]


def research_files(kind: str) -> list[Path]:
    return sorted(HERE.glob(f"*.{kind}.yaml"))


def show_slug(slug: str) -> None:
    countries = scope_countries(slug)
    if not countries:
        raise SystemExit(f"scopes/{slug}.md has no **Country:** line")
    text = (ALLOWLIST / "regions.yaml").read_text(encoding="utf-8").splitlines()
    for line in text:
        if not line.startswith("#"):
            break
        print(line)
    entries = [(n, l) for n, l, e in lines_of(ALLOWLIST / "regions.yaml") if e.get("country") in countries]
    print(f"\n# Existing regions for {', '.join(countries)} ({len(entries)}), regions.yaml line: entry")
    for n, l in entries:
        print(f"{n}: {l}")
    print(f"\n# Other research slices for {', '.join(countries)}")
    for s in siblings(slug):
        print(f"{s}: {status(s)}")


def find(kind: str, names: list[str]) -> None:
    files = [ALLOWLIST / f"{kind}s.yaml", *research_files(f"{kind}s")]
    for name in names:
        key = _fold(name)
        hits = [(p, n, l) for p in files for n, l, e in lines_of(p) if key in {_fold(x) for x in labels(e)}]
        if not hits:
            print(f"{name}: not found")
        for p, n, l in hits:
            print(f"{name}: {p.name}:{n}: {l}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("slug", nargs="?")
    ap.add_argument("--grape", nargs="+", metavar="NAME")
    ap.add_argument("--region", nargs="+", metavar="NAME")
    args = ap.parse_args(argv)
    if not (args.slug or args.grape or args.region):
        ap.error("give a slug, --grape or --region")
    if args.slug:
        show_slug(args.slug)
    if args.grape:
        find("grape", args.grape)
    if args.region:
        find("region", args.region)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
