"""
backend/app/modules/chem_buffer.py
Aqueous Buffer Equilibrium Simulation Module (Module: chem.buffer).

Standard: Section 9.2 & Section 18 (P3-T2) of Simly Orbis MVP Build Specification.
"""

from __future__ import annotations

import time
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.chem.buffer import (
    compute_buffer_state,
    simulate_buffer_stress,
)
from app.core.base import RealityCheck, RunResult, SimModule


class BufferParams(BaseModel):
    acid_name: str = Field(default="acetic", description="Weak acid identity (e.g. acetic, phosphate, formate)")
    pka: float = Field(default=4.76, ge=1.0, le=14.0, description="Acid dissociation constant pKa")
    acid_conc_m: float = Field(default=0.1, ge=0.0001, le=5.0, description="Concentration of weak acid HA (M)")
    salt_conc_m: float = Field(default=0.1, ge=0.0001, le=5.0, description="Concentration of conjugate base salt NaA (M)")
    volume_ml: float = Field(default=100.0, ge=10.0, le=1000.0, description="Total buffer volume (mL)")
    stress_test: Literal["none", "add_hcl", "add_naoh"] = Field(default="none", description="Stress test by adding strong acid or base")
    stress_titrant_conc_m: float = Field(default=1.0, ge=0.01, le=5.0, description="Concentration of added stress titrant (M)")
    stress_added_volume_ml: float = Field(default=10.0, ge=0.0, le=100.0, description="Volume of stress titrant added (mL)")


class ChemBufferModule(SimModule):
    """District Chemistry Module: Buffer Equilibrium & Capacity Simulator."""

    id = "chem.buffer"
    name = "Buffer Equilibrium & Capacity"
    district = "chemistry"
    description = (
        "Rigorous aqueous buffer simulator solving exact electroneutrality charge balance, "
        "Van Slyke buffer capacity, and pH response to strong acid/base additions."
    )
    version = "1.0.0"
    params_model = BufferParams

    def run(self, params: BufferParams | dict[str, Any]) -> RunResult:
        start_t = time.perf_counter()
        if isinstance(params, dict):
            p = BufferParams(**params)
        else:
            p = params

        ka = 10.0 ** (-p.pka)
        state = compute_buffer_state(
            total_acid_conc=p.acid_conc_m,
            total_salt_conc=p.salt_conc_m,
            ka=ka,
        )

        time_series = []
        if p.stress_test in ("add_hcl", "add_naoh"):
            titrant_type = "hcl" if p.stress_test == "add_hcl" else "naoh"
            stress_points = simulate_buffer_stress(
                initial_volume_ml=p.volume_ml,
                acid_conc=p.acid_conc_m,
                salt_conc=p.salt_conc_m,
                ka=ka,
                titrant_type=titrant_type,
                titrant_conc_m=p.stress_titrant_conc_m,
                max_added_ml=p.stress_added_volume_ml,
                num_steps=30,
            )
            time_series = [
                {
                    "added_volume_ml": pt.added_volume_ml,
                    "added_moles": pt.added_moles,
                    "ph": pt.ph,
                    "buffer_capacity_beta": pt.buffer_capacity_beta,
                }
                for pt in stress_points
            ]

        summary = {
            "initial_ph": round(state.ph, 4),
            "buffer_capacity_beta": round(state.buffer_capacity_beta, 6),
            "ha_equilibrium_m": round(state.ha_conc, 6),
            "a_equilibrium_m": round(state.a_conc, 6),
            "alpha_ha": round(state.alpha_0, 4),
            "alpha_a_minus": round(state.alpha_1, 4),
            "charge_balance_residual": state.charge_balance_residual,
        }

        exec_ms = (time.perf_counter() - start_t) * 1000.0

        reality_check = RealityCheck(
            is_physiologic=True,
            warnings=[],
            cmax_safe=True,
            tmax_plausible=True,
            auc_normal=True,
        )

        return RunResult(
            module_id=self.id,
            engine_version="1.0.0",
            execution_time_ms=exec_ms,
            parameters=p.model_dump(),
            summary=summary,
            time_series=time_series,
            reality_check=reality_check,
            visual_directives=[
                {"type": "plot_buffer_curve", "target": "buffer_graph"},
            ],
        )
