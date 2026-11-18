# Simly Orbis Stage Gate Self-Audit Report

**Status:** PASS  
**Platform Version:** 0.4.1-dev  
**Single Source of Truth:** Backend Simulators  
**Governance Standard:** Educational Simulation &bull; Not Medical Advice &bull; Not Clinical Evidence  

---

## Stage Gates Verification Summary

| Gate | Requirement | Status | Evidence / Metrics |
| :---: | :--- | :---: | :--- |
| 1 | Git Repository State | **PASS** | Clean/Expected: True, Ahead: 41, HEAD: fc2eb164 |
| 2 | App Version | **PASS** | Version `0.4.1-dev` declared in `backend/app/config.py` |
| 3 | Pytest Test Suite | **PASS** | [fresh venv] `==================== 465 passed, 16241 warnings in 24.26s =====================` |
| 4 | Validation Row Governance | **PASS** | Evaluated 32 rows across 5 files: 32 unverified (with blank retrieved_on), 0 verified. Violations: 0 |
| 5 | Frozen Tolerances Guard | **PASS** | 3/3 frozen tolerance files verified. |
| 6 | Engine Immutability (Rule R1/R7) | **PASS** | Protected files checked: 4 engines + R1-R10/S1-S8 rules. Violations: 0 |
| 7 | CI Workflow Configuration | **PASS** | `.github/workflows/ci.yml` invokes bare `pytest backend/tests`. |
| 8 | QA Playthrough Proof | **PASS** | Folder: `20261114_111033` | Media count: 55 | report.md: True | MD5 collisions: 0 | Districts: 4/4 verified |
| 9 | First-Run Parser Baselines & Held-Out Status | **PASS** | Recorded rates & held-out status: Dose Lab baseline: 24.2% (15/62); Space Stage baseline: 89.1%; founder set: not provided; agent-written seed set, not founder-written (n=4/exp too small to be meaningful) |
| 10 | Claims & Compliance Audit (Rule R4/R6) | **PASS** | Total occurrences: 9 (all explicitly hedged/disclaimed). Unhedged violations: 0 |
| 11 | Gitignore Coverage | **PASS** | Coverage confirmed: qa/out (True), __pycache__ (True) |

---

## Detailed Gate Findings

### Gate 1: Git Repository State

HEAD: `fc2eb164` | Clean: True (expected audit files: True) | Ahead: 41

**Last 15 Commits:**
```
fc2eb16 docs(p1): Phase P1 report and self-audit
d5dca9a test(p1): P1 extra gate multi-viewport screenshots, axe audit, and keyboard navigation
001c412 feat(p1): provenance popovers and reality check integration
3881cd4 feat(p1): experiment briefings, report screens, and print stylesheet
37e8e45 feat(p1): loading, empty, error, offline, and WebGL fallback states
0b67319 test(p1): accessibility baseline, axe-core check, and focus trapping
613e7c5 feat(p1): i18n localization scaffolding, dictionary, and lint script
0586da8 feat(p1): phone-playable touch layout and responsive bottom sheet
1de60c8 feat(p1): accessible HUD refactor, source chips, and actions panel
bb3a2ee feat(p1): keyboard onboarding tutorial and persistent settings
7d76b6b feat(p1): lobby district tiles, waking state, and market modal
01e77b0 feat(p1): app shell, client router, route views, and 404 page
03daf30 feat(p1): shared component library, showcase page, and DOM tests
b7b09c0 feat(p1): design tokens, typography, and contrast verification script
70a3c9e docs(p0): recheck table verifying P0 tasks and F1-F5 fixes
```

### Gate 3: Pytest Test Suite

Exit code: 0

Command: `E:\Simly Orbis\fresh\Scripts\pytest.exe backend/tests`

Final line: `==================== 465 passed, 16241 warnings in 24.26s =====================`

### Gate 4: Validation Row Governance

All rows strictly comply with Rule R2/R3.

### Gate 5: Frozen Tolerances Guard

- validation/tolerances.yaml: `5b5d857ed4862b51...` OK
- validation/space_tolerances.yaml: `fc4ba76cb3ee9d65...` OK
- validation/pkpd_tolerances.yaml: `443d18ab90e60b43...` OK

### Gate 6: Engine Immutability (Rule R1/R7)

- `backend/app/pharma/pk.py`: 0 diff vs `cb9b66f` (PASS)
- `backend/app/pharma/trial.py`: 0 diff vs `cb9b66f` (PASS)
- `backend/app/chem/titration.py`: 0 diff vs `cb9b66f` (PASS)
- `backend/app/space/orbit.py`: 0 diff vs `cb9b66f` (PASS)
- Rules R1-R10 and S1-S8: Unmodified (PASS)

### Gate 10: Claims & Compliance Audit (Rule R4/R6)

All mentions are strictly negative/disclaimer statements.

---

## Non-Negotiable Rules Audit

1. **R1 (Single Source of Truth):** Frontend and 3D scenes act solely as visual rendering clients. Simulation results, differential equations, and safety assessments are evaluated strictly by backend engines.
2. **R2 (AI Proposes, Engine Decides):** Dr. Orbis and Ask Orbis NLP proposals are strictly routed through engine state machines and validation boundaries.
3. **R3 (Validation Integrity):** `verified_by` remains strictly `"unverified"` for all pending rows. Tolerances are guarded by immutable SHA-256 hashes.
4. **R4 (Real Proof Only):** 100% of reported QA frames are verified non-empty, unique, and perceptually distinct (0 hash collisions, 0 near-duplicates).
5. **R5 (No Fabricated Provenance):** Literature citations are accompanied by unverified flags and blank `retrieved_on` timestamps pending primary source human sign-off.
6. **R6 (Adult-Only Boundaries):** Dose Response Lab enforces strict adult ranges (Age 18–90, Weight 40–150 kg, CrCl 15–150 mL/min). Pediatric inquiries are rejected.
7. **R7 (Engine Immutability):** Baseline engines (`pharma.pk`, `pharma.trial`, `chem.titration`, `space.orbit`) and safety rules R1–R10 / S1–S8 maintain 0 diff vs baseline commits.
