# Repo Audit Checklist

### Project Intent vs Reality
- [x] What the project claims to be: a local-first Streamlit + CLI assistant for Israeli planning data/regulation search with reproducible operator workflows. Evidence: `README.md`, `docs/manifest/00_overview.md`.
- [x] What it actually provides:
  - [x] UI surfaces and app entrypoint (`app.py`, `pages/1_📍_Map_Viewer.py`, `pages/2_📐_Plan_Analyzer.py`, `pages/3_💾_Data_Management.py`).
  - [x] Service/domain/infrastructure layers and factory wiring (`src/application/services/*`, `src/domain/*`, `src/infrastructure/factory.py`).
  - [x] Local operations CLIs (`scripts/data_cli.py`, `scripts/build_vectordb_cli.py`, `scripts/quick_status.py`, `scripts/observability_cli.py`).
  - [x] CI + release workflows (`.github/workflows/ci.yml`, `.github/workflows/release.yml`).
- [ ] Top 3 alignment risks:
  - [ ] Legacy docs still claim release workflow is missing, conflicting with actual repo state. Evidence: `docs/HOW_IT_WORKS.md`, `.github/workflows/release.yml`.
  - [ ] Formatting governance is still phased (debt allowlist remains), so full-repo style consistency is not yet enforced. Evidence: `scripts/quality_black_debt_allowlist.txt` (66 lines), `docs/manifest/11_ci.md`.
  - [ ] External boundary trust assumptions are risky (TLS verification bypass on iPlan paths). Evidence: `src/infrastructure/repositories/iplan_repository.py`, `src/data_pipeline/discovery_service.py`, `docs/manifest/06_security.md`.

### Logic / Algorithm Alignment & Output Quality
- [x] Core logic entry points identified:
  - [x] Web flows: `app.py` + `pages/*`.
  - [x] CLI flows: `scripts/data_cli.py`, `scripts/build_vectordb_cli.py`, `scripts/quick_status.py`.
  - [x] Core services: `src/application/services/regulation_query_service.py`, `src/application/services/plan_search_service.py`.
  - [x] Build orchestration: `src/vectorstore/unified_pipeline.py`.
- [ ] Algorithm/logic alignment vs docs promises:
  - [x] Query/search/build boundaries mostly align to canonical manifest docs. Evidence: `docs/manifest/00_overview.md`, `docs/manifest/01_architecture.md`, `docs/manifest/04_api_contracts.md`.
  - [ ] Legacy docs contain stale claims (release workflow pending). Evidence: `docs/HOW_IT_WORKS.md`, `.github/workflows/release.yml`.
- [x] Output schema and semantics are documented:
  - [x] Query/search DTO interpretation (`docs/how_to/interpret_outputs.md`, `src/application/dtos.py`).
  - [x] Data/export formats (`docs/reference/data_formats.md`, `scripts/data_cli.py`).
  - [x] External boundary context and runbook commands (`docs/manifest/09_runbook.md`, `docs/troubleshooting.md`).
- [x] Correctness signals exist:
  - [x] Marker suites and strict marker taxonomy (`pytest.ini`, `tests/*`).
  - [x] Data contracts and integration suites (`tests/integration/data_contracts/*`, `tests/integration/vectordb/*`, `tests/integration/iplan/*`).
  - [x] Latest verification snapshots are green (`65 unit passed`, `23 integration passed`, `1 integration skipped`).
- [ ] Completeness gaps:
  - [ ] Full-repo formatting gate not yet enabled (phased debt-burn mode still active). Evidence: `docs/manifest/11_ci.md`, `scripts/quality_black_debt_allowlist.txt`.
  - [ ] Release checklist is present but mostly an unexecuted template outside an active tag cycle. Evidence: `docs/implementation/checklists/06_release_readiness.md`.
- [x] Interpretability posture:
  - [x] User-facing interpretation docs and reference exist (`docs/how_to/interpret_outputs.md`, `docs/reference/data_formats.md`).
  - [ ] Some legacy run guidance points to obsolete test paths, which can mislead interpretation/verification flow. Evidence: `docs/RUN_GUIDE.md`, `tests/`.

### User Journeys (Happy Paths)
- New user (install -> run minimal example -> understand outputs):
  - [x] Works today: `./setup.sh`, `./run_webapp.sh`, quickstart and docs index are coherent. Evidence: `README.md`, `docs/getting_started/installation.md`, `docs/getting_started/quickstart.md`, `docs/INDEX.md`.
  - [ ] Missing/fragile: `LICENSE` and `CONTRIBUTING.md` are absent; some legacy docs are stale. Evidence: `README.md` TODO section, `docs/HOW_IT_WORKS.md`.
  - [ ] Next step outcome: onboarding docs no longer reference stale release/testing claims and include licensing/contribution basics. Target: `docs/HOW_IT_WORKS.md`, `docs/RUN_GUIDE.md`, `CONTRIBUTING.md`, `LICENSE`.
- Power user (configure -> run end-to-end -> interpret results):
  - [x] Works today: CLI + runbook + observability bundle support deterministic triage and degraded-mode interpretation. Evidence: `scripts/*`, `docs/manifest/09_runbook.md`, `docs/troubleshooting.md`.
  - [ ] Missing/fragile: observability remains terminal-first; browser dashboard and network saturation/error-rate signals are not yet implemented. Evidence: `docs/manifest/07_observability.md`.
  - [ ] Next step outcome: power users can inspect golden signals in a browser-grade view or equivalent richer interface without changing event schema. Target: `docs/manifest/07_observability.md`, optional UI surface under `scripts/` or `pages/`.
- Contributor (run tests -> change safely -> validate):
  - [x] Works today: marker suites, lint gates, dependency sync check, and prompt-pack integrity checks are wired. Evidence: `.github/workflows/ci.yml`, `docs/manifest/11_ci.md`.
  - [ ] Missing/fragile: formatting debt allowlist means contributors can still hit inconsistent style boundaries across untouched files. Evidence: `scripts/quality_black_debt_allowlist.txt`, `docs/manifest/11_ci.md`.
  - [ ] Next step outcome: contributor flow reaches stable full-repo format gate (`black --check .`) with allowlist removed. Target: `.github/workflows/ci.yml`, `scripts/quality_black_debt_allowlist.txt`.

### Missing “Product” Pieces
- [x] Installation story - Solid.
  - Evidence: `docs/getting_started/installation.md`, `setup.sh`.
- [x] Hello world / minimal reproducible example - Solid.
  - Evidence: `docs/getting_started/quickstart.md`, `README.md` quickstart.
- [x] Config/story coherence - Solid.
  - Evidence: `src/config.py`, `docs/reference/configuration.md`, `docs/how_to/configuration.md`.
- [x] Reproducibility - Solid.
  - Evidence: `requirements.lock`, `scripts/check_dependency_sync.py`, `docs/reference/dependencies.md`.
- [ ] Observability - Partial.
  - Evidence: strong CLI/dashboard and alert routing exist (`scripts/observability_cli.py`, `docs/manifest/07_observability.md`), but browser dashboard and network saturation/error-rate signals remain open (`docs/manifest/07_observability.md`).
- [x] Output validation - Solid.
  - Evidence: `data_contracts` marker suites and integration contract tests (`tests/integration/data_contracts/*`, `tests/e2e/data_contracts/*`).
- [ ] Documentation structure - Partial.
  - Evidence: canonical Diataxis + manifest index is strong (`docs/INDEX.md`), but stale legacy guidance remains (`docs/HOW_IT_WORKS.md`, `docs/RUN_GUIDE.md`).
- [x] Testing strategy - Solid.
  - Evidence: `pytest.ini` markers + docs (`docs/manifest/10_testing.md`) + CI marker jobs.
- [ ] Packaging/release - Partial.
  - Evidence: release workflow and policy exist (`.github/workflows/release.yml`, `docs/reference/versioning_policy.md`, `docs/reference/release_workflow.md`), but no `LICENSE` and release checklist is not pre-filled for upcoming tag (`docs/implementation/checklists/06_release_readiness.md`).
- [ ] Security/safety basics - Partial.
  - Evidence: security baseline exists (`docs/manifest/06_security.md`) but TLS bypass and no security automation gate remain (`src/infrastructure/repositories/iplan_repository.py`, `.github/workflows/ci.yml`).
- [ ] Dependency/tooling stack coherence - Partial.
  - Evidence: inventory/lock/check tooling is solid (`docs/reference/dependencies.md`, `scripts/check_dependency_sync.py`), but some runtime deps are declared without active runtime usage (for example `fastapi`, `uvicorn` in `requirements.txt` with no code imports in `src/` or `scripts/`).

- [x] Dependency inventory (required):
  - Evidence: `requirements.txt`, `requirements-dev.txt`, `requirements.lock`, `docs/reference/dependencies.md`.
- [ ] Category map (required):
  - [x] Packaging/locking: `requirements.lock`, `scripts/check_dependency_sync.py`.
  - [x] Config + secrets: `pydantic-settings`, `.env` handling in `src/config.py`.
  - [x] Validation/contracts: pytest `data_contracts` suites in `tests/integration/data_contracts/*`.
  - [x] Lint/format/types baseline: `ruff`, `black` gates in `.github/workflows/ci.yml`.
  - [x] CI/release: `.github/workflows/ci.yml`, `.github/workflows/release.yml`.
  - [x] Observability: `src/telemetry.py`, `scripts/observability_cli.py`, `docs/manifest/07_observability.md`.
  - [x] Data/persistence: `chromadb` in `src/infrastructure/repositories/chroma_repository.py`.
  - [ ] Security automation category remains missing (no dependency scanning/SAST gate in CI).
- [ ] Bespoke vs buy (required):
  - [ ] TLS and external-boundary retry/validation behaviors are partly bespoke and should be normalized around explicit policy toggles and adapter wrappers. Evidence: `src/infrastructure/repositories/iplan_repository.py`, `src/data_pipeline/*`.
  - [x] Existing ecosystem tools are leveraged for quality and dependency drift (`ruff`, `black`, `pytest`, lock/doc sync checker).

### Architecture & Boundaries
- [x] Separation of concerns is clear (UI -> application -> domain -> infrastructure).
  - Evidence: `docs/manifest/01_architecture.md`, `src/application/*`, `src/domain/*`, `src/infrastructure/*`.
- [ ] Coupling pain points:
  - [ ] Factory singleton remains a central wiring hotspot for many boundaries. Evidence: `src/infrastructure/factory.py`.
  - [ ] External provider specifics leak into multiple pipeline/repository surfaces. Evidence: `src/infrastructure/repositories/iplan_repository.py`, `src/data_pipeline/*`.
- [ ] API/CLI boundary that should exist but does not:
  - [ ] `fastapi`/`uvicorn` are declared, but no maintained API boundary is implemented; this creates expectation drift. Evidence: `requirements.txt`, `src/`, `scripts/`.
- [ ] Architecture docs drift:
  - [ ] Legacy pages still contain stale runtime/CI statements; canonical manifest is accurate but supplementary pages need reconciliation. Evidence: `docs/HOW_IT_WORKS.md`, `docs/manifest/01_architecture.md`.

- [ ] High-impact recommendations (3-7):
  - [ ] Outcome: canonical and legacy architecture/how-it-works docs no longer contradict release/CI reality.
  - [ ] Outcome: iPlan boundary security mode is explicit (strict SSL default with documented opt-out for edge environments).
  - [ ] Outcome: contributor quality gates converge to full-repo formatting without allowlist debt.
  - [ ] Outcome: dependency manifest reflects active runtime boundaries (remove or justify unused API stack deps).

### UI/UX (If Applicable)
- [x] UI surfaces and launch path are clear.
  - Evidence: `app.py`, `pages/*`, `README.md`, `docs/getting_started/quickstart.md`.
- [x] UX-to-logic alignment is mostly coherent.
  - Evidence: UI pages route to service boundaries via factory (`src/infrastructure/factory.py`, `src/application/services/*`).
- [ ] Output presentation/clarity is partial.
  - Evidence: interpretation docs exist (`docs/how_to/interpret_outputs.md`), but legacy run docs still contain stale assertions that can confuse failure interpretation (`docs/RUN_GUIDE.md`, `docs/HOW_IT_WORKS.md`).
- [ ] Common UX footguns remain:
  - [ ] Hidden prerequisites for optional network/browser paths (`RUN_NETWORK_TESTS`, local Chrome for pydoll). Evidence: `tests/integration/iplan/test_pydoll_live_mavat_documents__optional.py`, `docs/manifest/10_testing.md`.
  - [ ] Empty/error state understanding relies on runbook literacy; a simpler operator-facing summary page is still missing. Evidence: `scripts/quick_status.py`, `docs/troubleshooting.md`.

### Consistency & Maintenance Risks
- [ ] Dead/unused entrypoints risk:
  - [ ] Optional API dependency stack appears unused in current code paths. Evidence: `requirements.txt`, no imports in `src/`/`scripts/`.
- [ ] Conflicting docs vs code:
  - [ ] `docs/HOW_IT_WORKS.md` says release workflow is pending, but it exists and is active. Evidence: `docs/HOW_IT_WORKS.md`, `.github/workflows/release.yml`.
  - [ ] `docs/RUN_GUIDE.md` references test files that no longer exist. Evidence: `docs/RUN_GUIDE.md`, `tests/`.
- [ ] Duplicate configs / policy spread:
  - [ ] Release and observability guidance is split across manifest/reference/how-to/legacy pages; drift risk remains if legacy pages are not kept synced.
- [ ] Works-on-my-machine assumptions:
  - [ ] TLS verify bypass and optional live-network paths can hide environment-specific failures. Evidence: `src/infrastructure/repositories/iplan_repository.py`, `tests/integration/iplan/test_pydoll_live_mavat_documents__optional.py`.
- [ ] Hidden prerequisites:
  - [ ] Browser runtime + external endpoint stability are required for some operational paths. Evidence: `README.md` prerequisites, `docs/manifest/10_testing.md`.

### Prioritized Next Steps

#### P0 (must fix to avoid misleading users)
- [ ] Outcome: canonical and legacy operational docs present the same release/CI truth.
  - Owner type: maintainer
  - Effort: S
  - Evidence: mismatch between `docs/HOW_IT_WORKS.md` and `.github/workflows/release.yml`.
- [ ] Outcome: external iPlan boundary uses explicit SSL policy controls with safe default and documented override path.
  - Owner type: maintainer
  - Effort: M
  - Evidence: `verify=False` usage in `src/infrastructure/repositories/iplan_repository.py` and `src/data_pipeline/*`.
- [ ] Outcome: stale runbook/test-path references are removed from legacy guides so contributor verification is not misleading.
  - Owner type: contributor
  - Effort: S
  - Evidence: `docs/RUN_GUIDE.md` references missing test files under `tests/`.

#### P1 (should fix to enable adoption)
- [ ] Outcome: formatting debt allowlist is reduced to zero and CI upgrades to full-repo `black --check`.
  - Owner type: maintainer
  - Effort: M/L
  - Evidence: `scripts/quality_black_debt_allowlist.txt` (66 lines), `docs/manifest/11_ci.md`.
- [ ] Outcome: repo has basic distribution/compliance metadata (`LICENSE`, `CONTRIBUTING.md`) aligned with release docs.
  - Owner type: contributor
  - Effort: S
  - Evidence: missing files noted in `README.md` TODO section.
- [ ] Outcome: dependency manifest is reconciled with active runtime boundaries (keep/remove/justify API stack deps).
  - Owner type: maintainer
  - Effort: S/M
  - Evidence: `requirements.txt` includes `fastapi`/`uvicorn` with no observed usage in `src/` or `scripts/`.

#### P2 (nice-to-have polish)
- [ ] Outcome: CI includes baseline security automation checks (dependency vulnerability scan and/or static security lint).
  - Owner type: maintainer
  - Effort: M
  - Evidence: no security automation stage in `.github/workflows/ci.yml`.
- [ ] Outcome: observability UX expands beyond terminal dashboard while preserving current event schema.
  - Owner type: contributor
  - Effort: M
  - Evidence: explicit gap in `docs/manifest/07_observability.md`.

### Prompt-00 Handoff (Required)
- [ ] **Top P0 outcomes to copy into `docs/implementation/checklists/02_milestones.md`**
  - [ ] Outcome: legacy docs release/CI drift removed.
    - target files/areas: `docs/HOW_IT_WORKS.md`, `docs/RUN_GUIDE.md`, `docs/INDEX.md`
    - acceptance signal: no stale "release workflow pending" claims and no references to missing test files.
    - suggested phase: `Phase 5`
  - [ ] Outcome: iPlan SSL policy hardened with explicit strict mode + override.
    - target files/areas: `src/infrastructure/repositories/iplan_repository.py`, `src/data_pipeline/*`, `docs/manifest/06_security.md`, `docs/troubleshooting.md`
    - acceptance signal: strict mode default (or explicit documented default), plus tests/docs for override path.
    - suggested phase: `Phase 5`
- [ ] **Top P1 outcomes to copy into `docs/implementation/checklists/02_milestones.md`**
  - [ ] Outcome: formatting debt allowlist reduced to zero and full-repo format gate enabled.
    - target files/areas: `scripts/quality_black_debt_allowlist.txt`, `.github/workflows/ci.yml`, `docs/manifest/11_ci.md`
    - acceptance signal: `wc -l scripts/quality_black_debt_allowlist.txt` -> `0`; CI uses full-repo `black --check`.
    - suggested phase: `Phase 6`
  - [ ] Outcome: repo compliance/contributor metadata completed.
    - target files/areas: `LICENSE`, `CONTRIBUTING.md`, `docs/reference/release_workflow.md`
    - acceptance signal: files exist and are linked from `README.md`/docs index.
    - suggested phase: `Phase 5`
- [ ] **Architecture drift outcomes to copy into `docs/implementation/checklists/00_architecture_coherence.md` (if used)**
  - [ ] Outcome: manifest and supplementary architecture pages stay synchronized with release/CI reality and boundary policy.
    - target files/areas: `docs/manifest/01_architecture.md`, `docs/ARCHITECTURE.md`, `docs/HOW_IT_WORKS.md`
    - acceptance signal: no contradictory runtime/CI statements across these pages.
    - suggested phase: `Phase 5`
- [ ] **Packaging/release outcomes to implement via `prompt-11-docs-diataxis-release.md` release discipline artifacts**
  - [ ] Outcome: release-readiness checklist is exercised per target tag and linked to version/changelog metadata.
    - target files/areas: `docs/implementation/checklists/06_release_readiness.md`, `CHANGELOG.md`, `docs/reference/versioning_policy.md`
    - acceptance signal: checklist items completed for release packet and `CMD-023`/`CMD-041` evidence recorded.
    - suggested phase: `Phase 5`
- [ ] **Observability/reliability outcomes to implement via `prompt-02-app-development-playbook.md` Observability & Reliability Gate**
  - [ ] Outcome: boundary security + observability policies are consistent and operator-friendly.
    - target files/areas: `src/infrastructure/repositories/iplan_repository.py`, `docs/manifest/06_security.md`, `docs/manifest/07_observability.md`, `docs/troubleshooting.md`
    - acceptance signal: strict SSL policy documented/tested; runbook triage commands remain coherent.
    - suggested phase: `Phase 5`
- [ ] **Recommended execution packeting**
  - [ ] First packet (1-5 items): fix stale docs contradictions + remove obsolete test path references + add `LICENSE`/`CONTRIBUTING.md`.
  - [ ] Second packet (1-5 items): implement SSL policy hardening with tests and docs.
  - [ ] Defer items: browser observability UI expansion and CI security automation until P0/P1 alignment drift is closed.
