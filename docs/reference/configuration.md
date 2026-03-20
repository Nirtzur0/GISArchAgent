# Configuration Reference

## Settings source
- `src/config.py` via `pydantic-settings`
- environment file: `.env`

## Key configuration fields
| Name | Default | Purpose |
| --- | --- | --- |
| `openai_base_url` | `""` | Optional OpenAI-compatible API base URL used by synthesis and upload analysis |
| `openai_api_key` | `None` | Optional provider key |
| `openai_model` | `gpt-4o-mini` | Text synthesis model name |
| `openai_vision_model` | `gpt-4o-mini` | Vision analysis model name |
| `anthropic_api_key` | `None` | Optional provider key |
| `google_api_key` | `None` | Legacy compatibility field |
| `gemini_api_key` | `None` | Legacy compatibility field |
| `chroma_persist_directory` | `./data/vectorstore` | Local vector DB path |
| `iplan_base_url` | iPlan URL | iPlan system base |
| `iplan_api_url` | iPlan ArcGIS URL | API endpoint base |
| `log_level` | `INFO` | Runtime logging level |

Canonical provider env surface:

```bash
OPENAI_BASE_URL=
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OPENAI_VISION_MODEL=gpt-4o-mini
```

Set `OPENAI_BASE_URL` only when you have a real OpenAI-compatible API endpoint. When it is left blank, the app stays in retrieval-only mode and disables upload analysis explicitly.

Legacy fields remain readable for compatibility, but new setup and docs should use the `OPENAI_*` variables.

## External dependency boundaries (artifact-linked)
Use these IDs when documenting or changing boundary assumptions:

| Boundary | Config/runtime surface | Artifact | Notes |
| --- | --- | --- | --- |
| iPlan ArcGIS endpoint family | `iplan_base_url`, `iplan_api_url` | `artifact:ART-EXT-001` | Primary planning data endpoint family; verify with boundary contract tests and `CMD-040`. |
| MAVAT attachment URL family | `src/data_management/pydoll_fetcher.py` URL patterns | `artifact:ART-EXT-002` | URL semantics and attachment fetch behavior; deterministic checks + opt-in live rehearsal path. |
| Gemini provider behavior | `gemini_api_key`, `google_api_key` | `artifact:ART-EXT-003` | Missing/failed provider should degrade gracefully with deterministic fallback semantics. |
| `pydoll-python` browser runtime | Chrome/CDP runtime + optional live drill env vars | `artifact:ART-EXT-004` | Runtime dependency for MAVAT scraping/build workflows; live path remains opt-in. |
| Chroma local persistence | `chroma_persist_directory` | `artifact:ART-EXT-005` | Local-first vector persistence boundary for retrieval workflows. |

Operational links:
- Boundary snapshot bundle: `CMD-040` in `docs/manifest/09_runbook.md`
- Boundary triage guidance: `docs/troubleshooting.md`
- Artifact metadata source: `docs/artifacts/index.json`

## Security notes
- Never commit `.env`.
- Avoid logging secret values.
