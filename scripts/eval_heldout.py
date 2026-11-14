#!/usr/bin/env python3
"""
scripts/eval_heldout.py
Standalone Held-Out Evaluation Script for Ask Orbis.

Standard: Section 18 (P0-T4) of Simly Orbis MVP Build Specification.
Evaluates backend/tests/data/heldout_phrases.json and prints per-experiment pass rates.
Educational simulation platform. Not medical advice. Not clinical evidence.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

# Ensure backend is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.lab.agent import parse_request_rule_based
from app.lab.engine import create_session

DATA_DIR = REPO_ROOT / "backend" / "tests" / "data"
HELDOUT_JSON = DATA_DIR / "heldout_phrases.json"
HELDOUT_SHA = DATA_DIR / "heldout.sha256"


def evaluate_heldout() -> int:
    if not HELDOUT_JSON.exists():
        print(f"Error: {HELDOUT_JSON} not found.")
        return 1
    if not HELDOUT_SHA.exists():
        print(f"Error: {HELDOUT_SHA} not found.")
        return 1

    actual_hash = hashlib.sha256(HELDOUT_JSON.read_bytes()).hexdigest()
    expected_hash = HELDOUT_SHA.read_text(encoding="utf-8").strip()

    if actual_hash != expected_hash:
        print(f"[FAIL] Hash guard failed: expected {expected_hash}, got {actual_hash}")
        return 1

    with open(HELDOUT_JSON, "r", encoding="utf-8") as f:
        phrases = json.load(f)

    stats: dict[str, dict[str, int]] = {}

    for item in phrases:
        exp_id = item["experiment_id"]
        if exp_id not in stats:
            stats[exp_id] = {"total": 0, "passed": 0}
        stats[exp_id]["total"] += 1

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
            stats[exp_id]["passed"] += 1

    print("=== Ask Orbis Held-Out Evaluation Report ===")
    print("Label: founder-written, not tuned\n")
    print(f"File: {HELDOUT_JSON.name} (SHA-256: {actual_hash[:16]}...)")
    print("-" * 55)
    print(f"{'Experiment':<22} | {'Passed':<8} | {'Total':<6} | {'Pass Rate':<8}")
    print("-" * 55)

    total_p = 0
    total_n = 0
    for exp_id in sorted(stats.keys()):
        s = stats[exp_id]
        rate = (s["passed"] / s["total"]) * 100.0 if s["total"] else 0.0
        total_p += s["passed"]
        total_n += s["total"]
        print(f"{exp_id:<22} | {s['passed']:<8} | {s['total']:<6} | {rate:6.1f}%")

    overall_rate = (total_p / total_n) * 100.0 if total_n else 0.0
    print("-" * 55)
    print(f"{'OVERALL':<22} | {total_p:<8} | {total_n:<6} | {overall_rate:6.1f}%\n")
    return 0


if __name__ == "__main__":
    sys.exit(evaluate_heldout())
