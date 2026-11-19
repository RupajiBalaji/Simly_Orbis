"""
backend/app/pharma/pkpd/trial_v2.py
Virtual Clinical Population Trial Engine v2.

Upgraded multi-compartment population simulation built on the core pkpd engine
(supporting 1- and 2-compartment models, IV bolus, IV infusion, and oral routes).
Simulates virtual patient cohorts (1 to 1000 adults) with log-normal physiological
variability and adult-only covariate distributions (Weight 40-150 kg, Age 18-90 yr, CrCl 15-150 mL/min).

Acceptance criteria:
- Cohort of one equals the single-patient engine result exactly.
- Seeded reruns are 100% deterministic and identical.
- 1,000-patient runtime is recorded.
- Labelled: 'virtual population, not a clinical trial'.
- Insight sentence generated deterministically by code (not AI).
- Deterministic CSV export.

Educational simulation only. Not medical advice. Not clinical evidence.
"""

from __future__ import annotations

import csv
import io
import json
import math
import time
from pathlib import Path
from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, Field

from app.pharma.pkpd.engine import (
    AdultCovariates,
    ModelType,
    PKPDParams,
    PKPDResult,
    RouteType,
    apply_covariates,
    simulate_pkpd,
)

DRUGS_V2_PATH = Path(__file__).resolve().parent / "drugs_v2.json"


def load_drugs_v2() -> dict[str, Any]:
    """Load the frozen v2 drug library."""
    with open(DRUGS_V2_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


class TrialRegimen(BaseModel):
    """Regimen specifications for virtual trial cohort."""

    drug_id: str = Field(default="paracetamol", description="Drug identifier in drugs_v2 library")
    route: RouteType = Field(default=RouteType.oral, description="Administration route (oral, iv_bolus, iv_infusion)")
    dose_mg: float = Field(default=500.0, ge=0.1, le=5000.0, description="Dose in mg")
    n_doses: int = Field(default=1, ge=1, le=12, description="Number of doses administered")
    interval_h: float = Field(default=6.0, ge=1.0, le=48.0, description="Dosing interval in hours")
    infusion_duration_h: float = Field(default=1.0, ge=0.1, le=24.0, description="Infusion duration (if iv_infusion)")


class VirtualCohortConfig(BaseModel):
    """Virtual cohort generation parameters."""

    n_patients: int = Field(default=500, ge=1, le=1000, description="Number of virtual patients (1 to 1000)")
    seed: int = Field(default=42, description="Random seed for reproducible cohort sampling")
    zero_variability: bool = Field(default=False, description="Disable random variability (forces reference adult)")


class PatientRecord(BaseModel):
    """Individual virtual patient simulation outcome."""

    patient_id: int
    weight_kg: float
    age_yr: float
    crcl_ml_min: float
    cmax: float
    auc: float
    t_max_h: float
    c_trough: float
    status: Literal["target", "below", "above"]
    color: str
    icon: str


class DistributionStats(BaseModel):
    """Statistical summary of a population distribution."""

    min: float
    p5: float
    p25: float
    median: float
    mean: float
    p75: float
    p95: float
    max: float
    std: float


class TrialV2Summary(BaseModel):
    """Summary metrics of virtual population simulation."""

    n_patients: int
    seed: int
    drug_id: str
    drug_name: str
    target_window_low: float
    target_window_high: float
    cmax_dist: DistributionStats
    auc_dist: DistributionStats
    pct_target: float
    pct_below: float
    pct_above: float
    timing_ms: float
    insight: str
    label: str = "virtual population, not a clinical trial"
    disclaimer: str = (
        "Educational simulation only. Not medical advice. Not clinical evidence. "
        "Virtual cohort generated with synthetic log-normal physiological variability."
    )


class TrialV2Result(BaseModel):
    """Complete virtual trial v2 response structure."""

    summary: TrialV2Summary
    patients: list[PatientRecord]
    time_series_representative: dict[str, list[float]]


def compute_distribution_stats(arr: np.ndarray) -> DistributionStats:
    """Compute standard statistical quantiles and moments for an array."""
    if len(arr) == 0:
        return DistributionStats(
            min=0.0, p5=0.0, p25=0.0, median=0.0, mean=0.0, p75=0.0, p95=0.0, max=0.0, std=0.0
        )
    return DistributionStats(
        min=round(float(np.min(arr)), 4),
        p5=round(float(np.percentile(arr, 5)), 4),
        p25=round(float(np.percentile(arr, 25)), 4),
        median=round(float(np.median(arr)), 4),
        mean=round(float(np.mean(arr)), 4),
        p75=round(float(np.percentile(arr, 75)), 4),
        p95=round(float(np.percentile(arr, 95)), 4),
        max=round(float(np.max(arr)), 4),
        std=round(float(np.std(arr)), 4),
    )


def generate_trial_insight(
    drug_name: str,
    dose_mg: float,
    interval_h: float,
    n_doses: int,
    pct_target: float,
    pct_below: float,
    pct_above: float,
    target_low: float,
    target_high: float,
) -> str:
    """
    Generate deterministic, code-written analytical insight statement.
    Strictly generated by program logic, never invented by AI (Rule R2).
    """
    regimen_desc = f"{dose_mg:.0f} mg" if n_doses == 1 else f"{dose_mg:.0f} mg q{interval_h:.0f}h x{n_doses}"

    if pct_target >= 80.0:
        assessment = "high therapeutic target attainment"
    elif pct_target >= 50.0:
        assessment = "moderate therapeutic coverage with noticeable variability"
    else:
        assessment = "suboptimal target coverage requiring dosage adjustment"

    details = []
    if pct_below > 10.0:
        details.append(f"{pct_below:.1f}% sub-therapeutic (<{target_low:.2f} mg/L)")
    if pct_above > 5.0:
        details.append(f"{pct_above:.1f}% exceeding upper limit (>{target_high:.2f} mg/L)")

    details_str = f" ({', '.join(details)})" if details else ""

    return (
        f"{drug_name} {regimen_desc} achieved {pct_target:.1f}% within the target window "
        f"[{target_low:.2f}–{target_high:.2f} mg/L], representing {assessment}{details_str}. "
        f"Population simulation based on log-normal adult physiological distributions."
    )


def build_base_pkpd_params(regimen: TrialRegimen, drug_cfg: dict[str, Any]) -> PKPDParams:
    """Construct baseline reference PKPDParams from drug catalog and regimen."""
    model_type = ModelType(drug_cfg.get("model_type", "one_compartment"))
    return PKPDParams(
        model_type=model_type,
        route=regimen.route,
        dose_mg=regimen.dose_mg,
        n_doses=regimen.n_doses,
        interval_h=regimen.interval_h,
        cl=float(drug_cfg["cl"]),
        v1=float(drug_cfg["v1"]),
        q=float(drug_cfg.get("q", 0.0)),
        v2=float(drug_cfg.get("v2", 0.0)),
        ka=float(drug_cfg.get("ka", 1.5)),
        f_bioav=float(drug_cfg.get("f_bioav", 1.0)),
        t_lag=float(drug_cfg.get("t_lag", 0.0)),
        infusion_duration_h=regimen.infusion_duration_h,
        fe=float(drug_cfg.get("fe", 0.0)),
        pd_enabled=False,
        target_window_low=float(drug_cfg.get("target_window_low", 5.0)),
        target_window_high=float(drug_cfg.get("target_window_high", 20.0)),
    )


def simulate_trial_v2(
    regimen: TrialRegimen,
    cohort_cfg: VirtualCohortConfig,
) -> TrialV2Result:
    """
    Execute Virtual Trial v2 population simulation.

    Guarantees:
    - n_patients == 1 with zero_variability or default single-patient returns
      EXACT numerical results of simulate_pkpd(base_params).
    - Seeded runs are identical across runs.
    - Duration is measured and reported.
    """
    start_time = time.perf_counter()
    drugs = load_drugs_v2()
    drug_cfg = drugs.get(regimen.drug_id)
    if not drug_cfg:
        drug_cfg = drugs["paracetamol"]

    drug_name = drug_cfg.get("name", regimen.drug_id)
    target_low = float(drug_cfg.get("target_window_low", 10.0))
    target_high = float(drug_cfg.get("target_window_high", 20.0))

    base_params = build_base_pkpd_params(regimen, drug_cfg)
    n = cohort_cfg.n_patients
    seed = cohort_cfg.seed

    patients: list[PatientRecord] = []
    cmax_vals = np.zeros(n, dtype=np.float64)
    auc_vals = np.zeros(n, dtype=np.float64)

    # Special case: single patient cohort (n=1) or zero variability
    if n == 1 or cohort_cfg.zero_variability:
        # Evaluate reference adult single-patient directly using the pkpd engine
        single_res = simulate_pkpd(base_params)
        cmax_single = single_res.cmax
        auc_single = single_res.auc_analytic
        tmax_single = single_res.tmax
        trough_single = single_res.concentrations[-1] if single_res.concentrations else 0.0

        for i in range(n):
            status: Literal["target", "below", "above"]
            if cmax_single < target_low:
                status = "below"
                color = "#3b82f6"
                icon = "arrow-down"
            elif cmax_single > target_high:
                status = "above"
                color = "#ef4444"
                icon = "warning"
            else:
                status = "target"
                color = "#10b981"
                icon = "shield"

            rec = PatientRecord(
                patient_id=i + 1,
                weight_kg=70.0,
                age_yr=35.0,
                crcl_ml_min=100.0,
                cmax=round(cmax_single, 4),
                auc=round(auc_single, 4),
                t_max_h=round(tmax_single, 3),
                c_trough=round(trough_single, 4),
                status=status,
                color=color,
                icon=icon,
            )
            patients.append(rec)
            cmax_vals[i] = cmax_single
            auc_vals[i] = auc_single

        rep_series = {
            "times": single_res.times,
            "concentrations": single_res.concentrations,
        }
    else:
        rng = np.random.default_rng(seed)

        # 1. Weight: log-normal median 70.0 kg, CV 18% -> bounded [40.0, 150.0]
        cv_w = 0.18
        sigma_w = math.sqrt(math.log(1.0 + cv_w * cv_w))
        weights = np.clip(rng.lognormal(math.log(70.0), sigma_w, n), 40.0, 150.0)

        # 2. Age: truncated normal mean 45.0, std 15.0 -> bounded [18.0, 90.0]
        ages = np.clip(rng.normal(45.0, 15.0, n), 18.0, 90.0)

        # 3. CrCl: log-normal median 100.0 mL/min, CV 25% -> bounded [15.0, 150.0]
        cv_crcl = 0.25
        sigma_crcl = math.sqrt(math.log(1.0 + cv_crcl * cv_crcl))
        crcls = np.clip(rng.lognormal(math.log(100.0), sigma_crcl, n), 15.0, 150.0)

        # 4. Inter-individual variability (IIV) on CL, V, and Ka
        cv_cl = 0.30
        sigma_cl = math.sqrt(math.log(1.0 + cv_cl * cv_cl))
        cl_mults = rng.lognormal(0.0, sigma_cl, n)

        cv_v = 0.20
        sigma_v = math.sqrt(math.log(1.0 + cv_v * cv_v))
        v_mults = rng.lognormal(0.0, sigma_v, n)

        cv_ka = 0.25
        sigma_ka = math.sqrt(math.log(1.0 + cv_ka * cv_ka))
        ka_mults = rng.lognormal(0.0, sigma_ka, n)

        rep_res: PKPDResult | None = None

        for i in range(n):
            w_i = float(weights[i])
            a_i = float(ages[i])
            crcl_i = float(crcls[i])

            cov = AdultCovariates(weight_kg=w_i, age_yr=a_i, crcl_ml_min=crcl_i)
            scaled = apply_covariates(base_params, cov)

            # Apply IIV
            scaled.cl = max(0.05, scaled.cl * float(cl_mults[i]))
            scaled.v1 = max(0.5, scaled.v1 * float(v_mults[i]))
            if scaled.model_type == ModelType.two_compartment:
                scaled.v2 = max(0.5, scaled.v2 * float(v_mults[i]))
                scaled.q = max(0.05, scaled.q * float(cl_mults[i]))
            if scaled.route == RouteType.oral and scaled.ka > 0:
                scaled.ka = max(0.05, scaled.ka * float(ka_mults[i]))

            res = simulate_pkpd(scaled)
            if i == 0:
                rep_res = res

            cmax_i = res.cmax
            auc_i = res.auc_analytic
            cmax_vals[i] = cmax_i
            auc_vals[i] = auc_i
            trough_i = res.concentrations[-1] if res.concentrations else 0.0

            status: Literal["target", "below", "above"]
            if cmax_i < target_low:
                status = "below"
                color = "#3b82f6"
                icon = "arrow-down"
            elif cmax_i > target_high:
                status = "above"
                color = "#ef4444"
                icon = "warning"
            else:
                status = "target"
                color = "#10b981"
                icon = "shield"

            patients.append(
                PatientRecord(
                    patient_id=i + 1,
                    weight_kg=round(w_i, 1),
                    age_yr=round(a_i, 1),
                    crcl_ml_min=round(crcl_i, 1),
                    cmax=round(cmax_i, 4),
                    auc=round(auc_i, 4),
                    t_max_h=round(res.tmax, 3),
                    c_trough=round(trough_i, 4),
                    status=status,
                    color=color,
                    icon=icon,
                )
            )

        rep_series = {
            "times": rep_res.times if rep_res else [],
            "concentrations": rep_res.concentrations if rep_res else [],
        }

    duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

    count_target = int(np.sum((cmax_vals >= target_low) & (cmax_vals <= target_high)))
    count_below = int(np.sum(cmax_vals < target_low))
    count_above = int(np.sum(cmax_vals > target_high))

    pct_target = round((count_target / n) * 100.0, 2)
    pct_below = round((count_below / n) * 100.0, 2)
    pct_above = round((count_above / n) * 100.0, 2)

    insight = generate_trial_insight(
        drug_name=drug_name,
        dose_mg=regimen.dose_mg,
        interval_h=regimen.interval_h,
        n_doses=regimen.n_doses,
        pct_target=pct_target,
        pct_below=pct_below,
        pct_above=pct_above,
        target_low=target_low,
        target_high=target_high,
    )

    summary = TrialV2Summary(
        n_patients=n,
        seed=seed,
        drug_id=regimen.drug_id,
        drug_name=drug_name,
        target_window_low=target_low,
        target_window_high=target_high,
        cmax_dist=compute_distribution_stats(cmax_vals),
        auc_dist=compute_distribution_stats(auc_vals),
        pct_target=pct_target,
        pct_below=pct_below,
        pct_above=pct_above,
        timing_ms=duration_ms,
        insight=insight,
    )

    return TrialV2Result(
        summary=summary,
        patients=patients,
        time_series_representative=rep_series,
    )


def compare_trials_v2(
    regimen_a: TrialRegimen,
    regimen_b: TrialRegimen,
    cohort_cfg: VirtualCohortConfig,
) -> dict[str, Any]:
    """
    Simulate and compare two regimens side-by-side using the same virtual population.
    """
    res_a = simulate_trial_v2(regimen_a, cohort_cfg)
    res_b = simulate_trial_v2(regimen_b, cohort_cfg)

    diff_target = round(res_a.summary.pct_target - res_b.summary.pct_target, 2)
    diff_toxic = round(res_a.summary.pct_above - res_b.summary.pct_above, 2)
    diff_cmax = round(res_a.summary.cmax_dist.median - res_b.summary.cmax_dist.median, 3)

    if diff_toxic > 2.0:
        verdict = f"Regimen A achieves {diff_target:+.1f}% target coverage but increases above-limit risk by {diff_toxic:+.1f}%."
    elif diff_target > 0.0:
        verdict = f"Regimen A improves population target coverage by {diff_target:+.1f}% without excessive elevated concentrations."
    else:
        verdict = f"Regimen B maintains equal or better target attainment (Δ target: {diff_target:+.1f}%)."

    return {
        "regimen_a": res_a.model_dump(),
        "regimen_b": res_b.model_dump(),
        "comparison": {
            "diff_pct_target": diff_target,
            "diff_pct_above": diff_toxic,
            "diff_cmax_median": diff_cmax,
            "verdict": verdict,
            "label": "virtual population, not a clinical trial",
        },
    }


def generate_trial_v2_csv(result: TrialV2Result) -> str:
    """Export virtual trial population outcomes to standard CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "patient_id",
        "weight_kg",
        "age_yr",
        "crcl_ml_min",
        "cmax_mg_l",
        "auc_mg_h_l",
        "t_max_h",
        "c_trough_mg_l",
        "status",
    ])
    for p in result.patients:
        writer.writerow([
            p.patient_id,
            p.weight_kg,
            p.age_yr,
            p.crcl_ml_min,
            p.cmax,
            p.auc,
            p.t_max_h,
            p.c_trough,
            p.status,
        ])
    return output.getvalue()
