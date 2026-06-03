#!/usr/bin/env python
"""
Run the full conversion matrix and write conversion-matrix.md.

Usage:
    python scripts/run_matrix.py                      # full sweep
    python scripts/run_matrix.py -k image             # only image pairs
    python scripts/run_matrix.py -k "audio or video"  # subset

Runs with the project's coverage gate and the default "-m not matrix" filter
disabled (the matrix is excluded from the normal suite), so it can be invoked
standalone.
"""

import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent


def main() -> int:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/matrix",
        "-o",
        "addopts=",  # drop coverage gate + "-m not matrix" from pytest.ini
        "-m",
        "matrix",
        "-p",
        "no:cacheprovider",
        "--tb=line",
        *sys.argv[1:],
    ]
    return subprocess.call(cmd, cwd=str(BACKEND))


if __name__ == "__main__":
    raise SystemExit(main())
