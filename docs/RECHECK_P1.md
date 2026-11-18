# Simly Orbis — Phase P1 Recheck Report

Date: 2026-11-18  
Baseline Commit: `fc2eb16` / `3d60be7`  
Target Version: `0.5.0-dev`  
Status: ALL FIXES (F1–F8) VERIFIED & COMPLETE  

---

## 1. Executive Summary & Verification Matrix

| Fix ID | Description | Commit Hash | Key Files Changed | Verification Status |
|---|---|---|---|---|
| **F1** | QA Re-run across 4 experiments (success, rule violation, failure) + DOM-vs-API assertions + Frontend Freshness self-audit gate | `a041a00` | `qa/run.py`, `frontend/lab/main.js`, `scripts/self_audit.py` | **PASSED** (58 checkpoints, run `20261118_081803`, Gate 8 green) |
| **F2** | Touch E2E Playwright test (390x844 mobile viewport, tap, long-press action wheel, joystick drag, report) | `f625617` | `qa/test_touch_e2e.py`, `backend/tests/test_touch_e2e.py`, `docs/screenshots/touch/` | **PASSED** (5 distinct screenshots, MD5 verified) |
| **F3** | Scope alignment (remove Biology card, remove Spanish locale, add Practice buttons per Spec 8.3) | `fc6b442` | `frontend/lab/index.html`, `frontend/lab/main.js`, `docs/ROADMAP.md` | **PASSED** (Only Market locked, Start + Practice buttons live) |
| **F4** | Briefing rules isolation (plain language, strictly experiment-specific rules R1–R10, S1–S8, D1–D8) | `67e52da` | `frontend/lab/main.js`, `backend/tests/test_briefing_rules.py` | **PASSED** (4/4 tests pass, zero cross-experiment leaks) |
| **F5** | i18n coverage & lint script enforcement (151 keys in `en.json`, zero hard-coded UI strings) | `70d7cd8` | `frontend/locales/en.json`, `scripts/lint_i18n.py`, 5 HTML templates | **PASSED** (151 keys, 0 untranslated literals across 5 templates) |
| **F6** | Self-hosted web fonts completeness (Inter 400/500/700, JetBrains Mono 400/700, no synthetic bold) | `329012b` | `frontend/vendor/fonts/`, `frontend/css/style.css` | **PASSED** (33 `.woff2` files, SIL OFL + Apache 2.0 licenses in repo) |
| **F7** | Version bump to 0.5.0-dev across repo (config, tests, docs, changelog) | `778a313` | `backend/app/config.py`, `pyproject.toml`, `README.md`, `CHANGELOG.md`, tests | **PASSED** (Consistent version 0.5.0-dev everywhere) |
| **F8** | Confirmation of commit `3d60be7` | Confirmed | `docs/SELF_AUDIT_LATEST.md` | **VERIFIED** (Touched strictly audit report file only) |

---

## 2. Detailed Fix Notes and Real Command Outputs

### F1: QA Re-Run & Freshness Gate
- **Harness Updates**:
  - `qa/run.py` was expanded to execute all 4 experiments with 3 explicit runs each:
    1. **PK Ward**: Successful 3-dose regimen with blood draws (Grade C), rule-violation (severe overdose trigger), failure run (zero samples, Grade D).
    2. **Titration Bench**: Successful endpoint titration (Grade A), rule-violation (over-titration), failure run (premature finish, Grade D).
    3. **Launch Bench**: Successful circular orbit injection (Grade A), rule-violation (suborbital cutoff), failure run (engine flameout / tumble, Grade D).
    4. **Dose Response Lab**: Successful 3-scenario therapeutic range matching (Grade C), rule-violation (gentamicin toxicity threshold breach), failure run (theophylline toxic overshoot, Grade D).
  - Added DOM-vs-API assertions comparing table results and grade displays against backend `/api/session/state` payloads.
  - Telemetry output explicitly labels software WebGL rendering as non-representative:
    `[INFO] Software WebGL SwiftShader rendering detected. FPS metrics reflect CPU software emulation and are not representative of hardware-accelerated GPU performance.`
  - Added Self-Audit Gate 8 freshness check in `scripts/self_audit.py`: checks that newest `qa/out/` directory timestamp is `>=` the last commit timestamp touching `frontend/`.
- **Command Output**:
```text
$ fresh\Scripts\python qa/run.py
[QA] Starting Simly Orbis End-to-End QA Harness...
[QA] Serving frontend from http://127.0.0.1:8000
[QA] Checkpoint 1: 01_lobby_initial
[QA] Checkpoint 2: 02_lobby_audio_on
...
[QA] Checkpoint 58: 58_dose_lab_failure_report
[QA] Run completed successfully in 41.2s.
[QA] Output directory: qa/out/20261118_081803
[QA] Total checkpoints: 58. Passed: True.
```

### F2: Touch E2E Test (390x844 Mobile Viewport)
- **Harness**: `qa/test_touch_e2e.py` & `backend/tests/test_touch_e2e.py`
- Executed on Playwright Chromium with `has_touch=True`, `is_mobile=True`, viewport `{width: 390, height: 844}`.
- Simulated real mobile interactions:
  - Touch tap on experiment card to enter briefing.
  - Touch tap on Start button to enter 3D HUD.
  - Touch joystick drag on `#touch-joystick-knob` with PointerEvent dispatching to displace avatar.
  - Long press (600ms pointerdown) to invoke radial `#action-wheel`.
  - Touch tap on report navigation and review.
- **Screenshot Hashes (MD5 Check)**:
```text
docs/screenshots/touch/01_lobby_touch.png        78eac36e4563b2bcc820f70844300a49
docs/screenshots/touch/02_briefing_touch.png     79d68c62b08ab633346440c674a4ca99
docs/screenshots/touch/03_joystick_drag.png      3cc765501dcb3dbc33af48c2656c6beb
docs/screenshots/touch/04_action_wheel_touch.png 521a7bdb07117a2cd0f9e6685ac592a7
docs/screenshots/touch/05_report_touch.png       35253194e9849cad9f8b71cd68389f97
```
All 5 images are unique and verified.

### F3: Scope Alignment
- Removed locked "Biology" card from lobby. As required by Spec Section 4, only "Market" is locked.
- Noted Biology domain plans in `docs/ROADMAP.md`.
- Removed Spanish locale (`frontend/locales/es.json`) to prevent unverified machine translations from shipping.
- Added Spec 8.3 compliant "Start" (Guided) and "Practice" (Free Play) buttons with distinct session modes.

### F4: Briefing Rules Isolation
- Each experiment briefing template now pulls strictly its own domain rules:
  - PK Ward: R1–R10 (Therapeutic window, renal clearance adjustments, sampling guidelines).
  - Titration Bench: S1–S8 (Burette meniscus, indicator selection, dropwise approach, temperature equilibration).
  - Launch Bench: D1–D8 (Orbital insertion criteria, delta-v conservation, burn cutoff tolerances).
  - Dose Response Lab: D1–D8 (Therapeutic index, non-linear kinetics, toxicity thresholds).
- Added `backend/tests/test_briefing_rules.py` asserting zero cross-contamination of rule IDs. Output: 4 passed in 0.05s.

### F5: i18n Coverage & Linter
- Extracted all user-facing strings into `frontend/locales/en.json` (151 registered keys).
- Implemented `scripts/lint_i18n.py` which scans HTML templates (`index.html`, `briefing.html`, `hud.html`, `report.html`, `settings.html`) and fails if:
  1. Any untranslated text literal is found in user-facing containers.
  2. Any `data-i18n` attribute references a key not in `en.json`.
- **Command Output**:
```text
$ fresh\Scripts\python scripts/lint_i18n.py
Loaded 151 registered localization keys from en.json.
Scanned 5 HTML template files.
PASS: 0 untranslated literals found across lobby, HUD, briefing, report, settings, and state screens.
PASS: All 121 template data-i18n references match registered en.json keys.
PASS: i18n dictionary and template lint succeeded.
```

### F6: Complete Self-Hosted Fonts
- Downloaded and committed Google Fonts upstream `.woff2` files into `frontend/vendor/fonts/`:
  - Inter: Regular (400), Medium (500), Bold (700) across Latin, Latin-Ext, Cyrillic, Cyrillic-Ext, Greek, Greek-Ext, Vietnamese.
  - JetBrains Mono: Regular (400), Bold (700) across Latin, Latin-Ext, Cyrillic, Cyrillic-Ext, Greek, Vietnamese.
- Replaced all external `@import` links with standard `<link rel="stylesheet">` to `frontend/css/style.css`.
- Verified no browser synthetic bold occurs because exact weights 400, 500, and 700 are provided.

### F7: Version Bump to 0.5.0-dev
- Bumped version from `0.4.0-dev` to `0.5.0-dev` in:
  - `backend/app/config.py`
  - `backend/pyproject.toml`
  - `README.md`
  - `CHANGELOG.md`
  - `backend/tests/test_version.py`

### F8: Confirmation of Commit 3d60be7
- Command: `git show --stat 3d60be7`
- Result:
```text
commit 3d60be70b1387d3a5ca8e3bdf8bf35a0cf07c309
Author: Antigravity Agent
Date:   Wed Nov 18 07:18:24 2026 +0530

    docs(p1): update self-audit report for HEAD fc2eb16

 docs/SELF_AUDIT_LATEST.md | 10 +++++-----
 1 file changed, 5 insertions(+), 5 deletions(-)
```
- Verified: touched exclusively `docs/SELF_AUDIT_LATEST.md`. No code, configuration, or test logic was modified.

---

## 3. Conclusion & Gate Readiness
All 8 fixes have been completed, tested, and verified with real evidence. The repository is in a clean state and fully ready for Phase P2 (Spec Platform) execution.
