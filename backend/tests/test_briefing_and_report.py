"""Tests for experiment briefings, report screens, and print stylesheet (P1-T11)."""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from pathlib import Path


@pytest.mark.asyncio
async def test_all_four_experiments_load_via_api():
    """Verify all 4 required experiments exist and return valid definitions via API."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for exp_id in ["pk_ward", "titration_bench", "launch_bench", "dose_lab"]:
            res = await ac.get(f"/api/lab/experiments/{exp_id}")
            assert res.status_code == 200, f"Experiment {exp_id} failed to load: {res.text}"
            data = res.json()
            assert data["id"] == exp_id
            assert "title" in data
            assert "district" in data
            assert len(data.get("learning_goals", [])) > 0
            assert isinstance(data.get("required_ppe", []), list)


@pytest.mark.asyncio
async def test_briefing_screen_elements_in_html():
    """Verify briefing screen includes equipment list, rules list, scoring rubric, and practice mode."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/")
        assert res.status_code == 200
        html = res.text

        # Briefing screen elements
        assert 'id="screen-brief"' in html
        assert 'id="brief-title"' in html
        assert 'id="brief-district"' in html
        assert 'id="brief-description"' in html
        assert 'id="brief-learning-goals"' in html
        assert 'id="brief-equipment-list"' in html
        assert 'id="brief-rules-list"' in html
        assert 'id="brief-scoring-rubric"' in html
        assert 'id="brief-ppe-bar"' in html
        assert 'id="brief-practice-mode"' in html
        assert 'id="btn-start-experiment"' in html


def test_report_js_empty_violations_and_export():
    """Verify report.js contains the exact empty violations text, print button, and retry logic."""
    report_js = Path(__file__).resolve().parent.parent.parent / "frontend" / "lab" / "game" / "report.js"
    assert report_js.exists()
    content = report_js.read_text(encoding="utf-8")

    # Empty violations state string per spec
    assert "Zero safety violations -- exemplary protocol discipline!" in content

    # Buttons
    assert 'id="btn-report-print"' in content
    assert 'id="btn-report-lobby"' in content
    assert 'id="btn-report-replay"' in content
    assert "window.print()" in content


def test_print_stylesheet_in_lab_css():
    """Verify lab.css includes @media print rules with hidden interactive controls and white background."""
    lab_css = Path(__file__).resolve().parent.parent.parent / "frontend" / "lab.css"
    assert lab_css.exists()
    content = lab_css.read_text(encoding="utf-8")

    assert "@media print" in content
    assert "#screen-report" in content
    assert "display: none !important" in content
    assert "page-break-inside: avoid" in content
