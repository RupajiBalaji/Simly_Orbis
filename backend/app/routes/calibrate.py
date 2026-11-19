"""
backend/app/routes/calibrate.py
Pharma Calibration API Route (P4-T5 / Spec Section 9.1).

Accepts concentration-time dataset CSV, fits PK parameters via Nelder-Mead simplex,
and reports train and hold-out test metrics.
Strictly labelled: 'fit to your data, not validation'.
Never calibrated against unverified reference rows.
"""

from __future__ import annotations

import csv
import io
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from app.pharma.pkpd.calibrate import (
    CalibrationMetrics,
    DatasetSplit,
    calibrate_pkpd_holdout,
)
from app.pharma.pkpd.engine import ModelType, PKPDParams, RouteType

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/pharma/calibrate", tags=["calibration"])

MAX_CSV_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_ROWS = 5000


class CalibrationRequest(BaseModel):
    """Payload to calibrate pharmacokinetic parameters against user dataset."""

    csv_data: str = Field(..., description="CSV content containing time and concentration columns")
    route: str = Field(default="oral", description="Route: 'oral', 'iv_bolus', 'iv_infusion'")
    dose_mg: float = Field(default=500.0, ge=0.1, le=5000.0, description="Administered dose in mg")
    model_type: str = Field(default="one_compartment", description="'one_compartment' or 'two_compartment'")
    train_ratio: float = Field(default=0.7, ge=0.3, le=0.9, description="Fraction of observations for training")


class CalibrationResponse(BaseModel):
    """Parameter estimation and hold-out evaluation outcome."""

    fitted_params: dict[str, float]
    train_rmse: float
    train_mean_fold_error: float
    train_pct_within_2fold: float
    test_rmse: float
    test_mean_fold_error: float
    test_pct_within_2fold: float
    iterations: int
    converged: bool
    label: str = "fit to your data, not validation"
    disclaimer: str = (
        "Educational parameter estimation. Fit to your data, not validation. "
        "Calibration is never run against unverified reference rows."
    )


def parse_csv_data(csv_text: str) -> tuple[list[float], list[float]]:
    """Parse time and concentration pairs from CSV text."""
    if len(csv_text.encode("utf-8")) > MAX_CSV_BYTES:
        raise HTTPException(status_code=413, detail="CSV file exceeds maximum size limit of 5 MB.")

    reader = csv.reader(io.StringIO(csv_text.strip()))
    rows = list(reader)

    if not rows:
        raise HTTPException(status_code=400, detail="CSV file is empty.")

    if len(rows) > MAX_ROWS:
        raise HTTPException(status_code=400, detail=f"CSV file exceeds maximum row limit of {MAX_ROWS} rows.")

    header = [h.strip().lower() for h in rows[0]]

    # Detect time column
    time_col = -1
    for i, col in enumerate(header):
        if col in ("time", "time_h", "t", "hours", "hour"):
            time_col = i
            break

    # Detect conc column
    conc_col = -1
    for i, col in enumerate(header):
        if col in ("conc", "concentration", "c", "cp", "concs", "plasma_conc"):
            conc_col = i
            break

    if time_col == -1 or conc_col == -1:
        # Fallback to column 0 as time and column 1 as conc
        time_col = 0
        conc_col = 1
        data_rows = rows if not any(c.isalpha() for c in rows[0]) else rows[1:]
    else:
        data_rows = rows[1:]

    times: list[float] = []
    concs: list[float] = []

    for r_idx, row in enumerate(data_rows):
        if not row or len(row) <= max(time_col, conc_col):
            continue
        try:
            t_val = float(row[time_col].strip())
            c_val = float(row[conc_col].strip())
            if t_val >= 0.0 and c_val >= 0.0:
                times.append(t_val)
                concs.append(c_val)
        except ValueError:
            continue

    if len(times) < 4:
        raise HTTPException(status_code=400, detail="Insufficient valid concentration-time points (minimum 4 required).")

    # Sort by time
    combined = sorted(zip(times, concs), key=lambda x: x[0])
    times_sorted = [x[0] for x in combined]
    concs_sorted = [x[1] for x in combined]

    return times_sorted, concs_sorted


@router.post("", response_model=CalibrationResponse, summary="Fit PK parameters to user dataset")
async def calibrate_dataset(body: CalibrationRequest) -> CalibrationResponse:
    """
    Fit pharmacokinetic parameters to user-provided concentration-time dataset.
    Returns parameter estimates, train RMSE, and hold-out test RMSE.
    """
    times, concs = parse_csv_data(body.csv_data)

    # Hold-out partition (e.g. alternating or systematic split)
    n = len(times)
    n_train = max(2, int(round(n * body.train_ratio)))
    step = max(1, int(round(1.0 / (1.0 - body.train_ratio)))) if body.train_ratio < 1.0 else n + 1

    train_times: list[float] = []
    train_concs: list[float] = []
    test_times: list[float] = []
    test_concs: list[float] = []

    for idx, (t, c) in enumerate(zip(times, concs)):
        if idx % step == 0 and len(test_times) < (n - n_train):
            test_times.append(t)
            test_concs.append(c)
        else:
            train_times.append(t)
            train_concs.append(c)

    if not test_times:
        test_times = [train_times.pop()]
        test_concs = [train_concs.pop()]

    split = DatasetSplit(
        train_times=train_times,
        train_concs=train_concs,
        test_times=test_times,
        test_concs=test_concs,
    )

    route_enum = RouteType(body.route)
    model_enum = ModelType(body.model_type)

    base = PKPDParams(
        model_type=model_enum,
        route=route_enum,
        dose_mg=body.dose_mg,
        f_bioav=1.0,
    )

    params_to_fit = ["cl", "v1"]
    if route_enum == RouteType.oral:
        params_to_fit.append("ka")
    if model_enum == ModelType.two_compartment:
        params_to_fit.extend(["q", "v2"])

    metrics: CalibrationMetrics = calibrate_pkpd_holdout(
        base_params=base,
        data=split,
        param_names=params_to_fit,
    )

    return CalibrationResponse(
        fitted_params=metrics.fitted_params,
        train_rmse=metrics.train_rmse,
        train_mean_fold_error=metrics.train_mean_fold_error,
        train_pct_within_2fold=metrics.train_pct_within_2fold,
        test_rmse=metrics.test_rmse,
        test_mean_fold_error=metrics.test_mean_fold_error,
        test_pct_within_2fold=metrics.test_pct_within_2fold,
        iterations=metrics.iterations,
        converged=metrics.converged,
    )
