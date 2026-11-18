"""Tests for provenance popovers and reality check integration (P1-T12)."""

import pytest
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from backend.app.main import app

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.mark.asyncio
async def test_provenance_metadata_and_chips_in_frontend():
    """Verify all 4 source chips [Engine], [Game], [Lit], [AI] are defined and wired in UI components."""
    components_js = (REPO_ROOT / "frontend" / "ui" / "components.js").read_text(encoding="utf-8")
    assert "PROVENANCE_METADATA" in components_js
    for chip_type in ["engine", "game", "lit", "ai"]:
        assert chip_type in components_js
    assert "createSourceChip" in components_js
    assert "initProvenancePopovers" in components_js
    assert "showProvenancePopover" in components_js

    components_css = (REPO_ROOT / "frontend" / "ui" / "components.css").read_text(encoding="utf-8")
    assert ".source-chip" in components_css
    assert ".chip-engine" in components_css
    assert ".chip-game" in components_css
    assert ".chip-lit" in components_css
    assert ".chip-ai" in components_css
    assert ".provenance-popover" in components_css


@pytest.mark.asyncio
async def test_reality_check_screen_and_unverified_badges():
    """Verify #screen-reality-check table exists, lists benchmarks, and marks all rows strictly unverified."""
    index_html = (REPO_ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    assert 'id="screen-reality-check"' in index_html
    assert 'class="reality-check-table"' in index_html
    assert 'id="reality-check-tbody"' in index_html

    # Check that rows have "N/A: unverified"
    assert 'status-unverified' in index_html
    assert 'N/A: unverified' in index_html

    # Check all model cards are referenced in the table rows
    required_cards = [
        "/docs/model_cards/pharma_pk.md",
        "/docs/model_cards/pharma_trial.md",
        "/docs/model_cards/pharma_pkpd.md",
        "/docs/model_cards/chem_titration.md",
        "/docs/model_cards/space_orbit.md",
    ]
    for card_url in required_cards:
        assert card_url in index_html, f"Missing model card link {card_url} in reality check table"


@pytest.mark.asyncio
async def test_model_cards_accessible_via_http():
    """Verify all 5 model cards linked from Reality Check serve HTTP 200."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        cards = [
            "pharma_pk.md",
            "pharma_trial.md",
            "pharma_pkpd.md",
            "chem_titration.md",
            "space_orbit.md",
        ]
        for card in cards:
            res = await ac.get(f"/docs/model_cards/{card}")
            assert res.status_code == 200, f"Card {card} failed with status {res.status_code}"
            assert len(res.text) > 100
            assert "Model Card" in res.text


@pytest.mark.asyncio
async def test_hud_readout_source_chips_present():
    """Verify live telemetry readouts include [Engine], [Game], [Lit], and [AI] source chips with accessibility attributes."""
    index_html = (REPO_ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    assert 'data-source-type="engine"' in index_html
    assert 'data-source-type="game"' in index_html
    assert 'data-source-type="lit"' in index_html
    assert 'data-source-type="ai"' in index_html
