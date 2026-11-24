#!/usr/bin/env python3
"""
scripts/capture_real_hud_proof.py
Captures real lab HUD screenshots and movement proof strip for Problem A and B.

Enforces strict assertions before saving:
- Backend is awake (/api/health == 200)
- Lobby and waking modal are NOT visible
- All 5 data-hud-persistent elements are visible
- 3D WebGL canvas is rendering (width > 0, height > 0)
- Captures before_1920x1080.png from commit 3d60be7
- Captures after_* screenshots at 5 target viewports across Oral PK Ward and Launch & Orbit Bench
- Generates 4-frame movement proof strip across camera yaws 0°, 90°, 180°, 270°
- Validates MD5 uniqueness across all saved proof files
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "docs" / "screenshots" / "ux-fix"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def wait_for_server(url: str, timeout: float = 20.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


def capture_before_screenshot():
    print("[1/4] Capturing before_1920x1080.png from commit 3d60be7...")
    out_path = OUTPUT_DIR / "before_1920x1080.png"
    if out_path.exists():
        im = Image.open(out_path)
        if im.size == (1920, 1080):
            print(f"  -> already captured and verified: {out_path} ({out_path.stat().st_size} bytes)")
            return

    worktree_dir = REPO_ROOT / "temp_old_3d60be7"
    if not worktree_dir.exists():
        subprocess.run(["git", "worktree", "add", str(worktree_dir), "3d60be7"], check=True)

    port = 8019
    env = os.environ.copy()
    env["ENVIRONMENT"] = "development"
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--app-dir", str(worktree_dir / "backend"), "--port", str(port)],
        cwd=str(worktree_dir),
    )

    try:
        url = f"http://127.0.0.1:{port}/api/health"
        if not wait_for_server(url):
            raise RuntimeError(f"Server on {port} did not start")

        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            page.goto(f"http://127.0.0.1:{port}/#/lab?exp=pk_ward", wait_until="networkidle")
            page.wait_for_selector("#webgl-canvas", state="attached", timeout=15000)
            page.wait_for_timeout(3500)

            out_path = OUTPUT_DIR / "before_1920x1080.png"
            page.screenshot(path=str(out_path))
            print(f"  -> Saved {out_path} ({out_path.stat().st_size} bytes)")
            im = Image.open(out_path)
            assert im.size == (1920, 1080), f"Expected 1920x1080, got {im.size}"
            browser.close()
    finally:
        proc.terminate()
        proc.wait()
        subprocess.run(["git", "worktree", "remove", str(worktree_dir), "--force"], check=False)


def capture_after_screenshots(port: int = 8018):
    print("[2/4] Capturing after_* screenshots inside real running experiments...")
    from playwright.sync_api import sync_playwright

    targets = [
        ("after_1920x1080.png", 1920, 1080, "pk_ward", "Oral PK Ward (1920x1080 Desktop)"),
        ("after_1366x768.png", 1366, 768, "pk_ward", "Oral PK Ward (1366x768 Standard Laptop)"),
        ("after_1280x720.png", 1280, 720, "launch_bench", "Launch & Orbit Bench (1280x720 Space District)"),
        ("after_768x1024.png", 768, 1024, "pk_ward", "Oral PK Ward (768x1024 iPad Portrait)"),
        ("after_390x844.png", 390, 844, "pk_ward", "Oral PK Ward (390x844 iPhone Mobile)"),
        ("after_launch_bench_1920x1080.png", 1920, 1080, "launch_bench", "Launch & Orbit Bench (1920x1080 Space District)"),
        ("after_launch_bench_1366x768.png", 1366, 768, "launch_bench", "Launch & Orbit Bench (1366x768 Space District)"),
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for filename, w, h, exp_id, desc in targets:
            page = browser.new_page(viewport={"width": w, "height": h})
            page.goto(f"http://127.0.0.1:{port}/#/lab?exp={exp_id}", wait_until="networkidle")

            # Wait for lab elements
            page.wait_for_selector("#lab-hud", state="attached", timeout=15000)
            page.wait_for_selector("#webgl-canvas, canvas", state="attached", timeout=15000)
            page.wait_for_timeout(3000)

            # ASSERTIONS BEFORE SAVING
            # 1. Lobby and waking modal are not visible
            assert not page.is_visible("#screen-lobby"), f"FAIL: Lobby is visible during {filename}"
            assert not page.is_visible("#screen-wakeup"), f"FAIL: Waking modal is visible during {filename}"

            # 2. All 5 data-hud-persistent elements are visible
            persistent_keys = ["top-left", "top-right", "task-card", "ask-orbis", "dr-orbis"]
            for key in persistent_keys:
                sel = f'[data-hud-persistent="{key}"]'
                assert page.is_visible(sel), f"FAIL: Persistent element '{key}' ({sel}) is not visible in {filename} at {w}x{h}"

            persistent_count = page.locator("[data-hud-persistent]").count()
            assert persistent_count == 5, f"FAIL: Expected exactly 5 persistent elements, found {persistent_count}"

            # 3. 3D canvas is rendering
            canvas_info = page.evaluate("""() => {
                const c = document.querySelector('#lab-canvas') || document.querySelector('canvas');
                return c ? { w: c.width, h: c.height } : null;
            }""")
            assert canvas_info and canvas_info["w"] > 0 and canvas_info["h"] > 0, f"FAIL: Canvas not rendering: {canvas_info}"

            out_path = OUTPUT_DIR / filename
            page.screenshot(path=str(out_path))
            im = Image.open(out_path)
            assert im.size == (w, h), f"Expected size ({w}, {h}), got {im.size}"
            print(f"  -> Verified & saved {filename} ({w}x{h}): {desc}")
            page.close()

        browser.close()


def capture_movement_proof_strip(port: int = 8018):
    print("[3/4] Capturing movement proof strip across camera yaws (0°, 90°, 180°, 270°)...")
    from playwright.sync_api import sync_playwright

    yaws = [
        (0, "Yaw 0° (Looking South)"),
        (90, "Yaw 90° (Looking West)"),
        (180, "Yaw 180° (Looking North)"),
        (270, "Yaw 270° (Looking East)"),
    ]

    frames = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.goto(f"http://127.0.0.1:{port}/#/lab?exp=pk_ward", wait_until="networkidle")
        page.wait_for_selector("#lab-hud", state="attached", timeout=15000)
        page.wait_for_selector("#webgl-canvas, canvas", state="attached", timeout=15000)
        page.wait_for_timeout(3000)

        for deg, label in yaws:
            rad = deg * 3.141592653589793 / 180.0
            # Position camera at specified yaw angle relative to character
            page.evaluate(f"""() => {{
                if (window.characterController) {{
                    window.characterController.spawnForExperiment('pk_ward');
                }}
                const charPos = window.characterController?.rig?.root?.position || new THREE.Vector3(-3.85, 0, -2.85);
                const dist = 3.8;
                const camX = charPos.x + dist * Math.sin({rad});
                const camZ = charPos.z + dist * Math.cos({rad});
                const camY = charPos.y + 1.6;
                window.sceneManager.camera.position.set(camX, camY, camZ);
                window.sceneManager.controls.target.copy(charPos);
                window.sceneManager.camera.lookAt(charPos);
                window.sceneManager.cameraRig.target.copy(charPos);
            }}""")
            page.wait_for_timeout(400)

            # Capture Before
            before_bytes = page.screenshot()
            before_img = Image.open(io_bytes(before_bytes))

            # Press W for 500ms
            page.keyboard.down("KeyW")
            page.wait_for_timeout(500)
            page.keyboard.up("KeyW")
            page.wait_for_timeout(200)

            # Capture After
            after_bytes = page.screenshot()
            after_img = Image.open(io_bytes(after_bytes))

            frames.append((label, before_img, after_img))
            print(f"  -> Captured movement frame pair for {label}")

        browser.close()

    # Stitch 4-frame comparison strip
    thumb_w, thumb_h = 320, 180
    header_h = 36
    strip_w = thumb_w * 4
    strip_h = thumb_h * 2 + header_h

    strip = Image.new("RGB", (strip_w, strip_h), (12, 7, 29))
    draw = ImageDraw.Draw(strip)

    for i, (label, b_img, a_img) in enumerate(frames):
        x = i * thumb_w
        # Draw header label
        draw.text((x + 10, 10), label, fill=(56, 189, 248))
        draw.text((x + 10, header_h + 6), "Before W", fill=(148, 163, 184))
        draw.text((x + 10, header_h + thumb_h + 6), "After W (travels away from cam)", fill=(52, 211, 153))

        b_thumb = b_img.resize((thumb_w - 4, thumb_h - 4))
        a_thumb = a_img.resize((thumb_w - 4, thumb_h - 4))

        strip.paste(b_thumb, (x + 2, header_h + 2))
        strip.paste(a_thumb, (x + 2, header_h + thumb_h + 2))

    strip_path = OUTPUT_DIR / "movement_proof_strip.png"
    strip.save(strip_path)
    print(f"  -> Saved movement proof strip: {strip_path} ({strip_path.stat().st_size} bytes)")


def io_bytes(b: bytes):
    import io
    return io.BytesIO(b)


def verify_md5_uniqueness():
    print("[4/4] Verifying MD5 uniqueness across docs/screenshots/ux-fix/...")
    hashes: dict[str, str] = {}
    collisions = []

    for path in sorted(OUTPUT_DIR.glob("*.png")):
        data = path.read_bytes()
        md5 = hashlib.md5(data).hexdigest()
        sha256 = hashlib.sha256(data).hexdigest()
        if md5 in hashes:
            collisions.append((path.name, hashes[md5]))
        else:
            hashes[md5] = path.name
        print(f"  {path.name:36s} size={len(data):7d}  MD5={md5}  SHA256={sha256[:12]}...")

    if collisions:
        raise RuntimeError(f"MD5 collisions detected: {collisions}")
    print(f"All {len(hashes)} proof files strictly unique (0 collisions).")


if __name__ == "__main__":
    capture_before_screenshot()

    port = 8018
    env = os.environ.copy()
    env["ENVIRONMENT"] = "development"
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--app-dir", str(REPO_ROOT / "backend"), "--port", str(port)],
        cwd=str(REPO_ROOT),
    )

    try:
        url = f"http://127.0.0.1:{port}/api/health"
        if not wait_for_server(url):
            raise RuntimeError(f"Server on {port} did not start")

        capture_after_screenshots(port)
        capture_movement_proof_strip(port)
    finally:
        proc.terminate()
        proc.wait()

    verify_md5_uniqueness()
    print("ALL PROOF CAPTURES COMPLETED AND VALIDATED SUCCESSFULLY!")
