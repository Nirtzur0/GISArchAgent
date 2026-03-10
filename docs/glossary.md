# Glossary

- **Core Objective**: canonical statement of what the project is building and why (`docs/manifest/00_overview.md`).
- **DOCS_ROOT**: root documentation directory locked by `docs/.prompt_system.yml`.
- **Manifest docs**: `docs/manifest/*`, design and policy truth.
- **Implementation docs**: `docs/implementation/*`, execution evidence and progress.
- **Marker suite**: pytest subset selected via markers (`unit`, `integration`, `e2e`, `data_contracts`).
- **Vector DB**: local Chroma persistence for regulation retrieval (`data/vectorstore`).
- **Alignment gate**: objective-drift check (`docs/implementation/checklists/07_alignment_review.md`).
- **Architecture coherence gate**: diagram/contracts/data-model drift check (`docs/implementation/checklists/00_architecture_coherence.md`).
