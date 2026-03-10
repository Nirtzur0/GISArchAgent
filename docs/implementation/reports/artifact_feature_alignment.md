# Artifact-Feature Alignment Report

## Verdict
ALIGNED_WITH_GAPS

## Run Context
- Gate type: `prompt-15-artifact-feature-alignment-gate`.
- Trigger: post-M8 re-ranking selected artifact-feature alignment as the highest-impact unrun gate.
- Date: 2026-02-09.

## Artifact Inventory Summary

| Artifact ID | Role | Source Type | Affected Feature Area | Evidence Paths |
| --- | --- | --- | --- | --- |
| ART-EXT-001 | iPlan ArcGIS PlanningPublic endpoint family is the primary external planning-data source. | web_page / API endpoint | plan search, data discovery, integration adapters | `src/config.py`, `src/infrastructure/repositories/iplan_repository.py`, `src/data_pipeline/discovery_service.py`, `docs/reference/configuration.md` |
| ART-EXT-002 | MAVAT portal and attachment URL patterns define document-link generation and scraping behavior. | web_page / API endpoint | document service, pydoll fetchers, attachment typing | `src/data_management/pydoll_fetcher.py`, `src/infrastructure/services/document_service.py`, `tests/unit/data_management/test_mavat_artifact_type_guessing.py` |
| ART-EXT-003 | Gemini provider behavior/availability drives degraded-mode fallback expectations. | provider docs/API behavior (not locally captured) | regulation synthesis, plan analysis, degraded observability | `src/application/services/regulation_query_service.py`, `src/application/services/plan_search_service.py`, `docs/manifest/07_observability.md` |
| ART-EXT-004 | Browser automation dependency (`pydoll`) and runtime constraints shape optional live-network rehearsal policy. | package/runtime docs (not locally captured) | build ingestion path, optional live integration rehearsals | `src/data_management/pydoll_fetcher.py`, `tests/integration/iplan/test_pydoll_live_mavat_documents__optional.py`, `docs/manifest/10_testing.md`, `docs/troubleshooting.md` |
| ART-EXT-005 | Chroma persistence contract underpins local-first regulation retrieval guarantees. | package docs/API behavior (not locally captured) | regulation repository and vector persistence | `src/infrastructure/repositories/chroma_repository.py`, `docs/manifest/05_data_model.md`, `docs/reference/dependencies.md` |
| ART-PROC-001 | Artifact store/index contract is required for durable external evidence traceability. | process charter | roadmap/ADR grounding and evidence replay | `project-prompts/charter-artifacts-system.md` |

## Artifact-to-Feature Matrix

| Artifact ID | Expected implication | Current feature/test coverage | Status (Supported/Partial/Missing/Misaligned) | Evidence paths |
| --- | --- | --- | --- | --- |
| ART-EXT-001 | iPlan endpoint assumptions should map to adapter behavior and deterministic contract tests. | iPlan repository adapters exist; deterministic degraded-path drills and integration tests exist. | Partial | `src/infrastructure/repositories/iplan_repository.py`, `tests/integration/iplan/test_external_dependency_drills.py`, `tests/integration/data_contracts/test_boundary_payload_contracts.py` |
| ART-EXT-002 | MAVAT URL semantics should map to stable document-link construction and attachment typing. | URL construction and attachment-type tests exist; live-network validation is optional. | Partial | `src/data_management/pydoll_fetcher.py`, `src/infrastructure/services/document_service.py`, `tests/unit/data_management/test_mavat_artifact_type_guessing.py`, `tests/integration/iplan/test_pydoll_live_mavat_documents__optional.py` |
| ART-EXT-003 | Provider outages/errors should never block core journeys and should emit explicit degraded reasons. | Deterministic fallback + degraded telemetry and tests exist. | Supported | `src/application/services/regulation_query_service.py`, `src/application/services/plan_search_service.py`, `tests/unit/application/test_external_dependency_degraded_modes.py`, `docs/manifest/07_observability.md` |
| ART-EXT-004 | Browser/runtime prerequisites should stay bounded and non-flaky in default CI while preserving rehearsal coverage. | Optional live drill is gated and bounded; deterministic non-network drills exist. | Supported | `tests/integration/iplan/test_pydoll_live_mavat_documents__optional.py`, `docs/manifest/10_testing.md`, `docs/troubleshooting.md`, `docs/manifest/09_runbook.md` |
| ART-EXT-005 | Local vector persistence should remain deterministic and test-observable. | Chroma repository boundary and persistence contracts are in place. | Supported | `src/infrastructure/repositories/chroma_repository.py`, `tests/integration/data_contracts/test_persistence_contracts.py`, `docs/manifest/05_data_model.md` |
| ART-PROC-001 | Load-bearing external artifacts should be indexed with IDs, retrieval metadata, and local references. | Canonical artifact store baseline exists (`docs/artifacts/README.md`, `docs/artifacts/index.json`) with initial `ART-EXT-*` entries; citation adoption in decisions/assumptions is still pending. | Partial | `project-prompts/charter-artifacts-system.md`, `docs/artifacts/README.md`, `docs/artifacts/index.json` |

## Top Corrective Outcomes

1. COR-01: initialize artifact store baseline and seed load-bearing external artifacts.
   - Why now: the prompt-15 gate is blocked by process-level evidence gaps, not implementation behavior gaps.
   - Target files/areas: `docs/artifacts/README.md`, `docs/artifacts/index.json`, optional `docs/artifacts/excerpts/*`, `docs/implementation/checklists/08_artifact_feature_alignment.md`.
   - Acceptance signal: artifact store exists with stable IDs for ART-EXT-001..ART-EXT-005 and retrieval metadata policy.
   - Verification approach: docs check (`test -f`, JSON validity, ID references).
   - Prompt-chain recommendation: `prompt-02` -> `prompt-03`.

2. COR-02: codify endpoint-family artifact implications into explicit contract coverage matrix.
   - Why now: endpoint behavior is tested, but implications are spread across tests/docs without a single artifact-to-contract map.
   - Target files/areas: `docs/manifest/04_api_contracts.md`, `tests/integration/data_contracts/test_boundary_payload_contracts.py`, `tests/integration/iplan/test_iplan_sample_data_quality.py`, `docs/troubleshooting.md`.
   - Acceptance signal: iPlan/MAVAT artifact assumptions are mapped to concrete contract tests and failure triage paths.
   - Verification approach: contract + integration test reruns and docs grep.
   - Prompt-chain recommendation: `prompt-10` -> `prompt-02` -> `prompt-03`.

3. COR-03: make artifact citations explicit in external-dependency ADR/risk surfaces.
   - Why now: decisions reference behaviors and URLs but do not yet use stable artifact IDs.
   - Target files/areas: `docs/manifest/03_decisions.md`, `docs/implementation/reports/assumptions_register.md`, `docs/manifest/07_observability.md`.
   - Acceptance signal: key external-dependency decisions/assumptions cite artifact IDs (`ART-EXT-*`/future `ART-*`) instead of URL-only references.
   - Verification approach: docs check for artifact ID citations.
   - Prompt-chain recommendation: `prompt-11` -> `prompt-03`.

## Top Opportunity Outcomes

1. OPP-01: artifact freshness and review cadence policy.
   - Why now: once an artifact store exists, drift prevention requires explicit refresh cadence and ownership.
   - Target files/areas: `docs/artifacts/README.md`, `docs/manifest/09_runbook.md`, `docs/implementation/03_worklog.md`.
   - Acceptance signal: cadence/owner policy exists for refreshing load-bearing artifacts and logging updates.
   - Verification approach: docs check.
   - Prompt-chain recommendation: `prompt-11` -> `prompt-03`.

2. OPP-02: external dependency health snapshot command bundle.
   - Why now: operators currently infer external-boundary health from multiple commands; a single snapshot workflow improves incident triage speed.
   - Target files/areas: `scripts/quick_status.py`, `docs/manifest/09_runbook.md`, `docs/troubleshooting.md`, optional tests under `tests/integration/iplan/*`.
   - Acceptance signal: one command path summarizes iPlan/MAVAT/provider boundary health for local runs.
   - Verification approach: integration + docs check.
   - Prompt-chain recommendation: `prompt-02` -> `prompt-10` -> `prompt-03`.

3. OPP-03: artifact-linked onboarding notes for provider boundaries.
   - Why now: contributors need quicker context on which external systems are load-bearing and where to verify assumptions.
   - Target files/areas: `docs/README.md`, `docs/INDEX.md`, `docs/reference/configuration.md`, `docs/artifacts/README.md`.
   - Acceptance signal: onboarding docs link to artifact IDs for iPlan/MAVAT/Gemini/pydoll/Chroma dependency boundaries.
   - Verification approach: docs check.
   - Prompt-chain recommendation: `prompt-11` -> `prompt-03`.

## Mapping to Milestones
- M9 outcome mapping (updated in `docs/implementation/checklists/02_milestones.md`):
  - artifact store + alignment baseline (`COR-01`)
  - endpoint-family contract mapping (`COR-02`)
  - existing post-M8 signal-quality and formatting outcomes remain active.

## Missing Metadata Notes
- Canonical artifact store baseline now exists under `docs/artifacts/`.
- Initial `ART-EXT-001..ART-EXT-005` entries include URL/kind/retrieval timestamp metadata.
- Local snapshot blobs/checksums (`sha256`, `local_path`) are not yet populated for external pages and remain optional follow-up work.
- Artifact ID citation adoption across decisions/assumptions is complete (`COR-03`).

## Recommended Immediate Next Prompt
- `prompt-03-alignment-review-gate` (post-`OPP-03` drift refresh), then `prompt-02-app-development-playbook` for `CMD-040` warning/cadence hardening.

## 2026-02-09 Update (`COR-02` execution)
- Prompt executed: `prompt-02-app-development-playbook` (`COR-02`, manual/no router script).
- Result:
  - endpoint-family artifact assumptions are now explicitly mapped into contract coverage in `docs/manifest/04_api_contracts.md`.
  - integration contract coverage was tightened with explicit iPlan-family metadata and plan-number pattern checks:
    - `tests/integration/data_contracts/test_boundary_payload_contracts.py`
    - `tests/integration/iplan/test_iplan_sample_data_quality.py`
  - triage mapping for endpoint-family drift is explicit in `docs/troubleshooting.md`.
- Verification evidence:
  - `rg -n "ART-EXT-001|ART-EXT-002|endpoint-family|MAVAT|iPlan" docs/manifest/04_api_contracts.md docs/troubleshooting.md`
  - `./venv/bin/python -m pytest tests/integration/data_contracts/test_boundary_payload_contracts.py -q`
  - `./venv/bin/python -m pytest tests/integration/iplan/test_iplan_sample_data_quality.py -q`
- Remaining corrective priority:
  - `COR-03` artifact-cited external dependency decisions/assumptions.

## 2026-02-09 Update (`COR-03` execution)
- Prompt executed: `prompt-11-docs-diataxis-release` (`COR-03`, manual/no router script).
- Result:
  - load-bearing external dependency decisions now include explicit artifact citations in:
    - `docs/manifest/03_decisions.md`
  - assumptions now include explicit artifact citations in:
    - `docs/implementation/reports/assumptions_register.md`
  - observability dependency guardrails now include explicit artifact citation mapping in:
    - `docs/manifest/07_observability.md`
- Verification evidence:
  - `rg -n "ART-EXT-00[1-5]" docs/manifest/03_decisions.md docs/implementation/reports/assumptions_register.md docs/manifest/07_observability.md`
  - `rg -n "Artifact citations|Artifact Citations" docs/manifest/03_decisions.md docs/manifest/07_observability.md`
- Remaining corrective priorities:
  - `IMP-17` saturation memory-pressure signal completeness.
  - `IMP-18` formatting debt burn phase 5.

## 2026-02-09 Update (`OPP-01` execution)
- Prompt executed: `prompt-11-docs-diataxis-release` (`OPP-01`, manual/no router script).
- Result:
  - artifact freshness cadence policy is now explicit in:
    - `docs/artifacts/README.md`
  - owner model, trigger rules, and logging requirements are codified (weekly cadence + 30-day staleness cap).
  - command-map linkage added via:
    - `docs/manifest/09_runbook.md` (`CMD-039` artifact freshness audit).
  - decision log updated:
    - `docs/manifest/03_decisions.md` (`ADR-0028`)
- Verification evidence:
  - `rg -n "Refresh Cadence Policy|Primary owner|Logging requirements|CMD-039" docs/artifacts/README.md docs/manifest/09_runbook.md`
  - `python3 -c "import json,datetime,pathlib; items=json.loads(pathlib.Path('docs/artifacts/index.json').read_text(encoding='utf-8')).get('artifacts', []); cutoff=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=30)).isoformat(); stale=[i.get('id','unknown') for i in items if (not isinstance(i.get('retrieved_at'), str)) or (i.get('retrieved_at') < cutoff)]; print(f'artifacts_total={len(items)} stale_total={len(stale)}'); print('stale_ids=' + ','.join(stale) if stale else 'stale_ids=')"` -> `artifacts_total=5`, `stale_total=0`
- Remaining opportunity priorities:
  - `OPP-02` external dependency health snapshot bundle.
  - `OPP-03` artifact-linked onboarding boundaries.

## 2026-02-09 Update (`OPP-02` execution)
- Prompt executed: `prompt-02-app-development-playbook` (`OPP-02`, manual/no router script).
- Result:
  - external dependency health snapshot bundle is now available through one canonical command path:
    - `python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills`
  - snapshot bundle includes:
    - iPlan/MAVAT/Gemini boundary configuration checks,
    - recent observability boundary signals,
    - deterministic drill outcomes,
    - optional live-network rehearsal command reminder.
  - command-map and triage docs updated:
    - `docs/manifest/09_runbook.md` (`CMD-040`)
    - `docs/troubleshooting.md`
    - `docs/reference/cli.md`
- Verification evidence:
  - `python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills`
  - `./venv/bin/python -m pytest tests/unit/scripts/test_quick_status_external_snapshot.py -q`
  - `rg -n "CMD-040|external --since-minutes|snapshot bundle" scripts/quick_status.py docs/manifest/09_runbook.md docs/troubleshooting.md docs/reference/cli.md`
  - `./venv/bin/python -m pytest tests/integration/iplan/test_external_dependency_drills.py -q`
  - `./venv/bin/python -m pytest tests/integration/data_contracts/test_boundary_payload_contracts.py tests/integration/iplan/test_iplan_sample_data_quality.py -q`
- Remaining opportunity priority:
  - `OPP-03` artifact-linked onboarding boundaries.

## 2026-02-09 Update (`OPP-03` execution)
- Prompt executed: `prompt-11-docs-diataxis-release` (`OPP-03`, manual/no router script).
- Result:
  - onboarding docs now contain explicit artifact-linked boundary notes for iPlan/MAVAT/Gemini/pydoll/Chroma in:
    - `docs/README.md`
    - `docs/INDEX.md`
    - `docs/reference/configuration.md`
    - `docs/artifacts/README.md`
  - artifact-alignment tracking synchronized:
    - `docs/implementation/checklists/08_artifact_feature_alignment.md` (`OPP-03` checked)
    - `docs/implementation/checklists/02_milestones.md` (onboarding artifact-link outcome checked)
- Verification evidence:
  - `rg -n "artifact:ART-EXT-001|artifact:ART-EXT-002|artifact:ART-EXT-003|artifact:ART-EXT-004|artifact:ART-EXT-005" docs/README.md docs/INDEX.md docs/reference/configuration.md docs/artifacts/README.md`
  - `rg -n "External dependency boundaries|External Boundary Artifacts|Boundary Onboarding Map" docs/README.md docs/INDEX.md docs/reference/configuration.md docs/artifacts/README.md`
- Remaining opportunity priority:
  - none in `OPP-*`; follow-up routing should come from `prompt-03` alignment rerun.
