"""
Tests for ChemTitrationModule (chem.titration) and analytical reality checks.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.registry import get_module
from app.modules.chem_titration import ChemTitrationModule, TitrationParams


def test_titration_module_registry():
    module = get_module("chem.titration")
    assert isinstance(module, ChemTitrationModule)
    assert module.id == "chem.titration"
    assert module.district == "chemistry"
    assert module.version == "1.0.0"


def test_titration_run_strong_acid():
    module = ChemTitrationModule()
    params = TitrationParams(
        analyte="hcl_0.1M",
        analyte_volume_ml=25.0,
        titrant_conc_m=0.1,
        titrant_added_ml=25.0,
        indicator="phenolphthalein",
    )
    result = module.run(params)
    assert result.module_id == "chem.titration"
    assert result.summary["ph"] == 7.000
    assert result.summary["equivalence_volume_ml"] == 25.0
    assert result.summary["is_past_equivalence"] is True
    assert result.summary["overshoot_ml"] == 0.0
    assert "titrant_volume_ml" in result.series
    assert "ph_curve" in result.series
    assert len(result.series["titrant_volume_ml"]) == 101


def test_titration_run_weak_acid():
    module = ChemTitrationModule()
    # At half-equivalence (12.5 mL), pH should equal pKa (4.76)
    params = TitrationParams(
        analyte="acetic_0.1M",
        analyte_volume_ml=25.0,
        titrant_conc_m=0.1,
        titrant_added_ml=12.5,
        indicator="phenolphthalein",
    )
    result = module.run(params)
    assert abs(result.summary["ph"] - 4.76) <= 0.05
    assert result.summary["is_past_equivalence"] is False


def test_titration_reality_checks_pass():
    module = ChemTitrationModule()
    checks = module.reality_checks()
    assert len(checks) == 4
    for c in checks:
        assert c.passed is True, f"Reality check {c.name} failed: {c}"


@pytest.mark.asyncio
async def test_titration_reality_check_endpoint(client: AsyncClient):
    resp = await client.get("/api/modules/chem.titration/reality-check")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 4
    assert all(c["passed"] is True for c in data)
