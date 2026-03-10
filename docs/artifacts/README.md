# Artifact Store

This directory is the canonical local store for load-bearing external artifacts.

## Purpose
- Keep external evidence re-findable and auditable.
- Link decisions, assumptions, and implementation choices to stable artifact IDs.
- Reduce citation drift for endpoint/provider/runtime assumptions.

## Layout
```text
docs/artifacts/
  README.md
  index.json
  blobs/
  excerpts/
```

- `index.json` is the machine-readable source of truth.
- `blobs/` holds immutable local snapshots (when captured).
- `excerpts/` holds short human notes/snippets tied to artifact IDs.

## Metadata Policy
- Every load-bearing external artifact must include:
  - `id` (stable, unique)
  - `kind`
  - `url`
  - `retrieved_at` (RFC3339 UTC)
- Prefer stable references:
  - endpoint base URLs with clear family notes,
  - provider/package canonical docs pages,
  - permalinks when code references are external.
- `sha256` and `local_path` are required only when a local blob snapshot is stored.

## ID Convention
- External runtime/provider artifacts: `ART-EXT-###`
- Process/policy artifacts: `ART-PROC-###`
- Use IDs in docs as `artifact:<ID>` (for example `artifact:ART-EXT-001`).

## Boundary Onboarding Map (OPP-03)
This map is the onboarding shortcut for external provider/runtime boundaries:

| Artifact | Boundary claim | Primary onboarding docs |
| --- | --- | --- |
| `artifact:ART-EXT-001` | iPlan endpoint family is the primary planning data boundary. | `docs/README.md`, `docs/INDEX.md`, `docs/reference/configuration.md` |
| `artifact:ART-EXT-002` | MAVAT attachment URL pattern drives document fetch semantics. | `docs/README.md`, `docs/INDEX.md`, `docs/reference/configuration.md` |
| `artifact:ART-EXT-003` | Gemini provider behavior shapes degraded fallback expectations. | `docs/README.md`, `docs/INDEX.md`, `docs/reference/configuration.md` |
| `artifact:ART-EXT-004` | `pydoll-python` + browser runtime is a bounded optional live dependency. | `docs/README.md`, `docs/INDEX.md`, `docs/reference/configuration.md` |
| `artifact:ART-EXT-005` | Chroma persistence is the local vectorstore boundary. | `docs/README.md`, `docs/INDEX.md`, `docs/reference/configuration.md` |

## Refresh Cadence Policy (OPP-01)
- Primary owner: maintainer on active implementation packet.
- Secondary owner: release maintainer for the next `v*` tag window.

Cadence rules:
- During active development, run the artifact freshness check (`CMD-039`) at least once every 7 days.
- Hard staleness limit: no `ART-EXT-*` entry may exceed 30 days without explicit rationale in worklog.
- Trigger-based refresh (run immediately, outside weekly cadence):
  - endpoint/provider/runtime incident that challenges an existing assumption,
  - dependency upgrade or environment change touching iPlan/MAVAT/Gemini/pydoll/Chroma boundaries,
  - decision/assumption updates that rely on changed external behavior.

Logging requirements:
- Update `retrieved_at` in `docs/artifacts/index.json` for every refreshed artifact entry.
- Record each refresh run in `docs/implementation/03_worklog.md` including:
  - date/time and owner,
  - artifact IDs reviewed (`ART-EXT-*`),
  - stale IDs (if any) and remediation decision,
  - follow-up docs updated (for example decisions/assumptions/observability).
- If an artifact remains stale by design (for example provider outage), log the deferral rationale and next retry date.

Command-map linkage:
- `CMD-039` in `docs/manifest/09_runbook.md` is the canonical freshness audit command.
