#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUNTIME_DIR="$ROOT_DIR/.playwright-runtime"

rm -rf "$RUNTIME_DIR"
mkdir -p "$RUNTIME_DIR/cache" "$RUNTIME_DIR/vectorstore"
cp "$ROOT_DIR/data/samples/iplan_sample_data.json" "$RUNTIME_DIR/iplan_layers.json"

export GISARCHAGENT_DATA_FILE="$RUNTIME_DIR/iplan_layers.json"
export GISARCHAGENT_VECTORSTORE_DIR="$RUNTIME_DIR/vectorstore"
export GISARCHAGENT_CACHE_DIR="$RUNTIME_DIR/cache"

cd "$ROOT_DIR"
exec ./venv/bin/python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8001
