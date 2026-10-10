"""
One-compartment, first-order oral absorption pharmacokinetics engine.

Bateman equation (single dose at time t_dose):

    C(t) = (F * D * ka) / (Vd * (ka - ke)) * (exp(-ke*(t-t_dose)) - exp(-ka*(t-t_dose)))
           for t >= t_dose, else 0.

When ka == ke the limit is used (L'Hôpital / Taylor):

    C(t) = (F * D * ka) / Vd * (t - t_dose) * exp(-ke*(t-t_dose))

Multiple doses are handled by superposition (linear system).
"""

from __future__ import annotations

import math

from app.sim.models import Drug, Patient, SimulationResult


# Simulation resolution (hours)
_TIME_STEP = 0.1
_KA_KE_EPSILON = 1e-9  # treat |ka - ke| < this as equal


def _bateman_single(
    *,
    t_elapsed: float,   # time since this dose was given  (h)
    F: float,           # bioavailability
    D: float,           # dose  (mg)
    ka: float,          # absorption rate constant  (h⁻¹)
    ke: float,          # elimination rate constant  (h⁻¹)
    Vd: float,          # volume of distribution  (L)
) -> float:
    """
    Return the plasma concentration (mg/L) at *t_elapsed* hours after a
    single oral dose D.  Returns 0 for t_elapsed < 0.
    """
    if t_elapsed < 0:
        return 0.0

    if abs(ka - ke) < _KA_KE_EPSILON:
        # Limit form when ka ≈ ke:  C = (F*D*ka/Vd) * t * exp(-ke*t)
        return (F * D * ka / Vd) * t_elapsed * math.exp(-ke * t_elapsed)

    return (
        (F * D * ka) / (Vd * (ka - ke))
        * (math.exp(-ke * t_elapsed) - math.exp(-ka * t_elapsed))
    )


def simulate(
    drug: Drug,
    patient: Patient,
    dose_mg: float,
    n_doses: int,
    interval_h: float,
) -> SimulationResult:
    """
    Simulate plasma concentration over 0–24 h.

    Parameters
    ----------
    drug        : Drug pharmacokinetic parameters.
    patient     : Patient demographics.
    dose_mg     : Dose per administration (mg).
    n_doses     : Number of doses given (first dose always at t=0).
    interval_h  : Dosing interval (h).  Ignored when n_doses == 1.

    Returns
    -------
    SimulationResult with time series and summary statistics.
    """
    if n_doses < 1:
        raise ValueError("n_doses must be >= 1")
    if dose_mg < 0:
        raise ValueError("dose_mg must be >= 0")

    # Derived PK parameters
    ke = math.log(2) / drug.half_life * patient.clearance_multiplier
    ka = drug.ka
    F = drug.bioavailability
    Vd = drug.vd_per_kg * patient.weight_kg   # L

    # Dose administration times
    dose_times = [i * interval_h for i in range(n_doses)]

    # Build time grid: 0 to 24 h inclusive
    n_steps = round(24.0 / _TIME_STEP) + 1
    times: list[float] = [round(i * _TIME_STEP, 10) for i in range(n_steps)]

    # Superposition: sum contributions from each dose
    concentrations: list[float] = []
    for t in times:
        total = sum(
            _bateman_single(
                t_elapsed=t - t_dose,
                F=F,
                D=dose_mg,
                ka=ka,
                ke=ke,
                Vd=Vd,
            )
            for t_dose in dose_times
        )
        concentrations.append(total)

    # ------------------------------------------------------------------ #
    # Summary statistics
    # ------------------------------------------------------------------ #
    peak_concentration = max(concentrations)
    time_of_peak = times[concentrations.index(peak_concentration)]

    n = len(concentrations)
    n_green = sum(
        1 for c in concentrations if drug.green_low <= c <= drug.green_high
    )
    n_below = sum(1 for c in concentrations if c < drug.green_low)
    n_red = sum(1 for c in concentrations if c > drug.red_threshold)

    pct_green = 100.0 * n_green / n
    pct_below = 100.0 * n_below / n
    pct_red = 100.0 * n_red / n

    return SimulationResult(
        times=times,
        concentrations=concentrations,
        peak_concentration=peak_concentration,
        time_of_peak=time_of_peak,
        pct_green=pct_green,
        pct_below_green=pct_below,
        pct_red=pct_red,
    )
