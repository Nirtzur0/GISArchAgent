# Architecture

## Scope, Constraints, and Quality Scenarios

### Scope
GISArchAgent is a local-first planning intelligence system for Israeli planning workflows. It combines:
- Streamlit UI flows,
- application/domain services,
- repository adapters for external and local data,
- CLI-driven data and vector-index maintenance.

### Constraints
- Python runtime and dependency set are defined in `requirements.txt` and `requirements-dev.txt`.
- Local persistence is under `data/` (gitignored runtime artifacts).
- External boundaries are optional but load-bearing when enabled (`iPlan` APIs, Gemini APIs).
- CI baseline is GitHub Actions (`.github/workflows/ci.yml`) with marker and prompt-pack integrity gates.

### Quality Scenarios
1. Query resilience without LLM keys:
   - Given no Gemini key,
   - when a regulation query is executed,
   - then deterministic fallback output is returned (no hard crash).
2. Reproducible verification:
   - Given a clean local setup,
   - when marker suites are run,
   - then unit/integration/e2e/data_contract suites complete with stable taxonomy.
3. Boundary-failure containment:
   - Given iPlan or Gemini failures,
   - when search/build flows execute,
   - then failures are logged and returned as degraded results rather than uncaught exceptions.
4. Architecture/doc coherence:
   - Given implementation or boundary changes,
   - when a packet closes,
   - then manifest + implementation checklists/worklog are updated in the same packet.

## C4-1 System Context

```mermaid
flowchart LR
  User[Planner / Architect / Contributor]
  UI[Streamlit UI\napp.py + pages/*]
  CLI[CLI scripts\nscripts/*.py]
  Core[Application + Domain\nsrc/application + src/domain]
  Infra[Infrastructure adapters\nsrc/infrastructure/*]
  IPlan[iPlan ArcGIS API]
  Gemini[Gemini APIs (optional)]
  Chroma[(ChromaDB\ndata/vectorstore)]
  Local[(Local files\ndata/raw + data/cache)]

  User --> UI
  User --> CLI
  UI --> Core
  CLI --> Core
  Core --> Infra
  Infra --> IPlan
  Infra --> Gemini
  Infra --> Chroma
  Infra --> Local
```

## C4-2 Containers

| Container | Responsibility | Evidence |
| --- | --- | --- |
| Streamlit UI | User query/search/data-management workflows. | `app.py`, `pages/*` |
| Application services | Use-case orchestration (`query`, `search_plans`, rights, upload). | `src/application/services/*` |
| Domain model/contracts | Core entities, value objects, repository interfaces. | `src/domain/*` |
| Infrastructure adapters | iPlan + Chroma repositories, cache, LLM/vision services, factory wiring. | `src/infrastructure/*` |
| Data/vector pipeline | Data discovery/fetch/indexing and vector DB build orchestration. | `src/data_pipeline/*`, `src/vectorstore/*`, `scripts/build_vectordb_cli.py` |
| CI and docs governance | PR/push marker gates + prompt-pack integrity checks. | `.github/workflows/ci.yml` |

## C4-3 Components (High-risk areas)

### A) Regulation query path
- `RegulationQueryService` -> `IRegulationRepository` -> `ChromaRegulationRepository`.
- Optional `GeminiLLMService` synthesis with deterministic fallback when unavailable.
- Primary risk: retrieval quality drift and stale index content.

### B) Plan search path
- `PlanSearchService` -> `IPlanRepository` (`IPlanGISRepository`) -> optional vision analysis + cache.
- Primary risk: external API instability and optional AI dependency failures.

### C) Vector DB build path
- CLI (`scripts/build_vectordb_cli.py`) -> `UnifiedDataPipeline` -> Chroma persistence.
- Primary risk: browser-automation prerequisites and long-running build reliability.

## Runtime Scenarios

### Scenario 1: Regulation query (happy path)
1. User submits query in Streamlit.
2. UI builds `RegulationQuery` DTO.
3. `RegulationQueryService.query()` calls repository search.
4. Service returns LLM synthesis if configured, otherwise deterministic fallback.
5. UI renders answer and top matched regulations.

### Scenario 2: Plan search with optional vision
1. User submits plan search inputs.
2. `PlanSearchService.search_plans()` queries iPlan repository.
3. Service fetches plan image and optional vision analysis (cached when available).
4. Result DTO is returned and rendered.

### Scenario 3: Failure path (boundary degradation)
1. External boundary call fails (iPlan/Gemini).
2. Repository/service logs error and returns degraded/empty structured result.
3. UI continues to render with failure context and no hard crash.

### Scenario 4: CI verification path
1. Push or PR triggers `.github/workflows/ci.yml`.
2. Marker suites (`unit`, `integration`, `e2e`, `data_contracts`) run.
3. Prompt-pack integrity checks validate manifests/system coherence.
4. Changes are gated on pass/fail status.

## Deployment and Trust Boundaries

### Runtime shape
- Primary runtime: local Python process for Streamlit app.
- Operational runtime: local CLI processes for data/vector maintenance.
- Persistence: local filesystem (`data/`).

### Trust boundaries
- Boundary A: local app <-> iPlan API over HTTPS.
- Boundary B: local app <-> optional Gemini APIs.
- Boundary C: local app <-> local persisted data and caches.
- Boundary D: GitHub-hosted CI runners <-> repository (read/execute checks).

## Cross-Cutting Concepts
- Configuration: `src/config.py` + `pydantic-settings`.
- Dependency wiring: singleton `ApplicationFactory` in `src/infrastructure/factory.py`.
- Logging: Python `logging` across services/repositories/scripts.
- Testing: pytest marker taxonomy (`unit`, `integration`, `e2e`, `data_contracts`) in `pytest.ini`.
- Reliability: fallback behavior in service boundaries and defensive exception handling.
- Docs governance: packet status + checklist + worklog updates in `docs/implementation/*`.

## Risks and Technical Debt
- Observability instrumentation is still partial (metrics/tracing/dashboarding remain planned work).
- Dedicated tag/release CI workflow is not yet implemented.
- Legacy deep-dive docs (`docs/ARCHITECTURE.md`, `docs/HOW_IT_WORKS.md`) require periodic sync with manifest updates.
- External provider variability (iPlan/Gemini) can degrade non-core flows.
