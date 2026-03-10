# Feature Audit and Replatform Parity Map

## Summary

This audit maps the legacy Streamlit feature surface to the new React + FastAPI application. It is the source of truth for migration scope, parity tracking, and stale-path cleanup.

## Feature Inventory

| Capability | Legacy entrypoint | Backend owner | Target route | Target API | Parity status |
|---|---|---|---|---|---|
| Regulation Q&A | `app.py` query assistant | `RegulationQueryService` | `/` | `POST /api/regulations/query` | Implemented |
| System stats | `app.py` stats view | `ApplicationFactory`, `DataStore`, cache service | `/` | `GET /api/system/status` | Implemented |
| Query history | `app.py` session state | UI-only state | `/` | n/a | Implemented in browser storage |
| Live plan search | main app / plan services | `PlanSearchService`, `IPlanGISRepository` | future dashboard extension | `GET /api/plans/search` | API implemented, UI not surfaced yet |
| Map browsing of local plans | `pages/1_📍_Map_Viewer.py` | `DataStore` | `/map` | `GET /api/data/search` | Implemented |
| Building-rights calculation | `pages/2_📐_Plan_Analyzer.py` | `BuildingRightsService` | `/analyzer` | `POST /api/building-rights/calculate` | Implemented |
| Applicable regulations for scenario | `pages/2_📐_Plan_Analyzer.py` | `BuildingRightsService` | `/analyzer` | `POST /api/building-rights/calculate` | Implemented |
| Upload + analyze | `pages/2_📐_Plan_Analyzer.py` | `PlanUploadService` | `/analyzer` | `POST /api/uploads/analyze` | Implemented |
| DataStore stats | `pages/3_💾_Data_Management.py` | `DataStore` | `/data` | `GET /api/data/status` | Implemented |
| DataStore search | `pages/3_💾_Data_Management.py` | `DataStore` | `/data` and `/map` | `GET /api/data/search` | Implemented |
| Data import | `pages/3_💾_Data_Management.py` | `DataStore` | `/data` | `POST /api/data/import` | Implemented |
| Live data fetch | `pages/3_💾_Data_Management.py` | `DataFetcherFactory`, `IPlanPydollFetcher` | `/data` | `POST /api/data/fetch` | Implemented |
| Vector DB status | `pages/3_💾_Data_Management.py` | `VectorDBManagementService` | `/data` | `GET /api/vectordb/status` | Implemented |
| Vector DB init | `pages/3_💾_Data_Management.py` | `VectorDBManagementService` | `/data` | `POST /api/vectordb/initialize` | Implemented |
| Vector DB rebuild | `pages/3_💾_Data_Management.py` | `VectorDBManagementService` | `/data` | `POST /api/vectordb/rebuild` | Implemented |
| Vector DB semantic search | `pages/3_💾_Data_Management.py` | `VectorDBManagementService` | `/data` | `POST /api/vectordb/search` | Implemented |
| Add regulation | `pages/3_💾_Data_Management.py` | `VectorDBManagementService` | `/data` | `POST /api/vectordb/regulations` | Implemented |
| Vector DB import/export | `pages/3_💾_Data_Management.py` | `VectorDBManagementService` | future `/data` controls expansion | `POST /api/vectordb/import`, `GET /api/vectordb/export` | API implemented, export/import UI partial |

## Mismatches Reconciled

- `docs/QUICK_START.md` still references `.env.example` and `scripts/populate_regulations.py`, neither of which exists. The new stack should rely on explicit FastAPI/React run instructions instead.
- The old naming in `src/infrastructure/services/llm_service.py` and `src/infrastructure/services/vision_service.py` was Gemini-specific, but the runtime path is now OpenAI-compatible and provider-neutral.
- `DataFetcherFactory` uses `iplan` as a Pydoll-backed fetcher even though older docs still describe direct iPlan fetch as the primary path.
- Existing UI tests cover only Streamlit smoke execution. The new app needs browser-level route coverage and API contract coverage.

## Dead or Deferred Paths

- `app.py` and `pages/*` are now legacy UI entrypoints and should be removed once the React app is the only supported interface.
- Legacy Gemini terminology in docs should be removed or updated to OpenAI-compatible ChatMock terminology.
- `GET /api/plans/search` exists for parity with the old live-search service, but the first React pass does not expose a dedicated live-search workflow yet.
- Vector DB export/import has API parity, but the React data-ops screen currently prioritizes search/add/init/rebuild and local data import.

## Removal Target

After the new frontend and Playwright coverage are stable:

1. Remove Streamlit-only presentation code from `app.py` and `pages/`.
2. Remove stale Gemini-specific docs and setup instructions.
3. Collapse runtime docs around one primary stack: FastAPI backend + React frontend + OpenAI-compatible provider configuration.
