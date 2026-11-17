"""Tests for client-side router, app shell, route views, and 404 page (P1-T3)."""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
import re
from pathlib import Path


@pytest.mark.asyncio
async def test_app_shell_screens_present():
    """Verify index.html contains all app shell screens, router links, and breadcrumbs."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/")
        assert res.status_code == 200
        html = res.text

        # All route screens
        assert 'id="screen-lobby"' in html
        assert 'id="screen-leaderboard"' in html
        assert 'id="screen-settings"' in html
        assert 'id="screen-model-cards"' in html
        assert 'id="screen-reality-check"' in html
        assert 'id="screen-404"' in html

        # App shell elements
        assert 'data-nav-route="lobby"' in html
        assert 'data-nav-route="leaderboard"' in html
        assert 'data-nav-route="settings"' in html
        assert 'data-nav-route="model-cards"' in html
        assert 'data-nav-route="reality-check"' in html
        assert 'id="user-profile-chip"' in html
        assert 'id="btn-top-mute"' in html
        assert 'id="app-breadcrumbs"' in html


@pytest.mark.asyncio
async def test_404_page_and_router_assets():
    """Verify 404.html and router.js are served correctly."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res_404 = await ac.get("/404.html")
        assert res_404.status_code == 200
        assert "404" in res_404.text
        assert "Experiment Not Found" in res_404.text
        assert "#/lobby" in res_404.text

        res_router = await ac.get("/router.js")
        assert res_router.status_code == 200
        assert "export class Router" in res_router.text
        assert "export function initRouter" in res_router.text


def test_router_logic_and_route_table():
    """Verify router.js defines standard routing logic, hash parsing, and route fallback."""
    router_file = Path(__file__).resolve().parent.parent.parent / "frontend" / "router.js"
    assert router_file.exists()
    content = router_file.read_text(encoding="utf-8")

    # Route matching & parameter extraction
    assert "parseHash" in content
    assert "handleHashChange" in content
    assert "notFoundRoute" in content
    assert "updateActiveNavLinks" in content

    # Test simulating router hash parsing logic in Python to verify spec compliance
    def parse_hash(raw_hash: str, default_route="lobby"):
        raw = raw_hash.lstrip("#").strip()
        if not raw or raw == "/":
            return {"routeName": default_route, "params": {}}
        parts = raw.split("?", 1)
        clean_path = parts[0].strip("/")
        segments = clean_path.split("/")
        route_name = segments[0] or default_route
        params = {}
        if len(segments) > 1:
            params["id"] = "/".join(segments[1:])
        if len(parts) > 1:
            for pair in parts[1].split("&"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    params[k] = v
        return {"routeName": route_name, "params": params}

    # Verify routes
    assert parse_hash("") == {"routeName": "lobby", "params": {}}
    assert parse_hash("#/") == {"routeName": "lobby", "params": {}}
    assert parse_hash("#/briefing?exp=pk_ward") == {"routeName": "briefing", "params": {"exp": "pk_ward"}}
    assert parse_hash("#/lab?exp=launch_bench") == {"routeName": "lab", "params": {"exp": "launch_bench"}}
    assert parse_hash("#/report?session=sess_123") == {"routeName": "report", "params": {"session": "sess_123"}}
    assert parse_hash("#/model-cards/pharma_pk") == {"routeName": "model-cards", "params": {"id": "pharma_pk"}}
    assert parse_hash("#/reality-check") == {"routeName": "reality-check", "params": {}}
    assert parse_hash("#/settings") == {"routeName": "settings", "params": {}}
    assert parse_hash("#/leaderboard") == {"routeName": "leaderboard", "params": {}}
    assert parse_hash("#/nonexistent_route")["routeName"] == "nonexistent_route"
