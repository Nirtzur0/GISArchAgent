# Milestones

## M0 - Shape Baseline (Completed)
- [x] Outcome: docs baseline, objective, PRD, architecture coherence packet, and audit handoff are established.
  - AC: required manifest + implementation + audit files exist and are coherent.
  - Verify: `test -f docs/manifest/00_overview.md && test -f docs/implementation/reports/prd.md && test -f docs/implementation/checklists/00_architecture_coherence.md && test -f checkbox.md`
  - Files: `docs/manifest/*`, `docs/implementation/*`, `checkbox.md`
  - Docs: `docs/implementation/00_status.md`, `docs/implementation/03_worklog.md`
  - Alternatives: N/A

## M1 - P0 Reliability and Release Discipline
- [x] Outcome: CI baseline exists and enforces canonical tests and docs status updates.
  - AC: `.github/workflows/*` exists and runs marker test gates (`unit`, `integration`, `e2e`, `data_contracts`) and prompt-pack integrity checks.
  - Verify:
    - `./venv/bin/python -m pytest -m unit -q`
    - `./venv/bin/python -m pytest -m integration -q`
    - `./venv/bin/python -m pytest -m e2e -q`
    - `./venv/bin/python -m pytest -m data_contracts -q`
    - `python3 project-prompts/scripts/prompts_manifest.py --check`
    - `python3 project-prompts/scripts/system_integrity.py --mode prompt_pack --root project-prompts`
  - Files: `.github/workflows/ci.yml`, `docs/manifest/11_ci.md`
  - Docs: `docs/implementation/00_status.md`, `docs/manifest/09_runbook.md`, `docs/reference/release_workflow.md`
  - Alternatives: use single combined test job vs split jobs.

- [x] Outcome: release discipline artifacts are committed.
  - AC: `CHANGELOG.md`, versioning policy, release checklist, upgrade notes template exist.
  - Verify: `test -f CHANGELOG.md && test -f docs/reference/versioning_policy.md && test -f docs/implementation/checklists/06_release_readiness.md && test -f docs/how_to/upgrade_notes_template.md`
  - Files: `CHANGELOG.md`, `docs/reference/versioning_policy.md`, `docs/implementation/checklists/06_release_readiness.md`, `docs/how_to/upgrade_notes_template.md`
  - Docs: `docs/manifest/11_ci.md`, `docs/reference/release_workflow.md`, `docs/INDEX.md`
  - Alternatives: lightweight docs-only release process for first iteration.

- [x] Outcome: dedicated tag/release workflow automates release validation and publish path.
  - AC: `.github/workflows/release.yml` exists, runs marker + prompt-pack checks on `v*` tags, and publishes GitHub release notes.
  - Verify:
    - `test -f .github/workflows/release.yml`
    - `rg -n "tags:|v\\*|pytest -m unit|pytest -m integration|pytest -m e2e|pytest -m data_contracts|prompts_manifest.py|system_integrity.py|action-gh-release" .github/workflows/release.yml`
  - Files: `.github/workflows/release.yml`, `docs/reference/release_workflow.md`
  - Docs: `docs/manifest/11_ci.md`, `docs/manifest/09_runbook.md`, `docs/implementation/03_worklog.md`
  - Alternatives: keep release publishing fully manual and run validation locally only.

## M2 - P1 Architecture and Observability Hardening
- [x] Outcome: observability plan is partially instrumented for critical workflows.
  - AC: structured logging/correlation and workflow-level metrics are present for query + build paths.
  - Verify:
    - `./venv/bin/python -m pytest tests/unit/application/test_regulation_query_service__fallback.py -q`
    - `./venv/bin/python -m pytest -m unit -q`
    - `rg -n "OBS_EVENT|emit_observability_event|workflow_metrics.jsonl|request_id" src/application/services/regulation_query_service.py src/application/services/plan_search_service.py src/vectorstore/unified_pipeline.py src/telemetry.py`
  - Files: `src/application/services/regulation_query_service.py`, `src/application/services/plan_search_service.py`, `src/vectorstore/unified_pipeline.py`, `src/application/dtos.py`, `src/telemetry.py`
  - Docs: `docs/manifest/07_observability.md`, `docs/manifest/09_runbook.md`, `docs/implementation/03_worklog.md`
  - Alternatives: staged instrumentation (query path first, build path second).

- [x] Outcome: legacy architecture docs are reconciled to manifest architecture.
  - AC: no major contradictions between `docs/manifest/01_architecture.md` and legacy architecture pages.
  - Verify:
    - `test -f app.py && test -f scripts/data_cli.py && test -f scripts/build_vectordb_cli.py`
    - `rg -n "^markers =|unit:|integration:|e2e:|data_contracts:" pytest.ini`
    - `test -f .github/workflows/ci.yml && rg -n "pytest -m unit|pytest -m integration|pytest -m e2e|pytest -m data_contracts" .github/workflows/ci.yml`
  - Files: `docs/ARCHITECTURE.md`, `docs/HOW_IT_WORKS.md`, `docs/manifest/01_architecture.md`, `docs/manifest/04_api_contracts.md`, `docs/manifest/05_data_model.md`
  - Docs: `docs/implementation/checklists/00_architecture_coherence.md`, `docs/implementation/reports/architecture_coherence_report.md`
  - Alternatives: retain legacy docs as linked deep-dives only.

## M3 - P2 UX and Maintenance Polish
- [x] Outcome: docs navigation and quickstart are cleaned and consistent.
  - AC: broken/duplicate links removed, and stale operational claims are removed from primary onboarding/engineering docs.
  - Verify:
    - `! rg -n "CI is not yet wired|release automation still missing|CI workflows still missing|until CI/release automation exists" docs/INDEX.md docs/README.md docs/manifest/10_testing.md`
    - `rg -n "Getting Started|Reference|Engineering Docs" docs/INDEX.md docs/README.md`
    - `rg -o "docs/[A-Za-z0-9_./-]+\\.md" docs/INDEX.md docs/README.md | sed 's/:.*://g' | awk '{print $NF}' | sort -u | xargs -I{} test -f "{}"`
  - Files: `docs/README.md`, `docs/INDEX.md`, `docs/manifest/10_testing.md`
  - Docs: `docs/implementation/checklists/03_improvement_bets.md`, `docs/implementation/03_worklog.md`
  - Alternatives: keep legacy docs untouched and add warnings.

## M4 - P3 Operational Maturity (Improvement Bets)
- [x] Outcome: observability backend and alert routing are added for critical workflows.
  - AC: structured events are consumable via a documented backend path; thresholded alerts and responder ownership are defined; saturation signal coverage exists for build flow.
  - Verify:
    - `rg -n "backend|dashboard|alert|saturation" docs/manifest/07_observability.md`
    - `rg -n "CMD-015|CMD-019|CMD-020|CMD-024|CMD-025|CMD-026|triage|observability" docs/manifest/09_runbook.md`
    - `python3 scripts/observability_cli.py summary --events-limit 200 --alerts-limit 200`
    - `./venv/bin/python -m pytest tests/unit/infrastructure/test_telemetry_backend.py -q`
    - `./venv/bin/python -m pytest tests/unit/infrastructure/test_observability_query.py -q`
    - `./venv/bin/python -m pytest -m unit -q`
    - `./venv/bin/python -m pytest -m integration -q`
  - Files: `src/telemetry.py`, `src/observability/query.py`, `scripts/observability_cli.py`, `src/application/services/regulation_query_service.py`, `src/application/services/plan_search_service.py`, `src/vectorstore/unified_pipeline.py`, `tests/unit/infrastructure/test_telemetry_backend.py`, `tests/unit/infrastructure/test_observability_query.py`
  - Docs: `docs/manifest/07_observability.md`, `docs/manifest/09_runbook.md`, `docs/implementation/checklists/03_improvement_bets.md`
  - Alternatives: keep local-only logs/JSONL and defer backend routing.

- [x] Outcome: CI quality gates and release semantic checks are hardened.
  - AC: CI enforces lint/format checks; release workflow validates tag/changelog coherence before publish.
  - Verify:
    - `rg -n "Incremental lint gate|Format guard|ruff check|black --check" .github/workflows/ci.yml`
    - `rg -n "check_release_semantics.py|ref_name|CMD-023" .github/workflows/release.yml`
    - `./venv/bin/ruff check src tests scripts --select E9,F63,F7`
    - `./venv/bin/black --check src/telemetry.py src/vectorstore/unified_pipeline.py tests/unit/infrastructure/test_telemetry_backend.py scripts/check_release_semantics.py`
    - `./venv/bin/python scripts/check_release_semantics.py --tag v0.1.0 --changelog CHANGELOG.md`
    - `python3 project-prompts/scripts/prompts_manifest.py --check`
    - `python3 project-prompts/scripts/system_integrity.py --mode prompt_pack --root project-prompts`
  - Files: `.github/workflows/ci.yml`, `.github/workflows/release.yml`, `scripts/check_release_semantics.py`
  - Docs: `docs/manifest/11_ci.md`, `docs/reference/release_workflow.md`, `docs/implementation/checklists/03_improvement_bets.md`
  - Alternatives: keep marker-only quality gates and manual release semantics review.

- [x] Outcome: external dependency degraded-mode guardrails are explicit and testable.
  - AC: iPlan/Gemini degraded paths have deterministic tests and runbook triage guidance.
  - Verify:
    - `./venv/bin/python -m pytest tests/unit/application/test_external_dependency_degraded_modes.py -q`
    - `./venv/bin/python -m pytest tests/unit/infrastructure/test_iplan_repository_error_signal.py -q`
    - `./venv/bin/python -m pytest -m integration -q`
    - `rg -n "degraded_reasons|iplan_|vision_service_unavailable|llm_synthesis_unavailable" src/application/services/regulation_query_service.py src/application/services/plan_search_service.py`
    - `rg -n "CMD-027|CMD-028|degraded|external dependency" docs/manifest/09_runbook.md docs/manifest/07_observability.md docs/troubleshooting.md`
  - Files: `src/application/services/*`, `src/infrastructure/repositories/iplan_repository.py`, `tests/unit/application/test_external_dependency_degraded_modes.py`, `tests/unit/infrastructure/test_iplan_repository_error_signal.py`
  - Docs: `docs/manifest/07_observability.md`, `docs/troubleshooting.md`, `docs/implementation/checklists/03_improvement_bets.md`
  - Alternatives: rely on ad-hoc manual triage for external failures.

## M5 - P4 Post-Alignment Follow-ups (Completed)
- [x] Outcome: observability UX depth is expanded beyond JSONL/CLI baseline.
  - AC: visual/operator-friendly dashboard path and richer saturation signals are documented and command-map aligned.
  - Verify:
    - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500`
    - `python3 scripts/observability_cli.py summary --events-limit 500 --alerts-limit 500`
    - `./venv/bin/python -m pytest tests/unit/infrastructure/test_observability_query.py -q`
    - `./venv/bin/python -m pytest tests/unit/infrastructure/test_telemetry_backend.py -q`
    - `rg -n "CMD-029|memory_used_ratio|disk_free_ratio_cache_dir|rss_mb" docs/manifest/09_runbook.md docs/manifest/07_observability.md src/vectorstore/unified_pipeline.py`
  - Files: `src/vectorstore/unified_pipeline.py`, `src/telemetry.py`, `src/observability/query.py`, `scripts/observability_cli.py`, `tests/unit/infrastructure/test_observability_query.py`, `tests/unit/infrastructure/test_telemetry_backend.py`
  - Docs: `docs/manifest/07_observability.md`, `docs/manifest/09_runbook.md`, `docs/reference/cli.md`
  - Alternatives: keep CLI-only observability triage.

- [x] Outcome: CI quality gate coverage is widened with bounded debt plan.
  - AC: quality workflow includes broader lint/format surfaces and explicit debt-burn sequencing.
  - Verify:
    - `rg -n "Expanded lint gate|CMD-021|CMD-022|CMD-030|quality_changed_python.py|ruff check \\.|black --check" .github/workflows/ci.yml`
    - `./venv/bin/ruff check . --select E9,F63,F7 --exclude project-prompts`
    - `BASE_SHA=$(git rev-parse HEAD~1) && python3 scripts/quality_changed_python.py --base "$BASE_SHA" --head HEAD --exclude-file scripts/quality_black_debt_allowlist.txt --count`
    - `BASE_SHA=$(git rev-parse HEAD~1) && python3 scripts/quality_changed_python.py --base "$BASE_SHA" --head HEAD --exclude-file scripts/quality_black_debt_allowlist.txt --print0 | xargs -0 -r ./venv/bin/black --check`
    - `wc -l scripts/quality_black_debt_allowlist.txt`
  - Files: `.github/workflows/ci.yml`, `scripts/quality_changed_python.py`, `scripts/quality_black_debt_allowlist.txt`
  - Docs: `docs/manifest/11_ci.md`, `docs/manifest/09_runbook.md`
  - Alternatives: keep incremental checks unchanged.

- [x] Outcome: reproducible environment lock + dependency-doc drift checks are added.
  - AC: deterministic recreate path exists and CI can detect dependency/docs mismatch.
  - Verify:
    - `test -f requirements.lock`
    - `python3 scripts/check_dependency_sync.py --requirements requirements.txt --dev-requirements requirements-dev.txt --lock requirements.lock --doc docs/reference/dependencies.md`
    - `rg -n "CMD-032|CMD-033|check_dependency_sync.py|requirements.lock" docs/manifest/09_runbook.md docs/manifest/11_ci.md .github/workflows/ci.yml`
  - Files: `requirements.lock`, `scripts/check_dependency_sync.py`, `.github/workflows/ci.yml`
  - Docs: `docs/manifest/02_tech_stack.md`, `docs/manifest/11_ci.md`, `docs/reference/dependencies.md`, `docs/manifest/09_runbook.md`
  - Alternatives: rely on manual dependency/doc updates only.

## M6 - Next-Cycle Bounded Improvements (Completed)
- [x] Outcome: formatting debt burn phase 2 completed for one bounded module group.
  - AC: one module group is reformatted, removed from allowlist, and promoted to always-enforced formatting surfaces.
  - Verify:
    - `./venv/bin/black src/domain/__init__.py src/domain/entities/__init__.py src/domain/entities/analysis.py src/domain/entities/plan.py src/domain/entities/regulation.py src/domain/repositories/__init__.py src/domain/value_objects/__init__.py src/domain/value_objects/building_rights.py src/domain/value_objects/geometry.py`
    - `wc -l scripts/quality_black_debt_allowlist.txt` (before: `96`, after: `81`)
    - `rg -n "^src/domain/" scripts/quality_black_debt_allowlist.txt` (no matches)
    - `rg -n "src/domain/__init__.py|src/domain/entities/analysis.py|src/domain/value_objects/building_rights.py" .github/workflows/ci.yml docs/manifest/09_runbook.md`
  - Files: `scripts/quality_black_debt_allowlist.txt`, `.github/workflows/ci.yml`, `src/domain/*`
  - Docs: `docs/manifest/11_ci.md`, `docs/manifest/09_runbook.md`, `docs/implementation/checklists/03_improvement_bets.md`
  - Alternatives: keep allowlist unchanged and rely only on changed-file formatting checks.

- [x] Outcome: observability backend evolution direction is explicitly selected (local-only vs hosted path).
  - AC: an architecture-level decision and bounded implementation plan are documented.
  - Verify:
    - `rg -n "local-only|hosted|trigger|ADR-0017" docs/manifest/07_observability.md docs/manifest/03_decisions.md`
    - `rg -n "IMP-08|observability backend evolution" docs/implementation/reports/improvement_directions.md docs/implementation/checklists/03_improvement_bets.md`
  - Files: `docs/manifest/07_observability.md`, `docs/manifest/03_decisions.md`
  - Docs: `docs/implementation/reports/improvement_directions.md`
  - Alternatives: defer decision and continue incremental local tooling only.

- [x] Outcome: deterministic external dependency drill depth is expanded.
  - AC: additional deterministic/non-network failure rehearsal is documented and test-covered.
  - Verify:
    - `./venv/bin/python -m pytest tests/integration/iplan/test_external_dependency_drills.py -q`
    - `./venv/bin/python -m pytest tests/unit/application/test_external_dependency_degraded_modes.py tests/unit/infrastructure/test_iplan_repository_error_signal.py tests/integration/iplan/test_external_dependency_drills.py -q`
    - `rg -n "CMD-034|CMD-035|External dependency deterministic rehearsal" docs/manifest/09_runbook.md`
    - `rg -n "test_external_dependency_drills.py|CMD-034|CMD-035|rehearsal" docs/troubleshooting.md docs/manifest/07_observability.md`
  - Files: `tests/integration/iplan/test_external_dependency_drills.py`, `docs/troubleshooting.md`, `docs/manifest/09_runbook.md`
  - Docs: `docs/manifest/07_observability.md`, `docs/implementation/checklists/03_improvement_bets.md`
  - Alternatives: keep current degraded-path coverage unchanged.

## M7 - Post-M6 Alignment Corrections (Completed)
- [x] Outcome: formatting debt burn phase 3 migrates one additional bounded module group into always-enforced format surfaces.
  - AC: allowlist baseline decreases from current `81` lines and migrated files are removed from debt allowlist.
  - Verify:
    - `./venv/bin/black src/application/__init__.py src/application/dtos.py src/application/services/building_rights_service.py src/application/services/plan_upload_service.py`
    - `wc -l scripts/quality_black_debt_allowlist.txt` (before: `81`, after: `77`)
    - `rg -n "^src/application/(__init__\\.py|dtos\\.py|services/building_rights_service\\.py|services/plan_upload_service\\.py)$" scripts/quality_black_debt_allowlist.txt` (no matches)
    - `rg -n "src/application/__init__\\.py|src/application/dtos\\.py|src/application/services/building_rights_service\\.py|src/application/services/plan_upload_service\\.py|CMD-022" .github/workflows/ci.yml docs/manifest/09_runbook.md`
    - `BASE_SHA=$(git rev-parse HEAD~1) && python3 scripts/quality_changed_python.py --base "$BASE_SHA" --head HEAD --exclude-file scripts/quality_black_debt_allowlist.txt --print0 | xargs -0 -r ./venv/bin/black --check`
  - Files: `scripts/quality_black_debt_allowlist.txt`, `src/application/*`, `.github/workflows/ci.yml`
  - Docs: `docs/manifest/11_ci.md`, `docs/manifest/09_runbook.md`
  - Alternatives: keep current phased debt baseline unchanged.

- [x] Outcome: observability threshold calibration and triage guidance are tightened for degraded/error hotspots.
  - AC: threshold rationale and operator triage sequence are updated with current baseline evidence.
  - Verify:
    - `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json`
    - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500`
    - `python3 scripts/observability_cli.py summary --events-limit 500 --alerts-limit 500`
    - `./venv/bin/python -m pytest tests/unit/infrastructure/test_telemetry_backend.py -q`
    - `rg -n "4000ms|8000ms|CMD-036|calibration|threshold|sev2|sev3|triage|CMD-024|CMD-029" docs/manifest/07_observability.md docs/troubleshooting.md docs/manifest/09_runbook.md`
  - Files: `src/telemetry.py` (if thresholds change), `scripts/observability_cli.py` (if UX/query changes)
  - Docs: `docs/manifest/07_observability.md`, `docs/troubleshooting.md`, `docs/manifest/09_runbook.md`
  - Alternatives: keep current threshold baselines and triage flow unchanged.

- [x] Outcome: optional live-network rehearsal policy is explicit and repeatable without destabilizing default CI.
  - AC: network-dependent tests remain gated by default and documented with a bounded manual rehearsal cadence.
  - Verify:
    - `./venv/bin/python -m pytest -m integration -q`
    - `RUN_NETWORK_TESTS=1 RUN_NETWORK_REHEARSAL_MAX_ATTEMPTS=1 RUN_NETWORK_REHEARSAL_TIMEOUT_SECONDS=45 ./venv/bin/python -m pytest tests/integration/iplan/test_pydoll_live_mavat_documents__optional.py -q`
    - `rg -n "RUN_NETWORK_TESTS|RUN_NETWORK_ALLOW_CI|RUN_NETWORK_REHEARSAL_MAX_ATTEMPTS|CMD-037|bounded|cadence" tests/integration/iplan/test_pydoll_live_mavat_documents__optional.py docs/troubleshooting.md docs/manifest/10_testing.md docs/manifest/09_runbook.md`
  - Files: `tests/integration/iplan/test_pydoll_live_mavat_documents__optional.py`
  - Docs: `docs/troubleshooting.md`, `docs/manifest/10_testing.md`, `docs/manifest/09_runbook.md`
  - Alternatives: keep current ad-hoc network rehearsal behavior.

## M8 - Post-M7 Operational Discipline Bets (Completed)
- [x] Outcome: threshold recalibration cadence policy is explicit and command-map aligned.
  - AC: docs define periodic and trigger-based `CMD-036` recalibration flow with evidence recording expectations.
  - Verify:
    - `rg -n "CMD-036|cadence|weekly|trigger|recalibration" docs/manifest/07_observability.md docs/manifest/09_runbook.md docs/troubleshooting.md`
    - `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json`
    - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500`
  - Files: `docs/manifest/07_observability.md`, `docs/manifest/09_runbook.md`, `docs/troubleshooting.md`
  - Docs: `docs/implementation/checklists/03_improvement_bets.md`, `docs/implementation/reports/improvement_directions.md`
  - Alternatives: keep threshold calibration as ad-hoc operator judgment.

- [x] Outcome: formatting debt burn phase 4 migrates another bounded module group into always-enforced format surfaces.
  - AC: allowlist baseline decreases below current `77` and migrated files are removed from debt allowlist.
  - Verify:
    - `./venv/bin/black src/data_management/__init__.py src/data_management/data_store.py src/data_management/fetchers.py src/data_management/pydoll_fetcher.py`
    - `wc -l scripts/quality_black_debt_allowlist.txt`
    - `rg -n "^src/data_management/(__init__\\.py|data_store\\.py|fetchers\\.py|pydoll_fetcher\\.py)$" scripts/quality_black_debt_allowlist.txt` (no matches)
    - `BASE_SHA=$(git rev-parse HEAD~1) && python3 scripts/quality_changed_python.py --base "$BASE_SHA" --head HEAD --exclude-file scripts/quality_black_debt_allowlist.txt --print0 | xargs -0 -r ./venv/bin/black --check`
    - `rg -n "CMD-022|quality_black_debt_allowlist" .github/workflows/ci.yml docs/manifest/09_runbook.md docs/manifest/11_ci.md`
  - Files: `scripts/quality_black_debt_allowlist.txt`, `.github/workflows/ci.yml`, `src/data_management/*`
  - Docs: `docs/manifest/11_ci.md`, `docs/manifest/09_runbook.md`, `docs/implementation/checklists/03_improvement_bets.md`
  - Alternatives: keep current phased debt baseline unchanged.

- [x] Outcome: saturation snapshot discipline is explicit for build-window triage evidence.
  - AC: runbook/troubleshooting define a repeatable build-window snapshot drill and expected saturation fields.
  - Verify:
    - `(python3 scripts/build_vectordb_cli.py build --max-plans 1 --no-vision || true) && python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500`
    - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500`
    - `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json`
    - `rg -n "saturation_ratio_1m|memory_used_ratio|disk_free_ratio_cache_dir|build-window|snapshot" docs/manifest/07_observability.md docs/manifest/09_runbook.md docs/troubleshooting.md`
  - Files: `docs/manifest/07_observability.md`, `docs/manifest/09_runbook.md`, `docs/troubleshooting.md`, optional `scripts/observability_cli.py`
  - Docs: `docs/implementation/checklists/03_improvement_bets.md`, `docs/implementation/reports/improvement_directions.md`
  - Alternatives: rely on passive windows where saturation values may be absent.

## M9 - Post-M8 Evidence-Fit and Signal-Quality Bets
- [x] Outcome: artifact-feature alignment baseline is fully grounded with canonical artifact store metadata.
  - AC: alignment report/checklist exist with explicit verdict and matrix coverage; canonical artifact store exists with baseline load-bearing entries.
  - Verify:
    - `test -f docs/implementation/checklists/08_artifact_feature_alignment.md`
    - `test -f docs/implementation/reports/artifact_feature_alignment.md`
    - `test -f docs/artifacts/README.md && test -f docs/artifacts/index.json`
    - `rg -n "Artifact ID|Status \\(Supported/Partial/Missing/Misaligned\\)|ALIGNED|ALIGNED_WITH_GAPS|MISALIGNED" docs/implementation/reports/artifact_feature_alignment.md docs/implementation/checklists/08_artifact_feature_alignment.md`
    - `rg -n "ART-EXT-001|ART-EXT-002|ART-EXT-003|ART-EXT-004|ART-EXT-005" docs/artifacts/index.json`
  - Files: `docs/implementation/checklists/08_artifact_feature_alignment.md`, `docs/implementation/reports/artifact_feature_alignment.md`, `docs/artifacts/*`
  - Docs: `docs/implementation/00_status.md`, `docs/implementation/03_worklog.md`
  - Alternatives: keep artifact mapping report-only without canonical artifact metadata.

- [x] Outcome: iPlan/MAVAT external endpoint implications are mapped to explicit contract coverage and triage evidence.
  - AC: API contract docs, boundary tests, and troubleshooting guidance explicitly tie endpoint-family assumptions to verification surfaces.
  - Verify:
    - `rg -n "iPlan|MAVAT|endpoint|attachment|contract" docs/manifest/04_api_contracts.md docs/troubleshooting.md`
    - `./venv/bin/python -m pytest tests/integration/data_contracts/test_boundary_payload_contracts.py -q`
    - `./venv/bin/python -m pytest tests/integration/iplan/test_iplan_sample_data_quality.py -q`
    - `rg -n "CMD-034|CMD-035|CMD-037" docs/manifest/09_runbook.md`
  - Files: `docs/manifest/04_api_contracts.md`, `tests/integration/data_contracts/test_boundary_payload_contracts.py`, `tests/integration/iplan/test_iplan_sample_data_quality.py`, `docs/troubleshooting.md`
  - Docs: `docs/implementation/checklists/08_artifact_feature_alignment.md`, `docs/implementation/reports/artifact_feature_alignment.md`
  - Alternatives: keep endpoint-family mapping implicit across scattered docs/tests.

- [x] Outcome: load-bearing external dependency decisions and assumptions are artifact-cited (`COR-03`).
  - AC: decision, assumption, and observability guardrail docs reference stable artifact IDs (`ART-EXT-*`) for external dependency claims.
  - Verify:
    - `rg -n "ART-EXT-00[1-5]" docs/manifest/03_decisions.md docs/implementation/reports/assumptions_register.md docs/manifest/07_observability.md`
    - `rg -n "Artifact citations|Artifact Citations" docs/manifest/03_decisions.md docs/manifest/07_observability.md`
  - Files: `docs/manifest/03_decisions.md`, `docs/implementation/reports/assumptions_register.md`, `docs/manifest/07_observability.md`
  - Docs: `docs/implementation/checklists/08_artifact_feature_alignment.md`, `docs/implementation/reports/artifact_feature_alignment.md`
  - Alternatives: keep URL-only decision/assumption references without stable artifact IDs.

- [x] Outcome: saturation signal completeness for memory pressure is improved in build-window triage evidence.
  - AC: build-window snapshots provide actionable memory pressure context (or explicit availability semantics), and docs define interpretation.
  - Verify:
    - `(python3 scripts/build_vectordb_cli.py build --max-plans 1 --no-vision || true) && python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500`
    - `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json`
    - `./venv/bin/python -m pytest tests/unit/infrastructure/test_telemetry_backend.py tests/unit/infrastructure/test_observability_query.py tests/unit/vectorstore/test_unified_pipeline_saturation_snapshot.py -q`
    - `rg -n "memory_used_ratio|memory_used_ratio_source|memory_used_ratio_unavailable_reason|rss_mb|saturation_ratio_1m" src/vectorstore/unified_pipeline.py src/observability/query.py docs/manifest/07_observability.md docs/troubleshooting.md docs/manifest/09_runbook.md`
  - Files: `src/vectorstore/unified_pipeline.py`, `src/observability/query.py`, `scripts/observability_cli.py`
  - Docs: `docs/manifest/07_observability.md`, `docs/troubleshooting.md`, `docs/implementation/checklists/03_improvement_bets.md`
  - Alternatives: continue accepting partial saturation snapshots without stronger memory-context semantics.

- [x] Outcome: formatting debt burn phase 5 migrates a bounded infrastructure module batch into strict formatting enforcement.
  - AC: allowlist baseline decreases below `73`, selected infrastructure files are removed from debt allowlist, and `CMD-022` coverage expands accordingly.
  - Verify:
    - `./venv/bin/black src/infrastructure/__init__.py src/infrastructure/factory.py src/infrastructure/repositories/chroma_repository.py src/infrastructure/services/cache_service.py src/infrastructure/services/document_service.py src/infrastructure/services/llm_service.py src/infrastructure/services/vision_service.py`
    - `wc -l scripts/quality_black_debt_allowlist.txt`
    - `rg -n "^src/infrastructure/(__init__\\.py|factory\\.py|repositories/chroma_repository\\.py|services/cache_service\\.py|services/document_service\\.py|services/llm_service\\.py|services/vision_service\\.py)$" scripts/quality_black_debt_allowlist.txt` (no matches)
    - `rg -n "src/infrastructure/__init__\\.py|src/infrastructure/factory\\.py|src/infrastructure/repositories/chroma_repository\\.py|src/infrastructure/repositories/iplan_repository\\.py|src/infrastructure/services/cache_service\\.py|src/infrastructure/services/document_service\\.py|src/infrastructure/services/llm_service\\.py|src/infrastructure/services/vision_service\\.py|CMD-022" .github/workflows/ci.yml docs/manifest/09_runbook.md docs/manifest/11_ci.md`
  - Files: `scripts/quality_black_debt_allowlist.txt`, `.github/workflows/ci.yml`, `src/infrastructure/*`
  - Docs: `docs/manifest/09_runbook.md`, `docs/manifest/11_ci.md`, `docs/implementation/checklists/03_improvement_bets.md`
  - Alternatives: keep phased debt baseline unchanged.

- [x] Outcome: artifact freshness cadence ownership and audit command policy are explicit (`OPP-01`).
  - AC: artifact freshness owner model, cadence policy, and canonical audit command are documented and linked in command map.
  - Verify:
    - `rg -n "Refresh Cadence Policy|Primary owner|Logging requirements|CMD-039" docs/artifacts/README.md docs/manifest/09_runbook.md`
    - `python3 -c "import json,datetime,pathlib; items=json.loads(pathlib.Path('docs/artifacts/index.json').read_text(encoding='utf-8')).get('artifacts', []); cutoff=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=30)).isoformat(); stale=[i.get('id','unknown') for i in items if (not isinstance(i.get('retrieved_at'), str)) or (i.get('retrieved_at') < cutoff)]; print(f'artifacts_total={len(items)} stale_total={len(stale)}'); print('stale_ids=' + ','.join(stale) if stale else 'stale_ids=')"`
  - Files: `docs/artifacts/README.md`, `docs/artifacts/index.json`, `docs/manifest/09_runbook.md`
  - Docs: `docs/implementation/checklists/08_artifact_feature_alignment.md`, `docs/implementation/reports/artifact_feature_alignment.md`, `docs/manifest/03_decisions.md`
  - Alternatives: keep artifact freshness policy implicit and worklog-only.

- [x] Outcome: recurring evidence cadence captures are centralized in one canonical ledger surface (`IMP-19`).
  - AC: recurring `CMD-036` + `CMD-029` + `CMD-038` (+ `CMD-039`) evidence is checklisted and auditable in a single canonical file.
  - Verify:
    - `test -f docs/implementation/checklists/09_evidence_cadence_ledger.md`
    - `rg -n "CMD-036|CMD-029|CMD-038|CMD-039|IMP-19 bootstrap entry" docs/implementation/checklists/09_evidence_cadence_ledger.md docs/manifest/09_runbook.md docs/manifest/07_observability.md`
    - `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json`
    - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500`
    - `(python3 scripts/build_vectordb_cli.py build --max-plans 1 --no-vision || true) && python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500`
  - Files: `docs/implementation/checklists/09_evidence_cadence_ledger.md`, `docs/manifest/09_runbook.md`, `docs/manifest/07_observability.md`
  - Docs: `docs/implementation/00_status.md`, `docs/implementation/03_worklog.md`, `docs/manifest/03_decisions.md`
  - Alternatives: keep cadence evidence distributed across ad-hoc packet and worklog notes.

- [x] Outcome: external dependency health snapshot bundle is available via one canonical command path (`OPP-02`).
  - AC: one reproducible command summarizes iPlan/MAVAT/provider boundary status and deterministic drill outcomes for local triage.
  - Verify:
    - `python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills`
    - `./venv/bin/python -m pytest tests/unit/scripts/test_quick_status_external_snapshot.py -q`
    - `rg -n "CMD-040|external --since-minutes|snapshot bundle" scripts/quick_status.py docs/manifest/09_runbook.md docs/troubleshooting.md docs/reference/cli.md`
    - `./venv/bin/python -m pytest tests/integration/iplan/test_external_dependency_drills.py -q`
    - `./venv/bin/python -m pytest tests/integration/data_contracts/test_boundary_payload_contracts.py tests/integration/iplan/test_iplan_sample_data_quality.py -q`
  - Files: `scripts/quick_status.py`, `docs/manifest/09_runbook.md`, `docs/troubleshooting.md`
  - Docs: `docs/implementation/checklists/08_artifact_feature_alignment.md`, `docs/implementation/reports/artifact_feature_alignment.md`, `docs/manifest/03_decisions.md`
  - Alternatives: keep external boundary triage as multi-command manual flow only.

- [x] Outcome: onboarding docs include artifact-linked boundary notes for external provider/runtime assumptions (`OPP-03`).
  - AC: onboarding/reference docs map iPlan/MAVAT/Gemini/pydoll/Chroma claims to `ART-EXT-*` IDs.
  - Verify:
    - `rg -n "artifact:ART-EXT-001|artifact:ART-EXT-002|artifact:ART-EXT-003|artifact:ART-EXT-004|artifact:ART-EXT-005" docs/README.md docs/INDEX.md docs/reference/configuration.md docs/artifacts/README.md`
    - `rg -n "External dependency boundaries|External Boundary Artifacts|Boundary Onboarding Map" docs/README.md docs/INDEX.md docs/reference/configuration.md docs/artifacts/README.md`
  - Files: `docs/README.md`, `docs/INDEX.md`, `docs/reference/configuration.md`, `docs/artifacts/README.md`
  - Docs: `docs/implementation/checklists/08_artifact_feature_alignment.md`, `docs/implementation/reports/artifact_feature_alignment.md`, `docs/manifest/03_decisions.md`
  - Alternatives: keep onboarding boundary assumptions implicit and scattered across manifest docs.

- [x] Outcome: `CMD-040` warning interpretation and cadence capture policy are explicit and command-map enforced.
  - AC: external snapshot warnings include context-specific guidance and cadence ledger template requires recurring `CMD-040` evidence capture.
  - Verify:
    - `./venv/bin/python -m pytest tests/unit/scripts/test_quick_status_external_snapshot.py -q`
    - `./venv/bin/ruff check scripts/quick_status.py tests/unit/scripts/test_quick_status_external_snapshot.py --select E9,F63,F7`
    - `python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills`
    - `rg -n "warning_context|CMD-040 Snapshot Cadence|CMD-040|Canonical command bundle" scripts/quick_status.py docs/manifest/09_runbook.md docs/manifest/07_observability.md docs/troubleshooting.md docs/implementation/checklists/09_evidence_cadence_ledger.md docs/reference/cli.md`
  - Files: `scripts/quick_status.py`, `tests/unit/scripts/test_quick_status_external_snapshot.py`
  - Docs: `docs/implementation/checklists/09_evidence_cadence_ledger.md`, `docs/manifest/09_runbook.md`, `docs/manifest/07_observability.md`, `docs/troubleshooting.md`, `docs/reference/cli.md`, `docs/manifest/03_decisions.md`
  - Alternatives: keep coarse warning semantics and non-enforced cadence capture discipline.

## M10 - Post-CMD-040 Guardrail and Signal-Fit Follow-through
- [x] Outcome: onboarding/reference artifact-link citation guardrail is command-map enforced (`CMD-041`).
  - AC: one canonical command fails when required `artifact:ART-EXT-*` citations are missing from onboarding/reference boundary docs.
  - Verify:
    - `for file in docs/README.md docs/INDEX.md docs/reference/configuration.md docs/artifacts/README.md; do for id in artifact:ART-EXT-001 artifact:ART-EXT-002 artifact:ART-EXT-003 artifact:ART-EXT-004 artifact:ART-EXT-005; do rg -q "$id" "$file" || { echo "$file missing $id"; exit 1; }; done; done; echo "onboarding_artifact_links_ok files=4 ids=5"`
    - `rg -n "CMD-041|artifact-link guardrail|citation guardrail" docs/manifest/09_runbook.md docs/reference/cli.md docs/README.md docs/INDEX.md docs/manifest/03_decisions.md`
  - Files: `docs/manifest/09_runbook.md`, `docs/reference/cli.md`, `docs/README.md`, `docs/INDEX.md`
  - Docs: `docs/manifest/03_decisions.md`
  - Alternatives: keep ad-hoc `rg` checks in packet notes only.

- [x] Outcome: historical-noise warning handling requires narrowed-window confirmation logging before escalation.
  - AC: ledger template and runbook/troubleshooting guidance explicitly require narrowed-window `CMD-040` rerun evidence plus `CMD-025`/`CMD-028` inspection when `warning_context=historical_runtime_window_noise`.
  - Verify:
    - `rg -n "historical_runtime_window_noise|narrowed-window|CMD-025|CMD-028" docs/implementation/checklists/09_evidence_cadence_ledger.md docs/manifest/09_runbook.md docs/troubleshooting.md`
    - `python3 scripts/quick_status.py external --since-minutes 60 --events-limit 1000 --alerts-limit 500 --run-drills`
    - `python3 scripts/observability_cli.py alerts --since-minutes 60 --limit 50`
    - `python3 scripts/observability_cli.py events --outcome error --since-minutes 60 --limit 100`
  - Files: `docs/implementation/checklists/09_evidence_cadence_ledger.md`, `docs/manifest/09_runbook.md`, `docs/troubleshooting.md`
  - Docs: `docs/implementation/checklists/07_alignment_review.md`, `docs/implementation/reports/alignment_review.md`
  - Alternatives: keep narrowed-window confirmation as optional operator judgment.

- [x] Outcome: warning-context follow-up rendering has regression coverage for non-boundary warning scenarios.
  - AC: unit tests assert snapshot warning follow-up text for non-boundary warning branches in rendered snapshot output.
  - Verify:
    - `./venv/bin/python -m pytest tests/unit/scripts/test_quick_status_external_snapshot.py -q`
    - `rg -n "warning_context|follow-up|historical_runtime_window_noise|runtime_errors_or_alerts_unconfirmed" tests/unit/scripts/test_quick_status_external_snapshot.py scripts/quick_status.py`
  - Files: `tests/unit/scripts/test_quick_status_external_snapshot.py`, optional `scripts/quick_status.py`
  - Docs: `docs/implementation/checklists/07_alignment_review.md`, `docs/implementation/reports/alignment_review.md`
  - Alternatives: rely only on manual `CMD-040` output inspection.

- [x] Outcome: `CMD-040` operator output is free of pydantic namespace startup warning noise.
  - AC: running `CMD-040` no longer emits `protected namespace` warnings before the snapshot report.
  - Verify:
    - `python3 scripts/quick_status.py external --since-minutes 60 --events-limit 200 --alerts-limit 200 --run-drills 2>&1 | rg -n "protected namespace|UserWarning"` (no matches)
    - `./venv/bin/python -m pytest tests/unit/scripts/test_quick_status_external_snapshot.py -q`
    - `./venv/bin/black --check src/config.py tests/unit/scripts/test_quick_status_external_snapshot.py`
  - Files: `src/config.py`, `tests/unit/scripts/test_quick_status_external_snapshot.py`
  - Docs: `docs/implementation/checklists/07_alignment_review.md`, `docs/implementation/reports/alignment_review.md`
  - Alternatives: suppress warnings in command wrappers instead of fixing settings configuration.

## M11 - Release Readiness Guardrail Wiring
- [x] Outcome: release-readiness packet explicitly requires `CMD-041` onboarding citation guardrail verification.
  - AC: release checklist and release-workflow reference include a blocking `CMD-041` verification step.
  - Verify:
    - `rg -n "CMD-041|onboarding artifact-link|citation guardrail" docs/implementation/checklists/06_release_readiness.md docs/reference/release_workflow.md docs/manifest/09_runbook.md`
    - `for file in docs/README.md docs/INDEX.md docs/reference/configuration.md docs/artifacts/README.md; do for id in artifact:ART-EXT-001 artifact:ART-EXT-002 artifact:ART-EXT-003 artifact:ART-EXT-004 artifact:ART-EXT-005; do rg -q "$id" "$file" || { echo "$file missing $id"; exit 1; }; done; done; echo "onboarding_artifact_links_ok files=4 ids=5"`
  - Files: `docs/implementation/checklists/06_release_readiness.md`, `docs/reference/release_workflow.md`
  - Docs: `docs/implementation/checklists/07_alignment_review.md`, `docs/implementation/reports/alignment_review.md`
  - Alternatives: keep `CMD-041` guardrail in runbook only and rely on contributor memory at release time.

## M12 - Post-Release-Wiring Reliability Follow-through
- [x] Outcome: release workflow validation job enforces `CMD-041` citation guardrail automatically.
  - AC: `.github/workflows/release.yml` runs the `CMD-041` guardrail in `release-validation` before publish steps.
  - Verify:
    - `rg -n "CMD-041|artifact:ART-EXT-001|onboarding_artifact_links_ok" .github/workflows/release.yml docs/reference/release_workflow.md docs/manifest/11_ci.md`
    - `for file in docs/README.md docs/INDEX.md docs/reference/configuration.md docs/artifacts/README.md; do for id in artifact:ART-EXT-001 artifact:ART-EXT-002 artifact:ART-EXT-003 artifact:ART-EXT-004 artifact:ART-EXT-005; do rg -q "$id" "$file" || { echo "$file missing $id"; exit 1; }; done; done; echo "onboarding_artifact_links_ok files=4 ids=5"`
  - Files: `.github/workflows/release.yml`
  - Docs: `docs/reference/release_workflow.md`, `docs/manifest/11_ci.md`
  - Alternatives: keep `CMD-041` as manual pre-tag check only.

- [x] Outcome: recurring build timeout noise is distinguished from boundary degradation in first-pass operator flow.
  - AC: `CMD-040` warning semantics explicitly separate recurring build-timeout sev1 noise from boundary-degraded escalation and document narrowed-window follow-up commands.
  - Verify:
    - `python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills`
    - `python3 scripts/observability_cli.py alerts --since-minutes 180 --limit 100`
    - `rg -n "historical_build_timeout_sev1_noise|warning_noise_profile|build timeout|sev1|CMD-040|CMD-026|CMD-028" scripts/quick_status.py docs/troubleshooting.md docs/manifest/07_observability.md docs/manifest/09_runbook.md docs/reference/cli.md`
  - Files: `scripts/quick_status.py`, optional `src/telemetry.py`
  - Docs: `docs/troubleshooting.md`, `docs/manifest/07_observability.md`, `docs/manifest/09_runbook.md`
  - Alternatives: keep existing warning context handling without further timeout-noise differentiation.

- [x] Outcome: post-M12 reranking uses an explicit convergence guardrail to prevent repetitive low-impact routing loops.
  - AC: improvement-direction rerank notes include a repeat-loop stop condition and unresolved-outcome delta check before selecting the same immediate route again.
  - Verify:
    - `rg -n "convergence guardrail|repeat-loop|unresolved-outcome delta|IMP-22" docs/implementation/reports/improvement_directions.md docs/implementation/checklists/03_improvement_bets.md docs/implementation/checklists/02_milestones.md`
    - `rg -n "Recommended immediate next prompt" docs/implementation/reports/improvement_directions.md`
  - Files: `docs/implementation/reports/improvement_directions.md`
  - Docs: `docs/implementation/checklists/03_improvement_bets.md`, `docs/implementation/checklists/07_alignment_review.md`, `docs/implementation/reports/alignment_review.md`
  - Alternatives: continue ad-hoc reranking without explicit convergence stop conditions.

## M13 - Planner UX Redesign and Frontend Systemization
- [x] Outcome: planner-first route redesign ships without changing the current route or backend API contract.
  - AC: `/`, `/map`, `/analyzer`, and `/data` remain intact while the shell and route composition shift to Workspace / Investigation / Feasibility / Operations.
  - Verify:
    - `cd frontend && npm run build`
    - `cd frontend && npm run test:e2e`
  - Files: `frontend/src/App.tsx`, `frontend/src/AppRedesign.tsx`, `frontend/src/main.tsx`, `frontend/src/styles.redesign.css`
  - Docs: `docs/implementation/reports/dashboard_ux_audit_redesign.md`, `docs/implementation/checklists/10_dashboard_redesign.md`
  - Alternatives: deeper route restructure or backend contract changes.

- [x] Outcome: implementation-aware UX audit and redesign handoff are recorded in dedicated packet artifacts.
  - AC: a single report uses the requested 17-section structure and a paired checklist tracks acceptance and verification.
  - Verify:
    - `test -f docs/implementation/reports/dashboard_ux_audit_redesign.md`
    - `test -f docs/implementation/checklists/10_dashboard_redesign.md`
    - `rg -n "^# [0-9]+\\." docs/implementation/reports/dashboard_ux_audit_redesign.md`
  - Files: `docs/implementation/reports/dashboard_ux_audit_redesign.md`, `docs/implementation/checklists/10_dashboard_redesign.md`
  - Docs: `docs/implementation/00_status.md`, `docs/implementation/03_worklog.md`
  - Alternatives: split the audit, redesign, and handoff across separate ad-hoc notes.

- [x] Outcome: Figma capture file contains current-state and redesigned route frames for review and implementation handoff.
  - AC: the file `GISArchAgent - Planner UX Redesign` exists and includes both baseline evidence captures and redesigned route captures.
  - Verify:
    - open `https://www.figma.com/design/d6ExX1CAGJtmV6HzA1j73D` and confirm current-state, redesign, and handoff frames are present
  - Files: Figma file `GISArchAgent - Planner UX Redesign`
  - Docs: `docs/implementation/00_status.md`, `docs/implementation/03_worklog.md`, `docs/implementation/checklists/10_dashboard_redesign.md`
  - Alternatives: keep evidence only in markdown and local screenshots.
