# Tutorials

## Tutorial: Local Query + Data Maintenance Loop

### Goal
Run the app, validate data/vector status, and execute one maintenance command.

### Steps
1. Install and setup:
```bash
./setup.sh
```
2. Start app:
```bash
./run_webapp.sh
```
3. In another terminal, inspect data status:
```bash
python3 scripts/data_cli.py status -v
```
4. Inspect vector DB status:
```bash
python3 scripts/quick_status.py
```
5. Optional build refresh:
```bash
python3 scripts/build_vectordb_cli.py build --max-plans 10 --no-vision
```

### Checkpoint
You should see CLI status output and no fatal errors in app startup.

### Common issues
- Missing optional dependencies: see `docs/troubleshooting.md`.
- External API instability: retry with reduced scope and inspect logs.
