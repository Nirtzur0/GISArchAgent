# Prompt Execution Plan

- Generated: `2026-02-08T22:28:24Z`
- Method: manual prompt-first routing (`project-prompts/prompt-00-prompt-routing-plan.md`), no router script.
- Target repo: `/Users/nirtzur/Documents/projects/GISArchAgent`
- Inferred cycle stage: `Cool-down` (reliability/release packet in progress)
- Legacy phase hint: `phase_5`
- Appetite: `medium`

## Repo State Signals (Evidence)
- Objective and baseline docs exist: `docs/manifest/00_overview.md`, `docs/implementation/checklists/01_plan.md`.
- M1 reliability packet is still open in milestones: `docs/implementation/checklists/02_milestones.md`.
- CI baseline implementation was started but not yet fully synced in status/checklists: `.github/workflows/ci.yml`, `docs/manifest/11_ci.md`, `docs/implementation/00_status.md`.
- Tests are currently stable with marker-based runs recorded in worklog: `docs/implementation/03_worklog.md`.
- Prompt-pack updated to latest submodule commit; old router-based command references are stale and should be retired: `project-prompts/`, `docs/manifest/09_runbook.md`.

## Candidate Scoring (Prompt-00 Rubric)
Scoring formula: `Urgency + Coverage Impact + Evidence Strength - Effort Penalty`.

| Prompt ID | Category | Urgency (0-5) | Coverage (0-5) | Evidence (0-5) | Effort Penalty (0-3) | Total | Decision |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `prompt-02-app-development-playbook` | build | 5 | 5 | 5 | 2 | 13 | **Selected now** |
| `prompt-03-alignment-review-gate` | alignment | 2 | 3 | 4 | 1 | 8 | Deferred (run after M1 sync) |
| `prompt-14-improvement-direction-bet-loop` | improvement | 2 | 4 | 3 | 1 | 8 | Exploration (next cycle candidate) |
| `prompt-10-tests-stabilization-loop` | tests | 2 | 3 | 4 | 2 | 7 | Deferred (suite already green) |
| `prompt-11-docs-diataxis-release` | docs/release | 2 | 3 | 3 | 1 | 7 | Deferred (mostly complete) |
| `prompt-04-architecture-coherence-loop` | architecture | 2 | 3 | 3 | 2 | 6 | Deferred (M2 scope) |
| `prompt-15-artifact-feature-alignment-gate` | artifact_alignment | 1 | 3 | 2 | 1 | 5 | Exploration |
| `prompt-05-readme-onboarding` | docs | 1 | 2 | 3 | 1 | 5 | Not now |
| `prompt-09-tests-refactor-suite` | tests | 1 | 2 | 3 | 2 | 4 | Not now |
| `prompt-06-ui-e2e-verification-loop` | ui | 1 | 2 | 2 | 3 | 2 | Not now |

## Selected Immediate Prompt IDs
1. `prompt-02-app-development-playbook`

## Deferred / Not-Now Prompt IDs
- `prompt-03-alignment-review-gate`
- `prompt-04-architecture-coherence-loop`
- `prompt-10-tests-stabilization-loop`
- `prompt-11-docs-diataxis-release`
- `prompt-09-tests-refactor-suite`
- `prompt-05-readme-onboarding`
- `prompt-06-ui-e2e-verification-loop`

## Exploration Prompt IDs (Relevant but not selected now)
- `prompt-14-improvement-direction-bet-loop`
- `prompt-15-artifact-feature-alignment-gate`
- `prompt-03-alignment-review-gate`
- `prompt-04-architecture-coherence-loop`

## Selected Packet (Now)
### `prompt-02-app-development-playbook`
- Why now:
  - It directly closes the active M1 reliability packet and removes the highest known delivery risk (missing CI baseline sync).
  - It is the only prompt that intentionally combines code + docs + checklist/status/worklog synchronization for this scope.
- Dependencies:
  - `charter-prompt-system.md`
  - `charter-app-implementation-system.md`
  - `charter-docs-system.md`
  - `guardrails-repo-change.md`
- Expected deliverables for this packet:
  - `.github/workflows/ci.yml`
  - `docs/manifest/11_ci.md`
  - `docs/manifest/09_runbook.md`
  - `docs/reference/release_workflow.md`
  - `docs/implementation/checklists/02_milestones.md`
  - `docs/implementation/00_status.md`
  - `docs/implementation/03_worklog.md`
  - `docs/manifest/03_decisions.md`

## Packet Sizing Note
- Keep this packet to 1-5 checklist items.
- Scope-cut order if needed:
  1. CI workflow + command parity
  2. milestone/checklist/status/worklog sync
  3. decision log and release-workflow mapping cleanup
