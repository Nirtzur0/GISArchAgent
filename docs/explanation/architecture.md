# Architecture Explanation

This page explains the runtime architecture at a high level.

For a concept-first walkthrough of the problem domain, tradeoffs, and code mapping, see:
- `docs/explanation/problem_landscape_and_solution.md`

For canonical engineering details, see:
- `docs/manifest/01_architecture.md`
- `docs/manifest/04_api_contracts.md`
- `docs/manifest/05_data_model.md`

## Overview
GISArchAgent combines a Streamlit UI with application services, domain models, and infrastructure adapters to local/external data sources.

## Primary boundaries
- UI boundary: `app.py`, `pages/*`
- Service boundary: `src/application/services/*`
- Domain boundary: `src/domain/*`
- External/local infrastructure boundary: `src/infrastructure/*`, `src/vectorstore/*`, `src/data_pipeline/*`

## Why this split
- Keeps business behavior testable.
- Isolates external system failures.
- Supports local-first operation with optional AI integrations.
