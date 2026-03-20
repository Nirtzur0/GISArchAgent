# Tests

This repo uses **pytest**.

The suite is organized by the test pyramid:

- `tests/unit/`: pure logic (domain/application/mappers). No real DB/network.
- `tests/integration/`: boundary contracts (Chroma persistence, repository wiring). Uses temp dirs.
- `tests/e2e/`: canonical FastAPI smoke checks + end-to-end output sanity.
- `tests/helpers/`: shared factories/fakes/assertions (used heavily by `data_contracts`).

## Quick start

```bash
# Full suite
./venv/bin/python -m pytest

# Unit only
./venv/bin/python -m pytest -m unit

# Integration only
./venv/bin/python -m pytest -m integration

# E2E only
./venv/bin/python -m pytest -m e2e

# Contract checks only
./venv/bin/python -m pytest -m data_contracts

# Maintained browser smoke
cd frontend && npm run test:e2e
```

## Markers

Markers are declared in `/Users/nirtzur/Documents/projects/GISArchAgent/pytest.ini`.

Common ones:
- `unit`, `integration`, `e2e`
- `data_contracts` (range/completeness checks)
- `db`, `ui`

## Notes

- Integration tests create isolated Chroma persistence dirs via `tmp_path_factory`.
- `pytest -m e2e` now validates the maintained FastAPI runtime, not the legacy Streamlit surface.
- Browser-level coverage for the maintained React UI lives in `frontend/tests/app.spec.ts`.
- Unit tests should not touch Selenium, live iPlan discovery, or real network.
