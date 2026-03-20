#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

BACKEND_HOST="${GISARCHAGENT_BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${GISARCHAGENT_BACKEND_PORT:-8000}"
FRONTEND_HOST="${GISARCHAGENT_FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${GISARCHAGENT_FRONTEND_PORT:-5173}"
PORT_RESOLVER="scripts/dev_stack_ports.py"

if [ ! -x "./venv/bin/python" ]; then
    echo "Missing virtual environment. Run ./setup.sh first."
    exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
    echo "npm is required to run the React frontend. Install Node.js 20+ and rerun ./setup.sh."
    exit 1
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "Frontend dependencies are missing. Running npm ci..."
    (
        cd frontend
        npm ci
    )
fi

source venv/bin/activate

if [ ! -f "$PORT_RESOLVER" ]; then
    echo "Missing port resolver helper at $PORT_RESOLVER"
    exit 1
fi

resolve_port() {
    python3 "$PORT_RESOLVER" --host "$1" --port "$2"
}

RESOLVED_BACKEND_PORT="$(resolve_port "$BACKEND_HOST" "$BACKEND_PORT")"
RESOLVED_FRONTEND_PORT="$(resolve_port "$FRONTEND_HOST" "$FRONTEND_PORT")"

if [ "$RESOLVED_BACKEND_PORT" != "$BACKEND_PORT" ]; then
    echo "Port ${BACKEND_PORT} is already in use; using backend port ${RESOLVED_BACKEND_PORT} instead."
fi

if [ "$RESOLVED_FRONTEND_PORT" != "$FRONTEND_PORT" ]; then
    echo "Port ${FRONTEND_PORT} is already in use; using frontend port ${RESOLVED_FRONTEND_PORT} instead."
fi

BACKEND_URL="http://${BACKEND_HOST}:${RESOLVED_BACKEND_PORT}"
FRONTEND_URL="http://${FRONTEND_HOST}:${RESOLVED_FRONTEND_PORT}"
export VITE_API_BASE_URL="$BACKEND_URL"

cleanup() {
    if [ -n "${FRONTEND_PID:-}" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    if [ -n "${BACKEND_PID:-}" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
}

trap cleanup EXIT INT TERM

echo "Starting FastAPI backend on ${BACKEND_URL}"
./venv/bin/python -m uvicorn src.api.app:app --reload --host "$BACKEND_HOST" --port "$RESOLVED_BACKEND_PORT" &
BACKEND_PID=$!

echo "Starting React frontend on ${FRONTEND_URL}"
(
    cd frontend
    npm run dev -- --host "$FRONTEND_HOST" --port "$RESOLVED_FRONTEND_PORT"
) &
FRONTEND_PID=$!

echo ""
echo "GISArchAgent dev stack is starting:"
echo "- Backend:  ${BACKEND_URL}"
echo "- Frontend: ${FRONTEND_URL}"
echo "Press Ctrl-C to stop both processes."

while kill -0 "$BACKEND_PID" 2>/dev/null && kill -0 "$FRONTEND_PID" 2>/dev/null; do
    sleep 1
done

if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    wait "$BACKEND_PID" || true
    echo "FastAPI backend exited."
fi

if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
    wait "$FRONTEND_PID" || true
    echo "React frontend exited."
fi
