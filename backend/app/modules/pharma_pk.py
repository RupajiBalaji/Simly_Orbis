"""
Module #1: Oral Pharmacokinetics (Pharma District).

Wraps the existing one-compartment Bateman pk_engine into the unified
SimModule architecture.
"""

from __future__ import annotations

import math
import time
from typing import Any

from pydantic import BaseModel, Field

from app.core.base import ModelCard, RealityCheck, RunResult, SimModule
from app.core.version import ENGINE_VERSION
from app.sim.drugs import get_drug
from app.sim.models import Patient
from app.sim.pk_engine import simulate


class PharmaPKParams(BaseModel):
    """Input parameters for oral pharmacokinetics simulation."""

    drug_id: str = Field(..., description="Drug identifier (e.g. 'paracetamol')")
    weight_kg: float = Field(..., ge=10.0, le=200.0, description="Patient weight in kg (10-200)")
    clearance_multiplier: float = Field(
        1.0, ge=0.2, le=1.5, description="Multiplier on elimination rate ke (0.2-1.5)"
    )
    dose_mg: float = Field(..., ge=0.0, le=5000.0, description="Dose per administration in mg (0-5000)")
    n_doses: int = Field(1, ge=1, le=6, description="Number of doses (1-6)")
    interval_h: float = Field(
        6.0, ge=1.0, le=24.0, description="Dosing interval in hours (1-24)"
    )


class PharmaPKModule(SimModule):
    """One-compartment oral absorption PK module for the Pharma district."""

    id = "pharma.pk"
    name = "Oral Pharmacokinetics"
    district = "pharma"
    description = (
        "One-compartment oral absorption model with linear superposition for multi-dose regimens."
    )
    version = "1.0.0"
    params_model = PharmaPKParams

    def run(self, params: BaseModel | dict[str, Any]) -> RunResult:
        """Run pure PK computation and package output into RunResult."""
        t_start = time.perf_counter()

        if isinstance(params, dict):
            validated = self.params_model.model_validate(params)
        else:
            validated = params  # type: ignore[assignment]

        drug = get_drug(validated.drug_id)
        patient = Patient(
            weight_kg=validated.weight_kg,
            clearance_multiplier=validated.clearance_multiplier,
        )

        res = simulate(
            drug=drug,
            patient=patient,
            dose_mg=validated.dose_mg,
            n_doses=validated.n_doses,
            interval_h=validated.interval_h,
        )

        warnings: list[str] = []
        if res.pct_red > 0.0:
            warnings.append(
                f"Toxicity threshold exceeded: {res.pct_red:.1f}% of simulation time above {drug.red_threshold} mg/L."
            )
        if res.pct_green < 20.0 and validated.dose_mg > 0:
            warnings.append(
                f"Sub-therapeutic regimen: only {res.pct_green:.1f}% of time inside the therapeutic window."
            )
        if validated.dose_mg * validated.n_doses > 4000.0 and validated.drug_id.lower() == "paracetamol":
            warnings.append(
                "Total paracetamol exceeds adult maximum recommended daily limit (4000 mg)."
            )

        duration_ms = (time.perf_counter() - t_start) * 1000.0

        summary = {
            "peak_concentration": round(res.peak_concentration, 4),
            "time_of_peak": round(res.time_of_peak, 2),
            "pct_green": round(res.pct_green, 2),
            "pct_below_green": round(res.pct_below_green, 2),
            "pct_red": round(res.pct_red, 2),
            "green_low": drug.green_low,
            "green_high": drug.green_high,
            "red_threshold": drug.red_threshold,
        }

        series = {
            "time_h": res.times,
            "concentration_mg_per_l": [round(c, 5) for c in res.concentrations],
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
        Verify the simulation engine against analytical closed-form benchmarks.

        Three independent physical/mathematical checks using paracetamol:
        1. Analytic tmax (closed-form vs. interpolated simulation peak)
        2. Terminal elimination half-life from late log-linear slope
        3. Linear dose proportionality (doubling dose doubles peak concentration)
        """
        drug = get_drug("paracetamol")
        standard_patient = Patient(weight_kg=70.0, clearance_multiplier=1.0)
        ke = math.log(2) / drug.half_life
        ka = drug.ka

        checks: list[RealityCheck] = []

        # -------------------------------------------------------------
        # 1. Analytic tmax
        # -------------------------------------------------------------
        # Closed-form Bateman peak time: tmax = ln(ka / ke) / (ka - ke)
        tmax_analytical = math.log(ka / ke) / (ka - ke)
        res_single = simulate(drug, standard_patient, dose_mg=500.0, n_doses=1, interval_h=6.0)

        # Refine grid peak with 3-point parabolic interpolation around peak step
        idx = res_single.concentrations.index(res_single.peak_concentration)
        t0, t1, t2 = res_single.times[idx - 1], res_single.times[idx], res_single.times[idx + 1]
        y0, y1, y2 = res_single.concentrations[idx - 1], res_single.concentrations[idx], res_single.concentrations[idx + 1]
        denom = (t0 - t1) * (t0 - t2) * (t1 - t2)
        A = (t2 * (y1 - y0) + t1 * (y0 - y2) + t0 * (y2 - y1)) / denom
        B = (t2 * t2 * (y0 - y1) + t1 * t1 * (y2 - y0) + t0 * t0 * (y1 - y2)) / denom
        tmax_actual = -B / (2 * A) if abs(A) > 1e-12 else res_single.time_of_peak

        tmax_diff = abs(tmax_actual - tmax_analytical) / tmax_analytical
        checks.append(
            RealityCheck(
                name="Analytic tmax",
                description="Simulated peak time matches Bateman closed-form tmax = ln(ka/ke)/(ka-ke).",
                expected=round(tmax_analytical, 4),
                actual=round(tmax_actual, 4),
                tolerance=0.02,  # 2%
                passed=bool(tmax_diff <= 0.02),
                source_note=(
                    "Classical one-compartment Bateman oral absorption equation analytical maximum. "
                    "Expected derived from ln(ka/ke)/(ka-ke) using paracetamol ka=2.0 h⁻¹, half-life=2.5 h."
                ),
            )
        )

        # -------------------------------------------------------------
        # 2. Terminal half-life
        # -------------------------------------------------------------
        # For t >> 1/ka, absorption is essentially complete; terminal elimination slope = -ke.
        # Estimate ke from log-concentration slope between 12h and 20h.
        t1_idx = int(round(12.0 / 0.1))
        t2_idx = int(round(20.0 / 0.1))
        c1 = res_single.concentrations[t1_idx]
        c2 = res_single.concentrations[t2_idx]
        time1 = res_single.times[t1_idx]
        time2 = res_single.times[t2_idx]
        slope = (math.log(c2) - math.log(c1)) / (time2 - time1)
        estimated_ke = -slope
        estimated_hl = math.log(2) / estimated_ke

        hl_diff = abs(estimated_hl - drug.half_life) / drug.half_life
        checks.append(
            RealityCheck(
                name="Terminal half-life",
                description="Late elimination phase slope matches drug's configured elimination half-life.",
                expected=round(drug.half_life, 4),
                actual=round(estimated_hl, 4),
                tolerance=0.05,  # 5%
                passed=bool(hl_diff <= 0.05),
                source_note=(
                    "Log-linear regression of mono-exponential elimination phase (12h to 20h). "
                    "Expected is paracetamol half-life (2.5 h) from drugs.json catalogue."
                ),
            )
        )

        # -------------------------------------------------------------
        # 3. Dose proportionality
        # -------------------------------------------------------------
        # First-order linear kinetics: doubling dose from 500mg to 1000mg doubles peak concentration.
        res_double = simulate(drug, standard_patient, dose_mg=1000.0, n_doses=1, interval_h=6.0)
        ratio = res_double.peak_concentration / res_single.peak_concentration
        ratio_diff = abs(ratio - 2.0) / 2.0

        checks.append(
            RealityCheck(
                name="Dose proportionality",
                description="Doubling single dose exactly doubles peak concentration in linear kinetics.",
                expected=2.0,
                actual=round(ratio, 4),
                tolerance=0.01,  # 1%
                passed=bool(ratio_diff <= 0.01),
                source_note=(
                    "Superposition principle in linear constant-coefficient ordinary differential equations. "
                    "Expected ratio is 2.0x when comparing 1000 mg vs 500 mg single oral doses."
                ),
            )
        )

        card = self.get_model_card()
        for c in checks:
            c.model_card = card

        return checks

    def get_model_card(self) -> ModelCard:
        """Return scientific documentation card for oral pharmacokinetics."""
        return ModelCard(
            module_id=self.id,
            name=self.name,
            underlying_models=[
                "One-compartment open pharmacokinetic model with first-order extravascular/oral absorption (ka) and first-order elimination (ke).",
                "Analytical Bateman function multi-dose superposition algorithm.",
            ],
            key_assumptions=[
                "Apparent volume of distribution (Vd) is homogeneous and well-stirred across the central compartment.",
                "First-order elimination with constant metabolic and renal clearance (CL = ke * Vd).",
                "Complete oral bioavailability fraction (F = 1.0) with instantaneous gastrointestinal dissolution.",
            ],
            known_limitations=[
                "Does not account for non-linear saturable metabolism (Michaelis-Menten kinetics).",
                "Omits multi-compartmental tissue distribution kinetics and protein-binding equilibria.",
                "Renal or hepatic clearance impairment is simplified to a constant clearance multiplier.",
            ],
            disclaimer="Educational simulation only. Not validated for clinical dosing or industrial chemical process control.",
        )

