#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "=========================================="
echo "GISArchAgent - Setup"
echo "=========================================="
echo ""

echo "Checking Python version..."
python_version="$(python3 --version 2>&1 | awk '{print $2}')"
echo "Found Python $python_version"
python3 - <<'PY'
import sys

minimum = (3, 10)
if sys.version_info < minimum:
    raise SystemExit(
        f"Error: Python {minimum[0]}.{minimum[1]} or higher is required"
    )
PY
echo "Python version OK"
echo ""

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists"
fi
echo ""

echo "Installing Python dependencies..."
source venv/bin/activate
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt -r requirements-dev.txt
echo "Python dependencies installed"
echo ""

if ! command -v npm >/dev/null 2>&1; then
    echo "Error: npm is required for the React frontend bootstrap"
    echo "Install Node.js 20+ and rerun ./setup.sh"
    exit 1
fi

echo "Installing frontend dependencies..."
if [ -f "frontend/package-lock.json" ]; then
    (
        cd frontend
        npm ci
    )
else
    (
        cd frontend
        npm install
    )
fi
echo "Frontend dependencies installed"
echo ""

if [ ! -f ".env.example" ]; then
    echo "Error: missing .env.example template"
    exit 1
fi

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env from .env.example"
else
    echo ".env already exists"
fi
echo ""

echo "Creating local data directories..."
mkdir -p data/raw data/processed data/vectorstore data/local_projects data/cache
echo "Local data directories ready"
echo ""

echo "=========================================="
echo "Setup Complete"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review .env and set OPENAI_* values if you want synthesis or vision."
echo "2. Start the canonical dev stack with ./run_webapp.sh."
echo "3. Optional sanity checks:"
echo "   ./venv/bin/python -m pytest tests/integration/api/test_fastapi_endpoints.py -q"
echo "   (cd frontend && npm run build)"
echo "4. Optional vector/data status:"
echo "   python3 scripts/data_cli.py status -v"
echo "   python3 scripts/quick_status.py"
