"""
Pytest wrapper for frontend/tests/movement_math.test.mjs.
Runs node's built-in test runner (node --test) to verify camera-relative
locomotion mathematics and critically damped easing.
Skips cleanly if node is not installed.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_movement_math_node_unit_tests():
    """Verify camera-relative movement vectors across 0, 90, 180, 270 deg and damping."""
    node_bin = shutil.which("node")
    if not node_bin:
        pytest.skip("Node.js is not installed on this system.")

    test_file = REPO_ROOT / "frontend" / "tests" / "movement_math.test.mjs"
    assert test_file.exists(), f"Test file not found at {test_file}"

    proc = subprocess.run(
        [node_bin, "--test", str(test_file)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert proc.returncode == 0, f"Node test runner failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "pass 6" in proc.stdout or "fail 0" in proc.stdout
