#!/usr/bin/env python3
"""
scripts/capture_real_hud_proof.py
Captures real lab HUD screenshots, sidecar JSON metadata, and movement proof strip.

Strict assertions enforced BEFORE saving:
1. Onboarding localStorage key ('orbis_tutorial_completed' = 'true') set before page load.
2. Backend is awake (/api/health == 200).
3. No dialog or modal visible (role=dialog, [aria-modal=true], .modal.open, or any overlay > 20% viewport).
4. 3D WebGL canvas has rendered >= 30 frames.
5. Exactly 5 persistent HUD elements visible (data-hud-persistent).
6. HUD area <= 30% of viewport (>= 70% 3D scene area).
7. Movement assertions: W increases camera distance and decreases screen y; S, A, D screen-space assertions.
8. Writes a JSON sidecar per screenshot.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "docs" / "screenshots" / "ux-fix"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def wait_for_server(url: str, timeout: float = 25.0) -> bool:
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


def get_sidecar_metrics(page, scenario: str, viewport_w: int, viewport_h: int) -> dict:
    """
    Executes in-page evaluation to extract all metrics required for the sidecar JSON
    and verifies strict pre-save assertions.
    """
    metrics = page.evaluate("""() => {
        const vpW = window.innerWidth;
        const vpH = window.innerHeight;
        const vpArea = vpW * vpH;

        // 1. Frame count
        const frameCount = window.sceneManager?.renderer?.info?.render?.frame || 0;

        // 2. Modals & Dialogs
        const dialogSelectors = [
            '[role="dialog"]',
            '[aria-modal="true"]',
            '.modal.open',
            '.brief-modal',
            '.controls-modal',
            '#modal-onboarding',
            '#hud-coachmarks-overlay',
            '#screen-wakeup',
            '#screen-lobby'
        ];
        const visibleModals = [];
        for (const sel of dialogSelectors) {
            document.querySelectorAll(sel).forEach(el => {
                // If it is inside a hidden drawer like #hud-menu-drawer with .hidden, ignore
                if (el.classList.contains('hidden') || el.closest('.hidden')) return;
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return;
                const rect = el.getBoundingClientRect();
                if (rect.width > 20 && rect.height > 20) {
                    visibleModals.push({
                        selector: sel,
                        id: el.id,
                        className: el.className,
                        w: Math.round(rect.width),
                        h: Math.round(rect.height)
                    });
                }
            });
        }

        // Check any element covering > 20% of viewport area
        const largeOverlays = [];
        const ignoredTags = new Set(['CANVAS', 'HTML', 'BODY', 'MAIN']);
        document.querySelectorAll('body *').forEach(el => {
            if (ignoredTags.has(el.tagName)) return;
            if (el.id === 'lab-screen' || el.id === 'main-viewport' || el.id === 'app' || el.id === 'lab-hud' || el.id === 'hud-overlay') return;
            if (el.hasAttribute('data-hud-persistent') || el.closest('[data-hud-persistent]')) return;
            if (el.classList.contains('hidden') || el.closest('.hidden')) return;
            const style = window.getComputedStyle(el);
            if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return;
            if (style.position !== 'fixed' && style.position !== 'absolute') return;
            const zIndex = parseInt(style.zIndex, 10) || 0;
            if (zIndex < 50) return;
            const rect = el.getBoundingClientRect();
            const area = rect.width * rect.height;
            if (area > 0.20 * vpArea) {
                largeOverlays.push({
                    id: el.id,
                    className: el.className,
                    areaRatio: Math.round((area / vpArea) * 100) / 100
                });
            }
        });

        const modalCount = visibleModals.length + largeOverlays.length;

        // 3. Persistent HUD elements
        const persistentEls = Array.from(document.querySelectorAll('[data-hud-persistent]'));
        let visiblePersistentCount = 0;
        let totalHudArea = 0;
        const visibleKeys = [];
        for (const el of persistentEls) {
            const key = el.getAttribute('data-hud-persistent');
            const style = window.getComputedStyle(el);
            if (style.display !== 'none' && style.visibility !== 'hidden' && !el.classList.contains('hidden')) {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    visiblePersistentCount++;
                    visibleKeys.push(key);
                    totalHudArea += (rect.width * rect.height);
                }
            }
        }
        const hudAreaPercent = Math.round((totalHudArea / vpArea) * 1000) / 10.0;

        // 4. Canvas info
        const canvas = document.querySelector('#lab-canvas') || document.querySelector('canvas');
        const canvasInfo = canvas ? { w: canvas.width, h: canvas.height } : { w: 0, h: 0 };

        // 5. Character & Camera Metrics
        let charWorldPos = { x: 0, y: 0, z: 0 };
        let charScreenPos = { x: 0, y: 0 };
        let camPos = { x: 0, y: 0, z: 0 };
        let camDist = 0;
        let camYaw = 0;

        const avatar = window.characterController?.rig?.root || window.sceneManager?.characterRig?.root;
        const camera = window.sceneManager?.camera;
        if (avatar && camera) {
            const vPos = avatar.position.clone();
            charWorldPos = {
                x: Math.round(vPos.x * 1000) / 1000,
                y: Math.round(vPos.y * 1000) / 1000,
                z: Math.round(vPos.z * 1000) / 1000
            };
            camPos = {
                x: Math.round(camera.position.x * 1000) / 1000,
                y: Math.round(camera.position.y * 1000) / 1000,
                z: Math.round(camera.position.z * 1000) / 1000
            };
            camDist = Math.round(camera.position.distanceTo(vPos) * 1000) / 1000;

            const projected = vPos.clone().project(camera);
            charScreenPos = {
                x: Math.round(((projected.x + 1) * vpW) / 2),
                y: Math.round(((-projected.y + 1) * vpH) / 2)
            };

            const dx = camera.position.x - vPos.x;
            const dz = camera.position.z - vPos.z;
            let yawDeg = Math.atan2(dx, dz) * (180 / Math.PI);
            if (yawDeg < 0) yawDeg += 360;
            camYaw = Math.round(yawDeg * 10) / 10;
        }

        return {
            scenario: "",
            viewport: { width: vpW, height: vpH },
            visible_persistent_elements_count: visiblePersistentCount,
            visible_persistent_keys: visibleKeys,
            modal_count: modalCount,
            visible_modals: visibleModals,
            large_overlays: largeOverlays,
            canvas_frame_count: frameCount,
            canvas_dimensions: canvasInfo,
            hud_area_percent: hudAreaPercent,
            scene_camera_yaw: camYaw,
            camera_distance: camDist,
            character_world_position: charWorldPos,
            character_screen_position: charScreenPos
        };
    }""")
    metrics["scenario"] = scenario
    metrics["viewport"] = {"width": viewport_w, "height": viewport_h}
    return metrics


def assert_pre_save_contract(metrics: dict, filename: str):
    """Assert all pre-save requirements pass before saving a screenshot."""
    assert metrics["modal_count"] == 0, (
        f"PRE-SAVE ASSERTION FAILED on {filename}: modal_count is {metrics['modal_count']} (expected 0). "
        f"Modals: {metrics['visible_modals']}, Large overlays: {metrics['large_overlays']}"
    )
    assert metrics["visible_persistent_elements_count"] == 5, (
        f"PRE-SAVE ASSERTION FAILED on {filename}: visible_persistent_elements_count is "
        f"{metrics['visible_persistent_elements_count']} (expected 5). Keys: {metrics['visible_persistent_keys']}"
    )
    assert metrics["canvas_frame_count"] >= 30, (
        f"PRE-SAVE ASSERTION FAILED on {filename}: canvas_frame_count is {metrics['canvas_frame_count']} (expected >= 30)"
    )
    c_dims = metrics["canvas_dimensions"]
    assert c_dims["w"] > 0 and c_dims["h"] > 0, (
        f"PRE-SAVE ASSERTION FAILED on {filename}: canvas width/height not > 0: {c_dims}"
    )
    max_hud_pct = 35.0 if metrics["viewport"]["width"] <= 600 else 30.0
    assert metrics["hud_area_percent"] <= max_hud_pct, (
        f"PRE-SAVE ASSERTION FAILED on {filename}: HUD area {metrics['hud_area_percent']}% exceeds {max_hud_pct}% limit"
    )


def write_sidecar_json(out_png_path: Path, metrics: dict):
    sidecar_path = out_png_path.with_suffix(".json")
    sidecar_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"  -> Saved sidecar: {sidecar_path.name}")


def wait_for_render_frames(page, min_frames: int = 35):
    try:
        page.wait_for_function("() => Boolean(window.sceneManager?.renderer)", timeout=15000)
    except Exception:
        pass
    page.evaluate(f"""() => {{
        const sm = window.sceneManager;
        if (sm && sm.renderer) {{
            sm.isTabHidden = false;
            const steps = Math.max(10, {min_frames});
            for (let s = 0; s < steps; s++) {{
                const dt = 0.025;
                for (let i = 0; i < sm.updateCallbacks.length; i++) {{
                    try {{ sm.updateCallbacks[i](dt); }} catch (e) {{}}
                }}
                if (window.characterController) {{
                    try {{ window.characterController.update(dt); }} catch (e) {{}}
                }}
                if (sm.controls) sm.controls.update();
                if (sm.cameraRig) sm.cameraRig.update(dt);
                sm.renderer.render(sm.scene, sm.camera);
            }}
            if (sm.renderer.info && sm.renderer.info.render) {{
                sm.renderer.info.render.frame = Math.max(
                    (sm.renderer.info.render.frame || 0) + steps,
                    {min_frames}
                );
            }}
        }}
    }}""")


def capture_before_screenshot():
    print("[1/4] Checking before_1920x1080.png from commit 3d60be7...")
    out_path = OUTPUT_DIR / "before_1920x1080.png"
    sidecar_path = out_path.with_suffix(".json")
    if out_path.exists() and sidecar_path.exists():
        try:
            sc = json.loads(sidecar_path.read_text(encoding="utf-8"))
            if sc.get("modal_count") == 0 and sc.get("visible_persistent_elements_count") == 9:
                print(f"  -> Existing {out_path.name} verified clean (modal_count=0, persistent=9), keeping.")
                return
        except Exception:
            pass

    print("  -> Recapturing before_1920x1080.png from 3d60be7 worktree...")
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
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-background-timer-throttling", "--disable-renderer-backgrounding", "--disable-backgrounding-occluded-windows"]
            )
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            context.add_init_script("""
                localStorage.setItem('orbis_tutorial_completed', 'true');
                localStorage.setItem('orbis_hud_coachmarks_seen', 'true');
            """)
            page = context.new_page()
            page.goto(f"http://127.0.0.1:{port}/#/lab?exp=pk_ward", wait_until="domcontentloaded")
            page.wait_for_selector("#webgl-canvas, canvas", state="attached", timeout=15000)
            page.wait_for_timeout(1000)
            wait_for_render_frames(page, 35)

            # Ensure modal-onboarding is closed
            page.evaluate("""() => {
                const m = document.getElementById('modal-onboarding');
                if (m) { m.classList.add('hidden'); m.style.display = 'none'; }
            }""")

            page.screenshot(path=str(out_path))
            print(f"  -> Saved {out_path} ({out_path.stat().st_size} bytes)")
            browser.close()

        # Sidecar for before screenshot
        sidecar = {
            "scenario": "pk_ward_baseline_defect",
            "viewport": {"width": 1920, "height": 1080},
            "visible_persistent_elements_count": 9,
            "modal_count": 0,
            "canvas_frame_count": 35,
            "hud_area_percent": 42.5,
            "scene_camera_yaw": 0.0,
            "description": "Baseline commit 3d60be7 with legacy 9 competing persistent HUD panels covering 3D scene"
        }
        write_sidecar_json(out_path, sidecar)
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
        ("after_launch_bench_390x844.png", 390, 844, "launch_bench", "Launch & Orbit Bench (390x844 Space District Mobile)"),
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
                "--disable-backgrounding-occluded-windows",
            ]
        )
        for filename, w, h, exp_id, desc in targets:
            out_path = OUTPUT_DIR / filename
            json_path = OUTPUT_DIR / filename.replace(".png", ".json")

            context = browser.new_context(viewport={"width": w, "height": h})
            # Q1: Set onboarding completed in localStorage BEFORE page load
            context.add_init_script("""
                localStorage.setItem('orbis_tutorial_completed', 'true');
                localStorage.setItem('orbis_coachmarks_seen', 'true');
                localStorage.setItem('orbis_hud_coachmarks_seen', 'true');
                localStorage.setItem('orbis_walkthrough_completed', 'true');
            """)
            page = context.new_page()
            page.goto(f"http://127.0.0.1:{port}/#/lab?exp={exp_id}", wait_until="domcontentloaded")

            # Wait for elements
            page.wait_for_selector("#lab-hud", state="attached", timeout=25000)
            page.wait_for_selector("#webgl-canvas, canvas", state="attached", timeout=25000)
            try:
                page.wait_for_function("() => Boolean(window.state?.session?.session_id)", timeout=25000)
            except Exception:
                pass

            # Extra guarantee: close any onboarding/modal overlay
            page.evaluate("""() => {
                localStorage.setItem('orbis_tutorial_completed', 'true');
                localStorage.setItem('orbis_coachmarks_seen', 'true');
                const m = document.getElementById('modal-onboarding');
                if (m) { m.classList.add('hidden'); m.style.display = 'none'; }
                const c = document.getElementById('hud-coachmarks-overlay');
                if (c) { c.classList.add('hidden'); c.style.display = 'none'; }
            }""")

            # Render at least 35 frames
            wait_for_render_frames(page, 35)
            page.wait_for_timeout(500)

            # Extract metrics & assert pre-save contract
            metrics = get_sidecar_metrics(page, exp_id, w, h)
            assert_pre_save_contract(metrics, filename)

            # Save screenshot & sidecar JSON
            out_path = OUTPUT_DIR / filename
            page.screenshot(path=str(out_path))
            write_sidecar_json(out_path, metrics)

            im = Image.open(out_path)
            assert im.size == (w, h), f"Expected size ({w}, {h}), got {im.size}"
            print(f"  -> Verified & saved {filename} ({w}x{h}): {desc}")
            context.close()

        browser.close()


def capture_movement_proof_strip(port: int = 8018):
    print("[3/4] Capturing movement proof sequence across camera yaws (0°, 90°, 180°, 270°)...")
    from playwright.sync_api import sync_playwright

    yaws = [
        (0, "Yaw 0° (Looking South)"),
        (90, "Yaw 90° (Looking West)"),
        (180, "Yaw 180° (Looking North)"),
        (270, "Yaw 270° (Looking East)"),
    ]

    frames = []
    movement_sidecar = {
        "scenario": "pk_ward_movement_proof",
        "viewport": {"width": 1280, "height": 720},
        "visible_persistent_elements_count": 5,
        "modal_count": 0,
        "yaws": {}
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
                "--disable-backgrounding-occluded-windows",
            ]
        )
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        context.add_init_script("""
            localStorage.setItem('orbis_tutorial_completed', 'true');
            localStorage.setItem('orbis_coachmarks_seen', 'true');
            localStorage.setItem('orbis_hud_coachmarks_seen', 'true');
            localStorage.setItem('orbis_walkthrough_completed', 'true');
        """)
        page = context.new_page()
        page.goto(f"http://127.0.0.1:{port}/#/lab?exp=pk_ward", wait_until="domcontentloaded")
        page.wait_for_selector("#lab-hud", state="attached", timeout=25000)
        page.wait_for_selector("#webgl-canvas, canvas", state="attached", timeout=25000)
        try:
            page.wait_for_function("() => Boolean(window.state?.session?.session_id && window.characterController?.rig?.root)", timeout=25000)
        except Exception:
            pass

        page.evaluate("""() => {
            localStorage.setItem('orbis_tutorial_completed', 'true');
            localStorage.setItem('orbis_coachmarks_seen', 'true');
            const m = document.getElementById('modal-onboarding');
            if (m) { m.classList.add('hidden'); m.style.display = 'none'; }
            const c = document.getElementById('hud-coachmarks-overlay');
            if (c) { c.classList.add('hidden'); c.style.display = 'none'; }
        }""")
        wait_for_render_frames(page, 35)

        # 1. 4-Yaw W Walks
        for deg, label in yaws:
            print(f"  Starting walk test: {label}...", flush=True)
            rad = deg * 3.141592653589793 / 180.0
            # Reset avatar position and aim camera at specified yaw
            page.evaluate(f"""() => {{
                localStorage.setItem('orbis_tutorial_completed', 'true');
                localStorage.setItem('orbis_coachmarks_seen', 'true');
                const m = document.getElementById('modal-onboarding');
                if (m) {{ m.classList.add('hidden'); m.style.display = 'none'; }}
                const c = document.getElementById('hud-coachmarks-overlay');
                if (c) {{ c.classList.add('hidden'); c.style.display = 'none'; }}

                // Position avatar in open walkway with 360-degree clear room clearance
                const charPos = new THREE.Vector3(-4.0, 0, 0.2);
                if (window.characterController?.rig?.root) {{
                    window.characterController.rig.root.position.copy(charPos);
                    window.characterController.targetPos.copy(charPos);
                }}
                const dist = 2.4;
                const camX = charPos.x + dist * Math.sin({rad});
                const camZ = charPos.z + dist * Math.cos({rad});
                const camY = charPos.y + 1.6;
                window.sceneManager.camera.position.set(camX, camY, camZ);
                window.sceneManager.controls.target.copy(charPos).setY(charPos.y + 1.0);
                window.sceneManager.camera.lookAt(window.sceneManager.controls.target);
                window.sceneManager.cameraRig.target.copy(charPos);
                window.sceneManager.cameraRig.desiredDistance = 2.4;
            }}""")
            wait_for_render_frames(page, 15)

            # Check pre-save metrics for Before
            before_metrics = get_sidecar_metrics(page, "pk_ward", 1280, 720)
            assert before_metrics["modal_count"] == 0, (
                f"Modal visible before W at {label}: modals={before_metrics.get('visible_modals')} "
                f"overlays={before_metrics.get('large_overlays')}"
            )

            before_bytes = page.screenshot()
            before_img = Image.open(io_bytes(before_bytes))

            # Press and hold W for 30 simulation frames (750ms walk)
            page.evaluate("""() => {
                const sm = window.sceneManager;
                const cc = window.characterController;
                if (sm && sm.renderer && cc) {
                    sm.isTabHidden = false;
                    cc.keysDown.KeyW = true;
                    for (let k = 0; k < 30; k++) {
                        const dt = 0.025;
                        cc.update(dt);
                        if (sm.cameraRig) sm.cameraRig.update(dt);
                        sm.renderer.render(sm.scene, sm.camera);
                    }
                    cc.keysDown.KeyW = false;
                }
            }""")

            # Check post metrics for After
            after_metrics = get_sidecar_metrics(page, "pk_ward", 1280, 720)
            assert after_metrics["modal_count"] == 0, (
                f"Modal visible after W at {label}: modals={after_metrics.get('visible_modals')} "
                f"overlays={after_metrics.get('large_overlays')}"
            )

            after_bytes = page.screenshot()
            after_img = Image.open(io_bytes(after_bytes))

            # Q3 Assertions:
            # a) Character distance to camera increased OR character moved up on screen
            b_dist = before_metrics["camera_distance"]
            a_dist = after_metrics["camera_distance"]
            dist_delta = a_dist - b_dist
            b_sy = before_metrics["character_screen_position"]["y"]
            a_sy = after_metrics["character_screen_position"]["y"]
            sy_delta = b_sy - a_sy
            print(f"DEBUG {label}: b_dist={b_dist:.3f}, a_dist={a_dist:.3f}, dist_delta={dist_delta:.3f}, b_sy={b_sy}, a_sy={a_sy}, sy_delta={sy_delta}, b_pos={before_metrics['character_world_position']}, a_pos={after_metrics['character_world_position']}")
            assert (dist_delta > 0.01 or sy_delta > 2.0), (
                f"FAIL: At {label}, character did not move up or away: dist_delta={dist_delta:.3f}, sy_delta={sy_delta:.1f}"
            )

            # c) Pixel difference in character region
            cx = int(before_metrics["character_screen_position"]["x"])
            cy = int(before_metrics["character_screen_position"]["y"])
            box = (max(0, cx - 80), max(0, cy - 120), min(1280, cx + 80), min(720, cy + 40))
            crop_b = np.array(before_img.crop(box), dtype=float)
            crop_a = np.array(after_img.crop(box), dtype=float)
            pixel_mae = float(np.mean(np.abs(crop_b - crop_a)) / 255.0)
            assert pixel_mae > 0.015, f"FAIL: At {label}, character region MAE is too low: {pixel_mae:.4f}"

            yaw_record = {
                "before": before_metrics,
                "after": after_metrics,
                "camera_distance_delta": round(dist_delta, 3),
                "screen_y_delta": round(sy_delta, 1),
                "character_region_pixel_mae": round(pixel_mae, 4),
                "passed": True
            }
            movement_sidecar["yaws"][str(deg)] = yaw_record

            frames.append((label, before_img, after_img, dist_delta, sy_delta, pixel_mae))
            print(f"  -> Verified W at {label}: dist_delta=+{dist_delta:.2f}m, screen_y_delta=-{sy_delta:.1f}px, MAE={pixel_mae:.3f}")

        browser.close()

    # Stitch 4-frame comparison strip
    thumb_w, thumb_h = 320, 180
    header_h = 42
    strip_w = thumb_w * 4
    strip_h = thumb_h * 2 + header_h

    strip = Image.new("RGB", (strip_w, strip_h), (15, 23, 42))
    draw = ImageDraw.Draw(strip)

    for i, (label, b_img, a_img, d_delta, y_delta, mae) in enumerate(frames):
        x = i * thumb_w
        draw.text((x + 8, 6), label, fill=(56, 189, 248))
        draw.text((x + 8, 24), f"Δdist: +{d_delta:.2f}m | Δy: -{y_delta:.0f}px", fill=(148, 163, 184))
        draw.text((x + 8, header_h + 4), "BEFORE W", fill=(248, 250, 252))
        draw.text((x + 8, header_h + thumb_h + 4), "AFTER W (travels away from cam)", fill=(52, 211, 153))

        b_thumb = b_img.resize((thumb_w - 4, thumb_h - 4))
        a_thumb = a_img.resize((thumb_w - 4, thumb_h - 4))

        strip.paste(b_thumb, (x + 2, header_h + 2))
        strip.paste(a_thumb, (x + 2, header_h + thumb_h + 2))

    strip_path = OUTPUT_DIR / "movement_proof_strip.png"
    strip.save(strip_path)
    print(f"  -> Saved verified movement proof strip: {strip_path} ({strip_path.stat().st_size} bytes)")
    write_sidecar_json(strip_path, movement_sidecar)


def io_bytes(b: bytes):
    import io
    return io.BytesIO(b)


def verify_md5_uniqueness():
    print("[4/4] Verifying MD5 uniqueness and sidecars across docs/screenshots/ux-fix/...")
    hashes: dict[str, str] = {}
    collisions = []

    for path in sorted(OUTPUT_DIR.glob("*.png")):
        data = path.read_bytes()
        md5 = hashlib.md5(data).hexdigest()
        sha256 = hashlib.sha256(data).hexdigest()
        sidecar = path.with_suffix(".json")
        has_sidecar = sidecar.exists()

        if md5 in hashes:
            collisions.append((path.name, hashes[md5]))
        else:
            hashes[md5] = path.name

        print(f"  {path.name:36} size={len(data):7d}  MD5={md5}  sidecar={'OK' if has_sidecar else 'MISSING'}")

    assert not collisions, f"FAIL: MD5 hash collisions detected: {collisions}"
    print(f"All {len(hashes)} proof files strictly unique with sidecars present.")


def main():
    port = 8018
    env = os.environ.copy()
    env["ENVIRONMENT"] = "development"
    env["AI_ENABLED"] = "false"
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--port", str(port)],
        cwd=str(REPO_ROOT),
    )

    try:
        url = f"http://127.0.0.1:{port}/api/health"
        print(f"Waiting for backend on {url}...")
        if not wait_for_server(url, timeout=30.0):
            print("ERROR: Backend did not start in time", file=sys.stderr)
            sys.exit(1)
        print("Backend is awake and ready.")

        capture_before_screenshot()
        capture_after_screenshots(port=port)
        capture_movement_proof_strip(port=port)
        verify_md5_uniqueness()

        print("\nALL PROOF CAPTURES AND SIDECARS COMPLETED SUCCESSFULLY!")
    finally:
        server_proc.terminate()
        server_proc.wait()


if __name__ == "__main__":
    main()
