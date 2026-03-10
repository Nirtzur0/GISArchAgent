# Data Formats Reference

## Regulation DTO shape (high-level)
Source: `src/application/dtos.py`, `src/domain/entities/regulation.py`

Key fields:
- `id` (string)
- `type` (enum-like string)
- `title` (string)
- `content` (string)
- `jurisdiction` (string)
- optional metadata/tags/date fields

## Plan DTO shape (high-level)
Source: `src/domain/entities/plan.py`

Key fields:
- `id`, `name`, `location`
- status/zone metadata
- optional geometry/extent

## Exported data store JSON
Source: `scripts/data_cli.py export`

Structure:
```json
{
  "metadata": {
    "exported_at": "ISO timestamp",
    "source": "GISArchAgent Data Store",
    "count": 0
  },
  "features": []
}
```

## Vector DB artifacts
- Chroma persistence under `data/vectorstore/`.
- Metadata/status accessed via repository and quick-status scripts.
