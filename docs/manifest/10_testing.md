# Testing Manifest

## Test Runner

- Runner: `pytest`
- Config: `/Users/nirtzur/Documents/projects/GISArchAgent/pytest.ini`

## Marker Taxonomy

Pyramid level:
- `unit`: pure logic only (no real DB/network/Selenium).
- `integration`: real boundary contracts (Chroma persistence, repository wiring).
- `e2e`: critical flow smoke checks (Streamlit scripts + end-to-end output sanity).

Cross-cutting:
- `data_contracts`: range + completeness checks (required fields, missingness, ranges, allowed categories, uniqueness).

Boundaries:
- `db`: touches real persistence boundary.
- `ui`: executes Streamlit scripts.
- `network`: requires real network access (should be rare; prefer skipping in CI).
- `slow`: explicitly slow tests.

## Test Command Map

Preferred (works in this repo’s current local setup):

- All: `./venv/bin/python -m pytest`
- Unit: `./venv/bin/python -m pytest -m unit`
- Integration: `./venv/bin/python -m pytest -m integration`
- E2E: `./venv/bin/python -m pytest -m e2e`
- Data contracts: `./venv/bin/python -m pytest -m data_contracts`

Generic (if your environment has `python` on PATH and deps installed):

- All: `python -m pytest`
- Unit: `python -m pytest -m unit`
- Integration: `python -m pytest -m integration`
- E2E: `python -m pytest -m e2e`
- Data contracts: `python -m pytest -m data_contracts`

## Environment Requirements

Unit tests:
- No external services.
- Deterministic by design (no sleeps, no real network).

Integration tests:
- Requires local filesystem for Chroma persistence.
- No real network.

E2E tests:
- Uses Streamlit’s `AppTest` to execute scripts in-process.
- Requires Streamlit + UI dependencies importable (folium/pyproj/pandas/etc).

