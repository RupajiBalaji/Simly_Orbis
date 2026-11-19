# Simly Orbis — Phase P1 Report: Core Loop & Visual Polish

**Platform Version:** `0.4.1-dev`  
**Phase:** P1 (Core Loop & Visual Polish)  
**Governance Standard:** Educational Simulation &bull; Not Medical Advice &bull; Not Clinical Evidence &bull; Not Mission-Planning Software  
**HEAD Commit:** `d5dca9a`  

---

## 1. Blockers

*None.* All 12 Phase P1 tasks and the P1 Extra Gate completed successfully in one uninterrupted run. All 11 stage gates pass.

---

## 2. Task Execution Table

| Task ID | Description | Status | Commit | ACCEPT Evidence |
| :--- | :--- | :---: | :---: | :--- |
| **P1-T1** | Tokens & Typography (Spec 7.1, 7.2) | **DONE** | `b7b09c0` | `frontend/styles/tokens.css` authored with color palette, semantic roles, font stacks, spacing, radii, elevation, focus ring (`3px solid var(--accent)`). `scripts/check_contrast.py` verifies WCAG 2.1 AA 4.5:1 text and 3:1 UI contrast. Verified via `backend/tests/test_tokens_contrast.py`. |
| **P1-T2** | Component Library (Spec 7.3) | **DONE** | `03daf30` | 17 reusable UI components authored in `frontend/ui/components.css` and `components.js`. Component showcase at `frontend/ui/index.html`. Self-hosted Inter and JetBrains Mono fonts with `OFL.txt` license verified in `frontend/vendor/fonts/`. Verified via `backend/tests/test_ui_components.py`. |
| **P1-T3** | App Shell & Router (Spec 8.12) | **DONE** | `01e77b0` | Hash-based client router (`frontend/router.js`) managing `#lobby`, `#briefing`, `#lab`, `#report`, `#leaderboard`, `#settings`, `#model-cards`, `#reality-check`, and `#404`. Top bar breadcrumbs, offline-ready fallback, and 404 screen. Verified via `backend/tests/test_router.py`. |
| **P1-T4** | Lobby Experience (Spec 8.1) | **DONE** | `7d76b6b` | District cards (Pharma, Chem, Space, Biology [Locked], Market [Locked]). Mode toggle (Guided vs Free Play). `#modal-why-locked` educational progression dialog. `#screen-wakeup` cold start visual feedback. Verified via `backend/tests/test_lobby.py`. |
| **P1-T5** | Onboarding & Settings (Spec 8.2, 8.13) | **DONE** | `bb3a2ee` | 90-second keyboard-trapped onboarding walkthrough modal (`#modal-onboarding`). Settings screen with quality tier selector, audio volume, mute toggle, WCAG font scaling (100%–140%), high-contrast toggle, colorblind filters, and localStorage persistence. Verified via `backend/tests/test_settings_and_onboarding.py`. |
| **P1-T6** | HUD Refactor (Spec 8.4, 8.5) | **DONE** | `1de60c8` | Docked layout with collapsible left Checklist panel, right Telemetry readouts with `[Engine]`, `[Game]`, `[Lit]`, `[AI]` source chips, active rules panel (`#hud-rules-panel`), live event log (`aria-live="polite"`), and station-based action drawer. Verified via `backend/tests/test_hud_refactor.py`. |
| **P1-T7** | Responsive Phone Layout (Spec 7.6, 8.17) | **DONE** | `0586da8` | Mobile CSS media queries for `< 768px` and `390x844` viewport. Touch targets $\ge 44 \times 44\text{px}$. Bottom sheet drag handle (`#bottom-sheet-drag-handle`) and virtual touch joystick zone (`#touch-joystick-zone`). Safe area insets. Verified via `backend/tests/test_phone_layout.py`. |
| **P1-T8** | i18n Localization Scaffolding (Spec 7.8) | **DONE** | `613e7c5` | English (`frontend/locales/en.json`) and Spanish (`frontend/locales/es.json`) dictionaries with 35+ core keys. Lightweight runtime `frontend/i18n.js` with `t(key, params)` and `setLocale()`. Static dictionary consistency linter `scripts/lint_i18n.py` passing 100%. Verified via `backend/tests/test_i18n.py`. |
| **P1-T9** | Accessibility Baseline (Spec 7.5) | **DONE** | `0b67319` | Focus-visible 3px outline on all interactive elements. Universal `@media (prefers-reduced-motion: reduce)` animation speed override (`0.01ms`). Accessible focus trapping and Escape handlers on all modals (`Onboarding`, `Why Locked`, `About`). Verified via `backend/tests/test_accessibility.py`. |
| **P1-T10** | Application States (Spec 8.17) | **DONE** | `37e8e45` | Global loading spinner (`#global-loading-spinner`). Empty state illustration on leaderboard (`#leaderboard-empty-state`). User-friendly session error overlay (`#session-error-overlay` with What Happened / What You Can Do). Offline banner (`#offline-state-banner`). WebGL failure fallback (`#webgl-fallback`). Verified via `backend/tests/test_states.py`. |
| **P1-T11** | Briefing & Report Screens (Spec 8.3, 8.11, 8.14) | **DONE** | `3881cd4` | Briefing screen (`#screen-brief`) dynamically populated with apparatus equipment pills, mandatory safety rules (R1–R4), scoring rubric preview, and Practice Mode toggle. Report screen with print/PDF stylesheet (`@media print`), return-to-lobby, retry buttons, and exact zero-violations string. Verified via `backend/tests/test_briefing_and_report.py`. |
| **P1-T12** | Provenance Popovers & Reality Check (Spec 8.10, 8.15, 14.1) | **DONE** | `001c412` | Interactive click/hover popovers on `[Engine]`, `[Game]`, `[Lit]`, and `[AI]` source chips displaying mathematical formulas, model card links, and verification status. Reality Check table connecting all 5 simulator engines to `/docs/model_cards/<id>.md`. Strictly verified: all benchmark rows show `"N/A: unverified"`. Verified via `backend/tests/test_provenance_popovers.py`. |
| **Extra Gate** | P1 Extra Gate (Axe, Viewports, Keyboard Nav) | **DONE** | `d5dca9a` | Automated Playwright runner (`scripts/run_p1_extra_gate.py`). Axe accessibility audit across all 2D screens: 0 critical, 0 serious issues. 19 multi-viewport screenshots captured at 1366x768, 768x1024, and 390x844. Keyboard-only navigation verified from Lobby to Report. Verified via `backend/tests/test_p1_extra_gate.py`. |

---

## 3. Fresh-venv Bare Pytest Final Line

Command: `E:\Simly Orbis\fresh\Scripts\pytest.exe backend/tests`  
```
==================== 465 passed, 16241 warnings in 18.56s =====================
```

*(Zero failures, 465 passed tests across all suites).*

---

## 4. QA Table and Proof Summary

Primary Playthrough Proof Run: `qa/out/20261114_111033`  
- **Total media artifacts:** 55 files (PNG screenshots, WebM video captures)
- **MD5 Hash Collisions:** 0
- **Near-Duplicate Frame Ratio:** 0.0%
- **Districts Verified:** 4 / 4 (`pk_ward`, `titration_bench`, `launch_bench`, `dose_lab`)
- **Report Present:** `qa/out/20261114_111033/report.md` (Verified complete)

### Phase P1 Extra Gate Media Proof (`docs/screenshots/p1/`):
- **Desktop (1366x768):** `lobby_1366x768.png`, `briefing_1366x768.png`, `settings_1366x768.png`, `reality_check_1366x768.png`, `model_cards_1366x768.png`, `report_1366x768.png`, `keyboard_nav_report_1366x768.png`
- **Tablet (768x1024):** `lobby_768x1024.png`, `briefing_768x1024.png`, `settings_768x1024.png`, `reality_check_768x1024.png`, `model_cards_768x1024.png`, `report_768x1024.png`
- **Mobile (390x844):** `lobby_390x844.png`, `briefing_390x844.png`, `settings_390x844.png`, `reality_check_390x844.png`, `model_cards_390x844.png`, `report_390x844.png`
- **Total Screenshots:** 19 unique PNG artifacts.

---

## 5. P1 Extra Gate Verification Results

1. **Automated Axe WCAG Audit on 2D Screens:**
   - Evaluated Screens: Lobby, Briefing, Settings, Reality Check, Model Cards, Report.
   - Evaluated Viewports: Desktop (1366x768), Tablet (768x1024), Mobile Phone (390x844).
   - **Critical Violations:** **0**
   - **Serious Violations:** **0**
   - **Status:** **PASS** ✅

2. **Multi-Viewport Responsive Rendering:**
   - Desktop (1366x768), Tablet (768x1024), and Mobile (390x844) confirmed free of horizontal scrolling or layout clipping.
   - Touch targets $\ge 44 \times 44\text{px}$ verified on mobile.
   - Bottom sheet drag handle and virtual joystick active.

3. **Keyboard-Only Lobby-to-Report Navigation:**
   - Sequence: `#/lobby` $\rightarrow$ `Tab` card focus $\rightarrow$ `Enter` $\rightarrow$ `#/briefing?exp=pk_ward` $\rightarrow$ `Tab` to `#btn-start-experiment` $\rightarrow$ `Enter` $\rightarrow$ `#/lab?exp=pk_ward` $\rightarrow$ `#/report` $\rightarrow$ `Tab` focus verified on `#btn-report-lobby` and `#btn-report-print`.
   - **Status:** **PASS** ✅

4. **Self-Hosted Typography and Fonts:**
   - Pinned font files confirmed on disk: `frontend/vendor/fonts/inter-normal-400.woff2` (48 KB) and `frontend/vendor/fonts/jetbrains-mono-normal-400.woff2` (31 KB).
   - License file confirmed: `frontend/vendor/fonts/OFL.txt` (SIL Open Font License 1.1).
   - Stylesheet loading: Confirmed strictly via `<link rel="stylesheet" href="./vendor/fonts/fonts.css" />` in HTML header; **zero `@import` rules in any CSS file**.

---

## 6. First-Run Parser Baselines & Held-Out Status

- **Recorded First-Run Rates (Untuned):**
  - Dose Lab baseline: **24.2%** (15 / 62)
  - Space Stage baseline: **89.1%** (49 / 55)
- **Founder Held-Out Set (`founder_heldout_phrases.json`):**
  - **Status:** `founder set: not provided` (agent never creates or edits founder file)
- **Agent Seed Held-Out Corpus Evaluation (`scripts/eval_heldout.py`):**
  - **Label:** `agent-written seed set, not founder-written`
  - **Note:** n=4 per experiment is too small to be meaningful.
  - **SHA-256 Guard:** `a67d6d83276f9a4f6655e51363282d9b020ef4df06bc3ddf3b673b1bb25699a1` (PASS)
  - `dose_lab`: 75.0% (3 / 4)
  - `launch_bench`: 25.0% (1 / 4)
  - `pk_ward`: 50.0% (2 / 4)
  - `titration_bench`: 100.0% (4 / 4)
  - **OVERALL SEED HELD-OUT PASS RATE:** **62.5%** (10 / 16)

---

## 7. Claims Gate Output

Command: `python scripts/check_claims.py`  
```
=== Simly Orbis Claims Grep Gate ===
[PASS] All promotional, clinical, and regulatory claims are strictly hedged and disclaimed.
```

---

## 8. Protected-File Diff Output

Protected engine files diff against base commit (`cb9b66f`):
```
git diff cb9b66f HEAD -- backend/app/pharma/pk.py backend/app/pharma/trial.py backend/app/chem/titration.py backend/app/space/orbit.py
```
*(Empty output: 0 diff across all 4 protected engine files).*

Safety Rules R1–R10 and S1–S8 diff against base commit (`cb9b66f`):
*(Empty deletion diff: rules R1–R10 and S1–S8 strictly unmodified).*

---

## 9. Open Issues

Referencing `docs/KNOWN_ISSUES.md`:
1. `ISS-001` (Severity: High, Status: Pending Founder Review): 32 validation rows remain `"unverified"` pending expert sign-off.
2. `ISS-002` (Severity: Low, Status: Documented): Software-WebGL rendering performance on headless / non-GPU environments (labelled "software render, not representative").
3. `ISS-003` (Severity: Med, Status: In Progress): Dose Lab natural language parser first-run baseline is 24.2% on unconstrained vocabulary.
4. `ISS-004` (Severity: Low, Status: In Progress): Launch Bench orbit transfer parsing needs formal grammar expansion for multi-burn parameters.
