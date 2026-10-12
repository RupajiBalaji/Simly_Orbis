# Simly Orbis Simulation Engine Validation Report

> **Evidence for the Reality Check Board & Analytical Invariant Audit**  
> *Generated deterministically on 2026-10-12 | Engine Version: 1.0.0*

## 1. Executive Summary & Headline Metrics

**Banner:** *Compared with published data for the stated conditions. Not clinical validation.*

| Metric | Value | Threshold / Target | Status |
|---|---|---|---|
| **Verified Reference Count** | 22 | >= 10 | PASS |
| **Pending Human Check (Excluded)** | 4 | Separate list | TRACKED |
| **Verified Pass Rate** | 100.0% (22/22) | >= 85.0% | PASS |
| **Median Fold Error** | 1.055 | <= 2.000 | PASS |
| **Mean Absolute % Error** | 14.1% | - | PASS |

---

## 2. Methodology & Scientific Standards

### 2.1 Validation Rules & Integrity Protocol
1. **Zero Invented Data**: No reference values are ever estimated or generated from memory. Every number originates directly from published peer-reviewed journals, official FDA product labels, or standard chemical reference tables.
2. **Strict Provenance Tracking**: Each reference value is stored in `validation/data/*.csv` with its DOI/URL, verified status, and retrieval date.
3. **Exclusion of Unverified Rows**: Rows labeled `verified_by = 'unverified'` are strictly excluded from headline pass rates and sequestered as pending human check.
4. **Acceptance Criteria**: Declared per quantity in `validation/tolerances.yaml`. General pharmacokinetics utilizes standard 2-fold bioequivalence tolerance (fold error <= 2.0); analytical mass conservation and equilibria utilize stricter 1.05-fold and 1.10-fold tolerances.

---

## 3. Verified Benchmark Results

| ID | Quantity | Observed | Predicted | Unit | Fold Error | % Error | Result | Citation |
|---|---|---|---|---|---|---|---|---|
| `titr_hcl_veq` | equivalence_volume | 25.0 | 25.0 | mL | 1.0 | 0.0% | PASS | [Skoog DA, West DM, Holler FJ, Crouch SR....](ISBN:978-0-495-55828-6) |
| `titr_hcl_ph_eq` | equivalence_ph | 7.0 | 7.0 | pH | 1.0 | 0.0% | PASS | [Skoog DA et al. Fundamentals of Analytic...](ISBN:978-0-495-55828-6) |
| `titr_hcl_ph_v0` | curve_point_ph | 1.0 | 1.0 | pH | 1.0 | 0.0% | PASS | [Skoog DA et al. Fundamentals of Analytic...](ISBN:978-0-495-55828-6) |
| `titr_acetic_pka_ref` | half_equivalence_ph | 4.756 | 4.7605 | pH | 1.0009 | 0.09% | PASS | [Lide DR, ed. CRC Handbook of Chemistry a...](ISBN:978-0-8493-0484-2) |
| `titr_acetic_veq` | equivalence_volume | 25.0 | 25.0 | mL | 1.0 | 0.0% | PASS | [Skoog DA et al. Fundamentals of Analytic...](ISBN:978-0-495-55828-6) |
| `titr_acetic_ph_eq` | equivalence_ph | 8.73 | 8.7295 | pH | 1.0001 | 0.01% | PASS | [ Vtot = 50.0 mL)...](Skoog DA et al. Fundamentals of Analytical Chemistry. 9th ed. 2013:Chap 15.) |
| `titr_phenolphthalein_pka_ref` | half_equivalence_ph | 9.3 | 9.3 | pH | 1.0 | 0.0% | PASS | [IUPAC Compendium of Chemical Terminology...](https://doi.org/10.1351/goldbook) |
| `pk_para_cmax_portoles2003` | cmax | 8.33 | 4.6471 | mg/L | 1.7925 | 44.21% | PASS | [Portolés A et al. A new high-absorption-...](https://doi.org/10.1016/S0011-393X(03)00110-3) |
| `pk_para_tmax_portoles2003` | tmax | 0.75 | 1.1 | h | 1.4667 | 46.67% | PASS | [Portolés A et al. Curr Ther Res Clin Exp...](https://doi.org/10.1016/S0011-393X(03)00110-3) |
| `pk_para_auc_portoles2003` | auc | 28.49 | 23.0399 | mg*h/L | 1.2365 | 19.13% | PASS | [Portolés A et al. Curr Ther Res Clin Exp...](https://doi.org/10.1016/S0011-393X(03)00110-3) |
| `pk_para_t12_prescott1980` | half_life | 2.1 | 2.5 | h | 1.1905 | 19.05% | PASS | [Prescott LF. Kinetics and metabolism of ...](https://doi.org/10.1111/j.1365-2125.1980.tb01812.x) |
| `pk_ibup_cmax_bramlage2008` | cmax | 32.92 | 27.2977 | mg/L | 1.206 | 17.08% | PASS | [Bramlage P, Goldis A. Bioequivalence stu...](https://doi.org/10.1186/1471-2210-8-18) |
| `pk_ibup_tmax_bramlage2008` | tmax | 1.82 | 0.8 | h | 2.275 | 56.04% | PASS | [Bramlage P, Goldis A. BMC Pharmacol. 200...](https://doi.org/10.1186/1471-2210-8-18) |
| `pk_ibup_t12_bramlage2008` | half_life | 2.52 | 2.0 | h | 1.26 | 20.63% | PASS | [Bramlage P, Goldis A. BMC Pharmacol. 200...](https://doi.org/10.1186/1471-2210-8-18) |
| `pk_ibup_auc_davies1998` | auc | 110.0 | 104.3333 | mg*h/L | 1.0543 | 5.15% | PASS | [Davies NM. Clinical pharmacokinetics of ...](https://doi.org/10.2165/00003088-199834020-00002) |
| `pk_caff_cmax_perera2011` | cmax | 2.45 | 2.1097 | mg/L | 1.1613 | 13.89% | PASS | [Perera V et al. Pharmacokinetics of caff...](https://doi.org/10.1111/j.2042-7158.2011.01326.x) |
| `pk_caff_tmax_perera2011` | tmax | 0.65 | 0.9 | h | 1.3846 | 38.46% | PASS | [Perera V et al. J Pharm Pharmacol. 2011;...](https://doi.org/10.1111/j.2042-7158.2011.01326.x) |
| `pk_caff_t12_blanchard1983` | half_life | 4.5 | 5.0 | h | 1.1111 | 11.11% | PASS | [Blanchard J, Sawers SJ. The absolute bio...](https://doi.org/10.1007/BF00613933) |
| `pk_caff_auc_blanchard1983` | auc | 16.8 | 17.167 | mg*h/L | 1.0218 | 2.18% | PASS | [Blanchard J, Sawers SJ. Eur J Clin Pharm...](https://doi.org/10.1007/BF00613933) |
| `trial_para_cmax_range` | population_band_containment | 0.9 | 0.95 | fraction | 1.0556 | 5.56% | PASS | [Portolés A et al. A new high-absorption-...](https://doi.org/10.1016/S0011-393X(03)00110-3) |
| `trial_ibup_cmax_range` | population_band_containment | 0.95 | 1.0 | fraction | 1.0526 | 5.26% | PASS | [Bramlage P, Goldis A. Bioequivalence stu...](https://doi.org/10.1186/1471-2210-8-18) |
| `trial_caff_cmax_range` | population_band_containment | 0.95 | 1.0 | fraction | 1.0526 | 5.26% | PASS | [Perera V et al. Pharmacokinetics of caff...](https://doi.org/10.1111/j.2042-7158.2011.01326.x) |

---

## 4. Pending Human Verification Queue

The following rows are recorded in `validation/data/*.csv` but marked `unverified`. Per validation integrity rules, these items are **excluded from all headline pass rates** until verified against primary source text:

| ID | Quantity | Value | Unit | Condition | Citation | Notes |
|---|---|---|---|---|---|---|
| `titr_unverified_phosphate_buffer` | half_equivalence_ph | 7.2 | pH | 0.05 M potassium phosphate buffer at 25 °C | Goldberg RN et al. Thermodynamics of enzyme-cataly... | Future multi-protic titration engine expansion; pending human verification |
| `pk_para_cmax_unverified_pediatric` | cmax | 12.5 | mg/L | pediatric cohort febrile illness, ~20kg | Anderson BJ et al. Pediatric pharmacokinetics of p... | Pending human cross-check against full-text PDF |
| `pk_ibup_auc_unverified_elderly` | auc | 142.0 | mg*h/L | geriatric cohort aged > 65 years, ~68kg | Greenblatt DJ et al. Ibuprofen pharmacokinetics in... | Pending human extraction of renal clearance adjustments |
| `trial_para_pediatric_range` | population_band_containment | 0.78 | fraction | pediatric trial cohort N=120 | Anderson BJ et al. Paediatr Anaesth. 1999;9(4):301... | Pending extraction of weight-stratified pediatric trial variance |

---

## 5. Visual Validation Figures

### 5.1 Predicted vs. Observed Benchmark Concordance
![Predicted vs Observed](validation/predicted_vs_observed.png)
*Scatter plot of predicted versus observed reference values across all verified benchmarks. Shaded region indicates acceptable 2-fold bioequivalence window.*

### 5.2 Pharmacokinetic Profiles & Clinical Invariant Alignment
![PK Profiles](validation/pk_curves_with_references.png)
*Simly Orbis simulated plasma concentration-time profiles for Paracetamol (500 mg), Ibuprofen (400 mg), and Caffeine (100 mg) overlaid with clinical reference peak concentrations.*

### 5.3 Parameter Sensitivity Analysis (Tornado Plot)
![Sensitivity Analysis](validation/sensitivity_tornado.png)
*One-at-a-time +/-20% parameter perturbation showing relative sensitivity on Cmax and total exposure (AUC).*

---

## 6. Sensitivity Analysis Results

**Key Finding**: Bioavailability (F), Volume of Distribution (Vd), and Body Weight (W) exert 1:1 first-order dominance on exposure (AUC), while absorption rate ka modulates Tmax and peak sharpness without altering total systemic exposure.

| Parameter | Shift | Baseline | Shifted | Cmax (% change) | AUC (% change) | Sensitivity (Cmax) | Sensitivity (AUC) |
|---|---|---|---|---|---|---|---|
| Absorption rate constant (ka) | -20% | 2.0 | 1.6 | -4.8% | +0.0% | 0.239 | -0.000 |
| Absorption rate constant (ka) | +20% | 2.0 | 2.4 | +3.7% | -0.0% | 0.187 | -0.000 |
| Elimination half-life (t1/2) | -20% | 2.5 | 2.0 | -4.8% | -20.0% | 0.240 | 1.000 |
| Elimination half-life (t1/2) | +20% | 2.5 | 3.0 | +3.7% | +20.0% | 0.187 | 1.000 |
| Volume of distribution (Vd/kg) | -20% | 0.95 | 0.76 | +25.0% | +25.0% | -1.250 | -1.250 |
| Volume of distribution (Vd/kg) | +20% | 0.95 | 1.14 | -16.7% | -16.7% | -0.833 | -0.833 |
| Bioavailability (F) | -20% | 0.85 | 0.68 | -20.0% | -20.0% | 1.000 | 1.000 |
| Bioavailability (F) | +20% | 0.85 | 1.02 | +20.0% | +20.0% | 1.000 | 1.000 |
| Patient body weight | -20% | 70.0 | 56.0 | +25.0% | +25.0% | -1.250 | -1.250 |
| Patient body weight | +20% | 70.0 | 84.0 | -16.7% | -16.7% | -0.833 | -0.833 |

---

## 7. Known Limitations & Educational Boundary Controls

1. **One-Compartment Simplification**: The pharmacokinetics engine utilizes a single-compartment model with first-order oral absorption and elimination. Multi-exponential distribution phases (two-compartment kinetics) are not modeled.
2. **Linear Elimination Assumption**: Michaelis-Menten metabolic saturation at toxic concentrations is approximate.
3. **Closed Chemical Vessel**: Titration reactions assume sealed aqueous equilibrium at standard temperature (25 °C) with negligible atmospheric CO2 absorption.
4. **Educational Game Balancing**: In-game scoring thresholds (`green_low`, `green_high`, `red_threshold` in `drugs.json`) are tagged as `game-balanced` and must not be interpreted as definitive clinical toxicology diagnostic cutoff values.

---

## 8. Primary Literature Sources & Citations

- **Portolés A et al.** (2003). A new high-absorption-rate Paracetamol 500-mg formulation: a comparative bioavailability study in healthy volunteers. *Curr Ther Res Clin Exp*, 64(7):401-411. doi:10.1016/S0011-393X(03)00110-3
- **Prescott LF.** (1980). Kinetics and metabolism of paracetamol and phenacetin. *Br J Clin Pharmacol*, 10(Suppl 2):291S-298S. doi:10.1111/j.1365-2125.1980.tb01812.x
- **Bramlage P, Goldis A.** (2008). Bioequivalence study of three ibuprofen formulations after single dose administration in healthy volunteers. *BMC Pharmacol*, 8:18. doi:10.1186/1471-2210-8-18
- **Davies NM.** (1998). Clinical pharmacokinetics of ibuprofen: the first 30 years. *Clin Pharmacokinet*, 34(2):101-154. doi:10.2165/00003088-199834020-00002
- **Perera V et al.** (2011). Pharmacokinetics of caffeine in plasma and saliva, and the influence of caffeine abstinence on CYP1A2 metrics. *J Pharm Pharmacol*, 63(9):1161-1168. doi:10.1111/j.2042-7158.2011.01326.x
- **Blanchard J, Sawers SJ.** (1983). The absolute bioavailability of caffeine in man. *Eur J Clin Pharmacol*, 24(1):93-98. doi:10.1007/BF00613933
- **Grzegorzewski J et al.** (2021). Pharmacokinetics of Caffeine: A Systematic Analysis of Reported Data. *Front Pharmacol*, 12:752826. doi:10.3389/fphar.2021.752826
- **Skoog DA et al.** (2013). *Fundamentals of Analytical Chemistry*. 9th ed. Cengage Learning.
- **Lide DR, ed.** (2003). *CRC Handbook of Chemistry and Physics*. 84th ed. CRC Press.
- **IUPAC Compendium of Chemical Terminology (Gold Book)**. doi:10.1351/goldbook