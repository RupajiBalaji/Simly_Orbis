"""
P9: Concurrent load test for Simly Orbis API (`scripts/load_test.py`).

Spawns a local uvicorn server on an ephemeral port (unless `--url` is given),
runs N (default 200) concurrent session flows:
  1. POST /api/lab/sessions
  2. GET  /api/lab/sessions/{session_id}
  3. POST /api/lab/sessions/{session_id}/actions (wear_ppe)
Computes p50/p95/p99 latencies and writes `docs/LOAD_TEST.md` with real machine specs.
"""

from __future__ import annotations

import argparse
import asyncio
import ctypes
import os
import platform
import socket
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPORT = ROOT / "docs" / "LOAD_TEST.md"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _machine_specs() -> dict[str, str]:
    ram_gb = "unknown"
    try:
        if os.name == "nt":
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(stat)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            ram_gb = f"{stat.ullTotalPhys / (1024 ** 3):.1f} GB"
        else:
            import psutil  # type: ignore
            ram_gb = f"{psutil.virtual_memory().total / (1024 ** 3):.1f} GB"
    except Exception:
        pass

    return {
        "os": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "processor": platform.processor() or "unknown",
        "cpu_count": str(os.cpu_count() or "unknown"),
        "ram": ram_gb,
        "python": platform.python_version(),
    }


def _percentile(sorted_vals: list[float], pct: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = min(len(sorted_vals) - 1, max(0, int(round((pct / 100.0) * (len(sorted_vals) - 1)))))
    return sorted_vals[idx]


async def _run_one_flow(client: httpx.AsyncClient, idx: int) -> dict[str, Any]:
    latencies_ms: list[float] = []
    errors: list[str] = []
    hdrs = {"X-Forwarded-For": f"10.{(idx // 250) + 1}.{(idx % 250) + 1}.1"}

    t0 = time.perf_counter()
    r1 = await client.post("/api/lab/sessions", json={"experiment_id": "pk_ward", "nickname": f"Load_{idx}"}, headers=hdrs)
    latencies_ms.append((time.perf_counter() - t0) * 1000.0)
    if r1.status_code != 201:
        errors.append(f"POST /sessions -> {r1.status_code}")
        return {"latencies_ms": latencies_ms, "errors": errors}

    sid = r1.json()["session_id"]

    t1 = time.perf_counter()
    r2 = await client.get(f"/api/lab/sessions/{sid}", headers=hdrs)
    latencies_ms.append((time.perf_counter() - t1) * 1000.0)
    if r2.status_code != 200:
        errors.append(f"GET /sessions/{{id}} -> {r2.status_code}")

    t2 = time.perf_counter()
    r3 = await client.post(
        f"/api/lab/sessions/{sid}/actions",
        json={"action": "wear_ppe", "target": "ppe_station", "params": {"items": ["goggles", "gloves", "lab_coat"]}},
        headers=hdrs,
    )
    latencies_ms.append((time.perf_counter() - t2) * 1000.0)
    if r3.status_code != 200:
        errors.append(f"POST /actions -> {r3.status_code}")

    return {"latencies_ms": latencies_ms, "errors": errors}


async def _run_load(base_url: str, concurrency: int) -> dict[str, Any]:
    limits = httpx.Limits(max_connections=concurrency + 20, max_keepalive_connections=concurrency)
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0, limits=limits) as client:
        # Wait briefly for readiness
        for _ in range(40):
            try:
                r = await client.get("/api/lab/experiments")
                if r.status_code == 200:
                    break
            except Exception:
                pass
            await asyncio.sleep(0.25)

        wall_start = time.perf_counter()
        results = await asyncio.gather(*[_run_one_flow(client, i) for i in range(concurrency)])
        wall_s = time.perf_counter() - wall_start

    all_lat = sorted(lat for res in results for lat in res["latencies_ms"])
    all_err = [err for res in results for err in res["errors"]]
    return {
        "concurrency": concurrency,
        "total_requests": len(all_lat),
        "wall_seconds": round(wall_s, 3),
        "rps": round(len(all_lat) / wall_s, 1) if wall_s > 0 else 0.0,
        "p50_ms": round(_percentile(all_lat, 50), 2),
        "p95_ms": round(_percentile(all_lat, 95), 2),
        "p99_ms": round(_percentile(all_lat, 99), 2),
        "max_ms": round(max(all_lat) if all_lat else 0.0, 2),
        "median_ms": round(statistics.median(all_lat) if all_lat else 0.0, 2),
        "error_count": len(all_err),
        "sample_errors": all_err[:10],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run concurrent load test against Simly Orbis.")
    parser.add_argument("--concurrency", type=int, default=200)
    parser.add_argument("--url", default="")
    parser.add_argument("--output", default=str(DEFAULT_REPORT))
    args = parser.parse_args(argv)

    proc: subprocess.Popen | None = None
    base_url = args.url.strip()
    if not base_url:
        port = _free_port()
        base_url = f"http://127.0.0.1:{port}"
        env = os.environ.copy()
        env["MONGODB_URI"] = ""
        env["AI_ENABLED"] = "false"
        env["ENVIRONMENT"] = "development"
        env["TRUST_PROXY"] = "true"
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
            cwd=str(ROOT),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    try:
        stats = asyncio.run(_run_load(base_url, args.concurrency))
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    specs = _machine_specs()
    ts = datetime.now(timezone.utc).isoformat()
    err_note = ", ".join(stats["sample_errors"]) if stats["sample_errors"] else "None"
    md = f"""# Simly Orbis — Concurrent Load Test Report (`scripts/load_test.py`)

- **Timestamp (UTC):** {ts}
- **Target:** `{base_url}` (local uvicorn in-memory mode)
- **Workload:** {stats['concurrency']} concurrent virtual sessions × 3 requests (`POST /api/lab/sessions`, `GET /api/lab/sessions/{{id}}`, `POST /api/lab/sessions/{{id}}/actions`)

## Machine Specs
- **OS:** {specs['os']}
- **CPU:** {specs['processor']} ({specs['cpu_count']} logical cores)
- **RAM:** {specs['ram']}
- **Python:** {specs['python']}

## Measured Results
| Metric | Value |
| --- | --- |
| Concurrent sessions | {stats['concurrency']} |
| Total HTTP requests | {stats['total_requests']} |
| Wall-clock duration | {stats['wall_seconds']} s |
| Throughput | {stats['rps']} req/s |
| p50 latency | {stats['p50_ms']} ms |
| p95 latency | {stats['p95_ms']} ms |
| p99 latency | {stats['p99_ms']} ms |
| Max latency | {stats['max_ms']} ms |
| Errors | {stats['error_count']} |

- **Sample Errors:** {err_note}
"""
    out_path = Path(args.output)
    out_path.write_text(md, encoding="utf-8")
    print(f"Wrote {out_path} | p50={stats['p50_ms']}ms p95={stats['p95_ms']}ms p99={stats['p99_ms']}ms errors={stats['error_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
