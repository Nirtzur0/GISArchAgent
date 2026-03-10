# Product Requirements Document

## Problem statement
GISArchAgent already offers useful local workflows (Streamlit UI, CLI tools, vector DB), but the engineering intent, acceptance criteria, and architecture readiness were under-documented. This increases drift risk between code, tests, and docs when making future changes.

## Users and jobs-to-be-done
- Planner/architect:
  - find relevant regulations and plan context quickly,
  - interpret outputs without reading all raw source files.
- Data operator:
  - inspect local data status,
  - refresh/repair vector DB safely,
  - export filtered datasets.
- Contributor:
  - implement changes without breaking runtime/test/docs coherence.

## In-scope workflows
- Local setup and app launch.
- Regulation query path with deterministic fallback.
- Plan search path (including optional vision analysis).
- Data management and vector DB build/status CLI workflows.
- Engineering documentation baseline and coherence checks.

## Out-of-scope / non-goals
- Hosted production deployment platform.
- Full legal advisory guarantees.
- Full iPlan ingestion at national historical completeness.
- Multi-team release orchestration tooling.

## Success metrics
- Required docs baseline exists and is internally linked.
- Architecture coherence gate produces a readiness verdict and drift checklist.
- Prompt-driven status/checklists are complete and actionable.
- Repo audit (`checkbox.md`) provides prioritized P0/P1/P2 outcomes.

## Requirements (functional + non-functional)
### Functional
- Provide a docs-root lock file and canonical command map.
- Define core objective + measurable acceptance criteria.
- Produce architecture/contracts/data/security/observability/deployment/testing manifests.
- Produce milestone + epic checklists for next execution packets.
- Produce a project-level audit with prioritized outcomes.

### Non-functional
- Docs must be evidence-based and repo-grounded.
- Changes should be minimal-diff and avoid code churn for docs-only prompt packets.
- Acceptance criteria must be pass/fail testable.
- All new artifacts must stay under the existing `docs/` system.

## Risks and assumptions
- External iPlan availability and quality can vary.
- Optional Gemini integrations may be unavailable in some local environments.
- Existing legacy docs may conflict with manifest docs and require gradual reconciliation.

## Acceptance criteria mapping
- AC-01: `docs/.prompt_system.yml` exists and maps canonical doc paths.
- AC-02: `docs/manifest/00_overview.md` contains complete `## Core Objective` block.
- AC-03: `docs/implementation/checklists/01_plan.md` includes testable AC/Verify/Files/Docs fields.
- AC-04: Architecture coherence deliverables exist with readiness verdict.
- AC-05: Repo audit output `checkbox.md` exists and includes Prompt-00 handoff section.

## Open questions / TODOs
- Should this project keep Streamlit-only UI or add a supported API surface?
- What CI baseline should be mandatory before release work starts?
- Which runtime SLOs are required for local-only vs future hosted use?
