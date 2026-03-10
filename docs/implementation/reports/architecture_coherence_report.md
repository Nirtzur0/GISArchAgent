# Architecture Coherence Report

## 1) Current Architecture Snapshot
- Manifest architecture (`docs/manifest/01_architecture.md`) was refreshed to current repo reality with explicit C4 context/containers/components, runtime scenarios, deployment boundaries, and risks.
- API/data boundary documents were refreshed to match current code contracts and persistence surfaces:
  - `docs/manifest/04_api_contracts.md`
  - `docs/manifest/05_data_model.md`
- Legacy architecture entrypoints were reconciled to avoid contradictory or speculative claims:
  - `docs/ARCHITECTURE.md`
  - `docs/HOW_IT_WORKS.md`

## 2) Diagram-to-Repo Mapping

| Element | Repo Evidence | Status |
| --- | --- | --- |
| UI container | `app.py`, `pages/*` | mapped |
| Application services | `src/application/services/*` | mapped |
| Domain model/contracts | `src/domain/*` | mapped |
| iPlan adapter boundary | `src/infrastructure/repositories/iplan_repository.py` | mapped |
| Chroma adapter boundary | `src/infrastructure/repositories/chroma_repository.py` | mapped |
| Data/vector pipeline container | `src/data_pipeline/*`, `src/vectorstore/*`, `scripts/build_vectordb_cli.py` | mapped |
| CI verification container | `.github/workflows/ci.yml` | mapped |
| Legacy architecture pages to manifest | `docs/ARCHITECTURE.md`, `docs/HOW_IT_WORKS.md` | mapped |

## 3) Key Mismatches, Decisions, and Open Risks
### Closed in this packet
- Closed: manifest architecture no longer claims missing CI baseline.
- Closed: legacy architecture pages no longer contain major contradictory runtime claims.
- Closed: architecture checklist/report now uses prompt-first routing context (no router script dependency).

### Still open
- Observability now has structured events + backend sinks + alert routing + query CLI baseline, but visual dashboard UX and richer resource saturation signals are still pending.
- CI quality gates now include incremental lint/format and release semantics checks; broader repo-wide quality conformance is still pending.

## 4) Verification Command Evidence
- `test -f app.py && test -f scripts/data_cli.py && test -f scripts/build_vectordb_cli.py`
- `rg -n "^markers =|unit:|integration:|e2e:|data_contracts:" pytest.ini`
- `test -f .github/workflows/ci.yml && rg -n "pytest -m unit|pytest -m integration|pytest -m e2e|pytest -m data_contracts" .github/workflows/ci.yml`
- `test -f .github/workflows/release.yml && rg -n "tags:|v\\*|pytest -m unit|pytest -m integration|pytest -m e2e|pytest -m data_contracts|prompts_manifest.py|system_integrity.py|action-gh-release" .github/workflows/release.yml`
- `python3 scripts/observability_cli.py summary --events-limit 200 --alerts-limit 200`
- `./venv/bin/ruff check src tests scripts --select E9,F63,F7`
- `./venv/bin/python scripts/check_release_semantics.py --tag v0.1.0 --changelog CHANGELOG.md`
- `python3 project-prompts/scripts/prompts_manifest.py --check`
- `python3 project-prompts/scripts/system_integrity.py --mode prompt_pack --root project-prompts`

## 5) Readiness Verdict and Rationale
- Verdict: GO_WITH_RISKS
- Rationale:
  - GO: architecture docs, contracts, and data model are coherent with code boundaries and current CI/release workflow state.
  - WITH_RISKS: operational maturity remains incomplete (visual observability UX depth + broader CI quality coverage + external dependency guardrails).

## 6) Now and Not now
### Now
- Execute degraded-mode guardrails packet for external dependency failures.
- Keep architecture/legacy docs synchronized as part of each packet closure.

### Not now
- Major service decomposition or platform redesign.
- Broad docs rewrite outside identified architecture/observability/CI drift items.
