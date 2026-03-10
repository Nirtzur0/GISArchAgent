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
- installs dependencies from `requirements.txt`
- creates `.env` if missing
- prepares `data/` directories
- attempts vector DB initialization

## Verify installation
```bash
./venv/bin/python -m pytest -m unit
```

## Optional dependency fix
If tests fail with `ModuleNotFoundError: pydoll`:
```bash
./venv/bin/pip install pydoll-python
```

## Next
- Continue with `docs/getting_started/quickstart.md`.
