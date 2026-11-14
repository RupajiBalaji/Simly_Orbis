# Model Card: pharma.trial (Virtual Trial Cohort Simulation)

**Engine ID:** `pharma.trial`  
**Engine Version:** `0.4.1-dev`  
**Status:** Educational Simulation &bull; Unverified  

---

## 1. Purpose & Intended Use
- **Purpose:** Simulates inter-individual pharmacokinetic variability across a synthetic adult patient cohort using log-normal parameter distributions.
- **Intended Use:** Teaching statistical power, biological variance, sample size considerations, and outlier observation in virtual clinical pharmacology.
- **Out-of-Scope Use:** Patient clinical trial planning, bioequivalence submission, or regulatory safety forecasting.

---

## 2. Mathematical Equations
For subject $i$, pharmacokinetic parameters are sampled from log-normal distributions:
$$P_i = P_{\text{pop}} \cdot \exp(\eta_i), \quad \eta_i \sim \mathcal{N}(0, \omega^2)$$
where $P_{\text{pop}}$ is the population median and $\omega$ is the between-subject variability (BSV) coefficient of variation:
$$\omega = \sqrt{\ln(1 + CV^2)}$$
Summary metrics compute cohort median, 5th, and 95th percentile intervals:
$$\text{CI}_{90\%} = [P_{5}, P_{95}]$$

---

## 3. Assumptions & Parameter Ranges
- **Assumptions:** Uncorrelated log-normal variance components ($\eta_{CL} \perp \eta_{V}$), identical absorption rates unless specified, linear disposition.
- **Valid Adult Cohort Bounds:**
  - Sample Size ($N$): $5$ to $1000$ subjects
  - Pop Clearance ($CL_{\text{pop}}$): $0.5$ to $50.0\text{ L/h}$
  - Pop Volume ($V_{\text{pop}}$): $5.0$ to $200.0\text{ L}$
  - $CV_{CL}, CV_{V}$: $5\%$ to $80\%$

---

## 4. Known Error Sources & Limitations
- Truncated covariate correlations (e.g., clearance-weight correlation is simplified).
- Does not simulate dropout, compliance non-adherence, or multi-dose protocol deviations.

---

## 5. Validation Status & Provenance
- **Validation Status:** Deterministic statistical test harness passing; empirical clinical cohorts unverified.
- **References:** `validation/data/pharma_trial_references.csv` (reserved for benchmark cohorts).
- **Acceptance Criteria:** Cohort mean within $\pm 10\%$ of theoretical analytical population mean.

---

## 6. Changelog
- `0.2.0-dev`: Initial cohort generator with seeded pseudo-random generator.
- `0.4.1-dev`: Model card formalized per MVP Specification Section 14.4.
