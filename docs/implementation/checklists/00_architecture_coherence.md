# Architecture Coherence Checklist

## Scope and Readiness
- Appetite: medium
- Packet state: downhill
- Readiness verdict: GO_WITH_RISKS
- Rationale: architecture boundaries and legacy-doc coherence are aligned to repo reality; remaining risks are observability backend depth and CI quality-gate breadth.

## C4 Coverage (L1/L2/L3 where used)
- [x] C4-1 system context documented and mapped to real boundaries.
- [x] C4-2 container boundaries documented and mapped to code paths.
- [x] C4-3 high-risk component views documented for query/search/build areas.
- [x] Quality scenarios included and aligned to current runtime behavior.

## Runtime and Deployment Coverage
- [x] Runtime scenario for regulation query documented.
- [x] Runtime scenario for plan search documented.
- [x] Failure-path runtime scenario documented.
- [x] Deployment/trust boundaries documented.

## Docs Architecture vs Code Reality (Drift Diff)
- [x] `docs/manifest/01_architecture.md` reflects current Streamlit + service + repository + pipeline structure.
- [x] Legacy architecture docs (`docs/ARCHITECTURE.md`, `docs/HOW_IT_WORKS.md`) are reconciled and point to manifest truth.
- [x] CI architecture references actual workflow files (`.github/workflows/ci.yml`).
- [x] Observability section references implemented structured events/correlation, backend sinks, and query CLI (`docs/manifest/07_observability.md`); visual dashboard UX remains deferred.
- [x] Dedicated tag/release workflow is implemented (`.github/workflows/release.yml`) and mapped in release docs.

## Invariants and Verification Commands
- [x] Invariant: key runtime entrypoints still exist.
  - Verify: `test -f app.py && test -f scripts/data_cli.py && test -f scripts/build_vectordb_cli.py`
- [x] Invariant: marker taxonomy remains explicit.
  - Verify: `rg -n "^markers =|unit:|integration:|e2e:|data_contracts:" pytest.ini`
- [x] Invariant: CI baseline workflow exists and is wired.
  - Verify: `test -f .github/workflows/ci.yml && rg -n "pytest -m unit|pytest -m integration|pytest -m e2e|pytest -m data_contracts" .github/workflows/ci.yml`
- [x] Invariant: prompt-pack integrity checks remain runnable.
  - Verify: `python3 project-prompts/scripts/prompts_manifest.py --check && python3 project-prompts/scripts/system_integrity.py --mode prompt_pack --root project-prompts`

## Now / Not now
### Now
- [x] Manifest architecture/contracts/data-model refreshed against current code boundaries.
- [x] Legacy architecture pages reconciled to avoid contradictory claims.
- [x] Coherence verdict updated and linked to status/worklog.

### Not now
- [ ] Add visual dashboard UX and richer resource saturation signals beyond JSONL + CLI query baseline.
- [ ] Expand CI quality coverage beyond incremental maintained surfaces.
- [ ] Broader platform decomposition beyond current milestone scope.

## Blockers / TODOs
- TODO: add visual dashboard/query UX and richer saturation signals (memory/disk/network).
- TODO: expand CI quality gates beyond incremental maintained surfaces.
