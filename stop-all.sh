#!/usr/bin/env bash
# Stops every local server this project can spin up:
#   - cellar backend (uvicorn, default :8000)
#   - cellar frontend dev server (vite, default :5173)
#   - llama-server (llama.cpp, default :8080) — started by ferment.sh or
#     the Cellar dashboard's "Simple" mode
#
# Safe to run any time, whether or not anything is actually up.
set -uo pipefail
cd "$(dirname "$0")"

CELLAR_PORT="${CELLAR_PORT:-8000}"
VITE_PORT=5173
LLAMA_PORT=8080

kill_port() {
    local port="$1" label="$2"
    local pids
    pids="$(lsof -ti "tcp:$port" 2>/dev/null || true)"
    if [[ -z "$pids" ]]; then
        echo "  $label (:$port) — not running"
        return
    fi
    echo "  $label (:$port) — killing pid(s) $pids"
    kill $pids 2>/dev/null || true
    sleep 0.5
    pids="$(lsof -ti "tcp:$port" 2>/dev/null || true)"
    [[ -n "$pids" ]] && kill -9 $pids 2>/dev/null || true
}

echo "Stopping local servers..."
kill_port "$CELLAR_PORT" "cellar backend"
kill_port "$VITE_PORT" "cellar frontend (vite dev)"
kill_port "$LLAMA_PORT" "llama-server"

if [[ -f .llama-server.pid ]]; then
    rm -f .llama-server.pid
fi

echo "Done."
