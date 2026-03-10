# Test Architecture Plan

## Proposed folder tree
Current structure is already aligned with the target pyramid and does not require a large move/rename refactor:

```text
tests/
  unit/
    application/
    data_contracts/
    data_management/
    data_pipeline/
    domain/
    infrastructure/
    vectorstore/
  integration/
    data_contracts/
    iplan/
    vectordb/
  e2e/
    data_contracts/
    webui/
  helpers/
  conftest.py
```

## Module responsibilities
- `unit/`: pure logic and deterministic behavior; no live network/browser side effects.
- `integration/`: boundary contracts (persistence, repository wiring, controlled external boundary behavior).
- `e2e/`: minimal critical-flow smoke checks.
- `helpers/`: shared factories/assertions/fakes, kept lightweight.

## Old -> New mapping table
No path moves are required in this packet. Existing topology already matches target architecture.

## Fixture strategy
- Keep `tests/conftest.py` minimal and boundary-safe.
- Keep feature-specific fixtures close to local modules.
- Continue using `tests/helpers/*` for shared object builders/assertions.

## Dependency strategy
- Real dependencies:
  - Chroma/persistence in integration tests.
  - optional live iPlan/pydoll tests remain explicitly marked/skipped when env unsupported.
- Unit tests:
  - remain deterministic and dependency-light.
- Time/clock handling:
  - no major clock-coupled flake sources currently detected.

## Test pyramid and selection policy
- Target ratio remains unit-majority with selected integration and small e2e set.
- Marker commands:
  - unit: `./venv/bin/python -m pytest -m unit`
  - integration: `./venv/bin/python -m pytest -m integration`
  - e2e: `./venv/bin/python -m pytest -m e2e`
  - contracts: `./venv/bin/python -m pytest -m data_contracts`

## Coverage goals
- Must-cover flows:
  - regulation query fallback and filtering
  - vector store contracts and persistence behavior
  - plan-search behavior and boundary failure handling
- Add explicit coverage threshold once CI baseline exists.

## Implementation packet decision
- Appetite: small
- Strategy:
  - do not perform large test file moves this packet,
  - capture landscape + architecture plan,
  - gate next test refactor work behind CI baseline and release-discipline packet completion.
