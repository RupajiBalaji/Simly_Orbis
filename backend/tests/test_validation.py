"""
Tests for Validation Harness (backend/tests/test_validation.py).

Verifies:
1. Runner determinism (identical results across runs).
2. GET /api/validation/summary endpoint functionality and caching.
3. Strict exclusion of unverified rows from headline pass rate.
4. CI failure enforcement if verified pass rate drops below tolerances.yaml threshold.
5. Parameter provenance tagging (clinical citations vs game-balanced thresholds).
6. Sensitivity analysis dominance rankings.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from httpx import AsyncClient

from app.sim.drugs import DRUGS
from app.validation.runner import ValidationRunner, get_validation_summary


@pytest.fixture
def runner():
    return ValidationRunner()


def test_validation_runner_deterministic(runner: ValidationRunner):
    """Evaluating benchmarks twice yields identical deterministic results."""
    run1 = runner.evaluate_all()
    run2 = runner.evaluate_all()

    assert run1["total_references"] == run2["total_references"]
    assert run1["human_verified"] == run2["human_verified"]
    assert run1["pending_human_check"] == run2["pending_human_check"]
    assert run1["pass_rate"] == run2["pass_rate"]
    assert run1["median_fold_error"] == run2["median_fold_error"]
    assert run1["mean_percent_error"] == run2["mean_percent_error"]

    # Verify per-item equality
    for item1, item2 in zip(run1["unverified_results"], run2["unverified_results"]):
        assert item1["id"] == item2["id"]
        assert item1["predicted_value"] == item2["predicted_value"]
        assert item1["fold_error"] == item2["fold_error"]
        assert item1["passed"] == item2["passed"]


@pytest.mark.asyncio
async def test_validation_summary_endpoint(client: AsyncClient):
    """GET /api/validation/summary returns 200 with required contract keys and banner."""
    res = await client.get("/api/validation/summary")
    assert res.status_code == 200
    data = res.json()

    assert "total_references" in data
    assert "human_verified" in data
    assert "pending_human_check" in data
    assert "pass_rate" in data
    assert "passed_verified_count" in data
    assert "median_fold_error" in data
    assert "mean_percent_error" in data
    assert "banner" in data
    assert "verified_results" in data
    assert "unverified_results" in data
    assert "sensitivity_analysis" in data

    # Verify mandatory disclaimer banner
    assert data["banner"] == "Compared with published data for the stated conditions. Not clinical validation."
    assert data["human_verified"] == 0
    assert data["pending_human_check"] >= 20
    assert data["total_references"] == data["human_verified"] + data["pending_human_check"]
    assert data["pass_rate"] == "N/A: awaiting human verification"
    assert data["median_fold_error"] == "N/A: awaiting human verification"
    assert data["ci_threshold_satisfied"] is False


def test_unverified_rows_excluded_from_headline_pass_rate(runner: ValidationRunner):
    """Unverified literature rows are strictly excluded from headline metrics and isolated in pending queue."""
    res = runner.evaluate_all()

    total = res["total_references"]
    verified_count = res["human_verified"]
    pending_count = res["pending_human_check"]

    assert pending_count > 0, "Expected unverified rows in test fixtures for queue testing"
    assert total == verified_count + pending_count

    # Check verified list
    for item in res["verified_results"]:
        assert item["is_verified"] is True
        assert item["verified_by"] != "unverified"

    # Check unverified list
    for item in res["unverified_results"]:
        assert item["is_verified"] is False
        assert item["verified_by"] == "unverified"

    if verified_count > 0:
        expected_pass_rate = round(res["passed_verified_count"] / verified_count, 4)
        assert res["pass_rate"] == expected_pass_rate
    else:
        assert res["pass_rate"] == "N/A: awaiting human verification"
        assert res["median_fold_error"] == "N/A: awaiting human verification"
        assert res["ci_threshold_satisfied"] is False

    # Test with synthetic references to confirm headline pass rate excludes unverified items
    synthetic_refs = [
        {
            "id": "titr_hcl_veq_synthetic",
            "quantity": "equivalence_volume",
            "value": 25.0,
            "unit": "mL",
            "population_or_condition": "test",
            "dose_or_regimen": "test",
            "source_citation": "test",
            "source_url_or_doi": "test",
            "retrieved_on": "2026-10-12",
            "verified_by": "Dr. Verifier",
            "notes": "",
            "source_file": "test.csv",
        },
        {
            "id": "titr_hcl_veq_unverified_failing",
            "quantity": "equivalence_volume",
            "value": 999.0,
            "unit": "mL",
            "population_or_condition": "test",
            "dose_or_regimen": "test",
            "source_citation": "test",
            "source_url_or_doi": "test",
            "retrieved_on": "2026-10-12",
            "verified_by": "unverified",
            "notes": "",
            "source_file": "test.csv",
        },
    ]
    test_runner = ValidationRunner()
    test_runner.references = synthetic_refs
    test_res = test_runner.evaluate_all()
    assert test_res["human_verified"] == 1
    assert test_res["pending_human_check"] == 1
    assert test_res["pass_rate"] == 1.0
    assert test_res["passed_verified_count"] == 1
    assert test_res["ci_threshold_satisfied"] is True


def test_verified_pass_rate_meets_ci_threshold(runner: ValidationRunner):
    """Verified pass rate satisfies CI threshold only with nonzero verified rows meeting tolerance floor."""
    res = runner.evaluate_all()
    min_required = res["min_verified_pass_rate_required"]

    # When verified count == 0, never show PASS
    assert res["human_verified"] == 0
    assert res["ci_threshold_satisfied"] is False
    assert res["pass_rate"] == "N/A: awaiting human verification"
    assert res["status"] == "N/A: awaiting human verification"

    synthetic_passing = [
        {
            "id": "titr_hcl_veq",
            "quantity": "equivalence_volume",
            "value": 25.0,
            "unit": "mL",
            "population_or_condition": "test",
            "dose_or_regimen": "test",
            "source_citation": "test",
            "source_url_or_doi": "test",
            "retrieved_on": "2026-10-12",
            "verified_by": "Dr. Verifier",
            "notes": "",
            "source_file": "test.csv",
        }
    ]
    test_runner = ValidationRunner()
    test_runner.references = synthetic_passing
    pass_res = test_runner.evaluate_all()
    assert pass_res["human_verified"] == 1
    assert pass_res["ci_threshold_satisfied"] is True
    assert pass_res["status"] == "PASS"
    assert pass_res["pass_rate"] >= min_required


def test_drug_parameter_provenance_integrity():
    """All drugs must specify parameter provenance; game thresholds must be tagged 'game-balanced'."""
    assert len(DRUGS) >= 3
    for drug_id, drug in DRUGS.items():
        prov = drug.provenance
        assert isinstance(prov, dict), f"Drug {drug_id} missing provenance dictionary"
        assert len(prov) > 0, f"Drug {drug_id} has empty provenance"

        # Check key PK parameters are linked to literature citations
        for key in ("ka", "half_life", "vd_per_kg", "bioavailability"):
            assert key in prov, f"Drug {drug_id} missing provenance for {key}"
            assert prov[key] != "game-balanced", f"PK parameter {key} on {drug_id} cannot be game-balanced"
            assert len(prov[key]) > 5, f"Citation for {key} on {drug_id} too brief"

        # Check gameplay thresholds are explicitly marked game-balanced
        for key in ("green_low", "green_high", "red_threshold"):
            assert key in prov, f"Drug {drug_id} missing provenance for {key}"
            assert prov[key] == "game-balanced", f"Threshold {key} on {drug_id} must be 'game-balanced'"


def test_sensitivity_analysis_identifies_dominant_parameters(runner: ValidationRunner):
    """Sensitivity analysis correctly isolates dominant AUC parameters (F, Vd, Weight)."""
    sens = runner.run_sensitivity_analysis()

    assert "dominant_parameters" in sens
    assert "summary" in sens
    assert "results" in sens

    dominant = sens["dominant_parameters"]
    assert "bioavailability" in dominant or "vd_per_kg" in dominant


def test_artifacts_generated_on_disk():
    """Validation harness creates results.json, report markdown, and matplotlib figures."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    results_json = base_dir / "validation" / "results.json"
    report_md = base_dir / "docs" / "VALIDATION_REPORT.md"
    plots_dir = base_dir / "docs" / "validation"

    assert results_json.exists(), "validation/results.json does not exist"
    assert report_md.exists(), "docs/VALIDATION_REPORT.md does not exist"
    assert results_json.stat().st_size > 0
    assert report_md.stat().st_size > 0

    assert (plots_dir / "predicted_vs_observed.png").exists()
    assert (plots_dir / "pk_curves_with_references.png").exists()
    assert (plots_dir / "sensitivity_tornado.png").exists()
    assert (plots_dir / "population_percentile_bands.png").exists()
