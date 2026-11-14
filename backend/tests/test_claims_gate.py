"""
backend/tests/test_claims_gate.py
Tests for the Claims Grep Gate (Section 14.6 & Section 18 P0-T7).

Verifies:
1. The claims gate passes on the clean repository (zero unhedged claims).
2. The claims gate fails when presented with planted unhedged phrases:
   - "clinically proven"
   - unhedged "validated"
   - unhedged "replaces animal testing"
   - "fda-approved"
"""

from __future__ import annotations

from pathlib import Path
import tempfile
import pytest

from scripts.check_claims import check_claims

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_claims_gate_passes_on_repository():
    """Verify repository markdown and documentation contain zero unhedged claim violations."""
    passed, violations = check_claims(REPO_ROOT)
    assert passed is True, f"Claims gate failed with violations:\n" + "\n".join(violations)
    assert len(violations) == 0


def test_claims_gate_fails_on_planted_unhedged_phrases():
    """Verify claims gate catches planted bad phrases without hedging context."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bad_file = Path(tmpdir) / "bad_claims.md"

        # Plant unhedged violations
        bad_content = """# New Product Overview
This software is clinically proven to optimize dosing in patients.
Our platform contains validated models ready for hospital use.
The software completely replaces animal testing for preclinical labs.
This device is FDA-approved for diagnostic analysis.
"""
        bad_file.write_text(bad_content, encoding="utf-8")

        passed, violations = check_claims(REPO_ROOT, target_paths=[bad_file])
        assert passed is False, "Claims gate should have failed on planted bad phrases!"
        assert len(violations) >= 4, f"Expected at least 4 violations, found {len(violations)}"

        # Verify specific violation types were identified
        violation_text = "\n".join(violations)
        assert "clinically proven" in violation_text
        assert "validated" in violation_text
        assert "replaces animal" in violation_text
        assert "FDA-approved" in violation_text


def test_claims_gate_allows_hedged_disclaimers():
    """Verify claims gate correctly permits disclaimed and negated mentions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        good_file = Path(tmpdir) / "good_claims.md"

        hedged_content = """# Compliance & Disclaimers
Educational simulation only. Not clinically validated for real patients.
The software is not FDA-approved and does not provide medical advice.
It does not replace animal testing; it helps reduce and refine experiments.
"""
        good_file.write_text(hedged_content, encoding="utf-8")

        passed, violations = check_claims(REPO_ROOT, target_paths=[good_file])
        assert passed is True, f"Hedged claims should pass! Violations found: {violations}"
        assert len(violations) == 0
