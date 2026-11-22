# Simly Orbis Stage Gate Self-Audit Report

**Status:** PASS  
**Platform Version:** 0.9.0-dev  
**Single Source of Truth:** Backend Simulators  
**Governance Standard:** Educational Simulation &bull; Not Medical Advice &bull; Not Clinical Evidence  

---

## Stage Gates Verification Summary

| Gate | Requirement | Status | Evidence / Metrics |
| :---: | :--- | :---: | :--- |
| 1 | Git Repository State | **PASS** | Clean/Expected: True, Ahead: 125, HEAD: bfb3fc04 |
| 2 | App Version | **PASS** | Version `0.9.0-dev` declared in `backend/app/config.py` |
| 3 | Pytest Test Suite (Clean-Clone) | **PASS** | [clean-clone venv] `=============== 815 passed, 4 skipped, 34478 warnings in 25.71s ===============` |
| 4 | Validation Row Governance | **PASS** | Evaluated 32 rows across 5 files: 32 unverified (with blank retrieved_on), 0 verified. Violations: 0 |
| 5 | Frozen Tolerances Guard | **PASS** | 4/4 frozen tolerance files verified. |
| 6 | Engine Immutability (Rule R1/R7) | **PASS** | Protected files checked: 8 engines + 26 rules. Violations: 0 files, 0 rule mismatches. |
| 7 | CI Workflow Configuration | **PASS** | `.github/workflows/ci.yml` invokes bare `pytest backend/tests`. |
| 8 | QA Playthrough Proof | **PASS** | Folder: `20261122_181225` (fresh (post-frontend commit)) | Media count: 74 | report.md: True | MD5 collisions: 0 | Districts: 4/4 verified |
| 9 | First-Run Parser Baselines & Held-Out Status | **PASS** | All 6 corpora first-run baseline rates verified in PHASE_5_REPORT.md; seed & founder status confirmed |
| 10 | Claims & Compliance Audit (Rule R4/R6) | **PASS** | Total occurrences: 19 (all explicitly hedged/disclaimed). Unhedged violations: 0 |
| 11 | Gitignore Coverage | **PASS** | Coverage confirmed: qa/out (True), __pycache__ (True) |

---

## Detailed Gate Findings

### Gate 1: Git Repository State

HEAD: `bfb3fc04` | Clean: False (expected audit files: True) | Ahead: 125

**Last 15 Commits:**
```
bfb3fc0 fix(frontend): support QA telemetry assertions and camera toggle in backward compatibility layer
bc8b245 docs: update SEE_THE_RESULT.md with 0.9.0-dev status and verification commands
cce7f17 feat(ux): simplify HUD with progressive disclosure and 5-element persistent layout (Problem A)
011b8cf fix(controls): camera-relative movement and stable follow camera rig (Problem B)
26b3ac2 docs(guide): add SEE_THE_RESULT.md verification and staging guide for founder
4737630 docs(audit): update SELF_AUDIT_LATEST.md with fresh playthrough proof
b3352fe fix(space): map space apparatuses and register 3D facility models in space scene
f6fc65e docs(audit): update SELF_AUDIT_LATEST.md with Phase 5 all-pass results
8ed92bf fix(engine): restore legacy engine.py byte-identical to commit 3d60be7
2c5fef8 docs(p5): author Phase 5 space completion report
4df28e5 test(qa): add space bench e2e playthroughs and verify space parser corpora (P5-T5)
f8baf23 feat(perf): implement tiered particle budgets and low-spec optimization for space bench (P5-T4)
c5df01a test(validation): recheck space reference rows and document radius sensitivity (P5-T3)
cc6b802 feat(space): add parameter sliders, delta-v budget bar, orbit controls, and why-it-failed panel (P5-T2)
4169d3b feat(space): implement five mission scenario specs with 3-step hint ladders and deterministic scoring (P5-T1)
```

### Gate 3: Pytest Test Suite (Clean-Clone)

Exit code: 0

Command: `pytest backend/tests`

Final line: `=============== 815 passed, 4 skipped, 34478 warnings in 25.71s ===============`

### Gate 4: Validation Row Governance

All rows strictly comply with Rule R2/R3.

### Gate 5: Frozen Tolerances Guard

- validation/tolerances.yaml: `5b5d857ed4862b51...` OK
- validation/space_tolerances.yaml: `fc4ba76cb3ee9d65...` OK
- validation/pkpd_tolerances.yaml: `443d18ab90e60b43...` OK
- validation/chem_tolerances.yaml: `2288d01d83e2a5fc...` OK

### Gate 6: Engine Immutability (Rule R1/R7)

- `backend/app/modules/pharma_pk.py`: 0 diff vs `cb9b66f` (PASS)
- `backend/app/modules/pharma_trial.py`: 0 diff vs `cb9b66f` (PASS)
- `backend/app/modules/chem_titration.py`: 0 diff vs `cb9b66f` (PASS)
- `backend/app/modules/space_orbit.py`: 0 diff vs `cb9b66f` (PASS)
- `backend/app/space/orbit.py`: 0 diff vs `cb9b66f` (PASS)
- `backend/app/pharma/pkpd/engine.py`: 0 diff vs `bd8ce6d` (PASS)
- `backend/app/chem/kinetics.py`: 0 diff vs `8c9609b` (PASS)
- `backend/app/chem/buffer.py`: 0 diff vs `6b6bc5e` (PASS)
- Rules R1-R10, S1-S8, and D1-D8: 26/26 matched snapshot SHA-256 (PASS)

### Gate 9: First-Run Parser Baselines & Held-Out Status

Latest Phase Report: PHASE_5_REPORT.md
Corpora Parser Rates (First-Run vs. Final):
  - pk        : first-run 22/22 (100.0%)     | final 22/22 (100.0%)     [present in PHASE_5_REPORT.md]
  - titration : first-run 20/20 (100.0%)     | final 20/20 (100.0%)     [present in PHASE_5_REPORT.md]
  - space     : first-run 49/55 (89.1%)      | final 55/55 (100.0%)     [present in PHASE_5_REPORT.md]
  - dose      : first-run 15/62 (24.2%)      | final 62/62 (100.0%)     [present in PHASE_5_REPORT.md]
  - kinetics  : first-run 9/55 (16.4%)       | final 54/55 (98.2%)      [present in PHASE_5_REPORT.md]
  - buffer    : first-run 10/55 (18.2%)      | final 54/55 (98.2%)      [present in PHASE_5_REPORT.md]
Held-Out Datasets Status:
  - agent-written seed set, not founder-written (n=4/exp too small to be meaningful) [10/16, 62.5%]
  - founder set: not provided

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
