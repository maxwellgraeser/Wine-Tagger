#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ensure openpyxl is available
if ! python3 -c "import openpyxl" 2>/dev/null; then
  echo "Installing openpyxl..."
  pip3 install --quiet openpyxl
fi

python3 "$SCRIPT_DIR/ingest.py"
