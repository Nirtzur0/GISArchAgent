# How the System Works

This file summarizes the current operational flow at a practical level.
For canonical architecture decisions and boundary definitions, see:
- `docs/manifest/01_architecture.md`
- `docs/manifest/04_api_contracts.md`
- `docs/manifest/05_data_model.md`

## 1) Startup and Wiring
1. `app.py` initializes the Streamlit app.
2. `src/infrastructure/factory.py` lazily creates and caches service/repository singletons.
3. Regulation repository initialization includes vector DB health checks and bootstrap behavior.

## 2) Regulation Query Flow
1. UI builds `RegulationQuery` DTO.
2. `RegulationQueryService.query()` calls `IRegulationRepository.search()`.
3. Results are returned with optional LLM synthesis, or deterministic fallback if LLM is unavailable.
4. Failures are logged and returned as structured empty/degraded responses.

## 3) Plan Search Flow
1. UI builds `PlanSearchQuery` DTO.
2. `PlanSearchService.search_plans()` resolves search precedence (`plan_id` > `location` > `keyword`).
3. iPlan repository access fetches plans and optional plan image data.
4. Optional vision analysis runs with cache support.
5. Response is returned as `PlanSearchResult`.

## 4) Vector Build and Data Maintenance
- `scripts/build_vectordb_cli.py build` runs unified pipeline ingestion/indexing.
- `scripts/build_vectordb_cli.py status` and `scripts/quick_status.py` report vector DB health.
- `scripts/data_cli.py` handles local data-store inspection/search/export tasks.

## 5) Verification and CI
- Local marker suites:
  - `./venv/bin/python -m pytest -m unit`
  - `./venv/bin/python -m pytest -m integration`
  - `./venv/bin/python -m pytest -m e2e`
  - `./venv/bin/python -m pytest -m data_contracts`
- CI baseline:
  - `.github/workflows/ci.yml` runs marker suites and prompt-pack integrity checks.

## 6) Known Gaps
- Observability instrumentation remains partial (metrics/tracing dashboards not fully implemented).
- Release workflow exists (`.github/workflows/release.yml`), but release-readiness checklist execution remains a manual discipline per tag cycle (`docs/implementation/checklists/06_release_readiness.md`).
