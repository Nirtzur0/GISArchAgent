#!/usr/bin/env python3
"""Validate release tag and changelog coherence."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SEMVER_TAG_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


def _read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Changelog file not found: {path}")
    return path.read_text(encoding="utf-8")


def _extract_release_version(tag: str) -> str:
    match = SEMVER_TAG_RE.match(tag.strip())
    if not match:
        raise ValueError(f"Tag '{tag}' is not valid SemVer format (expected vX.Y.Z)")
    return ".".join(match.groups())


def _validate_changelog_contains_version(changelog_text: str, version: str) -> None:
    version_heading = f"## [{version}]"
    if version_heading not in changelog_text:
        raise ValueError(
            f"Changelog is missing heading '{version_heading}'. "
            "Add a release section before pushing the tag."
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate tag/changelog coherence for release workflow"
    )
    parser.add_argument(
        "--tag", required=True, help="Git tag to validate (expected format: vX.Y.Z)"
    )
    parser.add_argument(
        "--changelog",
        default="CHANGELOG.md",
        help="Path to changelog file (default: CHANGELOG.md)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        version = _extract_release_version(args.tag)
        changelog_text = _read_text(Path(args.changelog))
        _validate_changelog_contains_version(changelog_text, version)
    except Exception as exc:
        print(f"Release semantics validation failed: {exc}", file=sys.stderr)
        return 1

    print(f"Release semantics validation passed for tag {args.tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
