#!/usr/bin/env python3
"""
Simple wrapper for the vector database builder CLI.

This forwards all commands to the integrated CLI in `scripts/`.

Usage:
  python3 build_vectordb.py --help
  python3 build_vectordb.py build --max-plans 100
  python3 build_vectordb.py status
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    script_path = Path(__file__).parent / "scripts" / "build_vectordb_cli.py"
    cmd = [sys.executable, str(script_path)] + sys.argv[1:]
    return int(subprocess.call(cmd))


if __name__ == "__main__":
    raise SystemExit(main())

