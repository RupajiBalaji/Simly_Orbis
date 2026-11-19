"""
backend/tests/test_ask_orbis_chemistry.py
Continuous NLP parser test suite for Kinetics Bench and Buffer Bench corpora (P3-T7).
Enforces >=90% overall pass rate and >=85% hard pass rate without loosening thresholds.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from app.lab.agent import parse_request_rule_based
from app.lab.engine import create_session

DATA_DIR = Path(__file__).resolve().parent / "data"


def _evaluate_corpus(json_filename: str, experiment_id: str):
    filepath = DATA_DIR / json_filename
    assert filepath.exists(), f"Corpus file {json_filename} missing"

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    session = create_session(experiment_id, "NLPTestUser")

    normal_items = [d for d in data if not d.get("is_hard")]
    hard_items = [d for d in data if d.get("is_hard")]

    def run_items(items):
        passed = 0
        failures = []
        for it in items:
            steps, _ = parse_request_rule_based(it["text"], session)
            actions = [s.action.value for s in steps]
            if actions == it.get("expected_actions", []):
                passed += 1
            else:
                failures.append((it["id"], it["text"], actions, it.get("expected_actions")))
        return passed, len(items), failures

    norm_pass, norm_tot, _ = run_items(normal_items)
    hard_pass, hard_tot, hard_fails = run_items(hard_items)
    tot_pass, tot_tot, tot_fails = run_items(data)

    overall_rate = tot_pass / tot_tot
    hard_rate = hard_pass / hard_tot

    assert overall_rate >= 0.90, (
        f"{experiment_id} overall pass rate {overall_rate*100:.1f}% below 90% target ({tot_pass}/{tot_tot}). "
        f"Failures: {tot_fails}"
    )
    assert hard_rate >= 0.85, (
        f"{experiment_id} hard pass rate {hard_rate*100:.1f}% below 85% target ({hard_pass}/{hard_tot}). "
        f"Hard failures: {hard_fails}"
    )


def test_ask_orbis_kinetics_corpus():
    """Verify Kinetics Bench NLP phrases pass >=90% overall and >=85% hard."""
    _evaluate_corpus("ask_orbis_phrases_kinetics.json", "kinetics_bench")


def test_ask_orbis_buffer_corpus():
    """Verify Buffer Bench NLP phrases pass >=90% overall and >=85% hard."""
    _evaluate_corpus("ask_orbis_phrases_buffer.json", "buffer_bench")
