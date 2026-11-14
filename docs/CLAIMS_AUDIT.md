# Claims Audit & Wording Verification

> **DISCLAIMER: Educational simulation platform. Not medical advice. Not clinical evidence.**
> Simly Orbis is an interactive laboratory learning simulator designed to build scientific intuition. It does not replace animal studies, physical bench trials, or human clinical trials.

This document records the audit of quantitative, performance, scientific, and capability claims across documentation, README, and frontend interfaces.

---

## 1. Claims Audit Register

| Claim & Text Snippet | Location | Claim Type | Source / Evidence | Action Taken / Status |
| :--- | :--- | :---: | :--- | :--- |
| **"achieving 60 FPS on our test laptop (AMD Ryzen, integrated graphics)"** | `README.md:10` | Fact with Source / Target | Measured locally on AMD Ryzen 7 5700U with integrated Radeon graphics in Low/Medium quality tier. In software WebGL environments, frame rates are lower. | Retained with explicit software-render caveat in [docs/KNOWN_ISSUES.md](KNOWN_ISSUES.md). |
| **"simulating up to 1,000 patients in under 20 ms"** | `README.md:10` | Target / Performance Fact | Vectorized NumPy Monte Carlo array calculation (`backend/app/modules/pharma_trial.py`); execution time measured via `time.perf_counter()`. | Retained as algorithmic compute time of the internal NumPy array. |
| **"Analytical Reality Checks: 11 / 11 Passed [PASS]"** | `README.md:74` | Fact with Source | `backend/tests/test_pk_engine.py`, `backend/tests/test_titration.py`, `backend/tests/test_reality_check.py`. | Retained; clarified as mathematical model internal consistency checks against textbook analytical formulas, not clinical validation. |
| **"Exact aqueous charge-balance equilibrium solver... Henderson-Hasselbalch relation used only for half-equivalence"** | `README.md:83` | Feature Description | Implemented in `backend/app/chem/titration.py:46` using iterative electroneutrality bisect/Newton root solver. | Retained; matches actual code implementation. |
| **"Drug parameters and therapeutic green/red thresholds"** | `backend/app/sim/drugs.json` | Risk / Pedagogical | Derived from published pharmacology reference monographs but thresholds adjusted for game balance. | Tagged explicitly as `game-balanced` in data and UI to prevent treatment cutoff confusion. |
| **"Clinical Validation" or "Empirical Validation"** | `docs/VALIDATION_REPORT.md` | Risk | Literature comparison against 22 published benchmark points. All currently marked `unverified`. | Labeled with prominent mandatory banner: *"Compared with published data for the stated conditions. Not clinical validation."* |
| **"10x faster / one tenth early cost"** | Pitch / Target claims | Target | Conceptual educational goals for simulation-based preparatory training before wet-lab access. | Audited: Any future mention must carry an explicit "target" label. Platform does not claim animal study replacement. |
| **"FDA Product Labels"** | `docs/VALIDATION_REPORT.md:27` | Fact with Source | Reference literature citations in `validation/data/pharma_pk_references.csv` sourced from published clinical literature and monograph parameters. | Verified factual citation provenance; explicitly tagged unverified until human review. |
| **"Orbital Mechanics & Launch Trajectory (`space.orbit`)"** | `docs/space_physics.md` | Feature Description / Model | Pure-Python Tsiolkovsky $\Delta v$, vis-viva, and Hohmann transfer equations evaluated against standard Earth $\mu$ ($3.986004418 \times 10^{14}\text{ m}^3/\text{s}^2$) and $R_\oplus = 6,371\text{ km}$. | Labeled as educational simulation targets and game-balanced ascent loss ($1,500\text{ m/s}$), not flight-readiness mission software. |
| **"Multi-Compartment PK/PD & Covariate Allometry (`pharma.pkpd`)"** | `docs/pkpd_models.md` | Feature Description / Model | 1- and 2-compartment open models with oral, IV bolus, and IV infusion routes; Cockcroft-Gault renal scaling and weight allometry; Emax pharmacodynamic model. | Explicit adult-only covariate ranges (age 18–90, weight 40–150 kg, CrCl 15–150 mL/min). Pediatric requests rejected. Tagged as educational simulation, not medical advice. |

---

## 2. Summary of Adjustments Made

1. **Clarified Scientific Scope**:
   - Confirmed that all titration references specify exact aqueous charge-balance solver dynamics, with Henderson-Hasselbalch used solely for buffer half-equivalence checks ($pH = pK_a$).
   - Explicitly documented that indicator colors interpolate across transition ranges.
2. **Pedagogical vs Clinical Distinction**:
   - Ensured `drugs.json` game-balanced thresholds are documented in [docs/KNOWN_ISSUES.md](KNOWN_ISSUES.md) and labeled in the Reality Check UI.
   - Added "Honest Status" section to [README.md](../README.md).
3. **Animal & Clinical Replacement Claims**:
   - Confirmed zero claims stating Simly Orbis replaces clinical trials or animal studies. All literature matches are educational comparisons under stated experimental assumptions.
