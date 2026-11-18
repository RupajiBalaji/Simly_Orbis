# Changelog

All notable changes to Simly Orbis ("Orbis Lab") will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Disclaimer:** Educational simulation platform. Not medical advice. Not clinical evidence.

---

## [0.5.0-dev] - 2026-11-18

### Added
- **Phase P1 Core UI Platform & Extra Gate**:
  - CSS design tokens (`tokens.css`), high-contrast dark theme (7:1+), accessible typography with discrete self-hosted font weights (Inter 400/500/700, JetBrains Mono 400/700; no synthetic bold).
  - Accessible component library: action wheel, HUD panels, live-region audit log, toasts, and provenance popovers.
  - Spec 8.3 Briefing and Report screens with print stylesheet (`@media print`), Start vs Practice modes, and experiment-specific safety rules (R1-R10, S1-S8, D1-D8).
  - Multi-viewport accessibility baseline with 0 critical / 0 serious Axe violations across 1366x768, 768x1024, and 390x844 viewports.
  - Comprehensive i18n scaffolding with `lint_i18n.py` enforcement guaranteeing zero untranslated UI literals across lobby, HUD, briefing, report, settings, and state screens.

## [0.4.0-dev] - 2026-11-14

### Added
- **Stage 3 "Pharma Depth": Deep PK/PD Engine (`pharma.pkpd`)**:
  - Deterministic 1-compartment oral absorption (Bateman), 1-compartment IV infusion/bolus, and 2-compartment open mammillary models with analytical solutions and Runge-Kutta 4th-order (RK4) numerical ODE solvers.
  - Multi-dose linear superposition across arbitrary intervals with analytical accumulation ratio ($R_{accum} = 1/(1 - e^{-k_{el}\tau})$).
  - Sigmoidal Hill $E_{\max}$ pharmacodynamic model ($E(C) = E_0 + \frac{E_{\max} \cdot C^\gamma}{EC_{50}^\gamma + C^\gamma}$).
  - Adult covariate scaling: body weight allometric powers ($V \propto (WT/70)^{1.0}$, $CL \propto (WT/70)^{0.75}$) and Cockcroft-Gault renal clearance adjustment ($f_e$ fraction excreted unchanged).
  - Adult-only guardrails (Age 18–90, Weight 40–150 kg, CrCl 15–150 mL/min). Pediatric requests strictly rejected.
  - Calibrated Drug Library v2: Theophylline, Vancomycin, and Gentamicin with frozen reference SHA-256 hashes (`validation/pkpd_tolerances.yaml`).
  - Analytical engine tests with 400+ green tests in full test suite.
- **Dose Response Lab District (`dose_lab`)**:
  - Fourth interactive district in world lobby featuring patient selection, drug library, route options, infusion pump parameters, and sampling slates.
  - Real-time concentration-time and pharmacodynamic response curves, target window shading, and live DOM metric badges (Cmax, Tmax, AUC).
  - Regimen comparison overlay: pins a baseline schedule and plots comparative response curves.
  - 8 Dose Lab safety rules (D1-D8): patient selection, route compatibility, pump priming, sampling interval, and toxic overdose alarms.
  - Ask Orbis & Dr. Orbis Dose Lab integration: 62-phrase corpus with regression suite, deterministic medical advice refusals, and paediatric disclaimers.
  - Automated QA harness integration: 4 distinct scenarios (Theophylline oral titration, Vancomycin 2-comp IV, Gentamicin renal impairment, and Overdose alarm) with 51 verified unique proof screenshots.

## [0.3.0-dev] - 2026-11-12

### Added
- **Space District: Launch & Orbit Bench (`launch_bench`)**:
  - Deterministic orbital mechanics engine (`backend/app/space/orbit.py`) implementing multi-stage Tsiolkovsky $\Delta v$, vis-viva equation, circular velocity, Keplerian orbital period, and Hohmann transfer maneuvers.
  - 4th-order Runge-Kutta (RK4) numerical state propagator with specific mechanical energy and angular momentum conservation verified to within $10^{-6}$ relative error.
  - Three rocket presets: Orbis-1 (two-stage orbital), Orbis-Heavy (three-stage GEO capable), and Sounding Rocket (suborbital).
  - 8 space safety rules (S1-S8): preflight checklist, range safety clearance, liftoff TWR > 1.0, propellant loading bounds, and apogee burns.
  - Visual directives and procedural Three.js SpaceScene: Launch Pad 39A, launch umbilical tower, hold-down clamps, multi-stage rocket, particle flame and smoke plumes, 3D Earth globe, glowing Keplerian orbit LineLoop, smooth Pad View <-> Orbit View transitions, and flight failure mode animations.
  - Ask Orbis Space capability: phrase parsing for 10 space actions with 55 phrase benchmark (100% pass rate).
  - Dr. Orbis Space Mentor: launch readiness dry-run preflight checks, TWR and $\Delta v$ mechanics explanations, and flight debriefings.
  - 5 space validation rows in `validation/data/space_orbit_references.csv` and frozen tolerance guard in `validation/space_tolerances.yaml`.
  - Space playthrough scenario added to QA test harness (`qa/run.py`), generating 48 verified unique proof assets.

## [0.2.0] - 2026-10-14

### Added
- **Ask Orbis Lab Agent**:
  - Natural language laboratory assistant powered by Google Gemini with offline rule-based fallback parser.
  - Multi-step clause splitting ("then", "and", commas, semicolons) preserving experiment station context.
  - Safety validation engine intercepting toxic, lethal, or impossible operations with educational corrective guidance.
  - Comprehensive phrase corpus test suite covering 42 realistic lab phrases across both experiment rooms.
- **Automated Validation Runner**:
  - Rigorous engine-vs-literature benchmarking framework (`backend/app/validation/runner.py`).
  - Reference data in `validation/data/*.csv` covering 22 benchmark rows across clinical pharmacokinetics and equilibrium chemistry.
  - Clear separation of automated validation vs. human verification (showing "N/A: awaiting human verification" when verified count is 0).
  - Verification worksheet generator (`scripts/make_verification_worksheet.py`) producing CSV and Markdown worksheets with verification guidelines.
  - Frozen-tolerance test guard preventing unauthorized loosening of scientific acceptance criteria.
- **Reality Check Board**:
  - In-game transparency interface displaying predicted vs. literature values and fold errors.
  - Strict parameter provenance: every threshold explicitly identified as either literature-sourced or `game-balanced`.
- **Director Mode & Scripted Walkthroughs**:
  - Deterministic automated demonstration pipeline for Pharmacokinetics Ward and Titration Bench.
  - Mistake demonstration mode showcasing clinical dosing errors and acid-base indicator misjudgments.
- **Procedural 3D Visual Engine**:
  - 100% procedural Three.js r160 visual assets (custom Kerbal-inspired avatars, dynamic beaker fluids, volumetric shadows, radial interaction wheel).
  - Tri-tier performance architecture (Low, Medium, High) with automatic GPU capability detection and manual override.
  - Camera rig with Follow, Orbit, and Free modes, including close-up head tracking and occlusion avoidance.
- **Automated QA Playwright Harness**:
  - End-to-end automated testing (`qa/run.py`) running headless Chromium against dynamically allocated ports.
  - Strict gating: zero console errors, zero 4xx/5xx responses, no blank frames, viewport framing acceptance (&ge; 98%), and FPS telemetry.
  - Proof uniqueness checker (`scripts/check_proof_unique.py`) verifying binary uniqueness (SHA-256 / MD5) and perceptual distinctness (MAE &ge; 0.1%).
- **Operational & Credibility Tooling**:
  - Live site smoke testing script (`scripts/smoke_live.py`) with cold-start detection, version verification, and security header checks.
  - Comprehensive Known Issues register (`docs/KNOWN_ISSUES.md`).
  - Repository-wide claims audit (`docs/CLAIMS_AUDIT.md`) eliminating unhedged or unverified marketing language.

### Changed
- Refactored titration engine documentation and UI descriptions to accurately state the charge-balance equilibrium solver rather than pure Henderson-Hasselbalch approximations.
- Separated production dependencies (`backend/requirements.txt`) from developer/test dependencies (`backend/requirements-dev.txt`) for streamlined Docker builds.
- Upgraded app version identifier to `0.2.0`.

---

## [0.1.0] - 2026-10-10

### Added
- Initial proof-of-concept release.
- Two-compartment PK oral and IV simulation model.
- Dynamic charge-balance acid-base titration engine.
- Basic Three.js interactive laboratory view.
- FastAPI backend with MongoDB / in-memory storage fallback.
