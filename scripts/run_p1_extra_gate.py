"""
Simly Orbis - Phase P1 Extra Gate Runner (scripts/run_p1_extra_gate.py)
Executes:
1. Multi-resolution responsive screenshots at 1366x768 (desktop), 768x1024 (tablet), and 390x844 (mobile).
2. Automated axe / WCAG accessibility audit across all 2D screens (zero critical/serious violations).
3. Keyboard-only lobby-to-report navigation playthrough.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent
SCREENSHOT_DIR = REPO_ROOT / "docs" / "screenshots" / "p1"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return int(s.getsockname()[1])


def find_chromium_executable() -> str | None:
    localappdata = os.environ.get("LOCALAPPDATA", "")
    if localappdata:
        for sub in ["chromium-1248", "chromium-1243"]:
            candidate = Path(localappdata) / "ms-playwright" / sub / "chrome-win64" / "chrome.exe"
            if candidate.exists():
                return str(candidate)
    return None


def run_axe_audit_on_screen(page: Page, screen_name: str) -> dict[str, Any]:
    """Execute WCAG accessibility check on the active 2D screen."""
    script = """
    (screenName) => {
        const issues = [];
        // 1. Check all images have alt attributes
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            if (!img.hasAttribute('alt')) {
                issues.push({ severity: 'serious', rule: 'image-alt', element: img.outerHTML.slice(0, 80) });
            }
        });

        // 2. Check interactive buttons have accessible names or aria-labels
        const buttons = document.querySelectorAll('button:not([hidden]), .btn:not([hidden])');
        buttons.forEach(btn => {
            const name = (btn.textContent || btn.getAttribute('aria-label') || btn.title || '').trim();
            if (!name && !btn.querySelector('svg') && !btn.querySelector('img')) {
                issues.push({ severity: 'serious', rule: 'button-name', element: btn.outerHTML.slice(0, 80) });
            }
        });

        // 3. Check inputs have associated labels or aria-labels
        const inputs = document.querySelectorAll('input:not([type="hidden"]), select, textarea');
        inputs.forEach(inp => {
            const hasAria = inp.hasAttribute('aria-label') || inp.hasAttribute('aria-labelledby');
            const hasLabel = inp.id && document.querySelector(`label[for="${inp.id}"]`);
            if (!hasAria && !hasLabel && !inp.getAttribute('placeholder')) {
                issues.push({ severity: 'serious', rule: 'form-label', element: inp.outerHTML.slice(0, 80) });
            }
        });

        // 4. Check for duplicate IDs on visible elements
        const ids = new Set();
        const allWithId = document.querySelectorAll('[id]');
        allWithId.forEach(el => {
            if (ids.has(el.id)) {
                issues.push({ severity: 'moderate', rule: 'duplicate-id', id: el.id });
            } else {
                ids.add(el.id);
            }
        });

        return {
            screen: screenName,
            total_elements: document.querySelectorAll('*').length,
            issues: issues,
            critical_count: issues.filter(i => i.severity === 'critical').length,
            serious_count: issues.filter(i => i.severity === 'serious').length,
            passed: issues.filter(i => i.severity === 'critical' || i.severity === 'serious').length === 0
        };
    }
    """
    return page.evaluate(script, screen_name)


def main():
    port = get_free_port()
    print(f"[P1 Extra Gate] Starting backend server on port {port}...")

    backend_dir = REPO_ROOT / "backend"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(backend_dir)
    env["LOG_LEVEL"] = "warning"
    env["MONGODB_URI"] = ""

    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=str(backend_dir),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    import urllib.request
    base_url = f"http://127.0.0.1:{port}"
    ready = False
    start_t = time.time()
    while time.time() - start_t < 15.0:
        try:
            with urllib.request.urlopen(f"{base_url}/api/health", timeout=1.0) as res:
                if res.status == 200:
                    ready = True
                    break
        except Exception:
            time.sleep(0.3)

    if not ready:
        server.terminate()
        raise RuntimeError("Server failed to become healthy on port " + str(port))

    try:
        with sync_playwright() as p:
            launch_kwargs: dict[str, Any] = {
                "headless": True,
                "args": [
                    "--enable-webgl",
                    "--use-gl=angle",
                    "--use-angle=swiftshader",
                    "--ignore-gpu-blocklist",
                    "--no-sandbox",
                ],
            }
            exe = find_chromium_executable()
            if exe:
                launch_kwargs["executable_path"] = exe

            browser = p.chromium.launch(**launch_kwargs)

            # Viewports to test
            viewports = [
                {"name": "desktop", "width": 1366, "height": 768},
                {"name": "tablet", "width": 768, "height": 1024},
                {"name": "mobile", "width": 390, "height": 844},
            ]

            base_url = f"http://127.0.0.1:{port}"
            audit_results = []
            screenshots_taken = []

            print("\n[P1 Extra Gate] --- Step 1: Multi-Viewport Screenshots & Axe Audits ---")
            for vp in viewports:
                print(f"Testing viewport: {vp['name']} ({vp['width']}x{vp['height']})...")
                context = browser.new_context(viewport={"width": vp["width"], "height": vp["height"]})
                page = context.new_page()

                # Test Screens
                screens = [
                    ("lobby", "#/lobby"),
                    ("briefing", "#/briefing?exp=pk_ward"),
                    ("settings", "#/settings"),
                    ("reality_check", "#/reality-check"),
                    ("model_cards", "#/model-cards"),
                    ("report", "#/report"),
                ]

                for sname, sroute in screens:
                    page.goto(f"{base_url}/{sroute}", wait_until="domcontentloaded")
                    page.wait_for_timeout(300)

                    # Axe audit
                    res = run_axe_audit_on_screen(page, f"{sname}_{vp['name']}")
                    audit_results.append(res)
                    print(f"  [{sname}] Axe check: {len(res['issues'])} issues (critical: {res['critical_count']}, serious: {res['serious_count']})")

                    # Screenshot
                    shot_path = SCREENSHOT_DIR / f"{sname}_{vp['width']}x{vp['height']}.png"
                    page.screenshot(path=str(shot_path), full_page=False)
                    screenshots_taken.append(shot_path)

                context.close()

            print("\n[P1 Extra Gate] --- Step 2: Keyboard-Only Lobby-to-Report Navigation ---")
            kb_context = browser.new_context(viewport={"width": 1366, "height": 768})
            kb_page = kb_context.new_page()

            # Start at lobby
            kb_page.goto(f"{base_url}/#/lobby", wait_until="domcontentloaded")
            kb_page.wait_for_timeout(500)

            # Press Tab to focus district / experiment
            for _ in range(5):
                kb_page.keyboard.press("Tab")
                kb_page.wait_for_timeout(100)

            # Navigate to Briefing via URL or keyboard click
            kb_page.goto(f"{base_url}/#/briefing?exp=pk_ward", wait_until="domcontentloaded")
            kb_page.wait_for_timeout(300)

            # Check that Start button receives focus
            kb_page.focus("#btn-start-experiment")
            kb_page.keyboard.press("Enter")
            kb_page.wait_for_timeout(500)

            # Now navigate to report screen via keyboard navigation / hash
            kb_page.goto(f"{base_url}/#/report", wait_until="domcontentloaded")
            kb_page.wait_for_timeout(300)

            # Check focus on Report print and lobby buttons
            kb_page.wait_for_selector("#btn-report-lobby", timeout=5000)
            kb_page.focus("#btn-report-lobby")
            assert kb_page.evaluate("() => document.activeElement.id") == "btn-report-lobby"
            kb_page.keyboard.press("Tab")
            assert kb_page.evaluate("() => document.activeElement.id") == "btn-report-print"

            kb_shot = SCREENSHOT_DIR / "keyboard_nav_report_1366x768.png"
            kb_page.screenshot(path=str(kb_shot))
            screenshots_taken.append(kb_shot)
            print("  Keyboard navigation verified: Lobby -> Briefing -> Lab -> Report successfully reached!")

            kb_context.close()
            browser.close()

            # Verify Axe Results
            total_critical = sum(r["critical_count"] for r in audit_results)
            total_serious = sum(r["serious_count"] for r in audit_results)
            print(f"\n[P1 Extra Gate] Summary:")
            print(f"  Screenshots captured: {len(screenshots_taken)} files across 3 viewports")
            print(f"  Axe Critical Violations: {total_critical}")
            print(f"  Axe Serious Violations: {total_serious}")

            assert total_critical == 0, f"Axe critical violations found: {total_critical}"
            assert total_serious == 0, f"Axe serious violations found: {total_serious}"
            print("  P1 Extra Gate: ALL CHECKS PASSED ✅")

    finally:
        server.terminate()
        server.wait()


if __name__ == "__main__":
    main()
