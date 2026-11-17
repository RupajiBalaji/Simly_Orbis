"""Tests for i18n localization scaffolding, dictionary, and lint script (P1-T8)."""

import pytest
import subprocess
import json
import sys
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


def test_i18n_lint_script_passes():
    """Verify scripts/lint_i18n.py executes cleanly and returns exit code 0."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    lint_script = repo_root / "scripts" / "lint_i18n.py"
    assert lint_script.exists()

    res = subprocess.run([sys.executable, str(lint_script)], capture_output=True, text=True)
    assert res.returncode == 0, f"lint_i18n.py failed: {res.stdout}\n{res.stderr}"
    assert "PASS: i18n dictionary and template lint succeeded" in res.stdout


@pytest.mark.asyncio
async def test_locales_served_via_static_routes():
    """Verify frontend/locales JSON files are served over HTTP 200."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res_en = await ac.get("/locales/en.json")
        assert res_en.status_code == 200
        en_dict = res_en.json()
        assert "common" in en_dict
        assert en_dict["common"]["app_title"] == "ORBIS LAB"

        res_es = await ac.get("/locales/es.json")
        assert res_es.status_code == 200
        es_dict = res_es.json()
        assert "common" in es_dict
        assert "Volver al Vestíbulo" in es_dict["common"]["back_to_lobby"]


def test_t_helper_logic_simulation():
    """Verify translation helper resolution, parameter interpolation, and fallbacks."""
    en_dict = {
        "common": {"greeting": "Hello, {name}!", "score": "Score: {pts} / {max}"},
        "errors": {"not_found": "Resource not found"}
    }
    es_dict = {
        "common": {"greeting": "¡Hola, {name}!"}
    }

    def simulate_t(dict_current, dict_en, key, params=None):
        params = params or {}
        parts = key.split(".")
        
        # Current dict
        val = dict_current
        for p in parts:
            if isinstance(val, dict) and p in val:
                val = val[p]
            else:
                val = None
                break
        
        # Fallback to EN
        if val is None:
            val = dict_en
            for p in parts:
                if isinstance(val, dict) and p in val:
                    val = val[p]
                else:
                    val = None
                    break
        
        if val is None:
            return key
            
        for k, v in params.items():
            val = val.replace(f"{{{k}}}", str(v))
        return val

    # Spanish with interpolation
    assert simulate_t(es_dict, en_dict, "common.greeting", {"name": "Alex"}) == "¡Hola, Alex!"

    # Fallback to English when key missing in Spanish
    assert simulate_t(es_dict, en_dict, "common.score", {"pts": 85, "max": 100}) == "Score: 85 / 100"
    assert simulate_t(es_dict, en_dict, "errors.not_found") == "Resource not found"

    # Missing key in both falls back to raw key
    assert simulate_t(es_dict, en_dict, "unknown.nested.key") == "unknown.nested.key"
