"""Replay every region / grape name the tagger ever asked the library for.

Reads `logs/*/tagger/*.json`, collects the names from `lookup_region`,
`lookup_grape` and `submit_tags` calls (with the country the model gave,
if any), and resolves each against a library.db. With `--baseline`, it
does the same against an older DB and lists every name whose result
changed. No LLM time: this is the cheap check that a library change helps.

    python -m fermentation.library_mcp.seed.research.replay_lookups --baseline /path/to/old.db
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from pathlib import Path

from ... import server

REPO = Path(__file__).resolve().parents[4]


def _calls(logs: Path) -> Counter:
    """(kind, name, country) -> times asked. kind is region / grape."""
    seen: Counter = Counter()
    for f in sorted(logs.glob("*/tagger/*.json")):
        try:
            transcript = json.loads(f.read_text(encoding="utf-8")).get("transcript") or []
        except (OSError, json.JSONDecodeError):
            continue
        for msg in transcript:
            for call in msg.get("tool_calls") or []:
                fn = call.get("function") or {}
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                except json.JSONDecodeError:
                    continue
                if not isinstance(args, dict):
                    continue
                name = fn.get("name")
                if name == "lookup_region" and args.get("name"):
                    seen[("region", args["name"], args.get("country"))] += 1
                elif name == "lookup_grape" and args.get("name"):
                    seen[("grape", args["name"], None)] += 1
                elif name == "submit_tags":
                    for r in args.get("region") or []:
                        if isinstance(r, str) and r.strip():
                            seen[("region", r, args.get("country"))] += 1
                    for g in args.get("grapes") or []:
                        if isinstance(g, str) and g.strip():
                            seen[("grape", g, None)] += 1
    return seen


def _use_db(path: Path) -> None:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    (server._COUNTRIES, server._REGIONS, server._GRAPES,
     server._C_IDX, server._R_IDX, server._G_IDX) = server._load_index(conn)
    server._CONN = conn


def _status(kind: str, name: str, country: str | None) -> str:
    if kind == "region":
        r = server.lookup_region(name, country)
    else:
        r = server.lookup_grape(name)
        if r["is_phrase"]:
            return "phrase"
    if not r["known"]:
        return "unknown"
    return f"{'placeholder' if r['is_placeholder'] else 'ok'}: {r['canonical']}"


def _resolve_all(db: Path, calls: Counter) -> dict:
    _use_db(db)
    return {k: _status(*k) for k in calls}


def _summary(label: str, results: dict, calls: Counter) -> list[str]:
    out = [f"{label}:"]
    for kind in ("region", "grape"):
        tally: Counter = Counter()
        for k, st in results.items():
            if k[0] == kind:
                tally[st.split(":")[0]] += calls[k]
        total = sum(tally.values())
        out.append(f"  {kind:6} {total:4} asked: " + ", ".join(f"{s} {n}" for s, n in tally.most_common()))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", type=Path, default=server.DB_PATH)
    ap.add_argument("--baseline", type=Path, help="older library.db to compare against")
    ap.add_argument("--logs", type=Path, default=REPO / "logs")
    args = ap.parse_args(argv)

    calls = _calls(args.logs)
    new = _resolve_all(args.db, calls)
    lines = [f"{len(calls)} distinct (kind, name, country) lookups from {args.logs}"]
    if args.baseline:
        old = _resolve_all(args.baseline, calls)
        lines += _summary(f"baseline {args.baseline.name}", old, calls)
        lines += _summary(f"current  {args.db.name}", new, calls)
        changed = [(k, old[k], new[k]) for k in sorted(calls, key=str) if old[k] != new[k]]
        lines.append(f"\nChanged ({len(changed)}):")
        lines += [f"  {k[0]:6} {k[1]!r}{f' [{k[2]}]' if k[2] else ''}: {o} -> {n}" for k, o, n in changed]
    else:
        lines += _summary(f"current {args.db.name}", new, calls)
    unknown = sorted((k for k, st in new.items() if st == "unknown"), key=lambda k: (-calls[k], str(k)))
    lines.append(f"\nStill unknown ({len(unknown)}):")
    lines += [f"  {k[0]:6} {k[1]!r}{f' [{k[2]}]' if k[2] else ''} x{calls[k]}" for k in unknown]
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
