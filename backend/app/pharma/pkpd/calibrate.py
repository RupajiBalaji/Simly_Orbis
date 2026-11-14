"""
backend/app/pharma/pkpd/calibrate.py
NumPy-only Parameter Calibration & Hold-Out Validation Framework.

Implements:
- Nelder-Mead downhill simplex optimizer in pure Python + NumPy (no scipy dependency).
- Parameter estimation for (CL, V1, ka) for 1-compartment oral/IV and optionally (V2, Q) for 2-compartment.
- Train / test hold-out split protocol.
- Metrics reporting: Root Mean Squared Error (RMSE), Fold Error, % of points within 2-fold window.
- NOTE: Calibration requires concentration-time profile data. Real-data calibration requires
  human-curated clinical concentration-time curves. This framework is verified on synthetic datasets.

Educational simulation platform. Not medical advice. Not clinical evidence.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Any

import numpy as np

from app.pharma.pkpd.engine import PKPDParams, ModelType, RouteType, simulate_pkpd


@dataclass
class DatasetSplit:
    """Concentration-time observations split into training and hold-out evaluation."""
    train_times: list[float]
    train_concs: list[float]
    test_times: list[float]
    test_concs: list[float]


@dataclass
class CalibrationMetrics:
    """Honest evaluation metrics across train and test partitions."""
    train_rmse: float
    train_mean_fold_error: float
    train_pct_within_2fold: float
    test_rmse: float
    test_mean_fold_error: float
    test_pct_within_2fold: float
    fitted_params: dict[str, float]
    iterations: int
    converged: bool


def _compute_metrics(obs: np.ndarray, pred: np.ndarray) -> tuple[float, float, float]:
    """Compute RMSE, mean fold error, and % within 2-fold."""
    if len(obs) == 0:
        return 0.0, 1.0, 100.0

    # Avoid zero divide
    eps = 1e-9
    obs_safe = np.maximum(obs, eps)
    pred_safe = np.maximum(pred, eps)

    rmse = float(np.sqrt(np.mean((obs - pred) ** 2)))

    fold_errors = np.maximum(obs_safe / pred_safe, pred_safe / obs_safe)
    mean_fold = float(np.mean(fold_errors))

    within_2fold = float(np.mean(fold_errors <= 2.0) * 100.0)

    return rmse, mean_fold, within_2fold


def nelder_mead(
    cost_fn: Callable[[np.ndarray], float],
    x0: np.ndarray,
    bounds: list[tuple[float, float]],
    max_iter: int = 400,
    tol: float = 1e-5,
) -> tuple[np.ndarray, int, bool]:
    """
    Standard Nelder-Mead simplex optimization constrained to box bounds via projection/penalty.
    """
    dim = len(x0)
    # Penalty cost wrapper
    def bounded_cost(x: np.ndarray) -> float:
        penalty = 0.0
        for i, (low, high) in enumerate(bounds):
            if x[i] < low:
                penalty += 1e6 * (low - x[i]) ** 2
            elif x[i] > high:
                penalty += 1e6 * (x[i] - high) ** 2
        return cost_fn(np.clip(x, [b[0] for b in bounds], [b[1] for b in bounds])) + penalty

    # Initialize simplex around x0
    simplex = [x0.copy()]
    for i in range(dim):
        p = x0.copy()
        step = 0.1 * p[i] if abs(p[i]) > 1e-5 else 0.1
        p[i] += step
        simplex.append(p)

    simplex_costs = [bounded_cost(p) for p in simplex]

    # Hyperparameters
    alpha = 1.0   # reflection
    gamma = 2.0   # expansion
    rho = 0.5     # contraction
    sigma = 0.5   # shrink

    converged = False
    iteration = 0

    for it in range(max_iter):
        iteration = it + 1
        # Sort simplex by cost
        order = np.argsort(simplex_costs)
        simplex = [simplex[i] for i in order]
        simplex_costs = [simplex_costs[i] for i in order]

        # Convergence test on simplex diameter
        std_cost = np.std(simplex_costs)
        if std_cost < tol:
            converged = True
            break

        # Centroid of best dim points (excluding worst)
        x_bar = np.mean(simplex[:-1], axis=0)
        x_worst = simplex[-1]
        cost_worst = simplex_costs[-1]
        cost_best = simplex_costs[0]
        cost_second_worst = simplex_costs[-2]

        # 1. Reflection
        x_r = x_bar + alpha * (x_bar - x_worst)
        cost_r = bounded_cost(x_r)

        if cost_best <= cost_r < cost_second_worst:
            simplex[-1] = x_r
            simplex_costs[-1] = cost_r
            continue

        # 2. Expansion
        if cost_r < cost_best:
            x_e = x_bar + gamma * (x_r - x_bar)
            cost_e = bounded_cost(x_e)
            if cost_e < cost_r:
                simplex[-1] = x_e
                simplex_costs[-1] = cost_e
            else:
                simplex[-1] = x_r
                simplex_costs[-1] = cost_r
            continue

        # 3. Contraction
        if cost_r < cost_worst:
            # Outside contraction
            x_c = x_bar + rho * (x_r - x_bar)
            cost_c = bounded_cost(x_c)
            if cost_c <= cost_r:
                simplex[-1] = x_c
                simplex_costs[-1] = cost_c
                continue
        else:
            # Inside contraction
            x_c = x_bar - rho * (x_bar - x_worst)
            cost_c = bounded_cost(x_c)
            if cost_c < cost_worst:
                simplex[-1] = x_c
                simplex_costs[-1] = cost_c
                continue

        # 4. Shrink
        x_best = simplex[0]
        for i in range(1, dim + 1):
            simplex[i] = x_best + sigma * (simplex[i] - x_best)
            simplex_costs[i] = bounded_cost(simplex[i])

    best_idx = int(np.argmin(simplex_costs))
    best_x = np.clip(simplex[best_idx], [b[0] for b in bounds], [b[1] for b in bounds])
    return best_x, iteration, converged


def calibrate_pkpd_holdout(
    base_params: PKPDParams,
    data: DatasetSplit,
    param_names: list[str] = ("cl", "v1", "ka"),
    init_guess: dict[str, float] | None = None,
    bounds: dict[str, tuple[float, float]] | None = None,
) -> CalibrationMetrics:
    """
    Fit parameters to training split and evaluate honestly against hold-out test split.
    """
    default_bounds = {
        "cl": (0.1, 100.0),
        "v1": (1.0, 300.0),
        "ka": (0.05, 10.0),
        "q": (0.1, 100.0),
        "v2": (1.0, 500.0),
    }
    bounds_dict = dict(default_bounds)
    if bounds:
        bounds_dict.update(bounds)

    x0_list: list[float] = []
    bounds_list: list[tuple[float, float]] = []

    for name in param_names:
        val = init_guess.get(name, getattr(base_params, name)) if init_guess else getattr(base_params, name)
        low, high = bounds_dict[name]
        clamped_val = max(low * 1.05, min(high * 0.95, float(val)))
        x0_list.append(clamped_val)
        bounds_list.append((low, high))

    x0 = np.array(x0_list, dtype=float)

    # Cost function on training set
    train_times = np.array(data.train_times)
    train_obs = np.array(data.train_concs)
    t_max_train = float(np.max(train_times)) if len(train_times) > 0 else 24.0

    def cost(p_arr: np.ndarray) -> float:
        test_p = PKPDParams(**base_params.__dict__)
        for name, val in zip(param_names, p_arr):
            setattr(test_p, name, float(val))
        try:
            res = simulate_pkpd(test_p, t_end_h=t_max_train, dt_h=0.05)
            # Interpolate to training times
            preds = np.interp(train_times, res.times, res.concentrations)
            return float(np.sum((train_obs - preds) ** 2))
        except Exception:
            return 1e12

    best_p, iters, converged = nelder_mead(cost, x0, bounds_list)

    # Evaluate fitted model on both train and test sets
    final_p = PKPDParams(**base_params.__dict__)
    fitted_dict: dict[str, float] = {}
    for name, val in zip(param_names, best_p):
        setattr(final_p, name, float(val))
        fitted_dict[name] = round(float(val), 4)

    t_eval = max(
        float(np.max(train_times)) if len(train_times) > 0 else 24.0,
        float(np.max(data.test_times)) if len(data.test_times) > 0 else 24.0,
    )
    final_sim = simulate_pkpd(final_p, t_end_h=t_eval, dt_h=0.05)

    train_preds = np.interp(train_times, final_sim.times, final_sim.concentrations)
    test_times = np.array(data.test_times)
    test_obs = np.array(data.test_concs)
    test_preds = np.interp(test_times, final_sim.times, final_sim.concentrations)

    tr_rmse, tr_fold, tr_pct = _compute_metrics(train_obs, train_preds)
    te_rmse, te_fold, te_pct = _compute_metrics(test_obs, test_preds)

    return CalibrationMetrics(
        train_rmse=round(tr_rmse, 4),
        train_mean_fold_error=round(tr_fold, 4),
        train_pct_within_2fold=round(tr_pct, 1),
        test_rmse=round(te_rmse, 4),
        test_mean_fold_error=round(te_fold, 4),
        test_pct_within_2fold=round(te_pct, 1),
        fitted_params=fitted_dict,
        iterations=iters,
        converged=converged,
    )
