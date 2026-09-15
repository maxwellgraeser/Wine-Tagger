"""cellar/server/app.py — FastAPI backend for the Cellar dashboard.

Drives all three pipeline stages from one place:

    ingestion     runs ingestion/ingest.py as a subprocess
    fermentation  runs `python -m fermentation.ferment --events-json` as a
                  subprocess and streams its JSON events over SSE
    distribution  reads/edits output/wines.json, exports the Lightspeed xlsx

Run from the repo root:  .venv/bin/uvicorn cellar.server.app:app --reload
In production the built frontend (cellar/web/dist) is served at `/`.
"""

from __future__ import annotations

import asyncio
import csv
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import uuid
from collections import deque
from collections.abc import AsyncIterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.sse import EventSourceResponse, ServerSentEvent
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fermentation import store as store_mod  # noqa: E402
from fermentation.constants import DEFAULT_API_URL, DEFAULT_CONFIDENCE_THRESHOLD, DEFAULT_MODEL  # noqa: E402
from fermentation.paths import (  # noqa: E402
    INPUT_CSV, LOGS_DIR, OUTPUT_DIR, PHASE_DIRS, PHASES, RUN_STATE_PATH, WINES_JSON, run_dir,
)

PYTHON = str(PROJECT_ROOT / ".venv" / "bin" / "python")
if not Path(PYTHON).exists():
    PYTHON = sys.executable
LIBRARY_DB = PROJECT_ROOT / "fermentation" / "library_mcp" / "library.db"
SAMPLE_DIR = PROJECT_ROOT / "Sample Xlsx"
WEB_DIST = HERE.parent / "web" / "dist"
LLAMA_SCRIPT = os.environ.get("LLAMA_SCRIPT", str(PROJECT_ROOT / "gemma3n.sh"))
LLAMA_LOG = PROJECT_ROOT / ".llama-server.log"
LLAMA_PID = PROJECT_ROOT / ".llama-server.pid"

app = FastAPI(title="Cellar", version="0.1.0")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Jobs — one subprocess per stage run, events buffered + fanned out over SSE
# ---------------------------------------------------------------------------

class Job:
    def __init__(self, stage: str, cmd: list[str]) -> None:
        self.id = uuid.uuid4().hex[:12]
        self.stage = stage                # "ingest" | "ferment"
        self.cmd = cmd
        self.started_at = _now()
        self.ended_at: Optional[str] = None
        self.exit_code: Optional[int] = None
        self.run_id: Optional[str] = None
        self.events: list[dict] = []
        self.proc: Optional[asyncio.subprocess.Process] = None
        self._waiters: list[asyncio.Queue] = []

    @property
    def running(self) -> bool:
        return self.exit_code is None and self.proc is not None

    def summary(self) -> dict:
        return {
            "id": self.id, "stage": self.stage, "cmd": self.cmd,
            "started_at": self.started_at, "ended_at": self.ended_at,
            "exit_code": self.exit_code, "running": self.running,
            "run_id": self.run_id, "event_count": len(self.events),
            "last": self.events[-1] if self.events else None,
        }

    def push(self, ev: dict) -> None:
        ev.setdefault("ts", time.time())
        ev.setdefault("job_id", self.id)
        self.events.append(ev)
        if ev.get("run_id") and not self.run_id:
            self.run_id = ev["run_id"]
        for q in list(self._waiters):
            q.put_nowait(ev)

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._waiters.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        if q in self._waiters:
            self._waiters.remove(q)


JOBS: dict[str, Job] = {}
JOB_ORDER: deque[str] = deque(maxlen=50)


def _active_job() -> Optional[Job]:
    for jid in reversed(JOB_ORDER):
        j = JOBS.get(jid)
        if j and j.running:
            return j
    return None


async def _pump(job: Job) -> None:
    assert job.proc is not None and job.proc.stdout is not None
    async for raw in job.proc.stdout:
        line = raw.decode("utf-8", errors="replace").rstrip("\n")
        if not line:
            continue
        ev: dict
        if line.startswith("{"):
            try:
                ev = json.loads(line)
                if not isinstance(ev, dict):
                    raise ValueError
            except ValueError:
                ev = {"type": "log", "message": line}
        else:
            ev = {"type": "log", "message": line}
        job.push(ev)
    code = await job.proc.wait()
    job.exit_code = code
    job.ended_at = _now()
    job.push({"type": "exit", "exit_code": code,
              "message": f"process exited with code {code}"})


async def _start_job(stage: str, cmd: list[str], env: Optional[dict] = None) -> Job:
    if (active := _active_job()) is not None:
        raise HTTPException(409, f"a {active.stage} job is already running ({active.id})")
    job = Job(stage, cmd)
    full_env = dict(os.environ)
    full_env["PYTHONUNBUFFERED"] = "1"
    if env:
        full_env.update(env)
    job.proc = await asyncio.create_subprocess_exec(
        *cmd, cwd=str(PROJECT_ROOT), env=full_env,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
        stdin=asyncio.subprocess.DEVNULL,
    )
    JOBS[job.id] = job
    JOB_ORDER.append(job.id)
    job.push({"type": "start", "message": "$ " + " ".join(cmd), "stage": stage})
    asyncio.create_task(_pump(job))
    return job


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

def _file_info(p: Path) -> dict:
    if not p.exists():
        return {"exists": False, "path": str(p)}
    st = p.stat()
    return {
        "exists": True, "path": str(p), "size": st.st_size,
        "mtime": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(timespec="seconds"),
    }


def _csv_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _llama_status(api_url: str = DEFAULT_API_URL) -> dict:
    base = api_url.split("/v1/")[0]
    out: dict[str, Any] = {"ok": False, "base_url": base, "api_url": api_url, "models": []}
    try:
        r = requests.get(f"{base}/health", timeout=1.5)
        out["ok"] = r.status_code == 200
        out["health"] = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
    except requests.RequestException as exc:
        out["error"] = str(exc.__class__.__name__)
        return out
    try:
        r = requests.get(f"{base}/v1/models", timeout=1.5)
        if r.ok:
            out["models"] = [m.get("id") for m in r.json().get("data", [])]
    except (requests.RequestException, ValueError):
        pass
    return out


def _run_ids() -> list[str]:
    if not LOGS_DIR.exists():
        return []
    return sorted((p.name for p in LOGS_DIR.iterdir() if (p / "run.json").exists()), reverse=True)


def _read_json(p: Path) -> Optional[Any]:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


@app.get("/api/status")
def api_status() -> dict:
    store = store_mod.load_store()
    wines = store["wines"]
    by_status: dict[str, int] = {}
    for w in wines:
        by_status[w.get("tag_status") or "pending"] = by_status.get(w.get("tag_status") or "pending", 0) + 1
    csv_rows = _csv_rows(INPUT_CSV)
    active = _active_job()
    run_state = _read_json(RUN_STATE_PATH) if RUN_STATE_PATH.exists() else None
    runs = _run_ids()
    return {
        "now": _now(),
        "project_root": str(PROJECT_ROOT),
        "defaults": {
            "api_url": DEFAULT_API_URL, "model": DEFAULT_MODEL,
            "confidence_threshold": DEFAULT_CONFIDENCE_THRESHOLD,
        },
        "llama": _llama_status(),
        "ingestion": {
            "inputs": [
                _file_info(p) | {"name": p.name}
                for p in sorted(SAMPLE_DIR.glob("*.xlsx"))
            ] if SAMPLE_DIR.exists() else [],
            "csv": _file_info(INPUT_CSV) | {"row_count": len(csv_rows)},
        },
        "fermentation": {
            "wines_json": _file_info(WINES_JSON) | {"count": len(wines), "by_status": by_status},
            "last_run_id": store.get("last_run_id"),
            "run_state": run_state,
            "runs": runs[:10],
        },
        "active_job": active.summary() if active else None,
        "jobs": [JOBS[j].summary() for j in reversed(JOB_ORDER) if j in JOBS][:10],
    }


# ---------------------------------------------------------------------------
# Stage runners
# ---------------------------------------------------------------------------

@app.post("/api/ingest/run")
async def api_ingest_run() -> dict:
    job = await _start_job("ingest", [PYTHON, str(PROJECT_ROOT / "ingestion" / "ingest.py")])
    return job.summary()


class FermentRequest(BaseModel):
    force: bool = False
    limit: int = 0
    confidence_threshold: Optional[int] = None
    model: Optional[str] = None
    api_url: Optional[str] = None
    no_producer_gate: bool = False
    phase: Optional[str] = None      # re-run from this phase...
    run_id: Optional[str] = None     # ...over this run's logs


@app.post("/api/ferment/run")
async def api_ferment_run(req: FermentRequest) -> dict:
    cmd = [PYTHON, "-m", "fermentation.ferment", "--events-json"]
    if req.force:
        cmd.append("--force")
    if req.limit and req.limit > 0:
        cmd += ["--limit", str(req.limit)]
    if req.confidence_threshold is not None:
        cmd += ["--confidence-threshold", str(req.confidence_threshold)]
    if req.model:
        cmd += ["--model", req.model]
    if req.api_url:
        cmd += ["--api-url", req.api_url]
    if req.no_producer_gate:
        cmd.append("--no-producer-gate")
    if req.phase:
        if req.phase not in PHASES:
            raise HTTPException(400, f"phase must be one of {PHASES}")
        if not req.run_id:
            raise HTTPException(400, "phase requires run_id")
        cmd += ["--phase", req.phase, "--run-id", req.run_id]
    job = await _start_job("ferment", cmd)
    return job.summary()


@app.post("/api/llama/start")
def api_llama_start() -> dict:
    st = _llama_status()
    if st["ok"]:
        return {"started": False, "reason": "already running", "llama": st}
    script = Path(LLAMA_SCRIPT)
    if not script.exists():
        raise HTTPException(400, f"LLAMA_SCRIPT not found: {script}")
    if shutil.which("llama-server") is None:
        raise HTTPException(400, "llama-server is not on PATH")
    port = st["base_url"].rsplit(":", 1)[-1] or "8080"
    with open(LLAMA_LOG, "ab") as log:
        proc = subprocess.Popen(
            [str(script), "--port", port], cwd=str(PROJECT_ROOT),
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
        )
    LLAMA_PID.write_text(str(proc.pid))
    return {"started": True, "pid": proc.pid, "script": str(script), "log": str(LLAMA_LOG)}


@app.get("/api/llama/log")
def api_llama_log(lines: int = 60) -> dict:
    if not LLAMA_LOG.exists():
        return {"lines": []}
    content = LLAMA_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
    return {"lines": content[-lines:]}


# ---------------------------------------------------------------------------
# Jobs + SSE
# ---------------------------------------------------------------------------

@app.get("/api/jobs")
def api_jobs() -> list[dict]:
    return [JOBS[j].summary() for j in reversed(JOB_ORDER) if j in JOBS]


@app.get("/api/jobs/{job_id}")
def api_job(job_id: str) -> dict:
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(404, "no such job")
    return job.summary() | {"events": job.events}


@app.post("/api/jobs/{job_id}/stop")
async def api_job_stop(job_id: str) -> dict:
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(404, "no such job")
    if job.running and job.proc is not None:
        job.proc.send_signal(2)  # SIGINT -> ferment saves run state and exits
        job.push({"type": "info", "message": "stop requested (SIGINT sent)"})
    return job.summary()


@app.get("/api/jobs/{job_id}/events", response_class=EventSourceResponse)
async def api_job_events(job_id: str, after: int = 0) -> AsyncIterable[ServerSentEvent]:
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(404, "no such job")
    q = job.subscribe()
    try:
        # Replay history first so a late subscriber sees everything.
        for i, ev in enumerate(job.events[after:], start=after):
            yield ServerSentEvent(data=ev, event=ev.get("type", "log"), id=str(i))
        if not job.running:
            return
        idx = len(job.events)
        while True:
            try:
                ev = await asyncio.wait_for(q.get(), timeout=15)
            except asyncio.TimeoutError:
                yield ServerSentEvent(comment="keepalive")
                if not job.running:
                    return
                continue
            yield ServerSentEvent(data=ev, event=ev.get("type", "log"), id=str(idx))
            idx += 1
            if ev.get("type") == "exit":
                return
    finally:
        job.unsubscribe(q)


# ---------------------------------------------------------------------------
# Ingestion output
# ---------------------------------------------------------------------------

@app.get("/api/ingestion/rows")
def api_ingestion_rows() -> dict:
    rows = _csv_rows(INPUT_CSV)
    return {"path": str(INPUT_CSV), "columns": list(rows[0].keys()) if rows else [], "rows": rows}


# ---------------------------------------------------------------------------
# Wines (output/wines.json)
# ---------------------------------------------------------------------------

@app.get("/api/wines")
def api_wines() -> dict:
    store = store_mod.load_store()
    return {
        "generated_at": store.get("generated_at"),
        "last_run_id": store.get("last_run_id"),
        "source_csv": store.get("source_csv"),
        "wines": store["wines"],
    }


def _phase_log(run_id: Optional[str], phase: str, product_id: str) -> Optional[dict]:
    if not run_id:
        return None
    return _read_json(run_dir(run_id) / PHASE_DIRS[phase] / f"{product_id}.json")


@app.get("/api/wines/{wine_id}")
def api_wine(wine_id: str, run_id: Optional[str] = None) -> dict:
    store = store_mod.load_store()
    wine = store_mod.find_wine(store, wine_id)
    if wine is None:
        raise HTTPException(404, "no such wine")
    # Every run that has any log for this wine, newest first.
    history = [
        r for r in _run_ids()
        if any((run_dir(r) / d / f"{wine_id}.json").exists() for d in ("search", "scorer", "tagger", "final"))
    ]
    rid = run_id or wine.get("run_id")
    if rid not in history and history:
        rid = history[0]
    logs = {
        "run_id": rid,
        "search": _phase_log(rid, "search", wine_id),
        "scorer": _phase_log(rid, "score", wine_id),
        "tagger": _phase_log(rid, "tag", wine_id),
        "final": _read_json(run_dir(rid) / "final" / f"{wine_id}.json") if rid else None,
    }
    return {"wine": wine, "logs": logs, "runs": history}


class WinePatch(BaseModel):
    country: Optional[str] = None
    region: Optional[list[str]] = None
    grapes: Optional[list[str]] = None
    is_blend: Optional[bool] = None
    organic: Optional[bool] = None
    confidence: Optional[int] = None
    tag_status: Optional[str] = None


@app.patch("/api/wines/{wine_id}")
def api_wine_patch(wine_id: str, patch: WinePatch) -> dict:
    if patch.tag_status is not None and patch.tag_status not in ("auto", "needs_review", "manual", "pending"):
        raise HTTPException(400, "bad tag_status")
    store = store_mod.load_store()
    fields = patch.model_dump(exclude_unset=True)
    row = store_mod.update_wine_tags(store, wine_id, **fields)
    if row is None:
        raise HTTPException(404, "no such wine")
    store_mod.save_store(store)
    return row


# ---------------------------------------------------------------------------
# Runs + logs
# ---------------------------------------------------------------------------

@app.get("/api/runs")
def api_runs() -> list[dict]:
    out = []
    for rid in _run_ids():
        rj = _read_json(run_dir(rid) / "run.json") or {}
        out.append({
            "run_id": rid,
            "started_at": rj.get("started_at"), "ended_at": rj.get("ended_at"),
            "status": rj.get("status"), "product_count": len(rj.get("product_ids") or []),
            "phases": {ph: (rj.get("phases") or {}).get(ph, {}) for ph in PHASES},
            "config": rj.get("config"),
        })
    return out


@app.get("/api/runs/{run_id}")
def api_run(run_id: str) -> dict:
    rj = _read_json(run_dir(run_id) / "run.json")
    if rj is None:
        raise HTTPException(404, "no such run")
    files = {}
    for ph, folder in list(PHASE_DIRS.items()) + [("final", "final")]:
        d = run_dir(run_id) / folder
        files[ph] = sorted(p.stem for p in d.glob("*.json")) if d.exists() else []
    return {"run": rj, "files": files}


@app.get("/api/runs/{run_id}/events")
def api_run_events(run_id: str, limit: int = 500) -> dict:
    p = run_dir(run_id) / "events.jsonl"
    if not p.exists():
        raise HTTPException(404, "no events for run")
    lines = p.read_text(encoding="utf-8").splitlines()[-limit:]
    events = []
    for ln in lines:
        try:
            events.append(json.loads(ln))
        except ValueError:
            continue
    return {"events": events}


@app.get("/api/runs/{run_id}/{phase}/{product_id}")
def api_run_phase_file(run_id: str, phase: str, product_id: str) -> Any:
    folder = PHASE_DIRS.get(phase, phase)
    if folder not in ("search", "scorer", "tagger", "final"):
        raise HTTPException(400, "phase must be search|score|tag|final")
    data = _read_json(run_dir(run_id) / folder / f"{product_id}.json")
    if data is None:
        raise HTTPException(404, "no log file")
    return data


# ---------------------------------------------------------------------------
# Library (canonical vocab for the tag editor)
# ---------------------------------------------------------------------------

def _lib() -> sqlite3.Connection:
    if not LIBRARY_DB.exists():
        raise HTTPException(503, "library.db not built")
    conn = sqlite3.connect(f"file:{LIBRARY_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/api/library/countries")
def api_lib_countries() -> list[str]:
    with _lib() as c:
        return [r["name"] for r in c.execute(
            "SELECT name FROM countries WHERE is_canonical=1 ORDER BY name")]


@app.get("/api/library/regions")
def api_lib_regions(country: Optional[str] = None) -> list[dict]:
    with _lib() as c:
        sql = ("SELECT r.name, c.name AS country, r.classification FROM regions r "
               "LEFT JOIN countries c ON c.id = r.country_id WHERE r.is_canonical=1")
        args: tuple = ()
        if country:
            sql += " AND c.name = ?"
            args = (country,)
        return [dict(r) for r in c.execute(sql + " ORDER BY r.name", args)]


@app.get("/api/library/grapes")
def api_lib_grapes() -> list[dict]:
    with _lib() as c:
        return [dict(r) for r in c.execute(
            "SELECT canonical_name AS name, color FROM grapes WHERE is_canonical=1 ORDER BY canonical_name")]


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

@app.get("/api/export.xlsx")
def api_export(status: Optional[str] = None) -> Response:
    import openpyxl

    store = store_mod.load_store()
    rows = store_mod.export_rows(store)
    if status:
        wanted = set(status.split(","))
        keep = {w["id"] for w in store["wines"] if w.get("tag_status") in wanted}
        rows = [r for r in rows if r["id"] in keep]
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "products"
    ws.append(["id", "name", "tags"])
    for r in rows:
        ws.append([r["id"], r["name"], r["tags"]])
    buf = io.BytesIO()
    wb.save(buf)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "lightspeed-export.xlsx").write_bytes(buf.getvalue())
    return Response(
        content=buf.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="lightspeed-export.xlsx"'},
    )


# ---------------------------------------------------------------------------
# Frontend (built) — mounted last so /api wins
# ---------------------------------------------------------------------------

if WEB_DIST.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str) -> FileResponse:
        target = WEB_DIST / path
        if path and target.is_file():
            return FileResponse(target)
        return FileResponse(WEB_DIST / "index.html")
