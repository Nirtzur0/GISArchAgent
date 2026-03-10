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
Open `http://localhost:8501`.

## 3) Try core workflow
- In the app, use the query assistant on the main page.
- Optionally navigate to plan analyzer/data management pages.

## 4) Validate tests
```bash
./venv/bin/python -m pytest -m unit
```

## 5) Check vector DB status
```bash
python3 scripts/quick_status.py
```

## Interpreting success
- App starts without import errors.
- Query UI is interactive and returns a result.
- Unit marker suite passes.
- Vector DB status command prints a non-crashing status report.
