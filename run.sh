#!/usr/bin/env bash
# Starts Cellar, the Wine Warehouse dashboard. Everything else (ingest, ferment,
# starting/stopping the llama-server) is done from the dashboard.
#
#   ./run.sh          build the frontend (if needed) and serve on http://localhost:8000
#   ./run.sh dev      hot reload: uvicorn on :8000 + vite on :5173
#
# Env: CELLAR_PORT (default 8000), VITE_PORT (default 5173, dev mode only),
#      LLAMA_MODEL (qwen | gemma, default qwen)
# A second checkout (e.g. a git worktree) can run beside the main one with
#   CELLAR_PORT=8010 VITE_PORT=5183 ./run.sh dev
set -euo pipefail
cd "$(dirname "$0")"

PYTHON=".venv/bin/python"
[[ -x "$PYTHON" ]] || { echo "error: $PYTHON missing — create the venv and pip install -r requirements.txt" >&2; exit 1; }
"$PYTHON" -c "import fastapi, uvicorn" 2>/dev/null || "$PYTHON" -m pip install -q -r requirements.txt

PORT="${CELLAR_PORT:-8000}"
VITE_PORT="${VITE_PORT:-5173}"
export CELLAR_PORT="$PORT" VITE_PORT   # vite.config.ts reads both
MODE="${1:-serve}"

kill_port() {
    local port="$1"
    local pids
    pids="$(lsof -ti "tcp:$port" 2>/dev/null || true)"
    if [[ -n "$pids" ]]; then
        echo "Killing existing process(es) on port $port: $pids"
        kill $pids 2>/dev/null || true
        sleep 0.5
        pids="$(lsof -ti "tcp:$port" 2>/dev/null || true)"
        [[ -n "$pids" ]] && kill -9 $pids 2>/dev/null || true
    fi
    return 0
}

kill_port "$PORT"
[[ "$MODE" == "dev" ]] && kill_port "$VITE_PORT"

if [[ ! -d cellar/web/node_modules ]]; then
    echo "Installing frontend dependencies..."
    (cd cellar/web && npm install)
fi

if [[ "$MODE" == "dev" ]]; then
    trap 'kill 0' EXIT
    "$PYTHON" -m uvicorn cellar.server.app:app --port "$PORT" --reload --reload-dir cellar/server --reload-dir fermentation &
    (cd cellar/web && npm run dev)
else
    if [[ ! -f cellar/web/dist/index.html || -n "$(find cellar/web/src -newer cellar/web/dist/index.html -print -quit 2>/dev/null)" ]]; then
        echo "Building frontend..."
        (cd cellar/web && npm run build)
    fi
    echo "Cellar → http://localhost:$PORT"
    exec "$PYTHON" -m uvicorn cellar.server.app:app --port "$PORT"
fi
