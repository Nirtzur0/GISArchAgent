# Test Stabilization Status

Date: 2026-02-06

## Done

- Refactored tests into pyramid structure (`unit`/`integration`/`e2e`) and added `data_contracts` suites.
- Full suite passes locally.
- Flake proof:
  - Unit suite passed 3x (`./venv/bin/python -m pytest -m unit`)
  - Data contract suite passed 3x (`./venv/bin/python -m pytest -m data_contracts`)

## In Progress

- Documented stabilization workflow and auditing artifacts (checklist/worklog/final report).
- (none)

## Next

- Optional: add CI workflow (see `/Users/nirtzur/Documents/projects/GISArchAgent/docs/manifest/11_ci.md`).

## Commands

- All: `./venv/bin/python -m pytest`
- Unit: `./venv/bin/python -m pytest -m unit`
- Integration: `./venv/bin/python -m pytest -m integration`
- E2E: `./venv/bin/python -m pytest -m e2e`
- Data contracts: `./venv/bin/python -m pytest -m data_contracts`
