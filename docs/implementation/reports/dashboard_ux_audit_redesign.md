# 1. Executive verdict

GISArchAgent was useful but not well designed. The product exposed real capability, yet the interface behaved like four adjacent tools rather than one planner workflow. The redesign fixes that by making plan selection and next-step clarity primary, demoting runtime noise, and removing slow or low-value surfaces from the main decision path.

The implemented direction is deliberately stricter:
- `/` is now a focused Workspace, not a dumping ground.
- `/map` is explicitly Investigation and map-first.
- `/analyzer` is Feasibility and scenario-first.
- `/data` is Operations and intentionally secondary to planner work.

The product is now calmer, more legible, and more obviously useful. It is still dense, but the density now serves planning decisions instead of exposing implementation detail.

# 2. Current-state audit

Current-state audit before implementation:
- The original landing page gave search, dossier, and assistant near-equal weight, so hierarchy was weak.
- Investigation, feasibility, and operations each had value, but they felt stitched together rather than sequenced.
- Query results and degraded backend states often surfaced as raw text or transport leakage instead of shaped UX.
- Mobile preserved feature access but collapsed into a long serial stack with weak prioritization.
- Repeated plan identity consumed space without adding meaning.
- Operational truth was present, but the app let it intrude on planner flows too often.

Behavioral audit after implementation:
- Workspace now has one dominant job: select a project, understand the brief, ask a grounded question.
- Investigation now makes the map the primary surface and keeps supporting facts/evidence subordinate.
- Feasibility keeps inputs, result, comparison, and upload-backed evidence in one coherent route.
- Operations now groups health, freshness, vector maintenance, and recovery actions instead of scattering them.

# 3. What is working

- Selected-plan persistence was strong and is preserved.
- The map route already carried meaningful site-review value because geometry, centroids, and source links existed.
- Building-rights comparison logic already answered a real user question and was worth keeping.
- The system already exposed degraded provider and scraper states honestly; that honesty is preserved.
- The local data inventory and regulation corpus remain valuable because they support grounded answers and operations review.

# 4. What is hurting UX

- Equal-weight panel competition on the old dashboard made the product feel assembled rather than authored.
- Long-form answer/result blocks made the assistant feel like a raw dump surface instead of a decision aid.
- Duplicate project identity weakened focus.
- Slow top-level data shaping introduced unnecessary waiting in the new brief surface until the backend overview path was simplified.
- Operations language mixed maintenance truth and planner context too casually.
- The old route model organized by implementation surfaces more than by user intent.

# 5. Feature impact matrix

| Feature / surface | User value | Cognitive cost | Decision impact | Classification | Decision |
| --- | --- | --- | --- | --- | --- |
| Plan search / queue | High | Medium | High | Keep + simplify | Keep, but make explicit selection the start of the flow |
| Project dossier block | Medium | Medium | High | Merge / redesign | Replace with project brief + shareable summary |
| Grounded assistant | High | Medium | High | Redesign | Keep, but anchor to selected plan and compact the answer surface |
| Query history | Medium | Low | Medium | Keep | Keep as lightweight recall, not a dominant surface |
| Map canvas | High | Medium | High | Keep | Make it the dominant investigation surface |
| Side detail rails on map | Medium | Medium | Medium | Simplify | Keep, but subordinate to map and evidence review |
| Building-rights result | High | Medium | High | Keep | Preserve as primary feasibility output |
| Proposal comparison cards | High | Low | High | Keep | Preserve and tighten copy/visual hierarchy |
| Upload analysis | Medium | Medium | Medium | Keep + clarify | Keep, but frame as supporting evidence, not core path |
| System status on planner routes | Low | High | Low | Move / hide | Demote out of planner routes unless blocking |
| Operations admin tasks | Medium | Medium | Medium | Keep | Keep, but isolate inside Operations |
| Vector search / authoring | Medium | Medium | Medium | Keep | Keep as an operations utility, not a dashboard centerpiece |
| Raw failure text | Low | High | Medium | Remove | Replace with designed state surfaces |
| Decorative dashboard charts | Low | Medium | Low | Remove | Do not add |

# 6. Visualization decision table

| User question | Data available | Decision supported | Recommended surface | Why it helps | Why simpler may be better | Placement |
| --- | --- | --- | --- | --- | --- | --- |
| What should I do next for this plan? | Selected plan, status, geometry, provider readiness | Choose next workflow step | Summary block + next actions | Faster than scanning multiple widgets | A chart adds no value | Workspace |
| Is this site spatially understandable? | Geometry, centroid, plan metadata | Move to site investigation | Map | Spatial context is the actual question | Text alone is insufficient | Investigation |
| What is the allowed development envelope? | Plot size, zone type, regulations | Feasibility decision | KPI/result cards | Comparable and scannable | A graph would add noise | Feasibility |
| How does proposal A compare to allowed rights? | Proposed values vs allowed values | Risk comparison | Comparison rows/cards | Direct delta framing is enough | Charts would overstate precision | Feasibility |
| Is the runtime healthy enough to trust? | Provider status, scraper availability, vector status, freshness | Operational trust / recovery | Status rows + grouped state surfaces | Clear status grouping supports action | Trend charts are unnecessary | Operations |
| Do I need historical trends? | No stable time-series backend | None right now | Reject | No user decision currently depends on trend lines | Simpler status is better | Do not add |
| Should Workspace show charts? | Limited top-level summary data | None | Reject | The route is for task initiation, not analytics | Summary tiles are enough | Do not add |

Approved visuals in this packet:
- compact status/KPI rows
- comparison cards for feasibility
- map as the primary investigation visual
- freshness and health indicators in Operations

Rejected visuals in this packet:
- generic trend charts on Workspace
- decorative activity graphs
- filler widgets with no direct decision support

# 7. Benchmark principles from strong modern products

Transferable principles used here:
- Linear: strong hierarchy, low-noise defaults, clear route purpose.
- Stripe Dashboard: disciplined grouping for dense information, especially around summaries and operational status.
- Vercel: operational truth is visible, but it does not dominate every product surface.

Principles intentionally transferred:
- fewer, clearer surfaces
- one dominant action per route
- grouped operational truth instead of repeated banners
- stronger overview/detail split
- cleaner defaults before drill-down

Principles intentionally not copied:
- decorative analytics density without a supporting user question
- motion-heavy affordances
- card proliferation for the sake of looking like a modern dashboard

# 8. Proposed redesign principles

- Clarity over cleverness.
- One dominant job per route.
- Overview first, detail on demand.
- Keep the selected plan visible across modes.
- Summaries before raw dumps.
- Planner work first, operations second.
- Use state surfaces for degraded, empty, loading, and error states.
- Only show visualizations when they answer a real question faster than text.

# 9. Proposed new information architecture

Primary route model:
- `/` = Workspace
  - project selection
  - project brief
  - grounded query
  - next-step summary
- `/map` = Investigation
  - map-first site review
  - selected-site facts
  - source/evidence actions
- `/analyzer` = Feasibility
  - scenario inputs
  - rights result
  - comparison verdicts
  - upload-backed evidence
- `/data` = Operations
  - provider health
  - data freshness/inventory
  - vector maintenance
  - recovery actions

Flow model:
1. Select a real project.
2. Read the brief and current blockers.
3. Move into investigation or feasibility.
4. Use Operations only when trust or data freshness requires intervention.

# 10. Figma redesign plan and file edits

Canonical design file:
- [GISArchAgent - Planner UX Redesign](https://www.figma.com/design/d6ExX1CAGJtmV6HzA1j73D)

Implemented Figma structure:
- `00_Current State`
- `01_Audit Verdict`
- `02_Foundations`
- `03_Workspace`
- `04_Investigation`
- `05_Feasibility`
- `06_Operations`
- `07_States`
- `08_Components`
- `09_Responsive`
- `10_Engineering Handoff`

Captured implementation evidence already mapped into the file:
- redesign workspace capture: node `1:2`
- current-state workspace capture: node `2:2`
- structured `/figma-handoff` board capture: node `3:2`

Figma-edit intent for this packet:
- keep the current Figma file as the canonical redesign source
- ground frames in the live implemented app rather than abstract mockups
- preserve old/current-state evidence beside redesigned frames for traceability

# 11. Front-end implementation plan

Implemented frontend structure:
- shell moved to `frontend/src/AppRedesign.tsx`
- route modules extracted into:
  - `frontend/src/redesign/pages/WorkspacePage.tsx`
  - `frontend/src/redesign/pages/InvestigationPage.tsx`
  - `frontend/src/redesign/pages/FeasibilityPage.tsx`
  - `frontend/src/redesign/pages/OperationsPage.tsx`
- reusable design-system layer extracted into:
  - `frontend/src/redesign/components.tsx`
  - `frontend/src/redesign/model.ts`
  - `frontend/src/redesign/tracking.ts`

Frontend implementation decisions:
- Workspace no longer auto-selects the first search result; explicit user selection is now required.
- Querying remains grounded to the selected plan and the answer surface stays compact until invoked.
- Investigation keeps the map dominant and avoids competing hero surfaces.
- Feasibility keeps scenario inputs visible while results and upload analysis remain nearby.
- Operations now uses one overview payload instead of noisy client fan-out for top-level status.
- `/figma-handoff` stays available as an internal artifact route.

Frontend acceptance criteria met:
- route URLs preserved
- planner-first hierarchy implemented
- new overview/event APIs consumed
- shared design-system components introduced
- browser tests updated to match redesigned flows

# 12. Back-end implementation plan

Implemented additive APIs:
- `GET /api/workspace/overview`
- `GET /api/operations/overview`
- `POST /api/ui/events`

Why each backend change was needed:
- `workspace/overview`
  - supports the calmer Workspace brief
  - centralizes selected-plan summary shaping
  - reduces frontend orchestration and repeated client formatting
- `operations/overview`
  - supports grouped operations status
  - collapses several top-level health/freshness concerns into one payload
- `ui/events`
  - supports later validation of redesign impact
  - uses existing local observability infrastructure instead of adding a separate analytics system

Important implementation constraint applied:
- overview endpoints are fast summary endpoints, not live probe surfaces
- fetcher capability is summarized without a blocking live probe so the Workspace and Operations routes do not stall

Backend payload support added:
- selected-plan brief
- summary metrics
- constraint signals
- next actions
- shareable brief
- grouped operations health/freshness/inventory
- lightweight event ingestion metadata

# 13. Instrumentation and future validation plan

Implemented instrumentation:
- route viewed
- workspace query submitted
- workspace error/degraded states
- feasibility calculation run/error
- upload analyzed/error
- vector search
- import / refresh / vector maintenance actions

Current event ingestion path:
- frontend posts to `POST /api/ui/events`
- backend writes to the existing telemetry event sink via `persist_ui_event(...)`

Future validation plan:
- measure Workspace time to first useful query
- measure plan-selection completion rate
- measure feasibility run frequency per selected plan
- measure degraded-state exposure frequency
- measure operations-task usage after planner workflow changes

# 14. Simulated A/B hypotheses

| Control | Variant | Expected user behavior change | Success metric | Confidence | Risk |
| --- | --- | --- | --- | --- | --- |
| Old equal-weight landing page | Focused Workspace with explicit project brief and next action | Faster comprehension and faster first useful action | Lower time to first grounded query, lower click depth | High | Low |
| Implicit first-result selection | Explicit planner queue selection | More deliberate context setting, fewer accidental queries | Higher selected-plan certainty, fewer irrelevant queries | Medium | Low |
| Raw long answer/result presentation | Compact answer summary + evidence list | Better scanning and better trust in supporting evidence | Faster evidence review, lower abandonment | High | Low |
| Multi-call ops top-level status | Single operations overview payload | Faster route load and clearer health grouping | Lower load time, fewer error surfaces | High | Low |
| Live fetcher probe on overview load | Capability summary on overview load | Faster perceived performance and fewer stuck loading states | Lower time spent in loading state | High | Very low |

# 15. Prioritized roadmap

Do first:
- keep the new planner-first route structure as the baseline
- stabilize the new overview/event APIs
- continue using the Figma file as the design-review source of truth

Do next:
- extract more visual primitives from route pages into stricter component variants
- extend responsive review across tablet and mobile breakpoints
- refine investigation and feasibility copy based on real user sessions

Do later:
- add saved views or preferences only if instrumentation shows clear repeated need
- add richer operational history only if real users need longitudinal diagnosis
- add new visualization only if a concrete user question emerges that text/cards cannot answer

# 16. Final list of edits made

Figma:
- used the canonical redesign file `GISArchAgent - Planner UX Redesign`
- preserved current-state and redesign evidence
- mapped implementation captures into nodes `1:2`, `2:2`, and `3:2`

Frontend:
- refactored the shell in `frontend/src/AppRedesign.tsx`
- kept `frontend/src/App.tsx` as the public entry path
- introduced route-level page modules and shared redesign components
- added new API client/types for overview and event ingestion
- updated Playwright coverage for the redesigned Workspace behavior

Backend:
- added `GET /api/workspace/overview`
- added `GET /api/operations/overview`
- added `POST /api/ui/events`
- added telemetry persistence for lightweight UI events
- optimized overview endpoints to avoid blocking fetcher probes

Docs and planning:
- refreshed this audit/handoff report to the required 16-section format
- updated `docs/implementation/checklists/10_dashboard_redesign.md`
- synced `docs/implementation/00_status.md`
- synced `docs/implementation/03_worklog.md`

Validation completed:
- `./venv/bin/python -m pytest tests/unit/infrastructure/test_telemetry_backend.py -q`
- `./venv/bin/python -m pytest tests/integration/api/test_fastapi_endpoints.py -q`
- `cd frontend && npm run build`
- `cd frontend && npm run test:e2e`
