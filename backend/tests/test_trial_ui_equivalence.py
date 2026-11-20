"""
Tests for Virtual Trial UI (P4-T2).

ACCEPT Criterion:
- Crowd gallery rendered with color and icons.
- Distribution charts rendered.
- Deterministic code-written insight sentence.
- CSV export button available.
- Label: 'virtual population, not a clinical trial'.
- ACCEPT: DOM values equal API values.
"""

from __future__ import annotations

import os
from pathlib import Path
import pytest
import uvicorn
import threading
import time
import socket

from app.main import app


def get_browser_launch_kwargs():
    kwargs = {
        "headless": True,
        "args": [
            "--enable-webgl",
            "--use-gl=angle",
            "--use-angle=swiftshader",
            "--ignore-gpu-blocklist",
            "--no-sandbox",
        ],
    }
    localappdata = os.environ.get("LOCALAPPDATA", "")
    if localappdata:
        for sub in ["chromium-1248", "chromium-1243"]:
            candidate = Path(localappdata) / "ms-playwright" / sub / "chrome-win64" / "chrome.exe"
            if candidate.exists():
                kwargs["executable_path"] = str(candidate)
                break
    return kwargs


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def live_server():
    port = get_free_port()
    config = uvicorn.Config(app=app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    time.sleep(1.0)
    base_url = f"http://127.0.0.1:{port}"
    yield base_url
    server.should_exit = True
    thread.join(timeout=2.0)


@pytest.mark.browser
def test_trial_ui_dom_equals_api(live_server):
    """ACCEPT: DOM values strictly equal API values in Virtual Trial UI."""
    pw = pytest.importorskip("playwright.sync_api")
    sync_playwright = pw.sync_playwright
    launch_kwargs = get_browser_launch_kwargs()
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        page = browser.new_page(viewport={"width": 1280, "height": 720})

        # Navigate to pk_ward
        page.goto(f"{live_server}/#/lab?exp=pk_ward")
        page.wait_for_selector("#virtual-trial-panel", state="attached", timeout=15000)

        # Open trial panel
        page.evaluate("() => { if (window.trialPanel) window.trialPanel.open(); }")
        page.wait_for_selector("#virtual-trial-panel:not(.hidden)", timeout=8000)

        # 1. Assert 'virtual population, not a clinical trial' label exists
        label_text = page.inner_text("#trial-disclaimer-label").strip().lower()
        assert label_text == "virtual population, not a clinical trial"

        # 2. Assert CSV export button exists
        assert page.is_visible("#btn-export-trial-csv")

        # 3. Trigger trial simulation
        page.evaluate("() => window.trialPanel.runTrialSimulation()")
        page.wait_for_selector("#trial-results-area:not(.hidden)", timeout=8000)
        page.wait_for_timeout(500)

        # 4. Extract API results from window.trialPanel.lastResult
        api_data = page.evaluate("() => window.trialPanel.lastResult")
        assert api_data is not None
        summary = api_data.get("summary", {})
        patients = api_data.get("patients", [])

        # 5. Extract DOM values
        dom_in_range = page.inner_text("#stat-pct-in-range").strip()
        dom_toxic = page.inner_text("#stat-pct-toxic").strip()
        dom_sub = page.inner_text("#stat-pct-sub").strip()
        dom_peak = page.inner_text("#stat-mean-peak").strip()
        dom_verdict = page.inner_text("#trial-verdict-text").strip()
        dom_total = page.inner_text("#cnt-total").strip()

        # 6. Strict ACCEPT assertion: DOM values equal API values
        api_target = summary.get("pct_target", summary.get("pct_in_range"))
        api_above = summary.get("pct_above", summary.get("pct_toxic"))
        api_below = summary.get("pct_below", summary.get("pct_subtherapeutic"))
        api_peak = summary.get("cmax_dist", {}).get("median", summary.get("mean_peak"))
        api_insight = summary.get("insight", summary.get("verdict"))

        assert dom_in_range == f"{api_target}%"
        assert dom_toxic == f"{api_above}%"
        assert dom_sub == f"{api_below}%"
        assert dom_peak == f"{api_peak:.1f} mg/L"
        assert dom_verdict == api_insight
        assert dom_total == str(summary.get("n_patients"))

        # 7. Assert crowd gallery rendered patient items
        gallery_cards = page.query_selector_all("#trial-crowd-grid .patient-pill")
        assert len(gallery_cards) > 0
        assert len(gallery_cards) <= 32

        browser.close()
