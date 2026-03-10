# Release Workflow Mapping

## Current State
- Baseline CI workflow exists at `.github/workflows/ci.yml` for PR/push test and prompt-pack checks.
- Dedicated tag/release workflow exists at `.github/workflows/release.yml`.

## Trigger Policy
- Release workflow trigger: push tags matching `v*`.
- Optional manual dry-run trigger: `workflow_dispatch` (validation job only unless ref is a tag).

## Workflow-to-Runbook Command Mapping
### `release-validation` job
- `CMD-018`: verify required release artifacts exist.
- `CMD-041`: enforce onboarding/reference boundary citation guardrail.
- `CMD-023`: validate release tag/changelog coherence.
- `CMD-004`: run unit marker suite.
- `CMD-005`: run integration marker suite.
- `CMD-006`: run e2e marker suite.
- `CMD-007`: run data-contract marker suite.
- `CMD-016`: prompt manifest integrity check.
- `CMD-017`: prompt system integrity check.

### Pre-tag documentation guardrails
- `CMD-041`: verify onboarding/reference boundary docs still include required `artifact:ART-EXT-*` citations.
- Guardrail is enforced in `release-validation` and should still be run locally pre-tag for fast feedback.

### `publish-github-release` job
- Runs only when `github.ref` is a tag.
- Creates/updates GitHub Release using generated notes (`softprops/action-gh-release`).

## Human Release Flow
1. Prepare artifacts:
   - update `CHANGELOG.md`
   - update `docs/implementation/checklists/06_release_readiness.md`
   - add upgrade notes when compatibility impact exists
2. Validate locally (recommended pre-tag):
   - `CMD-018`
   - `CMD-041`
   - `CMD-023` (with your target tag)
   - `CMD-004`, `CMD-005`, `CMD-006`, `CMD-007`
   - `CMD-016`, `CMD-017`
3. Create and push version tag:
   - `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
   - `git push origin vX.Y.Z`
4. Confirm workflow success in GitHub Actions and verify release artifact.

## Remaining Improvements
- Extend semantic validation to enforce richer changelog section structure/content.
- Optionally attach build artifacts/bundles when packaging pipeline is introduced.
