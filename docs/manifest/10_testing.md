# Testing Strategy

## Test Pyramid
- Unit tests: pure logic and deterministic behavior.
- Integration tests: boundary contracts (repository wiring, persistence behavior).
- E2E tests: canonical FastAPI smoke and end-to-end sanity.
- Data contract tests: required fields, range/completeness/shape checks.

## Marker Taxonomy
Canonical marker declarations live in `pytest.ini`.
Primary markers used for execution:
- `unit`
- `integration`
- `e2e`
- `data_contracts`

Boundary markers include `db`, `ui`, `network`, and `slow`.

## Command Mapping
Canonical command IDs are defined in `docs/manifest/09_runbook.md`:
- full suite: `CMD-003`
- unit: `CMD-004`
- integration: `CMD-005`
- e2e: `CMD-006`
- contracts: `CMD-007`
- deterministic external dependency rehearsal bundle: `CMD-035`
- optional live-network rehearsal (bounded manual drill): `CMD-037`

## Critical Flow Coverage Expectations
- Canonical runtime smoke:
  - FastAPI health, workspace, operations, regulation-query, and building-rights flows.
  - Browser-level maintained-UI coverage lives in `frontend/tests/app.spec.ts` and runs via `CMD-042`.
- Regulation query path:
  - happy path and no-LLM fallback path.
- Plan search path:
  - repository boundary behavior and error containment.
  - deterministic non-network drill coverage for iPlan boundary failures (`tests/integration/iplan/test_external_dependency_drills.py`).
- Vector DB/data boundaries:
  - persistence/contract checks and integrity invariants.

## Current Gaps
- CI quality gates now include repo-wide parse/syntax lint checks; formatting enforcement is still phased (changed-file + maintained-surface guard, not full-repo yet).
- Performance/load checks are not yet formalized.
- Golden-file strategy for output interpretation is limited.

## Optional Live-Network Rehearsal Policy
- Objective: keep a real-provider smoke path available without coupling merge/release reliability to network volatility.
- Default lane (CI + routine local): run deterministic rehearsal path (`CMD-035`) and keep live-network test skipped.
- Passive API/UI status checks must stay cheap:
  - `/api/health`, `/api/system/status`, `/api/workspace/overview`, and `/api/operations/overview` should not trigger the live scraper probe.
  - Validate probe-driven scraper status through `/api/data/fetcher-health` and API integration coverage rather than by loading the workspace shell.
- Live lane (manual only): run `CMD-037` on bounded cadence:
  - at most once per calendar week during normal operation,
  - additionally after dependency/runtime changes affecting pydoll/browser automation,
  - additionally after incidents where deterministic drills are green but provider regressions are still suspected.
- Guardrails:
  - `RUN_NETWORK_TESTS=1` is required to opt in.
  - CI execution is blocked unless `RUN_NETWORK_ALLOW_CI=1` is explicitly set for a dedicated rehearsal workflow.
  - rehearsal runtime is bounded by `RUN_NETWORK_REHEARSAL_MAX_ATTEMPTS` and `RUN_NETWORK_REHEARSAL_TIMEOUT_SECONDS` (defaults: 2 attempts, 45s timeout).
- Expected outcomes:
  - pass if artifacts are returned and validated,
  - skip when provider is throttled/unavailable, optional dependency is missing, or bounded timeout is exceeded.
  - when skipped after a bounded run, include the classified scraper status and latest recorded detail/timestamp in the skip reason when available.

## Policy
- Any code change affecting runtime behavior should update relevant tests or explicitly justify why no test change is needed.
- For boundary-heavy changes, prioritize contract/integration tests over only unit changes.
