# Deployment

## Current Deployment Shape
- Primary mode: local developer/operator deployment.
- Runtime process: FastAPI backend plus React/Vite frontend launched via `./run_webapp.sh`.
- Data persistence: local filesystem under `data/`.

## Environments
- Local development: supported and documented.
- CI/staging/production hosted environments: not yet defined in repo artifacts.

## Build and Startup
- Environment bootstrap: `./setup.sh`.
- App launch: `./run_webapp.sh`.
- Alternate local run: FastAPI on `8000` plus `frontend` Vite dev server on `5173`, with automatic port reassignment when those defaults are occupied.
- Vector DB maintenance: `scripts/build_vectordb_cli.py`.

## Trust Boundaries
- Outbound calls to iPlan ArcGIS.
- Optional outbound calls to OpenAI-compatible APIs.
- Local data and vector persistence.

## Release Shape (Current)
- No formal release pipeline or tagging workflow is committed.
- No versioning/changelog/release checklist artifacts are currently present.

## Deployment Risks
- External dependency availability and SSL compatibility.
- Local environment drift across contributors (dependency and browser setup).
- Hosted deployment profile is still undefined in repo artifacts.

## Follow-up Outcomes
- Define CI workflow and release discipline artifacts.
- Add reproducible environment pinning strategy for higher determinism.
- Define deployment profile if hosted mode becomes in-scope.
