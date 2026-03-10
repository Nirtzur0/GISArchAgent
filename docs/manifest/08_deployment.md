# Deployment

## Current Deployment Shape
- Primary mode: local developer/operator deployment.
- Runtime process: Streamlit app (`app.py`) in a Python virtual environment.
- Data persistence: local filesystem under `data/`.

## Environments
- Local development: supported and documented.
- CI/staging/production hosted environments: not yet defined in repo artifacts.

## Build and Startup
- Environment bootstrap: `./setup.sh`.
- App launch: `./run_webapp.sh` (or `streamlit run app.py`).
- Vector DB maintenance: `scripts/build_vectordb_cli.py`.

## Trust Boundaries
- Outbound calls to iPlan ArcGIS.
- Optional outbound calls to Gemini APIs.
- Local data and vector persistence.

## Release Shape (Current)
- No formal release pipeline or tagging workflow is committed.
- No versioning/changelog/release checklist artifacts are currently present.

## Deployment Risks
- External dependency availability and SSL compatibility.
- Local environment drift across contributors (dependency and browser setup).
- Missing CI gate before changes are merged.

## Follow-up Outcomes
- Define CI workflow and release discipline artifacts.
- Add reproducible environment pinning strategy for higher determinism.
- Define deployment profile if hosted mode becomes in-scope.
