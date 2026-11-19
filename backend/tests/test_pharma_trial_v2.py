"""
Tests for Virtual Clinical Population Trial v2 (pharma.trial_v2).

Acceptance Criteria tested:
1. A cohort of one equals the single-patient pkpd engine result.
2. Seeded reruns are 100% deterministic and identical.
3. A 1,000-patient run time is measured and recorded.
4. Two-regimen comparative analysis and deterministic code-written insight statement.
5. Deterministic CSV export generation.
6. API routes verify 'virtual population, not a clinical trial' labeling and valid DOM/API models.
"""

from __future__ import annotations

import time
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.modules.pharma_trial_v2 import PharmaTrialV2Module, PharmaTrialV2Params
from app.pharma.pkpd.engine import PKPDParams, RouteType, simulate_pkpd
from app.pharma.pkpd.trial_v2 import (
    TrialRegimen,
    VirtualCohortConfig,
    compare_trials_v2,
    generate_trial_v2_csv,
    simulate_trial_v2,
)


def test_cohort_of_one_equals_single_patient():
    """ACCEPT: A cohort of one equals the single-patient engine result."""
    regimen = TrialRegimen(
        drug_id="paracetamol",
        route=RouteType.oral,
        dose_mg=500.0,
        n_doses=1,
        interval_h=6.0,
    )
    cohort_cfg = VirtualCohortConfig(
        n_patients=1,
        seed=42,
        zero_variability=True,
    )

    # 1. Run Virtual Trial v2 with N=1
    trial_res = simulate_trial_v2(regimen, cohort_cfg)
    assert len(trial_res.patients) == 1
    patient = trial_res.patients[0]

    # 2. Run single-patient core pkpd engine
    # Paracetamol reference: CL=18.0, V1=65.0, ka=1.5, f=0.88, t_lag=0.1
    base_params = PKPDParams(
        dose_mg=500.0,
        n_doses=1,
        interval_h=6.0,
        cl=18.0,
        v1=65.0,
        ka=1.5,
        f_bioav=0.88,
        t_lag=0.1,
    )
    single_res = simulate_pkpd(base_params)

    # Assert Cmax, AUC, and t_max are identical within numerical rounding
    assert pytest.approx(patient.cmax, rel=1e-4) == single_res.cmax
    assert pytest.approx(patient.auc, rel=1e-4) == single_res.auc_analytic
    assert pytest.approx(patient.t_max_h, rel=1e-3) == single_res.tmax
    assert trial_res.summary.cmax_dist.median == patient.cmax


def test_seeded_reruns_are_identical():
    """ACCEPT: Seeded reruns are 100% deterministic and identical."""
    regimen = TrialRegimen(
        drug_id="metformin",
        route=RouteType.oral,
        dose_mg=850.0,
        n_doses=2,
        interval_h=12.0,
    )
    cohort_cfg = VirtualCohortConfig(
        n_patients=100,
        seed=12345,
    )

    run_1 = simulate_trial_v2(regimen, cohort_cfg)
    run_2 = simulate_trial_v2(regimen, cohort_cfg)

    # Compare summaries
    assert run_1.summary.pct_target == run_2.summary.pct_target
    assert run_1.summary.pct_below == run_2.summary.pct_below
    assert run_1.summary.pct_above == run_2.summary.pct_above
    assert run_1.summary.cmax_dist.median == run_2.summary.cmax_dist.median
    assert run_1.summary.auc_dist.mean == run_2.summary.auc_dist.mean
    assert run_1.summary.insight == run_2.summary.insight

    # Compare every patient record
    for p1, p2 in zip(run_1.patients, run_2.patients):
        assert p1.patient_id == p2.patient_id
        assert p1.weight_kg == p2.weight_kg
        assert p1.age_yr == p2.age_yr
        assert p1.crcl_ml_min == p2.crcl_ml_min
        assert p1.cmax == p2.cmax
        assert p1.auc == p2.auc
        assert p1.status == p2.status


def test_1000_patient_runtime_recorded():
    """ACCEPT: A 1,000-patient run time is recorded and reported."""
    regimen = TrialRegimen(
        drug_id="gentamicin",
        route=RouteType.iv_infusion,
        dose_mg=280.0,
        n_doses=1,
        infusion_duration_h=0.5,
    )
    cohort_cfg = VirtualCohortConfig(
        n_patients=1000,
        seed=999,
    )

    t0 = time.perf_counter()
    trial_res = simulate_trial_v2(regimen, cohort_cfg)
    wall_ms = (time.perf_counter() - t0) * 1000.0

    assert len(trial_res.patients) == 1000
    assert trial_res.summary.timing_ms > 0.0
    print(f"\n[ACCEPT 1,000-Patient Timing] Completed 1,000 virtual patients in {trial_res.summary.timing_ms:.2f} ms (wall clock {wall_ms:.2f} ms).")
    # Must complete comfortably under 10 seconds
    assert trial_res.summary.timing_ms < 10000.0


def test_compare_trials_v2():
    """Verify side-by-side comparative analysis of two regimens."""
    reg_a = TrialRegimen(drug_id="amoxicillin", route=RouteType.oral, dose_mg=500.0, n_doses=3, interval_h=8.0)
    reg_b = TrialRegimen(drug_id="amoxicillin", route=RouteType.oral, dose_mg=875.0, n_doses=2, interval_h=12.0)
    cohort_cfg = VirtualCohortConfig(n_patients=200, seed=42)

    comp = compare_trials_v2(reg_a, reg_b, cohort_cfg)
    assert "regimen_a" in comp
    assert "regimen_b" in comp
    assert "comparison" in comp
    assert comp["comparison"]["label"] == "virtual population, not a clinical trial"
    assert "verdict" in comp["comparison"]


def test_csv_export():
    """Verify CSV export formatting and header structure."""
    regimen = TrialRegimen(drug_id="caffeine", route=RouteType.oral, dose_mg=200.0)
    cohort_cfg = VirtualCohortConfig(n_patients=50, seed=42)
    res = simulate_trial_v2(regimen, cohort_cfg)

    csv_text = generate_trial_v2_csv(res)
    lines = csv_text.strip().splitlines()
    assert lines[0] == "patient_id,weight_kg,age_yr,crcl_ml_min,cmax_mg_l,auc_mg_h_l,t_max_h,c_trough_mg_l,status"
    assert len(lines) == 51  # Header + 50 patients


def test_sim_module_wrapper():
    """Verify SimModule interface implementation for pharma.trial_v2."""
    mod = PharmaTrialV2Module()
    assert mod.id == "pharma.trial_v2"
    assert mod.district == "pharma"

    params = PharmaTrialV2Params(drug_id="paracetamol", dose_mg=500.0, n_patients=50)
    run_res = mod.run(params)
    assert run_res.module_id == "pharma.trial_v2"
    assert "cmax_dist" in run_res.summary
    assert run_res.summary["label"] == "virtual population, not a clinical trial"

    checks = mod.reality_checks()
    assert len(checks) >= 2
    for c in checks:
        assert c.passed is True


@pytest.mark.asyncio
async def test_api_trial_v2_endpoints():
    """Verify HTTP API endpoints for Virtual Trial v2."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Run endpoint
        run_payload = {
            "regimen": {
                "drug_id": "paracetamol",
                "route": "oral",
                "dose_mg": 500.0,
                "n_doses": 1,
            },
            "cohort": {
                "n_patients": 50,
                "seed": 42,
            },
        }
        res = await client.post("/api/trial/v2/run", json=run_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["summary"]["label"] == "virtual population, not a clinical trial"
        assert len(data["patients"]) == 50
        assert all(p["icon"] in ("shield", "arrow-down", "warning") for p in data["patients"])
        assert all(p["color"].startswith("#") for p in data["patients"])

        # 2. Compare endpoint
        comp_payload = {
            "regimen_a": {
                "drug_id": "paracetamol",
                "route": "oral",
                "dose_mg": 500.0,
                "n_doses": 1,
            },
            "regimen_b": {
                "drug_id": "paracetamol",
                "route": "oral",
                "dose_mg": 1000.0,
                "n_doses": 1,
            },
            "cohort": {
                "n_patients": 50,
                "seed": 42,
            },
        }
        res_comp = await client.post("/api/trial/v2/compare", json=comp_payload)
        assert res_comp.status_code == 200
        comp_data = res_comp.json()
        assert "comparison" in comp_data
        assert comp_data["comparison"]["label"] == "virtual population, not a clinical trial"

        # 3. CSV export endpoint
        res_csv = await client.post("/api/trial/v2/export_csv", json=run_payload)
        assert res_csv.status_code == 200
        assert "text/csv" in res_csv.headers["content-type"]
        assert "patient_id" in res_csv.text
