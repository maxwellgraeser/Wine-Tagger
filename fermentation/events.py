"""Progress reporting for a fermentation run.

Two consumers: a human at a terminal, and the cellar backend reading the
subprocess's stdout. With `json_lines=True` every event is printed as one
JSON object per line (and nothing else goes to stdout); otherwise a short
human-readable line is printed. Every event is also appended to
`logs/<run_id>/events.jsonl` regardless of mode.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Optional


class EventSink:
    def __init__(self, run_id: str, log_path: Optional[Path], json_lines: bool) -> None:
        self.run_id = run_id
        self.json_lines = json_lines
        self._fh = None
        if log_path is not None:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            self._fh = log_path.open("a", encoding="utf-8")

    def close(self) -> None:
        if self._fh is not None:
            self._fh.close()
            self._fh = None

    def emit(self, type_: str, message: str = "", **data: Any) -> None:
        payload = {"ts": time.time(), "run_id": self.run_id, "type": type_, "message": message}
        payload.update(data)
        if self._fh is not None:
            self._fh.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
            self._fh.flush()
        if self.json_lines:
            sys.stdout.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
        else:
            sys.stdout.write(self._human(payload) + "\n")
        sys.stdout.flush()

    # -- convenience wrappers ------------------------------------------------

    def phase_start(self, phase: str, total: int) -> None:
        self.emit("phase_start", f"=== Phase {phase}: {total} wines ===", phase=phase, total=total)

    def phase_end(self, phase: str, **counts: Any) -> None:
        self.emit("phase_end", f"=== Phase {phase} done ===", phase=phase, **counts)

    def progress(self, phase: str, index: int, total: int, product_id: str,
                 name: str, message: str, **extra: Any) -> None:
        self.emit(
            "progress", f"[{phase} {index + 1}/{total}] {name} | {message}",
            phase=phase, index=index, total=total, product_id=product_id,
            name=name, **extra,
        )

    def info(self, message: str, **extra: Any) -> None:
        self.emit("info", message, **extra)

    def error(self, message: str, **extra: Any) -> None:
        self.emit("error", message, **extra)

    @staticmethod
    def _human(payload: dict) -> str:
        return payload.get("message") or payload["type"]
