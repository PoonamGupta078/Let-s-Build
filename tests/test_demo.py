"""Regression test for the one-command demo script (scripts/run_demo.py)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO_SCRIPT = ROOT / "scripts" / "run_demo.py"


def test_demo_script_runs_and_reports_outcomes():
    """The demo must exit 0 and report meaningful SEE/TRACE/CUT outcomes.

    Assertions target stable, meaningful content (seed/exit accounts and the
    SEE rule that fires), not formatting or ordering.
    """
    proc = subprocess.run(
        [sys.executable, str(DEMO_SCRIPT)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    output = proc.stdout + proc.stderr
    assert proc.returncode == 0, f"demo exited {proc.returncode}:\n{output}"

    # Meaningful outcomes from the seeded two-mule cash-out case.
    assert "S" in output           # seed account
    assert "M1" in output          # first mule
    assert "M2" in output          # second mule
    assert "CASH" in output        # exit account
    assert "RPT001" in output      # SEE rapid pass-through rule fired
    assert "DISCLAIMER" in output  # advisory disclaimer printed
