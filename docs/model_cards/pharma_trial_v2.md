# Model Card: pharma.trial_v2 (Virtual Trial v2 Population Simulation)

**Engine ID:** `pharma.trial_v2`  
**Engine Version:** `0.7.0-dev`  
**Status:** Educational Simulation &bull; Unverified  

---

## 1. Purpose & Intended Use
- **Purpose:** High-performance population pharmacokinetic/pharmacodynamic (PopPK/PD) simulator generating heterogeneous adult cohorts ($N = 10$ to $1000$ patients) under log-normal inter-individual variability and physiological covariate distributions.
- **Intended Use:** Teaching statistical power, biological variability, therapeutic target attainment, adverse event incidence, and covariate impact (weight, age, renal clearance) in virtual clinical trials.
- **Out-of-Scope Use:** Patient clinical trial design, bioequivalence submission, clinical dosing recommendations, or regulatory safety forecasting.

---

## 2. Mathematical Equations
For virtual subject $i$, parameters are sampled with log-normal inter-individual variability:
$$\theta_i = \theta_{\text{pop}} \cdot \exp(\eta_{\theta,i}), \quad \eta_{\theta,i} \sim \mathcal{N}(0, \omega_\theta^2)$$
where $\omega_\theta = \sqrt{\ln(1 + CV^2)}$.

Demographic covariates are sampled from adult distributions:
- Weight $W_i \sim \mathcal{N}(74.0, 14.0^2)\text{ kg}$, bounded $[40, 140]\text{ kg}$.
- Age $A_i \sim \mathcal{N}(48.0, 16.0^2)\text{ yr}$, bounded $[18, 85]\text{ yr}$.
- Creatinine Clearance $\text{CrCl}_i \sim \text{LogNormal}(\mu_{\text{crcl}}, \sigma_{\text{crcl}}^2)$, bounded $[15, 150]\text{ mL/min}$.

Covariate scaling adjusts clearance and volume:
$$CL_i = CL_{\text{pop}} \cdot \left(\frac{W_i}{70}\right)^{0.75} \cdot \left((1 - f_e) + f_e \cdot \frac{\text{CrCl}_i}{120}\right)$$
$$V_{d,i} = V_{d,\text{pop}} \cdot \left(\frac{W_i}{70}\right)^{1.0}$$

Distribution percentiles (P5, P25, P50/median, P75, P95) and target window statistics are computed across the simulated population.

---

## 3. Assumptions & Parameter Ranges
- **Assumptions:** Uncorrelated random effects between clearance and volume; 1-compartment oral or IV disposition per individual; adult-only physiology.
- **Valid Cohort Bounds:**
  - Population size ($N$): $10$ to $1000$ patients
  - Dosing regimens: single dose or multiple steady-state dosing
  - Supported compounds: all 12 compounds in `backend/data/pharma_drugs.yaml`

---

## 4. Known Error Sources & Limitations
- Covariate correlations are parameterized independently rather than through full demographic joint covariance matrices.
- Non-linear protein binding saturation and organ-specific blood flow distributions are simplified.
- Does not simulate protocol non-compliance, dropouts, or trial attrition.

---

## 5. Validation Status & Provenance
- **Validation Status:** Unverified (awaiting formal clinical benchmark verification).
- **Provenance:** G5 game-balanced approximate educational simulation.
- **Performance Benchmark:** 1000-patient simulation executes in $< 5.0\text{ s}$ on single-thread CPU (~4.0 s observed).

---

## 6. Changelog
- `0.7.0-dev`: Initial Virtual Trial v2 engine with multi-patient simulation, crowd visualizations, covariate scaling, CSV export, and responsive distribution percentiles.
