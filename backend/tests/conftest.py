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

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
import app.db as _db


@pytest_asyncio.fixture
async def client():
    """
    Spin up the full ASGI app and return an httpx client.
    Ensures init_db() populates _db.database before any request arrives.
    """
    await _db.init_db()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
