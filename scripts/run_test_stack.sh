#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUNTIME_DIR="$ROOT_DIR/.playwright-runtime"
PYTHON_BIN="${GISARCHAGENT_PYTHON_BIN:-}"

rm -rf "$RUNTIME_DIR"
mkdir -p "$RUNTIME_DIR/cache" "$RUNTIME_DIR/vectorstore"
cp "$ROOT_DIR/data/samples/iplan_sample_data.json" "$RUNTIME_DIR/iplan_layers.json"

export GISARCHAGENT_DATA_FILE="$RUNTIME_DIR/iplan_layers.json"
export GISARCHAGENT_VECTORSTORE_DIR="$RUNTIME_DIR/vectorstore"
export GISARCHAGENT_CACHE_DIR="$RUNTIME_DIR/cache"

if [ -z "$PYTHON_BIN" ]; then
    if [ -x "$ROOT_DIR/venv/bin/python" ]; then
        PYTHON_BIN="$ROOT_DIR/venv/bin/python"
    else
        PYTHON_BIN="$(command -v python3)"
    fi
fi

cd "$ROOT_DIR"
exec "$PYTHON_BIN" -m uvicorn src.api.app:app --host 127.0.0.1 --port 8001
