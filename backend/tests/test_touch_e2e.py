"""Unit and integration test verifying touch e2e at 390x844 (Task F2)."""

import pytest
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.mark.browser
def test_touch_e2e_script_passes():
    """Verify qa/test_touch_e2e.py runs to completion and exits with code 0."""
    pytest.importorskip("playwright")
    script_path = REPO_ROOT / "qa" / "test_touch_e2e.py"
    assert script_path.exists(), "qa/test_touch_e2e.py missing"

    proc = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"test_touch_e2e.py failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "PASS: All 5 touch screenshots verified distinct and valid." in proc.stdout
