# Tech Stack

## Option A: Simplest Robust (Selected)
- UI: Streamlit (`app.py`, `pages/*`)
- Core runtime: Python 3.10+
- Domain/application layers: dataclass-driven clean architecture (`src/domain`, `src/application`, `src/infrastructure`)
- Data access:
  - iPlan ArcGIS via `requests` repository adapter
  - local JSON store via `src/data_management`
- Vector retrieval: ChromaDB local persistence (`data/vectorstore`)
- AI integrations:
  - Gemini LLM and Vision services (optional)
  - deterministic fallback answer path when no LLM key is configured
- Testing: `pytest` with strict markers (`pytest.ini`)
- Formatting/linting: `black`, `ruff` (`requirements-dev.txt`)
- Packaging/deps: `requirements.txt` + `requirements-dev.txt` + deterministic lock (`requirements.lock`)

### Why selected
- Matches current repo architecture and operational scripts.
- Lowest implementation risk for near-term milestones.
- Preserves local-first workflow with minimal migration overhead.

## Option B: More Scalable / Advanced
- Introduce explicit API service boundary (FastAPI) for programmatic access.
- Introduce async workers for ingestion and long-running analysis.
- Keep Streamlit as client UI over service contracts.
- Expand CI and release automation before scaling contributors.

### Why deferred
- Higher complexity and migration cost.
- Current goals focus on coherence, reliability, and docs alignment rather than platform expansion.

## Stack Gaps and Follow-ups
- CI/release workflows are committed and active (`.github/workflows/ci.yml`, `.github/workflows/release.yml`).
- Dependency reproducibility is now lock-backed (`requirements.lock`) with docs drift guard (`scripts/check_dependency_sync.py`, `docs/reference/dependencies.md`).
- Full-repo formatting conformance remains phased through debt-burn guardrails (`scripts/quality_black_debt_allowlist.txt`, `CMD-022`/`CMD-030`).
