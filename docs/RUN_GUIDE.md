# Complete Application Run Guide

This guide is the practical run path for local operation and validation.
For canonical command IDs and latest command-map truth, use `docs/manifest/09_runbook.md`.

## Scope and Source of Truth
- Command map: `docs/manifest/09_runbook.md`
- Testing strategy: `docs/manifest/10_testing.md`
- Troubleshooting: `docs/troubleshooting.md`
- CLI specs: `docs/reference/cli.md`

## 1) Setup and Launch

### Environment bootstrap
```bash
./setup.sh
```

### Start the app
```bash
./run_webapp.sh
```

Then open the frontend URL printed by the script, usually `http://127.0.0.1:5173`.
If `8000` or `5173` are already occupied, the launcher prints the next free local ports and keeps the frontend pointed at the resolved backend automatically.

## 2) Core Verification (Automated)

Run the narrow canonical checks first:

```bash
./venv/bin/python -m pytest tests/integration/api/test_fastapi_endpoints.py -q
cd frontend && npm run build
cd frontend && npm run test:e2e
```

Then run the broader marker suites from the repository venv:

```bash
./venv/bin/python -m pytest -m unit
./venv/bin/python -m pytest -m integration
./venv/bin/python -m pytest -m e2e
./venv/bin/python -m pytest -m data_contracts
```

Optional full-suite run:

```bash
./venv/bin/python -m pytest
```

## 3) Manual UI Walkthrough

After `./run_webapp.sh`, verify these flows:

### Workspace page
- Select a plan from the local catalog.
- Run a grounded regulation query and confirm retrieval-only messaging is understandable when no provider is configured.
- Switch to `Live iPlan` and confirm degraded live-search warnings are explicit instead of hanging silently.

### Investigation page
- Load map layers and apply filters.
- Confirm marker popups and summary counters update.

### Feasibility page
- Run building-rights calculations with sample inputs.
- Validate charts/tables render and no UI errors appear.

### Operations page
- Check provider state, scraper state, and vector DB status.
- Run safe maintenance actions (status/check paths before rebuild).

## 4) CLI Operations

### Data store CLI
```bash
python3 scripts/data_cli.py status -v
python3 scripts/data_cli.py search --city "ירושלים"
python3 scripts/data_cli.py export out/plans_jerusalem.json --city "ירושלים" --pretty
```

### Vector DB pipeline CLI
```bash
python3 scripts/build_vectordb_cli.py check
python3 scripts/build_vectordb_cli.py status
python3 scripts/build_vectordb_cli.py build --max-plans 10 --no-vision
```

### Quick status and observability
```bash
python3 scripts/quick_status.py
python3 scripts/observability_cli.py dashboard --since-minutes 180 --events-limit 1000 --alerts-limit 500
python3 scripts/observability_cli.py summary --since-minutes 180 --events-limit 2000 --alerts-limit 1000 --as-json
```

## 5) External Dependency Triage Path

Use the one-shot snapshot bundle first:

```bash
python3 scripts/quick_status.py external --since-minutes 180 --events-limit 1000 --alerts-limit 500 --run-drills
```

If output shows `status=WARNING`, follow `warning_context` guidance in:
- `docs/manifest/09_runbook.md` (`CMD-040`)
- `docs/troubleshooting.md`

Targeted slices:

```bash
python3 scripts/observability_cli.py events --operation build --since-minutes 60 --limit 100
python3 scripts/observability_cli.py events --outcome error --since-minutes 60 --limit 100
python3 scripts/observability_cli.py alerts --since-minutes 60 --limit 50
```

## 6) Optional Live-Network Rehearsal

Live provider checks are opt-in and bounded.

```bash
RUN_NETWORK_TESTS=1 \
RUN_NETWORK_REHEARSAL_MAX_ATTEMPTS=2 \
RUN_NETWORK_REHEARSAL_TIMEOUT_SECONDS=45 \
./venv/bin/python -m pytest tests/integration/iplan/test_pydoll_live_mavat_documents__optional.py -q
```

Do not add this lane to default CI gates.

## 7) Documentation Guardrails

After editing onboarding/reference boundary docs, run:

```bash
for file in docs/README.md docs/INDEX.md docs/reference/configuration.md docs/artifacts/README.md; do
  for id in artifact:ART-EXT-001 artifact:ART-EXT-002 artifact:ART-EXT-003 artifact:ART-EXT-004 artifact:ART-EXT-005; do
    rg -q "$id" "$file" || { echo "$file missing $id"; exit 1; }
  done
done
echo "onboarding_artifact_links_ok files=4 ids=5"
```

## 8) Notes on Legacy References

This guide intentionally avoids deprecated references from retired top-level integration test files.
Use marker-driven commands and current test paths under `tests/unit/`, `tests/integration/`, and `tests/e2e/`.
