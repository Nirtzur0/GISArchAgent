"""
Test-runner hardening.

Some developer machines have globally-installed pytest plugins that auto-load via
entry points. If those plugins are incompatible with this repo's Python stack,
pytest can crash before collecting any tests.

We disable plugin autoload ONLY when it looks like we're running pytest.
This keeps normal application runs unchanged, while making `pytest` reliable.
"""

from __future__ import annotations

import os
import sys


def _looks_like_pytest_invocation(argv: list[str]) -> bool:
    # Common entrypoints:
    # - `pytest ...` => argv[0] endswith "pytest"
    # - `python -m pytest ...` => argv includes "-m", "pytest"
    base0 = os.path.basename(argv[0] or "")
    if base0 in {"pytest", "py.test"}:
        return True
    if len(argv) >= 3 and argv[1] == "-m" and argv[2] == "pytest":
        return True
    return any("pytest" in (a or "") for a in argv[:3])


if _looks_like_pytest_invocation(sys.argv):
    os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

