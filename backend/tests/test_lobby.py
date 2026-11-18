"""Tests for Lobby district tiles, waking state, and why locked modal (P1-T4)."""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from pathlib import Path


@pytest.mark.asyncio
async def test_lobby_district_cards_and_tiles():
    """Verify lobby contains district cards, experiment tiles, difficulty badges, and status chips."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/")
        assert res.status_code == 200
        html = res.text

        # Spec Section 4 District cards: Pharma, Chem, Space, Market (locked)
        assert 'id="card-district-pharma"' in html
        assert 'id="card-district-chemistry"' in html
        assert 'id="card-district-space"' in html
        assert 'id="card-district-market"' in html
        assert 'id="card-district-biology"' not in html

        # Experiment tiles with difficulty & time estimate
        assert 'data-exp-id="pk_ward"' in html
        assert 'data-exp-id="dose_lab"' in html
        assert 'data-exp-id="titration_bench"' in html
        assert 'data-exp-id="launch_bench"' in html

        assert 'Oral PK Ward' in html
        assert 'Dose Response Lab' in html
        assert 'Titration Bench' in html
        assert 'Launch &amp; Orbit Bench' in html

        # Difficulty & time metadata
        assert 'Novice' in html
        assert 'Advanced' in html
        assert '⏱️ 5 min' in html
        assert '⏱️ 8 min' in html
        assert '⏱️ 6 min' in html
        assert '⏱️ 7 min' in html

        # Status chips
        assert 'id="status-pk-ward"' in html
        assert 'id="status-dose-lab"' in html
        assert 'id="status-titration"' in html
        assert 'id="status-launch"' in html


@pytest.mark.asyncio
async def test_spec_8_3_start_and_practice_mode_buttons():
    """Verify Spec 8.3 Start and Practice buttons are present for mode selection."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/")
        html = res.text

        assert 'id="btn-start-experiment"' in html
        assert 'id="btn-practice-experiment"' in html
        assert 'Practice (No Score' in html
        assert 'Start Experiment' in html


@pytest.mark.asyncio
async def test_why_locked_modal_and_waking_state():
    """Verify Why Locked modal and Waking Up state elements exist with required content."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/")
        html = res.text

        # Why locked modal
        assert 'id="modal-why-locked"' in html
        assert 'id="why-locked-title"' in html
        assert 'id="why-locked-explanation"' in html
        assert 'id="why-locked-path"' in html
        assert 'id="btn-close-why-locked"' in html
        assert 'id="btn-why-locked-ok"' in html

        # Waking screen
        assert 'id="screen-wakeup"' in html
        assert 'id="wakeup-tip-container"' in html
        assert 'id="wakeup-tip-text"' in html
        assert 'id="wakeup-progress-bar"' in html
        assert 'id="wakeup-dots"' in html
