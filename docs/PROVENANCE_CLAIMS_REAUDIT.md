# Simly Orbis Provenance & Claims Re-Audit (P0-T3)

**Standard:** Section 18 (P0-T3) & Rules G3–G6 of *Simly Orbis MVP Build Specification*  
**Date:** 2026-11-14  
**Audit Scope:** All 32 validation rows in `validation/data/*.csv` and all repository documentation / UI copy  

---

## 1. Validation Row Provenance Audit

Every row across the 5 reference CSVs was audited against the three strict provenance integrity rules:
1. **Conditions vs. Values Consistency:** Stated conditions (doses, concentrations, orbital altitudes) agree with reference numbers.
2. **Zero Invented Retrieval Dates:** `retrieved_on` must remain strictly blank (`""`) until verified by a human expert.
3. **No Self-Derived Benchmarks:** Reference numbers must originate from primary literature, standard physical constants (IERS/CODATA), or explicit closed-form analytical identities—never our own engine simulation output.

### 1.1 Findings by Reference File

| File | Rows Checked | Unverified Count | Verified Count | Blank `retrieved_on` | Status | Notes / Provenance Category |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `chem_titration_references.csv` | 8 | 8 | 0 | 8 / 8 (100%) | **PASS** | Exact analytical mass conservation, CRC Handbook ($pK_a$), IUPAC indicator endpoints. |
| `pharma_pk_references.csv` | 14 | 14 | 0 | 14 / 14 (100%) | **PASS** | Published clinical bioequivalence literature (Portolés 2003, Bramlage 2008, Perera 2011, Blanchard 1983). |
| `pharma_trial_references.csv` | 0 | 0 | 0 | 0 / 0 | **PASS** | Reserved for future population trial benchmark cohorts. |
| `space_orbit_references.csv` | 5 | 5 | 0 | 5 / 5 (100%) | **PASS** | IERS Conventions ($\mu$), WGS-84 orbital mechanics (Curtis, Vallado). |
| `pkpd_references.csv` | 5 | 5 | 0 | 5 / 5 (100%) | **PASS** | Closed-form analytical identities (initial $C(0)$, steady-state $C_{ss}$, $\alpha+\beta$, $\alpha\beta$, $E(EC_{50})$). |
| **TOTAL** | **32** | **32** | **0** | **32 / 32 (100%)** | **PASS** | Zero unverified rows have invented dates. Zero unexplained rows. |

---

## 2. Text & Documentation Overclaiming Re-Audit

All Markdown files, UI source files, and configuration strings were scanned using `scripts/check_claims.py`:

| Target Term | Prohibited Context | Result in Repository | Compliance Finding |
| :--- | :--- | :---: | :--- |
| **"validated"** | Asserting platform / clinical validation | 3 occurrences | **PASS**: All 3 occurrences are explicitly hedged disclaimers ("What is NOT Validated", "not clinically validated"). |
| **"clinically proven"** | Claiming medical efficacy | 0 occurrences | **PASS**: Zero occurrences found. |
| **"replaces animal testing"** | Claiming total replacement of animal tests | 0 occurrences | **PASS**: Zero occurrences found. Formulated per G3 as "helps reduce, refine and prioritise experiments". |
| **"fda-approved"** | Asserting medical device clearance | 0 occurrences | **PASS**: Zero occurrences found. |

---

## 3. Governance Certification

- **Rule G3 (Honesty):** Orbis Lab is an educational simulation. It is not medical advice, not clinical evidence, and not mission-planning software.
- **Rule G4 (Real Proof Only):** All claims are verified against executable test runs and unique QA artifacts.
- **Rule G5 (No Fabricated Provenance):** Unverified benchmark rows remain blank on retrieval timestamps until primary source human review.
