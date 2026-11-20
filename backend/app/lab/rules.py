"""
Laboratory Safety Rules Engine.

DISCLAIMER: These safety rules are simplified summaries of standard educational
laboratory protocols. They are strictly for educational simulation and MUST NOT
be used for real clinical diagnosis, medical prescribing, or hazardous chemical operations.
"""

from __future__ import annotations

import json
from typing import Any, Callable

from app.lab.models import ActionRequest, ActionType, LabSession, Violation


class SafetyRule:
    """A laboratory safety rule with severity, penalty points, and educational explanation."""

    def __init__(
        self,
        rule_id: str,
        title: str,
        severity: str,
        penalty_points: int,
        explanation: str,
        checker: Callable[[LabSession, ActionRequest], bool],
    ) -> None:
        self.rule_id = rule_id
        self.title = title
        self.severity = severity
        self.penalty_points = penalty_points
        self.explanation = explanation
        self.checker = checker

    def check(self, session: LabSession, action_req: ActionRequest) -> Violation | None:
        """Check if action violates this rule in current session state."""
        if self.checker(session, action_req):
            return Violation(
                rule_id=self.rule_id,
                title=self.title,
                severity=self.severity,  # type: ignore[arg-type]
                penalty_points=self.penalty_points,
                explanation=self.explanation,
            )
        return None


# ---------------------------------------------------------------------------
# Rule Checkers
# ---------------------------------------------------------------------------

def _check_r1_goggles(session: LabSession, req: ActionRequest) -> bool:
    """R1 GOGGLES: Handling any chemical, drug or blood without goggles (critical)."""
    hazardous_actions = {
        ActionType.weigh,
        ActionType.dissolve,
        ActionType.pour,
        ActionType.draw_blood,
        ActionType.run_assay,
        ActionType.fill_burette,
        ActionType.pipette_analyte,
        ActionType.add_indicator,
        ActionType.titrate,
    }
    if req.action in hazardous_actions:
        return "goggles" not in session.ppe
    return False


def _check_r2_gloves(session: LabSession, req: ActionRequest) -> bool:
    """R2 GLOVES: Working with chemicals or performing blood draws without gloves (major)."""
    hazardous_actions = {
        ActionType.weigh,
        ActionType.dissolve,
        ActionType.pour,
        ActionType.draw_blood,
        ActionType.fill_burette,
        ActionType.pipette_analyte,
        ActionType.add_indicator,
        ActionType.titrate,
    }
    if req.action in hazardous_actions:
        return "gloves" not in session.ppe
    return False


def _check_r3_lab_coat(session: LabSession, req: ActionRequest) -> bool:
    """R3 LAB_COAT: Performing active bench operations without a lab coat (warning)."""
    bench_actions = {
        ActionType.weigh,
        ActionType.dissolve,
        ActionType.administer_oral,
        ActionType.draw_blood,
        ActionType.fill_burette,
        ActionType.pipette_analyte,
        ActionType.titrate,
    }
    if req.action in bench_actions:
        return "coat" not in session.ppe
    return False


def _check_r4_tare_first(session: LabSession, req: ActionRequest) -> bool:
    """R4 TARE_FIRST: Weighing powder without taring the balance (warning)."""
    if req.action == ActionType.weigh:
        balance = session.apparatus_state.get("digital_balance", {})
        return not balance.get("tared", False)
    return False


def _check_r5_label_samples(session: LabSession, req: ActionRequest) -> bool:
    """R5 LABEL_SAMPLES: Drawing blood or assaying an unlabelled tube, or using an unlabelled/dose-pending dosing cup (major)."""
    if req.action == ActionType.label:
        text = str(req.params.get("text", "")).lower()
        if "dose pending" in text or "pending" in text:
            return True

    if req.action == ActionType.draw_blood:
        target = req.target or "tube_1"
        tube = session.apparatus_state.get(target, {})
        return not tube.get("labeled", False) or "pending" in str(tube.get("label_text", "")).lower()

    if req.action == ActionType.run_assay:
        target = req.target or "tube_1"
        tube = session.apparatus_state.get(target, {})
        return not tube.get("labeled", False) or "pending" in str(tube.get("label_text", "")).lower()

    if req.action == ActionType.administer_oral:
        cup = session.apparatus_state.get("dosing_cup", {})
        if not cup.get("labeled", False):
            return True
        lbl = str(cup.get("label_text", "")).lower()
        if "dose pending" in lbl or "pending" in lbl:
            return True

    return False


def _check_r6_acid_into_water(session: LabSession, req: ActionRequest) -> bool:
    """R6 ACID_INTO_WATER: Adding water to concentrated acid instead of acid into water (major)."""
    if req.action == ActionType.pour:
        source = req.params.get("source", "")
        destination = req.params.get("destination", "")
        # Water into acid is dangerous
        if source in ("water", "water_jug", "wash_bottle", "deionized_water"):
            flask = session.apparatus_state.get(destination, {})
            analyte = flask.get("analyte")
            if analyte in ("hcl_0.1M", "acetic_0.1M"):
                return True
    return False


def _check_r7_burette_overfill(session: LabSession, req: ActionRequest) -> bool:
    """R7 BURETTE_OVERFILL: Filling burette >50 mL or not rinsing before first fill (warning)."""
    if req.action == ActionType.fill_burette:
        burette = session.apparatus_state.get("burette", {})
        if not burette.get("rinsed", False):
            return True
        volume = float(req.params.get("volume_ml", 50.0))
        current = float(burette.get("volume_ml", 0.0))
        if current + volume > 50.0:
            return True
    return False


def _check_r8_dose_limit(session: LabSession, req: ActionRequest) -> bool:
    """R8 DOSE_LIMIT: Administering or weighing above drug's maximum safe single dose (critical)."""
    if req.action in (ActionType.weigh, ActionType.administer_oral):
        dose = float(req.params.get("dose_mg", 0.0))
        if not dose:
            cup = session.apparatus_state.get("dosing_cup", {})
            dose = float(cup.get("contents", {}).get("dose_mg", 0.0))
        # For paracetamol: 1000 mg max safe single dose
        if dose > 1000.0:
            return True
    return False


def _check_r9_waste_bins(session: LabSession, req: ActionRequest) -> bool:
    """R9 WASTE_BINS: Biological/blood items must go to biohazard; chemicals to chemical bin (major)."""
    if req.action == ActionType.dispose_waste:
        item = req.params.get("item", "")
        bin_target = req.target or req.params.get("bin", "")

        is_bio_item = any(k in item for k in ["tube", "blood", "needle", "swab"])
        is_chem_item = any(k in item for k in ["acid", "naoh", "titrant", "analyte", "indicator", "flask_contents"])

        if is_bio_item and bin_target == "chemical_waste_bin":
            return True
        if is_chem_item and bin_target == "biohazard_bin":
            return True

    return False


def _check_r10_clean_finish(session: LabSession, req: ActionRequest) -> bool:
    """R10 CLEAN_FINISH: Submitting report before washing hands or removing PPE (warning)."""
    if req.action == ActionType.submit_report:
        sink = session.apparatus_state.get("sink", {})
        hands_washed = sink.get("hands_washed", False)
        ppe_removed = len(session.ppe) == 0
        return (not hands_washed) or (not ppe_removed)
    return False


# ---------------------------------------------------------------------------
# Space Safety Rule Checkers (S1 - S8)
# ---------------------------------------------------------------------------

def _check_s1_preflight_checklist(session: LabSession, req: ActionRequest) -> bool:
    """S1 PREFLIGHT_CHECKLIST: Launch attempted without running flight computer checklist."""
    if req.action == ActionType.launch:
        fc = session.apparatus_state.get("flight_computer", {})
        return not fc.get("checklist_complete", False)
    return False


def _check_s2_propellant_capacity(session: LabSession, req: ActionRequest) -> bool:
    """S2 PROPELLANT_CAPACITY: Stage fueled beyond tank capacity or <= 0."""
    if req.action == ActionType.fuel_rocket:
        rocket_state = session.apparatus_state.get("rocket", {})
        state_stages = rocket_state.get("stages", [])
        if "stages" in req.params:
            for p in req.params["stages"]:
                fuel_kg = float(p.get("propellant_kg", p.get("fuel_kg", 0.0)))
                stage_idx = int(p.get("stage", 1)) - 1
                if fuel_kg <= 0.0:
                    return True
                if 0 <= stage_idx < len(state_stages):
                    cap = float(state_stages[stage_idx].get("propellant_capacity_kg", 1e9))
                    if fuel_kg > cap:
                        return True
        elif "propellant_kg" in req.params:
            fuel_kg = float(req.params["propellant_kg"])
            stage_idx = int(req.params.get("stage", 1)) - 1
            if fuel_kg <= 0.0:
                return True
            if 0 <= stage_idx < len(state_stages):
                cap = float(state_stages[stage_idx].get("propellant_capacity_kg", 1e9))
                if fuel_kg > cap:
                    return True
    return False


def _check_s3_twr_liftoff(session: LabSession, req: ActionRequest) -> bool:
    """S3 TWR_LIFTOFF: Liftoff attempted with TWR <= 1.0."""
    if req.action == ActionType.launch:
        rocket_state = session.apparatus_state.get("rocket", {})
        twr = rocket_state.get("liftoff_twr")
        if twr is not None and twr <= 1.0:
            return True
    return False


def _check_s4_payload_declared(session: LabSession, req: ActionRequest) -> bool:
    """S4 PAYLOAD_DECLARED: Launch without declared payload or payload exceeds stage max."""
    if req.action == ActionType.launch:
        rocket_state = session.apparatus_state.get("rocket", {})
        if not rocket_state.get("payload_declared", False):
            return True
        payload_kg = float(rocket_state.get("payload_kg", 0.0))
        max_payload = float(rocket_state.get("payload_capacity_kg", 0.0))
        if payload_kg > max_payload or payload_kg <= 0.0:
            return True
    return False


def _check_s5_staging_order(session: LabSession, req: ActionRequest) -> bool:
    """S5 STAGING_ORDER: Ignite upper stage before lower stage burns out."""
    if req.action in (ActionType.burn_transfer, ActionType.circularize):
        rocket_state = session.apparatus_state.get("rocket", {})
        stages = rocket_state.get("stages", [])
        if len(stages) > 1:
            stage_1 = stages[0]
            if stage_1.get("fuel_pct", 0.0) > 5.0 and rocket_state.get("current_stage", 1) == 1:
                return True
    return False


def _check_s6_range_safety(session: LabSession, req: ActionRequest) -> bool:
    """S6 RANGE_SAFETY: Launch without range clearance."""
    if req.action == ActionType.launch:
        rc = session.apparatus_state.get("range_control", {})
        return not rc.get("cleared", False)
    return False


def _check_s7_dv_margin(session: LabSession, req: ActionRequest) -> bool:
    """S7 DV_MARGIN: Mission delta-v margin < 5% (warning / technique penalty)."""
    if req.action == ActionType.launch:
        rocket_state = session.apparatus_state.get("rocket", {})
        avail_dv = float(rocket_state.get("total_delta_v_ms", 0.0))
        req_dv = float(rocket_state.get("required_delta_v_ms", 9300.0))
        if req_dv > 0 and avail_dv < 1.05 * req_dv:
            return True
    return False


def _check_s8_debrief_cleanup(session: LabSession, req: ActionRequest) -> bool:
    """S8 DEBRIEF_CLEANUP: Submit report without debrief."""
    if req.action == ActionType.submit_report:
        return "debrief" not in session.protocol_progress
    return False


# ---------------------------------------------------------------------------
# Registered Safety Rules List
# ---------------------------------------------------------------------------

SAFETY_RULES: list[SafetyRule] = [
    SafetyRule(
        rule_id="R1_GOGGLES",
        title="Eye Protection Missing",
        severity="critical",
        penalty_points=25,
        explanation=(
            "Safety goggles must be worn whenever handling chemicals, drugs, or blood "
            "to prevent permanent corneal caustic burns or ocular pathogen transmission."
        ),
        checker=_check_r1_goggles,
    ),
    SafetyRule(
        rule_id="R2_GLOVES",
        title="Protective Gloves Missing",
        severity="major",
        penalty_points=15,
        explanation=(
            "Protective gloves must be worn when manipulating acids, bases, or patient blood "
            "to prevent chemical contact burns and biohazard contamination."
        ),
        checker=_check_r2_gloves,
    ),
    SafetyRule(
        rule_id="R3_LAB_COAT",
        title="Protective Lab Coat Missing",
        severity="warning",
        penalty_points=10,
        explanation=(
            "A standard buttoned lab coat shields everyday clothing and exposed skin from "
            "accidental chemical droplets, drug powders, and aerosol contamination."
        ),
        checker=_check_r3_lab_coat,
    ),
    SafetyRule(
        rule_id="R4_TARE_FIRST",
        title="Balance Not Tared",
        severity="warning",
        penalty_points=10,
        explanation=(
            "Digital analytical balances must always be zeroed (tared) with the tare dish "
            "prior to weighing active medicinal ingredients to avoid systematic dose errors."
        ),
        checker=_check_r4_tare_first,
    ),
    SafetyRule(
        rule_id="R5_LABEL_SAMPLES",
        title="Unlabelled Specimen or Medication",
        severity="major",
        penalty_points=15,
        explanation=(
            "Venous collection tubes and medication cups must be explicitly labelled before use "
            "to prevent catastrophic specimen misidentification or wrong-patient administration."
        ),
        checker=_check_r5_label_samples,
    ),
    SafetyRule(
        rule_id="R6_ACID_INTO_WATER",
        title="Hazardous Acid Dilution Sequence",
        severity="major",
        penalty_points=20,
        explanation=(
            "Always add acid slowly to water ('AAA'). Adding water directly to concentrated acid "
            "generates sudden localized boiling and violent corrosive acid splattering."
        ),
        checker=_check_r6_acid_into_water,
    ),
    SafetyRule(
        rule_id="R7_BURETTE_OVERFILL",
        title="Burette Conditioning or Capacity Breach",
        severity="warning",
        penalty_points=10,
        explanation=(
            "Burettes must be conditioned with titrant rinse to prevent water dilution error, "
            "and must never be filled above the calibrated 50 mL meniscus limit."
        ),
        checker=_check_r7_burette_overfill,
    ),
    SafetyRule(
        rule_id="R8_DOSE_LIMIT",
        title="Exceeded Maximum Safe Single Dose",
        severity="critical",
        penalty_points=30,
        explanation=(
            "Administering paracetamol above the maximum adult single dose limit (1000 mg) "
            "depletes endogenous glutathione and induces acute hepatic parenchymal necrosis."
        ),
        checker=_check_r8_dose_limit,
    ),
    SafetyRule(
        rule_id="R9_WASTE_BINS",
        title="Hazardous Waste Incompatible Segregation",
        severity="major",
        penalty_points=15,
        explanation=(
            "Biological sharps and blood tubes must be deposited strictly in biohazard containers; "
            "chemical reagents must enter chemical waste to prevent dangerous autoclave explosions."
        ),
        checker=_check_r9_waste_bins,
    ),
    SafetyRule(
        rule_id="R10_CLEAN_FINISH",
        title="Aseptic Handwash / PPE Removal Incomplete",
        severity="warning",
        penalty_points=10,
        explanation=(
            "Always doff PPE and perform thorough hygienic handwashing at the sink before "
            "handling documentation and submitting official laboratory records."
        ),
        checker=_check_r10_clean_finish,
    ),
]


SPACE_RULES: list[SafetyRule] = [
    SafetyRule(
        rule_id="S1_PREFLIGHT_CHECKLIST",
        title="Launch Attempted Without Preflight Checklist",
        severity="critical",
        penalty_points=25,
        explanation=(
            "Flight computer preflight systems diagnostic checklist must be executed and confirmed "
            "before initiating terminal launch countdown and engine ignition sequence."
        ),
        checker=_check_s1_preflight_checklist,
    ),
    SafetyRule(
        rule_id="S2_PROPELLANT_CAPACITY",
        title="Propellant Tank Capacity Exceeded or Empty",
        severity="major",
        penalty_points=20,
        explanation=(
            "Rocket stage propellant tanks must be loaded with positive mass within rated structural "
            "tank capacity limits to prevent catastrophic tank rupture or dry engine ignition."
        ),
        checker=_check_s2_propellant_capacity,
    ),
    SafetyRule(
        rule_id="S3_TWR_LIFTOFF",
        title="Insufficient Thrust-to-Weight Ratio (TWR <= 1.0)",
        severity="critical",
        penalty_points=30,
        explanation=(
            "Liftoff thrust must strictly exceed vehicle liftoff weight (TWR > 1.0). An under-powered "
            "rocket cannot lift off, pinning the vehicle to the pad while exhaust destroys pad infrastructure."
        ),
        checker=_check_s3_twr_liftoff,
    ),
    SafetyRule(
        rule_id="S4_PAYLOAD_DECLARED",
        title="Undeclared or Excessive Payload Mass",
        severity="major",
        penalty_points=15,
        explanation=(
            "Orbital payload mass must be declared and must not exceed the vehicle's structural "
            "payload capacity to preserve mission aerodynamic and mass budget stability."
        ),
        checker=_check_s4_payload_declared,
    ),
    SafetyRule(
        rule_id="S5_STAGING_ORDER",
        title="Premature Upper Stage Ignition / Staging Order Breach",
        severity="critical",
        penalty_points=25,
        explanation=(
            "Lower booster stages must complete their burn before upper stage ignition and interstage "
            "separation. Igniting upper stages prematurely causes plume impingement and vehicle breakup."
        ),
        checker=_check_s5_staging_order,
    ),
    SafetyRule(
        rule_id="S6_RANGE_SAFETY",
        title="Launch Attempted Without Range Clearance",
        severity="major",
        penalty_points=20,
        explanation=(
            "Launch operations require affirmative range clearance from tracking radar and downrange "
            "safety officers to protect airspace, shipping corridors, and populated zones."
        ),
        checker=_check_s6_range_safety,
    ),
    SafetyRule(
        rule_id="S7_DV_MARGIN",
        title="Insufficient Delta-V Margin (<5%)",
        severity="warning",
        penalty_points=10,
        explanation=(
            "Sound mission planning requires at least a 5% delta-v reserve margin above nominal "
            "orbital insertion requirements to absorb atmospheric drag and steering losses."
        ),
        checker=_check_s7_dv_margin,
    ),
    SafetyRule(
        rule_id="S8_DEBRIEF_CLEANUP",
        title="Report Submitted Without Mission Debrief",
        severity="warning",
        penalty_points=10,
        explanation=(
            "Flight telemetry, achieved orbital parameters, and propellant margins must be debriefed "
            "with tracking station before submitting final mission analytical documentation."
        ),
        checker=_check_s8_debrief_cleanup,
    ),
]


# ---------------------------------------------------------------------------
# Dose Response Lab Rules (D1 - D8)
# ---------------------------------------------------------------------------

def _load_drugs_v2_catalog() -> dict[str, Any]:
    from pathlib import Path
    drugs_path = Path(__file__).resolve().parent.parent / "pharma" / "pkpd" / "drugs_v2.json"
    if drugs_path.exists():
        with open(drugs_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _check_d1_max_dose(session: LabSession, req: ActionRequest) -> bool:
    """D1: Dose exceeds adult max single dose for selected drug (from drugs_v2.json max_game_dose_mg)."""
    catalog = _load_drugs_v2_catalog()
    pump = session.apparatus_state.get("infusion_pump", {})
    drug_id = pump.get("drug_id", "paracetamol")
    d_cfg = catalog.get(drug_id, {})
    max_dose = float(d_cfg.get("max_game_dose_mg", 1000.0))

    if req.action == ActionType.set_dose:
        dose = float(req.params.get("dose_mg", 0.0))
        return dose > max_dose
    elif req.action == ActionType.run_simulation:
        dose = float(pump.get("dose_mg", 0.0))
        return dose > max_dose
    return False


def _check_d2_renal_impairment(session: LabSession, req: ActionRequest) -> bool:
    """D2: Unadjusted dose in renal impairment: CrCl < 60 mL/min, drug fe > 0.4, dose > recommended."""
    catalog = _load_drugs_v2_catalog()
    mon = session.apparatus_state.get("patient_monitor", {})
    pump = session.apparatus_state.get("infusion_pump", {})
    drug_id = pump.get("drug_id", "paracetamol")
    d_cfg = catalog.get(drug_id, {})

    crcl = float(mon.get("crcl_ml_min", 100.0))
    fe = float(d_cfg.get("fe", 0.0))
    max_dose = float(d_cfg.get("max_game_dose_mg", 1000.0))
    recommended_renal_dose = max_dose * (crcl / 120.0)

    if crcl < 60.0 and fe > 0.4:
        if req.action == ActionType.set_dose:
            dose = float(req.params.get("dose_mg", 0.0))
            return dose > recommended_renal_dose or not mon.get("renal_check_acknowledged", False)
        elif req.action == ActionType.run_simulation:
            dose = float(pump.get("dose_mg", 0.0))
            return dose > recommended_renal_dose or not mon.get("renal_check_acknowledged", False)
    return False


def _check_d3_route_mismatch(session: LabSession, req: ActionRequest) -> bool:
    """D3: Route mismatch: oral dose given to patient with oral bioavailability F == 0 or not allowed."""
    catalog = _load_drugs_v2_catalog()
    pump = session.apparatus_state.get("infusion_pump", {})
    drug_id = pump.get("drug_id", "paracetamol")
    d_cfg = catalog.get(drug_id, {})
    f_bioav = float(d_cfg.get("f_bioav", 1.0))
    routes_allowed = d_cfg.get("routes_allowed", ["oral", "iv_bolus", "iv_infusion"])

    if req.action == ActionType.set_route:
        route = req.params.get("route") or req.target or "oral"
        if route == "oral" and (f_bioav <= 0.05 or "oral" not in routes_allowed):
            return True
        if route not in routes_allowed:
            return True
    elif req.action == ActionType.run_simulation:
        route = pump.get("route", "oral")
        if route == "oral" and (f_bioav <= 0.05 or "oral" not in routes_allowed):
            return True
        if route not in routes_allowed:
            return True
    return False


def _check_d4_covariate_bounds(session: LabSession, req: ActionRequest) -> bool:
    """D4: Out-of-bounds covariate requested: reject at boundary (age 18-90, weight 40-150, CrCl 15-150)."""
    if req.action == ActionType.set_covariates:
        params = req.params
        wt = params.get("weight_kg")
        age = params.get("age_yr")
        crcl = params.get("crcl_ml_min")
        if wt is not None and (float(wt) < 40.0 or float(wt) > 150.0):
            return True
        if age is not None and (float(age) < 18.0 or float(age) > 90.0):
            return True
        if crcl is not None and (float(crcl) < 15.0 or float(crcl) > 150.0):
            return True
    return False


def _check_d5_nti_sampling(session: LabSession, req: ActionRequest) -> bool:
    """D5: Narrow therapeutic index (NTI) drug with sampling count < 3."""
    if req.action == ActionType.run_simulation:
        catalog = _load_drugs_v2_catalog()
        pump = session.apparatus_state.get("infusion_pump", {})
        drug_id = pump.get("drug_id", "paracetamol")
        d_cfg = catalog.get(drug_id, {})
        c_low = float(d_cfg.get("target_window_low", 1.0))
        c_high = float(d_cfg.get("target_window_high", 2.0))
        is_nti = drug_id in ("theophylline", "gentamicin", "vancomycin", "digoxin") or (c_high / max(0.001, c_low) <= 2.5)

        if is_nti:
            sched = session.apparatus_state.get("sampling_schedule", {})
            times = sched.get("sample_times_h", [])
            return len(times) < 3
    return False


def _check_d6_infusion_rate(session: LabSession, req: ActionRequest) -> bool:
    """D6: Infusion rate exceeds max recommended (infusion duration < 15 min for rate-limited drugs)."""
    if req.action == ActionType.set_regimen:
        dur = req.params.get("infusion_duration_h")
        if dur is not None and float(dur) < 0.25:
            return True
    elif req.action == ActionType.run_simulation:
        pump = session.apparatus_state.get("infusion_pump", {})
        if pump.get("route") == "iv_infusion":
            dur = float(pump.get("infusion_duration_h", 1.0))
            return dur < 0.25
    return False


def _check_d7_window_prediction(session: LabSession, req: ActionRequest) -> bool:
    """D7: Missing target window prediction before running simulation."""
    if req.action == ActionType.run_simulation:
        slate = session.apparatus_state.get("prediction_slate", {})
        return not bool(slate.get("submitted", False))
    return False


def _check_d8_toxic_peak(session: LabSession, req: ActionRequest) -> bool:
    """D8: Toxic peak: simulated Cmax > target_window.c_toxic."""
    if req.action == ActionType.run_simulation:
        pump = session.apparatus_state.get("infusion_pump", {})
        mon = session.apparatus_state.get("patient_monitor", {})
        drug_id = pump.get("drug_id", "paracetamol")
        catalog = _load_drugs_v2_catalog()
        d_cfg = catalog.get(drug_id, {})
        c_high = float(d_cfg.get("target_window_high", 20.0))
        c_toxic = c_high * 1.5
        dose_mg = float(pump.get("dose_mg", 0.0))
        if dose_mg <= 0:
            return False

        try:
            from app.pharma.pkpd.engine import (
                PKPDParams,
                AdultCovariates,
                apply_covariates,
                simulate_pkpd,
                ModelType,
                RouteType,
            )
            route = RouteType(pump.get("route", d_cfg.get("routes_allowed", ["oral"])[0]))
            model_type = ModelType(d_cfg.get("model_type", "one_compartment"))
            base_params = PKPDParams(
                model_type=model_type,
                route=route,
                dose_mg=dose_mg,
                n_doses=int(pump.get("n_doses", 1)),
                interval_h=float(pump.get("interval_h", 8.0)),
                cl=float(d_cfg.get("cl", 10.0)),
                v1=float(d_cfg.get("v1", 40.0)),
                q=float(d_cfg.get("q", 0.0)),
                v2=float(d_cfg.get("v2", 0.0)),
                ka=float(d_cfg.get("ka", 1.5)),
                f_bioav=float(d_cfg.get("f_bioav", 1.0)),
                t_lag=float(d_cfg.get("t_lag", 0.0)),
                infusion_duration_h=float(pump.get("infusion_duration_h", 1.0)),
                fe=float(d_cfg.get("fe", 0.0)),
            )
            cov = AdultCovariates(
                weight_kg=float(mon.get("weight_kg", 70.0)),
                age_yr=float(mon.get("age_yr", 35.0)),
                crcl_ml_min=float(mon.get("crcl_ml_min", 100.0)),
            )
            scaled = apply_covariates(base_params, cov)
            sim_res = simulate_pkpd(scaled, t_end_h=24.0, dt_h=0.1)
            return sim_res.cmax > c_toxic
        except Exception:
            v1 = float(d_cfg.get("v1", 40.0))
            return (dose_mg / max(1.0, v1)) > c_toxic
    return False


DOSE_LAB_RULES: list[SafetyRule] = [
    SafetyRule(
        rule_id="D1",
        title="Dose Exceeds Maximum Safe Single Dose",
        severity="major",
        penalty_points=15,
        explanation="Administered dose exceeds the maximum recommended adult single dose from drug specifications.",
        checker=_check_d1_max_dose,
    ),
    SafetyRule(
        rule_id="D2",
        title="Unadjusted Dose in Renal Impairment",
        severity="critical",
        penalty_points=20,
        explanation="Patients with renal impairment (CrCl < 60 mL/min) receiving renally cleared drugs (fe > 0.4) require dose reduction.",
        checker=_check_d2_renal_impairment,
    ),
    SafetyRule(
        rule_id="D3",
        title="Route Mismatch (Incompatible Bioavailability)",
        severity="major",
        penalty_points=10,
        explanation="Selected administration route is incompatible with drug bioavailability (e.g. oral route for aminoglycosides or glycopeptides).",
        checker=_check_d3_route_mismatch,
    ),
    SafetyRule(
        rule_id="D4",
        title="Out-of-Bounds Adult Covariates Requested",
        severity="warning",
        penalty_points=5,
        explanation="Patient parameters must remain within adult boundary limits (Age 18-90, Weight 40-150 kg, CrCl 15-150 mL/min).",
        checker=_check_d4_covariate_bounds,
    ),
    SafetyRule(
        rule_id="D5",
        title="Inadequate Sampling Count for Narrow Therapeutic Index Drug",
        severity="warning",
        penalty_points=10,
        explanation="Narrow therapeutic index drugs require at least 3 blood sampling observation timepoints to characterize PK curve.",
        checker=_check_d5_nti_sampling,
    ),
    SafetyRule(
        rule_id="D6",
        title="Excessive Infusion Rate / Duration Too Short",
        severity="major",
        penalty_points=15,
        explanation="Intravenous infusions must not be administered in under 15 minutes (< 0.25h) to avoid adverse infusion reactions.",
        checker=_check_d6_infusion_rate,
    ),
    SafetyRule(
        rule_id="D7",
        title="Missing Target Window Prediction",
        severity="warning",
        penalty_points=5,
        explanation="Enter your predicted peak concentration and target window duration before executing simulation.",
        checker=_check_d7_window_prediction,
    ),
    SafetyRule(
        rule_id="D8",
        title="Toxic Peak Concentration Exceeded",
        severity="critical",
        penalty_points=25,
        explanation="Simulated Cmax exceeds the toxic concentration threshold (toxicity risk). Regimen adjustment required.",
        checker=_check_d8_toxic_peak,
    ),
]


def check_safety_rules(session: LabSession, req: ActionRequest) -> list[Violation]:
    """Evaluate active safety rules for the given action and return detected violations."""
    violations: list[Violation] = []
    if session.experiment_id == "launch_bench" or session.experiment_id in (
        "first_orbit", "fuel_limited_orbit", "hohmann_transfer", "twr_abort", "mass_budget_design"
    ):
        active_rules = SPACE_RULES
    elif session.experiment_id == "dose_lab":
        active_rules = DOSE_LAB_RULES
    else:
        active_rules = SAFETY_RULES
    for rule in active_rules:
        v = rule.check(session, req)
        if v:
            violations.append(v)
    return violations
