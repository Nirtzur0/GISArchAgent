# Test Stabilization Final Report

Date: 2026-02-06

## What Was Failing

1. `tests/integration/data_contracts/test_boundary_payload_contracts.py::test_chroma_metadata__required_keys_present__no_null_values`
   - Failure: `chromadb.errors.NotFoundError: Collection [regulations] does not exist`
   - Why: the test created a fresh `PersistentClient` but did not ensure the repository (which creates the `regulations` collection) had been instantiated in that temp persistence directory.

2. `tests/unit/domain/test_building_rights_calculator.py::test_calculate_from_zone__tama35__more_intense_than_r2`
   - Failure: TAMA35 returned a lower FAR than R2.
   - Why: `BuildingRightsCalculator.calculate_from_zone()` used overly-broad substring checks (`'A' in zone_upper`, `'C' in zone_upper`) which misclassified zone codes like `TAMA35` and `C1`.

## Root Causes

- Bucket A (test infra): integration boundary contract test assumed Chroma collection existed before initialization.
- Bucket C (production bug): zone-type parsing in `BuildingRightsCalculator` was incorrect for common zone codes.
- Bucket C (latent production bug found during refactor): `VectorDBLoader._parse_regulation_type()` referenced enum members that do not exist in `src.domain.entities.regulation.RegulationType` (would raise if exercised).

## Fixes Applied

- Fix (test): ensure Chroma collection exists by forcing repo initialization before direct Chroma inspection.
  - File: `/Users/nirtzur/Documents/projects/GISArchAgent/tests/integration/data_contracts/test_boundary_payload_contracts.py`

- Fix (prod): normalize zone code parsing and prefer explicit prefixes (`TAMA35`, `R1/R2/R3`, `C1`) over broad substring matching.
  - File: `/Users/nirtzur/Documents/projects/GISArchAgent/src/domain/value_objects/building_rights.py`

- Fix (prod): map iPlan `entity_subtype` metadata to existing coarse `RegulationType` enum values (no invented enum members).
  - File: `/Users/nirtzur/Documents/projects/GISArchAgent/src/data_pipeline/core/loader.py`

## Contract Changes (Thresholds/Fields/Ranges)

- No threshold loosening was required.
- Added explicit data contract suites with standardized, debug-first failure messages:
  - Helpers: `/Users/nirtzur/Documents/projects/GISArchAgent/tests/helpers/assertions.py`
  - Unit contracts: `/Users/nirtzur/Documents/projects/GISArchAgent/tests/unit/data_contracts/`
  - Integration contracts: `/Users/nirtzur/Documents/projects/GISArchAgent/tests/integration/data_contracts/`
  - E2E sanity contract: `/Users/nirtzur/Documents/projects/GISArchAgent/tests/e2e/data_contracts/`

## What’s Still Gated/Optional

- Nothing is skipped by default in the current local setup.
- E2E tests are marked `e2e` and can be excluded in constrained environments via `-m \"not e2e\"` (requires Streamlit + UI imports if run).

## How To Run

Preferred (repo local setup):

- All: `./venv/bin/python -m pytest`
- Unit: `./venv/bin/python -m pytest -m unit`
- Integration: `./venv/bin/python -m pytest -m integration`
- E2E: `./venv/bin/python -m pytest -m e2e`
- Data contracts: `./venv/bin/python -m pytest -m data_contracts`

## Verification Evidence (Flake Proof)

- Unit suite: passed 3x.
- Data contracts: passed 3x.
- Previously failing tests: each rerun 5x without failure.
- Integration suite: passed 3x.
- E2E suite: passed 1x.
- Full suite: `53 passed`.

