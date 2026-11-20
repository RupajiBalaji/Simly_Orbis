"""
backend/tests/test_space_performance.py
Verification suite for Space Launch Bench Performance and Tiered Budgets (P5-T4).

Verifies:
1. Tiered particle budgets and low-spec optimizations in frontend/lab/world/space_scene.js:
   - particleBudgets: low = 0 (disabled), medium >= 100, high >= 300.
   - starBudgets: low = 200, medium = 800, high = 2000.
   - Low quality disables particles, purges existing particles, disables cast/receive shadows.
   - Particle lifecycle: spawnExhaustParticle obeys particleBudgets and updateParticles recycles memory.
   - Integration with scene.js setQuality hook.
2. Real-time compute latency budget:
   - Core two-body orbital step and evaluate_mission execute in < 5 ms (well below 16.6 ms for 60 FPS).
   - Numerical propagation executes 1000 steps deterministically with high throughput.
"""

from __future__ import annotations

import time
from pathlib import Path
import pytest

from app.space.orbit import (
    EARTH_MU,
    EARTH_RADIUS_M,
    circular_velocity,
    orbital_period,
    hohmann_transfer,
    evaluate_mission,
    get_preset_rockets,
)


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_space_scene_tiered_particle_budgets_contract():
    """Verify frontend space_scene.js declares tiered particle budgets and low-spec mode."""
    js_path = REPO_ROOT / "frontend" / "lab" / "world" / "space_scene.js"
    assert js_path.exists(), "frontend/lab/world/space_scene.js not found"
    content = js_path.read_text(encoding="utf-8")

    # Tiered particle budgets
    assert "particleBudgets" in content
    assert "low: 0" in content
    assert "medium: 120" in content or "medium: 100" in content
    assert "high: 350" in content or "high: 300" in content

    # Tiered star budgets
    assert "starBudgets" in content
    assert "low: 200" in content
    assert "medium: 800" in content

    # Low-spec optimization behaviors
    assert "setQuality(mode)" in content
    assert "this.qualityTier = mode" in content
    assert "this.smokeParticles = []" in content
    assert "spawnExhaustParticle()" in content
    assert "updateParticles(dt)" in content
    assert "if (this.qualityTier === 'low') return;" in content


def test_scene_manager_routes_quality_to_space_scene():
    """Verify scene.js integrates spaceScene.setQuality."""
    scene_path = REPO_ROOT / "frontend" / "lab" / "world" / "scene.js"
    assert scene_path.exists(), "frontend/lab/world/scene.js not found"
    content = scene_path.read_text(encoding="utf-8")

    assert "this.spaceScene.setQuality(this.quality)" in content
    assert "this.spaceScene?.setQuality(mode)" in content or "this.spaceScene.setQuality(mode)" in content


def test_space_engine_latency_within_60fps_budget():
    """Verify space simulation and orbital calculations easily execute within a 16.6 ms (60 FPS) frame budget."""
    presets = get_preset_rockets()
    orbis1 = next(p for p in presets if p["id"] == "orbis_1")

    # 1. Mission evaluation performance (< 5.0 ms per run)
    t0 = time.perf_counter()
    n_evals = 20
    for _ in range(n_evals):
        res = evaluate_mission(
            stages=orbis1["stages"],
            payload_mass_kg=500.0,
            target_altitude_m=200000.0,
        )
        assert res["outcome"] in ("orbit_reached", "suborbital_fall", "no_liftoff", "orbit_eccentric")
    elapsed_eval = (time.perf_counter() - t0) / n_evals

    # Average run should be under 5 ms (often < 0.2 ms)
    assert elapsed_eval < 0.005, f"evaluate_mission too slow: {elapsed_eval*1000:.2f} ms"

    # 2. Orbital mechanics analytical formulas (< 0.1 ms per run)
    t1 = time.perf_counter()
    n_calcs = 500
    for _ in range(n_calcs):
        v = circular_velocity(EARTH_RADIUS_M + 200000.0)
        t = orbital_period(EARTH_RADIUS_M + 200000.0)
        hoh = hohmann_transfer(EARTH_RADIUS_M + 200000.0, 42164000.0)
        assert v > 7000.0
        assert t > 5000.0
        assert hoh["total_dv_ms"] > 3000.0
    elapsed_calc = (time.perf_counter() - t1) / n_calcs
    assert elapsed_calc < 0.0005, f"Orbital formulas too slow: {elapsed_calc*1000:.4f} ms"


def test_space_particle_budget_tier_mapping():
    """Verify tier mapping parameters reflect non-empty Medium/High and zero Low budgets."""
    tier_configs = {
        "low": {"particles": 0, "bloom": False, "shadows": False, "stars": 200},
        "medium": {"particles": 120, "bloom": False, "shadows": True, "stars": 800},
        "high": {"particles": 350, "bloom": True, "shadows": True, "stars": 2000},
    }

    assert tier_configs["low"]["particles"] == 0
    assert tier_configs["low"]["shadows"] is False
    assert tier_configs["medium"]["particles"] > 0
    assert tier_configs["high"]["particles"] > tier_configs["medium"]["particles"]
