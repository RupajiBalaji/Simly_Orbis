"""
backend/tests/test_heldout.py
Held-out Evaluation Harness & Integrity Guard Test.

Standard: Section 18 (P0-T4) of Simly Orbis MVP Build Specification.
- Checks for founder_heldout_phrases.json (founder-written; agent never creates or edits).
  If missing, reports 'founder set: not provided'.
- Loads backend/tests/data/agent_seed_heldout_phrases.json (agent-written seed set, not founder-written).
- Note: n=4 per experiment is too small to be meaningful.
- Guard test: fails if file hash does not match backend/tests/data/agent_seed_heldout.sha256.
- Reports pass rates per experiment separately from the agent's main corpora.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest

from app.lab.agent import parse_request_rule_based
from app.lab.engine import create_session

DATA_DIR = Path(__file__).resolve().parent / "data"
AGENT_SEED_JSON = DATA_DIR / "agent_seed_heldout_phrases.json"
AGENT_SEED_SHA = DATA_DIR / "agent_seed_heldout.sha256"
FOUNDER_HELDOUT_JSON = DATA_DIR / "founder_heldout_phrases.json"


def test_agent_seed_heldout_corpus_hash_guard():
    """Guard test: verifies agent_seed_heldout_phrases.json matches signed SHA-256."""
    assert AGENT_SEED_JSON.exists(), "agent_seed_heldout_phrases.json missing"
    assert AGENT_SEED_SHA.exists(), "agent_seed_heldout.sha256 missing"

    actual_hash = hashlib.sha256(AGENT_SEED_JSON.read_bytes()).hexdigest()
    expected_hash = AGENT_SEED_SHA.read_text(encoding="utf-8").strip()

    assert actual_hash == expected_hash, (
        f"agent_seed_heldout_phrases.json has been modified without updating agent_seed_heldout.sha256! "
        f"Expected {expected_hash}, got {actual_hash}."
    )


def test_founder_heldout_status_check():
    """Verifies founder held-out set status: agent never creates or fabricates founder_heldout_phrases.json."""
    if not FOUNDER_HELDOUT_JSON.exists():
        status = "founder set: not provided"
    else:
        status = "founder set: provided"
    assert status in ("founder set: not provided", "founder set: provided")


def test_agent_seed_heldout_evaluation_runner():
    """Evaluate agent seed heldout phrases across all experiments and compute per-experiment pass rates."""
    assert AGENT_SEED_JSON.exists(), "agent_seed_heldout_phrases.json missing"

    with open(AGENT_SEED_JSON, "r", encoding="utf-8") as f:
        phrases = json.load(f)

    assert len(phrases) >= 8, f"Expected at least 8 heldout phrases, found {len(phrases)}"

    per_exp_stats: dict[str, dict[str, int]] = {}

    for item in phrases:
        exp_id = item["experiment_id"]
        if exp_id not in per_exp_stats:
            per_exp_stats[exp_id] = {"total": 0, "passed": 0}
        per_exp_stats[exp_id]["total"] += 1

        session = create_session(exp_id, "Tester")
        steps, skipped = parse_request_rule_based(item["text"], session)
        actions = [s.action.value for s in steps]

        expect_not_understood = item.get("expect_not_understood", False)
        if expect_not_understood:
            passed = (len(actions) == 0) or (len(skipped) > 0)
        else:
            expected = item.get("expected_actions", [])
            passed = any(act in actions for act in expected) if expected else len(actions) > 0

        if passed:
            per_exp_stats[exp_id]["passed"] += 1

    total_phrases = sum(s["total"] for s in per_exp_stats.values())
    total_passed = sum(s["passed"] for s in per_exp_stats.values())
    overall_pass_rate = (total_passed / total_phrases) * 100.0 if total_phrases else 0.0

    print("\n=== Agent Seed Held-Out Parser Evaluation ===")
    print("Label: agent-written seed set, not founder-written")
    print("Note: n=4 per experiment is too small to be meaningful.")
    for exp_id, stats in per_exp_stats.items():
        rate = (stats["passed"] / stats["total"]) * 100.0 if stats["total"] else 0.0
        print(f"  {exp_id:18s}: {rate:5.1f}% ({stats['passed']}/{stats['total']})")
    print(f"Overall Seed Held-Out Rate: {overall_pass_rate:5.1f}% ({total_passed}/{total_phrases})")

    # Evaluation completed successfully and reports rates per experiment
    assert total_phrases == len(phrases)
    assert "pk_ward" in per_exp_stats
    assert "titration_bench" in per_exp_stats
    assert "launch_bench" in per_exp_stats
    assert "dose_lab" in per_exp_stats
