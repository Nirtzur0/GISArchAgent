# Project Overview

## Core Objective

### Objective
We are building GISArchAgent for planning and architecture practitioners so they can search Israeli planning data and regulations, inspect planning context, and make evidence-backed decisions with reproducible local workflows.

### Non-goals
- Replace legal or statutory review by licensed experts.
- Operate as a multi-tenant hosted SaaS product.
- Mirror all iPlan datasets/documents at full historical depth.
- Guarantee uptime/performance of external providers (iPlan ArcGIS, OpenAI-compatible APIs).

### Success Metrics
- A clean clone can reach a running UI via repo-native commands (`./setup.sh`, `./run_webapp.sh`).
- Core verification commands pass locally (`./venv/bin/python -m pytest` and marker subsets from `pytest.ini`).
- Three primary workflows are usable end-to-end:
  - plan search and dossier selection in the React workspace,
  - regulation query against the selected plan context in the React workspace,
  - vector DB maintenance through CLI scripts.
- Engineering docs remain coherent with repo entrypoints and boundaries (status/checklists/manifest docs kept in sync).

### Constraints
- Python runtime baseline: `>=3.10` (`pytest.ini`).
- Node.js runtime baseline: `>=20` for the React/Vite frontend.
- Local-first persistence under `data/` (gitignored except `.gitkeep`).
- Optional external integrations: OpenAI-compatible provider APIs and iPlan ArcGIS endpoints.
- Secrets must stay outside git (`.env` ignored by `.gitignore`).

### Do Not Break Invariants
- App must still return useful regulation answers without configured LLM keys (deterministic fallback path in `src/application/services/regulation_query_service.py`).
- Core CLI entrypoints remain stable (`scripts/data_cli.py`, `scripts/build_vectordb_cli.py`, `scripts/quick_status.py`).
- Test marker taxonomy remains strict and actionable (`pytest.ini`).
- Data directories remain local and gitignored (`.gitignore`).

### Primary User Journeys
1. New user setup and first query:
   - run `./setup.sh`, then `./run_webapp.sh`, then select a plan and ask a regulation question in the React workspace.
2. Planner performs plan search:
   - use the React workspace backed by local data search and optional live iPlan lookup.
3. Data operator maintains local data store:
   - run `python3 scripts/data_cli.py status/search/export`.
4. Data operator refreshes vector DB:
   - run `python3 scripts/build_vectordb_cli.py build ...` and `python3 scripts/quick_status.py`.
5. Contributor validates a change:
   - run pytest marker suites and inspect docs/checklists before review.

## Target Users
- Architecture and urban-planning practitioners needing quick access to planning rules.
- Data operators who maintain local planning datasets and vector indexes.
- Contributors extending the data pipeline, UI flows, and integration boundaries.

## Key Workflows
- Regulation retrieval and answer synthesis: React UI -> FastAPI -> `RegulationQueryService` -> `IRegulationRepository` (Chroma) -> optional OpenAI-compatible LLM.
- Plan search and optional vision analysis: React UI -> FastAPI -> `PlanSearchService` -> `IPlanRepository` (iPlan ArcGIS) -> optional OpenAI-compatible vision + cache.
- Data ingestion/build flow: CLI -> unified pipeline (`src/vectorstore/unified_pipeline.py`) -> persisted vector DB.
- Testing and change validation: `pytest` marker suites + docs status/checklist updates.
