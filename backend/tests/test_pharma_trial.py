"""
Unit and integration tests for pharma.trial (Virtual Clinical Population Trial).
"""

import time
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.registry import get_module
from app.main import app
from app.modules.pharma_trial import PharmaTrialModule, PharmaTrialParams


def test_trial_module_registration():
    """Verify pharma.trial is registered in the module registry."""
    try:
        mod = get_module("pharma.trial")
    except KeyError:
        from app.core.registry import register
        register(PharmaTrialModule())
        mod = get_module("pharma.trial")
    assert mod.id == "pharma.trial"
    assert mod.district == "pharma"
    assert mod.params_model == PharmaTrialParams


def test_trial_module_run_and_performance():
    """Verify 1000 patients run finishes in under 2 seconds and produces all contract fields."""
    mod = PharmaTrialModule()
    params = PharmaTrialParams(
        drug_id="paracetamol",
        dose_mg=500.0,
        n_doses=1,
        interval_h=6.0,
        n_patients=1000,
        seed=42,
        pct_reduced_liver=10.0,
    )

    t0 = time.perf_counter()
    result = mod.run(params)
    duration_s = time.perf_counter() - t0

    # Must finish well under 2.0s
    assert duration_s < 2.0, f"Execution took {duration_s:.3f}s (exceeds 2.0s limit)"

    # Verify summary
    summary = result.summary
    assert summary["n_patients"] == 1000
    assert "pct_in_range" in summary
    assert "pct_toxic" in summary
    assert "pct_subtherapeutic" in summary
    assert "mean_peak" in summary
    assert "median_peak" in summary
    assert "subgroups" in summary
    assert "group_counts" in summary
    assert summary["group_counts"]["total"] == 1000

    # Verify series
    series = result.series
    assert series is not None
    assert "p5" in series and len(series["p5"]) == 121
    assert "p25" in series and len(series["p25"]) == 121
    assert "p50" in series and len(series["p50"]) == 121
    assert "p75" in series and len(series["p75"]) == 121
    assert "p95" in series and len(series["p95"]) == 121
    assert "hist_bins" in series and len(series["hist_bins"]) == 21  # 20 bins = 21 edges
    assert "hist_counts" in series and len(series["hist_counts"]) == 20
    assert "outcomes" in series and len(series["outcomes"]) == 1000

    # Verify outcome codes are strictly 0, 1, or 2
    unique_codes = set(series["outcomes"])
    assert unique_codes.issubset({0, 1, 2})


def test_trial_module_all_reality_checks():
    """Verify all 4 scientific sanity checks pass."""
    mod = PharmaTrialModule()
    checks = mod.reality_checks()
    assert len(checks) == 4

    for check in checks:
        assert check.passed, f"Reality check '{check.name}' failed: expected {check.expected}, got {check.actual}"


def test_trial_module_seed_reproducibility():
    """Verify identical seed produces identical results."""
    mod = PharmaTrialModule()
    params = PharmaTrialParams(
        drug_id="paracetamol",
        dose_mg=650.0,
        n_doses=2,
        interval_h=6.0,
        n_patients=250,
        seed=1337,
        pct_reduced_liver=15.0,
    )

    r1 = mod.run(params)
    r2 = mod.run(params)

    assert r1.summary == r2.summary
    assert r1.series["outcomes"] == r2.series["outcomes"]


def test_trial_subgroup_reduced_liver_vulnerability():
    """Verify reduced-liver patients experience higher peak concentrations due to 0.6x clearance."""
    mod = PharmaTrialModule()
    params = PharmaTrialParams(
        drug_id="paracetamol",
        dose_mg=1500.0,
        n_doses=4,
        interval_h=6.0,
        n_patients=500,
        seed=42,
        pct_reduced_liver=20.0,
    )
    result = mod.run(params)

    subgroups = result.summary["subgroups"]
    norm = subgroups["normal_liver"]
    impaired = subgroups["reduced_liver"]

    assert impaired["count"] == 100
    assert norm["count"] == 400
    # Impaired clearance should lead to higher mean and median peak
    assert impaired["mean_peak"] > norm["mean_peak"]
    assert impaired["median_peak"] > norm["median_peak"]


@pytest.mark.asyncio
async def test_api_run_with_pharma_trial(client: AsyncClient):
    """Verify POST /api/run executes pharma.trial and persists run record."""
    payload = {
        "module_id": "pharma.trial",
        "params": {
            "drug_id": "paracetamol",
            "dose_mg": 500.0,
            "n_doses": 1,
            "interval_h": 6.0,
            "n_patients": 100,
            "seed": 42,
            "pct_reduced_liver": 10.0,
        },
        "nickname": "TrialTester",
    }
    res = await client.post("/api/run", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "run_id" in data
    assert data["result"]["module_id"] == "pharma.trial"
    assert data["result"]["summary"]["n_patients"] == 100


@pytest.mark.asyncio
async def test_api_trial_compare(client: AsyncClient):
    """Verify POST /api/trial/compare computes comparative metrics between two regimens."""
    payload = {
        "regimen_a": {
            "drug_id": "paracetamol",
            "dose_mg": 1000.0,
            "n_doses": 2,
            "interval_h": 8.0,
            "n_patients": 200,
            "seed": 42,
            "pct_reduced_liver": 10.0,
        },
        "regimen_b": {
            "drug_id": "paracetamol",
            "dose_mg": 500.0,
            "n_doses": 1,
            "interval_h": 6.0,
            "n_patients": 200,
            "seed": 42,
            "pct_reduced_liver": 10.0,
        },
    }
    res = await client.post("/api/trial/compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "trial_a" in data
    assert "trial_b" in data
    assert "comparison" in data
    comp = data["comparison"]
    assert "diff_pct_in_range" in comp
    assert "diff_pct_toxic" in comp
    assert "verdict" in comp


@pytest.mark.asyncio
async def test_trial_validation_errors(client: AsyncClient):
    """Verify validation boundaries: n_patients (20-1000), n_doses (1-6)."""
    # Invalid n_patients = 1500 (max 1000)
    res1 = await client.post(
        "/api/run",
        json={
            "module_id": "pharma.trial",
            "params": {"dose_mg": 500, "n_patients": 1500},
        },
    )
    assert res1.status_code == 422

    # Invalid n_doses = 8 (max 6)
    res2 = await client.post(
        "/api/run",
        json={
            "module_id": "pharma.trial",
            "params": {"dose_mg": 500, "n_doses": 8},
        },
    )
    assert res2.status_code == 422


@pytest.mark.asyncio
async def test_finish_session_with_trial_result(client: AsyncClient):
    """Verify POST /api/lab/sessions/{id}/finish accepts and stores trial_result in lab report."""
    # Create session
    s_res = await client.post(
        "/api/lab/sessions",
        json={"experiment_id": "pk_ward", "nickname": "Dr_Trial_Tester"},
    )
    assert s_res.status_code == 201
    session_id = s_res.json()["session_id"]

    trial_payload = {
        "n_patients": 500,
        "pct_in_range": 78.5,
        "pct_toxic": 3.2,
        "pct_subtherapeutic": 18.3,
        "mean_peak": 14.2,
    }

    # Finish session with trial_result
    f_res = await client.post(
        f"/api/lab/sessions/{session_id}/finish",
        json={"trial_result": trial_payload},
    )
    assert f_res.status_code == 200
    report = f_res.json()
    assert report["trial_result"] == trial_payload
    assert any("Virtual Clinical Trial:" in lesson for lesson in report["lessons_learned"])

