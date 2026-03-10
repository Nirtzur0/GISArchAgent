# Data Model

## Core Domain Entities

### Plan
- Identity and context: `id`, `name`, `location`, `region`, `status`, `zone_type`, `plan_type`.
- Spatial data: optional `geometry`, optional `extent`.
- Source metadata and optional dates.
- Evidence: `src/domain/entities/plan.py`.

### Regulation
- Identity and classification: `id`, `type`, `title`.
- Content model: `content`, optional `summary`, `jurisdiction`, `applicable_zones`.
- Optional lifecycle metadata (effective/expiry/update timestamps).
- Evidence: `src/domain/entities/regulation.py`.

### VisionAnalysis
- Identity: `plan_id`, `image_hash`.
- Content: description, OCR text, extracted structures, confidence metadata.
- Runtime metadata: provider/model/tokens/cost/cache markers.
- Evidence: `src/domain/entities/analysis.py`.

### BuildingRights
- Deterministic value object for zoning-derived constraints.
- Includes FAR/coverage/height/setbacks/parking/open-space fields and invariants.
- Evidence: `src/domain/value_objects/building_rights.py`.

## Persistence Surfaces

### Local JSON Data Store
- Paths: `data/raw/*`.
- Managed by `src/data_management/data_store.py` and `scripts/data_cli.py`.
- Stores iPlan-derived feature dictionaries and export payloads.

### Vector Store (Chroma)
- Paths: `data/vectorstore/*`.
- Adapter: `src/infrastructure/repositories/chroma_repository.py`.
- Indexes regulation chunks/metadata for semantic retrieval.

### Cache Artifacts
- Paths: `data/cache/*` and `data/cache/pydoll/*`.
- Managed by `src/infrastructure/services/cache_service.py` and pydoll fetchers.
- Stores TTL-backed analysis/discovery/pipeline artifacts.

### Pipeline Stats/Artifacts
- Example stats artifact: `data/cache/pipeline_stats.json` from unified pipeline runs.
- Evidence: `src/vectorstore/unified_pipeline.py`.

## Integrity and Consistency Rules
- Required fields, ranges, missingness, and shape invariants are enforced by `data_contracts` tests.
- `Regulation.id` stability is required for idempotent upsert and dedupe behavior.
- Vision cache entries should be keyed deterministically to plan/image identity and expire safely.
- Runtime persistence under `data/` stays out of version control.

## Data Lifecycle Notes
- Bootstrap path can initialize vector store from bundled sample sources.
- Ongoing updates occur via unified build pipeline (`scripts/build_vectordb_cli.py`).
- Query services consume immutable DTO snapshots produced at request time.

## Known Gaps
- Formal schema versioning and migration policy for persisted artifacts is minimal.
- Cross-store lineage metadata (raw -> parsed -> indexed) is only partially documented.
