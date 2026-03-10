#!/usr/bin/env python3
"""List changed Python files between two git revisions for CI quality gates."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ZERO_SHA = "0" * 40
EXCLUDED_PREFIXES = (
    "project-prompts/",
    "venv/",
    ".venv/",
)


def _resolve_head(head: str) -> str:
    return "HEAD" if head == "HEAD" else head


def _is_excluded(path: str) -> bool:
    return path.startswith(EXCLUDED_PREFIXES)


def _load_excluded_paths(path: str | None) -> set[str]:
    if not path:
        return set()
    excluded = set()
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        normalized = line.strip()
        if not normalized or normalized.startswith("#"):
            continue
        excluded.add(normalized)
    return excluded


def changed_python_files(
    base: str, head: str, excluded_paths: set[str] | None = None
) -> list[str]:
    if not base or base == ZERO_SHA:
        return []
    exclusions = excluded_paths or set()

    command = [
        "git",
        "diff",
        "--name-only",
        "--diff-filter=ACMR",
        "-z",
        base,
        _resolve_head(head),
        "--",
        "*.py",
    ]
    result = subprocess.run(
        command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    if not result.stdout:
        return []

    files = [
        entry
        for entry in result.stdout.decode("utf-8", errors="surrogateescape").split(
            "\x00"
        )
        if entry
    ]
    filtered = sorted(
        {path for path in files if not _is_excluded(path) and path not in exclusions}
    )

    # Guard against stale git index entries that no longer exist in workspace.
    return [path for path in filtered if Path(path).exists()]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List changed Python files between two revisions."
    )
    parser.add_argument("--base", required=True, help="Base revision SHA.")
    parser.add_argument(
        "--head", default="HEAD", help="Head revision SHA (default: HEAD)."
    )
    parser.add_argument(
        "--print0", action="store_true", help="Print NUL-separated output."
    )
    parser.add_argument(
        "--count", action="store_true", help="Print only count of files."
    )
    parser.add_argument(
        "--exclude-file",
        help="Optional newline-delimited file of paths to skip (debt allowlist).",
    )
    args = parser.parse_args()
    excluded_paths = _load_excluded_paths(args.exclude_file)

    try:
        files = changed_python_files(
            args.base, args.head, excluded_paths=excluded_paths
        )
    except subprocess.CalledProcessError as error:
        sys.stderr.write(error.stderr.decode("utf-8", errors="ignore"))
        return error.returncode or 1

    if args.count:
        sys.stdout.write(f"{len(files)}\n")
        return 0

    separator = "\x00" if args.print0 else "\n"
    if files:
        sys.stdout.write(separator.join(files))
        if not args.print0:
            sys.stdout.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
