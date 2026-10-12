"""
Shared data models for the PK engine.

These are plain dataclasses so the module stays dependency-free
(no FastAPI / Pydantic required).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Drug:
    """Pharmacokinetic parameters for a single drug."""

    name: str

    # Absorption rate constant  (h⁻¹)
    ka: float

    # Elimination half-life  (h)  →  ke = ln2 / half_life
    half_life: float

    # Volume of distribution per kg body weight  (L/kg)
    vd_per_kg: float

    # Oral bioavailability  (0–1)
    bioavailability: float

    # Therapeutic window: [green_low, green_high]  (mg/L)
    green_low: float
    green_high: float

    # Toxicity threshold  (mg/L)
    red_threshold: float

    # Suggested standard dose  (mg)
    standard_dose_mg: float

    # Parameter provenance: citations or "game-balanced"
    provenance: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Patient:
    """Patient demographics that influence PK."""

    # Body weight  (kg)
    weight_kg: float

    # Multiplier applied to ke  (1.0 = normal; <1.0 = reduced clearance)
    clearance_multiplier: float = 1.0


@dataclass
class SimulationResult:
    """Output of a single simulate() call."""

    # Parallel arrays – times in hours, concentrations in mg/L
    times: list[float]
    concentrations: list[float]

    # Summary statistics
    peak_concentration: float      # mg/L
    time_of_peak: float            # h

    # Percentage of simulated time spent in each zone
    pct_green: float               # in [green_low, green_high]
    pct_below_green: float         # < green_low
    pct_red: float                 # > red_threshold
