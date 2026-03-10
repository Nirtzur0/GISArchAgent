# Runbook

## Command Map

| ID | Command | Purpose | Source Evidence |
| --- | --- | --- | --- |
| CMD-001 | `./setup.sh` | Create venv, install dependencies, prepare `.env`, initialize local data/vector baseline. | `setup.sh` |
| CMD-002 | `./run_webapp.sh` | Launch Streamlit application entrypoint. | `run_webapp.sh` |
| CMD-003 | `./venv/bin/python -m pytest` | Run full test suite. | `README.md`, `tests/README.md` |
| CMD-004 | `./venv/bin/python -m pytest -m unit` | Run unit tests only. | `README.md`, `tests/README.md`, `pytest.ini` |
| CMD-005 | `./venv/bin/python -m pytest -m integration` | Run integration tests only. | `tests/README.md`, `pytest.ini` |
| CMD-006 | `./venv/bin/python -m pytest -m e2e` | Run end-to-end smoke tests only. | `tests/README.md`, `pytest.ini` |
| CMD-007 | `./venv/bin/python -m pytest -m data_contracts` | Run data contract checks. | `tests/README.md`, `pytest.ini` |
| CMD-008 | `python3 scripts/quick_status.py` | Inspect vector DB health quickly. | `scripts/quick_status.py` |
| CMD-009 | `python3 scripts/build_vectordb_cli.py build --max-plans <N>` | Build/update vector database via unified pipeline. | `scripts/build_vectordb_cli.py`, `scripts/README.md` |
| CMD-010 | `python3 scripts/build_vectordb_cli.py status` | Vector DB status through CLI wrapper. | `scripts/build_vectordb_cli.py` |
| CMD-011 | `python3 scripts/build_vectordb_cli.py check` | Check prerequisites for pipeline execution. | `scripts/build_vectordb_cli.py` |
| CMD-012 | `python3 scripts/data_cli.py status -v` | Inspect local data-store statistics. | `scripts/data_cli.py`, `scripts/README.md` |
| CMD-013 | `python3 scripts/data_cli.py search --city "<city>"` | Query filtered planning records from local data store. | `scripts/data_cli.py`, `scripts/README.md` |
| CMD-014 | `python3 scripts/data_cli.py export <out>.json --pretty` | Export data-store subset for downstream use. | `scripts/data_cli.py`, `scripts/README.md` |
| CMD-015 | `test -f data/cache/observability/workflow_metrics.jsonl && tail -n 20 data/cache/observability/workflow_metrics.jsonl || echo "No workflow metrics yet"` | Inspect recent build workflow metrics records. | `src/vectorstore/unified_pipeline.py` |
| CMD-016 | `python3 project-prompts/scripts/prompts_manifest.py --check` | Validate prompt pack manifest consistency. | `project-prompts/scripts/prompts_manifest.py` |
| CMD-017 | `python3 project-prompts/scripts/system_integrity.py --mode prompt_pack --root project-prompts` | Validate prompt system integrity boundaries. | `project-prompts/scripts/system_integrity.py` |
| CMD-018 | `test -f CHANGELOG.md && test -f docs/implementation/checklists/06_release_readiness.md && test -f docs/reference/release_workflow.md` | Validate required release packet artifacts exist before tag workflow runs. | `.github/workflows/release.yml`, `docs/reference/release_workflow.md` |
| CMD-019 | `test -f data/cache/observability/events_backend.jsonl && tail -n 20 data/cache/observability/events_backend.jsonl || echo "No backend events yet"` | Inspect local observability backend event stream. | `src/telemetry.py` |
| CMD-020 | `test -f data/cache/observability/alerts.jsonl && tail -n 20 data/cache/observability/alerts.jsonl || echo "No routed alerts yet"` | Inspect routed alert stream and severity/owner mapping. | `src/telemetry.py` |
| CMD-021 | `./venv/bin/ruff check . --select E9,F63,F7 --exclude project-prompts` | Run repo-wide syntax/parse-focused lint gate while excluding prompt submodule surfaces. | `.github/workflows/ci.yml` |
| CMD-022 | `./venv/bin/black --check src/telemetry.py src/observability/query.py src/application/__init__.py src/application/dtos.py src/data_management/__init__.py src/data_management/data_store.py src/data_management/fetchers.py src/data_management/pydoll_fetcher.py src/application/services/building_rights_service.py src/application/services/plan_upload_service.py src/application/services/regulation_query_service.py src/application/services/plan_search_service.py src/infrastructure/__init__.py src/infrastructure/factory.py src/infrastructure/repositories/chroma_repository.py src/infrastructure/repositories/iplan_repository.py src/infrastructure/services/cache_service.py src/infrastructure/services/document_service.py src/infrastructure/services/llm_service.py src/infrastructure/services/vision_service.py src/vectorstore/unified_pipeline.py src/domain/__init__.py src/domain/entities/__init__.py src/domain/entities/analysis.py src/domain/entities/plan.py src/domain/entities/regulation.py src/domain/repositories/__init__.py src/domain/value_objects/__init__.py src/domain/value_objects/building_rights.py src/domain/value_objects/geometry.py tests/unit/infrastructure/test_telemetry_backend.py tests/unit/infrastructure/test_observability_query.py tests/unit/application/test_external_dependency_degraded_modes.py tests/unit/infrastructure/test_iplan_repository_error_signal.py scripts/observability_cli.py scripts/check_release_semantics.py` | Enforce formatting guard for actively maintained packet surfaces. | `.github/workflows/ci.yml` |
| CMD-023 | `./venv/bin/python scripts/check_release_semantics.py --tag vX.Y.Z --changelog CHANGELOG.md` | Validate release tag and changelog section coherence. | `.github/workflows/release.yml`, `scripts/check_release_semantics.py` |
| CMD-024 | `python3 scripts/observability_cli.py summary --events-limit 500 --alerts-limit 500` | Query local observability backend summary (events, alerts, latency p95, latest signals). | `scripts/observability_cli.py`, `src/observability/query.py` |
| CMD-025 | `python3 scripts/observability_cli.py alerts --since-minutes 60 --limit 50` | Query routed alerts stream with time window filters. | `scripts/observability_cli.py`, `src/observability/query.py` |
| CMD-026 | `python3 scripts/observability_cli.py events --operation build --since-minutes 60 --limit 50` | Query event stream for workflow-specific triage. | `scripts/observability_cli.py`, `src/observability/query.py` |
| CMD-027 | `python3 scripts/observability_cli.py events --outcome degraded --since-minutes 120 --limit 100` | Query degraded-mode events for external dependency triage. | `scripts/observability_cli.py`, `docs/troubleshooting.md` |
| CMD-028 | `python3 scripts/observability_cli.py events --outcome error --since-minutes 120 --limit 100` | Query hard error events and correlate with alert stream. | `scripts/observability_cli.py`, `docs/troubleshooting.md` |
| CMD-029 | `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` | Render an operator dashboard (operations, degraded reasons, saturation snapshot, alert severities). | `scripts/observability_cli.py`, `src/observability/query.py` |
| CMD-030 | `BASE_SHA=$(git rev-parse HEAD~1) && python3 scripts/quality_changed_python.py --base "$BASE_SHA" --head HEAD --exclude-file scripts/quality_black_debt_allowlist.txt --print0 | xargs -0 -r ./venv/bin/black --check` | Enforce formatting on changed non-allowlisted Python files (bounded debt-burn mode). | `scripts/quality_changed_python.py`, `scripts/quality_black_debt_allowlist.txt`, `.github/workflows/ci.yml` |
| CMD-031 | `wc -l scripts/quality_black_debt_allowlist.txt && sed -n '1,40p' scripts/quality_black_debt_allowlist.txt` | Inspect current formatting debt allowlist size and top entries. | `scripts/quality_black_debt_allowlist.txt` |
| CMD-032 | `./venv/bin/pip freeze --all | LC_ALL=C sort > requirements.lock && python3 scripts/check_dependency_sync.py --requirements requirements.txt --dev-requirements requirements-dev.txt --lock requirements.lock --doc docs/reference/dependencies.md --write-doc` | Regenerate deterministic lock artifact and refresh dependency inventory doc. | `requirements.lock`, `scripts/check_dependency_sync.py`, `docs/reference/dependencies.md` |
| CMD-033 | `python3 scripts/check_dependency_sync.py --requirements requirements.txt --dev-requirements requirements-dev.txt --lock requirements.lock --doc docs/reference/dependencies.md` | Validate lockfile coverage and dependency-doc synchronization. | `scripts/check_dependency_sync.py`, `.github/workflows/ci.yml` |
| CMD-034 | `./venv/bin/python -m pytest tests/integration/iplan/test_external_dependency_drills.py -q` | Run deterministic, non-network iPlan dependency drill suite (service + repository + telemetry sink path). | `tests/integration/iplan/test_external_dependency_drills.py` |
| CMD-035 | `./venv/bin/python -m pytest tests/unit/application/test_external_dependency_degraded_modes.py tests/unit/infrastructure/test_iplan_repository_error_signal.py tests/integration/iplan/test_external_dependency_drills.py -q` | Run full external dependency rehearsal bundle (unit + integration drills) before/after incident triage changes. | `tests/unit/application/test_external_dependency_degraded_modes.py`, `tests/unit/infrastructure/test_iplan_repository_error_signal.py`, `tests/integration/iplan/test_external_dependency_drills.py` |
| CMD-036 | `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json` | Capture observability threshold calibration snapshot (latency p95 + alert mix over the active triage window). | `scripts/observability_cli.py`, `src/observability/query.py` |
| CMD-037 | `RUN_NETWORK_TESTS=1 RUN_NETWORK_REHEARSAL_MAX_ATTEMPTS=2 RUN_NETWORK_REHEARSAL_TIMEOUT_SECONDS=45 ./venv/bin/python -m pytest tests/integration/iplan/test_pydoll_live_mavat_documents__optional.py -q` | Run bounded opt-in live-network MAVAT rehearsal (manual drill; keep out of default CI). | `tests/integration/iplan/test_pydoll_live_mavat_documents__optional.py`, `docs/manifest/10_testing.md`, `docs/troubleshooting.md` |
| CMD-038 | `(python3 scripts/build_vectordb_cli.py build --max-plans 1 --no-vision || true) && python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` | Capture build-window saturation snapshot evidence even when external provider calls fail; record build operation latency/outcome plus saturation fields for triage windows. | `scripts/build_vectordb_cli.py`, `scripts/observability_cli.py`, `src/vectorstore/unified_pipeline.py` |
| CMD-039 | `python3 -c "import json,datetime,pathlib; items=json.loads(pathlib.Path('docs/artifacts/index.json').read_text(encoding='utf-8')).get('artifacts', []); cutoff=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=30)).isoformat(); stale=[i.get('id','unknown') for i in items if (not isinstance(i.get('retrieved_at'), str)) or (i.get('retrieved_at') < cutoff)]; print(f'artifacts_total={len(items)} stale_total={len(stale)}'); print('stale_ids=' + ','.join(stale) if stale else 'stale_ids=')"` | Audit artifact freshness against 30-day staleness policy and produce stale-ID summary for recurring cadence ledger records. | `docs/artifacts/index.json`, `docs/artifacts/README.md`, `docs/implementation/checklists/09_evidence_cadence_ledger.md` |
| CMD-040 | `python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills` | One-shot external dependency health snapshot bundle (iPlan/MAVAT/Gemini boundary configuration, recent observability signals, deterministic drill outcomes, explicit `warning_context` semantics, and warning-noise profile counters for first-pass triage). | `scripts/quick_status.py`, `tests/unit/scripts/test_quick_status_external_snapshot.py`, `tests/integration/iplan/test_external_dependency_drills.py`, `docs/troubleshooting.md` |
| CMD-041 | `for file in docs/README.md docs/INDEX.md docs/reference/configuration.md docs/artifacts/README.md; do for id in artifact:ART-EXT-001 artifact:ART-EXT-002 artifact:ART-EXT-003 artifact:ART-EXT-004 artifact:ART-EXT-005; do rg -q "$id" "$file" || { echo "$file missing $id"; exit 1; }; done; done; echo "onboarding_artifact_links_ok files=4 ids=5"` | Guardrail check that onboarding/reference boundary docs still carry required `artifact:ART-EXT-*` citations. | `docs/README.md`, `docs/INDEX.md`, `docs/reference/configuration.md`, `docs/artifacts/README.md` |

## Incident Triage Quick Path
1. App not starting:
   - run `CMD-001`, then `CMD-002`.
2. Query/search quality or runtime failures:
   - run `CMD-004`, `CMD-005`, `CMD-006`, `CMD-007`.
3. Vector DB issues:
   - run `CMD-008`, then `CMD-009` or `CMD-010`.
4. Data-store integrity concerns:
   - run `CMD-012`, then targeted `CMD-013`/`CMD-014`.
5. Release packet validation:
   - run `CMD-018`, `CMD-041`, then `CMD-004`..`CMD-007`, `CMD-016`, `CMD-017`.
6. Observability and alert triage:
   - run `CMD-029` for dashboard view, then query slices with `CMD-024`..`CMD-028` as needed.
7. CI quality hardening checks:
   - run `CMD-021`, then `CMD-030`, review debt baseline via `CMD-031`, and use `CMD-022` as maintained-surface fallback.
8. Dependency reproducibility and drift checks:
   - run `CMD-032` after dependency updates and ensure `CMD-033` passes before merge.
9. Release tag/changelog semantics:
   - run `CMD-023` before pushing `v*` tags.
10. External dependency deterministic rehearsal:
   - run `CMD-040` for a single-command external boundary snapshot bundle.
   - run `CMD-035`, then inspect degraded/error slices with `CMD-027` and `CMD-028`.
11. Optional live-network rehearsal (manual, bounded):
   - run `CMD-037` when deterministic drills are green but real-provider behavior is still suspect.
   - in CI, allow this only in dedicated rehearsal jobs by also setting `RUN_NETWORK_ALLOW_CI=1`.
12. Observability threshold calibration:
   - run `CMD-036`, then verify threshold docs/triage guidance against current alert mix.
   - follow recalibration cadence: at least weekly plus incident/threshold-change triggers.
   - record snapshot evidence (`CMD-036` + `CMD-029` + `CMD-040` for dependency-sensitive windows) in `docs/implementation/checklists/09_evidence_cadence_ledger.md`.
   - record threshold change/no-change rationale in `docs/manifest/03_decisions.md`.
13. Build-window saturation snapshot discipline:
   - run `CMD-038` when saturation fields are sparse in passive windows.
   - verify dashboard/summary include build operation and saturation fields (`saturation_ratio_1m`, `disk_free_ratio_cache_dir`, `rss_mb`).
   - if `memory_used_ratio` is `None`, treat it as valid only when explicit probe semantics are present (`memory_used_ratio_source`, `memory_used_ratio_unavailable_reason`).
   - attach both command outputs to `docs/implementation/checklists/09_evidence_cadence_ledger.md` as canonical incident evidence.
14. Artifact freshness cadence discipline:
   - run `CMD-039` at least weekly during active development windows.
   - run immediately after endpoint/provider/runtime incidents or dependency boundary changes.
   - record owner, reviewed artifact IDs, stale IDs, and remediation/deferral decisions in `docs/implementation/checklists/09_evidence_cadence_ledger.md`.
15. External dependency health snapshot bundle:
   - use `CMD-040` as the canonical one-shot bundle before/after dependency incidents.
   - if `status=DEGRADED`, escalate to `CMD-035` and targeted `CMD-027`/`CMD-028` slices.
   - if `status=WARNING`, use `warning_context`:
     - `boundary_degraded_signals_present`: escalate with `CMD-035`, then `CMD-027`/`CMD-028`.
     - `historical_build_timeout_sev1_noise`: treat as recurring build-timeout noise first, rerun `CMD-040` with narrower window, then inspect `CMD-026`/`CMD-028` before escalation.
     - `historical_runtime_window_noise`: narrow `--since-minutes` and inspect `CMD-025`/`CMD-028` before escalation.
     - `runtime_errors_or_alerts_unconfirmed`: rerun `CMD-040 --run-drills` and inspect `CMD-028`.
16. Onboarding artifact-link guardrail:
   - run `CMD-041` after editing onboarding/reference boundary docs or `docs/artifacts/index.json`.
   - if the command fails, restore missing `artifact:ART-EXT-*` citations before merge.

## Operational Notes
- Prefer repo-pinned venv commands for consistency.
- Treat commands above as canonical IDs for CI mapping and checklist verification.
- Keep live-network rehearsal bounded and opt-in; do not add `CMD-037` to default PR/release gates.
- Use `CMD-038` as the canonical build-window saturation snapshot drill before changing saturation thresholds or concluding saturation regressions.
- Use `CMD-039` as the canonical artifact freshness audit before release readiness and after external-dependency incidents.
- Use `docs/implementation/checklists/09_evidence_cadence_ledger.md` as the canonical recurring evidence ledger for `CMD-036`/`CMD-029`/`CMD-038`/`CMD-039`/`CMD-040`.
- Use `CMD-040` as the canonical single-command external dependency boundary snapshot bundle.
- Use `CMD-041` as the canonical onboarding/reference artifact-link citation guardrail.
- Prompt routing is now prompt-first/manual via `project-prompts/prompt-00-prompt-routing-plan.md` (router script removed from latest prompt library).

## CMD-036 Recalibration Cadence
- Weekly cadence:
  - run `CMD-036` at least once every 7 days during active development windows.
- Trigger-based recalibration (run immediately):
  - persistent sev3 alert noise with p95 below sev3 threshold,
  - repeated sev2 latency spikes across consecutive windows,
  - threshold/payload changes in telemetry or alert-routing surfaces.
- Evidence discipline:
  - pair `CMD-036` with `CMD-029` dashboard output from the same window.
  - record each cadence run in `docs/implementation/checklists/09_evidence_cadence_ledger.md`.
  - record threshold change/no-change rationale in `docs/manifest/03_decisions.md`.

## CMD-040 Snapshot Cadence
- Weekly cadence:
  - run `CMD-040` at least once every 7 days during active development windows.
- Trigger-based cadence (run immediately):
  - after external provider/network incidents touching iPlan/MAVAT/Gemini paths,
  - after dependency/runtime changes affecting pydoll/browser or boundary adapters,
  - after observability triage windows where `status=WARNING` persisted without clear root cause.
- Evidence discipline:
  - record `status`, `warning_context` (if present), and deterministic drill outcome summary in `docs/implementation/checklists/09_evidence_cadence_ledger.md`.
  - when `warning_context=historical_runtime_window_noise`, capture narrowed-window confirmation before escalation:
    - rerun `CMD-040` with reduced `--since-minutes` (for example `60`),
    - capture `CMD-025`/`CMD-028` inspection commands for the narrowed window,
    - record both command results in the same ledger entry before deciding escalation.
  - when `warning_context=historical_build_timeout_sev1_noise`, capture narrowed-window confirmation before escalation:
    - rerun `CMD-040` with reduced `--since-minutes` (for example `60`),
    - capture `CMD-026` (`operation=build`) and `CMD-028` inspection commands for the narrowed window,
    - record both command results in the same ledger entry before deciding escalation.
