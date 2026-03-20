# Improvement Bets Checklist

- Source report: `docs/implementation/reports/improvement_directions.md`
- Created by: `prompt-14-improvement-direction-bet-loop`
- Date: 2026-02-09

## IMP-01 - Observability Backend and Alert Routing
- [x] Outcome: critical workflow events are exported to a documented backend path with alert routing and saturation signal coverage.
  - Owner type: maintainer
  - Effort: M/L
  - Target files/areas: `src/telemetry.py`, `src/application/services/regulation_query_service.py`, `src/application/services/plan_search_service.py`, `src/vectorstore/unified_pipeline.py`, `docs/manifest/07_observability.md`, `docs/manifest/09_runbook.md`
  - Acceptance signal: backend collector path, alert thresholds, responder ownership, and query CLI commands are documented and verifiable.
  - Suggested prompt chain: `prompt-02` -> `prompt-03`

## IMP-02 - CI Quality-Gate Hardening and Release Semantics
- [x] Outcome: CI enforces lint/format checks and release workflow validates tag/changelog consistency.
  - Owner type: maintainer
  - Effort: S/M
  - Target files/areas: `.github/workflows/ci.yml`, `.github/workflows/release.yml`, optional validation script under `scripts/`, `docs/manifest/11_ci.md`, `docs/reference/release_workflow.md`
  - Acceptance signal: pull requests fail on style drift; release tag job fails when changelog/tag coherence is broken.
  - Suggested prompt chain: `prompt-02` -> `prompt-03`

## IMP-03 - Docs Navigation and Legacy Drift Cleanup
- [x] Outcome: canonical docs no longer contain contradictory guidance and navigation is consistent for users/contributors.
  - Owner type: contributor
  - Effort: S/M
  - Target files/areas: `docs/INDEX.md`, `docs/README.md`, `docs/manifest/10_testing.md`, selected legacy docs pages
  - Acceptance signal: stale claims are removed, primary links are coherent, and checklist/status references stay aligned.
  - Suggested prompt chain: `prompt-11` -> `prompt-03`

## IMP-04 - External Dependency Degradation Guardrails
- [x] Outcome: dependency failure/degraded paths are explicitly tested, observable, and triage-ready.
  - Owner type: maintainer
  - Effort: M
  - Target files/areas: `src/application/services/*`, `src/infrastructure/repositories/iplan_repository.py`, `tests/unit/application/test_external_dependency_degraded_modes.py`, `tests/unit/infrastructure/test_iplan_repository_error_signal.py`, `docs/manifest/07_observability.md`, `docs/troubleshooting.md`
  - Acceptance signal: deterministic degraded-mode tests pass and runbook triage steps are command-map aligned.
  - Suggested prompt chain: `prompt-10` -> `prompt-02` -> `prompt-03`

## IMP-05 - Reproducible Environment Lock Artifact
- [x] Outcome: deterministic dependency lock artifact exists and is command-map aligned.
  - Owner type: maintainer
  - Effort: S/M
  - Target files/areas: `requirements.lock`, `docs/manifest/02_tech_stack.md`, `docs/manifest/09_runbook.md`
  - Acceptance signal: lock regeneration and verification commands exist (`CMD-032`, `CMD-033`) and pass.
  - Suggested prompt chain: `prompt-02` -> `prompt-03`

## IMP-06 - Dependency-Doc Drift Automation
- [x] Outcome: CI detects drift between dependency manifests, lock artifact, and dependency inventory docs.
  - Owner type: maintainer
  - Effort: S
  - Target files/areas: `scripts/check_dependency_sync.py`, `.github/workflows/ci.yml`, `docs/reference/dependencies.md`, `docs/manifest/11_ci.md`
  - Acceptance signal: CI drift-check step fails on out-of-sync lock/docs and passes on synchronized state.
  - Suggested prompt chain: `prompt-02` -> `prompt-03`

## Post-M5 Next-Cycle Bets (from prompt-14 rerun)
### IMP-07 - Formatting Debt Burn (Phase 2)
- [x] Outcome: allowlist size is reduced by migrating one bounded module group into always-enforced formatting surfaces.
  - Owner type: maintainer
  - Effort: M
  - Target files/areas: `scripts/quality_black_debt_allowlist.txt`, `.github/workflows/ci.yml`, `src/domain/*`
  - Acceptance signal: allowlist count decreases and migrated modules are covered by strict format checks.
  - Verification:
    - `./venv/bin/black src/domain/__init__.py src/domain/entities/__init__.py src/domain/entities/analysis.py src/domain/entities/plan.py src/domain/entities/regulation.py src/domain/repositories/__init__.py src/domain/value_objects/__init__.py src/domain/value_objects/building_rights.py src/domain/value_objects/geometry.py`
    - `wc -l scripts/quality_black_debt_allowlist.txt` (before: `96`, after: `81`)
    - `rg -n "^src/domain/" scripts/quality_black_debt_allowlist.txt` (no matches)
    - `rg -n "src/domain/__init__.py|src/domain/entities/analysis.py|src/domain/value_objects/building_rights.py" .github/workflows/ci.yml docs/manifest/09_runbook.md`
  - Suggested prompt chain: `prompt-02` -> `prompt-03`

### IMP-08 - Observability Backend Evolution Decision
- [x] Outcome: explicit decision is recorded for local-only observability vs hosted backend/dashboard path.
  - Owner type: maintainer
  - Effort: M/L
  - Target files/areas: `docs/manifest/07_observability.md`, `docs/manifest/03_decisions.md`, `docs/implementation/reports/improvement_directions.md`
  - Acceptance signal: architecture-level decision + bounded implementation plan are documented.
  - Verification:
    - `rg -n "local-only|hosted|trigger|ADR-0017" docs/manifest/07_observability.md docs/manifest/03_decisions.md`
    - `rg -n "IMP-08|observability backend evolution" docs/implementation/reports/improvement_directions.md docs/implementation/checklists/02_milestones.md`
  - Suggested prompt chain: `prompt-14` -> `prompt-02`

### IMP-09 - External Dependency Drill Depth
- [x] Outcome: deterministic/non-network rehearsal coverage for dependency failures is expanded with explicit runbook drills.
  - Owner type: maintainer
  - Effort: M
  - Target files/areas: `tests/integration/iplan/*`, `docs/troubleshooting.md`, `docs/manifest/07_observability.md`
  - Acceptance signal: additional failure rehearsal commands/tests are green and triage instructions are tightened.
  - Verification:
    - `./venv/bin/python -m pytest tests/integration/iplan/test_external_dependency_drills.py -q`
    - `./venv/bin/python -m pytest tests/unit/application/test_external_dependency_degraded_modes.py tests/unit/infrastructure/test_iplan_repository_error_signal.py tests/integration/iplan/test_external_dependency_drills.py -q`
    - `rg -n "CMD-034|CMD-035|External dependency deterministic rehearsal" docs/manifest/09_runbook.md`
    - `rg -n "test_external_dependency_drills.py|CMD-034|CMD-035|deterministic" docs/manifest/07_observability.md docs/troubleshooting.md`
  - Suggested prompt chain: `prompt-10` -> `prompt-02` -> `prompt-03`

## Post-M6 Next-Cycle Bets (from post-IMP-09 prompt-14 rerun)
### IMP-10 - Formatting Debt Burn (Phase 3)
- [x] Outcome: allowlist size is reduced again by migrating one additional bounded module group into always-enforced formatting surfaces.
  - Owner type: maintainer
  - Effort: M
  - Target files/areas: `scripts/quality_black_debt_allowlist.txt`, `.github/workflows/ci.yml`, selected `src/*` module group
  - Acceptance signal: allowlist baseline decreases below `81` and migrated files are removed from debt allowlist and covered by strict formatting checks.
  - Verification:
    - `./venv/bin/black src/application/__init__.py src/application/dtos.py src/application/services/building_rights_service.py src/application/services/plan_upload_service.py`
    - `wc -l scripts/quality_black_debt_allowlist.txt` (before: `81`, after: `77`)
    - `rg -n "^src/application/(__init__\\.py|dtos\\.py|services/building_rights_service\\.py|services/plan_upload_service\\.py)$" scripts/quality_black_debt_allowlist.txt` (no matches)
    - `rg -n "src/application/__init__\\.py|src/application/dtos\\.py|src/application/services/building_rights_service\\.py|src/application/services/plan_upload_service\\.py|CMD-022" .github/workflows/ci.yml docs/manifest/09_runbook.md`
  - Suggested prompt chain: `prompt-02` -> `prompt-03`

### IMP-11 - Observability Threshold Calibration
- [x] Outcome: degraded/error threshold rationale and triage commands are recalibrated using current observability baseline evidence.
  - Owner type: maintainer
  - Effort: S/M
  - Target files/areas: `docs/manifest/07_observability.md`, `docs/troubleshooting.md`, `docs/manifest/09_runbook.md`, optional `src/telemetry.py`
  - Acceptance signal: threshold/triage docs explicitly reflect current dashboard baseline and command-map workflow.
  - Verification:
    - `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json`
    - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500`
    - `./venv/bin/python -m pytest tests/unit/infrastructure/test_telemetry_backend.py -q`
    - `rg -n "4000ms|8000ms|CMD-036|calibration|threshold" docs/manifest/07_observability.md docs/troubleshooting.md docs/manifest/09_runbook.md src/telemetry.py`
  - Suggested prompt chain: `prompt-02` -> `prompt-03`

### IMP-12 - Optional Live-Network Rehearsal Policy
- [x] Outcome: live-network rehearsal remains opt-in but is documented as a bounded, repeatable operational drill.
  - Owner type: maintainer
  - Effort: S
  - Target files/areas: `tests/integration/iplan/test_pydoll_live_mavat_documents__optional.py`, `docs/troubleshooting.md`, `docs/manifest/10_testing.md`, `docs/manifest/09_runbook.md`
  - Acceptance signal: explicit cadence/guardrail guidance exists for network rehearsals without destabilizing default CI.
  - Verification:
    - `./venv/bin/python -m pytest -m integration -q`
    - `RUN_NETWORK_TESTS=1 RUN_NETWORK_REHEARSAL_MAX_ATTEMPTS=1 RUN_NETWORK_REHEARSAL_TIMEOUT_SECONDS=45 ./venv/bin/python -m pytest tests/integration/iplan/test_pydoll_live_mavat_documents__optional.py -q`
    - `rg -n "RUN_NETWORK_TESTS|RUN_NETWORK_ALLOW_CI|RUN_NETWORK_REHEARSAL_MAX_ATTEMPTS|CMD-037|bounded|cadence" tests/integration/iplan/test_pydoll_live_mavat_documents__optional.py docs/troubleshooting.md docs/manifest/10_testing.md docs/manifest/09_runbook.md`
  - Suggested prompt chain: `prompt-10` -> `prompt-02` -> `prompt-03`

## Post-M7 Next-Cycle Bets (from post-IMP-12 prompt-14 rerun)
### IMP-13 - Threshold Recalibration Cadence Policy
- [x] Outcome: observability threshold recalibration is governed by explicit cadence and incident triggers.
  - Owner type: maintainer
  - Effort: S
  - Target files/areas: `docs/manifest/07_observability.md`, `docs/manifest/09_runbook.md`, `docs/troubleshooting.md`, optional `docs/implementation/checklists/02_milestones.md`
  - Acceptance signal: docs explicitly define when/how to rerun `CMD-036`, how to record baseline snapshots, and when threshold updates are required.
  - Verification:
    - `rg -n "CMD-036|cadence|weekly|trigger|recalibration" docs/manifest/07_observability.md docs/manifest/09_runbook.md docs/troubleshooting.md`
    - `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json`
    - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500`
  - Suggested prompt chain: `prompt-02` -> `prompt-03`

### IMP-14 - Formatting Debt Burn (Phase 4)
- [x] Outcome: one additional bounded module group is migrated from allowlist debt into always-enforced format surfaces.
  - Owner type: maintainer
  - Effort: M
  - Target files/areas: `scripts/quality_black_debt_allowlist.txt`, `.github/workflows/ci.yml`, `docs/manifest/09_runbook.md`, `src/data_management/*`
  - Acceptance signal: allowlist baseline drops below `77`, selected files are removed from allowlist, and `CMD-022` coverage is expanded for migrated files.
  - Verification:
    - `./venv/bin/black src/data_management/__init__.py src/data_management/data_store.py src/data_management/fetchers.py src/data_management/pydoll_fetcher.py`
    - `wc -l scripts/quality_black_debt_allowlist.txt`
    - `rg -n "^src/data_management/(__init__\\.py|data_store\\.py|fetchers\\.py|pydoll_fetcher\\.py)$" scripts/quality_black_debt_allowlist.txt` (no matches)
    - `BASE_SHA=$(git rev-parse HEAD~1) && python3 scripts/quality_changed_python.py --base "$BASE_SHA" --head HEAD --exclude-file scripts/quality_black_debt_allowlist.txt --print0 | xargs -0 -r ./venv/bin/black --check`
    - `rg -n "CMD-022|quality_black_debt_allowlist" .github/workflows/ci.yml docs/manifest/09_runbook.md docs/manifest/11_ci.md`
  - Suggested prompt chain: `prompt-02` -> `prompt-03`

### IMP-15 - Saturation Snapshot Discipline
- [x] Outcome: observability triage policy explicitly captures saturation snapshots during active build windows, not only passive query windows.
  - Owner type: maintainer
  - Effort: S/M
  - Target files/areas: `docs/manifest/07_observability.md`, `docs/manifest/09_runbook.md`, `docs/troubleshooting.md`, optional `scripts/observability_cli.py`
  - Acceptance signal: runbook documents a repeatable build-window drill and expected saturation fields (`saturation_ratio_1m`, `memory_used_ratio`, `disk_free_ratio_cache_dir`) for incident evidence.
  - Verification:
    - `(python3 scripts/build_vectordb_cli.py build --max-plans 1 --no-vision || true) && python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500`
    - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500`
    - `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json`
    - `rg -n "saturation_ratio_1m|memory_used_ratio|disk_free_ratio_cache_dir|build-window|snapshot" docs/manifest/07_observability.md docs/manifest/09_runbook.md docs/troubleshooting.md`
  - Suggested prompt chain: `prompt-02` -> `prompt-03`

## Post-M8 Next-Cycle Bets (from post-IMP-15 prompt-14 rerun)
### IMP-16 - Artifact-Feature Alignment Baseline Gate
- [x] Outcome: create explicit artifact-to-feature alignment verdict and map artifact-backed corrections/opportunities into milestones.
  - Owner type: maintainer
  - Effort: S/M
  - Target files/areas: `docs/implementation/checklists/08_artifact_feature_alignment.md`, `docs/implementation/reports/artifact_feature_alignment.md`, `docs/implementation/checklists/02_milestones.md`
  - Acceptance signal: alignment artifacts exist with matrix coverage and explicit verdict (`ALIGNED`, `ALIGNED_WITH_GAPS`, or `MISALIGNED`), and top outcomes are schedulable.
  - Verification:
    - `test -f docs/implementation/checklists/08_artifact_feature_alignment.md`
    - `test -f docs/implementation/reports/artifact_feature_alignment.md`
    - `rg -n "Artifact ID|Expected implication|Status \\(Supported/Partial/Missing/Misaligned\\)|ALIGNED|ALIGNED_WITH_GAPS|MISALIGNED" docs/implementation/reports/artifact_feature_alignment.md docs/implementation/checklists/08_artifact_feature_alignment.md`
    - `rg -n "M9|artifact" docs/implementation/checklists/02_milestones.md`
    - `test -f docs/artifacts/README.md && test -f docs/artifacts/index.json`
  - Suggested prompt chain: `prompt-15` -> `prompt-03`

### IMP-17 - Saturation Signal Completeness (Memory Pressure)
- [x] Outcome: build-window saturation snapshots include actionable memory pressure context (or explicit availability semantics) for consistent triage evidence.
  - Owner type: maintainer
  - Effort: S/M
  - Target files/areas: `src/vectorstore/unified_pipeline.py`, `src/observability/query.py`, `scripts/observability_cli.py`, `docs/manifest/07_observability.md`, `docs/troubleshooting.md`
  - Acceptance signal: dashboard/summary windows stop presenting opaque memory signal gaps and triage docs explicitly describe interpretation.
  - Verification:
    - `(python3 scripts/build_vectordb_cli.py build --max-plans 1 --no-vision || true) && python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500`
    - `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json`
    - `./venv/bin/python -m pytest tests/unit/infrastructure/test_telemetry_backend.py tests/unit/infrastructure/test_observability_query.py tests/unit/vectorstore/test_unified_pipeline_saturation_snapshot.py -q`
    - `rg -n "memory_used_ratio|memory_used_ratio_source|memory_used_ratio_unavailable_reason|rss_mb|saturation_ratio_1m" src/vectorstore/unified_pipeline.py src/observability/query.py docs/manifest/07_observability.md docs/troubleshooting.md docs/manifest/09_runbook.md`
  - Suggested prompt chain: `prompt-02` -> `prompt-10` -> `prompt-03`

### IMP-18 - Formatting Debt Burn (Phase 5, Infrastructure Batch)
- [x] Outcome: migrate a bounded `src/infrastructure/*` group from debt allowlist into always-enforced formatting surfaces.
  - Owner type: maintainer
  - Effort: M
  - Target files/areas: `scripts/quality_black_debt_allowlist.txt`, `.github/workflows/ci.yml`, `docs/manifest/09_runbook.md`, `src/infrastructure/*`
  - Acceptance signal: allowlist baseline decreases below `73`, migrated infrastructure files are removed from allowlist, and strict formatting checks cover them.
  - Verification:
    - `./venv/bin/black src/infrastructure/__init__.py src/infrastructure/factory.py src/infrastructure/repositories/chroma_repository.py src/infrastructure/services/cache_service.py src/infrastructure/services/document_service.py src/infrastructure/services/llm_service.py src/infrastructure/services/vision_service.py`
    - `wc -l scripts/quality_black_debt_allowlist.txt`
    - `rg -n "^src/infrastructure/(__init__\\.py|factory\\.py|repositories/chroma_repository\\.py|services/cache_service\\.py|services/document_service\\.py|services/llm_service\\.py|services/vision_service\\.py)$" scripts/quality_black_debt_allowlist.txt` (no matches)
    - `rg -n "src/infrastructure/__init__\\.py|src/infrastructure/factory\\.py|src/infrastructure/repositories/chroma_repository\\.py|src/infrastructure/repositories/iplan_repository\\.py|src/infrastructure/services/cache_service\\.py|src/infrastructure/services/document_service\\.py|src/infrastructure/services/llm_service\\.py|src/infrastructure/services/vision_service\\.py|CMD-022" .github/workflows/ci.yml docs/manifest/09_runbook.md docs/manifest/11_ci.md`
  - Suggested prompt chain: `prompt-02` -> `prompt-03`

### IMP-19 - Evidence Cadence Ledger Hardening
- [x] Outcome: recurring observability evidence capture is centralized in one checklisted ledger surface.
  - Owner type: maintainer
  - Effort: S
  - Target files/areas: `docs/implementation/checklists/09_evidence_cadence_ledger.md`, `docs/manifest/09_runbook.md`, `docs/manifest/07_observability.md`, `docs/implementation/03_worklog.md`
  - Acceptance signal: `CMD-036` + `CMD-029` + `CMD-038` (+ `CMD-039`) cadence evidence is captured in one canonical checklisted file and referenced by runbook/observability policy.
  - Verification:
    - `test -f docs/implementation/checklists/09_evidence_cadence_ledger.md`
    - `rg -n "CMD-036|CMD-029|CMD-038|CMD-039|IMP-19 bootstrap entry" docs/implementation/checklists/09_evidence_cadence_ledger.md docs/manifest/09_runbook.md docs/manifest/07_observability.md`
    - `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json`
    - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500`
    - `(python3 scripts/build_vectordb_cli.py build --max-plans 1 --no-vision || true) && python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500`
  - Suggested prompt chain: `prompt-11` -> `prompt-03`

## Post-M11 Next-Cycle Bets (from post-M11 prompt-14 rerun)
### IMP-20 - Release Workflow `CMD-041` Automation
- [x] Outcome: release validation job enforces onboarding/reference artifact-link citation guardrail before publish path.
  - Owner type: maintainer
  - Effort: S
  - Target files/areas: `.github/workflows/release.yml`, `docs/reference/release_workflow.md`, `docs/manifest/11_ci.md`
  - Acceptance signal: release workflow fails if required `artifact:ART-EXT-*` citations are missing from onboarding/reference boundary docs.
  - Suggested prompt chain: `prompt-02` -> `prompt-03`

### IMP-21 - Timeout-Noise Boundary Triage Tightening
- [x] Outcome: first-pass operator flow clearly distinguishes recurring build timeout sev1 noise from boundary-degraded escalation paths.
  - Owner type: maintainer
  - Effort: S/M
  - Target files/areas: `scripts/quick_status.py`, `docs/troubleshooting.md`, `docs/manifest/07_observability.md`, `docs/manifest/09_runbook.md`
  - Acceptance signal: `CMD-040` reports explicit `historical_build_timeout_sev1_noise` + `warning_noise_profile` and docs map corresponding narrowed-window escalation guards (`CMD-026`/`CMD-028`).
  - Suggested prompt chain: `prompt-02` -> `prompt-03`

### IMP-22 - Post-M12 Convergence Guardrail
- [x] Outcome: improvement-direction routing includes an explicit convergence check to prevent repetitive low-impact packet loops.
  - Owner type: maintainer
  - Effort: S
  - Target files/areas: `docs/implementation/reports/improvement_directions.md`, `docs/implementation/checklists/03_improvement_bets.md`, `docs/implementation/checklists/02_milestones.md`
  - Acceptance signal: rerank notes include bounded repeat-loop stop condition and explicit unresolved-outcome delta check before reusing the same immediate packet route.
  - Suggested prompt chain: `prompt-14` -> `prompt-03`

## Post-M12 Next-Cycle Bets (user-requested planner UX redesign)
### IMP-23 - Planner UX Redesign and Design-System Handoff
- [x] Outcome: planner-first UX redesign is implemented in the frontend and paired with a Figma-backed audit/handoff packet.
  - Owner type: maintainer
  - Effort: M/L
  - Target files/areas: `frontend/src/AppRedesign.tsx`, `frontend/src/styles.redesign.css`, `frontend/tests/app.spec.ts`, `docs/implementation/reports/dashboard_ux_audit_redesign.md`, `docs/implementation/checklists/10_dashboard_redesign.md`, Figma file `GISArchAgent - Planner UX Redesign`
  - Acceptance signal: redesigned planner-first routes are shipped, browser verification passes, the report/checklist exist, and the Figma file contains baseline plus redesign captures.
  - Verification:
    - `cd frontend && npm run build`
    - `cd frontend && npm run test:e2e`
    - `test -f docs/implementation/reports/dashboard_ux_audit_redesign.md`
    - `test -f docs/implementation/checklists/10_dashboard_redesign.md`
    - open `https://www.figma.com/design/d6ExX1CAGJtmV6HzA1j73D` and confirm current-state, redesign, and handoff frames are present
  - Suggested prompt chain: `prompt-06` -> `prompt-02` -> `prompt-03`
