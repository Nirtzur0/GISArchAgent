# Alignment Review Checklist

- Review date: 2026-02-09
- Stage: Cool-down (Phase 5 post-docs drift packet prompt-03 checkpoint)
- Verdict: ALIGNED_WITH_RISKS

## Required Questions
- [x] Are we still building the same thing defined by Core Objective?
  - Answer: yes.
  - Evidence: `docs/manifest/00_overview.md` objective/non-goals/user journeys still match runtime entrypoints (`app.py`, `scripts/data_cli.py`, `scripts/build_vectordb_cli.py`, `src/application/services/*`).

- [x] Is the main user journey usable end-to-end right now?
  - Answer: yes, with intentional live-network gating.
  - Evidence: marker suites are green in the current checkpoint (`65 unit passed`; `23 integration passed`, `1 skipped`), and boundary snapshot drills remain deterministic `PASS/PASS/PASS`.

- [x] Are we measuring the right success metrics from the objective?
  - Answer: mostly.
  - Evidence: observability/dashboard/boundary snapshots are active (`CMD-029`, `CMD-036`, `CMD-040`), release-doc citation guardrail is enforced (`CMD-041`), and lock/docs integrity checks pass.

- [x] Are we spending meaningful effort on explicit non-goals?
  - Answer: mostly no.
  - Evidence: recent packets stay in reliability/docs/operability scope; no hosted-SaaS/service-split work was introduced.

## Evidence-backed Misalignment Checklist
- [x] Release workflow enforces onboarding/reference citation guardrail (`CMD-041`) before publish path.
- [x] Legacy docs drift packet is closed (`docs/RUN_GUIDE.md` rewritten, stale release claim removed, metadata docs added).
- [x] Warning triage semantics distinguish recurring build-timeout historical noise (`historical_build_timeout_sev1_noise`) from boundary degradation.
- [ ] Next-cycle packet selection has not been re-ranked after this checkpoint (risk: repeating gate-only loops).
- [ ] Cadence captures remain manual and can drift if not explicitly scheduled.

## Top 3 Next Corrections
- [ ] Correction 1: run next-cycle rerank and select a fresh bounded implementation/docs packet.
  - Owner type: maintainer
  - Effort: S
  - Target files: `docs/implementation/reports/improvement_directions.md`, `docs/implementation/checklists/03_improvement_bets.md`, `docs/implementation/checklists/02_milestones.md`
  - Acceptance signal: a non-redundant immediate packet is selected and mapped to milestones/bets.

- [ ] Correction 2: keep release-validation and citation guardrail mapping synchronized after docs edits.
  - Owner type: contributor
  - Effort: S
  - Target files: `docs/implementation/checklists/06_release_readiness.md`, `docs/reference/release_workflow.md`, `docs/manifest/11_ci.md`, `.github/workflows/release.yml`
  - Acceptance signal: `CMD-041` mapping remains unchanged and verifiable in docs + release workflow.

- [ ] Correction 3: keep weekly cadence evidence and narrowed-window follow-through current.
  - Owner type: maintainer
  - Effort: S
  - Target files: `docs/implementation/checklists/09_evidence_cadence_ledger.md`
  - Acceptance signal: latest ledger entry includes `CMD-036`/`CMD-029`/`CMD-039`/`CMD-040`, plus narrowed-window evidence when warning contexts appear.

## Packet Mapping
- M11 mapping:
  - completed: release-readiness guardrail wiring for `CMD-041`.
  - open: no remaining outcomes.
- M12 mapping:
  - completed: release workflow `CMD-041` automation.
  - completed: timeout-noise triage tightening (`IMP-21`).
  - completed: convergence guardrail rerank (`IMP-22`).
- Immediate packet recommendation:
  - execute `prompt-14-improvement-direction-bet-loop` to select a new non-redundant packet and avoid repeating checkpoint-only loops.
- Follow-up packet recommendation:
  - execute `prompt-02-app-development-playbook` or `prompt-11-docs-diataxis-release` based on the selected top bet.

## Re-run Evidence
- `./venv/bin/python -m pytest -m unit -q` (`65 passed, 30 deselected`)
- `./venv/bin/python -m pytest -m integration -q` (`23 passed, 1 skipped, 71 deselected`)
- `./venv/bin/ruff check . --select E9,F63,F7 --exclude project-prompts` (pass)
- `python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500` (`events=222`, `alerts=7`, `regulation_query p95=3772.02ms`, `build p95=43434.35ms`, `memory_used_ratio_p95=0.59`)
- `python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json` (`events_total=222`, `alerts_total=7`, `memory_signal_context.status=available`)
- `python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills` (`status=WARNING`, `warning_context=historical_build_timeout_sev1_noise`, `warning_noise_profile: build_timeout_error_events=3 non_build_error_events=0 build_timeout_sev1_alerts=3 non_build_sev1_alerts=0`, deterministic drills `PASS/PASS/PASS`)
- `python3 scripts/quick_status.py external --since-minutes 60 --events-limit 1000 --alerts-limit 500 --run-drills` (`status=HEALTHY`, `events=50`, `alerts=0`, deterministic drills `PASS/PASS/PASS`)
- `python3 scripts/observability_cli.py events --operation build --since-minutes 60 --limit 100` (`No matching events.`)
- `python3 scripts/observability_cli.py events --outcome error --since-minutes 60 --limit 100` (`No matching events.`)
- `python3 scripts/observability_cli.py alerts --since-minutes 60 --limit 100` (`No matching alerts.`)
- `rg -n "convergence guardrail|repeat-loop|unresolved-outcome delta|IMP-22" docs/implementation/reports/improvement_directions.md docs/implementation/checklists/03_improvement_bets.md docs/implementation/checklists/02_milestones.md`
- `rg -n "CMD-041|onboarding_artifact_links_ok|artifact:ART-EXT-001" .github/workflows/release.yml docs/reference/release_workflow.md docs/manifest/11_ci.md`
- `python3 scripts/check_dependency_sync.py --requirements requirements.txt --dev-requirements requirements-dev.txt --lock requirements.lock --doc docs/reference/dependencies.md` (pass)
- `python3 project-prompts/scripts/prompts_manifest.py --check && echo prompts_manifest_ok` (`prompts_manifest_ok`)
- `python3 project-prompts/scripts/system_integrity.py --mode prompt_pack --root project-prompts` (`System integrity checks passed.`)
- `for file in docs/README.md docs/INDEX.md docs/reference/configuration.md docs/artifacts/README.md; do for id in artifact:ART-EXT-001 artifact:ART-EXT-002 artifact:ART-EXT-003 artifact:ART-EXT-004 artifact:ART-EXT-005; do rg -q "$id" "$file" || { echo "$file missing $id"; exit 1; }; done; done; echo "onboarding_artifact_links_ok files=4 ids=5"` (`onboarding_artifact_links_ok files=4 ids=5`)
