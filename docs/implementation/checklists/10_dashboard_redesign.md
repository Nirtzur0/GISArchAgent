# Checklist: Dashboard UX Audit + Redesign Packet

- Date: 2026-03-11
- Objective anchor: `docs/manifest/00_overview.md`
- Appetite: medium
- Active slice: planner-first UX redesign
- State: downhill

- [x] Ground the audit in the implemented web UI, not assumptions.
  - AC: findings reference the actual `/`, `/map`, `/analyzer`, and `/data` routes and current browser-tested flows.
  - Verify:
    - `cd frontend && npm run test:e2e`
  - Files: `frontend/src/AppRedesign.tsx`, `frontend/tests/app.spec.ts`
  - Docs: `docs/implementation/reports/dashboard_ux_audit_redesign.md`
  - Alternatives: write a generic audit without runtime evidence.

- [x] Redesign the current routes around planner-first hierarchy without changing backend contracts.
  - AC: `/`, `/map`, `/analyzer`, and `/data` remain intact while the shell, hierarchy, and route composition shift to Workspace / Investigation / Feasibility / Operations.
  - Verify:
    - `cd frontend && npm run build`
    - `cd frontend && npm run test:e2e`
  - Files: `frontend/src/App.tsx`, `frontend/src/AppRedesign.tsx`, `frontend/src/main.tsx`, `frontend/src/styles.redesign.css`
  - Docs: `docs/implementation/reports/dashboard_ux_audit_redesign.md`
  - Alternatives: route or API redesign.

- [x] Produce the implementation-aware redesign handoff with the exact requested 16-section structure.
  - AC: the report covers the required audit, feature-impact, visualization, benchmark, IA, Figma, FE/BE implementation, instrumentation, A/B, roadmap, and final-edit sections.
  - Verify:
    - `rg -n "^# [0-9]+\\." docs/implementation/reports/dashboard_ux_audit_redesign.md`
  - Files: `docs/implementation/reports/dashboard_ux_audit_redesign.md`
  - Docs: `docs/implementation/00_status.md`, `docs/implementation/03_worklog.md`
  - Alternatives: split findings across multiple shorter notes.

- [x] Capture current-state and redesigned pages into the new Figma file with MCP.
  - AC: the Figma file exists and contains current-state evidence plus redesigned route captures.
  - Verify:
    - open `https://www.figma.com/design/d6ExX1CAGJtmV6HzA1j73D` and confirm current-state, redesign, and handoff captures are present
  - Files: Figma file `GISArchAgent - Planner UX Redesign`
  - Docs: `docs/implementation/00_status.md`, `docs/implementation/03_worklog.md`
  - Alternatives: keep all evidence only in markdown and browser screenshots.

- [x] Update planning surfaces so the redesign is visible in repo tracking.
  - AC: milestone, improvement bet, status, and worklog reflect this packet.
  - Verify:
    - `rg -n "M13|IMP-23|dashboard_ux_audit_redesign|10_dashboard_redesign" docs/implementation/checklists/02_milestones.md docs/implementation/checklists/03_improvement_bets.md docs/implementation/reports/improvement_directions.md docs/implementation/00_status.md docs/implementation/03_worklog.md`
  - Files: `docs/implementation/checklists/02_milestones.md`, `docs/implementation/checklists/03_improvement_bets.md`, `docs/implementation/reports/improvement_directions.md`
  - Docs: `docs/implementation/00_status.md`, `docs/implementation/03_worklog.md`
  - Alternatives: treat the redesign as an untracked one-off request.
