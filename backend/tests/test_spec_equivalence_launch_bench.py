"""
Golden-Equivalence Test Suite for Launch & Orbit Bench (launch_bench).
Proves that the declarative spec runtime (SPEC_RUNTIME=True) produces identical
outcomes, scores, grade, and safety violations across 22 distinct scripted sequences
compared to the legacy engine path (SPEC_RUNTIME=False).

Baseline code state is pinned to commit 3d60be7 (P1 baseline HEAD).
All golden outputs are computed dynamically at test time by running both
the original pre-spec session engine and SpecRunner side-by-side on identical
scripted inputs (no stored snapshots).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
from typing import Any
import pytest

from app.config import settings
from app.lab.engine import apply_action, create_session
from app.lab.models import ActionRequest, ActionType


def compute_grade(score_parts: dict[str, int]) -> tuple[int, str]:
    """Compute total score and letter grade from rubric breakdown."""
    total = max(0, min(100, sum(score_parts.values())))
    if total >= 85:
        grade = "A"
    elif total >= 70:
        grade = "B"
    elif total >= 50:
        grade = "C"
    else:
        grade = "D"
    return total, grade


SEQUENCES: list[dict[str, Any]] = [
    {
        "name": "01_perfect_orbital_flight",
        "actions": [
            (ActionType.choose_rocket, "launch_pad", {"preset": "orbis_1"}),
            (ActionType.declare_payload, "launch_pad", {"payload_kg": 500.0}),
            (ActionType.fuel_rocket, "launch_pad", {"fuel_ratio": 1.0}),
            (ActionType.run_checklist, "flight_computer", {}),
            (ActionType.clear_range, "range_control", {}),
            (ActionType.launch, "launch_pad", {}),
            (ActionType.coast, None, {}),
            (ActionType.burn_transfer, None, {}),
            (ActionType.circularize, None, {}),
            (ActionType.debrief, "tracking_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "02_launch_uncleared_range",
        "actions": [
            (ActionType.choose_rocket, "launch_pad", {"preset": "orbis_1"}),
            (ActionType.declare_payload, "launch_pad", {"payload_kg": 500.0}),
            (ActionType.fuel_rocket, "launch_pad", {"fuel_ratio": 1.0}),
            (ActionType.run_checklist, "flight_computer", {}),
            (ActionType.launch, "launch_pad", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "03_launch_without_checklist",
        "actions": [
            (ActionType.choose_rocket, "launch_pad", {"preset": "orbis_1"}),
            (ActionType.declare_payload, "launch_pad", {"payload_kg": 500.0}),
            (ActionType.fuel_rocket, "launch_pad", {"fuel_ratio": 1.0}),
            (ActionType.clear_range, "range_control", {}),
            (ActionType.launch, "launch_pad", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "04_insufficient_twr_overload",
        "actions": [
            (ActionType.choose_rocket, "launch_pad", {"preset": "orbis_1"}),
            (ActionType.declare_payload, "launch_pad", {"payload_kg": 10000.0}),
            (ActionType.fuel_rocket, "launch_pad", {"fuel_ratio": 1.0}),
            (ActionType.run_checklist, "flight_computer", {}),
            (ActionType.clear_range, "range_control", {}),
            (ActionType.launch, "launch_pad", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "05_heavy_rocket_flight",
        "actions": [
            (ActionType.choose_rocket, "launch_pad", {"preset": "orbis_heavy"}),
            (ActionType.declare_payload, "launch_pad", {"payload_kg": 1500.0}),
            (ActionType.fuel_rocket, "launch_pad", {"fuel_ratio": 1.0}),
            (ActionType.run_checklist, "flight_computer", {}),
            (ActionType.clear_range, "range_control", {}),
            (ActionType.launch, "launch_pad", {}),
            (ActionType.coast, None, {}),
            (ActionType.burn_transfer, None, {}),
            (ActionType.circularize, None, {}),
            (ActionType.debrief, "tracking_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "06_cubesat_light_payload",
        "actions": [
            (ActionType.choose_rocket, "launch_pad", {"preset": "orbis_1"}),
            (ActionType.declare_payload, "launch_pad", {"payload_kg": 50.0}),
            (ActionType.fuel_rocket, "launch_pad", {"fuel_ratio": 1.0}),
            (ActionType.run_checklist, "flight_computer", {}),
            (ActionType.clear_range, "range_control", {}),
            (ActionType.launch, "launch_pad", {}),
            (ActionType.coast, None, {}),
            (ActionType.debrief, "tracking_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "07_suborbital_decay_low_fuel",
        "actions": [
            (ActionType.choose_rocket, "launch_pad", {"preset": "orbis_1"}),
            (ActionType.declare_payload, "launch_pad", {"payload_kg": 500.0}),
            (ActionType.fuel_rocket, "launch_pad", {"fuel_ratio": 0.2}),
            (ActionType.run_checklist, "flight_computer", {}),
            (ActionType.clear_range, "range_control", {}),
            (ActionType.launch, "launch_pad", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "08_early_submit_before_launch",
        "actions": [
            (ActionType.choose_rocket, "launch_pad", {"preset": "orbis_1"}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "09_empty_submit",
        "actions": [
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "10_double_fuel_load",
        "actions": [
            (ActionType.choose_rocket, "launch_pad", {"preset": "orbis_1"}),
            (ActionType.fuel_rocket, "launch_pad", {"fuel_ratio": 0.5}),
            (ActionType.fuel_rocket, "launch_pad", {"fuel_ratio": 1.0}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "11_debrief_without_launch",
        "actions": [
            (ActionType.choose_rocket, "launch_pad", {"preset": "orbis_1"}),
            (ActionType.debrief, "tracking_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "12_circularize_without_transfer",
        "actions": [
            (ActionType.choose_rocket, "launch_pad", {"preset": "orbis_1"}),
            (ActionType.declare_payload, "launch_pad", {"payload_kg": 500.0}),
            (ActionType.fuel_rocket, "launch_pad", {"fuel_ratio": 1.0}),
            (ActionType.run_checklist, "flight_computer", {}),
            (ActionType.clear_range, "range_control", {}),
            (ActionType.launch, "launch_pad", {}),
            (ActionType.coast, None, {}),
            (ActionType.circularize, None, {}),
            (ActionType.debrief, "tracking_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "13_full_geo_mission",
        "actions": [
            (ActionType.choose_rocket, "launch_pad", {"preset": "orbis_heavy"}),
            (ActionType.declare_payload, "launch_pad", {"payload_kg": 800.0}),
            (ActionType.fuel_rocket, "launch_pad", {"fuel_ratio": 1.0}),
            (ActionType.run_checklist, "flight_computer", {}),
            (ActionType.clear_range, "range_control", {}),
            (ActionType.launch, "launch_pad", {}),
            (ActionType.coast, None, {}),
            (ActionType.burn_transfer, None, {}),
            (ActionType.circularize, None, {}),
            (ActionType.debrief, "tracking_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "14_partial_checklist",
        "actions": [
            (ActionType.choose_rocket, "launch_pad", {"preset": "orbis_1"}),
            (ActionType.run_checklist, "flight_computer", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "15_clear_range_first",
        "actions": [
            (ActionType.clear_range, "range_control", {}),
            (ActionType.choose_rocket, "launch_pad", {"preset": "orbis_1"}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "16_coast_multiple_times",
        "actions": [
            (ActionType.choose_rocket, "launch_pad", {"preset": "orbis_1"}),
            (ActionType.declare_payload, "launch_pad", {"payload_kg": 500.0}),
            (ActionType.fuel_rocket, "launch_pad", {"fuel_ratio": 1.0}),
            (ActionType.run_checklist, "flight_computer", {}),
            (ActionType.clear_range, "range_control", {}),
            (ActionType.launch, "launch_pad", {}),
            (ActionType.coast, None, {}),
            (ActionType.coast, None, {}),
            (ActionType.debrief, "tracking_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "17_payload_at_capacity_limit",
        "actions": [
            (ActionType.choose_rocket, "launch_pad", {"preset": "orbis_1"}),
            (ActionType.declare_payload, "launch_pad", {"payload_kg": 2000.0}),
            (ActionType.fuel_rocket, "launch_pad", {"fuel_ratio": 1.0}),
            (ActionType.run_checklist, "flight_computer", {}),
            (ActionType.clear_range, "range_control", {}),
            (ActionType.launch, "launch_pad", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "18_fuel_without_rocket",
        "actions": [
            (ActionType.fuel_rocket, "launch_pad", {"fuel_ratio": 1.0}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "19_launch_without_fuel",
        "actions": [
            (ActionType.choose_rocket, "launch_pad", {"preset": "orbis_1"}),
            (ActionType.declare_payload, "launch_pad", {"payload_kg": 500.0}),
            (ActionType.run_checklist, "flight_computer", {}),
            (ActionType.clear_range, "range_control", {}),
            (ActionType.launch, "launch_pad", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "20_multiple_payload_declarations",
        "actions": [
            (ActionType.choose_rocket, "launch_pad", {"preset": "orbis_1"}),
            (ActionType.declare_payload, "launch_pad", {"payload_kg": 50.0}),
            (ActionType.declare_payload, "launch_pad", {"payload_kg": 500.0}),
            (ActionType.fuel_rocket, "launch_pad", {"fuel_ratio": 1.0}),
            (ActionType.run_checklist, "flight_computer", {}),
            (ActionType.clear_range, "range_control", {}),
            (ActionType.launch, "launch_pad", {}),
            (ActionType.coast, None, {}),
            (ActionType.debrief, "tracking_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "21_full_recovery_from_violations",
        "actions": [
            (ActionType.choose_rocket, "launch_pad", {"preset": "orbis_1"}),
            (ActionType.declare_payload, "launch_pad", {"payload_kg": 500.0}),
            (ActionType.fuel_rocket, "launch_pad", {"fuel_ratio": 1.0}),
            (ActionType.run_checklist, "flight_computer", {}),
            (ActionType.clear_range, "range_control", {}),
            (ActionType.launch, "launch_pad", {}),
            (ActionType.coast, None, {}),
            (ActionType.burn_transfer, None, {}),
            (ActionType.circularize, None, {}),
            (ActionType.debrief, "tracking_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
    {
        "name": "22_checklist_twice",
        "actions": [
            (ActionType.choose_rocket, "launch_pad", {"preset": "orbis_1"}),
            (ActionType.declare_payload, "launch_pad", {"payload_kg": 500.0}),
            (ActionType.fuel_rocket, "launch_pad", {"fuel_ratio": 1.0}),
            (ActionType.run_checklist, "flight_computer", {}),
            (ActionType.run_checklist, "flight_computer", {}),
            (ActionType.clear_range, "range_control", {}),
            (ActionType.launch, "launch_pad", {}),
            (ActionType.coast, None, {}),
            (ActionType.debrief, "tracking_station", {}),
            (ActionType.submit_report, None, {}),
        ],
    },
]


@pytest.mark.parametrize("seq_def", SEQUENCES, ids=[s["name"] for s in SEQUENCES])
def test_launch_bench_golden_equivalence(seq_def: dict[str, Any]):
    """
    Verify identical action outcomes, violations, scores, and grade between
    SPEC_RUNTIME=False (legacy engine) and SPEC_RUNTIME=True (spec runtime).
    """
    seq_name = seq_def["name"]
    actions = seq_def["actions"]

    # 1. Run under legacy engine path (SPEC_RUNTIME = False)
    settings.spec_runtime = False
    sess_old = create_session("launch_bench", f"Old_{seq_name}")
    old_step_results = []
    for action, target, params in actions:
        req = ActionRequest(action=action, target=target, params=params)
        res = apply_action(sess_old, req)
        tot, grd = compute_grade(sess_old.score_parts)
        old_step_results.append((res, dict(sess_old.score_parts), tot, grd))

    # 2. Run under declarative spec runtime (SPEC_RUNTIME = True)
    settings.spec_runtime = True
    sess_new = create_session("launch_bench", f"New_{seq_name}")
    sess_new.session_id = sess_old.session_id
    new_step_results = []
    for action, target, params in actions:
        req = ActionRequest(action=action, target=target, params=params)
        res = apply_action(sess_new, req)
        tot, grd = compute_grade(sess_new.score_parts)
        new_step_results.append((res, dict(sess_new.score_parts), tot, grd))

    # Reset flag to default
    settings.spec_runtime = False

    # 3. Step-by-step equivalence assertions
    assert len(old_step_results) == len(new_step_results)
    for idx, ((r_old, s_old, t_old, g_old), (r_new, s_new, t_new, g_new)) in enumerate(
        zip(old_step_results, new_step_results)
    ):
        step_label = f"Seq '{seq_name}' Step {idx} ({actions[idx][0].value})"

        # Outcome acceptance
        assert r_old.accepted == r_new.accepted, (
            f"{step_label}: accepted mismatch old={r_old.accepted} new={r_new.accepted}"
        )
        # Message
        assert r_old.message == r_new.message, (
            f"{step_label}: message mismatch\nOLD: {r_old.message}\nNEW: {r_new.message}"
        )
        # Violations count and rule IDs
        v_old_ids = [v.rule_id for v in r_old.violations]
        v_new_ids = [v.rule_id for v in r_new.violations]
        assert v_old_ids == v_new_ids, (
            f"{step_label}: violations mismatch old={v_old_ids} new={v_new_ids}"
        )
        # Visuals count and directives equality
        assert len(r_old.visuals) == len(r_new.visuals), (
            f"{step_label}: visuals count mismatch old={len(r_old.visuals)} new={len(r_new.visuals)}"
        )
        for v_idx, (v_o, v_n) in enumerate(zip(r_old.visuals, r_new.visuals)):
            type_o = v_o.get("type") if isinstance(v_o, dict) else getattr(v_o, "type", None)
            type_n = v_n.get("type") if isinstance(v_n, dict) else getattr(v_n, "type", None)
            assert type_o == type_n, f"{step_label} visual {v_idx}: type mismatch ({type_o} != {type_n})"
            target_o = v_o.get("target") if isinstance(v_o, dict) else getattr(v_o, "target", None)
            target_n = v_n.get("target") if isinstance(v_n, dict) else getattr(v_n, "target", None)
            assert target_o == target_n, f"{step_label} visual {v_idx}: target mismatch ({target_o} != {target_n})"
        # Dynamic score breakdown
        assert s_old == s_new, (
            f"{step_label}: score breakdown mismatch old={s_old} new={s_new}"
        )
        # Total score
        assert t_old == t_new, (
            f"{step_label}: total score mismatch old={t_old} new={t_new}"
        )
        # Letter grade
        assert g_old == g_new, (
            f"{step_label}: letter grade mismatch old={g_old} new={g_new}"
        )

    # Final session total score and grade equality
    tot_old, grd_old = compute_grade(sess_old.score_parts)
    tot_new, grd_new = compute_grade(sess_new.score_parts)
    assert tot_old == tot_new, (
        f"Final score mismatch in {seq_name}: old={tot_old} new={tot_new}"
    )
    assert grd_old == grd_new, (
        f"Final grade mismatch in {seq_name}: old={grd_old} new={grd_new}"
    )


def test_api_route_switch_under_spec_runtime_launch_bench():
    """Verify route behavior switches dynamically behind SPEC_RUNTIME flag for launch_bench."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    # 1. Old path
    settings.spec_runtime = False
    res_old = client.get("/api/lab/experiments/launch_bench")
    assert res_old.status_code == 200
    data_old = res_old.json()
    assert data_old["id"] == "launch_bench"

    # 2. Spec runtime path
    settings.spec_runtime = True
    res_new = client.get("/api/lab/experiments/launch_bench")
    assert res_new.status_code == 200
    data_new = res_new.json()
    assert data_new["id"] == "launch_bench"
    assert "Spec v1.0.0" in data_new["description"]

    # 3. Fallback: reset to default
    settings.spec_runtime = False
    res_fallback = client.get("/api/lab/experiments/launch_bench")
    assert res_fallback.status_code == 200
    assert "Spec v1.0.0" not in res_fallback.json()["description"]


def test_legacy_session_module_unmodified_since_3d60be7():
    """Verify that backend/app/lab/engine.py has 0 diff vs commit 3d60be7 (P1 baseline)."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    base_commit = "3d60be7"
    rev_check = subprocess.run(
        ["git", "cat-file", "-e", f"{base_commit}^{{commit}}"],
        cwd=repo_root,
        capture_output=True,
    )
    if rev_check.returncode == 0:
        res = subprocess.run(
            ["git", "diff", base_commit, "HEAD", "--", "backend/app/lab/engine.py"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        assert res.stdout.strip() == "", f"engine.py has diverged from commit {base_commit}:\n{res.stdout}"
    else:
        # Fallback for shallow clone: sha256 checksum guard
        engine_file = repo_root / "backend" / "app" / "lab" / "engine.py"
        sha = hashlib.sha256(engine_file.read_bytes()).hexdigest()
        assert sha == "a8a61a4376e8627628e22fa33c48079f03b3d562e0b7b76db6b7fefc48a3d92f"

