# Docs Index

GISArchAgent documentation for planners, operators, and contributors. This index is the canonical navigation entrypoint and links both user-facing docs and engineering control docs.

Quick Links: [Getting Started](getting_started/installation.md) | [Tutorials](tutorials/README.md) | [How-To](how_to/run_end_to_end.md) | [Reference](reference/cli.md) | [Troubleshooting](troubleshooting.md)

## Docs Bet
- Appetite: medium
- Now:
  - docs navigation cleanup and stale-claim reconciliation
  - release/observability command-map alignment
- Not now:
  - full rewrite of all legacy deep-dive pages into Diataxis pages
  - hosted deployment playbook until deployment target and operational ownership are selected

## Getting Started
- Installation: `docs/getting_started/installation.md`
- Quickstart: `docs/getting_started/quickstart.md`

## Tutorials
- End-to-end local workflow tutorial: `docs/tutorials/README.md`

## How-To Guides
- Configuration: `docs/how_to/configuration.md`
- Run end-to-end: `docs/how_to/run_end_to_end.md`
- Interpret outputs: `docs/how_to/interpret_outputs.md`
- Upgrade notes template: `docs/how_to/upgrade_notes_template.md`

## Reference
- CLI reference: `docs/reference/cli.md`
- Configuration reference: `docs/reference/configuration.md`
- Data formats: `docs/reference/data_formats.md`
- Dependency inventory: `docs/reference/dependencies.md`
- Versioning policy: `docs/reference/versioning_policy.md`
- Release workflow mapping: `docs/reference/release_workflow.md`

## Explanation
- Architecture explanation: `docs/explanation/architecture.md`
- Problem landscape and solution: `docs/explanation/problem_landscape_and_solution.md`
- Design decisions overview: `docs/explanation/design_decisions.md`

## Operational
- Troubleshooting: `docs/troubleshooting.md`
- Glossary: `docs/glossary.md`
- Changelog: `CHANGELOG.md`
- Contributing: `CONTRIBUTING.md`
- License: TODO - no `LICENSE` file is currently committed

## External Boundary Artifacts (Onboarding)
Use artifact-linked boundary notes when touching provider/runtime assumptions:
- iPlan endpoint family: `artifact:ART-EXT-001` (`docs/reference/configuration.md`, `docs/troubleshooting.md`)
- MAVAT attachment endpoints: `artifact:ART-EXT-002` (`docs/reference/configuration.md`, `docs/troubleshooting.md`)
- Gemini behavior and fallback assumptions: `artifact:ART-EXT-003` (`docs/reference/configuration.md`, `docs/manifest/07_observability.md`)
- `pydoll-python` runtime/browser assumptions: `artifact:ART-EXT-004` (`docs/reference/configuration.md`, `docs/manifest/10_testing.md`)
- Chroma local persistence assumptions: `artifact:ART-EXT-005` (`docs/reference/configuration.md`, `docs/manifest/05_data_model.md`)
- Artifact inventory source: `docs/artifacts/index.json` and policy: `docs/artifacts/README.md`
- Citation guardrail command: `CMD-041` in `docs/manifest/09_runbook.md` (fails if required `artifact:ART-EXT-*` citations are missing from onboarding/reference boundary docs).

## Engineering Docs
### Manifest (What and Why)
- Project overview and objective: `docs/manifest/00_overview.md`
- Architecture: `docs/manifest/01_architecture.md`
- Tech stack: `docs/manifest/02_tech_stack.md`
- Decisions log: `docs/manifest/03_decisions.md`
- API and boundary contracts: `docs/manifest/04_api_contracts.md`
- Data model: `docs/manifest/05_data_model.md`
- Security baseline: `docs/manifest/06_security.md`
- Observability and reliability: `docs/manifest/07_observability.md`
- Deployment shape: `docs/manifest/08_deployment.md`
- Runbook and command map: `docs/manifest/09_runbook.md`
- Testing strategy: `docs/manifest/10_testing.md`
- CI manifest: `docs/manifest/11_ci.md`
- Conventions: `docs/manifest/12_conventions.md`

### Implementation (What Was Done)
- Current status: `docs/implementation/00_status.md`
- Worklog: `docs/implementation/03_worklog.md`
- Architecture coherence checklist: `docs/implementation/checklists/00_architecture_coherence.md`
- Plan checklist: `docs/implementation/checklists/01_plan.md`
- Milestones: `docs/implementation/checklists/02_milestones.md`
- Improvement bets: `docs/implementation/checklists/03_improvement_bets.md`
- Test refactor checklist: `docs/implementation/checklists/03_test_refactor.md`
- Release readiness: `docs/implementation/checklists/06_release_readiness.md`
- Alignment review: `docs/implementation/checklists/07_alignment_review.md`
- Artifact-feature alignment: `docs/implementation/checklists/08_artifact_feature_alignment.md`
- Evidence cadence ledger: `docs/implementation/checklists/09_evidence_cadence_ledger.md`
- Reports index: `docs/implementation/reports/README.md`

## Legacy Deep Dives (Supplementary)
These pages are retained for historical and deep-technical context. When guidance conflicts, prefer Diataxis + manifest + implementation checklists.

- `docs/ARCHITECTURE.md`
- `docs/HOW_IT_WORKS.md`
- `docs/BUILD_VECTORDB_GUIDE.md`
- `docs/UNIFIED_PIPELINE.md`
- `docs/TEST_ARCHITECTURE.md`
- `docs/VECTOR_DB_MANAGEMENT.md`
- `docs/VECTOR_DB_VALIDATION.md`
- `docs/GENERIC_PIPELINE_ARCHITECTURE.md`
- `docs/SYSTEM_FLOW.md`
- `docs/IPLAN_DATA_SOURCES_MAP.md`

## Where to Look Next
- New users: installation -> quickstart -> tutorial.
- Power users: run end-to-end -> CLI reference -> output interpretation -> runbook commands.
- Contributors: manifest docs -> implementation checklists -> changelog/release workflow.
