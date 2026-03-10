# Decisions Log

This file records significant structural or policy decisions that affect maintainability, reliability, and delivery alignment.

## 2026-02-06: Introduce Marker Taxonomy and Pyramid Split
- Decision: Standardize pytest markers (`unit`, `integration`, `e2e`, `data_contracts`, plus boundary markers like `db`, `ui`).
- Decision: Split tests into `tests/unit`, `tests/integration`, `tests/e2e` to align with the test pyramid and improve debuggability.
- Rationale:
  - Prevents all-integration suites where failures are expensive and hard to localize.
  - Enables fast local workflows (`-m unit`) and reduces flake risk by isolating boundary tests.

## 2026-02-08 ADR-0002: Adopt Prompt-Pack Baseline Inside Existing `docs/`
- Context:
  - The repo had substantial docs, but canonical manifest/implementation artifacts were incomplete for prompt-driven lifecycle gates.
- Decision:
  - Keep `docs/` as the single docs root.
  - Add `docs/.prompt_system.yml` and required manifest/implementation baseline files without creating a parallel docs tree.
- Alternatives considered:
  - Create a new docs root (rejected: would create drift and duplicate sources of truth).
  - Leave docs as-is (rejected: missing objective/checklist/coherence artifacts).
- Consequences:
  - Immediate traceability improves.
  - Legacy docs still need incremental cleanup, tracked as follow-up milestones.

## 2026-02-08 ADR-0003: Select Option A Stack Continuity for Current Cycle
- Context:
  - Existing stack is Python + Streamlit + Chroma with working scripts/tests.
- Decision:
  - Use "simplest robust" option: keep current stack and focus on coherence/reliability gaps.
- Alternatives considered:
  - Introduce FastAPI/worker split now (rejected for this cycle due migration cost and churn risk).
- Consequences:
  - Faster delivery of reliability/docs goals.
  - API-service expansion remains a deferred architecture option.

## 2026-02-08 ADR-0004: Architecture Readiness Verdict = GO_WITH_RISKS
- Context:
  - Core runtime boundaries are clear and testable, but CI/release/observability maturity is incomplete.
- Decision:
  - Allow implementation packets to proceed only with explicit risk tracking and milestone gating.
- Key risks accepted:
  - Missing CI workflow.
  - Partial observability instrumentation.
  - Legacy docs drift.
- Consequences:
  - Next packets prioritize P0 reliability and release-discipline artifacts before broader feature expansion.

## 2026-02-08 ADR-0005: Add GitHub Actions CI Baseline for Marker Gates + Prompt-Pack Integrity
- Context:
  - M1 required CI enforcement for canonical command-map tests and docs/prompt-pack coherence.
  - Prompt library was updated and no longer includes router scripts, so CI needed to track prompt-pack integrity directly.
- Decision:
  - Add `.github/workflows/ci.yml` with two jobs:
    - marker test gates (`unit`, `integration`, `e2e`, `data_contracts`)
    - prompt-pack integrity checks (`prompts_manifest.py --check`, `system_integrity.py --mode prompt_pack`)
  - Keep optional network tests gated (`RUN_NETWORK_TESTS=1`) out of default CI path.
- Alternatives considered:
  - Single full-suite-only job (rejected: lower triage granularity).
  - Include lint/format immediately (deferred to keep first CI packet minimal and low-risk).
- Consequences:
  - CI baseline now exists and maps cleanly to command-map test IDs.
  - Remaining release automation gap is narrowed to dedicated tag/release workflow.

## 2026-02-08 ADR-0006: Implement Minimum Structured Observability for Query and Build Workflows
- Context:
  - M2 required partial instrumentation for critical query/build paths.
  - Existing logging lacked explicit correlation tokens and per-run metric records.
- Decision:
  - Add lightweight structured `OBS_EVENT` logging helpers in `src/telemetry.py`.
  - Instrument:
    - `RegulationQueryService.query()` and `PlanSearchService.search_plans()` with per-request correlation IDs and latency/outcome events.
    - `UnifiedDataPipeline.run_async()` with per-run correlation (`run_id`), outcome events, and JSONL metrics sink.
  - Persist build workflow metrics in `data/cache/observability/workflow_metrics.jsonl`.
- Alternatives considered:
  - Full metrics/tracing stack integration now (rejected for packet scope and complexity).
  - Keep docs-only observability plan with no code changes (rejected: did not satisfy M2 acceptance criteria).
- Consequences:
  - Critical workflows now emit structured, correlation-friendly events with minimal code churn.
  - Dashboarding and alert routing remain a follow-up packet.

## 2026-02-08 ADR-0007: Add Dedicated Tag-Driven Release Workflow in GitHub Actions
- Context:
  - Baseline CI (`ci.yml`) covered PR/push verification but release tagging and publish flow were still manual.
  - Alignment gate identified release-tag automation as top operational drift.
- Decision:
  - Add `.github/workflows/release.yml` triggered by `v*` tags and manual dispatch.
  - Enforce release validation gates in that workflow:
    - marker suites (`unit`, `integration`, `e2e`, `data_contracts`)
    - prompt-pack integrity checks
    - release artifact presence checks
  - Add automated GitHub release publication step (`softprops/action-gh-release`) on tag refs.
- Alternatives considered:
  - Keep release process docs-only/manual (rejected: high drift risk).
  - Merge release logic into existing CI workflow (rejected: tag-specific concerns and permissions are cleaner in a dedicated workflow).
- Consequences:
  - Release-time validation is now codified and tied to runbook command IDs.
  - Remaining release hardening is semantic changelog/tag validation and optional packaged artifacts.

## 2026-02-08 ADR-0008: Add Local Observability Backend Sink and Rule-Based Alert Routing
- Context:
  - IMP-01 identified that structured events existed but remained mostly log-line based without a queryable sink and explicit alert routing ownership.
  - Operational maturity required threshold-based routing and initial saturation telemetry for long-running build workflows.
- Decision:
  - Extend `src/telemetry.py` to persist all structured events to a local backend sink (`data/cache/observability/events_backend.jsonl`).
  - Add rule-based alert evaluation/routing to `data/cache/observability/alerts.jsonl` with severity-to-owner mapping:
    - `sev1` -> `maintainer-oncall`
    - `sev2` -> `maintainer-primary`
    - `sev3` -> `maintainer`
  - Add baseline latency/degraded/error thresholds per operation (`regulation_query`, `plan_search`, `build`).
  - Add build-flow saturation signal (`saturation_ratio_1m`) to pipeline event/metrics output.
- Alternatives considered:
  - Add full external observability stack immediately (rejected: too heavy for bounded packet scope).
  - Keep logs-only observability and manual alert review (rejected: did not satisfy IMP-01 acceptance signal).
- Consequences:
  - Observability now has a concrete local backend/event history plus machine-evaluable alert stream.
  - Dashboard UI and richer resource signals (memory/disk/network) remain follow-up improvements.

## 2026-02-08 ADR-0009: Add Incremental CI Quality Gates and Release Tag/Changelog Semantic Validation
- Context:
  - IMP-02 required style/quality hardening and release semantics checks.
  - Full-repo lint/format enforcement is currently blocked by existing legacy debt, but keeping zero quality gates would leave drift unbounded.
- Decision:
  - Add `quality` job to `.github/workflows/ci.yml` with:
    - incremental lint gate: `ruff check src tests scripts --select E9,F63,F7`
    - bounded format guard: `black --check` on actively maintained packet surfaces
  - Add `scripts/check_release_semantics.py` and enforce it in `.github/workflows/release.yml` on tag refs.
- Alternatives considered:
  - Full-repo lint/format gate now (rejected: immediate red CI due unrelated existing debt).
  - No lint/format gate (rejected: leaves quality regression risk unbounded).
- Consequences:
  - CI now has enforceable incremental quality protection without blocking unrelated cleanup debt.
  - Next maturity step is broadening quality scope toward full-repo conformance.

## 2026-02-08 ADR-0010: Canonicalize Docs Navigation and Mark Legacy Pages as Supplementary
- Context:
  - IMP-03 identified drift risk from legacy top-level docs pages that could conflict with Diataxis/manifest guidance.
- Decision:
  - Rewrite `docs/INDEX.md` and `docs/README.md` as canonical navigation entrypoints.
  - Keep legacy deep-dive pages for historical/technical context, but explicitly mark them supplementary.
  - Define precedence: if conflicts exist, `docs/manifest/*` and `docs/implementation/*` are source of truth.
- Alternatives considered:
  - Delete legacy pages immediately (rejected: would remove useful technical context abruptly).
  - Leave navigation as-is (rejected: preserves avoidable onboarding drift).
- Consequences:
  - Onboarding and contributor navigation are clearer and less contradictory.
  - Full rewrite/migration of all legacy pages remains a deferred, optional cleanup.

## 2026-02-08 ADR-0011: Add Observability Query CLI for Local Backend Event/Alert Triage
- Context:
  - Observability backend and alert routing existed, but operators still had to manually inspect raw JSONL sinks.
  - Alignment and improvement packets flagged dashboard/query UX as the next observability depth gap.
- Decision:
  - Add reusable query/summarization helpers in `src/observability/query.py`.
  - Add `scripts/observability_cli.py` with `summary`, `events`, and `alerts` commands for filtered triage.
  - Extend runbook command map with `CMD-024`..`CMD-026` and wire docs to the new workflow.
- Alternatives considered:
  - Build full visual dashboard immediately (rejected: larger scope than this bounded packet).
  - Keep manual `tail`/grep only (rejected: poor operator UX and slower triage).
- Consequences:
  - Local observability backend now has a practical query UX baseline for daily debugging.
  - Dedicated visual dashboards and richer signal dimensions remain a follow-up.

## 2026-02-09 ADR-0012: Make External Dependency Degraded Paths Explicit and Deterministic
- Context:
  - IMP-04 identified a reliability gap: iPlan/Gemini failures could be swallowed as empty/partial results without explicit degraded-mode telemetry and deterministic verification.
- Artifact citations: `ART-EXT-001`, `ART-EXT-002`, `ART-EXT-003`, `ART-EXT-004`.
- Decision:
  - `RegulationQueryService` now falls back deterministically when LLM synthesis fails and emits `outcome=degraded` with `degraded_reasons=["llm_synthesis_unavailable"]`.
  - `PlanSearchService` now aggregates explicit degraded reasons for iPlan boundary failures and vision dependency degradation and emits them in observability events.
  - `IPlanGISRepository` now exposes optional `consume_last_error()` metadata to surface swallowed boundary exceptions without changing repository interface contracts.
  - Add deterministic tests for service-level degraded behavior and repository error signaling.
- Alternatives considered:
  - Keep fallback behavior silent and infer degradation only from logs (rejected: low triage signal quality).
  - Change repository interface signatures to return rich error objects (rejected for now: wider boundary churn than needed for bounded packet).
- Consequences:
  - External dependency degradation is now observable, queryable, and test-covered without requiring live network failures.
  - Alert routing can respond to degraded outcomes with actionable reason fields.

## 2026-02-09 ADR-0013: Add Observability Dashboard CLI and Richer Build Saturation Signals
- Context:
  - Post-IMP-04 alignment review identified the next observability gap as operator UX depth and limited saturation coverage beyond load average.
- Decision:
  - Extend build observability payloads with additional saturation/resource fields:
    - `load_1m`, `cpu_count`, `saturation_ratio_1m`
    - `rss_mb`, `memory_used_ratio`
    - `disk_free_ratio_cache_dir`, `disk_free_mb_cache_dir`
  - Extend alert evaluation with memory/disk pressure thresholds in addition to latency/load.
  - Extend observability query summarization with:
    - degraded-reason counts
    - saturation signal percentile snapshots
  - Add `dashboard` command to `scripts/observability_cli.py` for operator-facing triage view.
- Alternatives considered:
  - Implement a browser dashboard immediately (rejected: larger scope than current bounded packet).
  - Keep summary/events/alerts-only CLI without richer signals (rejected: insufficient operational depth for current correction).
- Consequences:
  - Operators now have an actionable dashboard-like CLI workflow with richer saturation context.
  - Browser dashboard remains a follow-up, but the command-map path is now explicit and test-covered.

## 2026-02-09 ADR-0014: Expand CI Lint Scope and Add Changed-File Formatting Debt Burn Gate
- Context:
  - Post-alignment M5 correction 2 required broader CI quality coverage without forcing an unsafe one-shot formatting rewrite across legacy files.
  - Repo-wide `black --check` currently fails on many pre-existing files, so full-repo format enforcement would block unrelated progress.
- Decision:
  - Expand `CMD-021` to run repo-wide parse/syntax lint gate:
    - `ruff check . --select E9,F63,F7 --exclude project-prompts`
  - Keep `CMD-022` maintained-surface formatting guard for critical packet files.
  - Add `CMD-030` changed-file formatting gate using `scripts/quality_changed_python.py` and `scripts/quality_black_debt_allowlist.txt` so touched non-allowlisted Python files must be formatted.
- Alternatives considered:
  - Enforce full-repo `black --check` immediately (rejected: fails on large existing debt set and causes oversized churn).
  - Keep previous incremental-only quality gates (rejected: coverage remained too narrow for current maturity target).
- Consequences:
  - CI quality coverage now spans the whole repository for high-signal lint/parsing failures.
  - Formatting debt is explicitly baselined and burns down over time as files move out of the allowlist, while critical surfaces remain always enforced.

## 2026-02-09 ADR-0015: Add Deterministic Dependency Lock Artifact and Docs Drift Gate
- Context:
  - Post-alignment M5 correction 3 required deterministic environment recreation and automatic detection of dependency-doc drift.
- Decision:
  - Add `requirements.lock` as the deterministic lock artifact generated from the repo venv package graph.
  - Add `scripts/check_dependency_sync.py` to enforce:
    - lockfile coverage for all direct requirements from `requirements.txt` + `requirements-dev.txt`
    - synchronized dependency inventory docs at `docs/reference/dependencies.md`
  - Add CI enforcement step (`CMD-033`) in `.github/workflows/ci.yml`.
  - Add regeneration command (`CMD-032`) for lock + docs refresh.
- Alternatives considered:
  - Keep range-only manifests without lock artifact (rejected: weak reproducibility guarantees).
  - Manual dependency-doc updates without CI checks (rejected: high drift risk).
- Consequences:
  - Dependency updates now have an explicit regenerate-and-verify workflow.
  - CI detects lock/docs drift before merge, reducing environment mismatch risk.

## 2026-02-09 ADR-0016: Execute Formatting Debt Burn Phase 2 on `src/domain` Module Group
- Context:
  - Post-M5 `prompt-14` selected formatting debt burn as the highest-impact bounded next packet.
  - Full-repo formatting enforcement remains too large for one packet, so migration needs module-batch sequencing.
- Decision:
  - Reformat `src/domain/*` and submodules with black.
  - Remove migrated `src/domain/*` files from `scripts/quality_black_debt_allowlist.txt`.
  - Promote these files into always-enforced maintained-surface formatting checks (`CMD-022`) in CI and runbook parity docs.
- Alternatives considered:
  - Keep `src/domain/*` under changed-file-only enforcement (rejected: slower debt burn and weaker baseline guarantees).
  - Attempt full-repo formatting in one packet (rejected: oversized churn/risk for bounded cycle scope).
- Consequences:
  - Allowlist baseline dropped from 96 lines to 81 lines in this packet.
  - Domain module formatting is now continuously enforced in CI, reducing regression risk in high-signal core logic surfaces.

## 2026-02-09 ADR-0017: Keep Observability Backend Local-Only Until Explicit Promotion Triggers
- Context:
  - Post-IMP-07 alignment left an open decision: continue local-only observability backend or promote to hosted operator backend/dashboard.
  - Current backend (`events_backend.jsonl`, `alerts.jsonl`, CLI dashboard/query commands) already supports day-to-day triage for current team size and run scale.
- Decision:
  - Keep local-only observability backend as the default and supported mode for the current cycle.
  - Defer hosted backend/dashboard implementation until explicit promotion triggers are met.
  - Preserve event schema compatibility and command-map parity so migration remains incremental.
- Promotion triggers:
  - sustained event volume exceeds local triage ergonomics,
  - multi-operator concurrent dashboard usage becomes routine,
  - incident MTTR indicates local-only tooling bottlenecks,
  - cross-host correlation requirements exceed local artifact limits.
- Alternatives considered:
  - Implement hosted backend immediately (rejected: added operational complexity without current demand signal).
  - Keep decision implicit/ad-hoc (rejected: risks recurring scope churn and routing indecision).
- Consequences:
  - Immediate focus can remain on reliability drills and bounded debt-burn packets.
  - Hosted backend work is now explicitly gated and trigger-driven rather than open-ended.

## 2026-02-09 ADR-0018: Execute Formatting Debt Burn Phase 3 on `src/application` Bounded Module Group
- Context:
  - Post-IMP-09 `prompt-14` selected formatting debt burn phase 3 (IMP-10) as the highest-impact immediate M7 correction.
  - The repository still uses phased formatting debt controls, so another bounded module promotion was needed instead of a full-repo formatting rewrite.
- Decision:
  - Reformat and promote the following `src/application` files into always-enforced formatting surfaces (`CMD-022`):
    - `src/application/__init__.py`
    - `src/application/dtos.py`
    - `src/application/services/building_rights_service.py`
    - `src/application/services/plan_upload_service.py`
  - Remove these files from `scripts/quality_black_debt_allowlist.txt`.
  - Update CI/runbook command-map parity for the expanded maintained-surface format guard.
- Alternatives considered:
  - Keep files under changed-file-only formatting enforcement (rejected: slower debt burn and weaker baseline guarantees).
  - Attempt full-repo `black --check` immediately (rejected: oversized churn for current bounded packet).
- Consequences:
  - Allowlist baseline dropped from `81` lines to `77` lines.
  - `src/application` core surfaces now have continuous formatting enforcement in CI, reducing regression risk while preserving phased migration pace.

## 2026-02-09 ADR-0019: Calibrate Regulation Query Latency Alert Thresholds to Reduce Noise
- Context:
  - M7 IMP-11 targeted observability threshold calibration and triage guidance tightening.
  - Calibration snapshot (`CMD-036`, last 180 minutes) showed:
    - `regulation_query` success latency `p95=3453.42ms`, `p99=4379.21ms`
    - `sev3` alert volume dominated by `latency_ms>=3000` despite mostly healthy outcomes.
- Decision:
  - Adjust `regulation_query` latency thresholds in `src/telemetry.py`:
    - `sev3`: `3000ms` -> `4000ms`
    - `sev2`: `6000ms` -> `8000ms`
  - Keep `plan_search` and `build` thresholds unchanged in this packet (insufficient new signal to justify tuning).
  - Add explicit calibration command-map coverage (`CMD-036`) and update triage docs with calibrated threshold expectations.
- Alternatives considered:
  - Keep prior thresholds unchanged (rejected: persistent low-signal alert noise).
  - Raise thresholds more aggressively (rejected: would weaken early visibility into sustained degradation).
  - Lower thresholds further to chase strict SLO target (rejected: already noisy relative to observed baseline).
- Consequences:
  - Sev3 latency alerts are expected to better represent p99-ish spikes rather than routine p90-p95 variation.
  - Severe outlier detection remains intact (sev2 still captures extreme latency events).
  - Thresholds should continue to be periodically recalibrated via `CMD-036`.

## 2026-02-09 ADR-0020: Lock Optional Live-Network Rehearsal as a Bounded Manual Policy
- Context:
  - M7 IMP-12 required keeping live MAVAT smoke coverage available without reintroducing CI flake risk.
  - Deterministic dependency drill suites (`CMD-034`, `CMD-035`) already cover default reliability checks and should remain the mandatory baseline.
- Artifact citations: `ART-EXT-002`, `ART-EXT-004`.
- Decision:
  - Keep `tests/integration/iplan/test_pydoll_live_mavat_documents__optional.py` opt-in only (`RUN_NETWORK_TESTS=1`).
  - Bound rehearsal runtime via configurable caps:
    - `RUN_NETWORK_REHEARSAL_MAX_ATTEMPTS` (default 2, clamped to 1..5)
    - `RUN_NETWORK_REHEARSAL_TIMEOUT_SECONDS` (default 45s, clamped to 15..180)
    - `RUN_NETWORK_REHEARSAL_BACKOFF_SECONDS` (default 2s, clamped to 1..10)
  - Block live rehearsal in CI unless explicitly allowed (`RUN_NETWORK_ALLOW_CI=1`) for dedicated manual drill workflows.
  - Add command-map entry `CMD-037` and codify bounded cadence/guardrails in testing and troubleshooting docs.
- Alternatives considered:
  - Promote live network test into default CI/release gates (rejected: unstable provider/network dependency).
  - Keep current ad-hoc live rehearsal with no cadence/timeout policy (rejected: uneven operational discipline).
- Consequences:
  - Provider-level smoke validation remains available while default CI stays deterministic.
  - Operators now have a repeatable manual drill with explicit cadence and runtime limits.
  - Failures from missing optional dependency or transient provider throttling are treated as expected skip outcomes for this optional path.

## 2026-02-09 ADR-0021: Make Threshold Recalibration Cadence Explicit for CMD-036
- Context:
  - IMP-13 targeted the residual drift where threshold recalibration existed but cadence/trigger policy was implicit.
  - Existing command-map support (`CMD-036`) and dashboard evidence path (`CMD-029`) were available but not bound to a repeatable operating policy.
- Decision:
  - Adopt explicit recalibration cadence:
    - run `CMD-036` at least weekly during active development.
    - run immediately after incident windows showing threshold/alert mismatch.
    - run immediately after threshold or observability payload changes.
  - Require paired evidence capture for each recalibration run:
    - `CMD-036` summary snapshot,
    - `CMD-029` dashboard output from the same window.
  - Require threshold change/no-change rationale to be recorded in decisions/worklog artifacts.
- Alternatives considered:
  - Keep recalibration as ad-hoc operator judgment (rejected: inconsistent operational discipline).
  - Auto-tune thresholds in CI on every run (rejected: unstable/noisy for current local-first operating model).
- Consequences:
  - Threshold tuning becomes predictable and auditable.
  - Alert-noise regressions are easier to detect and justify.
  - Remaining observability risk shifts from cadence ambiguity to data-window quality (for example saturation fields outside build windows).

## 2026-02-09 ADR-0022: Execute Formatting Debt Burn Phase 4 on `src/data_management` Bounded Module Group
- Context:
  - M8 IMP-14 selected another bounded formatting migration after IMP-13 closure.
  - Full-repo formatting enforcement remains deferred, so debt burn continues via module-group promotion into always-enforced surfaces.
- Decision:
  - Reformat and promote the following `src/data_management` files into always-enforced formatting checks (`CMD-022`):
    - `src/data_management/__init__.py`
    - `src/data_management/data_store.py`
    - `src/data_management/fetchers.py`
    - `src/data_management/pydoll_fetcher.py`
  - Remove migrated files from `scripts/quality_black_debt_allowlist.txt`.
  - Update CI/runbook parity for expanded `CMD-022` maintained-surface coverage.
- Alternatives considered:
  - Keep these files under changed-file-only formatting enforcement (rejected: slower debt burn and weaker baseline guarantees).
  - Attempt full-repo `black --check` immediately (rejected: oversized churn for current bounded packet).
- Consequences:
  - Allowlist baseline dropped from `77` lines to `73` lines.
  - `src/data_management` surfaces now have continuous formatting enforcement in CI.

## 2026-02-09 ADR-0023: Adopt Canonical Build-Window Saturation Snapshot Drill (CMD-038)
- Context:
  - IMP-15 targeted residual observability drift where passive windows often produced `None` saturation fields, reducing triage evidence quality.
  - Existing dashboard/query commands were available, but no explicit build-window saturation capture policy existed.
- Decision:
  - Add canonical saturation snapshot drill `CMD-038`:
    - `(python3 scripts/build_vectordb_cli.py build --max-plans 1 --no-vision || true) && python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500`
  - Require build-window evidence capture in runbook/troubleshooting for saturation triage windows.
  - Treat build command failures (for example external provider timeout) as valid evidence windows if structured `build` telemetry and dashboard snapshot are captured.
- Alternatives considered:
  - Keep passive-window dashboard checks only (rejected: saturation fields were frequently sparse/`None`).
  - Require successful build completion before snapshot capture (rejected: would drop useful incident evidence in provider-degraded windows).
- Consequences:
  - Saturation triage now has a repeatable, command-map aligned evidence path.
  - Observability evidence quality improves even when build attempts degrade due external dependencies.

## 2026-02-09 ADR-0024: Initialize Canonical Artifact Store Baseline Under `docs/artifacts`
- Context:
  - Post-M8 artifact-feature alignment gate (`prompt-15`) found process-level drift: load-bearing external assumptions existed in code/docs but had no canonical artifact index for traceability.
  - `COR-01` required a minimal, auditable artifact store before further artifact-derived correction packets.
- Artifact citations: `ART-EXT-001`, `ART-EXT-002`, `ART-EXT-003`, `ART-EXT-004`, `ART-EXT-005`.
- Decision:
  - Create canonical artifact store at `docs/artifacts/` with:
    - `docs/artifacts/README.md` (policy/layout/cadence),
    - `docs/artifacts/index.json` (schema v1 metadata),
    - seeded baseline entries `ART-EXT-001..ART-EXT-005` for iPlan, MAVAT, Gemini, pydoll, and Chroma dependencies.
  - Treat `index.json` as the local machine-readable source of truth for load-bearing external references.
  - Keep blob/checksum capture optional in this packet; require URL/kind/retrieval timestamp for each baseline entry.
- Alternatives considered:
  - Keep artifact mapping only in implementation reports (rejected: weak reproducibility and poor citation durability).
  - Add full snapshot ingestion pipeline immediately (rejected: oversized scope for bounded `COR-01` packet).
- Consequences:
  - Artifact traceability now has a canonical repo location and stable IDs.
  - Remaining follow-up is citation adoption in decisions/assumptions (`COR-03`) and endpoint-family contract tightening (`COR-02`).

## 2026-02-09 ADR-0025: Canonicalize Endpoint-Family Artifact-to-Contract Mapping for iPlan/MAVAT
- Context:
  - `COR-02` required making iPlan/MAVAT external endpoint assumptions explicit across API contracts, integration contract tests, and operator triage docs.
  - Prior state had coverage spread across multiple files without a single artifact-linked mapping surface.
- Artifact citations: `ART-EXT-001`, `ART-EXT-002`.
- Decision:
  - Add an explicit endpoint-family artifact contract map in `docs/manifest/04_api_contracts.md` tying:
    - `ART-EXT-001` (iPlan endpoint family) to deterministic integration contract tests,
    - `ART-EXT-002` (MAVAT attachment URL family) to deterministic + opt-in live verification surfaces.
  - Tighten integration coverage with explicit iPlan-family contract tests:
    - `test_iplan_endpoint_family__source_and_metadata_contract_fields_present`
    - `test_iplan_endpoint_family__plan_number_pattern_on_iplan_sources`
  - Add a dedicated triage path for endpoint-family drift in `docs/troubleshooting.md`.
- Alternatives considered:
  - Keep mapping implicit across existing tests/docs (rejected: weak traceability and slower incident triage).
  - Add live-network MAVAT checks to default CI (rejected: provider variability would reintroduce flake risk).
- Consequences:
  - Endpoint-family assumptions are now auditable and directly linked to verification commands.
  - Remaining artifact-alignment corrective work is focused on citation adoption (`COR-03`), not contract-map ambiguity.

## 2026-02-09 ADR-0026: Add Explicit macOS Memory-Pressure Fallback and Probe Semantics for Build Saturation Signals
- Context:
  - `IMP-17` targeted memory-pressure signal completeness because build-window dashboards repeatedly showed `memory_used_ratio_p95=None`.
  - Root cause on this host: `os.sysconf("SC_AVPHYS_PAGES")` is unavailable on macOS, so the previous memory ratio probe silently returned no value.
- Decision:
  - Keep the existing POSIX `sysconf` path as primary probe when available.
  - Add macOS fallback probe via `memory_pressure -Q` and parse `System-wide memory free percentage`.
  - Emit explicit probe semantics in build observability payloads:
    - `memory_used_ratio_source`
    - `memory_used_ratio_unavailable_reason`
  - Expose memory-signal availability context in observability summary/dashboard views for triage clarity.
- Alternatives considered:
  - Accept `memory_used_ratio=None` with doc-only interpretation (rejected: still opaque in operational windows).
  - Add `psutil` dependency for memory probing (rejected: unnecessary dependency expansion for bounded packet scope).
- Consequences:
  - Build-window saturation snapshots now provide actionable memory context on macOS (`memory_pressure_q` path).
  - If memory probing is unavailable, the gap is explicit and queryable instead of silent.
  - Triage confidence improves without changing alert thresholds or backend mode.

## 2026-02-09 ADR-0027: Execute Formatting Debt Burn Phase 5 on `src/infrastructure` Bounded Module Group
- Context:
  - Post-`IMP-17` alignment refresh routed `IMP-18` as the highest-impact remaining corrective packet.
  - Formatting debt baseline remained `73`, with a concentrated infrastructure batch still listed in `scripts/quality_black_debt_allowlist.txt`.
- Decision:
  - Reformat and promote the following infrastructure files into always-enforced `CMD-022` surfaces:
    - `src/infrastructure/__init__.py`
    - `src/infrastructure/factory.py`
    - `src/infrastructure/repositories/chroma_repository.py`
    - `src/infrastructure/services/cache_service.py`
    - `src/infrastructure/services/document_service.py`
    - `src/infrastructure/services/llm_service.py`
    - `src/infrastructure/services/vision_service.py`
  - Remove those files from `scripts/quality_black_debt_allowlist.txt`.
  - Update CI + runbook parity for the expanded `CMD-022` maintained-surface set.
- Alternatives considered:
  - Keep these files under changed-file-only formatting enforcement (rejected: slower debt burn, weaker baseline guarantees).
  - Attempt immediate full-repo formatting enforcement (rejected: oversized churn relative to bounded packet scope).
- Consequences:
  - Allowlist baseline dropped from `73` lines to `66` lines.
  - A broader infrastructure surface is now continuously enforced by `CMD-022` in CI.

## 2026-02-09 ADR-0028: Establish Artifact Freshness Cadence Ownership and Audit Command
- Context:
  - Post-`IMP-18` alignment gate identified `OPP-01` as the highest docs/ops drift: artifact refresh cadence and ownership were implicit.
  - Artifact store baseline and citations exist, but recurring freshness/audit discipline needed an explicit operator policy.
- Decision:
  - Define explicit artifact freshness owner model in `docs/artifacts/README.md`:
    - primary owner: active packet maintainer,
    - secondary owner: release maintainer.
  - Set cadence policy:
    - weekly freshness audit during active development,
    - hard 30-day staleness limit for `ART-EXT-*` unless explicitly deferred.
  - Add canonical freshness audit command (`CMD-039`) in `docs/manifest/09_runbook.md`.
  - Require worklog recording for each freshness run (owner, reviewed IDs, stale IDs, remediation/deferral decisions).
- Alternatives considered:
  - Keep cadence policy narrative-only with no command-map link (rejected: weaker operational repeatability).
  - Delay policy until artifact blob/checksum capture is complete (rejected: cadence drift risk exists now).
- Consequences:
  - Artifact freshness checks are now command-driven, owner-assigned, and auditable.
  - Remaining artifact opportunities shift from cadence policy to execution UX (`OPP-02`) and onboarding linkage (`OPP-03`).

## 2026-02-09 ADR-0029: Centralize Recurring Evidence Cadence in a Canonical Checklisted Ledger
- Context:
  - Post-`OPP-01` alignment rerun identified `IMP-19`: evidence cadence proof for `CMD-036`/`CMD-029`/`CMD-038` remained distributed across runbook/worklog packet notes.
  - Existing cadence policies were explicit, but execution evidence lacked one canonical checklisted surface.
- Decision:
  - Create canonical ledger file:
    - `docs/implementation/checklists/09_evidence_cadence_ledger.md`
  - Require recurring cadence runs to be recorded in that file with checklisted capture for:
    - `CMD-036` summary snapshot,
    - `CMD-029` dashboard snapshot from the same window,
    - `CMD-038` build-window drill evidence (or explicit defer reason),
    - `CMD-039` artifact freshness audit.
  - Update runbook/observability recording requirements to reference the ledger as the source-of-truth evidence surface.
- Alternatives considered:
  - Keep evidence in ad-hoc worklog packet sections only (rejected: auditability drift and repeated routing loops).
  - Add a script/database-backed evidence store now (rejected: oversized for a bounded docs discipline packet).
- Consequences:
  - Recurring evidence cadence is now auditable from one checklisted file.
  - Alignment correction focus shifts to operational UX gaps (`OPP-02`) and onboarding artifact-link coverage (`OPP-03`).

## 2026-02-09 ADR-0030: Add Single-Command External Dependency Health Snapshot Bundle (`CMD-040`)
- Context:
  - Post-`IMP-19` alignment gate routed `OPP-02`: external dependency triage required multiple separate commands, slowing incident response.
  - The project already had deterministic drill tests and observability slices, but no one-shot bundle for iPlan/MAVAT/Gemini boundary status.
- Artifact citations: `ART-EXT-001`, `ART-EXT-002`, `ART-EXT-003`, `ART-EXT-004`.
- Decision:
  - Extend `scripts/quick_status.py` with an `external` mode that provides:
    - boundary configuration snapshot (iPlan URLs, Gemini key presence, pydoll availability),
    - recent observability boundary signals (`events/alerts/degraded reasons`),
    - optional deterministic drill execution in a single command flow.
  - Add canonical runbook command:
    - `CMD-040` = `python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills`.
  - Use repo venv python (`./venv/bin/python`) for deterministic drill subprocesses when available to prevent interpreter mismatch drift.
- Alternatives considered:
  - Keep triage as manual multi-command sequence (`CMD-027`/`CMD-028`/`CMD-035`) only (rejected: slower, less repeatable first-pass diagnosis).
  - Add a network-live snapshot by default (rejected: would increase flake risk; live rehearsal remains opt-in via `RUN_NETWORK_TESTS=1`).
- Consequences:
  - Operators now have a single reproducible local command for external boundary health.
  - Deterministic drill outcomes are easier to compare across packets/incidents.
  - Remaining artifact opportunity focus shifts to onboarding artifact-link coverage (`OPP-03`).

## 2026-02-09 ADR-0031: Require Artifact-Linked Boundary Notes in Onboarding Docs (`OPP-03`)
- Context:
  - Post-`OPP-02` alignment still showed onboarding drift: boundary assumptions were documented, but new contributors had to cross-read multiple manifest files to map external dependencies.
  - `OPP-03` required explicit artifact-linked onboarding notes in docs entry surfaces.
- Artifact citations: `ART-EXT-001`, `ART-EXT-002`, `ART-EXT-003`, `ART-EXT-004`, `ART-EXT-005`.
- Decision:
  - Add explicit onboarding boundary mapping to:
    - `docs/README.md`
    - `docs/INDEX.md`
    - `docs/reference/configuration.md`
    - `docs/artifacts/README.md`
  - Use `artifact:ART-EXT-*` citations directly in those surfaces so boundary claims are traceable from onboarding pages without manifest deep-dives.
- Alternatives considered:
  - Keep artifact citations only in ADR/observability/assumptions docs (rejected: onboarding still required heavy context-switching).
  - Add a standalone onboarding page only (rejected: higher navigation overhead than embedding in existing entrypoints).
- Consequences:
  - External dependency boundary assumptions are now visible from primary onboarding/navigation docs.
  - Artifact traceability quality improves for first-time contributors and docs maintenance.
  - Next routing should focus on post-`OPP-03` alignment re-check and any remaining `CMD-040` warning-interpretation drift.

## 2026-02-09 ADR-0032: Harden `CMD-040` Warning Semantics and Recurring Cadence Capture
- Context:
  - Post-`OPP-03` alignment gate identified remaining drift in two areas:
    - recurring cadence entries did not explicitly require `CMD-040`,
    - `CMD-040` used a single coarse `WARNING` follow-up path, even when deterministic drills were green and degraded reasons were absent.
- Decision:
  - Add explicit warning-context classification in `scripts/quick_status.py` for `status=WARNING`:
    - `boundary_degraded_signals_present`
    - `historical_runtime_window_noise`
    - `runtime_errors_or_alerts_unconfirmed`
  - Route warning follow-up guidance by `warning_context` instead of a single generic warning message.
  - Expand recurring cadence policy and ledger template to require `CMD-040` capture (`status` + `warning_context`) alongside `CMD-036`/`CMD-029`/`CMD-038`/`CMD-039`.
  - Update runbook/observability/troubleshooting/CLI reference docs to reflect the hardened `CMD-040` semantics.
- Alternatives considered:
  - Keep a single generic warning follow-up path (rejected: ambiguous escalation behavior and repeated operator confusion).
  - Treat all warnings with passing drills as automatically healthy (rejected: risks masking real runtime errors in active windows).
- Consequences:
  - `CMD-040` warnings are now interpretable and actioned with clearer escalation boundaries.
  - recurring evidence cadence now includes external-boundary snapshots as a first-class required signal.
  - remaining alignment risk shifts from semantics ambiguity to normal provider/runtime variability.

## 2026-02-09 ADR-0033: Add Canonical Onboarding Artifact-Link Citation Guardrail (`CMD-041`)
- Context:
  - Post-`CMD-040` alignment rerun still identified one docs drift gap: onboarding/reference pages carried `artifact:ART-EXT-*` citations, but no single command-map guardrail enforced their continued presence.
  - Contributors could inadvertently remove boundary citations from one page without immediate feedback.
- Artifact citations: `ART-EXT-001`, `ART-EXT-002`, `ART-EXT-003`, `ART-EXT-004`, `ART-EXT-005`.
- Decision:
  - Add `CMD-041` to the runbook command map as the canonical onboarding/reference citation guardrail.
  - `CMD-041` checks required `artifact:ART-EXT-*` IDs across:
    - `docs/README.md`
    - `docs/INDEX.md`
    - `docs/reference/configuration.md`
    - `docs/artifacts/README.md`
  - Wire `CMD-041` into onboarding/reference surfaces so contributors know when to run it after boundary-doc edits.
- Alternatives considered:
  - Keep ad-hoc `rg` checks in packet notes only (rejected: not durable as a shared operational command).
  - Add a dedicated script for citation checks now (rejected: command-map shell guardrail is sufficient for current bounded scope).
- Consequences:
  - Onboarding artifact-link coverage is now enforceable via one reproducible command.
  - Future docs packets can verify boundary citation integrity without re-inventing check commands.

## 2026-02-09 ADR-0034: Add Snapshot Follow-up Rendering Regression Coverage and Remove `CMD-040` Startup Warning Noise
- Context:
  - Post-`CMD-041` alignment gate left two code-level gaps:
    - warning-follow-up rendering in `CMD-040` lacked explicit regression assertions for non-boundary warning scenarios,
    - snapshot output included pydantic startup warning noise from `Settings.model_name`.
- Decision:
  - Add rendered-output regression tests in `tests/unit/scripts/test_quick_status_external_snapshot.py` for:
    - `warning_context=historical_runtime_window_noise`,
    - `warning_context=runtime_errors_or_alerts_unconfirmed`.
  - Update `src/config.py` settings model configuration to allow `model_name` without protected-namespace warnings by setting:
    - `protected_namespaces=("settings_",)`.
- Alternatives considered:
  - Keep helper-level only assertions without testing rendered snapshot output (rejected: weaker regression protection for operator-visible behavior).
  - Suppress warning output in CLI wrapper only (rejected: hides the symptom instead of fixing settings semantics).
- Consequences:
  - `CMD-040` operator output stays focused on boundary signals and follow-up guidance.
  - Non-boundary warning branches now have deterministic regression coverage at the output layer.

## 2026-02-09 ADR-0035: Require `CMD-041` in Release-Readiness Sign-off
- Context:
  - Post-M10 alignment showed remaining docs drift: `CMD-041` existed in runbook/onboarding surfaces but was not explicitly required in release-readiness sign-off artifacts.
- Decision:
  - Add a blocking `CMD-041` verification step to release-readiness checklist:
    - `docs/implementation/checklists/06_release_readiness.md`
  - Map `CMD-041` into release workflow documentation as a required pre-tag manual guardrail:
    - `docs/reference/release_workflow.md`
    - `docs/manifest/11_ci.md`
  - Keep `CMD-041` as manual pre-tag validation for now and avoid claiming it as an automated release workflow job step.
- Alternatives considered:
  - Keep `CMD-041` in runbook only (rejected: release sign-off could miss boundary citation drift).
  - Add `CMD-041` directly to release workflow automation immediately (deferred: current packet scope is docs-only mapping/wiring).
- Consequences:
  - Release sign-off now explicitly includes onboarding/reference artifact-link integrity.
  - Boundary citation drift is less likely to escape into tagged releases.

## 2026-02-09 ADR-0036: Enforce `CMD-041` in Release Validation Workflow
- Context:
  - M11 completed documentation wiring for `CMD-041`, but enforcement remained manual and depended on local pre-tag discipline.
  - M12 prioritized reducing release-time citation drift risk by moving this guardrail into automated release validation.
- Decision:
  - Add `CMD-041` guardrail enforcement to `.github/workflows/release.yml` `release-validation` job.
  - Keep release docs aligned so `CMD-041` is described as both:
    - required local pre-tag validation for fast feedback,
    - enforced validation in the tagged release workflow.
- Alternatives considered:
  - Keep manual-only checks (rejected: higher drift risk under release pressure).
  - Move guardrail into a separate workflow only (rejected: weaker coupling with release sign-off semantics).
- Consequences:
  - Release validation now fails fast when onboarding/reference `artifact:ART-EXT-*` citations drift.
  - Command-map release discipline is more consistent between docs and automation.

## 2026-02-09 ADR-0037: Split `CMD-040` Historical Warning Path for Build-Timeout Sev1 Dominance
- Context:
  - After M12 release-workflow automation closure, warning windows remained dominated by recurring `build` timeout sev1 records while deterministic drills were green and degraded boundary reasons were zero.
  - Existing `historical_runtime_window_noise` classification was too coarse for first-pass operator decisions and did not clearly separate build-timeout noise from mixed historical warning windows.
- Decision:
  - Add a dedicated warning context in `scripts/quick_status.py`:
    - `historical_build_timeout_sev1_noise`
  - Emit `warning_noise_profile` counters in `CMD-040` output to show build-timeout vs non-build warning mix:
    - `build_timeout_error_events`
    - `non_build_error_events`
    - `build_timeout_sev1_alerts`
    - `non_build_sev1_alerts`
  - Route follow-up commands for this context to narrowed-window `CMD-040` plus `CMD-026`/`CMD-028` before escalation.
  - Keep `historical_runtime_window_noise` for non-dominant mixed historical windows and retain existing `CMD-025`/`CMD-028` guidance there.
- Alternatives considered:
  - Keep one historical-noise context only (rejected: ambiguous first-pass escalation behavior in recurring build-timeout windows).
  - Treat build timeout sev1 warnings as boundary degradations by default (rejected: deterministic drills + zero degraded reasons indicate non-boundary signal dominance).
- Consequences:
  - `CMD-040` now provides clearer first-pass triage semantics when recurring build timeout noise dominates warning windows.
  - Runbook/troubleshooting/observability guidance can distinguish build-timeout-noise handling from boundary-degraded escalation.
