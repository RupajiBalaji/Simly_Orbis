"""
Shared test fixtures.

The AsyncClient fixture manually drives the FastAPI lifespan so that
init_db() runs and app.db.database is populated before any test hits it.
"""

from __future__ import annotations

import os

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
    Spin up the full ASGI app (with lifespan) and return an httpx client.

    We drive the lifespan manually via the app's router context manager so
    that init_db() populates _db.database before any request arrives.
    """
    async with app.router.lifespan_context(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac
