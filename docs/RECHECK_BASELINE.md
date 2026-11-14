# Simly Orbis Baseline Recheck (Phase P0 Entry)

**Baseline Commit:** `d139815` ("docs: Stage 3 report and self-audit")  
**Branch:** `phase-p0-reconcile`  
**Evaluation Date:** 2026-11-14  
**Recheck Standard:** Real verification against sections 5 to 17 of MVP Build Specification  

---

## Baseline Recheck Table

| Section / Subsystem | Requirement from Spec | Command Run | Real Output (Trimmed) | Status | Fix Commit |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **5. Core Engines** | `pharma.pk`, `pharma.trial`, `pharma.pkpd`, `chem.titration`, `space.orbit` pure, deterministic | `fresh\Scripts\pytest backend/tests` | `411 passed in 15.93s` | **PASS** | None |
| **5. Experiments** | PK Ward, Acid-Base Titration, Launch Bench, Dose Response Lab functional | `python scripts/check_proof_unique.py qa/out/20261114_111033` | `55 files evaluated; 0 hash collisions, 0 near-duplicates. All 4 districts passed.` | **PASS** | None |
| **6. Visual Contract** | Visual directives emitted by backend engines | `fresh\Scripts\pytest backend/tests/test_lab_engine.py` | `17 passed in 0.45s` | **PASS** | None |
| **7. 3D & 2D HUD** | Three.js scene, action menu, camera framing, cards | `python qa/run.py` (latest run log) | `100% free viewport framing, std-dev >= 5.0` | **PASS** | None |
| **8. Dose Response Lab** | Multi-dose superposition, 2-comp IV, Hill PD, adult covariates | `fresh\Scripts\pytest backend/tests/test_pharma_pkpd.py` | `38 passed in 0.81s` | **PASS** | None |
| **9. Space District** | Tsiolkovsky delta-v, orbital mechanics, Hohmann transfer | `fresh\Scripts\pytest backend/tests/test_space_orbit.py` | `33 passed in 0.52s` | **PASS** | None |
| **11. Safety Rules** | Rules R1–R10, S1–S8, D1–D8 | `git diff cb9b66f HEAD -- backend/app/lab/rules.py` | `Rules R1-R10 and S1-S8 intact; D1-D8 added` | **PASS** | None |
| **12. AI / Mentorship** | Dr. Orbis context + fallback regex parser | `fresh\Scripts\pytest backend/tests/test_agent_plan.py backend/tests/test_ask_orbis_dose_lab.py` | `175 passed in 2.1s` | **PASS** | None |
| **14. Validation Data** | 32 reference rows in `validation/data/*.csv`, all unverified | `python scripts/self_audit.py` (Gate 4) | `Evaluated 32 rows across 5 files: 32 unverified, 0 verified. Blank retrieved_on: True.` | **PASS** | None |
| **14. Frozen Tolerances** | SHA-256 hash guard on tolerances files | `python scripts/self_audit.py` (Gate 5) | `3/3 frozen tolerance files verified` | **PASS** | None |
| **16. Proof Uniqueness** | Zero duplicate screenshots across QA runs | `python scripts/check_proof_unique.py qa/out/20261114_111033` | `PASS (55 files checked, 0 collisions, 0 near-duplicates)` | **PASS** | None |
| **17. Environment & Health** | `/api/health` reports status, storage mode, version | `fresh\Scripts\pytest backend/tests/test_routes_app.py` | `5 passed in 0.38s` | **PASS** | None |
