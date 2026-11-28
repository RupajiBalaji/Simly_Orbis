# Simly Orbis — Security Checklist (P9)

All checks below were executed against the current codebase and virtual environment (`.venv_space`).

## 1. Dependency Vulnerability Audit (`pip-audit`)
Command run:
```powershell
.venv_space\Scripts\python.exe -m pip_audit --version
```
Observed output:
```text
E:\Simly Orbis\.venv_space\Scripts\python.exe: No module named pip_audit
```
Status: **Not run (`pip_audit` is not installed in `.venv_space`).** Install `pip-audit` in a network-connected environment and run `python -m pip_audit -r backend/requirements.txt` before production deployment.

## 2. Content Security Policy & Security Headers
Command run:
```powershell
$env:PYTHONPATH="backend"
.venv_space\Scripts\python.exe -c "from fastapi.testclient import TestClient; from app.main import app; c = TestClient(app); r = c.get('/health'); print('STATUS:', r.status_code); print('CSP:', r.headers.get('content-security-policy')); print('HEADERS:', dict(r.headers))"
```
Observed output:
```text
CSP: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; font-src 'self'; media-src 'self' blob:; frame-ancestors 'none';
x-content-type-options: nosniff
referrer-policy: strict-origin-when-cross-origin
x-frame-options: DENY
permissions-policy: camera=(), microphone=(self), geolocation=()
```
Note: `unsafe-inline` is currently required for inline `<script>` / `<style>` in static pages (`teacher.html`, `student.html`, `expert.html`); moving inline scripts to external JS modules is recommended post-pilot.

## 3. Secrets Scan (`GEMINI_API_KEY` in `backend/`)
Command run:
```powershell
Select-String -Path backend/app/*.py,backend/app/*/*.py -Pattern "GEMINI_API_KEY"
```
Observed output:
```text
backend\app\ai.py:5:- Pluggable AIProvider interface (default: GeminiProvider when GEMINI_API_KEY is set)
backend\app\ai.py:105:    gemini_key = settings.gemini_api_key.strip()
backend\app\config.py:9:    gemini_api_key: str = ""
backend\app\main.py:251:        "has_api_key": bool(settings.gemini_api_key.strip()),
backend\app\main.py:254:        "active_mode": "gemini" if (settings.ai_enabled and bool(settings.gemini_api_key.strip())) else "rule_based_fallback",
backend\app\security.py:212:    has_gemini = bool(settings.gemini_api_key.strip())
```
Result: **PASS** — no hardcoded API keys in `backend/app/`; read exclusively from `settings.gemini_api_key` (environment/config).

## 4. Rate Limiting Verification
- Covered by `backend/tests/test_classroom_auth_matrix.py::test_auth_rate_limit_spoofed_xff_and_student_token_expiry` (verifies `TRUST_PROXY=False` blocks XFF spoofing and returns `429` on the 16th auth attempt/min) and `backend/tests/test_classroom_join.py::test_student_join_rate_limit`.
- Shared `resolve_client_ip(request)` in `app.security` is used across middleware, `/api/specs/*`, and `/api/classroom/*`.

## 5. Authorization Matrix & Server-Verified Submissions
- Covered by `backend/tests/test_classroom_auth_matrix.py` (guest, expert, student_own, student_other, teacher_other, teacher_own) and `backend/tests/test_classroom_submissions_verified.py` (server-side lookup of `lab_reports`, forged scores ignored, cross-student/wrong-experiment/unfinished/double-submit rejected).
- Cross-tenant teacher class access returns `404 Not Found` (`_get_owned_class`).
- CSV export prefixes formula characters (`=`, `+`, `-`, `@`) with `'`.
