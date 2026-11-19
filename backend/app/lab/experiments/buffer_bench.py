"""
backend/app/lab/experiments/buffer_bench.py
Buffer Solutions & Capacity Bench Experiment Implementation (chem.buffer).

Implements Section 9.2 & Section 18 (P3-T5) of Simly Orbis MVP Build Specification:
- Interactive buffer design workflow: target pH matching, pKa selection,
  solution preparation, initial pH & Van Slyke buffer capacity determination,
  strong acid (HCl) / strong base (NaOH) stress testing, pH response curve,
  and protocol safety compliance.
"""

from __future__ import annotations

import copy
import math
from typing import Any, Dict, List

from app.chem.buffer import (
    compute_buffer_state,
    henderson_hasselbalch_ph,
    max_buffer_capacity,
    simulate_buffer_stress,
)
from app.lab.experiments.base import ExperimentDefinition
from app.lab.models import (
    ActionRequest,
    ActionResult,
    ActionType,
    AvailableAction,
    CharacterAnimation,
    LabSession,
    Violation,
    VisualDirective,
)

BUFFER_SYSTEMS = {
    "acetate": {
        "name": "Acetic acid / Sodium acetate",
        "pka": 4.76,
        "optimal_range": [3.76, 5.76],
        "default_target_ph": 4.75,
    },
    "phosphate": {
        "name": "Dihydrogen phosphate / Monohydrogen phosphate",
        "pka": 7.20,
        "optimal_range": [6.20, 8.20],
        "default_target_ph": 7.40,
    },
    "formate": {
        "name": "Formic acid / Sodium formate",
        "pka": 3.75,
        "optimal_range": [2.75, 4.75],
        "default_target_ph": 3.80,
    },
    "tris": {
        "name": "Tris base / Tris-HCl",
        "pka": 8.06,
        "optimal_range": [7.06, 9.06],
        "default_target_ph": 8.10,
    },
}

BUFFER_BENCH_EXPERIMENT = ExperimentDefinition(
    id="buffer_bench",
    title="Buffer Solutions & Capacity Bench",
    district="chemistry",
    description=(
        "Design aqueous buffer systems for target pH values, evaluate Van Slyke buffer capacity, "
        "and stress-test buffer resistance against strong acid (HCl) and strong base (NaOH) additions."
    ),
    learning_goals=[
        "Maintain chemical laboratory PPE compliance (goggles, gloves, coat).",
        "Select conjugate acid-base systems whose pKa closely matches target pH.",
        "Prepare buffer solutions using Henderson-Hasselbalch and exact electroneutrality.",
        "Calibrate pH meter with two-point standard buffers before taking measurements.",
        "Determine experimental and theoretical Van Slyke buffer capacity (beta).",
        "Stress-test buffer stability against strong acid and strong base additions.",
        "Recognize buffer exhaustion when added strong titrant exceeds buffer capacity.",
        "Neutralize and safely dispose of chemical waste in designated containers.",
    ],
    required_ppe=["goggles", "gloves", "coat"],
    apparatus={
        "ph_meter": {
            "type": "ph_meter",
            "calibrated": False,
            "reading": None,
        },
        "buffer_beaker": {
            "type": "beaker",
            "volume_ml": 100.0,
            "system_id": "acetate",
            "target_ph": 4.75,
            "prepared": False,
            "acid_conc_m": 0.1,
            "salt_conc_m": 0.1,
            "pka": 4.76,
            "ph": None,
            "buffer_capacity_beta": None,
            "clean": True,
        },
        "magnetic_stirrer": {
            "type": "stirrer",
            "active": False,
            "rpm": 0,
        },
        "stress_burette": {
            "type": "burette",
            "titrant": "hcl",
            "titrant_conc_m": 1.0,
            "volume_dispensed_ml": 0.0,
            "stress_tested": False,
            "stress_curve": [],
        },
        "chemical_waste_bin": {
            "type": "waste_bin",
            "items": [],
        },
        "sink": {
            "type": "utility",
            "clean": True,
        },
    },
    inventory={
        "acetate_pair": {"name": "Acetic Acid / Sodium Acetate (pKa 4.76)", "pka": 4.76},
        "phosphate_pair": {"name": "Phosphate Buffer (pKa 7.20)", "pka": 7.20},
        "formate_pair": {"name": "Formic Acid / Sodium Formate (pKa 3.75)", "pka": 3.75},
        "tris_pair": {"name": "Tris / Tris-HCl (pKa 8.06)", "pka": 8.06},
        "hcl_solution": {"name": "1.0 M Hydrochloric Acid", "conc_m": 1.0},
        "naoh_solution": {"name": "1.0 M Sodium Hydroxide", "conc_m": 1.0},
    },
    protocol_steps=[
        "wear_ppe",
        "select_buffer_system",
        "prepare_buffer",
        "test_capacity",
        "stress_buffer",
        "submit_buffer_design",
        "dispose_waste",
        "wash_hands",
        "submit_report",
    ],
    rules=[
        {
            "rule_id": "B1",
            "title": "PPE Compliance for Corrosive & Buffer Safety",
            "explanation": "Always wear safety goggles, gloves, and a lab coat before handling buffer reagents, concentrated acids, or bases.",
        },
        {
            "rule_id": "B2",
            "title": "Inappropriate Buffer System Selection",
            "explanation": "The selected buffer pKa should be within +/- 1.2 pH unit of target pH for adequate buffering capacity.",
        },
        {
            "rule_id": "B3",
            "title": "Uncalibrated pH Meter Measurement",
            "explanation": "The pH meter must be calibrated with standard reference buffers before measuring buffer solutions.",
        },
        {
            "rule_id": "B4",
            "title": "Unmonitored Extreme Stress Addition",
            "explanation": "Stress titrant addition should be performed with gradual monitoring to capture the buffer breakdown inflection.",
        },
    ],
)


def get_buffer_available_actions(session: LabSession) -> List[AvailableAction]:
    """Return contextual available actions for the Buffer Bench."""
    actions: List[AvailableAction] = []
    ppe = session.ppe
    has_ppe = ("goggles" in ppe and "gloves" in ppe and "coat" in ppe)
    prog = set(session.protocol_progress)

    apparatus = session.apparatus_state
    ph_meter = apparatus.get("ph_meter", {})
    beaker = apparatus.get("buffer_beaker", {})
    burette = apparatus.get("stress_burette", {})

    # 1. PPE
    actions.append(
        AvailableAction(
            action=ActionType.wear_ppe,
            label="Put on Safety Gear (PPE)",
            targets=["avatar"],
            enabled=not has_ppe,
            disabled_reason="PPE already equipped." if has_ppe else None,
        )
    )

    # 2. Select Buffer System
    actions.append(
        AvailableAction(
            action=ActionType.select_buffer_system,
            label="Select Buffer Conjugate Pair",
            targets=["buffer_beaker"],
            enabled=has_ppe,
            disabled_reason="Put on safety PPE first." if not has_ppe else None,
        )
    )

    # 3. Prepare Buffer
    actions.append(
        AvailableAction(
            action=ActionType.prepare_buffer,
            label="Formulate & Prepare Buffer Solution",
            targets=["buffer_beaker"],
            enabled=has_ppe,
            disabled_reason="Put on safety PPE first." if not has_ppe else None,
        )
    )

    # 4. Test Capacity
    actions.append(
        AvailableAction(
            action=ActionType.test_capacity,
            label="Calibrate pH Meter & Test Buffer Capacity",
            targets=["ph_meter"],
            enabled=has_ppe and beaker.get("prepared", False),
            disabled_reason="Prepare a buffer solution before measuring capacity.",
        )
    )

    # 5. Stress Test Buffer
    actions.append(
        AvailableAction(
            action=ActionType.stress_buffer,
            label="Run Strong Acid / Base Stress Test",
            targets=["stress_burette"],
            enabled=has_ppe and beaker.get("prepared", False) and ph_meter.get("calibrated", False),
            disabled_reason="Calibrate pH meter and prepare buffer before running stress test.",
        )
    )

    # 6. Submit Buffer Design
    actions.append(
        AvailableAction(
            action=ActionType.submit_buffer_design,
            label="Submit Buffer Design Evaluation",
            targets=["avatar"],
            enabled=burette.get("stress_tested", False),
            disabled_reason="Complete acid/base stress test before submitting evaluation.",
        )
    )

    # 7. Dispose Waste
    actions.append(
        AvailableAction(
            action=ActionType.dispose_waste,
            label="Dispose Chemical Waste",
            targets=["chemical_waste_bin"],
            enabled=has_ppe and beaker.get("prepared", False),
            disabled_reason="Wear PPE before handling waste disposal.",
        )
    )

    # 8. Wash Hands
    actions.append(
        AvailableAction(
            action=ActionType.wash_hands,
            label="Wash Hands at Sink",
            targets=["sink"],
            enabled=True,
        )
    )

    # 9. Submit Report
    actions.append(
        AvailableAction(
            action=ActionType.submit_report,
            label="Submit Completed Buffer Report",
            targets=["avatar"],
            enabled="submit_buffer_design" in prog or burette.get("stress_tested", False),
            disabled_reason="Complete buffer evaluation before submitting final report.",
        )
    )

    return actions


def apply_buffer_action(session: LabSession, req: ActionRequest) -> ActionResult:
    """Execute action within Buffer Solutions & Capacity Bench."""
    action = req.action
    params = req.params or {}

    violations: List[Violation] = []
    visuals: List[Dict[str, Any]] = []
    events: List[Dict[str, Any]] = []
    message = ""
    status = session.status

    beaker = session.apparatus_state.setdefault(
        "buffer_beaker",
        {
            "type": "beaker",
            "volume_ml": 100.0,
            "system_id": "acetate",
            "target_ph": 4.75,
            "prepared": False,
            "acid_conc_m": 0.1,
            "salt_conc_m": 0.1,
            "pka": 4.76,
            "ph": None,
            "buffer_capacity_beta": None,
            "clean": True,
        },
    )
    ph_meter = session.apparatus_state.setdefault(
        "ph_meter",
        {"type": "ph_meter", "calibrated": False, "reading": None},
    )
    burette = session.apparatus_state.setdefault(
        "stress_burette",
        {
            "titrant": "hcl",
            "titrant_conc_m": 1.0,
            "volume_dispensed_ml": 0.0,
            "stress_tested": False,
            "stress_curve": [],
        },
    )
    waste_bin = session.apparatus_state.setdefault("chemical_waste_bin", {"items": []})
    sink = session.apparatus_state.setdefault("sink", {"clean": True})

    ppe = session.ppe
    has_ppe = ("goggles" in ppe and "gloves" in ppe and "coat" in ppe)

    # 1. Wear PPE
    if action == "wear_ppe":
        item = params.get("item", "all")
        if item == "all":
            session.ppe = {"goggles", "gloves", "coat"}
        else:
            session.ppe.add(item)
        message = f"Put on personal protective equipment: {', '.join(sorted(session.ppe))}."
        if "wear_ppe" not in session.protocol_progress:
            session.protocol_progress.append("wear_ppe")
            session.score_parts["safety"] = min(40, session.score_parts.get("safety", 40))
        visuals.append({"type": "particle", "target": "avatar", "name": "sparkle"})
        events.append({"type": "ppe_donned", "detail": "Equipped PPE"})

    # 2. Select Buffer System
    elif action == "select_buffer_system":
        if not has_ppe:
            v = Violation(
                rule_id="B1",
                title="PPE Violation",
                explanation="Handled buffer chemicals without protective equipment.",
                severity="warning",
                penalty_points=15,
            )
            violations.append(v)
            session.violations.append(v)
            session.score_parts["safety"] = max(0, session.score_parts.get("safety", 40) - 15)

        sys_id = params.get("system", "acetate")
        if sys_id not in BUFFER_SYSTEMS:
            return ActionResult(accepted=False, message=f"Unknown buffer system '{sys_id}'.")

        sys_info = BUFFER_SYSTEMS[sys_id]
        target_ph = float(params.get("target_ph", sys_info["default_target_ph"]))
        pka = sys_info["pka"]

        if abs(target_ph - pka) > 1.2:
            v = Violation(
                rule_id="B2",
                title="Suboptimal Buffer System Selection",
                explanation=f"Selected {sys_info['name']} (pKa {pka:.2f}) for target pH {target_ph:.2f}. Buffering capacity is highest within +/- 1.0 pH unit of pKa.",
                severity="warning",
                penalty_points=10,
            )
            violations.append(v)
            session.violations.append(v)
            session.score_parts["accuracy"] = max(0, session.score_parts.get("accuracy", 30) - 10)

        beaker["system_id"] = sys_id
        beaker["target_ph"] = target_ph
        beaker["pka"] = pka
        message = f"Selected buffer system: {sys_info['name']} (pKa {pka:.2f}) for target pH {target_ph:.2f}."
        if "select_buffer_system" not in session.protocol_progress:
            session.protocol_progress.append("select_buffer_system")
        events.append({"type": "system_selected", "system": sys_id, "target_ph": target_ph})

    # 3. Prepare Buffer
    elif action == "prepare_buffer":
        if not has_ppe:
            v = Violation(
                rule_id="B1",
                title="PPE Violation",
                explanation="Prepared buffer solutions without laboratory goggles, gloves, or coat.",
                severity="warning",
                penalty_points=15,
            )
            violations.append(v)
            session.violations.append(v)
            session.score_parts["safety"] = max(0, session.score_parts.get("safety", 40) - 15)

        target_ph = float(params.get("target_ph", beaker.get("target_ph", 4.75)))
        total_conc = float(params.get("total_conc_m", 0.2))
        vol_ml = float(params.get("volume_ml", 100.0))
        pka = float(beaker.get("pka", 4.76))

        ratio = 10.0 ** (target_ph - pka)
        ha_conc = total_conc / (1.0 + ratio)
        a_conc = total_conc - ha_conc

        ka = 10.0 ** (-pka)
        state = compute_buffer_state(
            total_acid_conc=ha_conc,
            total_salt_conc=a_conc,
            ka=ka,
        )

        beaker["prepared"] = True
        beaker["target_ph"] = target_ph
        beaker["volume_ml"] = vol_ml
        beaker["acid_conc_m"] = ha_conc
        beaker["salt_conc_m"] = a_conc
        beaker["ph"] = round(state.ph, 3)
        beaker["buffer_capacity_beta"] = round(state.buffer_capacity_beta, 4)
        beaker["clean"] = False

        message = (
            f"Prepared {vol_ml:.0f} mL buffer: [HA]={ha_conc:.3f} M, [A-]={a_conc:.3f} M. "
            f"Calculated equilibrium pH = {state.ph:.2f}, β = {state.buffer_capacity_beta:.4f} M/pH."
        )
        if "prepare_buffer" not in session.protocol_progress:
            session.protocol_progress.append("prepare_buffer")
        visuals.append({"type": "liquid", "target": "buffer_beaker", "name": "fill", "level": vol_ml / 150.0})
        events.append({"type": "buffer_prepared", "ph": state.ph, "beta": state.buffer_capacity_beta})

    # 4. Test Capacity / Calibrate Meter
    elif action == "test_capacity":
        if not beaker.get("prepared"):
            return ActionResult(accepted=False, message="Prepare buffer solution before testing capacity.")

        ph_meter["calibrated"] = True
        ph_val = beaker["ph"]
        beta = beaker["buffer_capacity_beta"]
        ph_meter["reading"] = ph_val

        message = f"pH meter calibrated. Measured baseline buffer pH = {ph_val:.2f}, Van Slyke buffer capacity β = {beta:.4f} M/pH."
        if "test_capacity" not in session.protocol_progress:
            session.protocol_progress.append("test_capacity")
        session.score_parts["technique"] = min(20, (10 if ph_meter.get("calibrated") else 0) + (10 if burette.get("stress_tested") and ph_meter.get("calibrated") else 0))
        visuals.append({"type": "readout", "target": "ph_meter", "value": ph_val, "unit": "pH"})
        events.append({"type": "capacity_tested", "ph": ph_val, "beta": beta})

    # 5. Stress Test Buffer
    elif action == "stress_buffer":
        if not has_ppe:
            v = Violation(
                rule_id="B1",
                title="PPE Violation",
                explanation="Performed strong acid/base additions without PPE.",
                severity="warning",
                penalty_points=15,
            )
            violations.append(v)
            session.violations.append(v)
            session.score_parts["safety"] = max(0, session.score_parts.get("safety", 40) - 15)

        if not beaker.get("prepared"):
            return ActionResult(accepted=False, message="Prepare a buffer before running stress test.")

        if not ph_meter.get("calibrated"):
            v = Violation(
                rule_id="B3",
                title="Uncalibrated pH Meter",
                explanation="Recorded stress test curve with an uncalibrated meter.",
                severity="warning",
                penalty_points=10,
            )
            violations.append(v)
            session.violations.append(v)
            session.score_parts["accuracy"] = max(0, session.score_parts.get("accuracy", 30) - 10)

        titrant = str(params.get("titrant", "hcl")).lower()
        titrant_conc = float(params.get("titrant_conc_m", 1.0))
        max_ml = float(params.get("max_added_ml", 15.0))
        num_steps = int(params.get("num_steps", 25))

        if max_ml > 30.0 or num_steps < 5:
            v = Violation(
                rule_id="B4",
                title="Unmonitored Extreme Stress Addition",
                explanation="Stress titrant addition should be performed with gradual monitoring to capture the buffer breakdown inflection.",
                severity="warning",
                penalty_points=10,
            )
            violations.append(v)
            session.violations.append(v)

        ka = 10.0 ** (-beaker["pka"])
        curve_pts = simulate_buffer_stress(
            initial_volume_ml=beaker["volume_ml"],
            acid_conc=beaker["acid_conc_m"],
            salt_conc=beaker["salt_conc_m"],
            ka=ka,
            titrant_type=titrant,
            titrant_conc_m=titrant_conc,
            max_added_ml=max_ml,
            num_steps=num_steps,
        )

        final_pt = curve_pts[-1]
        delta_ph = abs(final_pt.ph - beaker["ph"])

        serialized_curve = [
            {
                "added_ml": round(p.added_volume_ml, 2),
                "total_volume_ml": round(p.total_volume_ml, 2),
                "ph": round(p.ph, 3),
                "beta": round(p.buffer_capacity_beta, 4),
            }
            for p in curve_pts
        ]

        burette["titrant"] = titrant
        burette["titrant_conc_m"] = titrant_conc
        burette["volume_dispensed_ml"] = max_ml
        burette["stress_tested"] = True
        burette["stress_curve"] = serialized_curve
        ph_meter["reading"] = round(final_pt.ph, 3)

        message = (
            f"Completed {titrant.upper()} stress test ({max_ml:.1f} mL added). "
            f"pH shifted from {beaker['ph']:.2f} to {final_pt.ph:.2f} (ΔpH = {delta_ph:.2f})."
        )
        if "stress_buffer" not in session.protocol_progress:
            session.protocol_progress.append("stress_buffer")
        session.score_parts["technique"] = min(20, (10 if ph_meter.get("calibrated") else 0) + (10 if burette.get("stress_tested") and ph_meter.get("calibrated") else 0))
        visuals.append({"type": "animation", "target": "stress_burette", "name": "dispense"})
        visuals.append({"type": "readout", "target": "ph_meter", "value": round(final_pt.ph, 2), "unit": "pH"})
        events.append({"type": "stress_tested", "titrant": titrant, "delta_ph": round(delta_ph, 2)})

    # 6. Submit Buffer Design
    elif action == "submit_buffer_design":
        if not burette.get("stress_tested"):
            return ActionResult(accepted=False, message="Perform stress test before submitting evaluation.")

        target_ph = float(beaker.get("target_ph", 4.75))
        prepared_ph_raw = beaker.get("ph")
        prepared_ph = float(prepared_ph_raw) if prepared_ph_raw is not None else target_ph
        ph_error = abs(prepared_ph - target_ph)

        if ph_error <= 0.05:
            accuracy_pts = 30
        elif ph_error <= 0.20:
            accuracy_pts = 20
        elif ph_error <= 0.50:
            accuracy_pts = 10
        elif ph_error <= 1.0:
            accuracy_pts = 5
        else:
            accuracy_pts = 0

        if any(v.rule_id in ("B2", "B3") for v in session.violations):
            accuracy_pts = min(accuracy_pts, 5)

        session.score_parts["accuracy"] = accuracy_pts

        message = f"Buffer evaluation submitted. Target pH: {target_ph:.2f}, Prepared pH: {prepared_ph:.2f} (Error: {ph_error:.2f})."
        if "submit_buffer_design" not in session.protocol_progress:
            session.protocol_progress.append("submit_buffer_design")
        visuals.append({"type": "particle", "target": "avatar", "name": "sparkle"})
        events.append({"type": "design_submitted", "target_ph": target_ph, "prepared_ph": prepared_ph})

    # 7. Dispose Waste
    elif action == "dispose_waste":
        if not has_ppe:
            v = Violation(
                rule_id="B1",
                title="PPE Violation",
                explanation="Handled chemical waste without protective gear.",
                severity="warning",
                penalty_points=15,
            )
            violations.append(v)
            session.violations.append(v)
            session.score_parts["safety"] = max(0, session.score_parts.get("safety", 40) - 15)

        waste_bin["items"].append(f"Buffer mixture ({beaker.get('volume_ml', 100):.0f} mL)")
        beaker["prepared"] = False
        beaker["clean"] = True
        beaker["ph"] = None

        message = "Neutralized and disposed of buffer solutions into chemical waste container."
        if "dispose_waste" not in session.protocol_progress:
            session.protocol_progress.append("dispose_waste")
        visuals.append({"type": "pour", "target": "chemical_waste_bin"})
        events.append({"type": "waste_disposed", "target": "chemical_waste_bin"})

    # 8. Wash Hands
    elif action == "wash_hands":
        sink["clean"] = True
        message = "Washed hands thoroughly with soap and warm water."
        if "wash_hands" not in session.protocol_progress:
            session.protocol_progress.append("wash_hands")
        visuals.append({"type": "particle", "target": "sink", "name": "bubbles"})
        events.append({"type": "hands_washed"})

    # 9. Submit Report
    elif action == "submit_report":
        status = "completed"
        session.status = "completed"
        if "wash_hands" not in session.protocol_progress:
            v = Violation(
                rule_id="B1",
                title="Hygiene Violation",
                explanation="Exited laboratory bench without washing hands at sink.",
                severity="warning",
                penalty_points=5,
            )
            violations.append(v)
            session.violations.append(v)
            session.score_parts["safety"] = max(0, session.score_parts.get("safety", 40) - 5)

        n_proto = len([step for step in ["wear_ppe", "select_buffer_system", "prepare_buffer", "test_capacity", "stress_buffer", "submit_buffer_design", "dispose_waste", "wash_hands"] if step in session.protocol_progress])
        session.score_parts["protocol"] = min(10, int(round(10.0 * n_proto / 8)))

        message = "Submitted completed Buffer Solutions & Capacity Bench analytical report."
        if "submit_report" not in session.protocol_progress:
            session.protocol_progress.append("submit_report")
        visuals.append({"type": "particle", "target": "avatar", "name": "confetti"})
        events.append({"type": "report_submitted"})

    else:
        return ActionResult(accepted=False, message=f"Action '{action}' is not supported on Buffer Bench.")

    return ActionResult(
        accepted=True,
        message=message,
        events=events,
        violations=violations,
        visuals=visuals,
        status=status,
    )
