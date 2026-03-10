# Design Decisions

Canonical ADR-style decisions are tracked in:
- `docs/manifest/03_decisions.md`

## Decision themes
- Keep stack continuity (Python + Streamlit + Chroma) for this cycle.
- Enforce docs-first lifecycle with manifest/implementation split.
- Gate broader implementation with architecture coherence and alignment checks.

## Open design questions
- Whether to introduce a stable API boundary beyond UI/CLI.
- How to phase CI/release automation with minimal churn.
