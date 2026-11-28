"""Tests for P7-T4: scripts/eval_ai.py writes docs/AI_EVAL_LATEST.md with all 4 suites."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import eval_ai  # noqa: E402


def test_eval_ai_generates_report_with_all_four_suites(tmp_path):
    out = tmp_path / "AI_EVAL_LATEST.md"
    md = eval_ai.run_evaluation(output_path=out)
    assert out.exists()
    assert "Author suite" in md
    assert "Hard suite" in md
    assert "Red-team suite" in md
    assert "Held-out suite (founder-written, not tuned)" in md
    if not eval_ai.HELDOUT_PATH.exists():
        assert "NOT RUN, file missing" in md
