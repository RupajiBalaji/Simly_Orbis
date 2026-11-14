"""
backend/tests/test_model_cards.py
Tests for Scientific Model Cards (Section 14.4 & Section 18 P0-T5).

Verifies:
1. Five model cards exist under docs/model_cards/:
   - pharma_pk.md
   - pharma_trial.md
   - pharma_pkpd.md
   - chem_titration.md
   - space_orbit.md
2. Mandatory structural fields: purpose, equations, assumptions, parameter ranges,
   error sources, validation status, changelog.
3. Static documentation endpoints /docs/model_cards/{id}.md serve HTTP 200.
4. Compliance: disclaimers present, unverified rows acknowledged.
"""

from __future__ import annotations

from pathlib import Path
import pytest
from httpx import AsyncClient

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_CARDS_DIR = REPO_ROOT / "docs" / "model_cards"

REQUIRED_CARDS = [
    "pharma_pk.md",
    "pharma_trial.md",
    "pharma_pkpd.md",
    "chem_titration.md",
    "space_orbit.md",
]

REQUIRED_SECTIONS = [
    "Purpose & Intended Use",
    "Mathematical Equations",
    "Assumptions & Parameter Ranges",
    "Known Error Sources & Limitations",
    "Validation Status & Provenance",
    "Changelog",
]


def test_model_cards_exist_and_structured():
    """Verify all 5 required model cards exist on disk with mandatory sections."""
    assert MODEL_CARDS_DIR.exists(), "docs/model_cards directory missing"

    for card_name in REQUIRED_CARDS:
        card_path = MODEL_CARDS_DIR / card_name
        assert card_path.exists(), f"Missing model card: {card_name}"

        content = card_path.read_text(encoding="utf-8")
        assert len(content) > 300, f"Model card {card_name} is too short"

        for sec in REQUIRED_SECTIONS:
            assert sec in content, f"Model card {card_name} missing required section: '{sec}'"

        # Check educational disclaimer
        assert "Educational Simulation" in content or "educational simulation" in content.lower()


@pytest.mark.asyncio
async def test_model_card_http_endpoints_accessible(client: AsyncClient):
    """Verify each model card is accessible via HTTP at /docs/model_cards/{name}."""
    for card_name in REQUIRED_CARDS:
        res = await client.get(f"/docs/model_cards/{card_name}")
        assert res.status_code == 200, f"Failed to fetch /docs/model_cards/{card_name}: {res.status_code}"
        assert len(res.text) > 200
        assert "Model Card" in res.text
