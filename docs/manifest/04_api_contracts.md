# API and Boundary Contracts

## Contract Catalog

| Boundary | Input Contract | Output Contract | Evidence |
| --- | --- | --- | --- |
| UI -> Regulation query service | `RegulationQuery` (`query_text`, optional `location`, optional `regulation_type`, `max_results`) | `RegulationResult` (`regulations`, `query`, `total_found`, optional `answer`) | `src/application/dtos.py`, `src/application/services/regulation_query_service.py` |
| UI -> Plan search service | `PlanSearchQuery` (`plan_id`/`location`/`keyword`, `max_results`, optional vision flag) | `PlanSearchResult` (`plans`, `query`, `total_found`, `execution_time_ms`) | `src/application/dtos.py`, `src/application/services/plan_search_service.py` |
| Application -> Plan repository | `get_by_id`, `search_by_location`, `search_by_keyword`, `search_by_status`, `get_plan_image` | `Plan` entities / image bytes / empty results on failure | `src/domain/repositories/__init__.py`, `src/infrastructure/repositories/iplan_repository.py` |
| Application -> Regulation repository | `search`, `get_by_id`, `get_by_type`, `get_applicable_to_location`, `add_regulation`, `get_statistics` | `Regulation` entities + stats dictionary | `src/domain/repositories/__init__.py`, `src/infrastructure/repositories/chroma_repository.py` |
| CLI -> Vector build pipeline | `build/status/check` CLI args | terminal output + persisted Chroma updates + optional stats artifacts | `scripts/build_vectordb_cli.py`, `src/vectorstore/unified_pipeline.py` |
| CLI -> DataStore | CLI args (`status/search/export/backup`) | terminal output + exported JSON artifacts | `scripts/data_cli.py`, `src/data_management/data_store.py` |

## External Endpoint-Family Artifact Contract Map (`COR-02`)

| Artifact ID | Endpoint-family assumption | Explicit contract coverage | Failure-mode triage link |
| --- | --- | --- | --- |
| `ART-EXT-001` | iPlan PlanningPublic endpoint-family payloads keep stable planning identity fields used by search and retrieval flows. | `tests/integration/data_contracts/test_boundary_payload_contracts.py::test_iplan_endpoint_family__source_and_metadata_contract_fields_present`, `tests/integration/iplan/test_iplan_sample_data_quality.py::test_iplan_like_metadata__contains_plan_number_and_municipality`, `tests/integration/iplan/test_iplan_sample_data_quality.py::test_iplan_endpoint_family__plan_number_pattern_on_iplan_sources` | `docs/troubleshooting.md` -> `Endpoint-family contract drift (COR-02)` |
| `ART-EXT-002` | MAVAT attachment URL semantics remain bounded and explicit: deterministic local checks validate metadata invariants; live URL behavior stays opt-in. | Deterministic boundary contract checks in `tests/integration/data_contracts/test_boundary_payload_contracts.py`; optional live rehearsal in `tests/integration/iplan/test_pydoll_live_mavat_documents__optional.py`; attachment typing semantics in `tests/unit/data_management/test_mavat_artifact_type_guessing.py` | `docs/troubleshooting.md` -> `Endpoint-family contract drift (COR-02)` and `Live-network rehearsal policy` |

### Endpoint-Family Failure Semantics
- iPlan-family contract drift is treated as an integration contract failure, not a silent degrade:
  - required identity/metadata fields (`source`, `plan_number`, `municipality`) must remain present on iPlan-family records.
  - canonical verification commands:
    - `./venv/bin/python -m pytest tests/integration/data_contracts/test_boundary_payload_contracts.py -q`
    - `./venv/bin/python -m pytest tests/integration/iplan/test_iplan_sample_data_quality.py -q`
- MAVAT-family live endpoint variability is intentionally bounded:
  - deterministic contract checks stay in default integration suites.
  - live endpoint verification remains opt-in via `RUN_NETWORK_TESTS=1`.

## Request and Response Invariants
- `RegulationQuery.query_text` must be non-empty for meaningful retrieval.
- `PlanSearchQuery` precedence is deterministic: `plan_id` > `location` > `keyword`.
- Service boundaries should return structured empty/degraded results on dependency failures, not uncaught exceptions.
- DTO timestamps and execution metadata are generated in application services.

## Error Semantics
- External boundary failures are logged and converted to safe result objects where possible.
- Optional LLM/Vision integrations fail closed (core flows remain available).
- Build/persistence failures surface explicit CLI errors and non-zero exits.

## Verification and Contract Coverage
- Marker suites provide contract checks:
  - `unit` + `data_contracts`
  - `integration` + `data_contracts`
  - `e2e` smoke + output sanity
- Canonical commands are in `docs/manifest/09_runbook.md` (`CMD-004`..`CMD-007`).
- CI enforces the marker contract gates in `.github/workflows/ci.yml`.

## Known Gaps
- No stable public HTTP API boundary is currently exposed as the canonical runtime interface.
- Contract versioning policy for output payloads is still lightweight and docs-driven.
