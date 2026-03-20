# Installation

## Prerequisites
- macOS/Linux shell environment.
- Python 3.10+ (`pytest.ini` enforces minimum 3.10).
- Optional: Chrome installed for CDP-based pydoll flows.

## Install
```bash
# from repo root
./setup.sh
```

What `setup.sh` does (repo-sourced):
- creates `venv/`
- installs Python dependencies from `requirements.txt` and `requirements-dev.txt`
- installs frontend dependencies from `frontend/package-lock.json`
- creates `.env` from `.env.example` if missing
- prepares `data/` directories
- does not auto-build the vector DB

## Verify installation
```bash
./venv/bin/python -m pytest -m unit
cd frontend && npm run build
```

## Optional dependency fix
If tests fail with `ModuleNotFoundError: pydoll`:
```bash
./venv/bin/pip install pydoll-python
```

## Next
- Continue with `docs/getting_started/quickstart.md`.
