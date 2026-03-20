# Quickstart

## Outcome
Start the app locally, run one core query flow, and validate test health.

## 1) Setup
```bash
./setup.sh
```

## 2) Run app
```bash
./run_webapp.sh
```
Open `http://127.0.0.1:5173`.

## 3) Try core workflow
- In the workspace, search local plans and select one.
- Ask a regulation question against the selected plan context.
- Optionally navigate to the map, analyzer, and data pages.

## 4) Validate tests
```bash
./venv/bin/python -m pytest -m unit
```

## 5) Check vector DB status
```bash
python3 scripts/quick_status.py
```

## Interpreting success
- Backend and frontend both start without import errors.
- Workspace UI is interactive and returns a result.
- Unit marker suite passes.
- Vector DB status command prints a non-crashing status report.
