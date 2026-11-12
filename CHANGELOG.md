# Changelog

All notable changes to Simly Orbis ("Orbis Lab") will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Disclaimer:** Educational simulation platform. Not medical advice. Not clinical evidence.

---

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
