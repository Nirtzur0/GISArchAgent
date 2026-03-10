# Artifact-Feature Alignment Checklist

- Source report: `docs/implementation/reports/artifact_feature_alignment.md`
- Created by: `prompt-15-artifact-feature-alignment-gate`
- Review date: 2026-02-09
- Verdict: `ALIGNED_WITH_GAPS`

## Corrective Outcomes

### COR-01 - Artifact Store Baseline Initialization
- [x] Outcome: initialize canonical artifact store with IDs and metadata for load-bearing external sources.
  - Owner type: maintainer
  - Effort: S/M
  - Target files/areas: `docs/artifacts/README.md`, `docs/artifacts/index.json`, optional `docs/artifacts/excerpts/*`
  - Acceptance signal: `ART-EXT-001..ART-EXT-005` entries exist with URL, kind, and retrieval metadata policy.
  - Verification method: docs check
  - Suggested prompt chain: `prompt-02` -> `prompt-03`
  - Verification evidence:
    - `test -f docs/artifacts/README.md && test -f docs/artifacts/index.json`
    - `python3 -m json.tool docs/artifacts/index.json > /dev/null`
    - `rg -n "ART-EXT-001|ART-EXT-002|ART-EXT-003|ART-EXT-004|ART-EXT-005|retrieved_at" docs/artifacts/index.json`

### COR-02 - Endpoint-Family Artifact Contract Mapping
- [x] Outcome: map iPlan/MAVAT artifact assumptions into explicit contract coverage and triage links.
  - Owner type: maintainer
  - Effort: M
  - Target files/areas: `docs/manifest/04_api_contracts.md`, `tests/integration/data_contracts/test_boundary_payload_contracts.py`, `tests/integration/iplan/test_iplan_sample_data_quality.py`, `docs/troubleshooting.md`
  - Acceptance signal: endpoint assumptions and failure modes are explicitly tied to contract/integration checks.
  - Verification method: contract
  - Suggested prompt chain: `prompt-10` -> `prompt-02` -> `prompt-03`
  - Verification evidence:
    - `rg -n "ART-EXT-001|ART-EXT-002|endpoint-family|MAVAT|iPlan" docs/manifest/04_api_contracts.md docs/troubleshooting.md`
    - `./venv/bin/python -m pytest tests/integration/data_contracts/test_boundary_payload_contracts.py -q`
    - `./venv/bin/python -m pytest tests/integration/iplan/test_iplan_sample_data_quality.py -q`

### COR-03 - Artifact-Cited External Dependency Decisions
- [x] Outcome: add artifact ID citations to load-bearing external dependency decisions and assumptions.
  - Owner type: maintainer
  - Effort: S
  - Target files/areas: `docs/manifest/03_decisions.md`, `docs/implementation/reports/assumptions_register.md`, `docs/manifest/07_observability.md`
  - Acceptance signal: external dependency decisions/assumptions reference stable artifact IDs instead of URL-only text.
  - Verification method: docs check
  - Suggested prompt chain: `prompt-11` -> `prompt-03`
  - Verification evidence:
    - `rg -n "ART-EXT-00[1-5]" docs/manifest/03_decisions.md docs/implementation/reports/assumptions_register.md docs/manifest/07_observability.md`
    - `rg -n "Artifact citations|Artifact Citations" docs/manifest/03_decisions.md docs/manifest/07_observability.md`

## Opportunity Outcomes

### OPP-01 - Artifact Freshness Cadence Policy
- [x] Outcome: define artifact review/refresh cadence and ownership.
  - Owner type: maintainer
  - Effort: S
  - Target files/areas: `docs/artifacts/README.md`, `docs/manifest/09_runbook.md`, `docs/implementation/03_worklog.md`
  - Acceptance signal: cadence policy exists with explicit owner and logging expectations.
  - Verification method: docs check
  - Suggested prompt chain: `prompt-11` -> `prompt-03`
  - Verification evidence:
    - `rg -n "Refresh Cadence Policy|Primary owner|Logging requirements|CMD-039" docs/artifacts/README.md docs/manifest/09_runbook.md`
    - `python3 -c "import json,datetime,pathlib; items=json.loads(pathlib.Path('docs/artifacts/index.json').read_text(encoding='utf-8')).get('artifacts', []); cutoff=(datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=30)).isoformat(); stale=[i.get('id','unknown') for i in items if (not isinstance(i.get('retrieved_at'), str)) or (i.get('retrieved_at') < cutoff)]; print(f'artifacts_total={len(items)} stale_total={len(stale)}'); print('stale_ids=' + ','.join(stale) if stale else 'stale_ids=')"` (`artifacts_total=5`, `stale_total=0`)

### OPP-02 - External Dependency Health Snapshot Bundle
- [x] Outcome: add a single command path for external boundary health snapshotting.
  - Owner type: maintainer
  - Effort: M
  - Target files/areas: `scripts/quick_status.py`, `docs/manifest/09_runbook.md`, `docs/troubleshooting.md`, optional tests under `tests/integration/iplan/*`
  - Acceptance signal: one reproducible command bundle summarizes iPlan/MAVAT/provider boundary status for local triage.
  - Verification method: integration
  - Suggested prompt chain: `prompt-02` -> `prompt-10` -> `prompt-03`
  - Verification evidence:
    - `python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills`
    - `./venv/bin/python -m pytest tests/unit/scripts/test_quick_status_external_snapshot.py -q`
    - `rg -n "CMD-040|external --since-minutes|snapshot bundle" scripts/quick_status.py docs/manifest/09_runbook.md docs/troubleshooting.md docs/reference/cli.md`
    - `./venv/bin/python -m pytest tests/integration/iplan/test_external_dependency_drills.py -q`
    - `./venv/bin/python -m pytest tests/integration/data_contracts/test_boundary_payload_contracts.py tests/integration/iplan/test_iplan_sample_data_quality.py -q`

### OPP-03 - Artifact-Linked Onboarding Boundaries
- [x] Outcome: link onboarding docs to artifact IDs for external provider boundaries and assumptions.
  - Owner type: contributor
  - Effort: S
  - Target files/areas: `docs/README.md`, `docs/INDEX.md`, `docs/reference/configuration.md`, `docs/artifacts/README.md`
  - Acceptance signal: onboarding/reference docs include artifact-linked boundary notes for iPlan/MAVAT/Gemini/pydoll/Chroma.
  - Verification method: docs check
  - Suggested prompt chain: `prompt-11` -> `prompt-03`
  - Verification evidence:
    - `rg -n "artifact:ART-EXT-001|artifact:ART-EXT-002|artifact:ART-EXT-003|artifact:ART-EXT-004|artifact:ART-EXT-005" docs/README.md docs/INDEX.md docs/reference/configuration.md docs/artifacts/README.md`
    - `rg -n "External dependency boundaries|External Boundary Artifacts|Boundary Onboarding Map" docs/README.md docs/INDEX.md docs/reference/configuration.md docs/artifacts/README.md`
