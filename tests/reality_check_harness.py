"""Compatibility entrypoint: run real offline accounting regression tests."""

import subprocess
import sys
from pathlib import Path


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    raise SystemExit(subprocess.call(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests",
         "-p", "test_global_settlement_gate.py", "-v"], cwd=root
    ))
