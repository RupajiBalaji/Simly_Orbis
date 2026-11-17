# Simly Orbis MVP Gap Report (Phase P0 Baseline)

**Evaluated Version:** `0.4.0-dev` -> `0.4.1-dev` (P0 Target)  
**Evaluation Scope:** Sections 4 to 17 of *Simly Orbis MVP Build Specification and Agent Task Playbook (v1.0)* (20-section specification + 3 appendices)  
**Date:** 2026-11-14 (Updated 2026-11-17)  

---

## 1. Executive Summary & Specification Scope

The Simly Orbis MVP Build Specification comprises **20 sections** plus 3 appendices. As required by **Phase P0 Task P0-T1**, this GAP report systematically evaluates the repository baseline against the 14 core functional and architectural specification sections (**Sections 4 through 17**). 

Every capability marked **MUST** in Section 4 and detailed throughout Sections 5–17 has been audited. Identified gaps are explicitly mapped to their closing tasks in the phased playbook (P0 through P10).

---

## 2. Section-by-Section Audit (Sections 4 to 17)

| Spec Section | Title & Scope | Status | Audit Findings & Concrete Evidence | Closing Task |
| :--- | :--- | :---: | :--- | :---: |
| **Section 4** | **What MVP Means (The MUST List)** | **PARTIAL** | Core simulators, 3D client, guest play, and Ask Orbis operational. Missing teacher role, buffer/kinetics benches, and mobile joystick tuning. | P0 to P10 |
| **Section 5** | **Target Architecture & Technology Choices** | **DONE** | Python 3.12 FastAPI backend + Three.js vanilla JS client. MongoDB Atlas with clean in-memory fallback. Zero frontend build step. | Baseline |
| **Section 6** | **Visual Identity, Mood and World** | **PARTIAL** | Three.js laboratory world active with warm lighting, district signage, and tactile instruments. Needs character polish and post-processing tuning. | P1-T1, P5-T1 |
| **Section 7** | **Character, Controls, Camera & Interaction** | **PARTIAL** | Third-person and free orbit cameras present (`verify_camera_rig.py`). Keyboard/mouse navigation functional. IK hand solvers and mobile dual joysticks pending. | P1-T6, P1-T7, P5-T1 |
| **Section 8** | **Gameplay Loop, Scoring & Session Reports** | **PARTIAL** | 4-step game loop (Plan, Run, Review, Reality Check) with 0-100 scoring. On-screen reports exist. Dedicated print stylesheet and PDF export pending. | P1-T11 |
| **Section 9.1** | **Pharma District (PK Ward, Dose Lab, Trial Hall)** | **PARTIAL** | Dose Response Lab complete (1-/2-comp, Hill Emax, adult covariates, D1-D8 rules). PK Ward implements 5 core steps (needs 13-step expansion). Trial Hall basic simulation exists (needs cohort visualizer). | P3-T1, P3-T2 |
| **Section 9.2** | **Chemistry District (Titration, Kinetics, Buffer)** | **PARTIAL** | Titration Bench complete (Henderson-Hasselbalch, indicator color shift, burette flow). Kinetics Bench and Buffer Bench not yet created. | P4-T1, P4-T2 |
| **Section 9.3** | **Space District (Launch & Orbit Bench)** | **DONE** | Launch & Orbit Bench complete: Tsiolkovsky $\Delta v$, vis-viva, Hohmann transfer, 4-phase launch workflow, flight debrief telemetry, rules S1-S8. | Closed in Stage 2 |
| **Section 10** | **Spec-Driven Experiment Platform** | **PARTIAL** | Experiments currently hardcoded in Python engine (`app/lab/engine.py`). Declarative YAML/JSON experiment definition loader and CLI validator pending. | P2-T1, P2-T2 |
| **Section 11** | **Backend Architecture & APIs** | **DONE** | FastAPI async endpoints, lifespan startup validation, token-bucket IP rate limiting (120/min general, 10/min AI), payload cap (20 KB), CORS, `/api/health`. | P0-T6 |
| **Section 12** | **Dr. Orbis and Ask Orbis** | **PARTIAL** | Deterministic rule-based fallback parser + Gemini flash-lite integration with daily cap (`MENTOR_DAILY_CAP`) and kill switch (`AI_ENABLED`). Agent seed held-out set evaluated; founder set pending. Grammar expansion for complex clauses pending. | P0-T4, P7-T1..T4 |
| **Section 13** | **Accounts, Classrooms and Privacy** | **PARTIAL** | Guest play (nickname-only, no emails, localStorage) complete. Teacher accounts, classroom join codes, student assignment tracking, and privacy terms page pending. | P6-T1, P6-T2, P8-T3 |
| **Section 14** | **Reality Check and the Model Cards** | **PARTIAL** | Reality Check UI panel present. 5 standardized Model Cards authored in `docs/model_cards/` and mounted statically. Expert verification worksheet/log workflow pending. | P0-T5, P1-T12, P8-T1 |
| **Section 15** | **Validation Datasets & Tolerance System** | **DONE** | 32 reference rows across 5 CSVs strictly governed (`verified_by = "unverified"`, blank `retrieved_on`). Frozen tolerance YAML files guarded by immutable SHA-256 tests. | Baseline, P0-T3 |
| **Section 16** | **Automated QA, Visual Proof & Playwright Harness** | **DONE** | Automated Playwright QA runner (`qa/run.py`), MD5 hash collision and perceptual duplicate detector, 55 media artifacts verifying 4/4 districts. | Baseline, P0-T2 |
| **Section 17** | **Deployment, Environments & Operations** | **PARTIAL** | Turnkey Render Blueprint (`render.yaml`), Docker containerization, in-memory fallback. Shallow clone CI resilience added. Automated staging environment and backup scripts pending. | P0-T2, P10-T1 |

---

## 3. Comprehensive MUST Requirements Gap Table (from Section 4)

| Spec Ref | MVP Capability (MUST) | Current Repository Status | Concrete Evidence / Current State | Closing Task |
| :--- | :--- | :---: | :--- | :---: |
| **4 / 9.1** | **Pharma: PK Ward (13 steps)** | **PARTIAL** | Currently implements 5 core steps (weigh, dissolve, administer, blood sample, assay) in `backend/app/lab/engine.py`. | **P3-T1** |
| **4 / 9.1** | **Pharma: Dose Response Lab** | **DONE** | Complete: 1- & 2-comp models, oral & IV infusion, superposition, Hill Emax, adult covariates, D1–D8 rules, dual SVG curves. | Closed in Stage 3 |
| **4 / 9.1** | **Pharma: Virtual Trial Hall** | **PARTIAL** | Basic trial simulation exists in `backend/app/pharma/trial.py`. Lacks UI cohort visualizer and full trial hall experiment flow. | **P3-T2** |
| **4 / 9.2** | **Chemistry: Titration Bench** | **DONE** | Implements 5 steps (rinse, pipette, indicator, titrate, endpoint) with Henderson-Hasselbalch math and color changes. | Closed in Week 1 |
| **4 / 9.2** | **Chemistry: Kinetics Bench** | **MISSING** | Temperature/catalyst reaction kinetics engine not yet created. | **P4-T1** |
| **4 / 9.2** | **Chemistry: Buffer Bench** | **MISSING** | Multi-component buffer capacity and titration resistance engine not yet created. | **P4-T2** |
| **4 / 9.3** | **Space: Launch & Orbit Bench** | **DONE** | Tsiolkovsky delta-v, orbital velocity, Hohmann transfer, 4-step launch/transfer flow, rules S1–S8. | Closed in Stage 2 |
| **4 / 10** | **Spec-Driven Experiment Platform** | **PARTIAL** | Hardcoded experiments in `backend/app/lab/engine.py`. JSON/YAML spec loader, schema validator, and CLI not yet unified. | **P2-T1**, **P2-T2** |
| **4 / 7.4** | **Character: IK Hands & Cameras** | **PARTIAL** | Follow and free camera rigs exist (`verify_camera_rig.py`). Radial action menu exists. Full two-bone IK solver for hands in progress. | **P1-T6**, **P5-T1** |
| **4 / 12** | **Dr. Orbis & Ask Orbis Fallback** | **DONE** | Deterministic fallback parser + AI integration with daily cap and kill switch (`AI_ENABLED`). Tested across 175+ corpus phrases. | Closed in Stage 2/3 |
| **4 / 13.1** | **Teacher Accounts & Classrooms** | **MISSING** | Basic guest auth exists in `backend/app/routes/auth.py`. Teacher role, class codes, assignments, and CSV exports not yet implemented. | **P6-T1**, **P6-T2** |
| **4 / 13.2** | **Guest Play (Nickname, No Email)** | **DONE** | Guest sessions supported via local storage and `/api/auth/guest` without collecting student emails or PII. | Closed in Week 1 |
| **4 / 14** | **Reality Check & Model Cards** | **DONE** | Reality Check UI exists. 5 standardized Model Cards authored under `docs/model_cards/`, mounted at `/docs/model_cards/`, path traversal tests passing. | Closed in P0-T5 |
| **4 / 14.3** | **Expert Verification Workflow** | **PARTIAL** | `scripts/make_verification_worksheet.py` exists; need `scripts/apply_verification.py` and `validation/verification_log.csv`. | **P8-T1** |
| **4 / 8.8** | **Session Report (Screen & Print PDF)** | **PARTIAL** | On-screen HTML reports exist for all 4 experiments. Dedicated print stylesheet and PDF export need standardization. | **P1-T11** |
| **4 / 7.6** | **English UI with i18n Scaffolding** | **MISSING** | UI strings are hardcoded in English. Translation helper `t()` and `locales/en.json` dictionary needed. | **P1-T8** |
| **4 / 7.5** | **WCAG 2.1 AA & Keyboard Accessibility** | **PARTIAL** | Action menu supports keyboard. Comprehensive focus trapping, ARIA live regions, and automated Axe audit missing. | **P1-T9** |
| **4 / 7.6** | **Phone-Playable Touch Layout** | **PARTIAL** | Responsive CSS exists; touch joysticks and compact 390x844 viewport controls need optimization. | **P1-T7** |
| **4 / 13.3** | **Privacy, Terms & Cookie-Free** | **PARTIAL** | Disclaimers present on reports. Formal terms, privacy note, and first-party event tracker need standalone routes. | **P8-T3** |
| **4 / 17** | **Pilot Hosting & Monitoring** | **PARTIAL** | Hosted on Render Free tier (`render.yaml`). Staging environment, backup scripts, and automated uptime probes needed. | **P10-T1** |

---

## 4. Summary of Closed vs Pending Items in Phase P0

1. **P0-T1:** Baseline rechecked against Sections 4 to 17; GAP report updated.
2. **P0-T2:** Branch strategy documented; CI hygiene workflow configured with bare pytest, pip-audit, claims grep gate, and shallow clone resilience.
3. **P0-T3:** All 32 validation rows audited: 0 derived from engines, 0 invented dates, all unverified with blank `retrieved_on`.
4. **P0-T4:** Agent seed held-out harness and SHA-256 guard implemented; founder-written held-out set accurately reported as 'not provided' until supplied.
5. **P0-T5:** Standardized Model Cards for all 5 engines authored under `docs/model_cards/`, mounted with security/traversal guards.
6. **P0-T6:** Startup environment variable validation and `/api/health` configuration reporting (`ai_status`).
7. **P0-T7:** `docs/PITCH_FACTS.md` statistics register created and claims grep gate enforced.
