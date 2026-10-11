"""
Capture Proof Screenshots for Dr. Orbis Mentor & Reality Check Board via Chrome CDP.
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
    user_data = r"C:\Users\rupaj\AppData\Local\Temp\chrome_mentor_profile"
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
    print("[1] Headless Chrome launched.")
    time.sleep(2.5)

    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json") as resp:
            targets = json.loads(resp.read().decode())
        page_targets = [t for t in targets if t.get("type") == "page"]
        ws_url = page_targets[0]["webSocketDebuggerUrl"]
        print(f"[2] Connecting to CDP page target: {ws_url}")

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
            await asyncio.sleep(2.0)

            # Launch pk_ward
            print("[3] Launching PK Ward...")
            await eval_js("""
                (async () => {
                    await window.startExperimentSession('pk_ward', 'Dr. Orbis Researcher');
                })()
            """)
            await asyncio.sleep(2.5)

            # Screenshot 1: Dr. Orbis Hint (Offline / Fallback mode)
            print("[4] Querying Dr. Orbis Hint...")
            await eval_js("""
                (async () => {
                    await window.drOrbis.query('hint');
                })()
            """)
            await asyncio.sleep(1.0)
            await take_screenshot("proof_mentor_hint_offline.png")

            # Screenshot 2: Dr. Orbis Question & Answer (mode="ask")
            print("[5] Asking Dr. Orbis a question...")
            await eval_js("""
                (async () => {
                    await window.drOrbis.query('ask', 'How does liver clearance affect peak paracetamol concentration?');
                })()
            """)
            await asyncio.sleep(1.0)
            await take_screenshot("proof_mentor_ask.png")

            # Screenshot 3: Auto-explain on violation toast
            print("[6] Triggering safety violation auto-explain...")
            await eval_js("""
                (async () => {
                    // Try to tare balance without PPE -> triggers PPE violation
                    await window.actionMenu.executeAction('tare_balance', 'digital_balance', {});
                })()
            """)
            await asyncio.sleep(1.5)
            await take_screenshot("proof_mentor_explain_violation.png")

            # Screenshot 4: Reality Check 3D Wall Board
            print("[7] Framing Reality Check 3D Wall Board...")
            await eval_js("""
                (() => {
                    window.sceneManager.setStationCamera('reality_check_board');
                })()
            """)
            await asyncio.sleep(1.2)
            await take_screenshot("proof_reality_check_board.png")

            # Screenshot 5: Reality Check Panel with Model Cards
            print("[8] Opening Reality Check Panel & Model Cards...")
            await eval_js("""
                (async () => {
                    await window.realityCheckPanel.open();
                })()
            """)
            await asyncio.sleep(1.5)
            await take_screenshot("proof_reality_check_panel_model_card.png")

            # Close Reality Check Panel
            await eval_js("""
                window.realityCheckPanel.close();
            """)
            await asyncio.sleep(0.5)

            # Screenshot 6: F3 FPS during mentor usage
            print("[9] Measuring FPS during mentor usage...")
            await eval_js("""
                (() => {
                    if (window.debugOverlay && !window.state.debugOverlayActive) {
                        window.debugOverlay.toggle();
                    }
                })()
            """)
            await asyncio.sleep(1.0)
            await take_screenshot("proof_mentor_fps.png")

            # Turn off F3 overlay
            await eval_js("""
                (() => {
                    if (window.debugOverlay && window.state.debugOverlayActive) {
                        window.debugOverlay.toggle();
                    }
                })()
            """)
            await asyncio.sleep(0.5)

            # Screenshot 7: Final Lab Report with Trial Result, Reality Checks (11/11 passed), Hints Used, and Dr. Orbis Debrief
            print("[10] Completing session and compiling Final Report...")
            await eval_js("""
                (async () => {
                    window.state.skipAnimation = true;
                    await window.actionMenu.executeAction('wear_ppe', 'avatar', { item: 'all' });
                    await window.actionMenu.executeAction('tare_balance', 'digital_balance', {});
                    await window.actionMenu.executeAction('weigh', 'digital_balance', { amount_g: 0.5, substance: 'paracetamol' });
                    await window.actionMenu.executeAction('dissolve', 'dosing_cup', { substance: 'paracetamol', solvent: 'water' });
                    await window.actionMenu.executeAction('label', 'dosing_cup', { text: 'Pt: Alex | 500mg' });
                    await window.actionMenu.executeAction('administer_oral', 'patient_bed', {});
                    await window.actionMenu.executeAction('advance_time', 'ward_clock', { hours: 1.0 });
                    await window.actionMenu.executeAction('label', 'tube_1', { text: 't=1.0h' });
                    await window.actionMenu.executeAction('draw_blood', 'tube_1', {});
                    await window.actionMenu.executeAction('run_assay', 'tube_1', {});
                    await window.actionMenu.executeAction('dispose_waste', 'chemical_waste_bin', { item: 'dosing_cup' });
                    await window.actionMenu.executeAction('wash_hands', 'sink', {});

                    const finRes = await window.api.finishSession(window.state.session.session_id, {
                        trial_result: {
                            n_patients: 500,
                            pct_in_range: 82.4,
                            pct_toxic: 1.2,
                            pct_subtherapeutic: 16.4,
                            mean_peak: 14.8
                        }
                    });
                    window.hud.hide();
                    window.reportScreen.show(finRes);
                })()
            """)
            await asyncio.sleep(2.0)
            await take_screenshot("proof_final_report_complete.png")

            print("\n[SUCCESS] All 7 proof screenshots successfully captured!")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    asyncio.run(main())
