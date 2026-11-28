# Changelog

All notable changes to Simly Orbis ("Orbis Lab") will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Disclaimer:** Educational simulation platform. Not medical advice. Not clinical evidence.

---

## [0.9.1-dev] - 2026-11-28

### Added
- **UI Round 2 & 3 (U1–U7, V1–V5) & P5-HARDEN-ALL**:
  - Unified Current Task primary action button (`Go to <Station> and do this` walk-and-act, single primary button budget, 5-second post-walkthrough pulse) and `❓ What do I do?` plain-English step explanation popover.
  - Launch Bench collapsible telemetry/sliders drawer toggled via `🚀` in top-left (persisted in `localStorage`), PBR lighting (`buildLighting()`), `#space-scene-loading` indicator, and Pad View camera `(18.5, 11.0, 26.0)` with `maxDistance: 220.0` framing full rocket, pad apron, and character.
  - Shared `resolve_client_ip(request)` in `app.security` with `TRUST_PROXY` gating and last-hop extraction used by `SecurityAndRateLimitMiddleware` and `routes/specs.py`.
  - Read-only `?debug=1` / `F3` telemetry hook (`window.__debugTelemetry`) and `qa/run.py` movement/camera assertions.

### Fixed
- Computed true starting `Score: 100` (sum of `score_parts`) and normalized `Safety 100/100` (neutral/green when `violations` is empty; missing PPE shown as calm `📋 To-Do` chip).
- Suppressed floating proximity prompt when not matching the active step target (no `Use Label Pen` during Step 1 PPE).
- Stacked mobile `#hud-top-right` below `#hud-top-left` (`top: 52px`) at `<= 600px` so experiment titles never clip at `390x844`.
- Repositioned `#toast-container` below the HUD (`top: 66px`) and suppressed benchmark/auto-performance toasts in headless/software-render runs.
- Filtered third-party `DeprecationWarning` noise in `backend/pytest.ini` and synced `scripts/self_audit.py` governance labels to G-ids.

---

## [0.9.0-dev] - 2026-11-22

### Added
- **Problem A: Clean HUD & Progressive Disclosure Architecture**:
  - Reduced persistent HUD elements to at most 5 (`data-hud-persistent`): Top-Left (Title + Progress + Menu), Top-Right (Time, Score, Safety, Settings), Bottom-Center (Current Task Card), Bottom-Left (Ask Orbis chat bubble button), Bottom-Right (Dr. Orbis round button with unread dot).
  - Current Task card displays step title, one-line hint, missing PPE warning, 1-3 primary actions, and "Go to <Station>" button.
  - Slide-over Simulation Menu drawer organizing secondary controls (camera view, display & graphics, audio, controls help, demo cheats, full station list).
  - 4-step coach marks onboarding sequence on first run, skippable and persisted.
  - Responsive layout verified across 1920x1080, 1366x768, 1280x720, 768x1024, and 390x844 (bottom sheet on mobile).
  - Objective acceptance tests in Playwright test suite for non-overlapping HUD boxes and <30% HUD area at 1366x768.

### Fixed
- **Problem B: Locomotion & Camera Rig Stability**:
  - Resolved right-vector mirroring bug in `controller.js` and `camera_rig.js` with pure math module `movement_math.js` (`rightX = -fwdZ; rightZ = fwdX;`).
  - Gated camera yaw chase behind optional `autoAlignBehind` setting (persisted in localStorage, default OFF).
  - Enforced camera yaw changes only through explicit user input (mouse/touch drag, Q/E, Re-center).
  - Implemented critically damped exponential easing (`exp(-k*dt)`) for avatar following with constant distance, clamped pitch, and zero overshoot.
  - Verified avatar model local +Z facing matches travel velocity heading (<0.01° error).

---

## [0.8.0-dev] - 2026-11-20

### Added
- **Phase P4 Pharma Depth & Security Hardening**:
  - Virtual Trial v2 (`pharma.trial_v2`) multi-compartment population simulation with adult covariate distributions (age, weight, CrCl), log-normal clearance variance, and percentile curves.
  - Interactive Trial Sidecar UI (`trial_panel.js`) with 1,000-subject instanced crowd arena, percentile visualization, and CSV export.
  - Frozen 12-compound pharmacology library (`pharma_drugs.yaml`) with G5 parameter-level literature citations and blank `retrieved_on`.
  - Dose Response Lab interactive polish with debounced recalculation, multi-regimen overlay, and renal function adjustments.
  - Nelder-Mead parameter calibration harness (`calibrate.py`, `routes/calibrate.py`) with hold-out validation and strict honest labeling ("fit to your data, not validation").
  - Adversarial clinical red-team suite (26 cases) verifying 100% refusal rate for personal symptoms, pediatric dosing, and prescribing queries.
  - Pre-launch security audit mitigations: pinned updated dependencies (`fastapi==0.115.14`, `python-dotenv==1.2.4`, `Pillow==13.0.0`), rate-limit bypass protection against client Host headers, Gate 6 per-rule SHA-256 snapshots (`rule_snapshots.json`), and CI clean-clone test procedures.

## [0.7.0-dev] - 2026-11-19

### Added
- **Phase P3 Chemistry Expansion**:
  - Reaction Kinetics Engine (`chem.kinetics`) supporting 0th, 1st, 2nd order rate laws, consecutive reactions ($A \to B \to C$), Arrhenius temperature dependence, and RK4 numerical integration with seeded measurement noise.
  - Aqueous Buffer Equilibrium Engine (`chem.buffer`) supporting exact electroneutrality charge-balance, Henderson-Hasselbalch discrepancy analysis, differential Van Slyke buffer capacity $\beta(\text{pH})$, and acid/base stress titrations.
  - Interactive Reaction Kinetics Bench (`kinetics_bench`) and Buffer Solutions Bench (`buffer_bench`) with 3D scene apparatus and HUD parameter analysis panels.
  - Real QA test suites with success, rule-violation, and failure runs for all six laboratory experiments.
  - Chemistry validation tolerances file (`validation/chem_tolerances.yaml`) and frozen SHA-256 hash (`validation/chem_tolerances.sha256`).
  - Natural language phrase parsing corpora for chemistry benches with generic grammar rules achieving 98.2% pass rates.
  - Comprehensive model documentation (`docs/chem_models.md`), model cards (`docs/model_cards/chem_kinetics.md`, `docs/model_cards/chem_buffer.md`), and permanent recheck audit log (`docs/RECHECK_P3.md`).

## [0.6.0-dev] - 2026-11-19

### Added
- **Phase P2 Spec Platform**:
  - Declarative experiment specification format (`ExperimentSpec`) implementing Section 10 of MVP Build Specification.
  - Comprehensive Pydantic schema validation (`backend/app/specs/validator.py`) and CLI validator tool (`scripts/validate_specs.py`).
  - Migration of Titration Bench, PK Ward, Launch Bench, and Dose Response Lab to declarative specs (`specs/*.json`).
  - Strict golden-equivalence testing framework (`backend/tests/test_spec_equivalence_*.py`) running legacy and spec runtime on 22 scripted sequences per experiment (96 tests total, 100% pass).
  - Dual-mode `SPEC_RUNTIME` configuration flag with legacy fallback retention and QA harness support.
  - Dynamic spec-driven Ask Orbis vocabulary and Dr. Orbis mentor hints.
  - Spec authoring UI (`frontend/authoring.html`), documentation (`docs/EXPERIMENT_SPEC_GUIDE.md`), worked example fixture (`specs/fixtures/worked_example_neutralization.json`), size limits, rate limiting, and security hardening.

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
