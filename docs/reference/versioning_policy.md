# Versioning Policy

## Policy
Use SemVer-style version numbers: `MAJOR.MINOR.PATCH`.

## Rules
- MAJOR: incompatible API/behavior changes.
- MINOR: backward-compatible feature additions.
- PATCH: backward-compatible fixes/docs-only corrections.

## Compatibility guidance
- Document any behavior-affecting changes in `CHANGELOG.md`.
- For major/minor releases, include upgrade guidance via `docs/how_to/upgrade_notes_template.md`.

## Deprecation policy
- Mark deprecated behavior in docs/changelog before removal.
- Provide at least one release cycle of migration guidance for non-trivial changes.
