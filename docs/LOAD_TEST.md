# Simly Orbis — Concurrent Load Test Report (`scripts/load_test.py`)

- **Timestamp (UTC):** 2026-11-28T15:00:23.081151+00:00
- **Target:** `http://127.0.0.1:58337` (local uvicorn in-memory mode)
- **Workload:** 200 concurrent virtual sessions × 3 requests (`POST /api/lab/sessions`, `GET /api/lab/sessions/{id}`, `POST /api/lab/sessions/{id}/actions`)

## Machine Specs
- **OS:** Windows 11 (AMD64)
- **CPU:** AMD64 Family 23 Model 104 Stepping 1, AuthenticAMD (16 logical cores)
- **RAM:** 15.3 GB
- **Python:** 3.14.5

## Measured Results
| Metric | Value |
| --- | --- |
| Concurrent sessions | 200 |
| Total HTTP requests | 600 |
| Wall-clock duration | 5.314 s |
| Throughput | 112.9 req/s |
| p50 latency | 777.83 ms |
| p95 latency | 3379.5 ms |
| p99 latency | 4615.85 ms |
| Max latency | 5166.1 ms |
| Errors | 0 |

- **Sample Errors:** None
