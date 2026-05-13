#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# ---------------------------------------------------------------------------
# Model / runtime config — override via env vars or edit these defaults
# ---------------------------------------------------------------------------
: "${CURATION_MODEL:=gemma3n:e4b}"
: "${CURATION_API_URL:=http://localhost:11434/v1/chat/completions}"
: "${CURATION_CONFIDENCE_THRESHOLD:=75}"

# Install deps if needed
if ! python3 -c "import requests" 2>/dev/null; then
    echo "Installing requests..."
    pip3 install requests
fi

exec python3 curate.py \
    --model "$CURATION_MODEL" \
    --api-url "$CURATION_API_URL" \
    --confidence-threshold "$CURATION_CONFIDENCE_THRESHOLD" \
    "$@"
