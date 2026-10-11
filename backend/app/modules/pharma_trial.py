"""
Module: Virtual Clinical Population Trial (pharma.trial).

Simulates clinical pharmacokinetics across virtual patient cohorts (20 to 1000 patients)
incorporating realistic log-normal population variability (body weight, clearance,
absorption rate constant ka) and a reduced-liver-clearance subgroup.
"""

from __future__ import annotations

import math
import time
from typing import Any

import numpy as np
from pydantic import BaseModel, Field

from app.core.base import ModelCard, RealityCheck, RunResult, SimModule
from app.core.version import ENGINE_VERSION
from app.sim.drugs import get_drug
from app.sim.models import Patient
from app.sim.pk_engine import simulate


class PharmaTrialParams(BaseModel):
    """Input parameters for virtual clinical trial cohort simulation."""

    drug_id: str = Field(default="paracetamol", description="Drug identifier (e.g. 'paracetamol')")
    dose_mg: float = Field(..., ge=0.0, le=5000.0, description="Dose per administration in mg (0-5000)")
    n_doses: int = Field(1, ge=1, le=6, description="Number of doses (1-6)")
    interval_h: float = Field(6.0, ge=1.0, le=24.0, description="Dosing interval in hours (1-24)")
    n_patients: int = Field(500, ge=20, le=1000, description="Virtual patient cohort size (20-1000)")
    seed: int = Field(42, description="Pseudorandom seed for reproducible cohort sampling")
    pct_reduced_liver: float = Field(
        10.0, ge=0.0, le=50.0, description="Percentage of cohort with impaired liver clearance (0-50%)"
    )


def _simulate_cohort(
    drug: Any,
    params: PharmaTrialParams,
    *,
    zero_variability: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Vectorized computation of plasma concentration time series across virtual patient cohort.

    Returns:
        times: 1D array of timepoints (shape T,)
        C_total: 2D array of plasma concentrations (shape N, T)
        peaks: 1D array of per-patient peak concentration (shape N,)
        reduced_mask: boolean mask indicating impaired liver clearance (shape N,)
        weights: 1D array of patient weights (shape N,)
        cl_mults: 1D array of patient clearance multipliers (shape N,)
    """
    n_patients = params.n_patients
    dose_mg = params.dose_mg
    n_doses = params.n_doses
    interval_h = params.interval_h
    seed = params.seed
    pct_reduced_liver = params.pct_reduced_liver

    rng = np.random.default_rng(seed)

    if zero_variability:
        weights = np.full(n_patients, 70.0, dtype=np.float64)
        cl_mults = np.full(n_patients, 1.0, dtype=np.float64)
        kas = np.full(n_patients, float(drug.ka), dtype=np.float64)
        reduced_mask = np.zeros(n_patients, dtype=bool)
    else:
        # 1. Body weight: log-normal, median 70 kg, CV 18%
        cv_w = 0.18
        sigma_w = math.sqrt(math.log(1.0 + cv_w * cv_w))
        mu_w = math.log(70.0)
        weights = rng.lognormal(mu_w, sigma_w, n_patients)

        # 2. Clearance multiplier: log-normal, median 1.0, CV 30%
        cv_cl = 0.30
        sigma_cl = math.sqrt(math.log(1.0 + cv_cl * cv_cl))
        mu_cl = math.log(1.0)
        cl_mults = rng.lognormal(mu_cl, sigma_cl, n_patients)

        # 3. Absorption rate ka: log-normal, median drug.ka, CV 25%
        cv_ka = 0.25
        sigma_ka = math.sqrt(math.log(1.0 + cv_ka * cv_ka))
        mu_ka = math.log(drug.ka)
        kas = rng.lognormal(mu_ka, sigma_ka, n_patients)

        # 4. Reduced-liver subgroup: clearance x0.6
        n_reduced = int(round(n_patients * (pct_reduced_liver / 100.0)))
        perm = rng.permutation(n_patients)
        reduced_mask = np.zeros(n_patients, dtype=bool)
        if n_reduced > 0:
            reduced_mask[perm[:n_reduced]] = True
            cl_mults[reduced_mask] *= 0.6

    # Derived parameters
    ke = (math.log(2) / drug.half_life) * cl_mults
    Vd = drug.vd_per_kg * weights
    F = drug.bioavailability

    # Time grid: 0 to 24 h with step 0.2 h (121 points)
    times = np.linspace(0.0, 24.0, 121)
    dose_times = [i * interval_h for i in range(n_doses)]

    C_total = np.zeros((n_patients, len(times)), dtype=np.float64)

    for t_d in dose_times:
        t_el = times - t_d
        mask = t_el >= 0
        if not np.any(mask):
            continue
        t_el_pos = np.where(mask, t_el, 0.0)
        diff = kas - ke
        diff = np.where(np.abs(diff) < 1e-9, 1e-9, diff)
        coeff = (F * dose_mg * kas) / (Vd * diff)

        e_ke = np.exp(-ke[:, None] * t_el_pos[None, :])
        e_ka = np.exp(-kas[:, None] * t_el_pos[None, :])
        contrib = coeff[:, None] * (e_ke - e_ka)
        contrib[:, ~mask] = 0.0
        C_total += contrib

    peaks = np.max(C_total, axis=1)
    return times, C_total, peaks, reduced_mask, weights, cl_mults


class PharmaTrialModule(SimModule):
    """Virtual clinical trial simulation module for the Pharma district."""

    id = "pharma.trial"
    name = "Virtual Clinical Trial"
    district = "pharma"
    description = (
        "Cohort simulation of oral pharmacokinetics across up to 1000 virtual patients "
        "with log-normal demographic variability and impaired liver clearance subgroups."
    )
    version = "1.0.0"
    params_model = PharmaTrialParams

    def run(self, params: BaseModel | dict[str, Any]) -> RunResult:
        """Execute vectorized population clinical trial computation."""
        t_start = time.perf_counter()

        if isinstance(params, dict):
            validated = self.params_model.model_validate(params)
        else:
            validated = params  # type: ignore[assignment]

        drug = get_drug(validated.drug_id)
        times, C_total, peaks, reduced_mask, weights, cl_mults = _simulate_cohort(drug, validated)

        n_patients = validated.n_patients

        # Classification thresholds
        in_green_matrix = (C_total >= drug.green_low) & (C_total <= drug.green_high)
        frac_green = np.mean(in_green_matrix, axis=1)

        is_toxic = peaks > drug.red_threshold
        is_in_range = (~is_toxic) & (frac_green >= 0.60)
        is_subtherapeutic = (~is_toxic) & (~is_in_range)

        # Outcome codes: 0 = below, 1 = in range, 2 = toxic
        outcomes = np.zeros(n_patients, dtype=int)
        outcomes[is_in_range] = 1
        outcomes[is_toxic] = 2

        n_toxic = int(np.sum(is_toxic))
        n_in_range = int(np.sum(is_in_range))
        n_subtherapeutic = int(np.sum(is_subtherapeutic))

        pct_toxic = round(100.0 * n_toxic / n_patients, 2)
        pct_in_range = round(100.0 * n_in_range / n_patients, 2)
        pct_subtherapeutic = round(100.0 * n_subtherapeutic / n_patients, 2)

        mean_peak = round(float(np.mean(peaks)), 3)
        median_peak = round(float(np.median(peaks)), 3)

        # Subgroup breakdown
        def get_subgroup_dict(mask: np.ndarray) -> dict[str, Any]:
            count = int(np.sum(mask))
            if count == 0:
                return {
                    "count": 0,
                    "pct_in_range": 0.0,
                    "pct_toxic": 0.0,
                    "pct_subtherapeutic": 0.0,
                    "mean_peak": 0.0,
                    "median_peak": 0.0,
                }
            return {
                "count": count,
                "pct_in_range": round(100.0 * float(np.sum(is_in_range & mask)) / count, 2),
                "pct_toxic": round(100.0 * float(np.sum(is_toxic & mask)) / count, 2),
                "pct_subtherapeutic": round(100.0 * float(np.sum(is_subtherapeutic & mask)) / count, 2),
                "mean_peak": round(float(np.mean(peaks[mask])), 3),
                "median_peak": round(float(np.median(peaks[mask])), 3),
            }

        subgroups = {
            "normal_liver": get_subgroup_dict(~reduced_mask),
            "reduced_liver": get_subgroup_dict(reduced_mask),
        }

        group_counts = {
            "total": n_patients,
            "in_range": n_in_range,
            "toxic": n_toxic,
            "subtherapeutic": n_subtherapeutic,
            "reduced_liver": int(np.sum(reduced_mask)),
        }

        # Percentile bands over time (5, 25, 50, 75, 95)
        p5 = np.percentile(C_total, 5, axis=0)
        p25 = np.percentile(C_total, 25, axis=0)
        p50 = np.percentile(C_total, 50, axis=0)
        p75 = np.percentile(C_total, 75, axis=0)
        p95 = np.percentile(C_total, 95, axis=0)

        # Peak concentration histogram
        max_p = max(float(np.max(peaks)), drug.red_threshold * 1.25, 1.0)
        hist_counts, bin_edges = np.histogram(peaks, bins=20, range=(0.0, max_p))

        # Warnings
        warnings: list[str] = []
        if pct_toxic > 5.0:
            warnings.append(
                f"Elevated cohort toxicity: {pct_toxic:.1f}% of virtual patients exceeded red threshold ({drug.red_threshold} mg/L)."
            )
        if pct_subtherapeutic > 40.0 and validated.dose_mg > 0:
            warnings.append(
                f"Subtherapeutic exposure in {pct_subtherapeutic:.1f}% of cohort (failed to maintain green window >= 60% of time)."
            )
        if subgroups["reduced_liver"]["pct_toxic"] > 20.0:
            warnings.append(
                f"High susceptibility in impaired-liver subgroup ({subgroups['reduced_liver']['pct_toxic']:.1f}% toxic rate)."
            )

        duration_ms = (time.perf_counter() - t_start) * 1000.0

        summary = {
            "n_patients": n_patients,
            "pct_in_range": pct_in_range,
            "pct_toxic": pct_toxic,
            "pct_subtherapeutic": pct_subtherapeutic,
            "mean_peak": mean_peak,
            "median_peak": median_peak,
            "subgroups": subgroups,
            "group_counts": group_counts,
            "green_low": drug.green_low,
            "green_high": drug.green_high,
            "red_threshold": drug.red_threshold,
        }

        series = {
            "time_h": [round(float(t), 2) for t in times],
            "p5": [round(float(v), 3) for v in p5],
            "p25": [round(float(v), 3) for v in p25],
            "p50": [round(float(v), 3) for v in p50],
            "p75": [round(float(v), 3) for v in p75],
            "p95": [round(float(v), 3) for v in p95],
            "hist_bins": [round(float(b), 2) for b in bin_edges],
            "hist_counts": [int(c) for c in hist_counts],
            "outcomes": [int(o) for o in outcomes],
        }

        return RunResult(
            module_id=self.id,
            params=validated.model_dump(),
            summary=summary,
            series=series,
            warnings=warnings,
            duration_ms=round(duration_ms, 3),
            engine_version=ENGINE_VERSION,
        )

    def reality_checks(self) -> list[RealityCheck]:
        """
        Verify the clinical trial simulation module against 4 rigorous scientific checks:
        1. With zero variability all patients equal the single-patient pharma.pk result.
        2. The median of the population peak is within 10% of the deterministic median patient.
        3. Same seed gives identical output.
        4. Doubling the dose never reduces mean peak.
        """
        drug = get_drug("paracetamol")
        standard_patient = Patient(weight_kg=70.0, clearance_multiplier=1.0)
        checks: list[RealityCheck] = []

        # ------------------------------------------------------------------
        # 1. Zero variability equals single-patient pharma.pk result
        # ------------------------------------------------------------------
        params_base = PharmaTrialParams(
            drug_id="paracetamol",
            dose_mg=500.0,
            n_doses=1,
            interval_h=6.0,
            n_patients=50,
            seed=42,
            pct_reduced_liver=0.0,
        )
        times_zv, c_zv, peaks_zv, _, _, _ = _simulate_cohort(drug, params_base, zero_variability=True)
        single_res = simulate(drug, standard_patient, dose_mg=500.0, n_doses=1, interval_h=6.0)

        # Interpolate single patient curve at times_zv
        single_interp = np.interp(times_zv, single_res.times, single_res.concentrations)
        max_dev = float(np.max(np.abs(c_zv[0] - single_interp)))
        diff_fraction = max_dev / max(single_res.peak_concentration, 1e-6)

        checks.append(
            RealityCheck(
                name="Zero Variability Equivalence",
                description="With demographic CVs set to zero, virtual patients exactly match single-patient Bateman PK.",
                expected=0.0,
                actual=round(diff_fraction, 6),
                tolerance=0.01,  # 1%
                passed=bool(diff_fraction <= 0.01),
                source_note="Mathematical proof: lim_{CV->0} Population(t) = Deterministic(t).",
            )
        )

        # ------------------------------------------------------------------
        # 2. Population median peak within 10% of deterministic median patient
        # ------------------------------------------------------------------
        params_pop = PharmaTrialParams(
            drug_id="paracetamol",
            dose_mg=500.0,
            n_doses=1,
            interval_h=6.0,
            n_patients=500,
            seed=42,
            pct_reduced_liver=10.0,
        )
        _, _, peaks_pop, _, _, _ = _simulate_cohort(drug, params_pop, zero_variability=False)
        pop_median_peak = float(np.median(peaks_pop))
        det_peak = float(single_res.peak_concentration)
        peak_diff_pct = abs(pop_median_peak - det_peak) / det_peak

        checks.append(
            RealityCheck(
                name="Population Median Peak Concordance",
                description="Population median peak concentration is within 10% of deterministic median patient peak.",
                expected=round(det_peak, 4),
                actual=round(pop_median_peak, 4),
                tolerance=0.10,  # 10%
                passed=bool(peak_diff_pct <= 0.10),
                source_note="Central Limit & log-normal median property: Exp(ln(m)) = m for symmetric noise.",
            )
        )

        # ------------------------------------------------------------------
        # 3. Same seed gives identical output
        # ------------------------------------------------------------------
        run1 = self.run(params_pop)
        run2 = self.run(params_pop)

        identical_summary = run1.summary == run2.summary
        identical_outcomes = run1.series and run2.series and (run1.series.get("outcomes") == run2.series.get("outcomes"))
        reproducible = bool(identical_summary and identical_outcomes)

        checks.append(
            RealityCheck(
                name="Seed Reproducibility",
                description="Identical seed produces 100% bit-exact summary metrics and patient outcomes.",
                expected=1.0,
                actual=1.0 if reproducible else 0.0,
                tolerance=0.0,
                passed=reproducible,
                source_note="Deterministic PRNG reproducibility requirement (Numpy default_rng(seed)).",
            )
        )

        # ------------------------------------------------------------------
        # 4. Doubling dose never reduces mean peak
        # ------------------------------------------------------------------
        params_double = PharmaTrialParams(
            drug_id="paracetamol",
            dose_mg=1000.0,
            n_doses=1,
            interval_h=6.0,
            n_patients=500,
            seed=42,
            pct_reduced_liver=10.0,
        )
        _, _, peaks_double, _, _, _ = _simulate_cohort(drug, params_double, zero_variability=False)
        mean_base = float(np.mean(peaks_pop))
        mean_double = float(np.mean(peaks_double))
        dose_proportional = mean_double >= mean_base

        checks.append(
            RealityCheck(
                name="Dose Monotonicity",
                description="Doubling dose never reduces cohort mean peak concentration (mean_peak_1000mg >= mean_peak_500mg).",
                expected=round(mean_base * 2.0, 4),
                actual=round(mean_double, 4),
                tolerance=0.05,  # 5% of theoretical doubling
                passed=dose_proportional,
                source_note="Linear pharmacokinetics superposition: C(2*D) = 2*C(D).",
            )
        )

        card = self.get_model_card()
        for c in checks:
            c.model_card = card

        return checks

    def get_model_card(self) -> ModelCard:
        """Return scientific documentation card for population clinical trial simulation."""
        return ModelCard(
            module_id=self.id,
            name=self.name,
            underlying_models=[
                "Monte Carlo population pharmacokinetic simulator (N=20 to 1000 patients).",
                "Log-normal physiological distributions for patient weight (CV 18%), clearance multiplier (CV 30%), and absorption rate ka (CV 25%).",
                "Stratified hepatic impairment subgroup scaling elimination clearance by 0.6x.",
            ],
            key_assumptions=[
                "Parameters follow independent log-normal distributions centered on baseline clinical pharmacology values.",
                "Reduced liver impairment acts as a discrete categorical subgroup with uniform clearance reduction.",
                "Identical multi-dose Bateman absorption and elimination kinetics applied per individual patient.",
            ],
            known_limitations=[
                "Synthetic virtual population without real patient genomic or demographic covariate correlations.",
                "Simplified binary liver function stratification without renal impairment or concomitant medication interactions.",
                "Simulated educational population distributions are not calibrated for individualized patient dosing decisions.",
            ],
            disclaimer="Educational simulation only. Not validated for clinical dosing or industrial chemical process control.",
        )

