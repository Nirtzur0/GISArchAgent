# Contributing

Thanks for contributing to GISArchAgent.

## 1) Development Setup

```bash
./setup.sh
```

For local app runs:

```bash
./run_webapp.sh
```

## 2) Change Scope Expectations

- Keep changes focused and minimal.
- Do not mix unrelated refactors into functional fixes.
- When changing runtime behavior, update relevant docs in the same packet.

## 3) Required Local Verification Before PR

Run the baseline checks from `docs/manifest/09_runbook.md`:

```bash
./venv/bin/python -m pytest -m unit
./venv/bin/python -m pytest -m integration
./venv/bin/ruff check . --select E9,F63,F7 --exclude project-prompts
python3 scripts/check_dependency_sync.py --requirements requirements.txt --dev-requirements requirements-dev.txt --lock requirements.lock --doc docs/reference/dependencies.md
python3 project-prompts/scripts/prompts_manifest.py --check
python3 project-prompts/scripts/system_integrity.py --mode prompt_pack --root project-prompts
```

If your change touches onboarding/reference boundary docs, also run:

```bash
for file in docs/README.md docs/INDEX.md docs/reference/configuration.md docs/artifacts/README.md; do
  for id in artifact:ART-EXT-001 artifact:ART-EXT-002 artifact:ART-EXT-003 artifact:ART-EXT-004 artifact:ART-EXT-005; do
    rg -q "$id" "$file" || { echo "$file missing $id"; exit 1; }
  done
done
echo "onboarding_artifact_links_ok files=4 ids=5"
```

## 4) Testing Policy

- Prefer marker-based test runs (`unit`, `integration`, `e2e`, `data_contracts`).
- Keep live-network rehearsal optional and bounded (`RUN_NETWORK_TESTS=1`).
- Add or update tests when behavior changes.

## 5) Documentation Sync

When behavior, commands, or workflows change, update:

- `docs/implementation/00_status.md`
- `docs/implementation/03_worklog.md`
- Relevant docs under `docs/manifest/`, `docs/reference/`, `docs/how_to/`, or `docs/troubleshooting.md`

## 6) Pull Request Notes

PR descriptions should include:

- What changed and why.
- Commands run for verification.
- Any known limitations or deferred follow-ups.
