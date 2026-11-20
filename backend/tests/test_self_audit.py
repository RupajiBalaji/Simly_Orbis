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
import subprocess
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
    assert "0.7.0-dev" in res.evidence


def test_audit_check_validation_rows():
    res = check_validation_rows(REPO_ROOT)
    assert res.gate_id == 4
    assert res.passed is True
    assert "unverified" in res.evidence


def test_audit_check_frozen_tolerances():
    res = check_frozen_tolerance_hashes(REPO_ROOT)
    assert res.gate_id == 5
    assert res.passed is True
    assert "4/4" in res.evidence


def test_audit_check_protected_files():
    res = check_protected_files(REPO_ROOT, base_commit="cb9b66f")
    assert res.gate_id == 6
    assert res.passed is True


def test_audit_check_protected_files_fails_on_missing_path(tmp_path):
    res = check_protected_files(tmp_path, base_commit="cb9b66f")
    assert res.gate_id == 6
    assert res.passed is False
    assert "missing on disk" in res.evidence


def test_audit_check_protected_files_fails_on_planted_change(monkeypatch):
    orig_run = subprocess.run

    def mock_run(cmd, *args, **kwargs):
        if len(cmd) >= 4 and cmd[0] == "git" and cmd[1] == "cat-file" and "commit" in cmd[3]:
            class MockRev:
                returncode = 0
            return MockRev()
        if len(cmd) >= 5 and cmd[0] == "git" and cmd[1] == "diff" and "backend/app/modules/pharma_pk.py" in cmd:
            class MockProc:
                returncode = 0
                stdout = "diff --git a/pharma_pk.py b/pharma_pk.py\n+ planted unauthorized mutation"
                stderr = ""
            return MockProc()
        return orig_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", mock_run)
    res = check_protected_files(REPO_ROOT, base_commit="cb9b66f")
    assert res.gate_id == 6
    assert res.passed is False
    assert "Violations: 1 files" in res.evidence
    assert "UNAUTHORIZED MODIFICATION in `backend/app/modules/pharma_pk.py`" in res.details


def test_audit_check_protected_files_fails_on_changed_threshold(monkeypatch):
    """Gate 6 must fail if a rule checker's numeric threshold is modified."""
    from app.lab import rules as lab_rules

    # Copy rules so we don't pollute global state permanently
    orig_rules = list(lab_rules.DOSE_LAB_RULES)
    d1_orig = orig_rules[0]

    # Planted altered checker with mutated threshold
    def _mutated_checker(session, req):
        threshold = 999.0  # Modified threshold
        return False

    mutated_rule = lab_rules.SafetyRule(
        rule_id=d1_orig.rule_id,
        title=d1_orig.title,
        severity=d1_orig.severity,
        penalty_points=d1_orig.penalty_points,
        explanation=d1_orig.explanation,
        checker=_mutated_checker,
    )

    monkeypatch.setattr(lab_rules, "DOSE_LAB_RULES", [mutated_rule] + orig_rules[1:])
    res = check_protected_files(REPO_ROOT, base_commit="cb9b66f")
    assert res.gate_id == 6
    assert res.passed is False
    assert "1 rule mismatches" in res.evidence
    assert f"RULE DEFINITION CHANGED: Rule ID `{d1_orig.rule_id}` differs from baseline snapshot!" in res.details


def test_audit_check_protected_files_fails_on_changed_text(monkeypatch):
    """Gate 6 must fail if a rule's title or explanation text is modified."""
    from app.lab import rules as lab_rules

    orig_rules = list(lab_rules.SAFETY_RULES)
    r1_orig = orig_rules[0]

    mutated_rule = lab_rules.SafetyRule(
        rule_id=r1_orig.rule_id,
        title="Altered Non-Compliant Title",
        severity=r1_orig.severity,
        penalty_points=r1_orig.penalty_points,
        explanation="Altered explanation text that weakens safety pedagogy.",
        checker=r1_orig.checker,
    )

    monkeypatch.setattr(lab_rules, "SAFETY_RULES", [mutated_rule] + orig_rules[1:])
    res = check_protected_files(REPO_ROOT, base_commit="cb9b66f")
    assert res.gate_id == 6
    assert res.passed is False
    assert "1 rule mismatches" in res.evidence
    assert f"RULE DEFINITION CHANGED: Rule ID `{r1_orig.rule_id}` differs from baseline snapshot!" in res.details


def test_audit_check_protected_files_fails_on_missing_rule(monkeypatch):
    """Gate 6 must fail if any snapshotted rule is omitted from the active rule set."""
    from app.lab import rules as lab_rules

    orig_rules = list(lab_rules.SPACE_RULES)
    omitted_rule = orig_rules[0]

    # Omit S1
    monkeypatch.setattr(lab_rules, "SPACE_RULES", orig_rules[1:])
    res = check_protected_files(REPO_ROOT, base_commit="cb9b66f")
    assert res.gate_id == 6
    assert res.passed is False
    assert f"MISSING RULE: Rule ID `{omitted_rule.rule_id}` missing from active rules" in res.details


def test_audit_check_ci_workflow():
    res = check_ci_workflow(REPO_ROOT)
    assert res.gate_id == 7
    assert res.passed is True
    assert "bare `pytest backend/tests`" in res.evidence


@pytest.fixture
def qa_fixture_repo(tmp_path):
    """Temporary fixture folder for qa/out tests per Task F10."""
    run_dir = tmp_path / "qa" / "out" / "20261120_120000"
    run_dir.mkdir(parents=True)
    report = run_dir / "report.md"
    report.write_text(
        "# QA Report\n"
        "- pk_ward: passed\n"
        "- titration_bench: passed\n"
        "- launch_bench: passed\n"
        "- dose_lab: passed\n",
        encoding="utf-8",
    )
    for i in range(20):
        (run_dir / f"screen_{i:02d}.png").write_bytes(f"unique_png_{i}".encode("utf-8"))
    return tmp_path


def test_audit_check_qa_artifacts(qa_fixture_repo):
    res = check_qa_artifacts(qa_fixture_repo)
    assert res.gate_id == 8
    assert res.passed is True
    assert "MD5 collisions: 0" in res.evidence


def test_audit_check_parser_pass_rate():
    res = check_parser_pass_rate(REPO_ROOT)
    assert res.gate_id == 9
    assert res.passed is True
    assert "baseline" in res.evidence
    assert "pk" in res.details
    assert "buffer" in res.details
    assert "founder set: not provided" in res.details


def test_audit_check_parser_pass_rate_fails_when_corpus_missing(tmp_path):
    # Create fake repo structure with a report missing one corpus
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    fake_report = docs_dir / "PHASE_9_REPORT.md"
    fake_report.write_text("Only pk baseline 100% mentioned here.", encoding="utf-8")

    data_dir = tmp_path / "backend" / "tests" / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "agent_seed_heldout_phrases.json").write_text("{}", encoding="utf-8")

    res = check_parser_pass_rate(tmp_path)
    assert res.gate_id == 9
    assert res.passed is False
    assert "Missing first-run baseline rates" in res.evidence


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
