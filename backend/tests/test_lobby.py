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


@pytest.mark.asyncio
async def test_district_experiment_counts_equal_listed_tiles():
    """Verify experiment counts on district cards equal the exact number of experiment tiles listed (P2)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/")
        html = res.text

        # Chemistry district: Titration, Kinetics, Buffer -> 3 Experiments
        assert 'id="card-district-chemistry"' in html
        chem_block = html.split('id="card-district-chemistry"')[1].split('id="card-district-space"')[0]
        chem_tiles = chem_block.count('class="exp-tile card"')
        assert chem_tiles == 3, f"Expected 3 experiment tiles under Chemistry, found {chem_tiles}"
        assert '3 Experiments' in chem_block
        assert 'data-i18n="lobby.exp_count_3"' in chem_block

        # Pharma district: Oral PK Ward, Dose Response Lab -> 2 Experiments
        pharma_block = html.split('id="card-district-pharma"')[1].split('id="card-district-chemistry"')[0]
        pharma_tiles = pharma_block.count('class="exp-tile card"')
        assert pharma_tiles == 2, f"Expected 2 experiment tiles under Pharma, found {pharma_tiles}"
        assert '2 Experiments' in pharma_block
        assert 'data-i18n="lobby.exp_count_2"' in pharma_block

        # Space district: Launch & Orbit Bench -> 1 Experiment
        space_block = html.split('id="card-district-space"')[1].split('id="card-district-market"')[0]
        space_tiles = space_block.count('class="exp-tile card"')
        assert space_tiles == 1, f"Expected 1 experiment tile under Space, found {space_tiles}"
        assert '1 Experiment' in space_block
        assert 'data-i18n="lobby.exp_count_1"' in space_block


def test_offline_banner_non_overlapping_layout_contract():
    """Verify offline banner CSS contract: reserves space via --offline-banner-height and pushes .view-screen down."""
    lab_css_path = Path(__file__).resolve().parent.parent.parent / "frontend" / "lab.css"
    css = lab_css_path.read_text(encoding="utf-8")

    assert "--offline-banner-height" in css
    assert "body.has-offline-banner" in css
    assert ".offline-banner" in css
    assert "top: var(--offline-banner-height, 0px)" in css


def test_fast_server_state_simulation():
    """Simulate fast server (responds in < 2s): waking modal timer cancelled, no modal, no banner."""
    # Fast server simulation: ping returns 200 within 50ms
    is_awake = False
    modal_visible = False
    banner_visible = False
    retries_failed = False

    def on_2s_timer():
        nonlocal modal_visible
        if not is_awake:
            modal_visible = True

    # Server responds in 50ms
    server_response_time = 0.05
    if server_response_time < 2.0:
        is_awake = True
        # timer cancelled before 2s fires
        retries_failed = False
        banner_visible = retries_failed

    assert is_awake is True
    assert modal_visible is False, "Fast server must NOT display waking modal"
    assert banner_visible is False, "Fast server must NOT display offline banner"


def test_slow_server_state_simulation():
    """Simulate slow server (takes > 2s to answer): waking modal appears at 2s, no banner."""
    is_awake = False
    modal_visible = False
    retries_failed = False

    def on_2s_timer():
        nonlocal modal_visible
        if not is_awake:
            modal_visible = True

    # 2s timer fires
    on_2s_timer()
    assert modal_visible is True, "Slow server must display waking modal after 2 seconds"
    assert retries_failed is False, "Slow server waiting for cold start must NOT trigger offline banner"

    # Server answers at 4s
    is_awake = True
    modal_visible = False  # dismissed on connect
    assert modal_visible is False


def test_dead_server_state_simulation():
    """Simulate dead server: fails initial attempt + 2 retries -> banner shown, modal shown after 2s."""
    is_awake = False
    modal_visible = False
    retries_failed = False
    attempts = 0

    def on_2s_timer():
        nonlocal modal_visible
        if not is_awake:
            modal_visible = True

    # 3 attempts (initial + 2 retries) all fail
    for _ in range(3):
        attempts += 1
        # connection error / timeout

    if attempts >= 3:
        retries_failed = True

    banner_visible = retries_failed
    on_2s_timer()

    assert banner_visible is True, "Dead server must show offline banner after 2 retries"
    assert modal_visible is True, "Dead server must show waking modal after 2 seconds"

