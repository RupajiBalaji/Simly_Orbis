# Simly Orbis Stage Gate Self-Audit Report

**Status:** PASS  
**Platform Version:** 0.5.0-dev  
**Single Source of Truth:** Backend Simulators  
**Governance Standard:** Educational Simulation &bull; Not Medical Advice &bull; Not Clinical Evidence  

---

## Stage Gates Verification Summary

| Gate | Requirement | Status | Evidence / Metrics |
| :---: | :--- | :---: | :--- |
| 1 | Git Repository State | **PASS** | Clean/Expected: True, Ahead: 57, HEAD: baeb307a |
| 2 | App Version | **PASS** | Version `0.5.0-dev` declared in `backend/app/config.py` |
| 3 | Pytest Test Suite | **PASS** | [fresh venv] `=============== 582 passed, 19162 warnings in 92.59s (0:01:32) ================` |
| 4 | Validation Row Governance | **PASS** | Evaluated 32 rows across 5 files: 32 unverified (with blank retrieved_on), 0 verified. Violations: 0 |
| 5 | Frozen Tolerances Guard | **PASS** | 3/3 frozen tolerance files verified. |
| 6 | Engine Immutability (Rule R1/R7) | **PASS** | Protected files checked: 4 engines + R1-R10/S1-S8 rules. Violations: 0 |
| 7 | CI Workflow Configuration | **PASS** | `.github/workflows/ci.yml` invokes bare `pytest backend/tests`. |
| 8 | QA Playthrough Proof | **PASS** | Folder: `20261118_085910` (fresh (post-frontend commit)) | Media count: 62 | report.md: True | MD5 collisions: 0 | Districts: 4/4 verified |
| 9 | First-Run Parser Baselines & Held-Out Status | **PASS** | Recorded rates & held-out status: Dose Lab baseline: 24.2% (15/62); Space Stage baseline: 89.1%; founder set: not provided; agent-written seed set, not founder-written (n=4/exp too small to be meaningful) |
| 10 | Claims & Compliance Audit (Rule R4/R6) | **PASS** | Total occurrences: 10 (all explicitly hedged/disclaimed). Unhedged violations: 0 |
| 11 | Gitignore Coverage | **PASS** | Coverage confirmed: qa/out (True), __pycache__ (True) |

---

## Detailed Gate Findings

### Gate 1: Git Repository State

HEAD: `baeb307a` | Clean: False (expected audit files: True) | Ahead: 57

**Last 15 Commits:**
```
baeb307 feat(spec): experiment authoring form and validation UI
8a015a2 docs(spec): author experiment specification guide and worked example
bbdad8b feat(spec): spec-driven mentor hints and ask orbis vocabulary
84ff27b feat(spec): migrate PK Ward, Launch Bench, and Dose Response Lab to declarative specs
ef18cf4 feat(spec): migrate Titration Bench to declarative spec with golden-equivalence tests
9480cc1 feat(spec): experiment specification schema, loader, validator, and CLI
770cb62 docs(p1): record newest QA run 20261118_081803 in RECHECK_P1
712648f docs(p1): P1 recheck report with verification evidence
a041a00 test(p1): QA full run for 4 experiments and frontend freshness self-audit check
f625617 test(p1): touch e2e test at 390x844 with mobile interactions
778a313 chore: bump version to 0.5.0-dev
329012b fix(p1): complete font weights without synthetic bold
70d7cd8 fix(p1): comprehensive i18n coverage and template lint enforcement
67e52da fix(p1): experiment-specific briefing rules in plain language
fc6b442 fix(p1): align lobby scope, remove biology card and spanish locale, add practice buttons
```

### Gate 3: Pytest Test Suite

Exit code: 0

Command: `E:\Simly Orbis\fresh\Scripts\pytest.exe backend/tests`

Final line: `=============== 582 passed, 19162 warnings in 92.59s (0:01:32) ================`

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
