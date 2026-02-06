# Worklog: Test Stabilization

## 2026-02-06

- Baseline: `./venv/bin/python -m pytest -q` was green after refactor (53 tests).
  - Next: add required documentation system + flake-proof reruns.

- Bug fix (pipeline): `VectorDBLoader._parse_regulation_type()` referenced non-existent `RegulationType.*` members.
  - Change: map iPlan subtype metadata to existing coarse `RegulationType` enum values.
  - Files: `/Users/nirtzur/Documents/projects/GISArchAgent/src/data_pipeline/core/loader.py`
  - Next: validate with unit mapping tests + full suite.

- Bug fix (domain): `BuildingRightsCalculator.calculate_from_zone()` used substring checks (`'A' in zone_upper`) that misclassified `TAMA35` and `C1`.
  - Change: normalize zone code and prefer explicit prefixes (`R1/R2/R3/C1/TAMA35`).
  - Files: `/Users/nirtzur/Documents/projects/GISArchAgent/src/domain/value_objects/building_rights.py`
  - Next: run targeted unit tests 5x + unit suite.

- Verification (non-flake proof):
  - Unit suite `3x`: `./venv/bin/python -m pytest -m unit`
  - Unit contracts: `./venv/bin/python -m pytest -m \"unit and data_contracts\"`
  - Data contracts `3x`: `./venv/bin/python -m pytest -m data_contracts`
  - Integration suite `3x`: `./venv/bin/python -m pytest -m integration`
  - E2E suite: `./venv/bin/python -m pytest -m e2e`
  - Previously failing tests rerun `5x` each:
    - `tests/integration/data_contracts/test_boundary_payload_contracts.py::test_chroma_metadata__required_keys_present__no_null_values`
    - `tests/unit/domain/test_building_rights_calculator.py::test_calculate_from_zone__tama35__more_intense_than_r2`
  - Full suite: `./venv/bin/python -m pytest`
  - Next: none (optional CI follow-up).
