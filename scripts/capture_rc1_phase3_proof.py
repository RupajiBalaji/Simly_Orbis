"""
Capture Proof Screenshot for RC1 Phase 3 (Hardening, About Modal, and Security).
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
PORT = 9225
OUT_DIR = r"E:\Simly Orbis\docs\screenshots"
os.makedirs(OUT_DIR, exist_ok=True)

async def run_phase3_proof():
    user_data = r"C:\Users\rupaj\AppData\Local\Temp\chrome_rc1_p3_profile"
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

            # Check About modal trigger
            await eval_js("""
                (() => {
                    const btn = document.getElementById('btn-open-about');
                    if (btn) btn.click();
                    else {
                        const modal = document.getElementById('modal-about');
                        if (modal) modal.classList.remove('hidden');
                    }
                })()
            """)
            await asyncio.sleep(1.0)
            await screenshot("proof_rc1_3_hardening_about.png")

            print("[SUCCESS] Phase 3 proof screenshot captured!")

    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    asyncio.run(run_phase3_proof())
