# Test Architecture (Target)

This document is the **post-audit target** test architecture for GISArchAgent.

Goals:
- Make tests easy to find by **flow boundary** (unit/integration/e2e).
- Prefer **behavioral** assertions over internals.
- Add explicit **data contract** tests (required fields, missingness, ranges, enums, uniqueness).
- Keep the suite deterministic and CI-friendly (no sleeps; no real network in unit tests).

## Proposed folder tree

```text
tests/
  helpers/
    assertions.py
    factories.py
    fakes.py
  unit/
    application/
      test_regulation_query_service__fallback.py
    data_contracts/
      test_required_fields.py
      test_missingness_thresholds.py
      test_value_ranges.py
      test_allowed_categories.py
      test_shape_and_uniqueness.py
    data_pipeline/
      test_iplan_parse_record.py
      test_vectordb_loader_mapping.py
    domain/
      test_building_rights_calculator.py
      test_regulation_entity.py
    infrastructure/
      test_deterministic_embedding.py
  integration/
    data_contracts/
      test_boundary_payload_contracts.py
      test_persistence_contracts.py
    iplan/
      test_iplan_sample_data_quality.py
    vectordb/
      test_chroma_persistence.py
      test_repository_contract.py
      test_regulation_query_service_integration.py
  e2e/
    data_contracts/
      test_end_to_end_output_sanity.py
    webui/
      test_streamlit_smoke.py
  conftest.py
```

## Module responsibilities

### `tests/unit/`
- **Belongs:** pure logic (domain + application), parsers/mappers, deterministic utilities.
- **Must never:** touch real Chroma persistence, browser automation (Pydoll), or real network.
- **Markers:** `@pytest.mark.unit` (default), optionally `@pytest.mark.data_contracts`.

### `tests/integration/`
- **Belongs:** boundary contracts with real implementations: Chroma persistence, repository wiring, serialization.
- **Must never:** depend on production `data/` state or non-deterministic live iPlan discovery.
- **Markers:** `@pytest.mark.integration` plus boundary tags like `@pytest.mark.db`.

### `tests/e2e/`
- **Belongs:** minimal set of critical flow checks across layers (Streamlit script smoke; end-to-end query output sanity).
- **Must never:** be “deep” UI tests; keep assertions coarse and stable.
- **Markers:** `@pytest.mark.e2e`, plus `@pytest.mark.ui` where relevant.

### `tests/helpers/`
- **Belongs:** builders, fakes, and shared assertions.
- **Must never:** hide meaning; prefer explicit factories over magic fixtures.

## Fixture strategy

- `tests/conftest.py`:
  - Keep minimal: import-path setup + marker registration.
- Integration fixtures:
  - Create **temp** Chroma persistence directories via `tmp_path_factory` (module-scoped).
  - Initialize using deterministic sample regulations (factory auto-init path).
- No global mutable fixtures. Integration fixtures must be treated as **read-only** once initialized.

## Mocking strategy

- Mock only **external boundaries**:
  - LLM: fake object with deterministic `generate_answer`.
  - Vision/browser automation/network: unit tests never touch; integration tests avoid by using sample data.
- Prefer fakes over mocks for LLM.
- Time:
  - For parser contracts that stamp `datetime.now()`, patch the module-local `datetime` reference.

## Test pyramid + selection policy

- Target ratio: **~70% unit**, **~25% integration**, **~5% e2e**.
- Markers:
  - `unit`, `integration`, `e2e`
  - `data_contracts`
  - `db`, `ui`, `network`, `slow`
- Example commands:
  - Unit: `./venv/bin/python -m pytest -m unit`
  - Integration: `./venv/bin/python -m pytest -m integration`
  - E2E: `./venv/bin/python -m pytest -m e2e`
  - Full: `./venv/bin/python -m pytest`

## Old -> New mapping (high level)

| Old path | New path(s) | Reason |
|---|---|---|
| `tests/test_vectordb_integration.py` | `tests/integration/vectordb/*` + `tests/integration/data_contracts/*` | Split by responsibility; add explicit contract checks |
| `tests/test_iplan_integration.py` | `tests/integration/iplan/*` + `tests/unit/data_pipeline/*` + `tests/*/data_contracts/*` | Separate parser/loader unit behavior from DB integration and data contracts |
| `tests/test_webui_smoke.py` | `tests/e2e/webui/test_streamlit_smoke.py` | Clarify as E2E smoke; rename tests to convention |
