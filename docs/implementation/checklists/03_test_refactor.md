# Checklist: Test Refactor Suite

- Appetite: small
- State: downhill

## Now
- [x] Deliverable 1 completed (`test_landscape.md`).
  - AC: landscape includes framework/convention inventory, runtime baselines, core flows, risk/gap analysis.
  - Verify: `test -f docs/implementation/reports/test_landscape.md`
  - Files: `docs/implementation/reports/test_landscape.md`
  - Docs: `docs/implementation/00_status.md`, `docs/implementation/03_worklog.md`

- [x] Deliverable 2 completed (`test_architecture_plan.md`).
  - AC: target architecture and mapping strategy documented with runnable marker policy.
  - Verify: `test -f docs/implementation/reports/test_architecture_plan.md`
  - Files: `docs/implementation/reports/test_architecture_plan.md`
  - Docs: `docs/manifest/10_testing.md`

- [x] Suite verification completed on current architecture.
  - AC: unit and full suites pass in current environment.
  - Verify:
    - `/usr/bin/time -lp ./venv/bin/python -m pytest -m unit -q`
    - `/usr/bin/time -lp ./venv/bin/python -m pytest -q`
  - Files: `tests/*`
  - Docs: `docs/implementation/reports/test_landscape.md`

## Not now
- [ ] Large-scale test move/rename operations across all categories.
  - Reason: current structure is already aligned; prioritize CI and release workflow gaps first.
- [ ] Coverage-threshold enforcement.
  - Reason: should be introduced with CI baseline to avoid local-only policy drift.

## Follow-up links
- Milestone linkage: `docs/implementation/checklists/02_milestones.md`
- Architecture linkage: `docs/manifest/01_architecture.md`
