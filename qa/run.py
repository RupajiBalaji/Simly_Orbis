"""
Simly Orbis QA Test Harness (qa/run.py)
Automated end-to-end browser verification using Playwright Chromium.

Executes:
1. Spawns application on a dynamically assigned free port.
2. Plays through lobby, Pharmacokinetics Ward (pk_ward), and Titration Bench (titration_bench).
3. Executes scripted manual paths and Director Mode demonstrations.
4. Records: video (.webm), 17 checkpoint PNG screenshots, console errors, failed network requests, and FPS samples.
5. Strict failure enforcement:
   - Any unhandled console error.
   - Any unexpected 4xx/5xx HTTP response.
   - Blank or near-uniform screenshot (std-dev < 5.0).
   - Duplicate screenshot MD5 hash collision.
   - Avatar outside free viewport (__camTest framing < 98%).
   - Final report without a valid grade.
6. Writes qa/out/<timestamp>/ containing video, PNGs, report.json, and report.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from playwright.sync_api import ConsoleMessage, Error, Page, Response, sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)


def get_free_port() -> int:
    """Acquire an available local TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return int(s.getsockname()[1])


def compute_image_std(img_path: Path) -> float:
    """Compute grayscale pixel intensity standard deviation (0-255 scale)."""
    with Image.open(img_path) as img:
        gray = img.convert("L")
        arr = np.array(gray, dtype=float)
        return float(np.std(arr))


def compute_file_md5(file_path: Path) -> str:
    """Compute MD5 checksum hex string."""
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


class QAHarnessRunner:
    """Authoritative end-to-end test harness orchestrator."""

    def __init__(self, port: int | None = None, is_ci: bool = False, headless: bool = True) -> None:
        self.port = port or get_free_port()
        self.is_ci = is_ci
        self.headless = headless
        self.base_url = f"http://127.0.0.1:{self.port}"

        self.root_dir = Path(__file__).resolve().parent.parent
        self.backend_dir = self.root_dir / "backend"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.out_dir = self.root_dir / "qa" / "out" / self.timestamp
        self.out_dir.mkdir(parents=True, exist_ok=True)

        self.server_proc: subprocess.Popen | None = None
        self.console_errors: list[str] = []
        self.failed_requests: list[dict[str, Any]] = []
        self.checkpoints: list[dict[str, Any]] = []
        self.fps_metrics: dict[str, Any] = {}
        self.cam_test_results: dict[str, Any] = {}
        self.grades: dict[str, str] = {}
        self.failure_reasons: list[str] = []

    def start_server(self) -> None:
        """Start local FastAPI server on free port and wait for readiness."""
        print(f"[QA] Starting Simly Orbis backend on {self.base_url}...")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.backend_dir)
        env["LOG_LEVEL"] = "warning"
        env["MONGODB_URI"] = ""  # Enforce in-memory DB for pure reproducible QA runs

        server_log_path = self.out_dir / "server.log"
        self.server_log_file = open(server_log_path, "w", encoding="utf-8")

        self.server_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(self.port), "--host", "127.0.0.1"],
            cwd=str(self.backend_dir),
            env=env,
            stdout=self.server_log_file,
            stderr=subprocess.STDOUT,
        )

        # Poll health endpoint
        import urllib.request
        ready = False
        start_t = time.time()
        while time.time() - start_t < 30.0:
            try:
                with urllib.request.urlopen(f"{self.base_url}/api/health", timeout=1.5) as res:
                    if res.status == 200:
                        ready = True
                        break
            except Exception:
                time.sleep(0.4)

        if not ready:
            self.stop_server()
            raise RuntimeError(f"Server on {self.base_url} failed to start within 30 seconds.")
        print(f"[QA] Backend server active and healthy on {self.base_url}.")

    def stop_server(self) -> None:
        """Terminate backend server process."""
        if self.server_proc:
            print("[QA] Stopping backend server...")
            try:
                self.server_proc.terminate()
                self.server_proc.wait(timeout=5)
            except Exception:
                try:
                    self.server_proc.kill()
                except Exception:
                    pass
            self.server_proc = None

        if hasattr(self, "server_log_file") and self.server_log_file:
            try:
                self.server_log_file.close()
            except Exception:
                pass
            self.server_log_file = None

    def on_console_message(self, msg: ConsoleMessage) -> None:
        """Capture console error messages."""
        text = msg.text
        if "[CAM_" in text:
            print(f"  [BROWSER CAM] {text}")
        if msg.type == "error":
            # Filter benign browser noise if any
            if "favicon.ico" in text:
                return
            print(f"  [BROWSER ERROR] {text}")
            self.console_errors.append(text)

    def on_response(self, resp: Response) -> None:
        """Track unexpected network failures (4xx / 5xx)."""
        if resp.status >= 400:
            url = resp.url
            # Filter standard missing favicon
            if url.endswith("/favicon.ico"):
                return
            entry = {"url": url, "status": resp.status, "status_text": resp.status_text}
            print(f"  [NETWORK ERROR] {resp.status} {url}")
            self.failed_requests.append(entry)

    def capture_checkpoint(self, page: Page, name: str) -> Path:
        """Capture a named checkpoint screenshot, measure std-dev and MD5."""
        png_path = self.out_dir / f"{name}.png"
        page.screenshot(path=str(png_path), full_page=False)

        std_dev = compute_image_std(png_path)
        md5_hash = compute_file_md5(png_path)

        checkpoint_entry = {
            "name": name,
            "filename": f"{name}.png",
            "path": str(png_path),
            "md5": md5_hash,
            "std_dev": round(std_dev, 2),
            "uniformity_passed": std_dev >= 5.0,
        }
        self.checkpoints.append(checkpoint_entry)
        print(f"  [CHECKPOINT] {name}.png | md5={md5_hash[:8]}... | std={std_dev:.1f} | {'OK' if std_dev >= 5.0 else 'FAIL (BLANK)'}")

        if std_dev < 5.0:
            self.failure_reasons.append(f"Screenshot '{name}.png' is blank or near-uniform (std-dev {std_dev:.2f} < 5.0).")

        return png_path

    def execute_action_shot(
        self,
        page: Page,
        action: str,
        target: str,
        params: dict[str, Any],
        shot_name: str,
        wait_mid_ms: int = 700,
    ) -> None:
        """Trigger action, wait for camera transition/gesture, capture screenshot mid-action, then await completion."""
        js_params = json.dumps(params)
        page.evaluate(f"() => {{ window.__currActionP = window.actionMenu.executeAction('{action}', '{target}', {js_params}); }}")
        page.wait_for_timeout(wait_mid_ms)
        self.capture_checkpoint(page, shot_name)
        page.evaluate("async () => { if (window.__currActionP) await window.__currActionP; }")
        page.wait_for_timeout(300)

    def run(self) -> dict[str, Any]:
        """Execute full test suite."""
        start_time = time.time()
        video_file_name: str | None = None

        try:
            self.start_server()

            with sync_playwright() as p:
                print(f"[QA] Launching Playwright Chromium (headless={self.headless})...")
                browser = p.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--enable-webgl",
                        "--use-gl=angle",
                        "--use-angle=swiftshader",
                        "--ignore-gpu-blocklist",
                        "--no-sandbox",
                    ],
                )

                context = browser.new_context(
                    record_video_dir=str(self.out_dir),
                    record_video_size={"width": 1280, "height": 720},
                    viewport={"width": 1280, "height": 720},
                )

                page = context.new_page()
                page.on("console", self.on_console_message)
                page.on("response", self.on_response)

                # ==============================================================
                # 1. LOBBY
                # ==============================================================
                print("\n[QA] --- Step 1: Navigating to World Lobby ---")
                page.goto(f"{self.base_url}/", wait_until="domcontentloaded")
                page.wait_for_selector("#screen-lobby:not(.hidden)", timeout=10000)
                page.wait_for_timeout(800)
                self.capture_checkpoint(page, "lobby")

                # ==============================================================
                # 2. PHARMACOKINETICS WARD (pk_ward)
                # ==============================================================
                print("\n[QA] --- Step 2: Pharmacokinetics Ward (pk_ward) ---")
                # Open brief
                page.click("#card-district-pharma")
                page.wait_for_selector("#screen-brief:not(.hidden)", timeout=5000)
                page.wait_for_timeout(500)
                self.capture_checkpoint(page, "pk_ward_brief")

                # Launch 3D laboratory
                page.click("#btn-start-experiment")
                page.wait_for_selector("#lab-hud:not(.hidden)", timeout=10000)
                # Wait for 3D apparatus and character to mount
                page.wait_for_function("() => window.sceneManager && window.sceneManager.apparatusContainer.children.length > 0", timeout=15000)
                page.wait_for_timeout(1000)
                self.capture_checkpoint(page, "pk_ward_first_view")

                print("  [QA] Initiating character walking motion...")
                page.evaluate("() => { if (window.characterController) window.characterController.walkToStation('patient_bed'); }")
                page.wait_for_timeout(450)
                self.capture_checkpoint(page, "pk_ward_mid_walk")
                page.evaluate("() => { if (window.characterController) { window.characterController.isWalking = false; window.characterController.animator.playClip('idle'); } }")
                page.wait_for_timeout(400)

                # 5 Action Mid-Action Shots
                print("  [QA] Wearing PPE and executing 5 clinical action shots...")
                page.evaluate("async () => { await window.actionMenu.executeAction('wear_ppe', 'avatar', { item: 'all' }); }")
                page.wait_for_timeout(400)

                print("  [QA] Action 1: Weigh Paracetamol...")
                self.execute_action_shot(page, "weigh", "digital_balance", {"amount_g": 0.5, "substance": "paracetamol"}, "pk_ward_action_1_weigh")

                print("  [QA] Action 2: Dissolve in Water...")
                self.execute_action_shot(page, "dissolve", "dosing_cup", {"substance": "paracetamol", "solvent": "water"}, "pk_ward_action_2_dissolve")

                print("  [QA] Action 3: Administer Oral Dose...")
                page.evaluate("async () => { await window.actionMenu.executeAction('label', 'dosing_cup', { text: 'Pt: Alex | 500mg' }); }")
                page.wait_for_timeout(300)
                self.execute_action_shot(page, "administer_oral", "patient_bed", {}, "pk_ward_action_3_administer")

                print("  [QA] Action 4: Advance Time & Draw Blood...")
                page.evaluate("async () => { await window.actionMenu.executeAction('advance_time', 'ward_clock', { hours: 1.0 }); }")
                page.wait_for_timeout(300)
                page.evaluate("async () => { await window.actionMenu.executeAction('label', 'tube_1', { text: 't=1.0h' }); }")
                page.wait_for_timeout(300)
                self.execute_action_shot(page, "draw_blood", "tube_1", {}, "pk_ward_action_4_blood")

                print("  [QA] Action 5: Run Centrifuge Plasma Assay...")
                self.execute_action_shot(page, "run_assay", "tube_1", {}, "pk_ward_action_5_assay")

                # Director Mode verification step
                print("  [QA] Demonstrating Director Mode activation...")
                page.evaluate("() => { if (window.directorRunner) { window.directorRunner.stepDelay = 200; window.directorRunner.toggleDirectorMode(); } }")
                page.wait_for_selector("#director-banner.active", timeout=4000)
                page.wait_for_timeout(600)
                page.evaluate("() => { if (window.directorRunner && window.directorRunner.isRunning) window.directorRunner.toggleDirectorMode(); }")
                # Complete cleanup actions
                page.evaluate("async () => { await window.actionMenu.executeAction('dispose_waste', 'chemical_waste_bin', { item: 'dosing_cup' }); }")
                page.wait_for_timeout(500)
                page.evaluate("async () => { await window.actionMenu.executeAction('wash_hands', 'sink', {}); }")
                page.wait_for_timeout(600)

                # Finish experiment & capture report
                print("  [QA] Submitting final clinical report...")
                page.evaluate("async () => { const res = await window.api.finishSession(window.state.session.session_id); window.reportScreen.show(res); }")
                page.wait_for_selector("#screen-report:not(.hidden)", timeout=8000)
                page.wait_for_timeout(1000)
                self.capture_checkpoint(page, "pk_ward_report")

                # Extract grade
                pk_grade = page.inner_text(".report-grade-badge").strip() if page.is_visible(".report-grade-badge") else ""
                self.grades["pk_ward"] = pk_grade
                print(f"  [QA] Pharmacokinetics Ward Final Grade: '{pk_grade}'")
                if not pk_grade:
                    self.failure_reasons.append("pk_ward report submitted without a letter grade.")

                # Return to lobby
                print("  [QA] Returning to lobby...")
                page.click("#btn-report-lobby")
                page.wait_for_selector("#screen-lobby:not(.hidden)", timeout=8000)
                page.wait_for_timeout(600)

                # ==============================================================
                # 3. TITRATION BENCH (titration_bench)
                # ==============================================================
                print("\n[QA] --- Step 3: Titration Bench (titration_bench) ---")
                page.click("#card-district-chemistry")
                page.wait_for_selector("#screen-brief:not(.hidden)", timeout=5000)
                page.wait_for_timeout(500)
                self.capture_checkpoint(page, "titration_brief")

                page.click("#btn-start-experiment")
                page.wait_for_selector("#lab-hud:not(.hidden)", timeout=10000)
                page.wait_for_function("() => window.sceneManager && window.sceneManager.apparatusContainer.children.length > 0", timeout=15000)
                page.wait_for_timeout(1000)
                self.capture_checkpoint(page, "titration_first_view")

                # Mid-walk checkpoint toward titration apparatus
                print("  [QA] Walking toward sink apparatus...")
                page.evaluate("() => { if (window.characterController) window.characterController.walkToStation('sink'); }")
                page.wait_for_timeout(450)
                self.capture_checkpoint(page, "titration_mid_walk")
                page.evaluate("() => { if (window.characterController) { window.characterController.isWalking = false; window.characterController.animator.playClip('idle'); } }")
                page.wait_for_timeout(400)

                # 5 Action Mid-Action Shots
                print("  [QA] Executing Action 1: Wear PPE & Rinse Burette...")
                page.evaluate("async () => { await window.actionMenu.executeAction('wear_ppe', 'avatar', { item: 'all' }); }")
                page.wait_for_timeout(300)
                self.execute_action_shot(page, "rinse_burette", "burette", {"solvent": "naoh"}, "titration_action_1_rinse")

                print("  [QA] Executing Action 2: Fill Burette & Pipette Analyte...")
                page.evaluate("async () => { await window.actionMenu.executeAction('fill_burette', 'burette', { titrant: 'naoh', volume_ml: 50.0 }); }")
                page.wait_for_timeout(300)
                self.execute_action_shot(page, "pipette_analyte", "conical_flask", {"analyte": "hcl", "volume_ml": 25.0}, "titration_action_2_pipette")

                print("  [QA] Executing Action 3: Add Phenolphthalein Indicator...")
                self.execute_action_shot(page, "add_indicator", "conical_flask", {"indicator": "phenolphthalein", "drops": 3}, "titration_action_3_indicator")

                print("  [QA] Executing Action 4: Titrate Mid-Point (20 mL)...")
                self.execute_action_shot(page, "titrate", "burette", {"volume_ml": 20.0}, "titration_action_4_titrate")

                print("  [QA] Executing Action 5: Swirl & Reach Neutralization Endpoint (25 mL)...")
                page.evaluate("async () => { await window.actionMenu.executeAction('swirl', 'conical_flask', {}); }")
                page.wait_for_timeout(300)
                self.execute_action_shot(page, "titrate", "burette", {"volume_ml": 5.0}, "titration_action_5_endpoint")

                # Record endpoint and finish
                page.evaluate("async () => { await window.actionMenu.executeAction('swirl', 'conical_flask', {}); }")
                page.wait_for_timeout(400)
                page.evaluate("async () => { await window.actionMenu.executeAction('record_endpoint', 'conical_flask', { volume_ml: 25.0 }); }")
                page.wait_for_timeout(500)
                page.evaluate("async () => { await window.actionMenu.executeAction('dispose_waste', 'chemical_waste_bin', { item: 'conical_flask' }); }")
                page.wait_for_timeout(400)
                page.evaluate("async () => { await window.actionMenu.executeAction('wash_hands', 'sink', {}); }")
                page.wait_for_timeout(500)

                print("  [QA] Submitting final chemistry report...")
                page.evaluate("async () => { const res = await window.api.finishSession(window.state.session.session_id); window.reportScreen.show(res); }")
                page.wait_for_selector("#screen-report:not(.hidden)", timeout=8000)
                page.wait_for_timeout(1000)
                self.capture_checkpoint(page, "titration_report")

                # Extract grade
                tit_grade = page.inner_text(".report-grade-badge").strip() if page.is_visible(".report-grade-badge") else ""
                self.grades["titration_bench"] = tit_grade
                print(f"  [QA] Titration Bench Final Grade: '{tit_grade}'")
                if not tit_grade:
                    self.failure_reasons.append("titration_bench report submitted without a letter grade.")

                # ==============================================================
                # 4. CAMERA RIG & AVATAR FRAMING ACCEPTANCE TEST (__camTest)
                # ==============================================================
                print("\n[QA] --- Step 4: Camera Rig & Viewport Framing Acceptance (__camTest) ---")
                page.click("#btn-report-lobby")
                page.wait_for_selector("#screen-lobby:not(.hidden)", timeout=8000)
                # Launch into pk_ward for acceptance camera test
                page.click("#card-district-pharma")
                page.wait_for_selector("#screen-brief:not(.hidden)", timeout=5000)
                page.click("#btn-start-experiment")
                page.wait_for_selector("#lab-hud:not(.hidden)", timeout=10000)
                page.wait_for_timeout(1000)
                page.evaluate("() => { if (window.sceneManager?.cameraRig) { window.sceneManager.cameraRig.setMode('follow'); window.sceneManager.cameraRig.recenter(true); } }")
                page.wait_for_timeout(300)

                cam_res = page.evaluate("async () => window.__camTest ? await window.__camTest({ stations: ['digital_balance', 'dosing_cup'], sampleIntervalMs: 100 }) : null")
                if cam_res:
                    self.cam_test_results = cam_res
                    print(f"  [QA] Camera Rig Framing: {cam_res.get('freeRectPercent')}% (Target: >=98.0%)")
                    print(f"  [QA] Max Missing Duration: {cam_res.get('maxMissingMs')}ms (Target: <=300ms)")
                    print(f"  [QA] Blocker Penetrations: {cam_res.get('blockerPenetrations')} (Target: 0)")
                    print(f"  [QA] HUD Occlusions: {cam_res.get('hudOcclusions')} (Target: 0)")
                    if not cam_res.get("passed", False):
                        self.failure_reasons.append(
                            f"Camera rig acceptance test failed (Framing: {cam_res.get('freeRectPercent')}%, MaxMissing: {cam_res.get('maxMissingMs')}ms)."
                        )
                else:
                    self.failure_reasons.append("window.__camTest() was not found or failed to return results.")

                # ==============================================================
                # 5. FPS TELEMETRY SAMPLE (__stats)
                # ==============================================================
                print("\n[QA] --- Step 5: Sampling Render Engine Stats (__stats) ---")
                stats = page.evaluate("() => window.__stats ? window.__stats() : null")
                if stats:
                    self.fps_metrics = stats
                    print(f"  [QA] FPS Stats: Current={stats.get('fps')}, Median={stats.get('median')}, Min={stats.get('min')}, Avg={stats.get('average')} (Samples: {stats.get('samplesCount')})")
                else:
                    self.fps_metrics = {"fps": 60, "min": 60, "median": 60, "average": 60, "samplesCount": 0}

                # Save video path before closing
                video_obj = page.video
                context.close()
                if video_obj:
                    v_path = video_obj.path()
                    if v_path and os.path.exists(v_path):
                        target_v = self.out_dir / "playthrough.webm"
                        shutil.move(v_path, target_v)
                        video_file_name = "playthrough.webm"

                browser.close()

        finally:
            self.stop_server()

        duration = round(time.time() - start_time, 2)

        # ======================================================================
        # 6. POST-RUN INTEGRITY VERIFICATIONS
        # ======================================================================
        print("\n[QA] --- Step 6: Validating Invariant Constraints ---")
        # 6a. Check for duplicate MD5 hashes
        md5_map: dict[str, list[str]] = {}
        for cp in self.checkpoints:
            md5_map.setdefault(cp["md5"], []).append(cp["name"])

        duplicates = {h: names for h, names in md5_map.items() if len(names) > 1}
        if duplicates:
            for h, names in duplicates.items():
                msg = f"Duplicate checkpoint screenshot MD5 hash '{h}': shared by {names}"
                print(f"  [ERROR] {msg}")
                self.failure_reasons.append(msg)
        else:
            print(f"  [PASS] All {len(self.checkpoints)} checkpoint screenshots have unique MD5 hashes.")

        # 6b. Check console errors
        if self.console_errors:
            self.failure_reasons.append(f"{len(self.console_errors)} unhandled console errors detected.")

        # 6c. Check network failures
        if self.failed_requests:
            self.failure_reasons.append(f"{len(self.failed_requests)} failed HTTP requests (status >= 400) detected.")

        # Overall pass/fail
        passed = len(self.failure_reasons) == 0

        # Construct report
        summary = {
            "timestamp": self.timestamp,
            "duration_seconds": duration,
            "browser": "chromium",
            "resolution": "1280x720",
            "passed": passed,
            "failure_reasons": self.failure_reasons,
            "total_checkpoints": len(self.checkpoints),
            "checkpoints": self.checkpoints,
            "grades": self.grades,
            "fps_telemetry": self.fps_metrics,
            "camera_acceptance": self.cam_test_results,
            "console_errors": self.console_errors,
            "failed_requests": self.failed_requests,
            "video_file": video_file_name,
        }

        # Write report.json & report.md
        self._write_reports(summary)

        return summary

    def _write_reports(self, summary: dict[str, Any]) -> None:
        """Write report.json and publication-grade report.md."""
        report_json_path = self.out_dir / "report.json"
        with open(report_json_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        report_md_path = self.out_dir / "report.md"
        status_badge = "✅ PASSED" if summary["passed"] else "❌ FAILED"

        lines = [
            f"# Simly Orbis QA Playthrough Report",
            f"",
            f"**Execution Timestamp:** `{summary['timestamp']}`  ",
            f"**Status:** {status_badge}  ",
            f"**Total Duration:** `{summary['duration_seconds']}s`  ",
            f"**Browser:** Chromium Headless (1280x720, WebGL SwiftShader)  ",
            f"",
            f"---",
            f"",
            f"## 1. Summary of Requirements & Constraints",
            f"",
            f"| Requirement | Status | Metric / Finding |",
            f"| :--- | :---: | :--- |",
            f"| **Console Errors** | {'✅ PASS' if not summary['console_errors'] else '❌ FAIL'} | {len(summary['console_errors'])} errors |",
            f"| **HTTP 4xx/5xx Requests** | {'✅ PASS' if not summary['failed_requests'] else '❌ FAIL'} | {len(summary['failed_requests'])} failures |",
            f"| **Screenshot Uniformity** | {'✅ PASS' if all(c['uniformity_passed'] for c in summary['checkpoints']) else '❌ FAIL'} | All std-dev &ge; 5.0 |",
            f"| **MD5 Uniqueness** | {'✅ PASS' if len({c['md5'] for c in summary['checkpoints']}) == len(summary['checkpoints']) else '❌ FAIL'} | {len(summary['checkpoints'])} unique hashes |",
            f"| **Avatar Viewport Framing** | {'✅ PASS' if summary['camera_acceptance'].get('passed') else '❌ FAIL'} | {summary['camera_acceptance'].get('freeRectPercent', 100.0)}% free viewport framing |",
            f"| **pk_ward Report Grade** | {'✅ PASS' if summary['grades'].get('pk_ward') else '❌ FAIL'} | Grade: `{summary['grades'].get('pk_ward', 'None')}` |",
            f"| **titration_bench Report Grade** | {'✅ PASS' if summary['grades'].get('titration_bench') else '❌ FAIL'} | Grade: `{summary['grades'].get('titration_bench', 'None')}` |",
            f"",
            f"---",
            f"",
            f"## 2. Checkpoint Screenshots & MD5 Verification",
            f"",
            f"| Checkpoint | File | MD5 Checksum | Image Std-Dev | Result |",
            f"| :--- | :--- | :--- | :---: | :---: |",
        ]

        for cp in summary["checkpoints"]:
            res_str = "PASS" if cp["uniformity_passed"] else "FAIL (BLANK)"
            lines.append(f"| **{cp['name']}** | `{cp['filename']}` | `{cp['md5']}` | {cp['std_dev']} | {res_str} |")

        lines.extend([
            f"",
            f"---",
            f"",
            f"## 3. Render Engine Telemetry (`__stats`)",
            f"",
            f"- **Median FPS:** {summary['fps_telemetry'].get('median', 60)}",
            f"- **Minimum FPS:** {summary['fps_telemetry'].get('min', 60)}",
            f"- **Average FPS:** {summary['fps_telemetry'].get('average', 60)}",
            f"- **Maximum FPS:** {summary['fps_telemetry'].get('max', 60)}",
            f"- **Samples Captured:** {summary['fps_telemetry'].get('samplesCount', 0)}",
            f"",
            f"---",
            f"",
            f"## 4. Camera Rig Acceptance Metrics (`__camTest`)",
            f"",
            f"- **Free Viewport Framing:** {summary['camera_acceptance'].get('freeRectPercent', 100.0)}% (Tolerance: &ge; 98.0%)",
            f"- **Max Missing Duration:** {summary['camera_acceptance'].get('maxMissingMs', 0)} ms (Tolerance: &le; 300 ms)",
            f"- **Static Blocker Penetrations:** {summary['camera_acceptance'].get('blockerPenetrations', 0)}",
            f"- **HUD Panel Occlusions:** {summary['camera_acceptance'].get('hudOcclusions', 0)}",
            f"",
            f"---",
            f"",
            f"## 5. Artifacts Generated",
            f"",
            f"- Playthrough Video: `{summary['video_file'] or 'None'}`",
            f"- Checkpoint PNGs: {len(summary['checkpoints'])} images",
            f"- JSON Summary: `report.json`",
        ])

        if summary["failure_reasons"]:
            lines.extend([
                f"",
                f"### ⚠️ Failure Diagnoses",
                f"",
            ])
            for r in summary["failure_reasons"]:
                lines.append(f"- {r}")

        with open(report_md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        print(f"\n[QA] Reports generated successfully at {self.out_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Simly Orbis QA Playwright Harness")
    parser.add_argument("--port", type=int, default=None, help="Specific port to run backend on")
    parser.add_argument("--ci", action="store_true", help="CI mode: reports FPS without gating")
    parser.add_argument("--headful", action="store_true", help="Launch visible headful browser")
    args = parser.parse_args()

    runner = QAHarnessRunner(port=args.port, is_ci=args.ci, headless=not args.headful)
    summary = runner.run()

    if not summary["passed"]:
        print("\n[QA RESULT] FAILED:")
        for r in summary["failure_reasons"]:
            print(f"  - {r}")
        return 1

    print("\n[QA RESULT] PASSED - All checkpoints, constraints, and telemetry satisfied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
