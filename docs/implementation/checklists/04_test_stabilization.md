# Checklist: Test Stabilization

Each checked item implies the `Verify:` command(s) were run and notes were captured in the worklog.

## Phase 0: Test Interface

- [x] Identify test runner, markers, and environment requirements
  - AC: command map exists (unit/integration/e2e/all) and env needs are documented
  - Verify: (doc-only)
  - Files: (docs only)
  - Docs: `/Users/nirtzur/Documents/projects/GISArchAgent/docs/manifest/10_testing.md`

## Phase 1: Baseline Signal

- [x] Run unit tests (fast feedback)
  - AC: unit suite passes locally
  - Verify: `./venv/bin/python -m pytest -m unit` (3 runs total)
  - Files: (none)
  - Docs: `/Users/nirtzur/Documents/projects/GISArchAgent/docs/implementation/03_worklog.md`

- [x] Run unit data contract tests early
  - AC: `data_contracts` unit tests pass
  - Verify: `./venv/bin/python -m pytest -m \"unit and data_contracts\"`
  - Files: (none)
  - Docs: `/Users/nirtzur/Documents/projects/GISArchAgent/docs/implementation/03_worklog.md`

- [x] Run integration tests
  - AC: integration suite passes or explicit skips are documented and justified
  - Verify: `./venv/bin/python -m pytest -m integration` (3 runs total)
  - Files: (none)
  - Docs: `/Users/nirtzur/Documents/projects/GISArchAgent/docs/implementation/03_worklog.md`

- [x] Run e2e tests last
  - AC: e2e suite passes or explicit gating is documented
  - Verify: `./venv/bin/python -m pytest -m e2e`
  - Files: (none)
  - Docs: `/Users/nirtzur/Documents/projects/GISArchAgent/docs/implementation/03_worklog.md`

## Phase 2-4: Debug Loop + Contracts

- [x] Triage failures into buckets and fix root causes
  - AC: failures are eliminated without weakening contracts unnecessarily
  - Verify: failing tests rerun `5x`, impacted suites rerun
  - Files: varies
  - Docs: `/Users/nirtzur/Documents/projects/GISArchAgent/docs/implementation/03_worklog.md`, `/Users/nirtzur/Documents/projects/GISArchAgent/docs/manifest/03_decisions.md` (if needed)

- [x] Prove non-flakiness
  - AC: unit suite passes `3x` and `data_contracts` passes `3x`
  - Verify:
    - `./venv/bin/python -m pytest -m unit` (3 runs)
    - `./venv/bin/python -m pytest -m data_contracts` (3 runs)
  - Files: (none)
  - Docs: `/Users/nirtzur/Documents/projects/GISArchAgent/docs/implementation/03_worklog.md`

## Phase 5: Final Verification + Report

- [x] Run full suite and produce final report
  - AC: `./venv/bin/python -m pytest` passes; final report written
  - Verify: `./venv/bin/python -m pytest`
  - Files: `/Users/nirtzur/Documents/projects/GISArchAgent/docs/implementation/reports/test_stabilization_final_report.md`
  - Docs: `/Users/nirtzur/Documents/projects/GISArchAgent/docs/implementation/reports/test_stabilization_final_report.md`
