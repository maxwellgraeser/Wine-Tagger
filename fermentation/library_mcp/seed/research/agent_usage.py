"""Token use per research agent, read from Claude Code's transcripts.

    python -m fermentation.library_mcp.seed.research.agent_usage              # this session
    python -m fermentation.library_mcp.seed.research.agent_usage <session-id>

Every turn re-sends the whole context, so the re-read column (cache reads)
is the main cost, not output. `base` is the first turn's context: system
prompt and tool definitions, before the agent has read anything. Output
token counts in transcripts are unreliable (streaming), so they are left out.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
PROJECTS = Path.home() / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(REPO))


def _usage(path: Path) -> dict:
    seen: dict[str, dict] = {}
    models: set[str] = set()
    start = None
    for line in path.open():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        start = start or r.get("timestamp")
        msg = r.get("message")
        if r.get("type") != "assistant" or not isinstance(msg, dict) or msg.get("model") == "<synthetic>":
            continue
        u = msg.get("usage") or {}
        seen.setdefault(msg.get("id"), u)  # multi-block messages repeat the same usage
        models.add(msg.get("model"))
    ctx = [(u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
           + (u.get("cache_read_input_tokens") or 0) for u in seen.values()]
    return {
        "start": datetime.fromisoformat(start.replace("Z", "+00:00")).astimezone().strftime("%m-%d %H:%M") if start else "",
        "models": ",".join(sorted(m for m in models if m)),
        "turns": len(ctx),
        "base": ctx[0] if ctx else 0,
        "peak": max(ctx, default=0),
        "read": sum(u.get("cache_read_input_tokens") or 0 for u in seen.values()),
        "write": sum(u.get("cache_creation_input_tokens") or 0 for u in seen.values()),
    }


def main(argv: list[str]) -> int:
    session = argv[0] if argv else os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    main_log = PROJECTS / f"{session}.jsonl"
    if not session or not main_log.exists():
        print(f"no transcript for session {session!r} in {PROJECTS}")
        return 1
    rows = [("main thread", _usage(main_log))]
    for meta in sorted((PROJECTS / session / "subagents").glob("agent-*.meta.json")):
        desc = json.loads(meta.read_text()).get("description", "?")
        rows.append((desc, _usage(meta.with_name(meta.name.replace(".meta.json", ".jsonl")))))
    print(f"{'start':11} {'agent':42} {'model':16} {'turns':>5} {'base':>6} {'peak':>6} {'re-read':>8} {'written':>8}")
    for desc, u in sorted(rows, key=lambda r: r[1]["start"]):
        print(f"{u['start']:11} {desc[:42]:42} {u['models'][:16]:16} {u['turns']:5} {u['base'] // 1000:5}K "
              f"{u['peak'] // 1000:5}K {u['read'] / 1e6:7.1f}M {u['write'] // 1000:7}K")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
