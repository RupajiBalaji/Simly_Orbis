"""
Shared test fixtures.

The AsyncClient fixture manually drives the FastAPI lifespan so that
init_db() runs and app.db.database is populated before any test hits it.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure repo root and backend directory are in sys.path when pytest is invoked bare from repo root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = Path(__file__).resolve().parent.parent
for p in (REPO_ROOT, BACKEND_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Force memory mode before any app module is imported.
os.environ.setdefault("MONGODB_URI", "")
os.environ.setdefault("DB_NAME", "simly_orbis_test")
os.environ["ENVIRONMENT"] = "test"

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


def pytest_addoption(parser):
    parser.addoption(
        "--browser",
        action="store_true",
        default=False,
        help="Run browser-dependent end-to-end tests requiring Playwright",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "browser: mark test as requiring a real browser or Playwright"
    )


def pytest_collection_modifyitems(config, items):
    run_browser = config.getoption("--browser") or os.environ.get("RUN_BROWSER_TESTS", "").lower() in ("1", "true")
    if not run_browser:
        skip_browser = pytest.mark.skip(reason="requires --browser flag or RUN_BROWSER_TESTS=1")
        for item in items:
            if "browser" in item.keywords:
                item.add_marker(skip_browser)

from app.main import app
import app.db as _db
from app.core.registry import _REGISTRY, register
from app.modules.pharma_pk import PharmaPKModule
from app.modules.chem_titration import ChemTitrationModule
from app.modules.pharma_trial import PharmaTrialModule


@pytest_asyncio.fixture
async def client():
    """
    Spin up the full ASGI app and return an httpx client.
    Ensures init_db() populates _db.database before any request arrives.
    """
    await _db.init_db()
    _REGISTRY.clear()
    register(PharmaPKModule())
    register(ChemTitrationModule())
    register(PharmaTrialModule())
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
