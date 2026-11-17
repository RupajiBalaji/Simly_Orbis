#!/usr/bin/env python3
"""
scripts/eval_heldout.py
Evaluation Script for Ask Orbis Held-Out Sets.

Standard: Section 18 (P0-T4) of Simly Orbis MVP Build Specification.
- Checks for founder_heldout_phrases.json: reports 'founder set: not provided' if absent.
  (Agent must NEVER create or edit the founder file).
- Evaluates agent_seed_heldout_phrases.json: labelled 'agent-written seed set, not founder-written'.
  Notes that n=4 per experiment is too small to be meaningful.
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
FOUNDER_HELDOUT_JSON = DATA_DIR / "founder_heldout_phrases.json"
AGENT_SEED_JSON = DATA_DIR / "agent_seed_heldout_phrases.json"
AGENT_SEED_SHA = DATA_DIR / "agent_seed_heldout.sha256"


def _eval_phrases_list(phrases: list[dict]) -> tuple[dict[str, dict[str, int]], int, int]:
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

    total_p = sum(s["passed"] for s in stats.values())
    total_n = sum(s["total"] for s in stats.values())
    return stats, total_p, total_n


def evaluate_heldout() -> int:
    print("=" * 60)
    print("=== Ask Orbis Held-Out Evaluation Report ===")
    print("=" * 60 + "\n")

    # 1. Founder-written held-out set check
    print("--- 1. Founder Held-Out Evaluation ---")
    if not FOUNDER_HELDOUT_JSON.exists():
        print("founder set: not provided\n")
    else:
        try:
            with open(FOUNDER_HELDOUT_JSON, "r", encoding="utf-8") as f:
                f_phrases = json.load(f)
            stats, total_p, total_n = _eval_phrases_list(f_phrases)
            overall_rate = (total_p / total_n) * 100.0 if total_n else 0.0
            print("Label: founder-written, not tuned\n")
            print(f"File: {FOUNDER_HELDOUT_JSON.name}")
            print("-" * 55)
            print(f"{'Experiment':<22} | {'Passed':<8} | {'Total':<6} | {'Pass Rate':<8}")
            print("-" * 55)
            for exp_id in sorted(stats.keys()):
                s = stats[exp_id]
                rate = (s["passed"] / s["total"]) * 100.0 if s["total"] else 0.0
                print(f"{exp_id:<22} | {s['passed']:<8} | {s['total']:<6} | {rate:6.1f}%")
            print("-" * 55)
            print(f"{'OVERALL':<22} | {total_p:<8} | {total_n:<6} | {overall_rate:6.1f}%\n")
        except Exception as e:
            print(f"Error reading founder held-out set: {e}\n")

    # 2. Agent seed held-out set
    print("--- 2. Agent Seed Held-Out Evaluation ---")
    if not AGENT_SEED_JSON.exists():
        print(f"Error: {AGENT_SEED_JSON} not found.")
        return 1
    if not AGENT_SEED_SHA.exists():
        print(f"Error: {AGENT_SEED_SHA} not found.")
        return 1

    actual_hash = hashlib.sha256(AGENT_SEED_JSON.read_bytes()).hexdigest()
    expected_hash = AGENT_SEED_SHA.read_text(encoding="utf-8").strip()

    if actual_hash != expected_hash:
        print(f"[FAIL] Hash guard failed: expected {expected_hash}, got {actual_hash}")
        return 1

    with open(AGENT_SEED_JSON, "r", encoding="utf-8") as f:
        seed_phrases = json.load(f)

    stats, total_p, total_n = _eval_phrases_list(seed_phrases)
    overall_rate = (total_p / total_n) * 100.0 if total_n else 0.0

    print("Label: agent-written seed set, not founder-written")
    print("Note: n=4 per experiment is too small to be meaningful.\n")
    print(f"File: {AGENT_SEED_JSON.name} (SHA-256: {actual_hash[:16]}...)")
    print("-" * 55)
    print(f"{'Experiment':<22} | {'Passed':<8} | {'Total':<6} | {'Pass Rate':<8}")
    print("-" * 55)

    for exp_id in sorted(stats.keys()):
        s = stats[exp_id]
        rate = (s["passed"] / s["total"]) * 100.0 if s["total"] else 0.0
        print(f"{exp_id:<22} | {s['passed']:<8} | {s['total']:<6} | {rate:6.1f}%")

    print("-" * 55)
    print(f"{'OVERALL':<22} | {total_p:<8} | {total_n:<6} | {overall_rate:6.1f}%\n")
    return 0


if __name__ == "__main__":
    sys.exit(evaluate_heldout())
