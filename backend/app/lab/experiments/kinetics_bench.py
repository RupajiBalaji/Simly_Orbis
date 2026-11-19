"""
backend/app/lab/experiments/kinetics_bench.py
Reaction Kinetics Bench Experiment Implementation (chem.kinetics).

Implements Section 9.2 & Section 18 (P3-T4) of Simly Orbis MVP Build Specification:
- Interactive kinetics workflow: temperature selection, reactant preparation,
  spectrophotometer blank calibration, reaction initiation, time-series sampling,
  linearised transformations ([A], ln[A], 1/[A] vs t), seeded measurement noise,
  and student order & rate constant estimation scoring.
"""

from __future__ import annotations

import copy
import math
from typing import Any, Dict, List

from app.chem.kinetics import (
    arrhenius_k,
    celsius_to_kelvin,
    fit_best_order,
    generate_kinetics_observations,
    linear_regression,
)
from app.lab.experiments.base import ExperimentDefinition
from app.lab.models import (
    ActionRequest,
    ActionResult,
    AvailableAction,
    CharacterAnimation,
    LabSession,
    Violation,
    VisualDirective,
)

KINETICS_BENCH_EXPERIMENT = ExperimentDefinition(
    id="kinetics_bench",
    title="Reaction Kinetics Bench",
    district="chemistry",
    description=(
        "Investigate chemical reaction rates, determine reaction orders (0, 1, or 2), "
        "and calculate rate constants and activation energy using spectrophotometric "
        "time-series measurements, linearised plots, and seeded measurement noise."
    ),
    learning_goals=[
        "Maintain chemical laboratory PPE compliance (goggles, gloves, coat).",
        "Calibrate spectrophotometer with solvent blank before recording kinetic runs.",
        "Set and equilibrate reaction temperature using a circulating thermostat bath.",
        "Collect time-series concentration measurements with realistic measurement noise.",
        "Construct linearised kinetic plots ([A], ln[A], and 1/[A] vs time).",
        "Identify reaction order from linear regression correlation coefficients (R^2).",
        "Calculate experimental rate constants and evaluate temperature dependence.",
        "Safely neutralize and dispose of chemical reaction mixtures in designated waste.",
    ],
    required_ppe=["goggles", "gloves", "coat"],
    apparatus={
        "thermostat_bath": {
            "type": "thermostat",
            "temp_c": 25.0,
            "min_temp_c": 10.0,
            "max_temp_c": 80.0,
            "equilibrated": True,
        },
        "reaction_vessel": {
            "type": "reactor_flask",
            "volume_ml": 50.0,
            "reactant": None,
            "initial_conc_m": 1.0,
            "temperature_c": 25.0,
            "running": False,
            "started_at_s": 0.0,
            "true_order": 1,
            "true_k_ref": 0.05,
            "activation_energy_j": 45000.0,
            "clean": True,
        },
        "spectrophotometer": {
            "type": "detector",
            "calibrated": False,
            "cuvette_inserted": False,
            "last_reading_m": None,
            "time_series": [],
            "linear_fits": {},
        },
        "timer": {
            "type": "digital_timer",
            "elapsed_s": 0.0,
            "sampling_interval_s": 5.0,
            "num_samples": 10,
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
        "reactant_a": {"volume_ml": 250.0, "concentration_m": 2.0},
        "solvent_water": {"volume_ml": 1000.0},
    },
    scoring_weights={
        "safety": 30,
        "accuracy": 40,
        "technique": 20,
        "protocol": 10,
    },
)


def get_kinetics_available_actions(session: LabSession) -> List[AvailableAction]:
    """Context-aware actions available in Kinetics Bench."""
    ppe = session.ppe
    has_ppe = ("goggles" in ppe and "gloves" in ppe and "coat" in ppe)
    prog = session.protocol_progress
    vessel = session.apparatus_state.get("reaction_vessel", {})
    spec_dev = session.apparatus_state.get("spectrophotometer", {})

    actions: List[AvailableAction] = []

    # 1. PPE
    if not has_ppe:
        actions.append(AvailableAction(
            action="wear_ppe",
            label="Put on Lab PPE",
            targets=["avatar"],
            enabled=True,
        ))

    # 2. Set Temperature
    actions.append(AvailableAction(
        action="set_temperature",
        label="Set Thermostat Temperature",
        targets=["thermostat_bath"],
        enabled=True,
    ))

    # 3. Prepare Reactant
    actions.append(AvailableAction(
        action="prepare_reactant",
        label="Pipette Reactant into Vessel",
        targets=["reaction_vessel"],
        enabled=has_ppe and (vessel.get("reactant") is None),
        disabled_reason="Wear PPE first." if not has_ppe else "Reactant already charged.",
    ))

    # 4. Calibrate Spectrophotometer
    actions.append(AvailableAction(
        action="calibrate_spectrophotometer",
        label="Calibrate Spectrophotometer Blank",
        targets=["spectrophotometer"],
        enabled=has_ppe,
        disabled_reason="Wear PPE before handling cuvettes." if not has_ppe else None,
    ))

    # 5. Start Reaction
    has_charge = vessel.get("reactant") is not None
    actions.append(AvailableAction(
        action="start_reaction",
        label="Start Reaction Run",
        targets=["reaction_vessel"],
        enabled=has_ppe and has_charge and not vessel.get("running", False),
        disabled_reason="Charge reactant into vessel first." if not has_charge else None,
    ))

    # 6. Record Sampling
    actions.append(AvailableAction(
        action="record_sampling",
        label="Collect Kinetic Samples",
        targets=["spectrophotometer"],
        enabled=vessel.get("running", False) or "start_reaction" in prog,
        disabled_reason="Start reaction run first.",
    ))

    # 7. Analyze Linear Plots
    has_samples = len(spec_dev.get("time_series", [])) > 0
    actions.append(AvailableAction(
        action="analyze_linear_plots",
        label="Plot Linearised Rate Models",
        targets=["spectrophotometer"],
        enabled=has_samples,
        disabled_reason="Collect kinetic samples first.",
    ))

    # 8. Submit Estimate
    actions.append(AvailableAction(
        action="submit_order_estimate",
        label="Submit Order & Rate Constant Estimate",
        targets=["spectrophotometer"],
        enabled=has_samples,
        disabled_reason="Collect samples and plot data first.",
    ))

    # 9. Waste disposal & hand washing
    actions.append(AvailableAction(
        action="dispose_waste",
        label="Dispose Chemical Waste",
        targets=["chemical_waste_bin"],
        enabled=has_ppe and (vessel.get("reactant") is not None or "start_reaction" in prog),
    ))

    actions.append(AvailableAction(
        action="wash_hands",
        label="Wash Hands at Sink",
        targets=["sink"],
        enabled=True,
    ))

    actions.append(AvailableAction(
        action="submit_report",
        label="Submit Completed Kinetics Report",
        targets=["avatar"],
        enabled="submit_order_estimate" in prog or "record_sampling" in prog,
    ))

    return actions


def apply_kinetics_action(session: LabSession, req: ActionRequest) -> ActionResult:
    """Execute action within Kinetics Bench."""
    action = req.action
    params = req.params or {}
    target = req.target or ""

    violations: List[Violation] = []
    visuals: List[Dict[str, Any]] = []
    events: List[Dict[str, Any]] = []
    message = ""
    status = session.status

    vessel = session.apparatus_state.setdefault("reaction_vessel", {})
    spec_dev = session.apparatus_state.setdefault("spectrophotometer", {})
    thermo = session.apparatus_state.setdefault("thermostat_bath", {})

    ppe = session.ppe
    has_ppe = ("goggles" in ppe and "gloves" in ppe and "coat" in ppe)

    # -----------------------------------------------------------------------
    # Action Handlers
    # -----------------------------------------------------------------------
    if action == "wear_ppe":
        item = params.get("item", "all")
        if item == "all":
            session.ppe = {"goggles", "gloves", "coat"}
        else:
            session.ppe.add(item)
        message = f"Put on personal protective equipment: {', '.join(sorted(session.ppe))}."
        if "wear_ppe" not in session.protocol_progress:
            session.protocol_progress.append("wear_ppe")

    elif action == "set_temperature":
        temp_c = float(params.get("temperature_c", 25.0))
        if temp_c > 80.0:
            violations.append(Violation(
                rule_id="K2",
                title="Excessive Thermostat Temperature",
                severity="warning",
                penalty_points=10,
                explanation="Thermostat temperature exceeds 80°C threshold; high temperature creates solvent evaporation and vapor pressure hazards.",
            ))
            session.score_parts["safety"] = max(0, session.score_parts.get("safety", 30) - 10)
        thermo["temp_c"] = temp_c
        vessel["temperature_c"] = temp_c
        message = f"Set thermostat water bath to {temp_c:.1f} °C. Circulating fluid equilibrated."
        visuals.append(VisualDirective(type="readout", target="thermostat_bath", label="TEMPERATURE", value=f"{temp_c:.1f}", unit="°C").model_dump())
        if "set_temperature" not in session.protocol_progress:
            session.protocol_progress.append("set_temperature")

    elif action == "prepare_reactant":
        if not has_ppe:
            violations.append(Violation(
                rule_id="R1",
                title="Missing Personal Protective Equipment",
                severity="critical",
                penalty_points=20,
                explanation="Handled chemical reagents without required goggles, gloves, and coat.",
            ))
            session.score_parts["safety"] = max(0, session.score_parts.get("safety", 30) - 20)

        conc = float(params.get("initial_conc_m", 1.0))
        vol = float(params.get("volume_ml", 50.0))
        vessel["reactant"] = "reactant_a"
        vessel["initial_conc_m"] = conc
        vessel["volume_ml"] = vol
        vessel["clean"] = False
        message = f"Pipetted {vol:.1f} mL of reactant solution ([A]_0 = {conc:.2f} M) into reactor vessel."
        visuals.append(VisualDirective(type="liquid", target="reaction_vessel", hex="#38bdf8", volume_ml=vol, opacity=0.85).model_dump())
        if "prepare_reactant" not in session.protocol_progress:
            session.protocol_progress.append("prepare_reactant")

    elif action == "calibrate_spectrophotometer":
        spec_dev["calibrated"] = True
        spec_dev["cuvette_inserted"] = True
        message = "Inserted solvent blank into optical path and calibrated zero-absorbance baseline."
        visuals.append(VisualDirective(type="effect", target="spectrophotometer", name="glow", duration_ms=1000).model_dump())
        if "calibrate_spectrophotometer" not in session.protocol_progress:
            session.protocol_progress.append("calibrate_spectrophotometer")

    elif action == "start_reaction":
        if not has_ppe:
            violations.append(Violation(
                rule_id="R1",
                title="Chemical Reaction Started Without PPE",
                severity="critical",
                penalty_points=15,
                explanation="Started kinetic reaction without wearing full laboratory PPE.",
            ))
            session.score_parts["safety"] = max(0, session.score_parts.get("safety", 30) - 15)

        vessel["running"] = True
        # Determine reaction parameters (order preset: default 1, can be passed or scenario fixed)
        order = int(params.get("order", vessel.get("true_order", 1)))
        vessel["true_order"] = order

        # Arrhenius rate constant at vessel temperature
        temp_c = float(vessel.get("temperature_c", 25.0))
        t_kelvin = celsius_to_kelvin(temp_c)
        ea_j = float(vessel.get("activation_energy_j", 45000.0))
        a_pre = 3.5e6  # Pre-exponential factor
        k_at_t = arrhenius_k(a_pre, ea_j, t_kelvin)
        vessel["true_k"] = round(k_at_t, 4)

        message = f"Reaction initiated at {temp_c:.1f} °C. Timer synchronized."
        visuals.append(VisualDirective(type="effect", target="reaction_vessel", name="bubbles", duration_ms=1500).model_dump())
        if "start_reaction" not in session.protocol_progress:
            session.protocol_progress.append("start_reaction")

    elif action == "record_sampling":
        if not spec_dev.get("calibrated", False):
            violations.append(Violation(
                rule_id="K1",
                title="Uncalibrated Optical Detector",
                severity="warning",
                penalty_points=10,
                explanation="Collected spectrophotometric kinetic data without zeroing against solvent blank.",
            ))
            session.score_parts["technique"] = max(0, session.score_parts.get("technique", 20) - 10)

        order = int(vessel.get("true_order", 1))
        k_val = float(vessel.get("true_k", 0.05))
        a0 = float(vessel.get("initial_conc_m", 1.0))
        duration_s = float(params.get("duration_s", 60.0))
        n_samples = int(params.get("num_samples", 12))
        noise_sd = float(params.get("noise_sd", 0.02))
        seed = int(params.get("seed", 42))

        step_t = duration_s / max(1, n_samples - 1)
        time_points = [round(i * step_t, 2) for i in range(n_samples)]

        obs = generate_kinetics_observations(
            order=order,
            k=k_val,
            a0=a0,
            time_points=time_points,
            noise_sd=noise_sd,
            seed=seed,
        )

        ts_data = [
            {
                "time_s": o.time,
                "conc_measured": round(o.a_measured, 5),
                "ln_conc": round(o.ln_a_measured, 5) if o.ln_a_measured is not None else None,
                "inv_conc": round(o.inv_a_measured, 5) if o.inv_a_measured is not None else None,
            }
            for o in obs
        ]
        spec_dev["time_series"] = ts_data
        spec_dev["last_reading_m"] = ts_data[-1]["conc_measured"]
        message = f"Acquired {len(ts_data)} time-series absorption data points over {duration_s:.0f} s (noise σ={noise_sd:.3f})."
        visuals.append(VisualDirective(type="readout", target="spectrophotometer", label="FINAL CONCENTRATION", value=f"{ts_data[-1]['conc_measured']:.4f}", unit="M").model_dump())
        if "record_sampling" not in session.protocol_progress:
            session.protocol_progress.append("record_sampling")

    elif action == "analyze_linear_plots":
        ts = spec_dev.get("time_series", [])
        if len(ts) < 2:
            return ActionResult(
                accepted=False,
                message="Cannot compute linear fits: fewer than 2 data points collected.",
                status=session.status,
            )

        times = [pt["time_s"] for pt in ts]
        c_vals = [pt["conc_measured"] for pt in ts]
        ln_vals = [pt["ln_conc"] for pt in ts if pt["ln_conc"] is not None]
        inv_vals = [pt["inv_conc"] for pt in ts if pt["inv_conc"] is not None]

        s0, i0, r2_0 = linear_regression(times, c_vals)
        s1, i1, r2_1 = linear_regression(times, ln_vals) if len(ln_vals) == len(times) else (0, 0, 0)
        s2, i2, r2_2 = linear_regression(times, inv_vals) if len(inv_vals) == len(times) else (0, 0, 0)

        fits = {
            "order_0": {"slope": round(s0, 5), "intercept": round(i0, 5), "r_squared": round(r2_0, 4)},
            "order_1": {"slope": round(s1, 5), "intercept": round(i1, 5), "r_squared": round(r2_1, 4)},
            "order_2": {"slope": round(s2, 5), "intercept": round(i2, 5), "r_squared": round(r2_2, 4)},
        }
        spec_dev["linear_fits"] = fits
        message = f"Linear regressions computed: Order 0 R²={r2_0:.4f}, Order 1 R²={r2_1:.4f}, Order 2 R²={r2_2:.4f}."
        if "analyze_linear_plots" not in session.protocol_progress:
            session.protocol_progress.append("analyze_linear_plots")

    elif action == "submit_order_estimate":
        est_order = int(params.get("estimated_order", 1))
        est_k = float(params.get("estimated_k", 0.05))

        true_order = int(vessel.get("true_order", 1))
        true_k = float(vessel.get("true_k", 0.05))

        acc_score = 0
        order_correct = (est_order == true_order)
        if order_correct:
            acc_score += 20

        # Rate constant accuracy
        if true_k > 0.0:
            rel_err = abs(est_k - true_k) / true_k
            if rel_err <= 0.10:
                acc_score += 20
            elif rel_err <= 0.25:
                acc_score += 10
            elif rel_err <= 0.50:
                acc_score += 5

        session.score_parts["accuracy"] = acc_score
        message = (
            f"Submitted estimate: Order {est_order} (True: {true_order}), "
            f"k = {est_k:.4f} s⁻¹ (True: {true_k:.4f} s⁻¹). Accuracy score: {acc_score}/40 pts."
        )
        if "submit_order_estimate" not in session.protocol_progress:
            session.protocol_progress.append("submit_order_estimate")

    elif action == "dispose_waste":
        if not has_ppe:
            violations.append(Violation(
                rule_id="R1",
                title="Hazardous Waste Handled Without PPE",
                severity="critical",
                penalty_points=15,
                explanation="Transferred chemical reaction waste without full PPE.",
            ))
            session.score_parts["safety"] = max(0, session.score_parts.get("safety", 30) - 15)

        bin_apparatus = session.apparatus_state.setdefault("chemical_waste_bin", {})
        bin_items = bin_apparatus.setdefault("items", [])
        bin_items.append("reaction_vessel_waste")
        vessel["reactant"] = None
        vessel["running"] = False
        vessel["clean"] = True
        message = "Reaction contents safely decanted into designated chemical waste bin."
        if "dispose_waste" not in session.protocol_progress:
            session.protocol_progress.append("dispose_waste")

    elif action == "wash_hands":
        message = "Hands thoroughly washed at sink with soap and running water."
        if "wash_hands" not in session.protocol_progress:
            session.protocol_progress.append("wash_hands")

    elif action == "submit_report":
        session.status = "completed"
        status = "completed"
        # Technique score: bonus for calibration and analysis
        tech_score = 0
        if spec_dev.get("calibrated", False):
            tech_score += 10
        if "analyze_linear_plots" in session.protocol_progress:
            tech_score += 10
        session.score_parts["technique"] = min(20, tech_score)

        # Protocol score
        proto_score = min(10, len(session.protocol_progress))
        session.score_parts["protocol"] = proto_score

        message = "Experiment session completed! Reaction kinetics laboratory analytical report compiled."
        if "submit_report" not in session.protocol_progress:
            session.protocol_progress.append("submit_report")

    session.violations.extend(violations)
    events.append({"action": action, "message": message})

    # Prepare return result
    return ActionResult(
        accepted=True,
        message=message,
        events=events,
        violations=violations,
        visuals=visuals,
        status=status,
    )
