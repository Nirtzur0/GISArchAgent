# How-To: Run End-to-End

## Goal
Execute the core local workflow with repo-native commands.

## Steps
1. Setup:
```bash
./setup.sh
```

2. Run app:
```bash
./run_webapp.sh
```

3. Run test markers:
```bash
./venv/bin/python -m pytest -m unit
./venv/bin/python -m pytest -m integration
./venv/bin/python -m pytest -m e2e
cd frontend && npm run test:e2e
```

4. Inspect data/vector status:
```bash
python3 scripts/data_cli.py status -v
python3 scripts/quick_status.py
```

5. Inspect observability summary:
```bash
python3 scripts/observability_cli.py summary --events-limit 200 --alerts-limit 200
python3 scripts/observability_cli.py alerts --since-minutes 60 --limit 20
```

## Expected outcomes
- Marker suites complete without fatal errors.
- `pytest -m e2e` covers the maintained FastAPI smoke path, and Playwright covers the maintained React browser flow.
- App loads and primary pages are reachable.
- Status commands produce structured output.
- Observability summary prints event/alert counts and latency p95 by operation.
