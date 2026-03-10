# Checklist: Test Stabilization (Prompt-10)

Date: 2026-02-09
Prompt: `prompt-10-tests-stabilization-loop`
Appetite: medium
Scope state: downhill

## Command Sources
- `.github/workflows/ci.yml` (`python -m pytest -m unit|integration|e2e|data_contracts`)
- `pytest.ini` (marker taxonomy and strict marker policy)
- `docs/manifest/09_runbook.md` (`CMD-003`..`CMD-007`)

## Bet Tracking
### Now (active cluster)
- [x] TS-01: `COR-02` prep stability for endpoint-family contract mapping
  - State: downhill
  - Decision: required suites are stable and flake-free in local supported env before entering `prompt-02` implementation for `COR-02`.
  - Evidence: unit x3 + data-contract x3 are green; integration is green with one explicit optional network skip.

### Not now
- [x] TS-02: investigate aggregate full-suite hang in mixed-order execution.
  - Deferred reason: `prompt-10` DoD is satisfied by required suite reruns and historical non-flake checks.
  - Evidence: `./venv/bin/python -m pytest -q` entered a long sleep/no-progress state and was terminated; module-level required suites remained green.
- [x] TS-03: extend degraded-mode assertions + richer triage instrumentation in service workflows.
  - Completed via `prompt-02-app-development-playbook` follow-up for IMP-09:
    - `tests/integration/iplan/test_external_dependency_drills.py`
    - `docs/manifest/09_runbook.md` (`CMD-034`, `CMD-035`)

## Phase 0 — Test Interface
- [x] Test command map validated from CI + runbook.
  - Unit: `./venv/bin/python -m pytest -m unit`
  - Integration: `./venv/bin/python -m pytest -m integration`
  - E2E: `./venv/bin/python -m pytest -m e2e`
  - Contracts: `./venv/bin/python -m pytest -m data_contracts`
  - All: `./venv/bin/python -m pytest`

## Phase 1 — Baseline Signal
- [x] Unit baseline run completed (`50 passed, 28 deselected`).
- [x] Contract baseline run completed (`17 passed, 61 deselected`).
- [x] Integration baseline run completed (`21 passed, 1 skipped, 56 deselected`).
- [x] E2E baseline run completed (`5 passed, 73 deselected`).

## Phase 2-4 — Debug Loop + Flake Proof
- [x] No active failing cluster required root-cause code changes in this packet.
- [x] Unit suite rerun to 3 total green passes.
- [x] Data-contract suite rerun to 3 total green passes.
- [x] Historical failing tests rerun 5x each:
  - `tests/integration/data_contracts/test_boundary_payload_contracts.py::test_chroma_metadata__required_keys_present__no_null_values`
  - `tests/unit/domain/test_building_rights_calculator.py::test_calculate_from_zone__tama35__more_intense_than_r2`

## Phase 5 — Final Verification
- [x] Integration suite rerun once (supported env) with explicit optional network skip.
- [x] E2E suite rerun once for critical smoke flows.
- [x] Full suite aggregate run attempted; non-progress hang observed and terminated (`./venv/bin/python -m pytest -q`), tracked as non-blocking for this packet.
- [x] Final report refreshed at `docs/implementation/reports/test_stabilization_final_report.md`.
