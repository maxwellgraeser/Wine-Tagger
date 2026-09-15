#!/usr/bin/env bash
# Cellar — the Wine Warehouse dashboard.
#
#   ./cellar/run.sh          production-ish: builds the frontend once (if needed)
#                            and serves everything from FastAPI on :8000
#   ./cellar/run.sh dev      hot-reload: uvicorn on :8000 + vite on :5173
#
# Env: CELLAR_PORT (default 8000), LLAMA_SCRIPT (default ./gemma3n.sh)
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON=".venv/bin/python"
[[ -x "$PYTHON" ]] || { echo "error: $PYTHON missing — create the venv and pip install -r requirements.txt" >&2; exit 1; }
"$PYTHON" -c "import fastapi, uvicorn" 2>/dev/null || "$PYTHON" -m pip install -q -r requirements.txt

PORT="${CELLAR_PORT:-8000}"
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
}

kill_port "$PORT"
[[ "$MODE" == "dev" ]] && kill_port 5173

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
