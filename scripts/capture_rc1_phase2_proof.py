"""
Capture Proof Screenshot for RC1 Phase 2 (Audio & Consequences).
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
PORT = 9224
OUT_DIR = r"E:\Simly Orbis\docs\screenshots"
os.makedirs(OUT_DIR, exist_ok=True)

async def run_phase2_proof():
    user_data = r"C:\Users\rupaj\AppData\Local\Temp\chrome_rc1_p2_profile"
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
    time.sleep(2.5)

    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json") as resp:
            targets = json.loads(resp.read().decode())
        page_targets = [t for t in targets if t.get("type") == "page"]
        ws_url = page_targets[0]["webSocketDebuggerUrl"]

        async with websockets.connect(ws_url, max_size=25 * 1024 * 1024) as ws:
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
                return res.get("result", {}).get("result", {}).get("value")

            async def screenshot(filename):
                res = await send("Page.captureScreenshot", {"format": "png"})
                img_data = base64.b64decode(res["result"]["data"])
                path = os.path.join(OUT_DIR, filename)
                with open(path, "wb") as f:
                    f.write(img_data)
                print(f"Saved: {filename} ({len(img_data)} bytes)")
                return path

            await asyncio.sleep(2.0)
            await eval_js("(async () => { await window.startExperimentSession('pk_ward', 'Audio_Tester'); })()")
            await asyncio.sleep(2.0)

            # Test sound functions & volume slider
            audio_state = await eval_js("""
                (() => {
                    const soundBtn = document.getElementById('btn-toggle-sound');
                    const slider = document.getElementById('hud-volume-slider');
                    window.soundFX?.playClick();
                    window.soundFX?.playBalanceBeep();
                    window.soundFX?.playSuccessChime();
                    return {
                        muted: window.soundFX?.isMuted,
                        volume: window.soundFX?.volume,
                        btnText: soundBtn?.textContent,
                        sliderVal: slider?.value,
                    };
                })()
            """)
            print("Audio state: muted=", audio_state.get('muted'), "volume=", audio_state.get('volume'), "slider=", audio_state.get('sliderVal'))
            await screenshot("proof_rc1_2_1_sound_controls.png")

            # Trigger mistake demo for consequence animation
            print("Running Mistake Demo to verify consequence animation & alarm...")
            await eval_js("window.directorRunner.runMistakeDemo()")
            await asyncio.sleep(1.2)
            await screenshot("proof_rc1_2_2_consequence_animation.png")

            print("[SUCCESS] Phase 2 proof screenshots captured!")

    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    asyncio.run(run_phase2_proof())
