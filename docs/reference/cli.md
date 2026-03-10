# CLI Reference

## Data CLI
Entrypoint: `python3 scripts/data_cli.py`

Commands:
- `status [-v]`
- `search [--district ...] [--city ...] [--status ...] [--text ...] [--limit N] [-v]`
- `export <output_file> [--district ...] [--city ...] [--status ...] [--pretty]`
- `backup list [--limit N]`
- `backup restore <backup_file> [--force]`

## Vector DB CLI
Entrypoint: `python3 scripts/build_vectordb_cli.py`

Commands:
- `status [-v]`
- `build [--max-plans N] [--rebuild] [--headless] [--no-documents] [--no-vision] [-v]`
- `check`
- `export --output <path> --format [json|csv]`

## Wrapper
- `python3 build_vectordb.py ...` forwards arguments to `scripts/build_vectordb_cli.py`.

## Quick Status Utility
Entrypoint: `python3 scripts/quick_status.py`

Commands:
- Default vector DB status:
  - `python3 scripts/quick_status.py`
  - `python3 scripts/quick_status.py vectordb`
- External dependency health snapshot bundle:
  - `python3 scripts/quick_status.py external [--since-minutes N] [--events-limit N] [--alerts-limit N] [--run-drills] [--drill-timeout-seconds N]`

Notes:
- `external --run-drills` runs deterministic non-network boundary checks for iPlan/MAVAT contract surfaces.
- `external` prints `warning_context` when `status=WARNING` and includes `warning_noise_profile` counters for historical-noise windows so first-pass triage can identify recurring build-timeout sev1 dominance.
- Optional live-network rehearsal remains separate and opt-in (`RUN_NETWORK_TESTS=1`).

## Dependency Sync Utility
Entrypoint: `python3 scripts/check_dependency_sync.py`

Commands:
- Check mode:
  - `--requirements requirements.txt --dev-requirements requirements-dev.txt --lock requirements.lock --doc docs/reference/dependencies.md`
- Regenerate docs inventory:
  - same args + `--write-doc`

## Observability CLI
Entrypoint: `python3 scripts/observability_cli.py`

Commands:
- `summary [--events-limit N] [--alerts-limit N] [--since-minutes N] [--as-json]`
- `events [--component <name>] [--operation <name>] [--outcome <name>] [--since-minutes N] [--limit N]`
- `alerts [--severity sev1|sev2|sev3] [--route <owner>] [--since-minutes N] [--limit N]`
- `dashboard [--events-limit N] [--alerts-limit N] [--since-minutes N] [--top-reasons N]`

Notes:
- Reads local backend sinks under `data/cache/observability/` by default.
- `dashboard` provides an operator-oriented terminal view (operations, degraded reasons, saturation snapshot, alert severities).

## Documentation Guardrail
Entrypoint: shell command from runbook (`CMD-041`)

Command:
- `for file in docs/README.md docs/INDEX.md docs/reference/configuration.md docs/artifacts/README.md; do for id in artifact:ART-EXT-001 artifact:ART-EXT-002 artifact:ART-EXT-003 artifact:ART-EXT-004 artifact:ART-EXT-005; do rg -q "$id" "$file" || { echo "$file missing $id"; exit 1; }; done; done; echo "onboarding_artifact_links_ok files=4 ids=5"`

Notes:
- Use this after editing onboarding/reference boundary docs to prevent citation drift.
- Canonical command-map source: `docs/manifest/09_runbook.md` (`CMD-041`).
