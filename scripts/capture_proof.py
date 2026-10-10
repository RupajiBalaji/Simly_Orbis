"""
Capture Proof Screenshots for Orbis Virtual Clinical Trial via Chrome CDP.
"""

import asyncio
import base64
import json
import os
import subprocess
import time
import urllib.request
import websockets

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PORT = 9222
OUT_DIR = r"E:\Simly Orbis\docs\screenshots"
os.makedirs(OUT_DIR, exist_ok=True)


async def main():
    user_data = r"C:\Users\rupaj\AppData\Local\Temp\chrome_proof_profile"
    # 1. Launch Chrome in headless mode with remote debugging
    proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        "--no-sandbox",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data}",
        f"--remote-debugging-port={PORT}",
        "--window-size=1440,900",
        "--hide-scrollbars",
        "http://127.0.0.1:8000/",
    ])
    print("[1] Chrome launched with remote debugging.")
    time.sleep(2.5)

    try:
        # Get devtools WebSocket URL
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json") as resp:
            targets = json.loads(resp.read().decode())
        ws_url = targets[0]["webSocketDebuggerUrl"]
        print(f"[2] Connecting to CDP: {ws_url}")

        async with websockets.connect(ws_url, max_size=20 * 1024 * 1024) as ws:
            msg_id = 0

            async def send(method, params=None):
                nonlocal msg_id
                msg_id += 1
                req = {"id": msg_id, "method": method, "params": params or {}}
                await ws.send(json.dumps(req))
                while True:
                    raw = await ws.recv()
                    data = json.loads(raw)
                    if data.get("id") == msg_id:
                        return data

            async def eval_js(code):
                res = await send("Runtime.evaluate", {
                    "expression": code,
                    "awaitPromise": True,
                    "returnByValue": True,
                })
                return res.get("result", {}).get("value")

            async def take_screenshot(filename):
                res = await send("Page.captureScreenshot", {"format": "png"})
                b64 = res["result"]["data"]
                filepath = os.path.join(OUT_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(b64))
                print(f"[SCREENSHOT SAVED]: {filepath}")

            await send("Page.enable")
            await send("Runtime.enable")

            # Wait for main page to load
            await asyncio.sleep(2.0)

            # Step 1: Click "Enter Ward" in District Lobby
            print("[3] Launching PK Ward session...")
            await eval_js("""
                (() => {
                    const btn = document.querySelector('#card-district-pharma .btn-launch');
                    if (btn) btn.click();
                })()
            """)
            await asyncio.sleep(1.0)

            # Step 2: In brief modal, click "Launch 3D Laboratory"
            await eval_js("""
                (() => {
                    const btn = document.getElementById('btn-start-experiment');
                    if (btn) btn.click();
                })()
            """)
            await asyncio.sleep(3.0)

            # Step 3: Turn on F3 Debug Overlay
            print("[4] Enabling F3 debug overlay...")
            await eval_js("""
                (() => {
                    if (window.debugOverlay) window.debugOverlay.toggle();
                })()
            """)
            await asyncio.sleep(0.5)

            # Step 4: Open Virtual Trial Hall
            print("[5] Opening Virtual Trial Hall...")
            await eval_js("""
                (() => {
                    if (window.trialPanel) window.trialPanel.open();
                })()
            """)
            await asyncio.sleep(2.0)

            # Capture Screenshot 1: Trial Hall Before Run (with F3 FPS)
            print("[6] Capturing trial hall before run...")
            await take_screenshot("trial_hall_before_run.png")

            # Step 5: Execute Virtual Clinical Trial
            print("[7] Executing Virtual Clinical Trial simulation...")
            await eval_js("""
                window.trialPanel.runTrialSimulation();
            """)
            await asyncio.sleep(3.0)  # Wait for wave and charts

            # Capture Screenshot 2: Trial Hall After Run (with crowd wave and charts)
            print("[8] Capturing trial hall after run...")
            await take_screenshot("trial_hall_after_run.png")

            # Step 6: Click "Compare with Standard Dose"
            print("[9] Opening Regimen Comparison View...")
            await eval_js("""
                window.trialPanel.runTrialComparison();
            """)
            await asyncio.sleep(2.0)

            # Capture Screenshot 3: Regimen Comparison View
            print("[10] Capturing trial compare view...")
            await take_screenshot("trial_hall_compare_view.png")

            print("\n[SUCCESS] All proof screenshots captured successfully!")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    asyncio.run(main())
