#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# ---------------------------------------------------------------------------
# Runs fermentation end-to-end: ensures a llama-server is up, then runs
# `python -m fermentation.ferment` with any flags passed to this script.
#
#   ./ferment.sh --force --limit 3
#   LLAMA_SCRIPT=./gemma3n.sh ./ferment.sh
#
# Default model is Qwen2.5-7B-Instruct: gemma3n has no working tool-call
# support in llama.cpp (its chat template ignores `tools`, and its native
# tool_code/tool_output convention isn't parsed by tagger.py), so wines tag
# as needs_review with no tags even when web context is good.
#
# The library_mcp server is NOT started here — tagger.py spawns it as a stdio
# subprocess for the duration of the run.
#
# On macOS the llama-server opens in its own Terminal window (Ctrl-C there to
# stop it) and is left running so the next run skips the model load. Set
# LLAMA_WINDOW=0 to run it in the background instead, logging to $LLAMA_LOG;
# stop that one with: kill "$(cat .llama-server.pid)"
# ---------------------------------------------------------------------------
: "${FERMENTATION_API_URL:=http://localhost:8080/v1/chat/completions}"
: "${LLAMA_SCRIPT:=./qwen25-7b.sh}"
: "${LLAMA_LOG:=.llama-server.log}"
: "${LLAMA_STARTUP_TIMEOUT:=600}"   # seconds; first run downloads the GGUF
export FERMENTATION_API_URL

PYTHON=".venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
    echo "error: $PYTHON not found — create the venv and pip install -r requirements.txt" >&2
    exit 1
fi

# http://host:port/v1/chat/completions -> http://host:port
BASE_URL="${FERMENTATION_API_URL%%/v1/*}"
PORT=8080
if [[ "$BASE_URL" =~ :([0-9]+)$ ]]; then
    PORT="${BASH_REMATCH[1]}"
fi

server_ready() {
    [[ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE_URL/health")" == "200" ]]
}

port_in_use() {
    lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1
}

# Opens a new Terminal.app window running the given command in this directory.
open_terminal_window() {
    local sq="'\\''" cmd
    cmd="cd '${PWD//\'/$sq}' && exec $*"
    cmd="${cmd//\\/\\\\}"
    cmd="${cmd//\"/\\\"}"
    osascript -e "tell application \"Terminal\" to do script \"$cmd\"" \
              -e 'tell application "Terminal" to activate' >/dev/null
}

if server_ready; then
    echo "llama-server already running at $BASE_URL"
else
    if port_in_use; then
        # Something (likely a still-loading llama-server) already owns the port;
        # starting another would just fail to bind, so wait for it instead.
        echo "Port $PORT is in use but not healthy yet — waiting for it..."
        LLAMA_PID=""
    elif [[ "$(uname)" == "Darwin" && "${LLAMA_WINDOW:-1}" == "1" ]]; then
        echo "Starting $LLAMA_SCRIPT on port $PORT in a new Terminal window..."
        open_terminal_window "$LLAMA_SCRIPT" --port "$PORT"
        LLAMA_PID=""
    else
        echo "Starting $LLAMA_SCRIPT on port $PORT (log: $LLAMA_LOG)..."
        nohup "$LLAMA_SCRIPT" --port "$PORT" >"$LLAMA_LOG" 2>&1 &
        LLAMA_PID=$!
        echo "$LLAMA_PID" > .llama-server.pid
    fi

    waited=0
    until server_ready; do
        if [[ -n "$LLAMA_PID" ]] && ! kill -0 "$LLAMA_PID" 2>/dev/null; then
            echo "error: llama-server exited during startup. Last log lines:" >&2
            tail -n 20 "$LLAMA_LOG" >&2
            exit 1
        fi
        if [[ -z "$LLAMA_PID" ]] && (( waited >= 10 )) && ! pgrep -f "llama-server.*--port $PORT" >/dev/null; then
            echo "error: llama-server isn't running (check its Terminal window for errors)" >&2
            exit 1
        fi
        if (( waited >= LLAMA_STARTUP_TIMEOUT )); then
            echo "error: llama-server not ready after ${LLAMA_STARTUP_TIMEOUT}s (see $LLAMA_LOG)" >&2
            exit 1
        fi
        sleep 2
        waited=$((waited + 2))
    done
    echo "llama-server ready (${waited}s)"
fi

exec "$PYTHON" -m fermentation.ferment "$@"
