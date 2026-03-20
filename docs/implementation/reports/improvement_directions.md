# Improvement Directions Report

- Run date: 2026-02-08
- Prompt executed: `prompt-14-improvement-direction-bet-loop`
- Stage: Cool-down (Phase 4/5)
- Objective anchor: `docs/manifest/00_overview.md`

## Current-State Snapshot (Evidence-Based)
- Objective alignment: stable and explicit (`docs/manifest/00_overview.md`, `docs/implementation/reports/alignment_review.md`).
- Capability coverage: core query/search/build workflows are implemented and test-covered (`app.py`, `src/application/services/*`, `src/vectorstore/unified_pipeline.py`, `tests/*`).
- Reliability posture: CI and release workflows exist with incremental quality and semantic checks (`.github/workflows/ci.yml`, `.github/workflows/release.yml`).
- Observability posture: structured instrumentation + local backend/alert routing + build saturation signal + query CLI UX are implemented; visual dashboard UX remains pending (`docs/manifest/07_observability.md`, `scripts/observability_cli.py`).
- Documentation posture: canonical docs baseline exists and primary navigation/stale-claim cleanup is completed (`docs/INDEX.md`, `docs/README.md`, `docs/implementation/checklists/02_milestones.md`).
- Open operational risks: observability depth, CI quality-gate breadth, and external provider variability (`docs/implementation/reports/alignment_review.md`).

## Opportunity Inventory

| ID | Direction | Type | Evidence | Gap | Impact | Confidence | Effort | Deferral Risk | Suggested Prompt Chain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IMP-01 | Observability backend + alert routing | reliability/ops | `docs/manifest/07_observability.md`, `scripts/observability_cli.py`, `docs/implementation/reports/alignment_review.md` | implemented baseline and query UX; remaining gap is visual dashboard UX depth and richer resource signals | H | H | M/L | M | `prompt-14` -> `prompt-02` -> `prompt-03` |
| IMP-02 | CI quality-gate hardening + release semantics | devex/release | `docs/manifest/11_ci.md`, `.github/workflows/ci.yml`, `.github/workflows/release.yml`, `checkbox.md` | implemented incremental gates; remaining gap is broader repo quality coverage | M/H | H | S/M | M | `prompt-14` -> `prompt-02` -> `prompt-03` |
| IMP-03 | Docs navigation and legacy drift cleanup | docs/ux | `docs/INDEX.md`, `docs/implementation/checklists/02_milestones.md`, `checkbox.md`, `docs/manifest/10_testing.md` | some canonical pages still contain stale claims and legacy overlap | M | H | S/M | M | `prompt-14` -> `prompt-11` -> `prompt-03` |
| IMP-04 | External dependency degradation guardrails | reliability/testing | `docs/implementation/reports/alignment_review.md`, `docs/manifest/07_observability.md`, `tests/integration/iplan/*` | degraded-mode behavior is partially tested/documented but not fully triaged/observable | H | M | M | H | `prompt-14` -> `prompt-10` -> `prompt-02` -> `prompt-03` |
| IMP-05 | Reproducible environment lock artifact | build/reproducibility | `checkbox.md`, `requirements.txt`, `requirements-dev.txt`, `setup.sh` | no pinned lock artifact for deterministic recreation | M | M | M | M | `prompt-14` -> `prompt-02` -> `prompt-11` |
| IMP-06 | Dependency-doc drift automation | ci/docs | `checkbox.md`, `docs/manifest/02_tech_stack.md`, `docs/manifest/11_ci.md` | dependency documentation can drift from install files | M | M | S | M | `prompt-14` -> `prompt-02` |

## Selected Directions (Top 4)

### IMP-01: Observability backend + alert routing
- Outcome statement: critical query/search/build signals are exported to a documented backend path with thresholded alert routing and responder ownership.
- Why now: this is the highest residual operational risk after baseline CI and release automation were completed.
- Implementation surface (files/areas): `src/telemetry.py`, `src/application/services/regulation_query_service.py`, `src/application/services/plan_search_service.py`, `src/vectorstore/unified_pipeline.py`, `docs/manifest/07_observability.md`, `docs/manifest/09_runbook.md`.
- Integration dependencies: existing structured `OBS_EVENT` schema and workflow metrics sink; no architecture split required.
- Testing strategy: unit tests for telemetry helpers, integration tests for failure/degraded paths, optional e2e smoke assertions for visible degraded states.
- Observability/release/doc updates: update SLI/SLO mapping, command map, and triage runbook with backend query examples.
- Done signal: dashboard/collector path documented and reproducible; alert thresholds and owners recorded; verification commands pass.
- Suggested execution prompt chain: `prompt-02` -> `prompt-03`.

### IMP-02: CI quality-gate hardening + release semantics
- Outcome statement: CI and release workflows enforce style/format gates plus tag-to-changelog semantic consistency.
- Why now: current workflows verify tests/integrity but can still miss formatting drift and release metadata mismatches.
- Implementation surface (files/areas): `.github/workflows/ci.yml`, `.github/workflows/release.yml`, optional `scripts/` validation helper, `docs/manifest/11_ci.md`, `docs/reference/release_workflow.md`.
- Integration dependencies: current marker/prompt checks stay as baseline and are extended.
- Testing strategy: workflow lint command checks in CI and local script verification for release-tag/changelog mapping.
- Observability/release/doc updates: update command-map IDs and release readiness checklist references.
- Done signal: CI fails on formatting/lint drift and release workflow fails when tag/changelog do not align.
- Suggested execution prompt chain: `prompt-02` -> `prompt-03`.

### IMP-03: Docs navigation and legacy drift cleanup
- Outcome statement: onboarding/engineering docs no longer contain contradictory primary guidance; index/readme navigation is canonical.
- Why now: docs are close to coherent but still have targeted stale statements that reduce trust and increase contributor friction.
- Implementation surface (files/areas): `docs/INDEX.md`, `docs/README.md`, `docs/manifest/10_testing.md`, selected legacy pages under `docs/`.
- Integration dependencies: must stay synchronized with CI/test manifests and milestones.
- Testing strategy: grep-based stale-claim checks + manual navigation pass.
- Observability/release/doc updates: reflect final source-of-truth links and deprecation notes.
- Done signal: no contradictory CI/observability state claims in primary docs; navigation flow is consistent.
- Suggested execution prompt chain: `prompt-11` -> `prompt-03`.

### IMP-04: External dependency degradation guardrails
- Outcome statement: iPlan/Gemini failure/degraded states are explicitly instrumented, tested, and triaged with stable commands.
- Why now: external dependency variability remains the top runtime uncertainty in current residual-risk set.
- Implementation surface (files/areas): service fallback/error paths under `src/application/services/*`, relevant repository adapters, `tests/integration/*`, `docs/manifest/07_observability.md`, `docs/troubleshooting.md`.
- Integration dependencies: observability backend direction (IMP-01) amplifies value but is not a strict prerequisite.
- Testing strategy: add integration tests that force dependency errors/degraded paths; keep live network tests gated.
- Observability/release/doc updates: add explicit degraded-mode triage steps and threshold examples.
- Done signal: deterministic degraded-path tests pass and triage instructions are command-map aligned.
- Suggested execution prompt chain: `prompt-10` -> `prompt-02` -> `prompt-03`.

## Packeting Plan (Bounded)

### Now (appetite: medium)
1. Packet A: IMP-01 observability backend + alert routing.
   - Status: completed in current cycle via `prompt-02` (including query CLI UX baseline).
2. Post-packet drift refresh.
   - Prompt chain: `prompt-03` once.

### Next (appetite: medium)
1. Packet B: IMP-02 CI quality-gate hardening + release semantics.
   - Status: completed in current cycle via `prompt-02`.
2. Post-packet drift refresh.
   - Prompt chain: `prompt-03` once.
3. Packet C: IMP-03 docs navigation and stale-claim cleanup.
   - Status: completed in current cycle via `prompt-11`.
4. Post-packet drift refresh.
   - Prompt chain: `prompt-03` once.

### Not now (appetite: medium/large)
1. Packet D: IMP-04 external dependency degradation guardrails.
   - Prompt chain: `prompt-10` then `prompt-02` then `prompt-03`.
2. IMP-05/IMP-06 (reproducibility lock artifact and dependency-doc drift automation) after A/B/C close.

## Handoff
- Recommended immediate next prompt: `prompt-03-alignment-review-gate` (post-IMP-04 drift refresh).

## 2026-02-09 Update
- IMP-04 packet execution (`prompt-10` -> `prompt-02`) is now complete:
  - deterministic degraded-mode tests added:
    - `tests/unit/application/test_external_dependency_degraded_modes.py`
    - `tests/unit/infrastructure/test_iplan_repository_error_signal.py`
  - degraded outcome reason telemetry is explicit in:
    - `src/application/services/regulation_query_service.py`
    - `src/application/services/plan_search_service.py`
    - `src/infrastructure/repositories/iplan_repository.py`
  - triage command map and troubleshooting guidance updated:
    - `docs/manifest/09_runbook.md` (`CMD-027`, `CMD-028`)
    - `docs/manifest/07_observability.md`
    - `docs/troubleshooting.md`

## 2026-02-09 Update (M5 correction progress)
- M5 correction 1 (observability UX/saturation depth) is complete:
  - operator dashboard command + richer saturation/resource signals are implemented and mapped (`CMD-029`).
- M5 correction 2 (CI quality gate breadth with bounded debt) is complete:
  - repo-wide parse/syntax lint gate (`CMD-021`) now runs in CI.
  - changed-file formatting debt-burn gate (`CMD-030`) was added via `scripts/quality_changed_python.py`.
  - formatting debt baseline is explicit in `scripts/quality_black_debt_allowlist.txt` and reviewable via `CMD-031`.
  - maintained-surface formatting guard (`CMD-022`) remains as critical-surface fallback.
- M5 correction 3 (reproducibility lock + dependency-doc drift automation) is complete:
  - deterministic lock artifact added: `requirements.lock`.
  - dependency lock/docs sync validator added: `scripts/check_dependency_sync.py`.
  - generated dependency inventory doc added: `docs/reference/dependencies.md`.
  - CI now enforces dependency drift check (`CMD-033`), and regeneration path is documented (`CMD-032`).
- Post-M5 drift refresh (`prompt-03`) has been rerun and synced.
- Recommended immediate next prompt:
  - `prompt-14-improvement-direction-bet-loop` to pick the next bounded post-M5 implementation bet.

## 2026-02-09 Update (Post-M5 prompt-14 rerun)
- Prompt executed: `prompt-14-improvement-direction-bet-loop` (manual rerun after M5 closure + prompt-03 refresh).
- Current top opportunities:
  1. Formatting debt burn phase 2 (migrate allowlist modules into always-enforced format surfaces).
  2. Observability backend evolution decision (local-only vs hosted operator backend/dashboard).
  3. External dependency drill depth (stronger deterministic/non-network failure rehearsal).
- Selected immediate direction:
  - formatting debt burn phase 2 (bounded module-batch packet).
- Recommended immediate next prompt:
  - `prompt-02-app-development-playbook` (formatting debt burn phase-2 packet), then `prompt-03-alignment-review-gate` once.

## 2026-02-09 Update (IMP-07 execution)
- IMP-07 formatting debt burn phase 2 is complete:
  - migrated module group: `src/domain/*`.
  - allowlist baseline reduced from `96` lines to `81` lines in `scripts/quality_black_debt_allowlist.txt`.
  - migrated files promoted to always-enforced formatting surfaces in `CMD-022`.
- Remaining next-cycle open bets:
  - IMP-08 observability backend evolution decision.
  - IMP-09 external dependency drill depth.
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` once (post-IMP-07 drift refresh), then `prompt-14` if further re-ranking is needed.

## 2026-02-09 Update (Post-IMP-07 prompt-03 rerun)
- Prompt executed: `prompt-03-alignment-review-gate`.
- Result:
  - alignment remains `ALIGNED_WITH_RISKS` with updated residual priorities.
  - immediate next bet-selection prompt is now `prompt-14-improvement-direction-bet-loop`.
- Recommended immediate next prompt:
  - `prompt-14-improvement-direction-bet-loop`, then `prompt-02-app-development-playbook` for the selected highest-impact bet (`IMP-08` or `IMP-09`).

## 2026-02-09 Update (Post-IMP-07 prompt-14 rerun)
- Prompt executed: `prompt-14-improvement-direction-bet-loop` (manual rerun, no router script).
- Candidate re-ranking outcome:
  1. IMP-08 observability backend evolution decision (selected now).
  2. IMP-09 external dependency drill depth.
  3. Continued formatting debt burn batches.
- Recommended immediate next prompt:
  - `prompt-02-app-development-playbook` for IMP-08, then `prompt-03-alignment-review-gate` once.

## 2026-02-09 Update (IMP-08 execution)
- IMP-08 observability backend evolution decision is complete:
  - `ADR-0017` added in `docs/manifest/03_decisions.md`.
  - `docs/manifest/07_observability.md` now locks local-only backend mode and defines hosted-backend promotion triggers.
  - milestone and bet checklists updated (`docs/implementation/checklists/02_milestones.md`, `docs/implementation/checklists/03_improvement_bets.md`).
- Remaining open next-cycle bet:
  - IMP-09 deterministic external dependency drill depth.
- Recommended immediate next prompt:
  - `prompt-10-tests-stabilization-loop` (IMP-09), then `prompt-02-app-development-playbook`, then `prompt-03-alignment-review-gate`.

## 2026-02-09 Update (IMP-09 execution)
- IMP-09 external dependency drill depth is complete:
  - added deterministic non-network integration drills:
    - `tests/integration/iplan/test_external_dependency_drills.py`
  - expanded explicit rehearsal command map:
    - `docs/manifest/09_runbook.md` (`CMD-034`, `CMD-035`)
  - tightened degraded-mode triage and rehearsal guidance:
    - `docs/troubleshooting.md`
    - `docs/manifest/07_observability.md`
  - milestone and bet checklists updated:
    - `docs/implementation/checklists/02_milestones.md`
    - `docs/implementation/checklists/03_improvement_bets.md`
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` (post-IMP-09 drift refresh).

## 2026-02-09 Update (Post-IMP-09 prompt-03 rerun)
- Prompt executed: `prompt-03-alignment-review-gate`.
- Result:
  - alignment remains `ALIGNED_WITH_RISKS`.
  - M6 is now fully complete and follow-up corrections are mapped to `M7` in `docs/implementation/checklists/02_milestones.md`.
- Recommended immediate next prompt:
  - `prompt-14-improvement-direction-bet-loop` (re-rank M7 corrections before next bounded implementation packet).

## 2026-02-09 Update (Post-IMP-09 prompt-14 rerun)
- Prompt executed: `prompt-14-improvement-direction-bet-loop` (manual rerun, no router script).
- Candidate re-ranking outcome:
  1. IMP-10 formatting debt burn phase 3 (selected now).
  2. IMP-11 observability threshold calibration.
  3. IMP-12 optional live-network rehearsal policy.
- Packet mapping updates:
  - new bets added in `docs/implementation/checklists/03_improvement_bets.md` (`IMP-10`..`IMP-12`).
  - milestone outcomes already mapped in `docs/implementation/checklists/02_milestones.md` (`M7`).
- Recommended immediate next prompt:
  - `prompt-02-app-development-playbook` for IMP-10, then `prompt-03-alignment-review-gate` once.

## 2026-02-09 Update (IMP-10 execution)
- IMP-10 formatting debt burn phase 3 is complete:
  - migrated module group: `src/application/*` (bounded files: `__init__.py`, `dtos.py`, `services/building_rights_service.py`, `services/plan_upload_service.py`).
  - allowlist baseline reduced from `81` lines to `77` lines in `scripts/quality_black_debt_allowlist.txt`.
  - migrated files promoted to always-enforced formatting surfaces in `CMD-022` (`.github/workflows/ci.yml`, `docs/manifest/09_runbook.md`).
- Remaining open M7 bets:
  - IMP-11 observability threshold calibration.
  - IMP-12 optional live-network rehearsal policy.
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` once (post-IMP-10 drift refresh), then `prompt-14` if re-ranking is needed.

## 2026-02-09 Update (Post-IMP-10 prompt-03 rerun)
- Prompt executed: `prompt-03-alignment-review-gate`.
- Result:
  - alignment remains `ALIGNED_WITH_RISKS`.
  - M7 remains in progress with two open corrections: IMP-11 and IMP-12.
- Recommended immediate next prompt:
  - `prompt-02-app-development-playbook` for IMP-11 (observability threshold calibration), then `prompt-03-alignment-review-gate` once.

## 2026-02-09 Update (IMP-11 execution)
- IMP-11 observability threshold calibration is complete:
  - regulation-query latency thresholds recalibrated in `src/telemetry.py`:
    - `sev3: 3000ms -> 4000ms`
    - `sev2: 6000ms -> 8000ms`
  - threshold calibration command map extended:
    - `docs/manifest/09_runbook.md` (`CMD-036`)
  - threshold rationale and triage guidance updated:
    - `docs/manifest/07_observability.md`
    - `docs/troubleshooting.md`
  - milestone and bet checklists updated:
    - `docs/implementation/checklists/02_milestones.md`
    - `docs/implementation/checklists/03_improvement_bets.md`
- Remaining open M7 bet:
  - IMP-12 optional live-network rehearsal policy.
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` once (post-IMP-11 drift refresh), then `prompt-02-app-development-playbook` for IMP-12.

## 2026-02-09 Update (Post-IMP-11 prompt-03 rerun)
- Prompt executed: `prompt-03-alignment-review-gate`.
- Result:
  - alignment remains `ALIGNED_WITH_RISKS`.
  - M7 now has one remaining open correction: IMP-12 optional live-network rehearsal policy.
- Recommended immediate next prompt:
  - `prompt-02-app-development-playbook` for IMP-12, then `prompt-03-alignment-review-gate` once.

## 2026-02-09 Update (IMP-12 execution)
- IMP-12 optional live-network rehearsal policy is complete:
  - bounded opt-in rehearsal guardrails implemented in:
    - `tests/integration/iplan/test_pydoll_live_mavat_documents__optional.py`
  - command map extended with live rehearsal drill:
    - `docs/manifest/09_runbook.md` (`CMD-037`)
  - cadence/guardrail policy documented in:
    - `docs/manifest/10_testing.md`
    - `docs/troubleshooting.md`
  - decision log and checklist surfaces updated:
    - `docs/manifest/03_decisions.md` (ADR-0020)
    - `docs/implementation/checklists/02_milestones.md`
    - `docs/implementation/checklists/03_improvement_bets.md`
- M7 state:
  - completed: IMP-10, IMP-11, IMP-12.
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` once (post-IMP-12 drift refresh).

## 2026-02-09 Update (Post-IMP-12 prompt-03 rerun)
- Prompt executed: `prompt-03-alignment-review-gate`.
- Result:
  - alignment remains `ALIGNED_WITH_RISKS`.
  - M7 remains fully complete (`IMP-10`, `IMP-11`, `IMP-12` all closed).
  - residual corrections are now post-M7 cadence/debt items, not additional M7 implementation packets.
- Recommended immediate next prompt:
  - `prompt-14-improvement-direction-bet-loop` to rank post-M7 bounded bets.
- Follow-up:
  - `prompt-02-app-development-playbook` for the highest-impact selected post-M7 bet.

## 2026-02-09 Update (Post-IMP-12 prompt-14 rerun)
- Prompt executed: `prompt-14-improvement-direction-bet-loop` (manual rerun, no router script).
- Candidate re-ranking outcome:
  1. IMP-13 observability threshold recalibration cadence policy (selected now).
  2. IMP-14 formatting debt burn phase 4.
  3. IMP-15 saturation snapshot discipline for observability triage windows.
- Evidence anchors:
  - threshold calibration exists but no explicit periodic cadence policy (`CMD-036` is command-mapped, cadence remains implicit).
  - formatting allowlist baseline is currently `77` lines (`scripts/quality_black_debt_allowlist.txt`).
  - recent dashboard windows can lack saturation values outside active build periods (`saturation_ratio_1m_p95=None`, `memory_used_ratio_p95=None`, `disk_free_ratio_cache_dir_p05=None`).
- Packet mapping updates:
  - new bets added in `docs/implementation/checklists/03_improvement_bets.md` (`IMP-13`..`IMP-15`).
  - new milestone outcomes mapped in `docs/implementation/checklists/02_milestones.md` (`M8`).
- Selected post-M7 directions (top 3):
  1. IMP-13 threshold recalibration cadence policy
     - outcome: explicit periodic and trigger-based `CMD-036` policy with evidence-recording requirements.
     - why now: thresholds were tuned once (IMP-11), but recurrence criteria are still implicit.
     - implementation surface: `docs/manifest/07_observability.md`, `docs/manifest/09_runbook.md`, `docs/troubleshooting.md`.
     - integration/testing: docs + command-map checks backed by `CMD-036` summary/dashboard evidence.
     - done signal: cadence + incident triggers are explicit and operationally repeatable.
     - suggested prompt chain: `prompt-02` -> `prompt-03`.
  2. IMP-14 formatting debt burn phase 4
     - outcome: migrate one additional bounded module group from allowlist debt into always-enforced formatting surfaces.
     - why now: debt baseline remains `77`, and phased migration policy is already in place.
     - implementation surface: `scripts/quality_black_debt_allowlist.txt`, `.github/workflows/ci.yml`, `docs/manifest/09_runbook.md`, selected `src/*` group.
     - integration/testing: changed-file and maintained-surface formatting checks (`CMD-022`, `CMD-030`) plus allowlist baseline delta.
     - done signal: allowlist baseline drops below `77` with migrated files continuously enforced.
     - suggested prompt chain: `prompt-02` -> `prompt-03`.
  3. IMP-15 saturation snapshot discipline
     - outcome: runbook/troubleshooting define build-window snapshot drill so saturation fields are consistently captured.
     - why now: passive windows frequently produce `None` saturation fields, weakening triage evidence quality.
     - implementation surface: `docs/manifest/07_observability.md`, `docs/manifest/09_runbook.md`, `docs/troubleshooting.md`, optional `scripts/observability_cli.py`.
     - integration/testing: build-window rehearsal + dashboard evidence path and docs grep checks for required fields.
     - done signal: repeatable snapshot workflow captures `saturation_ratio_1m`, `memory_used_ratio`, and `disk_free_ratio_cache_dir` context.
     - suggested prompt chain: `prompt-02` -> `prompt-03`.
- Recommended immediate next prompt:
  - `prompt-02-app-development-playbook` for IMP-13, then `prompt-03-alignment-review-gate` once.

## 2026-02-09 Update (IMP-13 execution)
- IMP-13 threshold recalibration cadence policy is complete:
  - explicit cadence/trigger policy added:
    - `docs/manifest/07_observability.md`
    - `docs/manifest/09_runbook.md`
    - `docs/troubleshooting.md`
  - decision log updated:
    - `docs/manifest/03_decisions.md` (ADR-0021)
  - milestone and bet checklists updated:
    - `docs/implementation/checklists/02_milestones.md`
    - `docs/implementation/checklists/03_improvement_bets.md`
- Remaining open M8 bets:
  - IMP-14 formatting debt burn phase 4.
  - IMP-15 saturation snapshot discipline.
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` once (post-IMP-13 drift refresh), then `prompt-02-app-development-playbook` for IMP-14.

## 2026-02-09 Update (Post-IMP-13 prompt-03 rerun)
- Prompt executed: `prompt-03-alignment-review-gate` (manual rerun, no router script).
- Result:
  - alignment remains `ALIGNED_WITH_RISKS`.
  - cadence policy drift is now closed and no longer an open correction.
  - residual correction focus remains on:
    1. IMP-14 formatting debt burn phase 4.
    2. IMP-15 saturation snapshot discipline.
- Evidence anchors:
  - `./venv/bin/python -m pytest -m unit -q` -> `50 passed, 28 deselected`
  - `./venv/bin/python -m pytest -m integration -q` -> `21 passed, 1 skipped, 56 deselected`
  - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` -> `events=274`, `alerts=16`, `regulation_query p95=3502.91ms`, saturation snapshot fields `None` outside active build windows
  - `wc -l scripts/quality_black_debt_allowlist.txt` -> `77`
- Recommended immediate next prompt:
  - `prompt-02-app-development-playbook` for IMP-14, then `prompt-03-alignment-review-gate` once.

## 2026-02-09 Update (IMP-14 execution)
- IMP-14 formatting debt burn phase 4 is complete:
  - migrated module group: `src/data_management/*` (`__init__.py`, `data_store.py`, `fetchers.py`, `pydoll_fetcher.py`).
  - allowlist baseline reduced from `77` lines to `73` lines in `scripts/quality_black_debt_allowlist.txt`.
  - migrated files promoted to always-enforced formatting surfaces in `CMD-022`:
    - `.github/workflows/ci.yml`
    - `docs/manifest/09_runbook.md`
  - CI debt-burn progression notes updated in:
    - `docs/manifest/11_ci.md`
  - decision recorded:
    - `docs/manifest/03_decisions.md` (ADR-0022)
- Remaining open M8 bet:
  - IMP-15 saturation snapshot discipline.
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` once (post-IMP-14 drift refresh), then `prompt-02-app-development-playbook` for IMP-15.

## 2026-02-09 Update (Post-IMP-14 prompt-03 rerun)
- Prompt executed: `prompt-03-alignment-review-gate` (manual rerun, no router script).
- Result:
  - alignment remains `ALIGNED_WITH_RISKS`.
  - M8 now has one remaining open correction (`IMP-15`).
  - formatting debt phase 4 closure is validated (`allowlist=73`), with further debt-burn now secondary to IMP-15.
- Evidence anchors:
  - `./venv/bin/python -m pytest -m unit -q` -> `50 passed, 28 deselected`
  - `./venv/bin/python -m pytest -m integration -q` -> `21 passed, 1 skipped, 56 deselected`
  - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` -> `events=284`, `alerts=16`, `regulation_query p95=3502.91ms`, saturation snapshot fields `None` outside active build windows
  - `wc -l scripts/quality_black_debt_allowlist.txt` -> `73`
- Recommended immediate next prompt:
  - `prompt-02-app-development-playbook` for IMP-15, then `prompt-03-alignment-review-gate` once.

## 2026-02-09 Update (IMP-15 execution)
- IMP-15 saturation snapshot discipline is complete:
  - canonical build-window snapshot drill added in command map:
    - `CMD-038` in `docs/manifest/09_runbook.md`
  - observability policy now defines required build-window snapshot evidence, expected saturation fields, and null-handling guidance:
    - `docs/manifest/07_observability.md`
    - `docs/troubleshooting.md`
  - milestone and bet checklists updated:
    - `docs/implementation/checklists/02_milestones.md` (M8 third outcome checked; M8 complete)
    - `docs/implementation/checklists/03_improvement_bets.md` (IMP-15 checked)
  - decision recorded:
    - `docs/manifest/03_decisions.md` (ADR-0023)
- Evidence anchors:
  - `(python3 scripts/build_vectordb_cli.py build --max-plans 1 --no-vision || true) && python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500`
    - build attempt degraded with external timeout but emitted structured `build` telemetry.
    - dashboard captured `build` operation and saturation snapshot fields (`saturation_ratio_1m_p95=0.267`, `disk_free_ratio_cache_dir_p05=0.3203`, `rss_mb_p95=280.56`).
  - `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json`
    - `events_total=286`, `alerts_total=17`, `events_by_operation.build=2`.
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` once (post-IMP-15 drift refresh).

## 2026-02-09 Update (Post-IMP-15 prompt-03 rerun)
- Prompt executed: `prompt-03-alignment-review-gate` (manual rerun, no router script).
- Result:
  - alignment remains `ALIGNED_WITH_RISKS`.
  - M8 is now fully complete (`IMP-13`, `IMP-14`, `IMP-15` all closed).
  - residual corrections now shift to post-M8 re-ranking rather than additional M8 implementation packets.
- Evidence anchors:
  - `./venv/bin/python -m pytest -m unit -q` -> `50 passed, 28 deselected`
  - `./venv/bin/python -m pytest -m integration -q` -> `21 passed, 1 skipped, 56 deselected`
  - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` -> `events=306`, `alerts=17`, `regulation_query p95=3453.42ms`, `build p95=44985.39ms`, saturation snapshot fields present except `memory_used_ratio`
  - `wc -l scripts/quality_black_debt_allowlist.txt` -> `73`
- Recommended immediate next prompt:
  - `prompt-14-improvement-direction-bet-loop` to rank post-M8 bounded bets.

## 2026-02-09 Update (Post-M8 prompt-14 rerun)
- Prompt executed: `prompt-14-improvement-direction-bet-loop` (manual rerun, no router script).
- Current-state snapshot (evidence-based):
  - objective and alignment posture remain stable (`docs/manifest/00_overview.md`, `docs/implementation/reports/alignment_review.md`).
  - M8 is fully complete and no M8 implementation packets remain (`docs/implementation/checklists/02_milestones.md`, `docs/implementation/checklists/03_improvement_bets.md`).
  - formatting debt is still material (`wc -l scripts/quality_black_debt_allowlist.txt` -> `73`).
  - observability saturation signal completeness remains partial in current windows (`python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` -> `memory_used_ratio_p95=None`).
  - artifact-feature alignment gate artifacts are missing (`docs/implementation/checklists/08_artifact_feature_alignment.md`, `docs/implementation/reports/artifact_feature_alignment.md` do not exist yet).

### Opportunity Inventory (Post-M8)

| ID | Direction | Type | Evidence | Gap | Impact | Confidence | Effort | Deferral Risk | Suggested Prompt Chain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IMP-16 | Artifact-feature alignment baseline gate | alignment/roadmap | missing `docs/implementation/checklists/08_artifact_feature_alignment.md`, missing `docs/implementation/reports/artifact_feature_alignment.md`, long-running multi-packet evolution in `docs/implementation/03_worklog.md` | no explicit artifact-to-feature verdict and no artifact-backed correction/opportunity map | H | H | S/M | H | `prompt-15` -> `prompt-03` |
| IMP-17 | Saturation signal completeness for memory pressure | reliability/observability | `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` (`memory_used_ratio_p95=None`), `src/vectorstore/unified_pipeline.py`, `src/observability/query.py` | memory signal can be absent in operational snapshots, reducing triage confidence and alert-context depth | M/H | M | S/M | M/H | `prompt-02` -> `prompt-10` -> `prompt-03` |
| IMP-18 | Formatting debt burn phase 5 (infrastructure batch) | quality/devex | `scripts/quality_black_debt_allowlist.txt` (`73` lines), allowlist paths include `src/infrastructure/*` | remaining debt keeps broad surfaces outside strict formatting enforcement | M | H | M | M | `prompt-02` -> `prompt-03` |
| IMP-19 | Evidence cadence ledger hardening | ops/docs | cadence policies exist in `docs/manifest/07_observability.md` and `docs/manifest/09_runbook.md`; execution proof currently relies on manual `docs/implementation/03_worklog.md` hygiene | recurring `CMD-036` + `CMD-029` + `CMD-038` evidence capture lacks a single checklisted ledger surface | M | M | S | M | `prompt-11` -> `prompt-03` |

### Selected Post-M8 Directions (Top 3)

1. IMP-16 artifact-feature alignment baseline gate
   - outcome: establish artifact-to-feature alignment artifacts with explicit verdict (`ALIGNED` / `ALIGNED_WITH_GAPS` / `MISALIGNED`) and milestone-ready corrections.
   - why now: this gate has not yet been run, while the repo has accumulated many reliability/ops packet changes that need evidence-fit validation.
   - implementation surface: `docs/implementation/checklists/08_artifact_feature_alignment.md`, `docs/implementation/reports/artifact_feature_alignment.md`, `docs/implementation/checklists/02_milestones.md`.
   - integration dependencies: existing implementation/milestone/worklog evidence and available artifact references.
   - testing strategy: docs checks for required matrix/verdict fields + milestone mapping checks.
   - observability/release/doc updates: add artifact-backed corrections/opportunities and route top outcomes into implementation packets.
   - done signal: artifact alignment report/checklist exist, include matrix + verdict, and top outcomes are mapped to milestones.
   - suggested prompt chain: `prompt-15` -> `prompt-03`.

2. IMP-17 saturation signal completeness for memory pressure
   - outcome: ensure saturation snapshots include actionable memory pressure context (or explicit availability semantics) across build-window drills.
   - why now: latest dashboard windows still show `memory_used_ratio_p95=None`, weakening incident evidence quality.
   - implementation surface: `src/vectorstore/unified_pipeline.py`, `src/observability/query.py`, `scripts/observability_cli.py`, `docs/manifest/07_observability.md`, `docs/troubleshooting.md`.
   - integration dependencies: existing `CMD-038` build-window drill and telemetry query pipeline.
   - testing strategy: unit tests for query/telemetry handling + integration drill evidence check (`dashboard`/`summary`).
   - observability/release/doc updates: update saturation-field expectations and null-handling guidance.
   - done signal: build-window dashboard snapshots provide non-empty memory context or explicit reasoned fallback with documented interpretation.
   - suggested prompt chain: `prompt-02` -> `prompt-10` -> `prompt-03`.

3. IMP-18 formatting debt burn phase 5 (infrastructure batch)
   - outcome: migrate a bounded `src/infrastructure/*` batch from debt allowlist into always-enforced formatting surfaces.
   - why now: phased debt strategy is working; continuing immediately preserves momentum and reduces CI blind spots.
   - implementation surface: `scripts/quality_black_debt_allowlist.txt`, `.github/workflows/ci.yml`, `docs/manifest/09_runbook.md`, `src/infrastructure/*`.
   - integration dependencies: existing `CMD-022` and `CMD-030` quality-gate flow.
   - testing strategy: targeted `black` run + allowlist delta checks + unchanged CI quality gates.
   - observability/release/doc updates: sync CI/runbook/decision tracking with new migrated surfaces.
   - done signal: allowlist baseline drops below `73` and selected infrastructure files are removed from allowlist and covered by strict formatting checks.
   - suggested prompt chain: `prompt-02` -> `prompt-03`.

## Packeting Plan (Post-M8)

### Now (appetite: medium)
1. Packet A: IMP-16 artifact-feature alignment baseline gate.
   - Prompt chain: `prompt-15` -> `prompt-03`.

### Next (appetite: medium)
1. Packet B: IMP-17 saturation signal completeness for memory pressure.
   - Prompt chain: `prompt-02` -> `prompt-10` -> `prompt-03`.
2. Packet C: IMP-18 formatting debt burn phase 5 (infrastructure batch).
   - Prompt chain: `prompt-02` -> `prompt-03`.

### Not now (appetite: small)
1. Packet D: IMP-19 evidence cadence ledger hardening.
   - Prompt chain: `prompt-11` -> `prompt-03`.

## Handoff (Post-M8)
- Recommended immediate next prompt:
  - `prompt-15-artifact-feature-alignment-gate`.
- Follow-up:
  - `prompt-02-app-development-playbook` for highest-impact corrective outcome from prompt-15 (or IMP-17 if no higher corrective blocker is found).

## 2026-02-09 Update (Post-M8 prompt-15 execution)
- Prompt executed: `prompt-15-artifact-feature-alignment-gate` (manual rerun, no router script).
- Result:
  - artifact-feature verdict established: `ALIGNED_WITH_GAPS`.
  - alignment artifacts created:
    - `docs/implementation/checklists/08_artifact_feature_alignment.md`
    - `docs/implementation/reports/artifact_feature_alignment.md`
  - top corrective sequence identified:
    1. `COR-01` artifact store baseline initialization.
    2. `COR-02` endpoint-family artifact-to-contract mapping.
    3. `COR-03` artifact-cited decisions/assumptions.
- Recommended immediate next prompt:
  - `prompt-02-app-development-playbook` for `COR-01`, then `prompt-03-alignment-review-gate`.

## 2026-02-09 Update (`COR-01` execution)
- Prompt executed: `prompt-02-app-development-playbook` (`COR-01`, manual/no router script).
- Result:
  - canonical artifact store baseline created under `docs/artifacts/`:
    - `README.md`, `index.json`, `blobs/.gitkeep`, `excerpts/.gitkeep`
  - baseline load-bearing artifacts seeded with metadata:
    - `ART-EXT-001`..`ART-EXT-005` in `docs/artifacts/index.json`
  - decision policy recorded:
    - `docs/manifest/03_decisions.md` (`ADR-0024`)
  - tracking surfaces synchronized:
    - `docs/implementation/checklists/08_artifact_feature_alignment.md` (`COR-01` checked)
    - `docs/implementation/checklists/02_milestones.md` (M9 artifact-baseline outcome checked)
    - `docs/implementation/checklists/03_improvement_bets.md` (`IMP-16` checked)
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` (post-`COR-01` drift refresh).
- Follow-up:
  - `prompt-10-tests-stabilization-loop` then `prompt-02-app-development-playbook` for `COR-02` endpoint-family contract mapping.

## 2026-02-09 Update (Post-`COR-01` prompt-03 rerun)
- Prompt executed: `prompt-03-alignment-review-gate` (manual rerun, no router script).
- Result:
  - alignment remains `ALIGNED_WITH_RISKS`.
  - `COR-01` closure remains validated.
  - highest remaining corrective priority is `COR-02` endpoint-family artifact-to-contract mapping.
- Evidence anchors:
  - `./venv/bin/python -m pytest -m unit -q` -> `50 passed, 28 deselected`
  - `./venv/bin/python -m pytest -m integration -q` -> `21 passed, 1 skipped, 56 deselected`
  - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` -> `events=278`, `alerts=15`, `memory_used_ratio_p95=None`
  - `wc -l scripts/quality_black_debt_allowlist.txt` -> `73`
- Recommended immediate next prompt:
  - `prompt-10-tests-stabilization-loop` for `COR-02` prep, then `prompt-02-app-development-playbook`, then `prompt-03`.

## 2026-02-09 Update (Post-`COR-02` prep prompt-10 rerun)
- Prompt executed: `prompt-10-tests-stabilization-loop` (manual rerun, no router script).
- Result:
  - `COR-02` preflight stabilization is complete.
  - required gates are green with rerun proof:
    - unit suite: `50 passed, 28 deselected` x3.
    - data-contract suite: `17 passed, 61 deselected` x3.
    - integration suite: `21 passed, 1 skipped, 56 deselected`.
    - e2e suite: `5 passed, 73 deselected`.
    - historical prior-failure tests: both target tests pass x5 each.
  - optional live-network MAVAT drill remains intentionally gated via `RUN_NETWORK_TESTS=1`.
  - aggregate full-suite run (`./venv/bin/python -m pytest -q`) entered no-progress sleep and was terminated; tracked as non-blocking for this prompt.
- Recommended immediate next prompt:
  - `prompt-02-app-development-playbook` for `COR-02` endpoint-family artifact-to-contract mapping, then `prompt-03-alignment-review-gate`.

## 2026-02-09 Update (`COR-02` execution)
- Prompt executed: `prompt-02-app-development-playbook` (`COR-02`, manual/no router script).
- Result:
  - endpoint-family artifact assumptions are now mapped explicitly in:
    - `docs/manifest/04_api_contracts.md`
  - contract coverage was tightened with explicit iPlan-family checks in:
    - `tests/integration/data_contracts/test_boundary_payload_contracts.py`
    - `tests/integration/iplan/test_iplan_sample_data_quality.py`
  - endpoint-family drift triage path is now explicit in:
    - `docs/troubleshooting.md`
  - tracking surfaces synchronized:
    - `docs/implementation/checklists/08_artifact_feature_alignment.md` (`COR-02` checked)
    - `docs/implementation/checklists/02_milestones.md` (M9 endpoint-family outcome checked)
    - `docs/manifest/03_decisions.md` (`ADR-0025`)
- Verification anchors:
  - `./venv/bin/python -m pytest tests/integration/data_contracts/test_boundary_payload_contracts.py -q` -> `3 passed, 1 warning`
  - `./venv/bin/python -m pytest tests/integration/iplan/test_iplan_sample_data_quality.py -q` -> `4 passed, 2 warnings`
  - `./venv/bin/python -m pytest tests/integration/data_contracts/test_boundary_payload_contracts.py tests/integration/iplan/test_iplan_sample_data_quality.py -q` -> `7 passed, 2 warnings`
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` (post-`COR-02` drift refresh).
- Follow-up:
  - `prompt-11-docs-diataxis-release` for `COR-03` artifact-citation adoption, then `prompt-03`.

## 2026-02-09 Update (Post-`COR-02` prompt-03 rerun)
- Prompt executed: `prompt-03-alignment-review-gate` (manual rerun, no router script).
- Result:
  - alignment remains `ALIGNED_WITH_RISKS`.
  - `COR-02` closure remains validated.
  - highest remaining corrective priority is now `COR-03` artifact-citation adoption.
- Evidence anchors:
  - `./venv/bin/python -m pytest -m unit -q` -> `50 passed, 30 deselected`
  - `./venv/bin/python -m pytest -m integration -q` -> `23 passed, 1 skipped, 56 deselected`
  - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` -> `events=303`, `alerts=17`, `memory_used_ratio_p95=None`
  - `wc -l scripts/quality_black_debt_allowlist.txt` -> `73`
- Recommended immediate next prompt:
  - `prompt-11-docs-diataxis-release` for `COR-03`, then `prompt-03-alignment-review-gate`.

## 2026-02-09 Update (`COR-03` execution)
- Prompt executed: `prompt-11-docs-diataxis-release` (`COR-03`, manual/no router script).
- Result:
  - artifact citations were adopted in load-bearing decision/assumption/observability docs:
    - `docs/manifest/03_decisions.md`
    - `docs/implementation/reports/assumptions_register.md`
    - `docs/manifest/07_observability.md`
  - tracking surfaces synchronized:
    - `docs/implementation/checklists/08_artifact_feature_alignment.md` (`COR-03` checked)
    - `docs/implementation/checklists/02_milestones.md` (M9 artifact-citation outcome checked)
    - `docs/implementation/reports/artifact_feature_alignment.md`
- Verification anchors:
  - `rg -n "ART-EXT-00[1-5]" docs/manifest/03_decisions.md docs/implementation/reports/assumptions_register.md docs/manifest/07_observability.md`
  - `rg -n "Artifact citations|Artifact Citations" docs/manifest/03_decisions.md docs/manifest/07_observability.md`
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` (post-`COR-03` drift refresh).
- Follow-up:
  - `prompt-02-app-development-playbook` for `IMP-17`, then `prompt-03`.

## 2026-02-09 Update (Post-`COR-03` prompt-03 rerun)
- Prompt executed: `prompt-03-alignment-review-gate` (manual rerun, no router script).
- Result:
  - alignment remains `ALIGNED_WITH_RISKS`.
  - `COR-03` closure remains validated.
  - highest remaining corrective priority is now `IMP-17` memory-pressure signal completeness.
- Evidence anchors:
  - `./venv/bin/python -m pytest -m unit -q` -> `50 passed, 30 deselected`
  - `./venv/bin/python -m pytest -m integration -q` -> `23 passed, 1 skipped, 56 deselected`
  - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` -> `events=313`, `alerts=17`, `memory_used_ratio_p95=None`
  - `wc -l scripts/quality_black_debt_allowlist.txt` -> `73`
- Recommended immediate next prompt:
  - `prompt-02-app-development-playbook` for `IMP-17`, then `prompt-03-alignment-review-gate`.

## 2026-02-09 Update (`IMP-17` execution)
- Prompt executed: `prompt-02-app-development-playbook` (`IMP-17`, manual/no router script).
- Result:
  - memory-pressure saturation signal completeness is improved with explicit probe semantics:
    - `src/vectorstore/unified_pipeline.py` now emits `memory_used_ratio_source` and `memory_used_ratio_unavailable_reason`.
    - macOS fallback probe uses `memory_pressure -Q` when `SC_AVPHYS_PAGES` is unavailable.
  - observability query/dashboard now exposes memory-signal availability context:
    - `src/observability/query.py`
    - `scripts/observability_cli.py`
  - documentation and tracking were synchronized:
    - `docs/manifest/07_observability.md`
    - `docs/troubleshooting.md`
    - `docs/manifest/09_runbook.md`
    - `docs/implementation/checklists/03_improvement_bets.md` (`IMP-17` checked)
    - `docs/implementation/checklists/02_milestones.md` (M9 memory-signal outcome checked)
    - `docs/manifest/03_decisions.md` (`ADR-0026`)
- Verification anchors:
  - `(python3 scripts/build_vectordb_cli.py build --max-plans 1 --no-vision || true) && python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500`
    - dashboard now reports `memory_used_ratio_p95=0.52`, `memory_signal_status=available`, `memory_signal_latest_source=memory_pressure_q`.
  - `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json`
    - `memory_signal_context.status=available`, `source_counts.memory_pressure_q=1`.
  - `./venv/bin/python -m pytest tests/unit/infrastructure/test_telemetry_backend.py tests/unit/infrastructure/test_observability_query.py tests/unit/vectorstore/test_unified_pipeline_saturation_snapshot.py -q`
    - `13 passed, 1 warning`
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` (post-`IMP-17` drift refresh).
- Follow-up:
  - `prompt-02-app-development-playbook` for `IMP-18` formatting debt burn phase 5.

## 2026-02-09 Update (Post-`IMP-17` prompt-03 rerun)
- Prompt executed: `prompt-03-alignment-review-gate` (manual rerun, no router script).
- Result:
  - alignment remains `ALIGNED_WITH_RISKS`.
  - `IMP-17` closure remains validated with explicit memory-signal semantics.
  - highest remaining corrective priority is now `IMP-18` formatting debt burn phase 5.
- Evidence anchors:
  - `./venv/bin/python -m pytest -m unit -q` -> `54 passed, 30 deselected`
  - `./venv/bin/python -m pytest -m integration -q` -> `23 passed, 1 skipped, 60 deselected`
  - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` -> `events=312`, `alerts=15`, `memory_used_ratio_p95=0.52`, `memory_signal_latest_source=memory_pressure_q`
  - `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json` -> `events_total=312`, `alerts_total=15`, `memory_signal_context.status=available`
  - `wc -l scripts/quality_black_debt_allowlist.txt` -> `73`
- Recommended immediate next prompt:
  - `prompt-02-app-development-playbook` for `IMP-18`, then `prompt-03-alignment-review-gate`.

## 2026-02-09 Update (`IMP-18` execution)
- Prompt executed: `prompt-02-app-development-playbook` (`IMP-18`, manual/no router script).
- Result:
  - formatting debt burn phase 5 is complete for bounded `src/infrastructure/*` surfaces.
  - promoted files into always-enforced `CMD-022` coverage:
    - `src/infrastructure/__init__.py`
    - `src/infrastructure/factory.py`
    - `src/infrastructure/repositories/chroma_repository.py`
    - `src/infrastructure/services/cache_service.py`
    - `src/infrastructure/services/document_service.py`
    - `src/infrastructure/services/llm_service.py`
    - `src/infrastructure/services/vision_service.py`
  - removed those paths from `scripts/quality_black_debt_allowlist.txt`.
  - command-map/CI parity synchronized in:
    - `.github/workflows/ci.yml`
    - `docs/manifest/09_runbook.md`
    - `docs/manifest/11_ci.md`
  - tracking synchronized:
    - `docs/implementation/checklists/03_improvement_bets.md` (`IMP-18` checked)
    - `docs/implementation/checklists/02_milestones.md` (M9 infrastructure formatting outcome checked)
    - `docs/manifest/03_decisions.md` (`ADR-0027`)
- Verification anchors:
  - `./venv/bin/black src/infrastructure/__init__.py src/infrastructure/factory.py src/infrastructure/repositories/chroma_repository.py src/infrastructure/services/cache_service.py src/infrastructure/services/document_service.py src/infrastructure/services/llm_service.py src/infrastructure/services/vision_service.py` (pass)
  - `wc -l scripts/quality_black_debt_allowlist.txt` -> `66`
  - `rg -n "^src/infrastructure/(__init__\\.py|factory\\.py|repositories/chroma_repository\\.py|services/cache_service\\.py|services/document_service\\.py|services/llm_service\\.py|services/vision_service\\.py)$" scripts/quality_black_debt_allowlist.txt` -> no matches
  - `rg -n "src/infrastructure/__init__\\.py|src/infrastructure/factory\\.py|src/infrastructure/repositories/chroma_repository\\.py|src/infrastructure/repositories/iplan_repository\\.py|src/infrastructure/services/cache_service\\.py|src/infrastructure/services/document_service\\.py|src/infrastructure/services/llm_service\\.py|src/infrastructure/services/vision_service\\.py|CMD-022" .github/workflows/ci.yml docs/manifest/09_runbook.md docs/manifest/11_ci.md`
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` (post-`IMP-18` drift refresh).

## 2026-02-09 Update (Post-`IMP-18` prompt-03 rerun)
- Prompt executed: `prompt-03-alignment-review-gate` (manual rerun, no router script).
- Result:
  - alignment remains `ALIGNED_WITH_RISKS`.
  - `IMP-18` closure remains validated.
  - highest remaining corrective priority is now `OPP-01` artifact freshness cadence policy.
- Evidence anchors:
  - `./venv/bin/python -m pytest -m unit -q` -> `54 passed, 30 deselected`
  - `./venv/bin/python -m pytest -m integration -q` -> `23 passed, 1 skipped, 60 deselected`
  - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` -> `events=310`, `alerts=14`, `memory_used_ratio_p95=0.52`, `memory_signal_latest_source=memory_pressure_q`
  - `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json` -> `events_total=310`, `alerts_total=14`, `memory_signal_context.status=available`
  - `wc -l scripts/quality_black_debt_allowlist.txt` -> `66`
- Recommended immediate next prompt:
  - `prompt-11-docs-diataxis-release` for `OPP-01`, then `prompt-03-alignment-review-gate`.

## 2026-02-09 Update (`OPP-01` execution)
- Prompt executed: `prompt-11-docs-diataxis-release` (`OPP-01`, manual/no router script).
- Result:
  - artifact freshness cadence policy now has explicit ownership, triggers, and logging requirements in:
    - `docs/artifacts/README.md`
  - canonical freshness audit command was added to command map:
    - `docs/manifest/09_runbook.md` (`CMD-039`)
  - decision record added:
    - `docs/manifest/03_decisions.md` (`ADR-0028`)
  - artifact-alignment tracking synchronized:
    - `docs/implementation/checklists/08_artifact_feature_alignment.md` (`OPP-01` checked)
    - `docs/implementation/reports/artifact_feature_alignment.md`
- Verification anchors:
  - `rg -n "Refresh Cadence Policy|Primary owner|Logging requirements|CMD-039" docs/artifacts/README.md docs/manifest/09_runbook.md`
  - `python3 -c "import json,datetime,pathlib; items=json.loads(pathlib.Path('docs/artifacts/index.json').read_text(encoding='utf-8')).get('artifacts', []); cutoff=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=30)).isoformat(); stale=[i.get('id','unknown') for i in items if (not isinstance(i.get('retrieved_at'), str)) or (i.get('retrieved_at') < cutoff)]; print(f'artifacts_total={len(items)} stale_total={len(stale)}'); print('stale_ids=' + ','.join(stale) if stale else 'stale_ids=')"` (`artifacts_total=5`, `stale_total=0`)
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` (post-`OPP-01` drift refresh).

## 2026-02-09 Update (Post-`OPP-01` prompt-03 rerun)
- Prompt executed: `prompt-03-alignment-review-gate` (manual rerun, no router script).
- Result:
  - alignment remains `ALIGNED_WITH_RISKS`.
  - `OPP-01` closure remains validated.
  - highest remaining corrective priority is now `IMP-19` evidence-cadence ledger hardening.
- Evidence anchors:
  - `./venv/bin/python -m pytest -m unit -q` -> `54 passed, 30 deselected`
  - `./venv/bin/python -m pytest -m integration -q` -> `23 passed, 1 skipped, 60 deselected`
  - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` -> `events=312`, `alerts=14`, `memory_used_ratio_p95=0.52`
  - `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json` -> `events_total=312`, `alerts_total=14`
  - `python3 -c "import json,datetime,pathlib; items=json.loads(pathlib.Path('docs/artifacts/index.json').read_text(encoding='utf-8')).get('artifacts', []); cutoff=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=30)).isoformat(); stale=[i.get('id','unknown') for i in items if (not isinstance(i.get('retrieved_at'), str)) or (i.get('retrieved_at') < cutoff)]; print(f'artifacts_total={len(items)} stale_total={len(stale)}'); print('stale_ids=' + ','.join(stale) if stale else 'stale_ids=')"` -> `artifacts_total=5`, `stale_total=0`
  - `wc -l scripts/quality_black_debt_allowlist.txt` -> `66`
- Recommended immediate next prompt:
  - `prompt-11-docs-diataxis-release` for `IMP-19`, then `prompt-03-alignment-review-gate`.

## 2026-02-09 Update (`IMP-19` execution)
- Prompt executed: `prompt-11-docs-diataxis-release` (`IMP-19`, manual/no router script).
- Result:
  - recurring evidence cadence is centralized in canonical ledger:
    - `docs/implementation/checklists/09_evidence_cadence_ledger.md`
  - runbook and observability policies now point to ledger as the execution source of truth:
    - `docs/manifest/09_runbook.md`
    - `docs/manifest/07_observability.md`
  - tracking surfaces synchronized:
    - `docs/implementation/checklists/03_improvement_bets.md` (`IMP-19` checked)
    - `docs/implementation/checklists/02_milestones.md` (M9 evidence-cadence outcome checked)
    - `docs/manifest/03_decisions.md` (`ADR-0029`)
- Verification anchors:
  - `test -f docs/implementation/checklists/09_evidence_cadence_ledger.md`
  - `rg -n "CMD-036|CMD-029|CMD-038|CMD-039|IMP-19 bootstrap entry" docs/implementation/checklists/09_evidence_cadence_ledger.md docs/manifest/09_runbook.md docs/manifest/07_observability.md`
  - `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json` -> `events_total=304`, `alerts_total=13`, `memory_signal_context.status=available`
  - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` -> `events=304`, `alerts=13`, `memory_used_ratio_p95=0.52`
  - `(python3 scripts/build_vectordb_cli.py build --max-plans 1 --no-vision || true) && python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` -> build degraded (`HTTPError`) but snapshot captured `build` operation + saturation fields.
  - `python3 -c "import json,datetime,pathlib; items=json.loads(pathlib.Path('docs/artifacts/index.json').read_text(encoding='utf-8')).get('artifacts', []); cutoff=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=30)).isoformat(); stale=[i.get('id','unknown') for i in items if (not isinstance(i.get('retrieved_at'), str)) or (i.get('retrieved_at') < cutoff)]; print(f'artifacts_total={len(items)} stale_total={len(stale)}'); print('stale_ids=' + ','.join(stale) if stale else 'stale_ids=')"` -> `artifacts_total=5`, `stale_total=0`
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` (post-`IMP-19` drift refresh).

## 2026-02-09 Update (Post-`IMP-19` prompt-03 rerun)
- Prompt executed: `prompt-03-alignment-review-gate` (manual rerun, no router script).
- Result:
  - alignment remains `ALIGNED_WITH_RISKS`.
  - `IMP-19` closure remains validated with centralized cadence ledger evidence.
  - highest remaining corrective priority is now `OPP-02` external dependency health snapshot bundle.
- Evidence anchors:
  - `./venv/bin/python -m pytest -m unit -q` -> `54 passed, 30 deselected`
  - `./venv/bin/python -m pytest -m integration -q` -> `23 passed, 1 skipped, 60 deselected`
  - `./venv/bin/ruff check . --select E9,F63,F7 --exclude project-prompts` -> pass
  - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` -> `events=304`, `alerts=13`, `memory_used_ratio_p95=0.52`
  - `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json` -> `events_total=304`, `alerts_total=13`
  - `python3 -c "import json,datetime,pathlib; items=json.loads(pathlib.Path('docs/artifacts/index.json').read_text(encoding='utf-8')).get('artifacts', []); cutoff=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=30)).isoformat(); stale=[i.get('id','unknown') for i in items if (not isinstance(i.get('retrieved_at'), str)) or (i.get('retrieved_at') < cutoff)]; print(f'artifacts_total={len(items)} stale_total={len(stale)}'); print('stale_ids=' + ','.join(stale) if stale else 'stale_ids=')"` -> `artifacts_total=5`, `stale_total=0`
  - `wc -l scripts/quality_black_debt_allowlist.txt` -> `66`
- Recommended immediate next prompt:
  - `prompt-02-app-development-playbook` for `OPP-02`, then `prompt-03-alignment-review-gate`.

## 2026-02-09 Update (`OPP-02` execution)
- Prompt executed: `prompt-02-app-development-playbook` (`OPP-02`, manual/no router script).
- Result:
  - one-shot external dependency health snapshot bundle is now available:
    - `python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills`
  - command-map and triage docs updated:
    - `docs/manifest/09_runbook.md` (`CMD-040`)
    - `docs/troubleshooting.md`
    - `docs/reference/cli.md`
  - tracking surfaces synchronized:
    - `docs/implementation/checklists/08_artifact_feature_alignment.md` (`OPP-02` checked)
    - `docs/implementation/checklists/02_milestones.md` (external snapshot outcome checked)
    - `docs/implementation/reports/artifact_feature_alignment.md`
    - `docs/manifest/03_decisions.md` (`ADR-0030`)
- Verification anchors:
  - `python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills` -> `status=WARNING`, deterministic drills `PASS/PASS/PASS`
  - `./venv/bin/python -m pytest tests/unit/scripts/test_quick_status_external_snapshot.py -q` -> `3 passed`
  - `./venv/bin/python -m pytest tests/integration/iplan/test_external_dependency_drills.py -q` -> `5 passed`
  - `./venv/bin/python -m pytest tests/integration/data_contracts/test_boundary_payload_contracts.py tests/integration/iplan/test_iplan_sample_data_quality.py -q` -> `7 passed`
  - `rg -n "CMD-040|external --since-minutes|snapshot bundle" scripts/quick_status.py docs/manifest/09_runbook.md docs/troubleshooting.md docs/reference/cli.md`
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` (post-`OPP-02` drift refresh).

## 2026-02-09 Update (Post-`OPP-02` prompt-03 rerun)
- Prompt executed: `prompt-03-alignment-review-gate` (manual rerun, no router script).
- Result:
  - alignment remains `ALIGNED_WITH_RISKS`.
  - `OPP-02` closure remains validated.
  - highest remaining corrective priority is now `OPP-03` artifact-linked onboarding boundary notes.
- Evidence anchors:
  - `./venv/bin/python -m pytest -m unit -q` -> `57 passed, 30 deselected`
  - `./venv/bin/python -m pytest -m integration -q` -> `23 passed, 1 skipped, 63 deselected`
  - `./venv/bin/ruff check . --select E9,F63,F7 --exclude project-prompts` -> pass
  - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` -> `events=294`, `alerts=12`, `memory_used_ratio_p95=0.52`
  - `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json` -> `events_total=294`, `alerts_total=12`
  - `python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills` -> `status=WARNING`, deterministic drills `PASS/PASS/PASS`
  - `python3 -c "import json,datetime,pathlib; items=json.loads(pathlib.Path('docs/artifacts/index.json').read_text(encoding='utf-8')).get('artifacts', []); cutoff=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=30)).isoformat(); stale=[i.get('id','unknown') for i in items if (not isinstance(i.get('retrieved_at'), str)) or (i.get('retrieved_at') < cutoff)]; print(f'artifacts_total={len(items)} stale_total={len(stale)}'); print('stale_ids=' + ','.join(stale) if stale else 'stale_ids=')"` -> `artifacts_total=5`, `stale_total=0`
  - `wc -l scripts/quality_black_debt_allowlist.txt` -> `66`
- Recommended immediate next prompt:
  - `prompt-11-docs-diataxis-release` for `OPP-03`, then `prompt-03-alignment-review-gate`.

## 2026-02-09 Update (`OPP-03` execution)
- Prompt executed: `prompt-11-docs-diataxis-release` (`OPP-03`, manual/no router script).
- Result:
  - onboarding docs now include explicit `artifact:ART-EXT-*` boundary notes for iPlan/MAVAT/Gemini/pydoll/Chroma in:
    - `docs/README.md`
    - `docs/INDEX.md`
    - `docs/reference/configuration.md`
    - `docs/artifacts/README.md`
  - tracking surfaces synchronized:
    - `docs/implementation/checklists/08_artifact_feature_alignment.md` (`OPP-03` checked)
    - `docs/implementation/checklists/02_milestones.md` (onboarding artifact-link outcome checked)
    - `docs/manifest/03_decisions.md` (`ADR-0031`)
- Verification anchors:
  - `rg -n "artifact:ART-EXT-001|artifact:ART-EXT-002|artifact:ART-EXT-003|artifact:ART-EXT-004|artifact:ART-EXT-005" docs/README.md docs/INDEX.md docs/reference/configuration.md docs/artifacts/README.md`
  - `rg -n "External dependency boundaries|External Boundary Artifacts|Boundary Onboarding Map" docs/README.md docs/INDEX.md docs/reference/configuration.md docs/artifacts/README.md`
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` (post-`OPP-03` drift refresh).

## 2026-02-09 Update (Post-`OPP-03` prompt-03 rerun)
- Prompt executed: `prompt-03-alignment-review-gate` (manual rerun, no router script).
- Result:
  - alignment remains `ALIGNED_WITH_RISKS`.
  - `OPP-03` closure remains validated.
  - highest remaining corrective priority is now `CMD-040` warning/cadence hardening.
- Evidence anchors:
  - `./venv/bin/python -m pytest -m unit -q` -> `57 passed, 30 deselected`
  - `./venv/bin/python -m pytest -m integration -q` -> `23 passed, 1 skipped, 63 deselected`
  - `./venv/bin/ruff check . --select E9,F63,F7 --exclude project-prompts` -> pass
  - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` -> `events=295`, `alerts=12`, `regulation_query p95=3502.91ms`, `build p95=44985.39ms`, `memory_used_ratio_p95=0.52`
  - `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json` -> `events_total=295`, `alerts_total=12`
  - `python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills` -> `status=WARNING`, deterministic drills `PASS/PASS/PASS`
  - `python3 -c "import json,datetime,pathlib; items=json.loads(pathlib.Path('docs/artifacts/index.json').read_text(encoding='utf-8')).get('artifacts', []); cutoff=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=30)).isoformat(); stale=[i.get('id','unknown') for i in items if (not isinstance(i.get('retrieved_at'), str)) or (i.get('retrieved_at') < cutoff)]; print(f'artifacts_total={len(items)} stale_total={len(stale)}'); print('stale_ids=' + ','.join(stale) if stale else 'stale_ids=')"` -> `artifacts_total=5`, `stale_total=0`
  - `wc -l scripts/quality_black_debt_allowlist.txt` -> `66`
- Recommended immediate next prompt:
  - `prompt-02-app-development-playbook` for `CMD-040` warning/cadence hardening, then `prompt-03-alignment-review-gate`.

## 2026-02-09 Update (`CMD-040` warning/cadence hardening execution)
- Prompt executed: `prompt-02-app-development-playbook` (manual/no router script).
- Result:
  - `CMD-040` warning semantics are now context-specific in `scripts/quick_status.py`:
    - `boundary_degraded_signals_present`
    - `historical_runtime_window_noise`
    - `runtime_errors_or_alerts_unconfirmed`
  - recurring cadence policy now requires `CMD-040` capture in canonical ledger flow:
    - `docs/implementation/checklists/09_evidence_cadence_ledger.md`
    - `docs/manifest/09_runbook.md`
    - `docs/manifest/07_observability.md`
    - `docs/troubleshooting.md`
    - `docs/reference/cli.md`
  - decision tracking synchronized:
    - `docs/manifest/03_decisions.md` (`ADR-0032`)
- Verification anchors:
  - `./venv/bin/python -m pytest tests/unit/scripts/test_quick_status_external_snapshot.py -q` -> `5 passed`
  - `./venv/bin/ruff check scripts/quick_status.py tests/unit/scripts/test_quick_status_external_snapshot.py --select E9,F63,F7` -> pass
  - `python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills` -> `status=WARNING`, `warning_context=historical_runtime_window_noise`, deterministic drills `PASS/PASS/PASS`
  - `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json` -> `events_total=286`, `alerts_total=12`
  - `(python3 scripts/build_vectordb_cli.py build --max-plans 1 --no-vision || true) && python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` -> build degraded (`HTTPError`) but emitted build telemetry + saturation evidence
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` (post-`CMD-040` hardening drift refresh).

## 2026-02-09 Update (Post-`CMD-040` prompt-03 rerun)
- Prompt executed: `prompt-03-alignment-review-gate` (manual rerun, no router script).
- Result:
  - alignment remains `ALIGNED_WITH_RISKS`.
  - `CMD-040` cadence + warning-interpretation hardening remains validated.
  - highest remaining corrective priority is now onboarding artifact-link guardrail command-map coverage.
- Evidence anchors:
  - `./venv/bin/python -m pytest -m unit -q` -> `59 passed, 30 deselected`
  - `./venv/bin/python -m pytest -m integration -q` -> `23 passed, 1 skipped, 65 deselected`
  - `./venv/bin/ruff check . --select E9,F63,F7 --exclude project-prompts` -> pass
  - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` -> `events=286`, `alerts=12`, `regulation_query p95=3502.91ms`, `build p95=44985.39ms`, `memory_used_ratio_p95=0.59`
  - `python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills` -> `status=WARNING`, `warning_context=historical_runtime_window_noise`, deterministic drills `PASS/PASS/PASS`
  - `python3 -c "import json,datetime,pathlib; items=json.loads(pathlib.Path('docs/artifacts/index.json').read_text(encoding='utf-8')).get('artifacts', []); cutoff=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=30)).isoformat(); stale=[i.get('id','unknown') for i in items if (not isinstance(i.get('retrieved_at'), str)) or (i.get('retrieved_at') < cutoff)]; print(f'artifacts_total={len(items)} stale_total={len(stale)}'); print('stale_ids=' + ','.join(stale) if stale else 'stale_ids=')"` -> `artifacts_total=5`, `stale_total=0`
  - `wc -l scripts/quality_black_debt_allowlist.txt` -> `66`
- Recommended immediate next prompt:
  - `prompt-11-docs-diataxis-release` for onboarding artifact-link guardrail command-map coverage, then `prompt-03-alignment-review-gate`.

## 2026-02-09 Update (`CMD-041` + narrowed-window docs hardening execution)
- Prompt executed: `prompt-11-docs-diataxis-release` (manual/no router script).
- Result:
  - canonical onboarding/reference citation guardrail command added:
    - `docs/manifest/09_runbook.md` (`CMD-041`)
  - onboarding/reference docs now explicitly point to the guardrail command:
    - `docs/reference/cli.md`
    - `docs/README.md`
    - `docs/INDEX.md`
  - decision tracking synchronized:
    - `docs/manifest/03_decisions.md` (`ADR-0033`)
  - historical-noise warning handling hardened with explicit narrowed-window evidence requirements:
    - `docs/implementation/checklists/09_evidence_cadence_ledger.md`
    - `docs/manifest/09_runbook.md`
    - `docs/troubleshooting.md`
- Verification anchors:
  - `for file in docs/README.md docs/INDEX.md docs/reference/configuration.md docs/artifacts/README.md; do for id in artifact:ART-EXT-001 artifact:ART-EXT-002 artifact:ART-EXT-003 artifact:ART-EXT-004 artifact:ART-EXT-005; do rg -q "$id" "$file" || { echo "$file missing $id"; exit 1; }; done; done; echo "onboarding_artifact_links_ok files=4 ids=5"` -> `onboarding_artifact_links_ok files=4 ids=5`
  - `python3 scripts/quick_status.py external --since-minutes 60 --events-limit 1000 --alerts-limit 500 --run-drills` -> `status=WARNING`, `warning_context=historical_runtime_window_noise`, deterministic drills `PASS/PASS/PASS`
  - `python3 scripts/observability_cli.py alerts --since-minutes 60 --limit 50`
  - `python3 scripts/observability_cli.py events --outcome error --since-minutes 60 --limit 100`
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` (post-`CMD-041` drift refresh).

## 2026-02-09 Update (Post-`CMD-041` prompt-03 rerun)
- Prompt executed: `prompt-03-alignment-review-gate` (manual rerun, no router script).
- Result:
  - alignment remains `ALIGNED_WITH_RISKS`.
  - onboarding citation guardrail and narrowed-window confirmation corrections are validated.
  - highest remaining corrective priority is now code-level warning-follow-up regression coverage (+ output warning cleanup).
- Evidence anchors:
  - `./venv/bin/python -m pytest -m unit -q` -> `59 passed, 30 deselected`
  - `./venv/bin/python -m pytest -m integration -q` -> `23 passed, 1 skipped, 65 deselected`
  - `./venv/bin/ruff check . --select E9,F63,F7 --exclude project-prompts` -> pass
  - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` -> `events=286`, `alerts=11`, `regulation_query p95=3502.91ms`, `build p95=44985.39ms`, `memory_used_ratio_p95=0.59`
  - `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json` -> `events_total=286`, `alerts_total=11`
  - `python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills` -> `status=WARNING`, `warning_context=historical_runtime_window_noise`, deterministic drills `PASS/PASS/PASS`
  - `wc -l scripts/quality_black_debt_allowlist.txt` -> `66`
- Recommended immediate next prompt:
  - `prompt-02-app-development-playbook`, then `prompt-03-alignment-review-gate`.

## 2026-02-09 Update (warning-rendering regression + output-noise cleanup execution)
- Prompt executed: `prompt-02-app-development-playbook` (manual/no router script).
- Result:
  - snapshot-output regression coverage added for non-boundary warning branches in:
    - `tests/unit/scripts/test_quick_status_external_snapshot.py`
  - pydantic startup warning noise removed from `CMD-040` by settings model-config hardening in:
    - `src/config.py`
  - tracking synchronized:
    - `docs/manifest/03_decisions.md` (`ADR-0034`)
    - `docs/implementation/checklists/02_milestones.md` (`M10` outcomes checked)
- Verification anchors:
  - `./venv/bin/python -m pytest tests/unit/scripts/test_quick_status_external_snapshot.py -q` -> `7 passed`
  - `./venv/bin/ruff check src/config.py tests/unit/scripts/test_quick_status_external_snapshot.py --select E9,F63,F7` -> pass
  - `./venv/bin/black --check src/config.py tests/unit/scripts/test_quick_status_external_snapshot.py` -> pass
  - `if python3 scripts/quick_status.py external --since-minutes 60 --events-limit 200 --alerts-limit 200 --run-drills 2>&1 | rg -n "protected namespace|UserWarning"; then echo "warning_noise_detected"; else echo "warning_noise_absent"; fi` -> `warning_noise_absent`
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` (post-packet drift refresh).

## 2026-02-09 Update (Post-regression prompt-03 rerun)
- Prompt executed: `prompt-03-alignment-review-gate` (manual rerun, no router script).
- Result:
  - alignment remains `ALIGNED_WITH_RISKS`.
  - M10 is fully complete.
  - highest remaining correction is docs-only release-readiness wiring for `CMD-041` (`M11`).
- Evidence anchors:
  - `./venv/bin/python -m pytest -m unit -q` -> `61 passed, 30 deselected`
  - `./venv/bin/python -m pytest -m integration -q` -> `23 passed, 1 skipped, 67 deselected`
  - `./venv/bin/ruff check . --select E9,F63,F7 --exclude project-prompts` -> pass
  - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` -> `events=266`, `alerts=9`, `regulation_query p95=3570.85ms`, `build p95=44985.39ms`, `memory_used_ratio_p95=0.59`
  - `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json` -> `events_total=266`, `alerts_total=9`
  - `python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills` -> `status=WARNING`, `warning_context=historical_runtime_window_noise`, deterministic drills `PASS/PASS/PASS`
  - `for file in docs/README.md docs/INDEX.md docs/reference/configuration.md docs/artifacts/README.md; do for id in artifact:ART-EXT-001 artifact:ART-EXT-002 artifact:ART-EXT-003 artifact:ART-EXT-004 artifact:ART-EXT-005; do rg -q "$id" "$file" || { echo "$file missing $id"; exit 1; }; done; done; echo "onboarding_artifact_links_ok files=4 ids=5"` -> `onboarding_artifact_links_ok files=4 ids=5`
- Recommended immediate next prompt:
  - `prompt-11-docs-diataxis-release`, then `prompt-03-alignment-review-gate`.

## 2026-02-09 Update (release-readiness `CMD-041` wiring execution)
- Prompt executed: `prompt-11-docs-diataxis-release` (manual/no router script).
- Result:
  - release readiness checklist now requires `CMD-041` verification and expected success output in:
    - `docs/implementation/checklists/06_release_readiness.md`
  - release workflow and CI manifest now map `CMD-041` as a required pre-tag docs guardrail:
    - `docs/reference/release_workflow.md`
    - `docs/manifest/11_ci.md`
  - runbook release packet validation path now includes `CMD-041`:
    - `docs/manifest/09_runbook.md`
  - decision + milestone mapping synchronized:
    - `docs/manifest/03_decisions.md` (`ADR-0035`)
    - `docs/implementation/checklists/02_milestones.md` (`M11` checked; `M12` opened)
- Verification anchors:
  - `rg -n "CMD-041|onboarding artifact-link|citation guardrail" docs/implementation/checklists/06_release_readiness.md docs/reference/release_workflow.md docs/manifest/11_ci.md docs/manifest/09_runbook.md`
  - `for file in docs/README.md docs/INDEX.md docs/reference/configuration.md docs/artifacts/README.md; do for id in artifact:ART-EXT-001 artifact:ART-EXT-002 artifact:ART-EXT-003 artifact:ART-EXT-004 artifact:ART-EXT-005; do rg -q "$id" "$file" || { echo "$file missing $id"; exit 1; }; done; done; echo "onboarding_artifact_links_ok files=4 ids=5"` -> `onboarding_artifact_links_ok files=4 ids=5`
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` (post-packet drift refresh).

## 2026-02-09 Update (Post-release-wiring prompt-03 rerun)
- Prompt executed: `prompt-03-alignment-review-gate` (manual rerun, no router script).
- Result:
  - alignment remains `ALIGNED_WITH_RISKS`.
  - M11 corrections are closed.
  - highest next packet is re-ranking (`prompt-14`) before selecting the next M12 implementation bet.
- Evidence anchors:
  - `./venv/bin/python -m pytest -m unit -q` -> `61 passed, 30 deselected`
  - `./venv/bin/python -m pytest -m integration -q` -> `23 passed, 1 skipped, 67 deselected`
  - `./venv/bin/ruff check . --select E9,F63,F7 --exclude project-prompts` -> pass
  - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` -> `events=276`, `alerts=9`, `regulation_query p95=3502.91ms`, `build p95=44985.39ms`, `memory_used_ratio_p95=0.59`
  - `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json` -> `events_total=276`, `alerts_total=9`
  - `python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills` -> `status=WARNING`, `warning_context=historical_runtime_window_noise`, deterministic drills `PASS/PASS/PASS`
  - `wc -l scripts/quality_black_debt_allowlist.txt` -> `66`
- Recommended immediate next prompt:
  - `prompt-14-improvement-direction-bet-loop`, then `prompt-02-app-development-playbook`, then `prompt-03-alignment-review-gate`.

## 2026-02-09 Update (Post-M11 prompt-14 rerun)
- Prompt executed: `prompt-14-improvement-direction-bet-loop` (manual rerun, no router script).
- Candidate re-ranking outcome:
  1. IMP-20 release-workflow `CMD-041` automation (selected now).
  2. IMP-21 boundary snapshot timeout-noise triage tightening.
  3. IMP-22 post-M12 bet refresh and convergence guardrail.
- Why this ranking now:
  - docs-level release guardrail wiring is complete, but enforcement is still manual and can drift under tag pressure.
  - warning windows remain influenced by recurring build timeout sev1 noise, so operator first-pass decisions still need tighter guidance.
  - repeated local optimization loops are a residual process risk without explicit post-M12 convergence checks.
- Selected immediate direction:
  - IMP-20 release-workflow `CMD-041` automation.
- Recommended immediate next prompt:
  - `prompt-02-app-development-playbook` for IMP-20, then `prompt-03-alignment-review-gate` once.

## 2026-02-09 Update (IMP-20 execution)
- Prompt executed: `prompt-02-app-development-playbook` (manual/no router script).
- Result:
  - release validation workflow now enforces onboarding/reference citation guardrail (`CMD-041` semantics) before publish path:
    - `.github/workflows/release.yml`
  - release docs updated from manual to automated guardrail mapping:
    - `docs/reference/release_workflow.md`
    - `docs/manifest/11_ci.md`
  - milestone/decision tracking synchronized:
    - `docs/implementation/checklists/02_milestones.md` (`M12` automation outcome checked)
    - `docs/manifest/03_decisions.md` (`ADR-0036`)
- Verification anchors:
  - `rg -n "CMD-041|onboarding_artifact_links_ok|artifact:ART-EXT-001" .github/workflows/release.yml docs/reference/release_workflow.md docs/manifest/11_ci.md`
  - `for file in docs/README.md docs/INDEX.md docs/reference/configuration.md docs/artifacts/README.md; do for id in artifact:ART-EXT-001 artifact:ART-EXT-002 artifact:ART-EXT-003 artifact:ART-EXT-004 artifact:ART-EXT-005; do rg -q "$id" "$file" || { echo "$file missing $id"; exit 1; }; done; done; echo "onboarding_artifact_links_ok files=4 ids=5"` -> `onboarding_artifact_links_ok files=4 ids=5`
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` (post-IMP-20 drift refresh).

## 2026-02-09 Update (IMP-21 execution)
- Prompt executed: `prompt-02-app-development-playbook` (manual/no router script).
- Result:
  - external snapshot warning classification now explicitly distinguishes recurring build-timeout sev1 windows:
    - `scripts/quick_status.py` now emits `warning_context=historical_build_timeout_sev1_noise` when warning signals are dominated by `build` timeout errors and deterministic drills pass.
    - snapshot output now includes `warning_noise_profile` counters for first-pass operator interpretation.
  - warning-follow-up guidance now separates commands for build-timeout dominance vs mixed historical noise:
    - build-timeout dominant windows route through narrowed-window `CMD-040` + `CMD-026`/`CMD-028`.
    - generic historical noise keeps narrowed-window `CMD-040` + `CMD-025`/`CMD-028`.
  - docs and milestone/bet tracking are synchronized:
    - `docs/troubleshooting.md`
    - `docs/manifest/07_observability.md`
    - `docs/manifest/09_runbook.md`
    - `docs/reference/cli.md`
    - `docs/implementation/checklists/02_milestones.md` (M12 timeout-noise outcome checked)
    - `docs/implementation/checklists/03_improvement_bets.md` (IMP-21 checked)
- Verification anchors:
  - `./venv/bin/python -m pytest tests/unit/scripts/test_quick_status_external_snapshot.py -q` -> `11 passed`
  - `python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills` -> `status=WARNING`, `warning_context=historical_build_timeout_sev1_noise`, `warning_noise_profile: build_timeout_error_events=4 non_build_error_events=0 build_timeout_sev1_alerts=4 non_build_sev1_alerts=0`
  - `rg -n "historical_build_timeout_sev1_noise|warning_noise_profile|CMD-026|CMD-028" scripts/quick_status.py docs/troubleshooting.md docs/manifest/07_observability.md docs/manifest/09_runbook.md docs/reference/cli.md`
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` (post-IMP-21 drift refresh).
- Follow-up:
  - `prompt-14-improvement-direction-bet-loop` for IMP-22 convergence guardrail selection/closure.

## 2026-02-09 Update (IMP-22 convergence guardrail closure)
- Prompt executed: `prompt-14-improvement-direction-bet-loop` (manual rerun, no router script).
- Result:
  - post-M12 reranking now includes an explicit convergence guardrail for immediate-route selection:
    - unresolved-outcome delta check:
      - do not repeat the same immediate packet route when unresolved outcome set is unchanged.
    - repeat-loop stop condition:
      - if the same immediate route appears in two consecutive reranks without a closed outcome, force route divergence.
    - forced divergence sequence:
      - run `prompt-03` once, then re-rank excluding the last-selected route until an unresolved outcome changes state.
  - tracking synchronized:
    - `docs/implementation/checklists/03_improvement_bets.md` (`IMP-22` checked)
    - `docs/implementation/checklists/02_milestones.md` (M12 convergence-guardrail outcome checked)
    - `docs/implementation/checklists/07_alignment_review.md`
    - `docs/implementation/reports/alignment_review.md`
- Verification anchors:
  - `rg -n "convergence guardrail|repeat-loop|unresolved-outcome delta|IMP-22" docs/implementation/reports/improvement_directions.md docs/implementation/checklists/03_improvement_bets.md docs/implementation/checklists/02_milestones.md`
  - `rg -n "Recommended immediate next prompt" docs/implementation/reports/improvement_directions.md docs/implementation/checklists/07_alignment_review.md docs/implementation/reports/alignment_review.md`
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` (post-IMP-22 drift refresh).

## 2026-02-09 Update (Post-IMP-22 prompt-03 rerun)
- Prompt executed: `prompt-03-alignment-review-gate` (manual rerun, no router script).
- Result:
  - alignment remains `ALIGNED_WITH_RISKS`.
  - M12 outcomes are fully closed (`IMP-20`, `IMP-21`, `IMP-22`).
  - routing focus moves from implementation-loop closure to cadence/evidence follow-through.
- Recommended immediate next prompt:
  - `prompt-11-docs-diataxis-release` only if cadence-ledger capture or release-doc guardrail drift appears.
- Follow-up:
  - otherwise continue normal evidence cadence and run `prompt-03` on the next scheduled checkpoint.

## 2026-02-09 Update (Post-IMP-22 cadence evidence capture via prompt-11)
- Prompt executed: `prompt-11-docs-diataxis-release` (manual/no router script).
- Result:
  - closed the remaining post-M12 cadence correction by recording narrowed-window follow-through evidence for `historical_build_timeout_sev1_noise` in:
    - `docs/implementation/checklists/09_evidence_cadence_ledger.md`
  - ledger template now explicitly includes context-specific narrowed-window evidence requirement for:
    - `historical_build_timeout_sev1_noise` -> `CMD-040` narrowed window + `CMD-026`/`CMD-028`
  - captured evidence snapshot:
    - 180-minute `CMD-040`: `status=WARNING`, `warning_context=historical_build_timeout_sev1_noise`, `warning_noise_profile: build_timeout_error_events=4 non_build_error_events=0 build_timeout_sev1_alerts=4 non_build_sev1_alerts=0`
    - 60-minute narrowed `CMD-040`: `status=HEALTHY`, `events=60`, `alerts=1`
    - narrowed-window triage slices:
      - `CMD-026` -> `No matching events.`
      - `CMD-028` -> `No matching events.`
- Recommended immediate next prompt:
  - `prompt-03-alignment-review-gate` (post-cadence-confirmation refresh).
- Follow-up:
  - `prompt-11-docs-diataxis-release` only if release-doc or cadence-ledger drift appears again.

## 2026-02-09 Update (Post-cadence prompt-03 rerun)
- Prompt executed: `prompt-03-alignment-review-gate` (manual rerun, no router script).
- Result:
  - alignment remains `ALIGNED_WITH_RISKS`.
  - no M12 implementation outcomes remain open and routing remains converged (no immediate-route loop regression observed).
  - cadence follow-through evidence is now embedded in the canonical ledger and does not require an additional implementation packet.
- Evidence anchors:
  - `./venv/bin/python -m pytest -m unit -q` -> `65 passed, 30 deselected`
  - `./venv/bin/python -m pytest -m integration -q` -> `23 passed, 1 skipped, 71 deselected`
  - `./venv/bin/ruff check . --select E9,F63,F7 --exclude project-prompts` -> pass
  - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` -> `events=232`, `alerts=7`, `regulation_query p95=3467.34ms`, `build p95=43434.35ms`, `memory_used_ratio_p95=0.59`
  - `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json` -> `events_total=232`, `alerts_total=7`, `memory_signal_context.status=available`
  - `python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills` -> `status=WARNING`, `warning_context=historical_build_timeout_sev1_noise`, `warning_noise_profile: build_timeout_error_events=3 non_build_error_events=0 build_timeout_sev1_alerts=3 non_build_sev1_alerts=0`, deterministic drills `PASS/PASS/PASS`
  - `python3 scripts/check_dependency_sync.py --requirements requirements.txt --dev-requirements requirements-dev.txt --lock requirements.lock --doc docs/reference/dependencies.md` -> pass
  - `python3 project-prompts/scripts/prompts_manifest.py --check` -> pass
  - `python3 project-prompts/scripts/system_integrity.py --mode prompt_pack --root project-prompts` -> pass
- Recommended immediate next prompt:
  - `prompt-11-docs-diataxis-release` only if release-doc or cadence-ledger drift appears.
- Follow-up:
  - otherwise continue scheduled cadence captures and run `prompt-03` at the next checkpoint.

## 2026-02-09 Update (Post-docs drift prompt-03 rerun)
- Prompt executed: `prompt-03-alignment-review-gate` (manual rerun, no router script).
- Result:
  - alignment remains `ALIGNED_WITH_RISKS`.
  - M11/M12 implementation outcomes remain closed; no mandatory implementation packet reopened.
  - residual drift is process-oriented (routing freshness + cadence hygiene), not a blocked feature/correctness gap.
- Evidence anchors:
  - `./venv/bin/python -m pytest -m unit -q` -> `65 passed, 30 deselected`
  - `./venv/bin/python -m pytest -m integration -q` -> `23 passed, 1 skipped, 71 deselected`
  - `./venv/bin/ruff check . --select E9,F63,F7 --exclude project-prompts` -> pass
  - `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` -> `events=222`, `alerts=7`, `regulation_query p95=3772.02ms`, `build p95=43434.35ms`, `memory_used_ratio_p95=0.59`
  - `python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills` -> `status=WARNING`, `warning_context=historical_build_timeout_sev1_noise`, deterministic drills `PASS/PASS/PASS`
  - `python3 scripts/quick_status.py external --since-minutes 60 --events-limit 1000 --alerts-limit 500 --run-drills` -> `status=HEALTHY`, `events=50`, `alerts=0`, deterministic drills `PASS/PASS/PASS`
  - `python3 scripts/observability_cli.py events --operation build --since-minutes 60 --limit 100` -> `No matching events.`
  - `python3 scripts/observability_cli.py events --outcome error --since-minutes 60 --limit 100` -> `No matching events.`
  - `python3 scripts/observability_cli.py alerts --since-minutes 60 --limit 100` -> `No matching alerts.`
- Recommended immediate next prompt:
  - `prompt-14-improvement-direction-bet-loop` (refresh next-cycle ranking and pick a non-redundant bounded packet).
- Follow-up:
  - execute the selected implementation/docs packet (`prompt-02` or `prompt-11`) from the rerank output.

## 2026-03-11 Update (Planner UX redesign packet)
- Trigger: direct user request for a Figma-backed planner UX audit, redesign, and implementation-ready handoff.
- New direction added:
  - `IMP-23 - Planner UX Redesign and Design-System Handoff`
- Why it is worth doing now:
  - the current React product is useful but visually fragmented
  - planner workflow hierarchy was weaker than the product value deserved
  - route-level consistency and state-surface quality were clear UX leverage points
- Implemented in this packet:
  - planner-first route redesign across `/`, `/map`, `/analyzer`, and `/data`
  - new stylesheet and app shell aligned to Workspace / Investigation / Feasibility / Operations
  - updated Playwright coverage to the redesigned hierarchy
  - dedicated packet artifacts:
    - `docs/implementation/reports/dashboard_ux_audit_redesign.md`
    - `docs/implementation/checklists/10_dashboard_redesign.md`
- Figma artifacts completed:
  - file: `https://www.figma.com/design/d6ExX1CAGJtmV6HzA1j73D`
  - direct redesign workspace capture (`node 1:2`)
  - direct current-state workspace capture (`node 2:2`)
  - structured `/figma-handoff` board capture (`node 3:2`)
- Remaining truth:
  - packet deliverables are complete
  - later cleanup can extract more frontend components if this redesign becomes the new baseline for additional work
- Recommended immediate next prompt:
  - none required for code delivery; run `prompt-03` only if prompt-pack routing discipline is being resumed
