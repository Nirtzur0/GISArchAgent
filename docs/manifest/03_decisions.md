# Decisions Log

This file records significant structural or policy decisions that affect maintainability, test signal, or developer workflow.

## 2026-02-06: Introduce Marker Taxonomy and Pyramid Split

- Decision: Standardize pytest markers (`unit`, `integration`, `e2e`, `data_contracts`, plus boundary markers like `db`, `ui`).
- Decision: Split tests into `tests/unit`, `tests/integration`, `tests/e2e` to align with the test pyramid and improve debuggability.
- Rationale:
  - Prevents “all-integration” suites where failures are expensive and hard to localize.
  - Enables fast local workflows (`-m unit`) and reduces flake risk by isolating boundary tests.

