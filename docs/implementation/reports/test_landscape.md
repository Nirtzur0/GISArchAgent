# Test Landscape Report

## Test frameworks and conventions
- Runner: `pytest` (`pytest.ini`).
- Plugins detected during runs: `anyio`, `langsmith`, `asyncio`.
- Marker conventions in use: `unit`, `integration`, `e2e`, `data_contracts`, plus boundary markers (`db`, `ui`, `network`, `slow`).
- CI execution: no committed workflow under `.github/workflows/`; tests are currently run locally.

## Baseline measurements
- Unit marker suite:
  - Command: `/usr/bin/time -lp ./venv/bin/python -m pytest -m unit -q`
  - Result: `37 passed, 23 deselected`
  - Runtime: `real 2.38s`
- Full suite:
  - Command: `/usr/bin/time -lp ./venv/bin/python -m pytest -q`
  - Result: `59 passed, 1 skipped`
  - Runtime: `real 13.37s`
- Coverage tooling:
  - No repository-native coverage command currently mapped in runbook/CI.

## Current test categories
- Unit tests: `tests/unit/*`
- Integration tests: `tests/integration/*`
- End-to-end tests: `tests/e2e/*`
- Contract tests: `tests/*/data_contracts/*`
- Slow/network tests: tagged via markers; one optional live pydoll integration test is currently skipped in full runs.

## Inventory of test files
### Application and domain behavior
- Paths: `tests/unit/application/*`, `tests/unit/domain/*`
- Touches: `src/application/services/*`, `src/domain/*`
- Type: unit
- Health: ✅ good

### Data pipeline and data management
- Paths: `tests/unit/data_pipeline/*`, `tests/unit/data_management/*`, `tests/integration/iplan/*`
- Touches: `src/data_pipeline/*`, `src/data_management/*`
- Type: mixed unit/integration
- Health: ⚠️ mostly good; optional live dependency path requires explicit environment assumptions.

### Vector DB and repository boundaries
- Paths: `tests/integration/vectordb/*`, `tests/unit/vectorstore/*`, `tests/unit/infrastructure/*`
- Touches: `src/vectorstore/*`, `src/infrastructure/repositories/*`
- Type: unit/integration/contract
- Health: ✅ good

### UI smoke and E2E sanity
- Paths: `tests/e2e/webui/*`, `tests/e2e/data_contracts/*`
- Touches: `app.py`, Streamlit pages, output contracts
- Type: e2e + contract
- Health: ✅ good

## Core flows
### Flow A: Regulation retrieval
- Entry points: `RegulationQueryService.query()`, UI query flow in `app.py`.
- Invariants: fallback response when LLM unavailable; deterministic result shape.
- Failure modes: vector store not initialized, external LLM errors.
- Dependencies: Chroma persistence, optional Gemini service.

### Flow B: Plan search and optional vision
- Entry points: `PlanSearchService.search_plans()`, plan analyzer page.
- Invariants: query precedence (plan_id > location > keyword), safe empty results on boundary failure.
- Failure modes: iPlan request failure, missing image, vision errors.
- Dependencies: iPlan ArcGIS, optional Gemini Vision.

### Flow C: Data/vector maintenance
- Entry points: `scripts/data_cli.py`, `scripts/build_vectordb_cli.py`, `scripts/quick_status.py`.
- Invariants: local persistence paths and non-crashing status output.
- Failure modes: missing dependencies, external fetch failure, persistence issues.
- Dependencies: local FS, Chroma, optional browser automation.

## Current test suite issues
- No CI pipeline currently enforces marker suites.
- Coverage is not tracked as a first-class metric yet.
- Optional dependency imports can block local verification if environment setup is incomplete.

## Risk areas / missing coverage
- Release workflow and CI checks are documentation-level but not automation-enforced.
- Observability behavior (logs/metrics expectations) lacks dedicated automated assertions.
- External-boundary failure simulation coverage can be expanded for iPlan/Gemini paths.

## Refactor opportunities
- Add explicit coverage command and threshold policy in CI.
- Add focused tests around dependency-optional startup paths.
- Keep current folder architecture; it already maps well to feature/boundary flows.
