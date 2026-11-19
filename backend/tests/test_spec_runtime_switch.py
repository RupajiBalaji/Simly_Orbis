"""
Simly Orbis - Tests for SPEC_RUNTIME Configuration Flag and Dual-Mode Fallback.
Requirement: Task F2 / Spec Section 10.5, 10.6.
Verifies that:
1. Default SPEC_RUNTIME is False (legacy engine active).
2. When SPEC_RUNTIME is False, session operations and experiment registry use legacy engine.
3. When SPEC_RUNTIME is True, session operations and experiment registry dispatch to SpecRunner.
4. Setting SPEC_RUNTIME back to False immediately restores the legacy path with zero side effects.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.lab.engine import apply_action, create_session
from app.lab.experiments import get_experiment, list_experiments
from app.lab.models import ActionRequest, ActionType
from app.main import app


@pytest.fixture(autouse=True)
def restore_spec_runtime():
    """Ensure SPEC_RUNTIME is always restored to False after each test."""
    original = settings.spec_runtime
    try:
        yield
    finally:
        settings.spec_runtime = original


def test_spec_runtime_flag_default_is_false():
    """Confirm SPEC_RUNTIME flag default value is strictly False."""
    from app.config import Settings
    fresh_settings = Settings(_env_file=None)
    assert fresh_settings.spec_runtime is False, "Default SPEC_RUNTIME must be False for backward compatibility"


def test_legacy_mode_when_spec_runtime_false():
    """Verify legacy path behavior when SPEC_RUNTIME=False."""
    settings.spec_runtime = False

    # 1. Experiment definition from registry
    exp = get_experiment("titration_bench")
    assert "Spec v1.0.0" not in exp.description

    # 2. Session created uses legacy session structure
    session = create_session("titration_bench", "Test_Legacy")
    assert session.experiment_id == "titration_bench"

    # 3. Apply action through legacy engine
    res = apply_action(session, ActionRequest(action=ActionType.wear_ppe, target="goggles"))
    assert res.accepted is True
    assert "PPE" in res.message or "goggles" in res.message.lower()

    # 4. API endpoint returns legacy experiment metadata
    client = TestClient(app)
    resp = client.get("/api/lab/experiments/titration_bench")
    assert resp.status_code == 200
    assert "Spec v1.0.0" not in resp.json()["description"]


def test_spec_runtime_mode_when_spec_runtime_true():
    """Verify declarative spec runner behavior when SPEC_RUNTIME=True."""
    settings.spec_runtime = True

    # 1. Experiment definition loaded from spec
    exp = get_experiment("titration_bench")
    assert "Spec v1.0.0" in exp.description

    # 2. Session created uses spec runtime
    session = create_session("titration_bench", "Test_Spec")
    assert session.experiment_id == "titration_bench"

    # 3. Apply action through SpecRunner
    res = apply_action(session, ActionRequest(action=ActionType.wear_ppe, target="goggles"))
    assert res.accepted is True
    assert "PPE" in res.message or "goggles" in res.message.lower()

    # 4. API endpoint returns spec description
    client = TestClient(app)
    resp = client.get("/api/lab/experiments/titration_bench")
    assert resp.status_code == 200
    assert "Spec v1.0.0" in resp.json()["description"]


def test_dynamic_fallback_between_modes():
    """Verify clean bidirectional switching between legacy and spec runtime."""
    client = TestClient(app)

    # Starts in legacy
    settings.spec_runtime = False
    assert "Spec v1.0.0" not in client.get("/api/lab/experiments/titration_bench").json()["description"]

    # Switch to spec runtime
    settings.spec_runtime = True
    assert "Spec v1.0.0" in client.get("/api/lab/experiments/titration_bench").json()["description"]

    # Revert back to legacy fallback
    settings.spec_runtime = False
    assert "Spec v1.0.0" not in client.get("/api/lab/experiments/titration_bench").json()["description"]
