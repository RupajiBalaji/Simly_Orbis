#!/usr/bin/env python3
"""
Fast non-blocking CI browser smoke check (T8).
Verifies pk_ward and launch_bench at 1366x768 (desktop) and 390x844 (mobile):
- Score: 100
- Safety 100/100
- Primary action button visible
- No onboarding/coachmark/lobby modal visible
Saves screenshots to qa/out/ci_smoke/.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "qa" / "out" / "ci_smoke"


def wait_for_health(url: str, timeout: float = 25.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.5) as resp:
                if resp.status == 200:
                    return
        except Exception:
            pass
        time.sleep(0.3)
    raise RuntimeError(f"Server did not become healthy at {url} within {timeout}s")


def main() -> int:
    from playwright.sync_api import sync_playwright

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    port = 8021
    env = os.environ.copy()
    env["ENVIRONMENT"] = "development"
    env["MONGODB_URI"] = ""
    env["QA_MODE"] = "true"

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--app-dir", str(REPO_ROOT / "backend"), "--host", "127.0.0.1", "--port", str(port)],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )

    try:
        wait_for_health(f"http://127.0.0.1:{port}/api/health")
        cases = [
            ("pk_ward", 1366, 768),
            ("pk_ward", 390, 844),
            ("launch_bench", 1366, 768),
            ("launch_bench", 390, 844),
        ]
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            for exp_id, w, h in cases:
                ctx = browser.new_context(viewport={"width": w, "height": h})
                ctx.add_init_script("""
                    localStorage.setItem('orbis_coachmarks_seen', 'true');
                    localStorage.setItem('orbis_tutorial_completed', 'true');
                    localStorage.setItem('orbis_onboarding_completed', 'true');
                """)
                page = ctx.new_page()
                page.goto(f"http://127.0.0.1:{port}/#/lab?exp={exp_id}", wait_until="domcontentloaded")
                page.wait_for_selector("#lab-hud:not(.hidden)", timeout=20000)
                page.wait_for_function("() => Boolean(window.state?.session?.session_id)", timeout=20000)
                page.wait_for_selector("#task-btn-primary", state="visible", timeout=15000)

                result = page.evaluate("""() => {
                    const score = document.getElementById('hud-safety-score')?.textContent?.trim();
                    const safety = document.getElementById('hud-safety-status')?.textContent?.trim();
                    const primaryBtn = document.getElementById('task-btn-primary');
                    const primaryVisible = Boolean(primaryBtn && primaryBtn.offsetWidth > 0 && primaryBtn.offsetHeight > 0);
                    const modalVisible = ['#modal-onboarding', '#hud-coachmarks-overlay', '#screen-lobby'].some(sel => {
                        const el = document.querySelector(sel);
                        if (!el || el.classList.contains('hidden')) return false;
                        const st = window.getComputedStyle(el);
                        return st.display !== 'none' && st.visibility !== 'hidden';
                    });
                    return { score, safety, primaryVisible, modalVisible };
                }""")
                assert result["score"] == "Score: 100", f"{exp_id} {w}x{h}: {result}"
                assert result["safety"] == "Safety 100/100", f"{exp_id} {w}x{h}: {result}"
                assert result["primaryVisible"], f"{exp_id} {w}x{h}: primary button not visible"
                assert not result["modalVisible"], f"{exp_id} {w}x{h}: modal visible"

                shot_path = OUT_DIR / f"smoke_{exp_id}_{w}x{h}.png"
                page.screenshot(path=str(shot_path))
                print(f"[CI-SMOKE] PASS {exp_id} ({w}x{h}) -> {shot_path.name}")
                ctx.close()
            browser.close()
        return 0
    finally:
        proc.terminate()
        proc.wait(timeout=10)


if __name__ == "__main__":
    raise SystemExit(main())
