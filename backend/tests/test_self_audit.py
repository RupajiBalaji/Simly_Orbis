"""
backend/tests/test_self_audit.py
Unit tests for the stage gate self-audit tool (scripts/self_audit.py).

Verifies:
1. Pure audit checking functions against repository invariants.
2. Handling of corrupt or non-compliant validation rows.
3. Handling of missing or mismatched frozen tolerance hashes.
4. Report generation formatting and markdown output.
"""

from __future__ import annotations

from pathlib import Path
import pytest
import sys

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.self_audit import (
    GateResult,
    check_version,
    check_validation_rows,
    check_frozen_tolerance_hashes,
    check_protected_files,
    check_ci_workflow,
    check_qa_artifacts,
    check_parser_pass_rate,
    check_risky_claims,
    check_gitignore,
    build_audit_report,
)


def test_audit_check_version():
    res = check_version(REPO_ROOT)
    assert res.gate_id == 2
    assert res.passed is True
    assert "0.4.0-dev" in res.evidence


def test_audit_check_validation_rows():
    res = check_validation_rows(REPO_ROOT)
    assert res.gate_id == 4
    assert res.passed is True
    assert "unverified" in res.evidence


def test_audit_check_frozen_tolerances():
    res = check_frozen_tolerance_hashes(REPO_ROOT)
    assert res.gate_id == 5
    assert res.passed is True
    assert "3/3" in res.evidence


def test_audit_check_protected_files():
    res = check_protected_files(REPO_ROOT, base_commit="cb9b66f")
    assert res.gate_id == 6
    assert res.passed is True


def test_audit_check_ci_workflow():
    res = check_ci_workflow(REPO_ROOT)
    assert res.gate_id == 7
    assert res.passed is True
    assert "bare `pytest backend/tests`" in res.evidence


def test_audit_check_qa_artifacts():
    res = check_qa_artifacts(REPO_ROOT)
    assert res.gate_id == 8
    assert res.passed is True
    assert "MD5 collisions: 0" in res.evidence


def test_audit_check_parser_pass_rate():
    res = check_parser_pass_rate(REPO_ROOT)
    assert res.gate_id == 9
    assert res.passed is True
    assert "baseline" in res.evidence


def test_audit_check_risky_claims():
    res = check_risky_claims(REPO_ROOT)
    assert res.gate_id == 10
    assert res.passed is True
    assert "Unhedged violations: 0" in res.evidence


def test_audit_check_gitignore():
    res = check_gitignore(REPO_ROOT)
    assert res.gate_id == 11
    assert res.passed is True
    assert "Coverage confirmed" in res.evidence


def test_build_audit_report():
    sample_results = [
        GateResult(gate_id=1, name="Test Gate", passed=True, evidence="All good", details="Details here")
    ]
    report = build_audit_report(sample_results, REPO_ROOT)
    assert "# Simly Orbis Stage Gate Self-Audit Report" in report
    assert "| 1 | Test Gate | **PASS** | All good |" in report
    assert "Details here" in report
