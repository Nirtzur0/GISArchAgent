# Conventions

## Repository Layout
- `src/`: domain/application/infrastructure/runtime modules.
- `scripts/`: operational and data-maintenance CLIs.
- `tests/`: pyramid structure (`unit`, `integration`, `e2e`, helpers).
- `docs/`: canonical docs root for manifest + implementation tracking.
- `data/`: local artifacts (gitignored except `.gitkeep`).

## Code Conventions
- Python-first codebase with typed interfaces at service/repository boundaries.
- Prefer small modules and explicit dependency wiring via `ApplicationFactory`.
- Keep boundary adapters in infrastructure modules; keep business behavior in domain/application layers.

## Testing Conventions
- Use pytest markers from `pytest.ini`; avoid ad-hoc marker additions without config updates.
- Keep unit tests deterministic (no real network/browser).
- Use integration/data-contract tests for boundary and schema invariants.

## Docs Conventions
- `docs/manifest/*`: what/why design and policy truth.
- `docs/implementation/*`: current packet status, checklists, reports, and worklog.
- Update `docs/implementation/00_status.md` and `03_worklog.md` in the same packet as meaningful changes.

## Naming and Path Rules
- Prefer descriptive snake_case module filenames in Python.
- Keep script names action-oriented (`build_*`, `quick_*`, `data_*`).
- Use relative repo paths in docs for portability.

## Change Discipline
- Default to minimal-diff changes aligned with explicit acceptance criteria.
- Avoid broad refactors without a scoped checklist item and verification evidence.
