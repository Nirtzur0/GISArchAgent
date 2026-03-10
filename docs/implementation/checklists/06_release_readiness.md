# Release Readiness Checklist

- [ ] Version bump policy applied for this release scope.
  - Verify: versioning decision matches `docs/reference/versioning_policy.md`.

- [ ] `CHANGELOG.md` updated with release notes.
  - Verify: unreleased/release entries reflect shipped changes.

- [ ] Upgrade notes completed (if compatibility impact exists).
  - Verify: `docs/how_to/upgrade_notes_template.md` instantiated for release.

- [ ] Test command-map checks pass.
  - Verify: runbook-linked marker suites pass (`CMD-004`, `CMD-005`, `CMD-006` as applicable).

- [ ] Onboarding artifact-link citation guardrail passes.
  - Verify: run `CMD-041` and confirm success output:
    - `onboarding_artifact_links_ok files=4 ids=5`

- [ ] CI tag/release workflow mapping verified.
  - Verify: `docs/reference/release_workflow.md` reflects actual automation state; TODOs explicit if missing.

- [ ] Release tag/changelog semantic check passes.
  - Verify: run `CMD-023` (`scripts/check_release_semantics.py`) with target tag.

- [ ] Status/worklog updated for release packet.
  - Verify: `docs/implementation/00_status.md` and `docs/implementation/03_worklog.md` updated.
