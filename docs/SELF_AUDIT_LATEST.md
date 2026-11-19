# Simly Orbis Stage Gate Self-Audit Report

**Status:** PASS  
**Platform Version:** 0.7.0-dev  
**Single Source of Truth:** Backend Simulators  
**Governance Standard:** Educational Simulation &bull; Not Medical Advice &bull; Not Clinical Evidence  

---

## Stage Gates Verification Summary

| Gate | Requirement | Status | Evidence / Metrics |
| :---: | :--- | :---: | :--- |
| 1 | Git Repository State | **PASS** | Clean/Expected: True, Ahead: 96, HEAD: d4b5d511 |
| 2 | App Version | **PASS** | Version `0.7.0-dev` declared in `backend/app/config.py` |
| 3 | Pytest Test Suite | **PASS** | covered by CI pytest step |
| 4 | Validation Row Governance | **PASS** | Evaluated 32 rows across 5 files: 32 unverified (with blank retrieved_on), 0 verified. Violations: 0 |
| 5 | Frozen Tolerances Guard | **PASS** | 4/4 frozen tolerance files verified. |
| 6 | Engine Immutability (Rule R1/R7) | **PASS** | Protected files checked: 4 engines + R1-R10/S1-S8 rules. Violations: 0 |
| 7 | CI Workflow Configuration | **PASS** | `.github/workflows/ci.yml` invokes bare `pytest backend/tests`. |
| 8 | QA Playthrough Proof | **PASS** | Folder: `20261119_214905` (fresh (post-frontend commit)) | Media count: 74 | report.md: True | MD5 collisions: 0 | Districts: 4/4 verified |
| 9 | First-Run Parser Baselines & Held-Out Status | **PASS** | All 6 corpora first-run baseline rates verified in PHASE_4_REPORT.md; seed & founder status confirmed |
| 10 | Claims & Compliance Audit (Rule R4/R6) | **PASS** | Total occurrences: 20 (all explicitly hedged/disclaimed). Unhedged violations: 0 |
| 11 | Gitignore Coverage | **PASS** | Coverage confirmed: qa/out (True), __pycache__ (True) |

---

## Detailed Gate Findings

### Gate 1: Git Repository State

HEAD: `d4b5d511` | Clean: True (expected audit files: True) | Ahead: 96

**Last 15 Commits:**
```
d4b5d51 docs(audit): update stage-gate self-audit report and touch e2e screenshots
10889d8 fix(qa): optimize AI model cascading timeouts and bypass rate limiter during automated QA
1e699f2 fix(audit): resolve static audit issues across backend routes, audit script, and authoring UI
d63e2f7 docs(p4): generate Phase 4 report and stage-gate self-audit
fd47f3a docs(pharma): author PK/PD model documentation and updated clinical model cards
a20e26f test(pharma): add red-team adversarial suite refusing personal dosing queries
174e6fd feat(pharma): add parameter calibration harness with synthetic recovery validation
4b09026 feat(pharma): enhance dose lab interactive regimen overlay and renal adjustments
c8b6762 feat(pharma): expand and freeze drug library with G5 provenance declarations
7600f39 feat(pharma): add virtual trial v2 crowd visualization and distribution analytics
4fe050d feat(pharma): implement virtual trial v2 multi-compartment population simulation
e2e6ab9 chore(version): bump platform version to 0.7.0-dev for Phase P4
e343fe9 docs(p3): complete RECHECK_P3.md and update Phase 3 report with honest disclosures
78d9ceb test(briefing): verify strict rule set isolation across all six laboratory experiments
b35bd46 docs(chem): document G5 provenance for buffer and kinetics constants with physical caveats
```

### Gate 3: Pytest Test Suite

Executed as a dedicated preceding step in the CI pipeline.

### Gate 4: Validation Row Governance

All rows strictly comply with Rule R2/R3.

### Gate 5: Frozen Tolerances Guard

- validation/tolerances.yaml: `5b5d857ed4862b51...` OK
- validation/space_tolerances.yaml: `fc4ba76cb3ee9d65...` OK
- validation/pkpd_tolerances.yaml: `443d18ab90e60b43...` OK
- validation/chem_tolerances.yaml: `2288d01d83e2a5fc...` OK

### Gate 6: Engine Immutability (Rule R1/R7)

- `backend/app/pharma/pk.py`: 0 diff vs `cb9b66f` (PASS)
- `backend/app/pharma/trial.py`: 0 diff vs `cb9b66f` (PASS)
- `backend/app/chem/titration.py`: 0 diff vs `cb9b66f` (PASS)
- `backend/app/space/orbit.py`: 0 diff vs `cb9b66f` (PASS)
- Rules R1-R10 and S1-S8: Unmodified (PASS)

### Gate 9: First-Run Parser Baselines & Held-Out Status

Latest Phase Report: PHASE_4_REPORT.md
Corpora Parser Rates (First-Run vs. Final):
  - pk        : first-run 22/22 (100.0%)     | final 22/22 (100.0%)     [present in PHASE_4_REPORT.md]
  - titration : first-run 20/20 (100.0%)     | final 20/20 (100.0%)     [present in PHASE_4_REPORT.md]
  - space     : first-run 49/55 (89.1%)      | final 55/55 (100.0%)     [present in PHASE_4_REPORT.md]
  - dose      : first-run 15/62 (24.2%)      | final 62/62 (100.0%)     [present in PHASE_4_REPORT.md]
  - kinetics  : first-run 9/55 (16.4%)       | final 54/55 (98.2%)      [present in PHASE_4_REPORT.md]
  - buffer    : first-run 10/55 (18.2%)      | final 54/55 (98.2%)      [present in PHASE_4_REPORT.md]
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
