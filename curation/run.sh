#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# ---------------------------------------------------------------------------
# Runtime config — model is sourced from curation/constants.py (DEFAULT_MODEL).
# Override per-run via the --model flag or CURATION_MODEL env var if needed.
# ---------------------------------------------------------------------------
: "${CURATION_API_URL:=http://localhost:8080/v1/chat/completions}"
: "${CURATION_CONFIDENCE_THRESHOLD:=75}"

# Install deps if needed
if ! python3 -c "import requests" 2>/dev/null; then
    echo "Installing requests..."
    pip3 install requests
fi

exec python3 curate.py \
    --api-url "$CURATION_API_URL" \
    --confidence-threshold "$CURATION_CONFIDENCE_THRESHOLD" \
    "$@"
