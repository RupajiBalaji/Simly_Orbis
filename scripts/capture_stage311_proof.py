"""
Capture Proof Screenshots for Stage 3.11: Camera and Label Fixes via Chrome CDP.
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
    user_data = r"C:\Users\rupaj\AppData\Local\Temp\chrome_stage311_profile"
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

            # -------------------------------------------------------------
            # Item 3: Start View framing the whole ward (avatar, balance, bed, trial screen)
            # -------------------------------------------------------------
            print("[3] Launching PK Ward and verifying first view after Start...")
            await eval_js("""
                (async () => {
                    await window.startExperimentSession('pk_ward', 'Alex Researcher');
                })()
            """)
            await asyncio.sleep(2.5)
            await take_screenshot("proof_ward_overview_framed.png")

            # -------------------------------------------------------------
            # Item 5: F3 Overlay & Disclaimer (no overlap)
            # -------------------------------------------------------------
            print("[4] Checking F3 overlay placement and disclaimer clearance...")
            await eval_js("""
                (() => {
                    const overlay = window.debugOverlay;
                    if (overlay && !window.state.debugOverlayActive) {
                        overlay.toggle();
                    }
                })()
            """)
            await asyncio.sleep(0.5)
            await take_screenshot("proof_f3_disclaimer_no_overlap.png")

            # Close F3 overlay for subsequent action shots
            await eval_js("""
                (() => {
                    const overlay = window.debugOverlay;
                    if (overlay && window.state.debugOverlayActive) {
                        overlay.toggle();
                    }
                })()
            """)
            await asyncio.sleep(0.3)

            # -------------------------------------------------------------
            # Item 1 & 2: WEIGH Action Camera (0%, 50%, 100%)
            # Side angle framing spatula & cup in hand, powder pile growing, balance display rising
            # -------------------------------------------------------------
            print("[5] Framing WEIGH action camera at 0%, 50%, 100%...")
            # 0%
            await eval_js("""
                (() => {
                    const sc = window.sceneManager;
                    const cc = window.characterController;
                    const bal = sc.getApparatus('digital_balance');
                    const balPos = new THREE.Vector3();
                    bal.getWorldPosition(balPos);
                    cc.rig.root.position.copy(bal.userData.stationPos);
                    cc.faceTarget(balPos);
                    const props = cc.createHeldProp('weigh');
                    cc.carryItem(props.right, props.left);
                    bal.userData.updateWeighProgress(0.0, 0.500);
                    sc.startActionCamera(balPos, cc.rig.root.position, 1800, 'weigh', 'digital_balance');
                    cc.animator.sampleClipAtProgress('weigh', 0.0, balPos);
                })()
            """)
            await asyncio.sleep(0.6)
            await take_screenshot("proof_action_weigh_0.png")

            # 50%
            await eval_js("""
                (() => {
                    const sc = window.sceneManager;
                    const cc = window.characterController;
                    const bal = sc.getApparatus('digital_balance');
                    const balPos = new THREE.Vector3();
                    bal.getWorldPosition(balPos);
                    bal.userData.updateWeighProgress(0.5, 0.500);
                    cc.animator.sampleClipAtProgress('weigh', 0.5, balPos);
                })()
            """)
            await asyncio.sleep(0.4)
            await take_screenshot("proof_action_weigh_50.png")

            # 100%
            await eval_js("""
                (() => {
                    const sc = window.sceneManager;
                    const cc = window.characterController;
                    const bal = sc.getApparatus('digital_balance');
                    const balPos = new THREE.Vector3();
                    bal.getWorldPosition(balPos);
                    bal.userData.updateWeighProgress(1.0, 0.500);
                    cc.animator.sampleClipAtProgress('weigh', 1.0, balPos);
                })()
            """)
            await asyncio.sleep(0.4)
            await take_screenshot("proof_action_weigh_100.png")

            # End action camera
            await eval_js("window.sceneManager.endActionCamera();")
            await asyncio.sleep(0.5)

            # -------------------------------------------------------------
            # Item 1: POUR Action Camera (0%, 50%, 100%)
            # Side angle framing water jug, cup, hands, and stream
            # -------------------------------------------------------------
            print("[6] Framing POUR action camera at 0%, 50%, 100%...")
            # 0%
            await eval_js("""
                (() => {
                    const sc = window.sceneManager;
                    const cc = window.characterController;
                    const cup = sc.getApparatus('dosing_cup');
                    const cupPos = new THREE.Vector3();
                    cup.getWorldPosition(cupPos);
                    cc.rig.root.position.copy(cup.userData.stationPos);
                    cc.faceTarget(cupPos);

                    const cupProp = sc.getApparatus('dosing_cup')?.clone();
                    if (cupProp) cupProp.scale.set(0.5, 0.5, 0.5);
                    const jugProp = sc.getApparatus('water_jug')?.clone();
                    if (jugProp) jugProp.scale.set(0.35, 0.35, 0.35);
                    cc.carryItem(jugProp, cupProp);

                    sc.startActionCamera(cupPos, cc.rig.root.position, 1800, 'pour', 'dosing_cup');
                    cc.animator.sampleClipAtProgress('pour', 0.0, cupPos);
                })()
            """)
            await asyncio.sleep(0.6)
            await take_screenshot("proof_action_pour_0.png")

            # 50%
            await eval_js("""
                (() => {
                    const sc = window.sceneManager;
                    const cc = window.characterController;
                    const cup = sc.getApparatus('dosing_cup');
                    const cupPos = new THREE.Vector3();
                    cup.getWorldPosition(cupPos);
                    cc.animator.sampleClipAtProgress('pour', 0.5, cupPos);
                })()
            """)
            await asyncio.sleep(0.4)
            await take_screenshot("proof_action_pour_50.png")

            # 100%
            await eval_js("""
                (() => {
                    const sc = window.sceneManager;
                    const cc = window.characterController;
                    const cup = sc.getApparatus('dosing_cup');
                    const cupPos = new THREE.Vector3();
                    cup.getWorldPosition(cupPos);
                    cc.animator.sampleClipAtProgress('pour', 1.0, cupPos);
                })()
            """)
            await asyncio.sleep(0.4)
            await take_screenshot("proof_action_pour_100.png")

            await eval_js("window.sceneManager.endActionCamera();")
            await asyncio.sleep(0.5)

            # -------------------------------------------------------------
            # Switch to Titration Bench for TITRATE and PIPETTE
            # -------------------------------------------------------------
            print("[7] Switching to Titration Bench for Titrate & Pipette action camera...")
            await eval_js("""
                (async () => {
                    await window.startExperimentSession('titration_bench', 'Chemist Orbis');
                })()
            """)
            await asyncio.sleep(2.5)

            # TITRATE (0%, 50%, 100%)
            print("[8] Framing TITRATE action camera at 0%, 50%, 100%...")
            # 0%
            await eval_js("""
                (() => {
                    const sc = window.sceneManager;
                    const cc = window.characterController;
                    cc.dropHeldItem();
                    const bur = sc.getApparatus('burette');
                    const burPos = new THREE.Vector3(0, 1.4, -2.0);
                    if (bur) bur.getWorldPosition(burPos);
                    cc.rig.root.position.set(-0.48, 0, -1.65);
                    cc.faceTarget(new THREE.Vector3(0.02, 1.25, -1.85));

                    sc.startActionCamera(burPos, cc.rig.root.position, 1800, 'titrate', 'burette');
                    cc.animator.sampleClipAtProgress('titrate', 0.0, burPos);
                })()
            """)
            await asyncio.sleep(0.6)
            await take_screenshot("proof_action_titrate_0.png")

            # 50%
            await eval_js("""
                (() => {
                    const sc = window.sceneManager;
                    const cc = window.characterController;
                    const bur = sc.getApparatus('burette');
                    const burPos = new THREE.Vector3(0, 1.4, -2.0);
                    if (bur) bur.getWorldPosition(burPos);
                    cc.animator.sampleClipAtProgress('titrate', 0.5, burPos);
                })()
            """)
            await asyncio.sleep(0.4)
            await take_screenshot("proof_action_titrate_50.png")

            # 100%
            await eval_js("""
                (() => {
                    const sc = window.sceneManager;
                    const cc = window.characterController;
                    const bur = sc.getApparatus('burette');
                    const burPos = new THREE.Vector3(0, 1.4, -2.0);
                    if (bur) bur.getWorldPosition(burPos);
                    cc.animator.sampleClipAtProgress('titrate', 1.0, burPos);
                })()
            """)
            await asyncio.sleep(0.4)
            await take_screenshot("proof_action_titrate_100.png")

            await eval_js("window.sceneManager.endActionCamera();")
            await asyncio.sleep(0.5)

            # PIPETTE (0%, 50%, 100%)
            print("[9] Framing PIPETTE action camera at 0%, 50%, 100%...")
            # 0%
            await eval_js("""
                (() => {
                    const sc = window.sceneManager;
                    const cc = window.characterController;
                    cc.dropHeldItem();
                    const flask = sc.getApparatus('conical_flask');
                    const flaskPos = new THREE.Vector3(0.02, 1.05, -1.85);
                    if (flask) flask.getWorldPosition(flaskPos);
                    cc.rig.root.position.set(-0.48, 0, -1.65);
                    cc.faceTarget(flaskPos);

                    const pipProp = cc.createHeldProp('pipette_analyte');
                    cc.carryItem(pipProp);

                    sc.startActionCamera(flaskPos, cc.rig.root.position, 1800, 'pipette', 'conical_flask');
                    cc.animator.sampleClipAtProgress('pipette', 0.0, flaskPos);
                })()
            """)
            await asyncio.sleep(0.6)
            await take_screenshot("proof_action_pipette_0.png")

            # 50%
            await eval_js("""
                (() => {
                    const sc = window.sceneManager;
                    const cc = window.characterController;
                    const flask = sc.getApparatus('conical_flask');
                    const flaskPos = new THREE.Vector3(0.02, 1.05, -1.85);
                    if (flask) flask.getWorldPosition(flaskPos);
                    cc.animator.sampleClipAtProgress('pipette', 0.5, flaskPos);
                })()
            """)
            await asyncio.sleep(0.4)
            await take_screenshot("proof_action_pipette_50.png")

            # 100%
            await eval_js("""
                (() => {
                    const sc = window.sceneManager;
                    const cc = window.characterController;
                    const flask = sc.getApparatus('conical_flask');
                    const flaskPos = new THREE.Vector3(0.02, 1.05, -1.85);
                    if (flask) flask.getWorldPosition(flaskPos);
                    cc.animator.sampleClipAtProgress('pipette', 1.0, flaskPos);
                })()
            """)
            await asyncio.sleep(0.4)
            await take_screenshot("proof_action_pipette_100.png")

            await eval_js("window.sceneManager.endActionCamera();")
            await asyncio.sleep(0.5)

            # -------------------------------------------------------------
            # Item 4: Trial Wording & Simulated Regimen in PK Ward
            # -------------------------------------------------------------
            print("[10] Switching back to PK Ward for Trial wording & Simulated Regimen...")
            await eval_js("""
                (async () => {
                    await window.startExperimentSession('pk_ward', 'Trial Specialist');
                    await window.trialPanel.open();
                    await window.trialPanel.runTrialSimulation();
                })()
            """)
            await asyncio.sleep(3.0)
            await take_screenshot("proof_trial_wording_regimen.png")

            print("\n[SUCCESS] All Stage 3.11 proof screenshots captured successfully!")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    asyncio.run(main())
