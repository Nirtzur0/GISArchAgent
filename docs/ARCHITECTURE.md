# Architecture (Legacy Deep-Dive Entry)

This page is kept as a legacy deep-dive entrypoint for contributors who previously used
`docs/ARCHITECTURE.md` directly.

Canonical architecture source of truth is:
- `docs/manifest/01_architecture.md`

## Current Runtime Topology
- UI: Streamlit app and pages (`app.py`, `pages/*`)
- Application services: query/search/upload/rights (`src/application/services/*`)
- Domain contracts and entities (`src/domain/*`)
- Infrastructure adapters and factory wiring (`src/infrastructure/*`)
- Data/vector pipeline (`src/data_pipeline/*`, `src/vectorstore/*`, `scripts/build_vectordb_cli.py`)
- Local persistence (`data/*`) with optional external boundaries (`iPlan`, `Gemini`)

## Operational and Verification Boundaries
- Command map and triage paths: `docs/manifest/09_runbook.md`
- API and boundary contracts: `docs/manifest/04_api_contracts.md`
- Data model and persistence surfaces: `docs/manifest/05_data_model.md`
- Observability posture: `docs/manifest/07_observability.md`
- CI gates: `.github/workflows/ci.yml`

## Notes on Legacy Content
Older drafts of this file included speculative architecture targets (for example, standalone REST service and Redis-centric runtime assumptions) that are not canonical for the current repository state. Those references are intentionally removed here to avoid drift.

## Related Docs
- `docs/HOW_IT_WORKS.md`
- `docs/manifest/01_architecture.md`
- `docs/implementation/checklists/00_architecture_coherence.md`
- `docs/implementation/reports/architecture_coherence_report.md`
