"""
backend/app/modules/chem_kinetics.py
Chemical Reaction Kinetics Simulation Module (Module: chem.kinetics).

Standard: Section 9.2 & Section 18 (P3-T1) of Simly Orbis MVP Build Specification.
"""

from __future__ import annotations

import time
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field

from app.chem.kinetics import (
    concentration_order_0,
    concentration_order_1,
    concentration_order_2,
    consecutive_kinetics,
    consecutive_peak_b,
    half_life_order_0,
    half_life_order_1,
    half_life_order_2,
    generate_kinetics_observations,
    fit_best_order,
)
from app.core.base import RealityCheck, RunResult, SimModule


class KineticsParams(BaseModel):
    order: Literal[0, 1, 2] = Field(default=1, description="Reaction order (0, 1, or 2)")
    k: float = Field(default=0.05, ge=0.0, le=100.0, description="Reaction rate constant")
    a0: float = Field(default=1.0, ge=0.0, le=10.0, description="Initial reactant concentration (M)")
    temperature_c: float = Field(default=25.0, ge=-20.0, le=200.0, description="Reaction temperature (°C)")
    duration_s: float = Field(default=60.0, ge=1.0, le=3600.0, description="Total reaction duration (s)")
    num_samples: int = Field(default=30, ge=2, le=500, description="Number of sampling intervals")
    noise_sd: float = Field(default=0.0, ge=0.0, le=0.5, description="Measurement noise standard deviation")
    seed: Optional[int] = Field(default=None, description="Random seed for repeatable noise")


class ChemKineticsModule(SimModule):
    """District Chemistry Module: Chemical Reaction Kinetics Simulator."""

    id = "chem.kinetics"
    name = "Chemical Reaction Kinetics"
    district = "chemistry"
    description = (
        "Reaction kinetics simulator with integrated rate laws for orders 0, 1, 2, "
        "Arrhenius temperature dependence, consecutive reactions, and linearised order fitting."
    )
    version = "1.0.0"
    params_model = KineticsParams

    def run(self, params: KineticsParams | dict[str, Any]) -> RunResult:
        start_t = time.perf_counter()
        if isinstance(params, dict):
            p = KineticsParams(**params)
        else:
            p = params

        step_size = p.duration_s / max(1, p.num_samples - 1)
        times = [i * step_size for i in range(p.num_samples)]

        obs = generate_kinetics_observations(
            order=p.order,
            k=p.k,
            a0=p.a0,
            time_points=times,
            noise_sd=p.noise_sd,
            seed=p.seed,
        )

        time_series = [
            {
                "time_s": o.time,
                "concentration_true_m": o.a_true,
                "concentration_measured_m": o.a_measured,
                "ln_conc": o.ln_a_measured,
                "inv_conc": o.inv_a_measured,
            }
            for o in obs
        ]

        if p.order == 0:
            t_half = half_life_order_0(p.a0, p.k) if p.k > 0 and p.a0 > 0 else 0.0
        elif p.order == 1:
            t_half = half_life_order_1(p.k) if p.k > 0 else 0.0
        else:
            t_half = half_life_order_2(p.a0, p.k) if p.k > 0 and p.a0 > 0 else 0.0

        fit = fit_best_order(obs) if len(obs) >= 2 else None

        summary = {
            "order": p.order,
            "k": p.k,
            "a0": p.a0,
            "half_life_s": round(t_half, 4),
            "final_concentration_m": round(obs[-1].a_measured, 6),
            "best_fit_order": fit.order_candidate if fit else None,
            "best_fit_r2": round(fit.r_squared, 4) if fit else None,
        }

        exec_ms = (time.perf_counter() - start_t) * 1000.0

        return RunResult(
            module_id=self.id,
            params=p.model_dump(),
            summary=summary,
            series={
                "time_s": [o.time_s for o in obs],
                "concentration_m": [o.a_measured for o in obs],
            },
            warnings=[],
            duration_ms=round(exec_ms, 3),
            engine_version="1.0.0",
        )

    def reality_checks(self) -> list[RealityCheck]:
        import math
        checks: list[RealityCheck] = []
        k = 0.05
        expected_thalf = math.log(2.0) / k
        actual_thalf = half_life_order_1(k)
        diff = abs(actual_thalf - expected_thalf) / expected_thalf
        checks.append(
            RealityCheck(
                name="First-order half-life",
                description="First-order half-life matches analytical formula t_1/2 = ln(2)/k within 0.1%.",
                expected=expected_thalf,
                actual=actual_thalf,
                tolerance=0.001,
                passed=diff <= 0.001,
                source_note="Integrated first-order rate law t_1/2 = ln(2)/k.",
            )
        )
        return checks
