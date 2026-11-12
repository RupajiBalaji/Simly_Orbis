#!/usr/bin/env python3
"""
scripts/smoke_live.py
Live-site and local-server smoke checker for Simly Orbis.
Uses Python standard library only (urllib).

Usage:
  python scripts/smoke_live.py [--base-url URL] [--allow-memory] [--timeout SECONDS]

Educational simulation platform. Not medical advice. Not clinical evidence.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Extract local app_version from backend/app/config.py
ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT_DIR / "backend" / "app" / "config.py"


def get_local_version() -> str:
    if not CONFIG_FILE.exists():
        return "unknown"
    for line in CONFIG_FILE.read_text(encoding="utf-8").splitlines():
        if "app_version:" in line or 'app_version: str = "' in line or 'app_version = "' in line:
            parts = line.split('"')
            if len(parts) >= 2:
                return parts[1]
    return "0.2.0"


def main() -> int:
    parser = argparse.ArgumentParser(description="Simly Orbis smoke checker (stdlib urllib only)")
    parser.add_argument("--base-url", default="https://simly-orbis.onrender.com", help="Target base URL")
    parser.add_argument("--allow-memory", action="store_true", help="Allow storage_mode == 'memory' instead of failing")
    parser.add_argument("--timeout", type=float, default=60.0, help="Wake-up timeout in seconds")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    local_ver = get_local_version()

    print(f"[SMOKE] Starting smoke check against: {base_url}")
    print(f"[SMOKE] Local repo version: {local_ver}")

    results: list[dict[str, str]] = []
    overall_passed = True

    # 1. Measure wake time of /api/ping with retries
    ping_url = f"{base_url}/api/ping"
    print(f"[SMOKE] Checking /api/ping (wake up)...")
    start_time = time.time()
    ping_ok = False
    ping_elapsed = 0.0
    retries = 0

    while time.time() - start_time < args.timeout:
        retries += 1
        try:
            req = urllib.request.Request(ping_url, headers={"User-Agent": "SimlyOrbisSmokeCheck/1.0"})
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data.get("ping") == "pong":
                        ping_elapsed = time.time() - t0
                        total_wake_time = time.time() - start_time
                        ping_ok = True
                        break
        except Exception:
            time.sleep(2.0)

    if ping_ok:
        results.append({
            "check": "/api/ping Wakeup",
            "status": "PASS",
            "detail": f"Awake in {total_wake_time:.2f}s ({retries} attempts, last ping {ping_elapsed*1000:.1f}ms)",
        })
    else:
        overall_passed = False
        results.append({
            "check": "/api/ping Wakeup",
            "status": "FAIL",
            "detail": f"Failed to wake within {args.timeout}s timeout ({retries} attempts)",
        })

    # 2. Call /api/health
    health_url = f"{base_url}/api/health"
    print(f"[SMOKE] Checking /api/health...")
    health_ok = False
    server_ver = "unknown"
    storage_mode = "unknown"
    try:
        req = urllib.request.Request(health_url, headers={"User-Agent": "SimlyOrbisSmokeCheck/1.0"})
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            if resp.status == 200:
                h_data = json.loads(resp.read().decode("utf-8"))
                server_ver = str(h_data.get("app_version") or h_data.get("version") or "unknown")
                storage_mode = str(h_data.get("storage_mode", "unknown"))
                health_ok = True
    except Exception as e:
        health_detail = f"Request error: {e}"

    if health_ok:
        # Check storage_mode
        if storage_mode == "mongodb":
            storage_status = "PASS"
            storage_detail = f"storage_mode = 'mongodb'"
        elif args.allow_memory:
            storage_status = "PASS"
            storage_detail = f"storage_mode = '{storage_mode}' (allowed via --allow-memory)"
        else:
            storage_status = "FAIL"
            overall_passed = False
            storage_detail = f"storage_mode is '{storage_mode}' (expected 'mongodb', pass --allow-memory for local/dev)"

        results.append({"check": "/api/health Endpoint", "status": "PASS", "detail": f"HTTP 200 OK"})
        results.append({"check": "Database Storage Mode", "status": storage_status, "detail": storage_detail})

        # Version check
        ver_status = "PASS"
        if server_ver != local_ver:
            ver_detail = f"WARNING: Remote server version '{server_ver}' differs from local repo '{local_ver}'"
        else:
            ver_detail = f"Server version matches local repo '{server_ver}'"
        results.append({"check": "App Version Consistency", "status": ver_status, "detail": ver_detail})
    else:
        overall_passed = False
        results.append({"check": "/api/health Endpoint", "status": "FAIL", "detail": health_detail})

    # 3. Check Web Pages & Static Assets
    paths_to_check = [
        ("/", "Main Landing / Lobby Page"),
        ("/index.html", "Lab Simulation Page"),
        ("/vendor/three.module.js", "Vendored Three.js r160 Asset"),
        ("/lab/main.js", "Main Laboratory Application JS"),
    ]

    sec_headers_checked = False
    found_headers: dict[str, str] = {}

    for p, desc in paths_to_check:
        url = f"{base_url}{p}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SimlyOrbisSmokeCheck/1.0"})
            with urllib.request.urlopen(req, timeout=15.0) as resp:
                status_code = resp.status
                if not sec_headers_checked:
                    sec_headers_checked = True
                    for h in ["Content-Security-Policy", "X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy"]:
                        val = resp.headers.get(h)
                        if val:
                            found_headers[h] = val

                if status_code == 200:
                    results.append({"check": f"HTTP 200: {p}", "status": "PASS", "detail": desc})
                else:
                    overall_passed = False
                    results.append({"check": f"HTTP 200: {p}", "status": "FAIL", "detail": f"Status {status_code}"})
        except Exception as e:
            overall_passed = False
            results.append({"check": f"HTTP 200: {p}", "status": "FAIL", "detail": f"Error: {e}"})

    # 4. Security Headers Check
    expected_sec_headers = ["Content-Security-Policy", "X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy"]
    missing_headers = [h for h in expected_sec_headers if h not in found_headers]

    if not missing_headers:
        results.append({
            "check": "Security Headers",
            "status": "PASS",
            "detail": f"Present: {', '.join(found_headers.keys())}",
        })
    else:
        overall_passed = False
        results.append({
            "check": "Security Headers",
            "status": "FAIL",
            "detail": f"Missing headers: {', '.join(missing_headers)}",
        })

    # Print Report Table
    print("\n" + "=" * 80)
    print("SIMLY ORBIS LIVE-SITE & ENDPOINT SMOKE CHECK RESULTS")
    print("=" * 80)
    print(f"{'Check':<30} | {'Status':<6} | {'Details'}")
    print("-" * 80)
    for r in results:
        status_flag = "PASS" if r["status"] == "PASS" else "FAIL"
        print(f"{r['check']:<30} | {status_flag:<6} | {r['detail']}")
    print("=" * 80)

    if overall_passed:
        print("\n[SMOKE RESULT] ALL CHECKS PASSED.")
        return 0
    else:
        print("\n[SMOKE RESULT] SMOKE CHECK FAILED.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
