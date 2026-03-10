# Observability and Reliability

## Current State
- Structured observability events are emitted as JSON log lines (`OBS_EVENT`) in critical paths:
  - `RegulationQueryService.query()`
  - `PlanSearchService.search_plans()`
  - `UnifiedDataPipeline.run_async()`
- Degraded external dependency outcomes are now explicit and machine-queryable:
  - `RegulationQueryService` emits `outcome=degraded` with `degraded_reasons=["llm_synthesis_unavailable"]` when Gemini synthesis fails and deterministic fallback is used.
  - `PlanSearchService` emits `outcome=degraded` with explicit `degraded_reasons` for iPlan boundary failures and vision dependency degradation.
- A local observability backend sink is now implemented via JSONL files:
  - `data/cache/observability/events_backend.jsonl` (all structured events)
  - `data/cache/observability/alerts.jsonl` (routed alerts)
- Operator query UX is available via CLI:
  - `python3 scripts/observability_cli.py summary`
  - `python3 scripts/observability_cli.py events ...`
  - `python3 scripts/observability_cli.py alerts ...`
  - `python3 scripts/observability_cli.py dashboard ...`
- Correlation tokens are now present:
  - per-request `request_id` in query/search workflows
  - per-run `run_id` in vector build workflow
- Build workflow metrics are persisted to:
  - `data/cache/pipeline_stats.json`
  - `data/cache/observability/workflow_metrics.jsonl`
- CI enforces core marker suites and prompt-pack integrity (`.github/workflows/ci.yml`).
- Release-tag automation enforces the same verification set before publish (`.github/workflows/release.yml`).

## Critical Workflows
1. Regulation query flow (`app.py` -> `RegulationQueryService` -> Chroma repository).
2. Plan search flow (`app.py`/pages -> `PlanSearchService` -> iPlan repository -> optional vision).
3. Vector DB build flow (`scripts/build_vectordb_cli.py` -> unified pipeline -> Chroma persistence).

## Log Schema (Implemented)
Structured events include:
- `timestamp`
- `level`
- `component`
- `operation`
- `request_id`
- `outcome` (`start`/`success`/`degraded`/`error`)
- optional: `error_class`, `message`, `latency_ms`, and workflow counters
- optional (build saturation/resource): `saturation_ratio_1m`, `load_1m`, `cpu_count`, `rss_mb`, `memory_used_ratio`, `memory_used_ratio_source`, `memory_used_ratio_unavailable_reason`, `disk_free_ratio_cache_dir`, `disk_free_mb_cache_dir`

Implementation evidence:
- `src/telemetry.py`
- `src/application/services/regulation_query_service.py`
- `src/application/services/plan_search_service.py`
- `src/vectorstore/unified_pipeline.py`

### Redaction Policy
- No API keys/secrets are logged.
- Query text is not logged verbatim in observability events; only bounded metadata (for example `query_length`).
- Large/raw documents are not emitted in structured events.

## Metrics and Tracing
### Metrics (implemented/partial)
- Query/search latency and outcome are emitted per request event.
- Build workflow counters and duration are persisted per run in `workflow_metrics.jsonl`.
- Build workflow saturation/resource signals include:
  - `saturation_ratio_1m` and `load_1m` (load vs CPU capacity)
  - `memory_used_ratio` and `rss_mb` (process/host memory pressure hints)
  - `memory_used_ratio_source` and `memory_used_ratio_unavailable_reason` (probe provenance and explicit fallback semantics when memory ratio is absent)
  - `disk_free_ratio_cache_dir` and `disk_free_mb_cache_dir` (cache path disk pressure)
- Pipeline totals are persisted in `pipeline_stats.json`.

### Tracing (implemented/partial)
- Request/run correlation is available via `request_id` across start/success/error events.
- Build pipeline run correlation is available via `run_id`.

## External Dependency Guardrails (Implemented Baseline)
- iPlan boundary error signals:
  - `IPlanGISRepository` records structured boundary error metadata (`operation`, `error_class`, `message`, `timestamp`) and exposes it via `consume_last_error()`.
  - `PlanSearchService` consumes that signal and emits degraded reasons such as:
    - `iplan_search_by_location_failed`
    - `iplan_search_by_keyword_failed`
    - `iplan_search_by_status_failed`
    - `iplan_get_by_id_failed`
    - `iplan_get_plan_image_failed`
- Gemini/vision degradation signals:
  - `RegulationQueryService` falls back to deterministic answer generation when LLM synthesis fails and emits degraded telemetry.
  - `PlanSearchService` emits degraded reasons for:
    - `vision_service_unavailable`
    - `vision_analysis_unavailable`
    - `plan_analysis_exception`
- Deterministic tests:
  - `tests/unit/application/test_external_dependency_degraded_modes.py`
  - `tests/unit/infrastructure/test_iplan_repository_error_signal.py`
  - `tests/integration/iplan/test_external_dependency_drills.py` (non-network service+repository drill path)

### Artifact Citations (COR-03)
- iPlan boundary assumptions and degraded reasons: `ART-EXT-001`.
- MAVAT attachment/live endpoint behavior assumptions: `ART-EXT-002`.
- Gemini degraded fallback assumptions: `ART-EXT-003`.
- pydoll/browser runtime dependency assumptions: `ART-EXT-004`.
- Local Chroma persistence boundary assumptions: `ART-EXT-005`.

## Golden Signals Snapshot
- `latency`: available in query/search/build events (`latency_ms` / run duration).
- `traffic`: available via request/run event counts.
- `errors`: available via `outcome=error` and `error_class`.
- `saturation`: available for build workflow via load/memory/disk resource signals.

## SLI / SLO Targets (Initial)
- Query flow availability (non-crash response): >= 99% for local runs over a release cycle.
- Query latency p95 (local baseline): <= 3s without external LLM synthesis.
- Vector DB build success ratio: >= 95% of scheduled/manual runs complete without fatal crash.
- Test reliability: marker suites pass in CI/local with no flaky rerun requirement for stable paths.

## Alert Thresholds and Severity Routing (Implemented Baseline)
- Routing sinks:
  - `events_backend.jsonl` for full event stream.
  - `alerts.jsonl` for thresholded routed alerts.
- Severity and route mapping:
  - `sev1` -> `maintainer-oncall`
  - `sev2` -> `maintainer-primary`
  - `sev3` -> `maintainer`
- Trigger rules (current baseline):
  - `outcome=error` -> `sev1`
  - `outcome=degraded` -> `sev2`
  - latency thresholds:
    - `regulation_query`: `sev3 >= 4000ms`, `sev2 >= 8000ms`
    - `plan_search`: `sev3 >= 5000ms`, `sev2 >= 10000ms`
    - `build`: `sev3 >= 120000ms`, `sev2 >= 300000ms`
  - saturation thresholds (`saturation_ratio_1m`):
    - `sev3 >= 1.0`
    - `sev2 >= 1.25`
  - memory pressure thresholds (`memory_used_ratio`):
    - `sev3 >= 0.90`
    - `sev2 >= 0.95`
  - disk pressure thresholds (`disk_free_ratio_cache_dir`):
    - `sev3 <= 0.20`
    - `sev2 <= 0.10`

### Calibration Snapshot (2026-02-09)
- Evidence window (`CMD-036`):
  - `events_total=222`, `alerts_total=16`
  - `regulation_query` latency `p95=3453.42ms`
  - prior threshold (`sev3 >= 3000ms`) produced high low-signal sev3 volume.
- Calibration decision:
  - raise `regulation_query` latency thresholds to:
    - `sev3 >= 4000ms`
    - `sev2 >= 8000ms`
- Expected effect:
  - preserve severe outlier detection while reducing alert noise for routine p90-p95 latency fluctuations.

### Threshold Recalibration Cadence Policy (2026-02-09)
- Canonical command: `CMD-036`.
- Recalibration cadence:
  - run at least once every 7 days during active development.
  - run after incident windows where sev2/sev3 alert mix diverges from observed latency behavior.
  - run after threshold or observability payload changes (for example updates in `src/telemetry.py`, `src/observability/query.py`, or alert-routing docs).
- Recalibration triggers (execute outside weekly cadence when any trigger occurs):
  - sev3 alert volume is persistently high but p95 latency remains below sev3 threshold.
  - sev2 latency spikes recur across two or more consecutive windows.
  - operator triage identifies threshold mismatch between dashboard signal and incident severity.
- Recording requirements:
  - capture `CMD-036` JSON snapshot and `CMD-029` dashboard output in `docs/implementation/checklists/09_evidence_cadence_ledger.md`.
  - for external-dependency-sensitive windows, also capture `CMD-040` in the same ledger entry.
  - document threshold change/no-change decision and rationale in `docs/manifest/03_decisions.md`.
  - update troubleshooting/runbook guidance when trigger logic or cadence changes.

### External Snapshot Warning Interpretation Policy (2026-02-09)
- Canonical command: `CMD-040`.
- When `status=WARNING`, interpretation must use `warning_context` from snapshot output:
  - `boundary_degraded_signals_present`:
    - treat as boundary-risk warning.
    - escalate with `CMD-035` and `CMD-027`/`CMD-028`.
  - `historical_build_timeout_sev1_noise`:
    - deterministic drills passed, degraded reasons are zero, and warning signals are dominated by recurring `build` timeout sev1 records.
    - treat as non-boundary first-pass warning noise.
    - rerun `CMD-040` with narrower `--since-minutes` and inspect `CMD-026`/`CMD-028` before escalation.
  - `historical_runtime_window_noise`:
    - deterministic drills passed and degraded reasons are zero.
    - treat as likely time-window noise (for example prior sev1/build errors in range).
    - rerun `CMD-040` with narrower `--since-minutes` and inspect `CMD-025`/`CMD-028` before escalation.
  - `runtime_errors_or_alerts_unconfirmed`:
    - runtime errors/sev1 exist without degraded reasons.
    - rerun `CMD-040 --run-drills` and inspect `CMD-028`.
- Snapshot output should include `warning_noise_profile` counters when warning windows are historical-noise-shaped so operator first pass can distinguish build-timeout dominance from mixed historical noise.
- Recording requirements:
  - recurring cadence ledger entries must include `CMD-040` status and `warning_context` for each dependency-boundary triage window.

### Build-Window Saturation Snapshot Discipline (2026-02-09)
- Canonical drill command: `CMD-038`.
- Purpose:
  - force a build-window observability sample so saturation fields are not inferred only from passive query windows.
  - collect build operation latency/outcome context and saturation fields in a single repeatable workflow.
- Drill flow:
  - run bounded build attempt: `python3 scripts/build_vectordb_cli.py build --max-plans 1 --no-vision`.
  - regardless of build success/failure, capture dashboard snapshot from the same window.
- Evidence requirements:
  - attach `CMD-038` output to `docs/implementation/checklists/09_evidence_cadence_ledger.md` for every saturation triage window.
  - confirm snapshot includes `build` operation plus saturation fields:
    - `saturation_ratio_1m`
    - `disk_free_ratio_cache_dir`
    - `rss_mb`
    - `memory_used_ratio` (if `None`, require explicit `memory_used_ratio_unavailable_reason` and inspect `memory_used_ratio_source`)
- Latest packet evidence (IMP-17):
  - build command ended with provider timeout (`HTTPError`) but still emitted structured `build` events/alerts.
  - dashboard snapshot captured `build` with:
    - `latency p95=44985.39ms`
    - `saturation_ratio_1m_p95=0.267`
    - `memory_used_ratio_p95=0.52`
    - `disk_free_ratio_cache_dir_p05=0.3177`
    - `rss_mb_p95=320.78`
    - `memory_signal_latest_source=memory_pressure_q`

## Debug Playbook (Canonical Command Map)
Use command IDs from `docs/manifest/09_runbook.md`:
- `CMD-008` vector DB status
- `CMD-009` vector DB build
- `CMD-003`..`CMD-007` test diagnostics
- `CMD-001`/`CMD-002` local setup and app startup
- `CMD-015` inspect build metrics sink
- `CMD-019` inspect observability backend event stream
- `CMD-020` inspect routed alerts stream
- `CMD-024` observability summary query
- `CMD-025` alerts query slice
- `CMD-026` events query slice
- `CMD-027` degraded event query slice
- `CMD-028` error event query slice
- `CMD-029` operator dashboard view
- `CMD-034` deterministic iPlan drill suite
- `CMD-035` full external dependency rehearsal bundle
- `CMD-036` threshold calibration snapshot (summary JSON)
- `CMD-037` bounded opt-in live-network rehearsal
- `CMD-038` build-window saturation snapshot drill
- `CMD-040` external dependency health snapshot bundle

## Backend Evolution Decision (Locked)
Decision reference: `ADR-0017` in `docs/manifest/03_decisions.md`.

- Current mode (explicit): keep local-only observability backend (`JSONL` sinks + CLI dashboard/query UX).
- Rationale:
  - current team/operator footprint is small and local-first workflows are the project objective baseline.
  - existing `CMD-024`..`CMD-029` triage path is sufficient for current latency/error/degraded diagnosis.
  - introducing hosted observability now would add operational overhead with low near-term ROI.
- Hosted backend promotion triggers (any trigger opens a bounded migration packet):
  1. sustained event volume exceeds local triage ergonomics (for example >50k events/week).
  2. multi-operator concurrent dashboard requirement becomes routine.
  3. incident MTTR indicates local-only tooling is a bottleneck.
  4. cross-host/run correlation requirements exceed local artifact constraints.
- Migration seam policy:
  - preserve event schema compatibility (`OBS_EVENT` + existing JSON fields) so a future hosted sink can be added without rewriting service emitters.
  - keep command-map parity; local CLI remains fallback even if hosted backend is added later.

## Remaining Gaps
- Local-only backend decision is locked for the current cycle; hosted backend is deferred behind explicit trigger criteria.
- Add browser-based dashboard/query UI on top of JSONL sinks (terminal dashboard path now exists via CLI).
- Continue applying recalibration cadence policy as runtime baselines evolve.
- Continue applying build-window saturation snapshot discipline (`CMD-038`) to avoid passive-window evidence gaps.
- Maintain recurring evidence entries in `docs/implementation/checklists/09_evidence_cadence_ledger.md`.
- Add network saturation/error-rate signals for long-running operations.
