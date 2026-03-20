# Troubleshooting

## `ModuleNotFoundError: pydoll`
Likely cause:
- optional dependency not installed in current venv.

Fix:
```bash
./venv/bin/pip install pydoll-python
```

## Scraper status stays `unvalidated`
Likely causes:
- no bounded live scraper probe has been run in the current API process,
- the process restarted and the in-memory probe cache was cleared.

What changed:
- `/api/health`, `/api/system/status`, `/api/workspace/overview`, and `/api/operations/overview` are intentionally passive and will not launch a live probe on page load.
- dependency availability (`scraping.available`) is separate from probe success (`scraping.runtime_ready`).

Validation command:
```bash
curl -s "http://127.0.0.1:8001/api/data/fetcher-health?probe_limit=1&timeout_seconds=20"
```

What to expect:
- `status=ready` and `runtime_ready=true` after a successful bounded probe,
- `status=timeout|error|skipped|unavailable` with `detail`, `last_probe_at`, and `last_probe_duration_ms` when validation does not succeed,
- the passive health/overview endpoints reflect the latest cached probe result after this call.

## App fails to start after setup
Likely causes:
- incomplete dependency install,
- missing/invalid virtualenv activation.

Fix:
```bash
./setup.sh
./run_webapp.sh
```

## Dependency drift / inconsistent environments
Likely causes:
- `requirements.lock` is stale after dependency manifest edits,
- dependency inventory doc is out of sync with manifests/lock.

Fix:
```bash
# Regenerate deterministic lock + inventory doc
./venv/bin/pip freeze --all | LC_ALL=C sort > requirements.lock
python3 scripts/check_dependency_sync.py --requirements requirements.txt --dev-requirements requirements-dev.txt --lock requirements.lock --doc docs/reference/dependencies.md --write-doc

# Verify drift check passes
python3 scripts/check_dependency_sync.py --requirements requirements.txt --dev-requirements requirements-dev.txt --lock requirements.lock --doc docs/reference/dependencies.md
```

## Vector DB status is uninitialized
Likely cause:
- no persisted Chroma data yet.

Fix:
```bash
python3 scripts/build_vectordb_cli.py build --max-plans 10 --no-vision
python3 scripts/quick_status.py
```

## iPlan / Gemini degraded results
Likely causes:
- transient iPlan network/provider instability,
- Gemini model/API transient failures,
- missing Gemini configuration while `include_vision_analysis=True`.

Triage steps:
```bash
# 0) One-shot external boundary snapshot bundle (recommended first pass)
python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills

# 1) Confirm baseline health
./venv/bin/python -m pytest -m unit -q
./venv/bin/python -m pytest -m integration -q

# 2) Inspect structured event/alert streams
python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500
python3 scripts/observability_cli.py summary --events-limit 500 --alerts-limit 500
python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json
python3 scripts/observability_cli.py events --outcome degraded --since-minutes 120 --limit 100
python3 scripts/observability_cli.py events --outcome error --since-minutes 120 --limit 100
python3 scripts/observability_cli.py alerts --since-minutes 120 --limit 100

# 3) Run deterministic non-network dependency drills
./venv/bin/python -m pytest tests/integration/iplan/test_external_dependency_drills.py -q
./venv/bin/python -m pytest tests/unit/application/test_external_dependency_degraded_modes.py tests/unit/infrastructure/test_iplan_repository_error_signal.py tests/integration/iplan/test_external_dependency_drills.py -q
```

What to look for:
- Snapshot bundle verdict (`CMD-040`):
  - `DEGRADED`: one or more deterministic drill checks failed; escalate with `CMD-035` and targeted `CMD-027`/`CMD-028` slices.
  - `WARNING`: use `warning_context` from `CMD-040` output:
    - `boundary_degraded_signals_present`: degraded boundary reasons are present; escalate with `CMD-035` and targeted `CMD-027`/`CMD-028`.
    - `historical_build_timeout_sev1_noise`: deterministic drills passed and warning signals are dominated by recurring `build` timeout sev1 records; treat as non-boundary first-pass noise, rerun `CMD-040` with a narrower window, then inspect `CMD-026`/`CMD-028` before escalating.
    - `historical_runtime_window_noise`: deterministic drills passed and degraded reasons are zero; treat as likely window noise (for example prior sev1/build errors), narrow `--since-minutes`, then inspect `CMD-025`/`CMD-028` before escalating.
    - `runtime_errors_or_alerts_unconfirmed`: runtime errors/sev1 exist but cause is not confirmed; rerun `CMD-040 --run-drills` and inspect `CMD-028`.
  - `HEALTHY`: no boundary failure indicators in this window and deterministic drills passed.
- iPlan boundary failures:
  - `degraded_reasons` containing `iplan_*_failed`
- Gemini synthesis degradation:
  - `operation=regulation_query`, `outcome=degraded`, `degraded_reasons=["llm_synthesis_unavailable"]`
- Vision degradation:
  - `operation=plan_search`, `degraded_reasons` containing `vision_service_unavailable` or `vision_analysis_unavailable`
- Latency-alert calibration checks:
  - `regulation_query` sev3 alerts should correspond to `latency_ms>=4000`
  - `regulation_query` sev2 alerts should correspond to `latency_ms>=8000`

Threshold recalibration cadence (`CMD-036`):
- run at least weekly during active development.
- run immediately after incidents where sev2/sev3 alert volume mismatches observed latency behavior.
- run immediately after threshold/payload changes in telemetry or alert-routing docs.
- for each recalibration run, keep paired evidence:
  - `CMD-036` JSON snapshot
  - `CMD-029` dashboard view for the same time window
- if thresholds are changed, record rationale in `docs/manifest/03_decisions.md`.

External snapshot cadence (`CMD-040`):
- run at least weekly during active development.
- run immediately after provider/runtime incidents or dependency-boundary changes.
- record each cadence capture in `docs/implementation/checklists/09_evidence_cadence_ledger.md` with:
  - `status`,
  - `warning_context` (when status is `WARNING`),
  - deterministic drill summary.
- when `warning_context=historical_runtime_window_noise`:
  - rerun `CMD-040` with a narrowed window (for example `--since-minutes 60`),
  - inspect `CMD-025` and `CMD-028` for that narrowed window,
  - record narrowed-window command outputs in the same ledger entry before escalation.
- when `warning_context=historical_build_timeout_sev1_noise`:
  - rerun `CMD-040` with a narrowed window (for example `--since-minutes 60`),
  - inspect `CMD-026` (`operation=build`) and `CMD-028` for the same narrowed window,
  - record both command outputs in the same ledger entry before escalation.

Build-window saturation snapshot discipline (`CMD-038`):
- when dashboard saturation fields are `None` in passive windows, run:
```bash
(python3 scripts/build_vectordb_cli.py build --max-plans 1 --no-vision || true) && python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500
```
- expected evidence:
  - `build` operation appears in dashboard summary.
  - saturation fields include `saturation_ratio_1m`, `disk_free_ratio_cache_dir`, and `rss_mb`.
  - if `memory_used_ratio` is `None`, verify explicit availability semantics in event payload/dashboard context:
    - `memory_used_ratio_source`
    - `memory_used_ratio_unavailable_reason`
- if build command fails due provider timeout/network instability, still keep the emitted `build` event + dashboard snapshot for triage evidence.

Remediation:
- Retry with smaller scoped queries (`plan_id` over broad location/keyword search).
- Set/verify Gemini API key when vision/LLM synthesis is expected.
- If degraded behavior persists, keep network tests gated and run deterministic rehearsal suites:
```bash
./venv/bin/python -m pytest tests/unit/application/test_external_dependency_degraded_modes.py -q
./venv/bin/python -m pytest tests/unit/infrastructure/test_iplan_repository_error_signal.py -q
./venv/bin/python -m pytest tests/integration/iplan/test_external_dependency_drills.py -q
```

## Endpoint-family contract drift (COR-02)
Likely causes:
- iPlan endpoint payload shape drift (missing `source`, `plan_number`, or municipality fields),
- sample-backed integration metadata no longer preserving iPlan-family assumptions,
- MAVAT attachment/link semantics changed without corresponding contract/runbook updates.

Verification commands:
```bash
./venv/bin/python -m pytest tests/integration/data_contracts/test_boundary_payload_contracts.py -q
./venv/bin/python -m pytest tests/integration/iplan/test_iplan_sample_data_quality.py -q
```

Interpretation:
- `test_iplan_endpoint_family__source_and_metadata_contract_fields_present` failure implies iPlan-family metadata contract drift.
- `test_iplan_endpoint_family__plan_number_pattern_on_iplan_sources` failure implies iPlan plan-identifier contract drift.
- If deterministic suites stay green but MAVAT endpoint behavior is still suspect, run bounded opt-in live rehearsal (`RUN_NETWORK_TESTS=1`) under the policy below.

## Live-network rehearsal policy (opt-in and bounded)
`tests/integration/iplan/test_pydoll_live_mavat_documents__optional.py` remains optional and should not gate default CI.

When to run:
- at most once per calendar week during normal operation,
- after pydoll/browser/dependency changes affecting live scraping,
- after incidents where deterministic drills are green but provider behavior is still suspect.

Run command:
```bash
RUN_NETWORK_TESTS=1 RUN_NETWORK_REHEARSAL_MAX_ATTEMPTS=2 RUN_NETWORK_REHEARSAL_TIMEOUT_SECONDS=45 ./venv/bin/python -m pytest tests/integration/iplan/test_pydoll_live_mavat_documents__optional.py -q
```

Guardrails:
- CI execution is blocked by default; only allow in a dedicated manual rehearsal job:
```bash
RUN_NETWORK_TESTS=1 RUN_NETWORK_ALLOW_CI=1 RUN_NETWORK_REHEARSAL_MAX_ATTEMPTS=1 RUN_NETWORK_REHEARSAL_TIMEOUT_SECONDS=45 ./venv/bin/python -m pytest tests/integration/iplan/test_pydoll_live_mavat_documents__optional.py -q
```
- Skip outcomes are acceptable for provider throttling, missing optional dependency, or bounded timeout.
- When the bounded rehearsal skips after running, inspect the emitted status/detail/timestamp in the skip reason to distinguish timeout/block/wrong-page style failures from a simple empty artifact list.
