# Checklist: Shape Packet Plan

- [x] Bootstrap operator and docs-system metadata.
  - AC: repo root has `AGENTS.md`; docs root mapping exists at `docs/.prompt_system.yml`.
  - Verify: `test -f AGENTS.md && test -f docs/.prompt_system.yml`
  - Files: `AGENTS.md`, `docs/.prompt_system.yml`
  - Docs: `docs/implementation/00_status.md`, `docs/implementation/03_worklog.md`
  - Alternatives: N/A

- [x] Lock project objective and PRD scope.
  - AC: `docs/manifest/00_overview.md` has complete `## Core Objective`; PRD report exists.
  - Verify: `test -f docs/manifest/00_overview.md && test -f docs/implementation/reports/prd.md`
  - Files: `docs/manifest/00_overview.md`, `docs/implementation/reports/prd.md`
  - Docs: `docs/implementation/reports/project_plan.md`
  - Alternatives: N/A

- [x] Create measurable acceptance plan for this packet.
  - AC: this checklist includes observable pass/fail criteria and verification commands.
  - Verify: `rg -n "AC:|Verify:|Files:|Docs:" docs/implementation/checklists/01_plan.md`
  - Files: `docs/implementation/checklists/01_plan.md`
  - Docs: `docs/implementation/00_status.md`
  - Alternatives: N/A

- [x] Produce architecture coherence gate artifacts.
  - AC: architecture docs/checklist/report exist and include readiness verdict + drift diff.
  - Verify: `test -f docs/manifest/01_architecture.md && test -f docs/implementation/checklists/00_architecture_coherence.md && test -f docs/implementation/reports/architecture_coherence_report.md`
  - Files: `docs/manifest/01_architecture.md`, `docs/manifest/04_api_contracts.md`, `docs/manifest/05_data_model.md`
  - Docs: `docs/implementation/checklists/00_architecture_coherence.md`, `docs/implementation/reports/architecture_coherence_report.md`
  - Alternatives: N/A

- [x] Create docs baseline for tech/security/observability/deployment/testing/CI/conventions.
  - AC: manifest pages `02`, `06`, `07`, `08`, `09`, `10`, `11`, `12` exist and are linked from index.
  - Verify: `for f in docs/manifest/02_tech_stack.md docs/manifest/06_security.md docs/manifest/07_observability.md docs/manifest/08_deployment.md docs/manifest/09_runbook.md docs/manifest/10_testing.md docs/manifest/11_ci.md docs/manifest/12_conventions.md; do test -f "$f"; done`
  - Files: `docs/manifest/*.md`
  - Docs: `docs/INDEX.md`
  - Alternatives: N/A

- [x] Produce repository audit checklist handoff.
  - AC: `checkbox.md` exists and includes P0/P1/P2 + Prompt-00 handoff mapping.
  - Verify: `test -f checkbox.md && rg -n "Prompt-00 Handoff|P0|P1|P2" checkbox.md`
  - Files: `checkbox.md`
  - Docs: `docs/implementation/checklists/02_milestones.md`
  - Alternatives: N/A

- [x] Validate prompt-pack integrity used for routing.
  - AC: prompt-pack manifest/integrity checks pass.
  - Verify: `python3 project-prompts/scripts/prompts_manifest.py --check && python3 project-prompts/scripts/system_integrity.py --mode prompt_pack --root project-prompts`
  - Files: `project-prompts/prompts.yml`, `project-prompts/prompts.json`
  - Docs: `docs/implementation/03_worklog.md`
  - Alternatives: N/A
