# Evidence Cadence Ledger

- Created by: `prompt-11-docs-diataxis-release` (`IMP-19`)
- Date: 2026-02-09
- Canonical purpose: single checklisted ledger for recurring observability evidence cadence captures.
- Canonical command bundle: `CMD-036`, `CMD-029`, `CMD-038`, `CMD-039`, `CMD-040`.

## Recurring Entry Template
For each cadence or trigger run, record one entry and complete all checks:

1. [ ] `CMD-036` snapshot captured for the active window.
2. [ ] `CMD-029` dashboard captured from the same window.
3. [ ] `CMD-038` build-window drill captured (or deferred with explicit reason).
4. [ ] `CMD-039` artifact freshness audit captured.
5. [ ] `CMD-040` external dependency snapshot captured (include `status` + `warning_context` when present).
   - [ ] If `warning_context=historical_runtime_window_noise`, include narrowed-window `CMD-040` rerun + `CMD-025`/`CMD-028` inspection evidence before escalation.
   - [ ] If `warning_context=historical_build_timeout_sev1_noise`, include narrowed-window `CMD-040` rerun + `CMD-026`/`CMD-028` inspection evidence before escalation.
6. [ ] Owner, outcome, and follow-up decisions recorded.

## Ledger Entries

### 2026-02-09 - IMP-19 bootstrap entry
- Owner: maintainer
- Trigger: post-`OPP-01` alignment correction packet (`IMP-19` hardening)
- [x] `CMD-036`:
  - command: `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json`
  - key results: `events_total=304`, `alerts_total=13`, `regulation_query p95=3467.34ms`, `build p95=44985.39ms`, `memory_signal_context.status=available`
- [x] `CMD-029`:
  - command: `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500`
  - key results: `events=304`, `alerts=13`, `saturation_ratio_1m_p95=0.2886`, `memory_used_ratio_p95=0.52`, `disk_free_ratio_cache_dir_p05=0.3176`, `rss_mb_p95=320.78`
- [x] `CMD-038`:
  - command: `(python3 scripts/build_vectordb_cli.py build --max-plans 1 --no-vision || true) && python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500`
  - key results: build ended degraded (`HTTPError` timeout) but produced `build` telemetry and alert evidence; dashboard retained saturation fields with `memory_signal_latest_source=memory_pressure_q`
- [x] `CMD-039`:
  - command: `python3 -c "import json,datetime,pathlib; items=json.loads(pathlib.Path('docs/artifacts/index.json').read_text(encoding='utf-8')).get('artifacts', []); cutoff=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=30)).isoformat(); stale=[i.get('id','unknown') for i in items if (not isinstance(i.get('retrieved_at'), str)) or (i.get('retrieved_at') < cutoff)]; print(f'artifacts_total={len(items)} stale_total={len(stale)}'); print('stale_ids=' + ','.join(stale) if stale else 'stale_ids=')"`
  - key results: `artifacts_total=5`, `stale_total=0`
- [ ] `CMD-040`:
  - command: `python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills`
  - key results: not captured in IMP-19 bootstrap entry (requirement added later by CMD-040 cadence hardening packet).
- [x] Outcome and follow-up:
  - no threshold change triggered in this packet; cadence discipline and ledger centralization are now explicit.
  - decision record: `docs/manifest/03_decisions.md` (`ADR-0029`).
  - next recommended packet: `prompt-02-app-development-playbook` for `OPP-02` (external dependency health snapshot bundle).

### 2026-02-09 - CMD-040 cadence hardening entry
- Owner: maintainer
- Trigger: post-`OPP-03` alignment correction (`CMD-040` cadence + warning-interpretation hardening)
- [x] `CMD-036`:
  - command: `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json`
  - key results: `events_total=286`, `alerts_total=12`, `regulation_query p95=3502.91ms`, `build p95=44985.39ms`, `memory_signal_context.status=available`
- [x] `CMD-029`:
  - command: `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500`
  - key results: `events=286`, `alerts=12`, `saturation_ratio_1m_p95=0.2886`, `memory_used_ratio_p95=0.59`, `disk_free_ratio_cache_dir_p05=0.3173`, `rss_mb_p95=320.78`
- [x] `CMD-038`:
  - command: `(python3 scripts/build_vectordb_cli.py build --max-plans 1 --no-vision || true) && python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500`
  - key results: build ended degraded (`HTTPError` timeout) but emitted `build` telemetry/alerts; dashboard retained saturation fields with `memory_signal_latest_source=memory_pressure_q`
- [x] `CMD-039`:
  - command: `python3 -c "import json,datetime,pathlib; items=json.loads(pathlib.Path('docs/artifacts/index.json').read_text(encoding='utf-8')).get('artifacts', []); cutoff=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=30)).isoformat(); stale=[i.get('id','unknown') for i in items if (not isinstance(i.get('retrieved_at'), str)) or (i.get('retrieved_at') < cutoff)]; print(f'artifacts_total={len(items)} stale_total={len(stale)}'); print('stale_ids=' + ','.join(stale) if stale else 'stale_ids=')"`
  - key results: `artifacts_total=5`, `stale_total=0`
- [x] `CMD-040`:
  - command: `python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills`
  - key results: `status=WARNING`, `warning_context=historical_runtime_window_noise`, deterministic drills `PASS/PASS/PASS`
- [x] narrowed-window confirmation (`historical_runtime_window_noise`):
  - command: `python3 scripts/quick_status.py external --since-minutes 60 --events-limit 1000 --alerts-limit 500 --run-drills`
  - key results: `status=WARNING`, `warning_context=historical_runtime_window_noise`, `events=95`, `alerts=5`, deterministic drills `PASS/PASS/PASS`
  - supporting triage commands:
    - `python3 scripts/observability_cli.py alerts --since-minutes 60 --limit 50`
    - `python3 scripts/observability_cli.py events --outcome error --since-minutes 60 --limit 100`
  - interpretation: narrowed-window signals remained dominated by historical build timeout errors (`UnifiedDataPipeline` `HTTPError`), with zero degraded dependency reasons; escalation deferred in favor of continued cadence monitoring.
- [x] Outcome and follow-up:
  - cadence template now requires `CMD-040` capture per recurring entry.
  - warning interpretation is now context-specific (`warning_context`) and escalation is conditioned on context with narrowed-window confirmation requirements.
  - next recommended packet: `prompt-03-alignment-review-gate`.

### 2026-02-09 - Post-IMP-22 build-timeout warning follow-through entry
- Owner: maintainer
- Trigger: post-`IMP-22` open correction to capture narrowed-window cadence evidence for `historical_build_timeout_sev1_noise`.
- [x] `CMD-036`:
  - command: `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json`
  - key results: `events_total=223`, `alerts_total=8`, `regulation_query p95=3706.13ms`, `build p95=44985.39ms`, `memory_signal_context.status=available`
- [x] `CMD-029`:
  - command: `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500`
  - key results: `events=223`, `alerts=8`, `saturation_ratio_1m_p95=0.2886`, `memory_used_ratio_p95=0.59`, `disk_free_ratio_cache_dir_p05=0.3173`, `rss_mb_p95=320.78`
- [ ] `CMD-038`:
  - command: `(python3 scripts/build_vectordb_cli.py build --max-plans 1 --no-vision || true) && python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500`
  - key results: deferred in this targeted follow-through entry; most recent build-window drill evidence remains in the `CMD-040 cadence hardening entry` above.
- [x] `CMD-039`:
  - command: `python3 -c "import json,datetime,pathlib; items=json.loads(pathlib.Path('docs/artifacts/index.json').read_text(encoding='utf-8')).get('artifacts', []); cutoff=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=30)).isoformat(); stale=[i.get('id','unknown') for i in items if (not isinstance(i.get('retrieved_at'), str)) or (i.get('retrieved_at') < cutoff)]; print(f'artifacts_total={len(items)} stale_total={len(stale)}'); print('stale_ids=' + ','.join(stale) if stale else 'stale_ids=')"`
  - key results: `artifacts_total=5`, `stale_total=0`
- [x] `CMD-040`:
  - command: `python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills`
  - key results: `status=WARNING`, `warning_context=historical_build_timeout_sev1_noise`, `warning_noise_profile: build_timeout_error_events=4 non_build_error_events=0 build_timeout_sev1_alerts=4 non_build_sev1_alerts=0`, deterministic drills `PASS/PASS/PASS`
- [x] narrowed-window confirmation (`historical_build_timeout_sev1_noise`):
  - command: `python3 scripts/quick_status.py external --since-minutes 60 --events-limit 1000 --alerts-limit 500 --run-drills`
  - key results: `status=HEALTHY`, `events=60`, `alerts=1`, deterministic drills `PASS/PASS/PASS`
  - supporting triage commands:
    - `python3 scripts/observability_cli.py events --operation build --since-minutes 60 --limit 100` (`No matching events.`)
    - `python3 scripts/observability_cli.py events --outcome error --since-minutes 60 --limit 100` (`No matching events.`)
    - `python3 scripts/observability_cli.py alerts --since-minutes 60 --limit 100` (`sev3 regulation_query` record only)
  - interpretation: the broader window is still dominated by historical build-timeout sev1 records, while narrowed-window evidence shows no current build/error boundary signals; escalation remains deferred.
- [x] Outcome and follow-up:
  - correction for narrowed-window `historical_build_timeout_sev1_noise` cadence evidence is now satisfied.
  - next recommended packet: `prompt-03-alignment-review-gate` (post-cadence confirmation refresh).
