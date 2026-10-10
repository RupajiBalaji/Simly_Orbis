"""
Orbis Lab stateful lab-session engine.

Implements the state machine, context-aware available actions,
simulation execution, and safety rule checking.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import random
from typing import Any

from app.core.registry import get_module
from app.lab.experiments import get_experiment
from app.lab.models import (
    ActionRequest,
    ActionResult,
    ActionType,
    AvailableAction,
    CharacterAnimation,
    LabSession,
    VisualDirective,
)
from app.lab.rules import check_safety_rules
from app.modules.chem_titration import compute_indicator_color, compute_ph_strong, compute_ph_weak
from app.sim.drugs import get_drug
from app.sim.models import Patient
from app.sim.pk_engine import simulate


def create_session(experiment_id: str, nickname: str) -> LabSession:
    """Instantiate a new lab session initialized with experiment apparatus and inventory."""
    exp = get_experiment(experiment_id)

    # Deep-copy apparatus state and inventory
    import copy
    apparatus_copy = copy.deepcopy(exp.apparatus)
    inventory_copy = copy.deepcopy(exp.inventory)

    session = LabSession(
        experiment_id=experiment_id,
        nickname=nickname.strip() or "Researcher",
        created_at=datetime.now(timezone.utc).isoformat(),
        clock_h=0.0,
        ppe=set(),
        apparatus_state=apparatus_copy,
        inventory=inventory_copy,
        samples=[],
        protocol_progress=[],
        score_parts={
            "safety": exp.scoring_weights.get("safety", 40),
            "accuracy": exp.scoring_weights.get("accuracy", 30),
            "technique": exp.scoring_weights.get("technique", 20),
            "protocol": exp.scoring_weights.get("protocol", 10),
        },
        violations=[],
        events=[
            {
                "timestamp_h": 0.0,
                "action": "session_start",
                "message": f"Session started for {exp.title} by {nickname}.",
                "severity": "info",
            }
        ],
        status="active",
    )
    return session


def get_available_actions(session: LabSession) -> list[AvailableAction]:
    """
    Return context-aware available actions with targets and enable/disable rationale.
    Powers the 3D client interaction menu and dev console.
    """
    exp = get_experiment(session.experiment_id)
    is_active = session.status == "active"
    actions: list[AvailableAction] = []

    # 1. Wear PPE
    ppe_missing = [p for p in ["goggles", "gloves", "coat"] if p not in session.ppe]
    actions.append(
        AvailableAction(
            action=ActionType.wear_ppe,
            label="Don PPE Gear",
            targets=["all", "goggles", "gloves", "coat"],
            enabled=is_active and len(ppe_missing) > 0,
            disabled_reason="All required PPE items already worn." if len(ppe_missing) == 0 else None,
        )
    )

    # 2. Remove PPE
    actions.append(
        AvailableAction(
            action=ActionType.remove_ppe,
            label="Doff PPE Gear",
            targets=["all", "gloves", "goggles", "coat"],
            enabled=is_active and len(session.ppe) > 0,
            disabled_reason="No PPE currently worn." if len(session.ppe) == 0 else None,
        )
    )

    # 3. Experiment specific actions
    if session.experiment_id == "pk_ward":
        balance = session.apparatus_state.get("digital_balance", {})
        cup = session.apparatus_state.get("dosing_cup", {})
        patient_st = session.apparatus_state.get("patient_bed", {}).get("patient", {})

        # Tare balance
        actions.append(
            AvailableAction(
                action=ActionType.tare_balance,
                label="Tare Balance",
                targets=["digital_balance"],
                enabled=is_active and not balance.get("tared", False),
                disabled_reason="Balance is already zeroed (tared)." if balance.get("tared", False) else None,
            )
        )

        # Weigh dose
        has_powder = session.inventory.get("paracetamol_powder", {}).get("amount_mg", 0) > 0
        actions.append(
            AvailableAction(
                action=ActionType.weigh,
                label="Weigh Paracetamol",
                targets=["digital_balance"],
                enabled=is_active and has_powder,
                disabled_reason="No medicinal powder remaining in inventory." if not has_powder else None,
            )
        )

        # Dissolve dose
        has_weighed = balance.get("reading_g", 0.0) > 0.0
        actions.append(
            AvailableAction(
                action=ActionType.dissolve,
                label="Dissolve in Water",
                targets=["dosing_cup"],
                enabled=is_active and has_weighed and not cup.get("dissolved", False),
                disabled_reason="No weighed powder on balance or already dissolved." if not has_weighed or cup.get("dissolved") else None,
            )
        )

        # Label container or tube
        unlabeled_targets = []
        if not cup.get("labeled"):
            unlabeled_targets.append("dosing_cup")
        for tid in ["tube_1", "tube_2", "tube_3"]:
            if not session.apparatus_state.get(tid, {}).get("labeled"):
                unlabeled_targets.append(tid)

        actions.append(
            AvailableAction(
                action=ActionType.label,
                label="Label Container / Tube",
                targets=unlabeled_targets or ["dosing_cup", "tube_1"],
                enabled=is_active and len(unlabeled_targets) > 0,
                disabled_reason="All current tubes and containers are already labelled." if len(unlabeled_targets) == 0 else None,
            )
        )

        # Administer oral
        can_administer = cup.get("dissolved", False) and cup.get("volume_ml", 0) > 0
        actions.append(
            AvailableAction(
                action=ActionType.administer_oral,
                label="Administer Oral Dose",
                targets=["patient_bed"],
                enabled=is_active and can_administer,
                disabled_reason="No dissolved liquid medication in dosing cup." if not can_administer else None,
            )
        )

        # Advance time
        actions.append(
            AvailableAction(
                action=ActionType.advance_time,
                label="Advance Clock",
                targets=["ward_clock"],
                enabled=is_active and session.clock_h < 24.0,
                disabled_reason="24-hour observation period completed." if session.clock_h >= 24.0 else None,
            )
        )

        # Draw blood
        available_tubes = [
            tid for tid in ["tube_1", "tube_2", "tube_3"]
            if not session.apparatus_state.get(tid, {}).get("drawn")
        ]
        has_doses = len(patient_st.get("doses_administered", [])) > 0
        actions.append(
            AvailableAction(
                action=ActionType.draw_blood,
                label="Venous Blood Draw",
                targets=available_tubes,
                enabled=is_active and len(available_tubes) > 0 and has_doses,
                disabled_reason="No doses administered yet or no empty collection tubes remaining." if not (available_tubes and has_doses) else None,
            )
        )

        # Run assay
        drawn_unassayed = [
            tid for tid in ["tube_1", "tube_2", "tube_3"]
            if session.apparatus_state.get(tid, {}).get("drawn") and not session.apparatus_state.get(tid, {}).get("analyzed")
        ]
        actions.append(
            AvailableAction(
                action=ActionType.run_assay,
                label="Run Centrifuge / Assay",
                targets=drawn_unassayed,
                enabled=is_active and len(drawn_unassayed) > 0,
                disabled_reason="No drawn unanalyzed blood tubes available." if len(drawn_unassayed) == 0 else None,
            )
        )

    elif session.experiment_id == "titration_bench":
        burette = session.apparatus_state.get("burette", {})
        flask = session.apparatus_state.get("conical_flask", {})

        # Rinse burette
        actions.append(
            AvailableAction(
                action=ActionType.rinse_burette,
                label="Rinse & Condition Burette",
                targets=["burette"],
                enabled=is_active and not burette.get("rinsed", False),
                disabled_reason="Burette has already been conditioned with titrant rinse." if burette.get("rinsed") else None,
            )
        )

        # Fill burette
        actions.append(
            AvailableAction(
                action=ActionType.fill_burette,
                label="Fill Burette with NaOH",
                targets=["burette"],
                enabled=is_active and burette.get("volume_ml", 0.0) < 50.0,
                disabled_reason="Burette is already filled to 50 mL mark." if burette.get("volume_ml", 0.0) >= 50.0 else None,
            )
        )

        # Pipette analyte
        actions.append(
            AvailableAction(
                action=ActionType.pipette_analyte,
                label="Pipette 25 mL Acid Analyte",
                targets=["acid_bottle_hcl", "acid_bottle_acetic"],
                enabled=is_active and flask.get("volume_ml", 0.0) == 0.0,
                disabled_reason="Flask already contains pipetted analyte solution." if flask.get("volume_ml", 0.0) > 0.0 else None,
            )
        )

        # Add indicator
        actions.append(
            AvailableAction(
                action=ActionType.add_indicator,
                label="Add Chemical Indicator",
                targets=["phenolphthalein", "methyl_orange", "bromothymol_blue"],
                enabled=is_active and flask.get("volume_ml", 0.0) > 0.0 and flask.get("indicator") is None,
                disabled_reason="Add acid analyte first, or indicator is already present." if (flask.get("volume_ml", 0.0) == 0 or flask.get("indicator")) else None,
            )
        )

        # Titrate
        has_titrant = burette.get("volume_ml", 0.0) > 0.0
        has_sample = flask.get("volume_ml", 0.0) > 0.0
        actions.append(
            AvailableAction(
                action=ActionType.titrate,
                label="Dispense NaOH Titrant",
                targets=["conical_flask"],
                enabled=is_active and has_titrant and has_sample,
                disabled_reason="Fill burette and pipette analyte into flask before titrating." if not (has_titrant and has_sample) else None,
            )
        )

        # Swirl
        actions.append(
            AvailableAction(
                action=ActionType.swirl,
                label="Swirl Conical Flask",
                targets=["conical_flask"],
                enabled=is_active and flask.get("volume_ml", 0.0) > 0.0,
                disabled_reason="Flask is currently empty." if flask.get("volume_ml", 0.0) == 0.0 else None,
            )
        )

        # Read pH meter
        actions.append(
            AvailableAction(
                action=ActionType.read_ph_meter,
                label="Measure with pH Meter",
                targets=["ph_meter"],
                enabled=is_active and flask.get("volume_ml", 0.0) > 0.0,
                disabled_reason="Flask is currently empty." if flask.get("volume_ml", 0.0) == 0.0 else None,
            )
        )

        # Record endpoint
        actions.append(
            AvailableAction(
                action=ActionType.record_endpoint,
                label="Record Equivalence Endpoint",
                targets=["conical_flask"],
                enabled=is_active and flask.get("titrant_added_ml", 0.0) > 0.0,
                disabled_reason="No titrant added yet." if flask.get("titrant_added_ml", 0.0) == 0.0 else None,
            )
        )

    # General actions
    # Pour / transfer
    actions.append(
        AvailableAction(
            action=ActionType.pour,
            label="Pour Liquid",
            targets=["water_jug", "wash_bottle"],
            enabled=is_active,
        )
    )

    # Dispose waste
    actions.append(
        AvailableAction(
            action=ActionType.dispose_waste,
            label="Dispose Waste",
            targets=["biohazard_bin", "chemical_waste_bin"],
            enabled=is_active,
        )
    )

    # Wash hands
    actions.append(
        AvailableAction(
            action=ActionType.wash_hands,
            label="Wash Hands at Sink",
            targets=["sink"],
            enabled=is_active,
        )
    )

    # Submit report
    actions.append(
        AvailableAction(
            action=ActionType.submit_report,
            label="Submit Lab Report",
            targets=["session_report"],
            enabled=is_active,
        )
    )

    return actions


def _compute_patient_pk(session: LabSession) -> tuple[float, str, dict[str, Any]]:
    """
    Compute current true plasma concentration via superposition of all doses given so far.
    Returns (concentration_mg_l, status_string, vitals_dict).
    """
    patient_data = session.apparatus_state.get("patient_bed", {}).get("patient", {})
    doses = patient_data.get("doses_administered", [])
    if not doses:
        return 0.0, "subtherapeutic", {"hr": 72, "spo2": 99, "status": "normal"}

    drug = get_drug(patient_data.get("drug_id", "paracetamol"))
    patient = Patient(
        weight_kg=float(patient_data.get("weight_kg", 70.0)),
        clearance_multiplier=float(patient_data.get("clearance_multiplier", 1.0)),
    )

    # Sum concentration at current clock_h across all administered doses
    total_conc = 0.0
    for d in doses:
        dose_mg = float(d["dose_mg"])
        admin_time = float(d["time_h"])
        elapsed = session.clock_h - admin_time
        if elapsed >= 0:
            # Simulate single dose from elapsed time
            res = simulate(drug, patient, dose_mg, n_doses=1, interval_h=24.0)
            # Find nearest point in simulation time array
            idx = int(round(elapsed / 0.1))
            if 0 <= idx < len(res.concentrations):
                total_conc += res.concentrations[idx]

    # Status classification
    if total_conc >= drug.red_threshold:
        status = "toxic"
        vitals = {"hr": 105, "spo2": 95, "status": "toxic_tachycardia"}
    elif total_conc >= drug.green_low:
        status = "therapeutic"
        vitals = {"hr": 70, "spo2": 99, "status": "stable_therapeutic"}
    else:
        status = "subtherapeutic"
        vitals = {"hr": 75, "spo2": 99, "status": "mild_pain"}

    return round(total_conc, 3), status, vitals


def apply_action(session: LabSession, req: ActionRequest) -> ActionResult:
    """
    Execute player action on lab session.
    Validates safety rules, advances physics/chemical state, records events,
    and returns 3D visual directives and character animations.
    """
    if session.status != "active":
        return ActionResult(
            accepted=False,
            message=f"Session is already {session.status}. No further actions permitted.",
            events=[],
            violations=[],
            visuals=[],
            status=session.status,
        )

    # 1. Run safety rules
    violations = check_safety_rules(session, req)
    session.violations.extend(violations)

    # Check for critical failures (2 or more critical violations terminate session)
    crit_count = sum(1 for v in session.violations if v.severity == "critical")
    if crit_count >= 2:
        session.status = "failed"
        session.score_parts["safety"] = max(0, session.score_parts["safety"] - 35)
        event_dict = {
            "timestamp_h": session.clock_h,
            "action": req.action.value,
            "message": "SESSION TERMINATED: Multiple critical laboratory safety breaches detected.",
            "severity": "critical",
        }
        session.events.append(event_dict)
        return ActionResult(
            accepted=False,
            message="CRITICAL SAFETY FAILURE: Two critical violations have terminated the session.",
            events=[event_dict],
            violations=violations,
            visuals=[VisualDirective(type="effect", target="lab_alarm", name="alarm", duration_ms=4000).model_dump()],
            character_animation=CharacterAnimation(name="idle", target="avatar", duration_ms=1000).model_dump(),
            status="failed",
        )

    # Apply penalty to safety score
    total_penalty = sum(v.penalty_points for v in violations)
    session.score_parts["safety"] = max(0, session.score_parts["safety"] - total_penalty)

    # 2. Domain logic execution
    visuals: list[dict[str, Any]] = []
    anim: CharacterAnimation | None = None
    msg = ""
    hints: list[str] = []
    accepted = True

    action = req.action
    params = req.params
    target = req.target or str(params.get("target", "") or "")

    # -----------------------------------------------------------------------
    # PPE Actions
    # -----------------------------------------------------------------------
    if action == ActionType.wear_ppe:
        target_ppe = target if target in ("goggles", "gloves", "coat") else "all"
        if target_ppe == "all":
            session.ppe.update(["goggles", "gloves", "coat"])
            msg = "Equipped full personal protective equipment: safety goggles, gloves, and lab coat."
        else:
            session.ppe.add(target_ppe)
            msg = f"Put on {target_ppe}."
        anim = CharacterAnimation(name="wear_ppe", target="avatar", duration_ms=1500)
        visuals.append(VisualDirective(type="effect", target="avatar", name="glow", duration_ms=1200).model_dump())
        if "wear_ppe" not in session.protocol_progress:
            session.protocol_progress.append("wear_ppe")

    elif action == ActionType.remove_ppe:
        target_ppe = target if target in ("goggles", "gloves", "coat") else "all"
        if target_ppe == "all":
            session.ppe.clear()
            msg = "Removed all PPE gear."
        else:
            session.ppe.discard(target_ppe)
            msg = f"Removed {target_ppe}."
        anim = CharacterAnimation(name="wear_ppe", target="avatar", duration_ms=1200)

    # -----------------------------------------------------------------------
    # PK Ward Domain Logic
    # -----------------------------------------------------------------------
    elif action == ActionType.tare_balance:
        bal = session.apparatus_state.setdefault("digital_balance", {})
        bal["tared"] = True
        bal["reading_g"] = 0.000
        msg = "Digital analytical balance tared (0.000 g display)."
        anim = CharacterAnimation(name="weigh", target="digital_balance", duration_ms=1200)
        visuals.append(VisualDirective(type="readout", target="digital_balance", label="Tare", value=0.000, unit="g").model_dump())
        if "tare_balance" not in session.protocol_progress:
            session.protocol_progress.append("tare_balance")

    elif action == ActionType.weigh:
        bal = session.apparatus_state.setdefault("digital_balance", {})
        dose_mg = float(params.get("dose_mg", 500.0))
        dose_g = dose_mg / 1000.0
        bal["reading_g"] = round(dose_g, 3)

        # Update powder inventory
        inv = session.inventory.get("paracetamol_powder", {})
        inv["amount_mg"] = max(0.0, inv.get("amount_mg", 5000.0) - dose_mg)

        msg = f"Weighed {dose_mg:.1f} mg ({dose_g:.3f} g) of paracetamol powder on analytical balance."
        anim = CharacterAnimation(name="weigh", target="digital_balance", duration_ms=1800)
        visuals.append(VisualDirective(type="readout", target="digital_balance", label="Weight", value=round(dose_g, 3), unit="g").model_dump())
        if "weigh_dose" not in session.protocol_progress:
            session.protocol_progress.append("weigh_dose")

    elif action == ActionType.dissolve:
        cup = session.apparatus_state.setdefault("dosing_cup", {})
        bal = session.apparatus_state.setdefault("digital_balance", {})
        dose_g = bal.get("reading_g", 0.500)
        dose_mg = dose_g * 1000.0
        volume_ml = float(params.get("volume_ml", 50.0))

        cup["contents"] = {"substance": "paracetamol", "dose_mg": dose_mg}
        cup["volume_ml"] = volume_ml
        cup["dissolved"] = True
        bal["reading_g"] = 0.000

        msg = f"Dissolved {dose_mg:.0f} mg powder in {volume_ml:.0f} mL water inside the dosing cup."
        anim = CharacterAnimation(name="pour", target="dosing_cup", duration_ms=1800)
        visuals.append(VisualDirective(type="liquid", target="dosing_cup", hex="#f1f5f9", volume_ml=volume_ml, opacity=0.85).model_dump())
        visuals.append(VisualDirective(type="effect", target="dosing_cup", name="bubbles", duration_ms=1500).model_dump())
        if "dissolve_dose" not in session.protocol_progress:
            session.protocol_progress.append("dissolve_dose")

    elif action == ActionType.label:
        lbl_target = target or "dosing_cup"
        text = str(params.get("text", "Paracetamol 500mg - Patient Alex"))
        obj = session.apparatus_state.setdefault(lbl_target, {})
        obj["labeled"] = True
        obj["label_text"] = text
        msg = f"Applied identification label to {lbl_target}: '{text}'."
        anim = CharacterAnimation(name="write_label", target=lbl_target, duration_ms=1400)
        visuals.append(VisualDirective(type="label", target=lbl_target, text=text).model_dump())

        if "dosing_cup" in lbl_target and "label_cup" not in session.protocol_progress:
            session.protocol_progress.append("label_cup")
        elif "tube" in lbl_target and "label_tube" not in session.protocol_progress:
            session.protocol_progress.append("label_tube")

    elif action == ActionType.administer_oral:
        cup = session.apparatus_state.setdefault("dosing_cup", {})
        patient_st = session.apparatus_state.setdefault("patient_bed", {}).setdefault("patient", {})
        dose_info = cup.get("contents", {})
        dose_mg = float(dose_info.get("dose_mg", 500.0))

        # Record administration
        doses = patient_st.setdefault("doses_administered", [])
        doses.append({"dose_mg": dose_mg, "time_h": session.clock_h})

        # Empty cup
        cup["volume_ml"] = 0.0
        cup["contents"] = {}
        cup["clean"] = False

        # Vitals update
        conc, status, vitals = _compute_patient_pk(session)
        msg = f"Administered {dose_mg:.0f} mg paracetamol oral suspension to patient at t={session.clock_h:.1f} h."
        anim = CharacterAnimation(name="administer", target="patient_bed", duration_ms=2200)
        visuals.append(VisualDirective(type="liquid", target="dosing_cup", hex="#f8fafc", volume_ml=0.0, opacity=0.0).model_dump())
        visuals.append(
            VisualDirective(
                type="vitals",
                patient="Alex (70 kg)",
                hr=vitals["hr"],
                spo2=vitals["spo2"],
                status=f"{status} (illustrative)",
            ).model_dump()
        )
        if "administer_oral" not in session.protocol_progress:
            session.protocol_progress.append("administer_oral")

    elif action == ActionType.advance_time:
        delta_h = float(params.get("hours", 1.0))
        delta_h = max(0.25, min(6.0, delta_h))
        session.clock_h = round(min(24.0, session.clock_h + delta_h), 2)

        conc, status, vitals = _compute_patient_pk(session)
        msg = f"Advanced ward clock by +{delta_h:.2f} h (current time: t={session.clock_h:.2f} h)."
        visuals.append(VisualDirective(type="readout", target="ward_clock", label="Time", value=session.clock_h, unit="h").model_dump())
        visuals.append(
            VisualDirective(
                type="vitals",
                patient="Alex (70 kg)",
                hr=vitals["hr"],
                spo2=vitals["spo2"],
                status=f"{status} (illustrative)",
            ).model_dump()
        )
        if "advance_time" not in session.protocol_progress:
            session.protocol_progress.append("advance_time")

    elif action == ActionType.draw_blood:
        tube_id = target if target in ("tube_1", "tube_2", "tube_3") else "tube_1"
        tube = session.apparatus_state.setdefault(tube_id, {})
        true_conc, status, vitals = _compute_patient_pk(session)

        # Apply deterministic 3% seeded assay noise
        seed_val = int(hashlib.md5(f"{session.session_id}_{tube_id}".encode()).hexdigest(), 16)
        rng = random.Random(seed_val)
        noise_factor = rng.gauss(1.0, 0.03)  # 3% standard deviation
        noisy_conc = round(true_conc * noise_factor, 3)

        tube["drawn"] = True
        tube["sample_time_h"] = session.clock_h
        tube["concentration_mg_l"] = true_conc
        tube["assayed_concentration_mg_l"] = noisy_conc
        session.samples.append({"tube_id": tube_id, "time_h": session.clock_h, "true_conc": true_conc, "noisy_conc": noisy_conc})

        msg = f"Drew 5 mL venous blood sample into {tube_id} at t={session.clock_h:.2f} h."
        anim = CharacterAnimation(name="draw_blood", target="patient_bed", duration_ms=2500)
        visuals.append(VisualDirective(type="liquid", target=tube_id, hex="#991b1b", volume_ml=5.0, opacity=0.95).model_dump())
        visuals.append(
            VisualDirective(
                type="vitals",
                patient="Alex (70 kg)",
                hr=vitals["hr"],
                spo2=vitals["spo2"],
                status=f"{status} (illustrative)",
            ).model_dump()
        )
        if "draw_blood" not in session.protocol_progress:
            session.protocol_progress.append("draw_blood")

    elif action == ActionType.run_assay:
        tube_id = target if target in ("tube_1", "tube_2", "tube_3") else "tube_1"
        tube = session.apparatus_state.get(tube_id, {})
        assayed_val = tube.get("assayed_concentration_mg_l", 0.0)
        tube["analyzed"] = True

        msg = f"Centrifuge assay completed for {tube_id}: measured plasma level = {assayed_val:.2f} mg/L."
        anim = CharacterAnimation(name="read", target="assay_analyzer", duration_ms=2000)
        visuals.append(VisualDirective(type="readout", target="assay_analyzer", label="Plasma Assay", value=assayed_val, unit="mg/L").model_dump())
        visuals.append(VisualDirective(type="effect", target="assay_analyzer", name="glow", duration_ms=2000).model_dump())
        if "run_assay" not in session.protocol_progress:
            session.protocol_progress.append("run_assay")

    # -----------------------------------------------------------------------
    # Titration Bench Domain Logic
    # -----------------------------------------------------------------------
    elif action == ActionType.rinse_burette:
        bur = session.apparatus_state.setdefault("burette", {})
        bur["rinsed"] = True
        msg = "Rinsed and conditioned the 50 mL burette with 5 mL of standardized 0.1 M NaOH titrant."
        anim = CharacterAnimation(name="turn_stopcock", target="burette", duration_ms=1800)
        visuals.append(VisualDirective(type="effect", target="burette", name="bubbles", duration_ms=1200).model_dump())
        if "rinse_burette" not in session.protocol_progress:
            session.protocol_progress.append("rinse_burette")

    elif action == ActionType.fill_burette:
        bur = session.apparatus_state.setdefault("burette", {})
        vol = float(params.get("volume_ml", 50.0))
        bur["volume_ml"] = vol
        bur["filled"] = True
        msg = f"Filled burette with {vol:.1f} mL of 0.1 M NaOH titrant."
        anim = CharacterAnimation(name="pour", target="burette", duration_ms=2000)
        visuals.append(VisualDirective(type="liquid", target="burette", hex="#f8fafc", volume_ml=vol, opacity=0.8).model_dump())
        visuals.append(VisualDirective(type="readout", target="burette", label="Titrant Vol", value=vol, unit="mL").model_dump())
        if "fill_burette" not in session.protocol_progress:
            session.protocol_progress.append("fill_burette")

    elif action == ActionType.pipette_analyte:
        flask = session.apparatus_state.setdefault("conical_flask", {})
        analyte_id = target or str(params.get("analyte", "hcl_0.1M"))
        if "acetic" in analyte_id:
            analyte_name = "acetic_0.1M"
        else:
            analyte_name = "hcl_0.1M"

        flask["analyte"] = analyte_name
        flask["volume_ml"] = 25.0
        flask["color_hex"] = "#f8fafc"
        msg = f"Pipetted exactly 25.0 mL of {analyte_name} acid analyte into the conical flask."
        anim = CharacterAnimation(name="pour", target="conical_flask", duration_ms=2200)
        visuals.append(VisualDirective(type="liquid", target="conical_flask", hex="#f8fafc", volume_ml=25.0, opacity=0.8).model_dump())
        if "pipette_analyte" not in session.protocol_progress:
            session.protocol_progress.append("pipette_analyte")

    elif action == ActionType.add_indicator:
        flask = session.apparatus_state.setdefault("conical_flask", {})
        indicator_name = target or str(params.get("indicator", "phenolphthalein"))
        flask["indicator"] = indicator_name

        # Calculate initial color
        analyte_name = flask.get("analyte", "hcl_0.1M")
        if analyte_name == "acetic_0.1M":
            init_ph = compute_ph_weak(0.1, 25.0, 0.1, 0.0)
        else:
            init_ph = compute_ph_strong(0.1, 25.0, 0.1, 0.0)

        color_hex = compute_indicator_color(init_ph, indicator_name)
        flask["ph"] = init_ph
        flask["color_hex"] = color_hex

        msg = f"Added 3 drops of {indicator_name} indicator to the flask (solution color: {color_hex})."
        anim = CharacterAnimation(name="pour", target="conical_flask", duration_ms=1600)
        visuals.append(VisualDirective(type="liquid", target="conical_flask", hex=color_hex, volume_ml=float(flask.get("volume_ml", 25.0)), opacity=0.9).model_dump())
        visuals.append(VisualDirective(type="effect", target="conical_flask", name="bubbles", duration_ms=1000).model_dump())
        if "add_indicator" not in session.protocol_progress:
            session.protocol_progress.append("add_indicator")

    elif action == ActionType.titrate:
        flask = session.apparatus_state.setdefault("conical_flask", {})
        bur = session.apparatus_state.setdefault("burette", {})
        added_ml = float(params.get("volume_ml", 1.0))
        added_ml = max(0.1, min(10.0, added_ml))

        bur_vol = float(bur.get("volume_ml", 50.0))
        bur["volume_ml"] = max(0.0, bur_vol - added_ml)

        current_titrant = float(flask.get("titrant_added_ml", 0.0)) + added_ml
        flask["titrant_added_ml"] = round(current_titrant, 2)
        flask_vol = float(flask.get("volume_ml", 25.0)) + added_ml
        flask["volume_ml"] = round(flask_vol, 2)

        # Run titration simulation math
        analyte = flask.get("analyte", "hcl_0.1M")
        ca = 0.1
        cb = 0.1
        va = 25.0
        if analyte == "acetic_0.1M":
            new_ph = compute_ph_weak(ca, va, cb, current_titrant)
        else:
            new_ph = compute_ph_strong(ca, va, cb, current_titrant)

        ind = flask.get("indicator", "phenolphthalein")
        new_color = compute_indicator_color(new_ph, ind)
        flask["ph"] = round(new_ph, 2)
        flask["color_hex"] = new_color

        msg = f"Dispensed +{added_ml:.2f} mL NaOH titrant (Total added: {current_titrant:.2f} mL)."
        anim = CharacterAnimation(name="turn_stopcock", target="burette", duration_ms=1600)
        visuals.append(VisualDirective(type="liquid", target="burette", hex="#f8fafc", volume_ml=round(bur["volume_ml"], 2), opacity=0.8).model_dump())
        visuals.append(VisualDirective(type="liquid", target="conical_flask", hex=new_color, volume_ml=round(flask_vol, 2), opacity=0.9).model_dump())
        visuals.append(VisualDirective(type="readout", target="burette", label="Remaining", value=round(bur["volume_ml"], 2), unit="mL").model_dump())

        if "titrate" not in session.protocol_progress:
            session.protocol_progress.append("titrate")

    elif action == ActionType.swirl:
        flask = session.apparatus_state.setdefault("conical_flask", {})
        color_hex = flask.get("color_hex", "#f8fafc")
        vol = float(flask.get("volume_ml", 25.0))
        msg = "Swirled conical flask to ensure thorough chemical neutralization."
        anim = CharacterAnimation(name="swirl", target="conical_flask", duration_ms=1600)
        visuals.append(VisualDirective(type="liquid", target="conical_flask", hex=color_hex, volume_ml=vol, opacity=0.9).model_dump())
        visuals.append(VisualDirective(type="effect", target="conical_flask", name="bubbles", duration_ms=1200).model_dump())
        if "swirl" not in session.protocol_progress:
            session.protocol_progress.append("swirl")

    elif action == ActionType.read_ph_meter:
        flask = session.apparatus_state.setdefault("conical_flask", {})
        current_ph = flask.get("ph", 7.0)
        msg = f"Calibrated glass-electrode pH meter reading: pH = {current_ph:.2f}."
        anim = CharacterAnimation(name="read", target="ph_meter", duration_ms=1500)
        visuals.append(VisualDirective(type="readout", target="ph_meter", label="pH", value=round(current_ph, 2), unit="pH").model_dump())

    elif action == ActionType.record_endpoint:
        flask = session.apparatus_state.setdefault("conical_flask", {})
        recorded_vol = float(params.get("volume_ml", flask.get("titrant_added_ml", 25.0)))
        flask["recorded_endpoint_ml"] = recorded_vol
        msg = f"Recorded titration endpoint at {recorded_vol:.2f} mL titrant delivered."
        anim = CharacterAnimation(name="write_label", target="conical_flask", duration_ms=1400)
        visuals.append(VisualDirective(type="readout", target="conical_flask", label="Endpoint", value=recorded_vol, unit="mL").model_dump())
        if "record_endpoint" not in session.protocol_progress:
            session.protocol_progress.append("record_endpoint")

    # -----------------------------------------------------------------------
    # Waste & Cleanup Logic
    # -----------------------------------------------------------------------
    elif action == ActionType.dispose_waste:
        item = str(params.get("item", target or "waste"))
        bin_target = target or "chemical_waste_bin"
        waste_bin = session.apparatus_state.setdefault(bin_target, {"items": []})
        waste_bin.setdefault("items", []).append(item)
        msg = f"Disposed {item} into {bin_target}."
        anim = CharacterAnimation(name="dispose", target=bin_target, duration_ms=1500)
        if "dispose_waste" not in session.protocol_progress:
            session.protocol_progress.append("dispose_waste")

    elif action == ActionType.wash_hands:
        sink = session.apparatus_state.setdefault("sink", {})
        sink["hands_washed"] = True
        msg = "Washed and decontaminated hands with soap and water at the sink."
        anim = CharacterAnimation(name="wash_hands", target="sink", duration_ms=2000)
        visuals.append(VisualDirective(type="effect", target="sink", name="bubbles", duration_ms=1500).model_dump())
        if "wash_hands" not in session.protocol_progress:
            session.protocol_progress.append("wash_hands")

    elif action == ActionType.submit_report:
        session.status = "completed"
        msg = "Experiment session completed! Final lab analytical report compiled."
        anim = CharacterAnimation(name="idle", target="avatar", duration_ms=1000)
        if "submit_report" not in session.protocol_progress:
            session.protocol_progress.append("submit_report")

    # Fallback / Pour general
    elif action == ActionType.pour:
        src = params.get("source", "water_jug")
        dst = params.get("destination", target or "dosing_cup")
        vol = float(params.get("volume_ml", 50.0))
        msg = f"Poured {vol:.0f} mL liquid from {src} to {dst}."
        anim = CharacterAnimation(name="pour", target=dst, duration_ms=1800)
        visuals.append(VisualDirective(type="liquid", target=dst, hex="#f8fafc", volume_ml=vol, opacity=0.8).model_dump())

    # 3. Dynamic Score Recalculation
    exp = get_experiment(session.experiment_id)
    n_proto_total = max(1, len(exp.protocol))
    n_proto_done = len(session.protocol_progress)
    session.score_parts["protocol"] = min(10, int(round(10.0 * n_proto_done / n_proto_total)))

    # Accuracy & technique scoring
    if session.experiment_id == "pk_ward":
        # Accuracy: did they draw blood and run assay?
        samples_done = sum(1 for tid in ["tube_1", "tube_2", "tube_3"] if session.apparatus_state.get(tid, {}).get("analyzed"))
        session.score_parts["accuracy"] = min(30, samples_done * 15)

        # Technique: tared balance (7), single dose <= 500mg (7), dissolved (6)
        t_score = 0
        if session.apparatus_state.get("digital_balance", {}).get("tared"):
            t_score += 7
        patient_doses = session.apparatus_state.get("patient_bed", {}).get("patient", {}).get("doses_administered", [])
        if patient_doses and all(d["dose_mg"] <= 500.0 for d in patient_doses):
            t_score += 7
        if session.apparatus_state.get("dosing_cup", {}).get("dissolved"):
            t_score += 6
        session.score_parts["technique"] = min(20, t_score)

    elif session.experiment_id == "titration_bench":
        # Technique: rinsed burette (7), dropwise/swirled (7), no severe overshoot (6)
        bur = session.apparatus_state.get("burette", {})
        flask = session.apparatus_state.get("conical_flask", {})
        t_score = 0
        if bur.get("rinsed"):
            t_score += 7
        if "swirl" in session.protocol_progress:
            t_score += 7
        overshoot = max(0.0, float(flask.get("titrant_added_ml", 0.0)) - 25.0)
        if overshoot <= 1.0:
            t_score += 6
        session.score_parts["technique"] = min(20, t_score)

        # Accuracy: accuracy of endpoint vs 25.0 mL
        rec_ep = flask.get("recorded_endpoint_ml")
        if rec_ep is not None:
            err = abs(rec_ep - 25.0)
            if err <= 0.2:
                session.score_parts["accuracy"] = 30
            elif err <= 0.5:
                session.score_parts["accuracy"] = 25
            elif err <= 1.0:
                session.score_parts["accuracy"] = 15
            else:
                session.score_parts["accuracy"] = 5
        else:
            session.score_parts["accuracy"] = 10 if flask.get("titrant_added_ml", 0.0) > 0 else 0

    # Record event in event log
    event_entry = {
        "timestamp_h": session.clock_h,
        "action": action.value,
        "message": msg,
        "severity": "violation" if violations else "normal",
    }
    session.events.append(event_entry)
    if len(session.events) > 500:
        session.events = session.events[-500:]

    return ActionResult(
        accepted=accepted,
        message=msg,
        events=[event_entry],
        violations=violations,
        visuals=visuals,
        character_animation=anim.model_dump() if anim else None,
        score_delta=-total_penalty if violations else 0,
        hints=hints,
        status=session.status,
    )
