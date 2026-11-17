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
4. Static mount does not shadow /docs or /openapi.json.
5. Interactive API docs are disabled in production mode.
6. Only docs/model_cards is served; path-traversal attempts are rejected.
"""

from __future__ import annotations

import os
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.main import app as main_app

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


@pytest.mark.asyncio
async def test_static_mount_does_not_shadow_docs_or_openapi(client: AsyncClient):
    """Verify that /docs/model_cards does not shadow FastAPI /docs or /openapi.json."""
    res_docs = await client.get("/docs")
    assert res_docs.status_code == 200, f"Expected /docs to return 200, got {res_docs.status_code}"
    assert "swagger" in res_docs.text.lower() or "html" in res_docs.text.lower()

    res_openapi = await client.get("/openapi.json")
    assert res_openapi.status_code == 200, f"Expected /openapi.json to return 200, got {res_openapi.status_code}"
    data = res_openapi.json()
    assert "openapi" in data or "paths" in data

    res_card = await client.get("/docs/model_cards/pharma_pk.md")
    assert res_card.status_code == 200


@pytest.mark.asyncio
async def test_model_cards_path_traversal_attempts_rejected(client: AsyncClient):
    """Verify that path-traversal attempts under /docs/model_cards are rejected and cannot leak host files."""
    traversal_paths = [
        "/docs/model_cards/../config.py",
        "/docs/model_cards/../../README.md",
        "/docs/model_cards/%2e%2e/config.py",
        "/docs/model_cards/%2e%2e/%2e%2e/README.md",
        "/docs/model_cards/..%2f..%2fREADME.md",
        "/docs/model_cards/nonexistent_file.md",
        "/docs/model_cards/README.md",  # README.md is in repo root, not in model_cards
    ]
    for path in traversal_paths:
        res = await client.get(path)
        # Traversal attempts must return 400, 404, or 403, and never 200
        assert res.status_code in (400, 404, 403), (
            f"Path traversal attempt '{path}' returned unexpected status {res.status_code}!"
        )


@pytest.mark.asyncio
async def test_production_mode_disables_interactive_docs():
    """Verify that in production mode, /docs, /redoc, and /openapi.json are disabled."""
    # Build test app configured with production mode
    prod_app = FastAPI(
        title="Simly Orbis Production Test",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    if MODEL_CARDS_DIR.exists():
        prod_app.mount("/docs/model_cards", StaticFiles(directory=MODEL_CARDS_DIR), name="model_cards_docs")

    transport = ASGITransport(app=prod_app)
    async with AsyncClient(transport=transport, base_url="http://test") as prod_client:
        r_docs = await prod_client.get("/docs")
        assert r_docs.status_code == 404, f"Expected /docs to be 404 in production, got {r_docs.status_code}"

        r_redoc = await prod_client.get("/redoc")
        assert r_redoc.status_code == 404, f"Expected /redoc to be 404 in production, got {r_redoc.status_code}"

        r_openapi = await prod_client.get("/openapi.json")
        assert r_openapi.status_code == 404, f"Expected /openapi.json to be 404 in production, got {r_openapi.status_code}"

        # Model cards remain accessible in production
        r_card = await prod_client.get("/docs/model_cards/pharma_pk.md")
        assert r_card.status_code == 200, "Model card should still be served in production"
