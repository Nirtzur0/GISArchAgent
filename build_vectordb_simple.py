#!/usr/bin/env python3
"""
Simple wrapper script to run the vector database builder.

This avoids circular import issues by running the actual script in a subprocess.
"""

import subprocess
import sys

if __name__ == '__main__':
    # Just run the actual python script
    cmd = [sys.executable, 'scripts/build_vectordb_cli.py'] + sys.argv[1:]
    sys.exit(subprocess.call(cmd))
