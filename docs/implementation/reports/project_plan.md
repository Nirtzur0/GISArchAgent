# Project Plan (Shape Stage)

## Objective Re-anchor
- Objective: Build and maintain a local-first GIS planning assistant with reliable query, plan-search, and data-maintenance workflows.
- This step advances objective by: establishing a canonical docs baseline, acceptance checklist, architecture coherence gate, and prioritized next milestones.
- Risks of misalignment: spending effort on low-value polish while unresolved architecture/CI/observability gaps remain.

## Entry Mode and Stage
- Entry mode: Existing Repo evolution.
- Cycle stage: Shape.
- Legacy phase tag: Phase 0.
- Intensity mode: Standard.

## 1) Problem and Scope Clarification
### What the app does
- Serves a Streamlit interface and CLI utilities for searching Israeli planning data/regulations and managing local vector DB/data-store artifacts.

### Primary users and workflows
- Planner/architect: ask regulation and plan-analysis questions.
- Data operator: inspect/manage local JSON and vector DB.
- Contributor: run tests and evolve the codebase safely.

### Inputs and outputs
- Inputs: local `.env` configuration, iPlan and optional Gemini APIs, local data files, user queries.
- Outputs: query answers, plan summaries/analysis, persisted vectors/doc artifacts, CLI status/export outputs.

### Non-goals and risks
- Non-goals and constraints are locked in `docs/manifest/00_overview.md`.
- Top risks are tracked in `docs/implementation/reports/assumptions_register.md`.

## 2) Tech Stack Proposal
### Option A (simplest robust)
- Keep Python + Streamlit + Chroma + pytest stack as-is.
- Tighten docs/contracts/testing/observability around existing boundaries.

### Option B (more scalable/advanced)
- Add explicit API service layer (FastAPI) and async background job queue for ingestion.
- Keep Streamlit as a thin client over stable service contracts.

### Selected
- Option A for current cycle. Reason: lowest change risk and aligns with current repo runtime and scripts.

## 3) Architecture (Source of Truth)
- Lean arc42+C4 profile captured in `docs/manifest/01_architecture.md`.
- Boundary contracts in `docs/manifest/04_api_contracts.md`.
- Data/storage invariants in `docs/manifest/05_data_model.md`.
- Security baseline in `docs/manifest/06_security.md`.

## 4) Structure and Conventions
- Repo layout and code/doc conventions are defined in `docs/manifest/12_conventions.md`.
- Canonical command map is `docs/manifest/09_runbook.md`.

## 5) Feature Breakdown -> Milestones -> Tasks
### Epic 1: Docs and architecture coherence baseline
- Outcome: all required manifest/implementation docs exist with readiness verdict and audit handoff.
- Main files: `docs/manifest/*`, `docs/implementation/checklists/*`, `checkbox.md`.

### Epic 2: Runtime and reliability hardening
- Outcome: observability and CI discipline are explicit and reproducible.
- Main files: `docs/manifest/07_observability.md`, `docs/manifest/11_ci.md`, future `.github/workflows/*`.

### Epic 3: Workflow correctness improvements
- Outcome: prioritized P0/P1 outcomes from audit are implemented and verified.
- Main files: `src/*`, `tests/*`, `docs/implementation/checklists/02_milestones.md`.

Milestones are captured in `docs/implementation/checklists/02_milestones.md`.
Epic details are in `docs/implementation/epics/`.

## 6) Testing Strategy
- Pyramid:
  - Unit tests for domain/application logic.
  - Integration tests for repository and persistence boundaries.
  - E2E smoke checks for Streamlit flows.
  - Data-contract tests for schema/range/completeness invariants.
- Canonical testing policy and commands are in `docs/manifest/10_testing.md` and `docs/manifest/09_runbook.md`.

## 6.5) Observability and Reliability Gate
- Current baseline and required improvements are captured in `docs/manifest/07_observability.md`.
- For critical workflow changes, packet completion requires:
  - updated triage commands in runbook,
  - defined metrics/log schema updates,
  - checklist verification evidence in status/worklog.

## Packet Plan (Now / Next / Not now)
- Now:
  - complete docs baseline + architecture coherence packet,
  - publish audit handoff outputs.
- Next:
  - close P0 outcomes from `checkbox.md` via first implementation packet.
- Not now:
  - large architectural rewrites (service split/hosted deployment).
