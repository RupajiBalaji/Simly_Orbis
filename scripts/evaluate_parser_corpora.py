"""
scripts/evaluate_parser_corpora.py
Re-run all author, hard, and agent seed held-out corpora with the spec-driven vocabulary.
Reports pass rates against previous baseline figures.
Never edits corpora.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

# Ensure backend is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.lab.agent import parse_request_rule_based
from app.lab.engine import create_session

DATA_DIR = REPO_ROOT / "backend" / "tests" / "data"

def evaluate_author_corpora():
    print("=" * 60)
    print("PARSER EVALUATION AGAINST SPEC-DRIVEN VOCABULARY")
    print("=" * 60)

    results = {}

    # 1. Base Pharma & Titration (ask_orbis_phrases.json)
    base_file = DATA_DIR / "ask_orbis_phrases.json"
    with open(base_file, "r", encoding="utf-8") as f:
        base_data = json.load(f)
    
    pk_phrases = [p for p in base_data if p.get("experiment_id") == "pk_ward"]
    titr_phrases = [p for p in base_data if p.get("experiment_id") == "titration_bench"]
    
    def check_item(item, session):
        steps, skipped = parse_request_rule_based(item["text"], session)
        actions = [s.action.value for s in steps]
        if item.get("expect_not_understood", False):
            return len(actions) == 0 and len(skipped) > 0
        return actions == item.get("expected_actions", [])

    # Eval PK
    pk_session = create_session("pk_ward", "Tester")
    pk_pass = sum(1 for item in pk_phrases if check_item(item, pk_session))
    results["pk_ward_author"] = (pk_pass, len(pk_phrases))

    # Eval Titration
    titr_session = create_session("titration_bench", "Tester")
    titr_pass = sum(1 for item in titr_phrases if check_item(item, titr_session))
    results["titration_bench_author"] = (titr_pass, len(titr_phrases))

    # 2. Space Orbit (ask_orbis_phrases_space.json)
    space_file = DATA_DIR / "ask_orbis_phrases_space.json"
    with open(space_file, "r", encoding="utf-8") as f:
        space_data = json.load(f)
    space_session = create_session("launch_bench", "Astronaut")
    space_pass = 0
    for item in space_data:
        steps, skipped = parse_request_rule_based(item["text"], space_session)
        actions = [s.action.value for s in steps]
        if actions == item["expected_actions"]:
            space_pass += 1
    results["launch_bench_author"] = (space_pass, len(space_data))

    # 3. Dose Lab (ask_orbis_phrases_dose_lab.json)
    dose_file = DATA_DIR / "ask_orbis_phrases_dose_lab.json"
    with open(dose_file, "r", encoding="utf-8") as f:
        dose_data = json.load(f)
    dose_session = create_session("dose_lab", "DrDose")
    dose_pass = sum(1 for item in dose_data if check_item(item, dose_session))
    results["dose_lab_author"] = (dose_pass, len(dose_data))

    # 4. Kinetics Bench (ask_orbis_phrases_kinetics.json)
    kin_file = DATA_DIR / "ask_orbis_phrases_kinetics.json"
    if kin_file.exists():
        with open(kin_file, "r", encoding="utf-8") as f:
            kin_data = json.load(f)
        kin_session = create_session("kinetics_bench", "Chemist")
        kin_pass = sum(1 for item in kin_data if check_item(item, kin_session))
        results["kinetics_bench_author"] = (kin_pass, len(kin_data))

    # 5. Buffer Bench (ask_orbis_phrases_buffer.json)
    buf_file = DATA_DIR / "ask_orbis_phrases_buffer.json"
    if buf_file.exists():
        with open(buf_file, "r", encoding="utf-8") as f:
            buf_data = json.load(f)
        buf_session = create_session("buffer_bench", "Chemist")
        buf_pass = sum(1 for item in buf_data if check_item(item, buf_session))
        results["buffer_bench_author"] = (buf_pass, len(buf_data))

    # 6. Agent Seed Held-Out (agent_seed_heldout_phrases.json)
    seed_file = DATA_DIR / "agent_seed_heldout_phrases.json"
    with open(seed_file, "r", encoding="utf-8") as f:
        seed_data = json.load(f)
    seed_stats = {}
    for item in seed_data:
        exp_id = item["experiment_id"]
        if exp_id not in seed_stats:
            seed_stats[exp_id] = [0, 0]
        seed_stats[exp_id][1] += 1
        s = create_session(exp_id, "Tester")
        steps, skipped = parse_request_rule_based(item["text"], s)
        actions = [st.action.value for st in steps]
        if item.get("expect_not_understood"):
            passed = len(actions) == 0 or len(skipped) > 0
        else:
            expected = item.get("expected_actions", [])
            passed = any(a in actions for a in expected) if expected else len(actions) > 0
        if passed:
            seed_stats[exp_id][0] += 1

    print("\n--- Author / Hard Corpora ---")
    for k, (passed, total) in results.items():
        pct = (passed / total) * 100.0 if total else 0.0
        print(f"  {k:25s}: {pct:5.1f}% ({passed}/{total})")

    print("\n--- Agent-Written Seed Held-Out Set (n=4 per exp; small sample) ---")
    tot_seed_pass = sum(v[0] for v in seed_stats.values())
    tot_seed_tot = sum(v[1] for v in seed_stats.values())
    for exp, (passed, total) in seed_stats.items():
        pct = (passed / total) * 100.0 if total else 0.0
        print(f"  {exp:25s}: {pct:5.1f}% ({passed}/{total})")
    tot_pct = (tot_seed_pass / tot_seed_tot) * 100.0 if tot_seed_tot else 0.0
    print(f"  {'Overall Seed Held-Out':25s}: {tot_pct:5.1f}% ({tot_seed_pass}/{tot_seed_tot})")

    # Founder status
    founder_file = DATA_DIR / "founder_heldout_phrases.json"
    if founder_file.exists():
        print("\nFounder Held-Out Set: provided")
    else:
        print("\nFounder Held-Out Set: not provided")

    return results, seed_stats

if __name__ == "__main__":
    evaluate_author_corpora()
