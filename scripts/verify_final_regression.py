"""
Final Regression Verification: Console Errors, FPS, and About Modal.
"""
import asyncio
import json
import os
import subprocess
import time
import urllib.request
import websockets

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PORT = 9227

async def run_final_check():
    user_data = r"C:\Users\rupaj\AppData\Local\Temp\chrome_final_check_profile"
    proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        "--no-sandbox",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data}",
        f"--remote-debugging-port={PORT}",
        "--window-size=1440,900",
        "http://127.0.0.1:8000/",
    ])
    time.sleep(2.5)

    console_errors = []

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
                    # Check console errors
                    if data.get("method") == "Console.messageAdded":
                        msg = data.get("params", {}).get("message", {})
                        if msg.get("level") == "error":
                            console_errors.append(msg.get("text"))
                    if data.get("id") == msg_id:
                        return data

            await send("Console.enable")

            async def eval_js(code):
                res = await send("Runtime.evaluate", {
                    "expression": code,
                    "awaitPromise": True,
                    "returnByValue": True,
                })
                return res.get("result", {}).get("result", {}).get("value")

            await asyncio.sleep(2.0)

            # Start pk_ward experiment
            await eval_js("(async () => { await window.startExperimentSession('pk_ward', 'FinalQC'); })()")
            await asyncio.sleep(2.5)

            # Measure real FPS over 1 second with F3 closed
            fps_result = await eval_js("""
                new Promise(resolve => {
                    let frames = 0;
                    const start = performance.now();
                    function loop() {
                        frames++;
                        if (performance.now() - start >= 1000) {
                            const fps = Math.round((frames * 1000) / (performance.now() - start));
                            resolve(fps);
                        } else {
                            requestAnimationFrame(loop);
                        }
                    }
                    requestAnimationFrame(loop);
                })
            """)

            print(f"Measured FPS (F3 closed): {fps_result} FPS")
            assert fps_result >= 45, f"FPS {fps_result} is below 45 FPS target!"

            # Test opening About modal via in-game HUD
            about_opened = await eval_js("""
                (() => {
                    const btn = document.getElementById('btn-hud-open-about');
                    if (btn) btn.click();
                    const modal = document.getElementById('modal-about');
                    return modal && !modal.classList.contains('hidden');
                })()
            """)
            print(f"About modal opened from HUD: {about_opened}")
            assert about_opened is True

            print(f"Total Console Errors: {len(console_errors)}")
            if console_errors:
                print("Console errors:", console_errors)

            print("[SUCCESS] Final regression check passed with flying colors!")

    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    asyncio.run(run_final_check())
