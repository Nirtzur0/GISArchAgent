# Documentation Home

Use `docs/INDEX.md` as the canonical entrypoint for all project documentation.

## Canonical Navigation
- User docs (Diataxis):
  - `docs/getting_started/*`
  - `docs/tutorials/*`
  - `docs/how_to/*`
  - `docs/reference/*`
  - `docs/explanation/*`
- Engineering control docs:
  - `docs/manifest/*`
  - `docs/implementation/*`

## External Dependency Boundaries (Onboarding)
Use these artifact IDs when reading or updating boundary assumptions:
- iPlan ArcGIS endpoint family: `artifact:ART-EXT-001`
- MAVAT attachment URL family: `artifact:ART-EXT-002`
- Gemini provider behavior: `artifact:ART-EXT-003`
- `pydoll-python` runtime dependency: `artifact:ART-EXT-004`
- Chroma persistence boundary: `artifact:ART-EXT-005`

Related entrypoints:
- `docs/reference/configuration.md` (config-to-boundary mapping)
- `docs/troubleshooting.md` (boundary triage paths)
- `docs/artifacts/index.json` (artifact metadata source of truth)
- `docs/manifest/09_runbook.md` (`CMD-041`: onboarding/reference artifact-link guardrail command)
- `CONTRIBUTING.md` (contributor workflow and verification policy)
- `LICENSE` (repository license metadata)

## Legacy Deep-Dive Pages
These pages are retained for context and deeper technical history:
- `docs/ARCHITECTURE.md`
- `docs/HOW_IT_WORKS.md`
- `docs/BUILD_VECTORDB_GUIDE.md`
- `docs/UNIFIED_PIPELINE.md`
- `docs/TEST_ARCHITECTURE.md`
- `docs/VECTOR_DB_MANAGEMENT.md`
- `docs/VECTOR_DB_VALIDATION.md`
- `docs/GENERIC_PIPELINE_ARCHITECTURE.md`
- `docs/SYSTEM_FLOW.md`
- `docs/IPLAN_DATA_SOURCES_MAP.md`

If any legacy page contradicts `docs/manifest/*` or `docs/implementation/*`, treat manifest/implementation docs as source of truth.
