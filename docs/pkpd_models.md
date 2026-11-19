# Pharmacokinetic & Pharmacodynamic (PK/PD) Mathematical Models

**Platform Version:** `0.7.0-dev`  
**Compliance Classification:** Educational Simulation &bull; Non-Clinical  
**Rule Adherence:** R1 (Engine Single Source of Truth), R5 (G5 Provenance & Blank Retrieved-On), R6 (Honest Educational Disclaimers, Adult Covariates Only)

---

## 1. Single-Compartment Pharmacokinetics (`pharma.pk`)

### 1.1 Model Overview
The 1-compartment model treats the body as a single well-mixed kinetic pool with instantaneous and uniform distribution. Elimination occurs as a first-order process proportional to the central plasma concentration.

### 1.2 Mathematical Formulations

#### Intravenous (IV) Bolus
For an instantaneous IV injection of dose $D$ into distribution volume $V_d$:
$$C(t) = \frac{D}{V_d} e^{-k_e t}$$
where:
- $k_e = \frac{CL}{V_d}$ is the elimination rate constant ($h^{-1}$).
- Elimination half-life: $t_{1/2} = \frac{\ln(2)}{k_e}$.
- Total systemic exposure: $\text{AUC}_{0-\infty} = \frac{D}{CL}$.

#### Extravascular (Oral) Administration (Bateman Function)
Following oral dosing with bioavailability $F$ and absorption rate $k_a$ ($k_a \neq k_e$):
$$C(t) = \frac{D \cdot F \cdot k_a}{V_d (k_a - k_e)} \left( e^{-k_e t} - e^{-k_a t} \right)$$
Key derived analytical metrics:
- Time of peak concentration ($t_{\max}$):
  $$t_{\max} = \frac{\ln(k_a / k_e)}{k_a - k_e}$$
- Peak concentration ($C_{\max}$):
  $$C_{\max} = C(t_{\max})$$
- Area under the curve:
  $$\text{AUC}_{0-\infty} = \int_0^\infty C(t) dt = \frac{F \cdot D}{CL}$$

#### Multiple Dosing at Steady State
Under repeated oral dosing at interval $\tau$:
$$C_{\text{ss}}(t) = \frac{D \cdot F \cdot k_a}{V_d (k_a - k_e)} \left( \frac{e^{-k_e t}}{1 - e^{-k_e \tau}} - \frac{e^{-k_a t}}{1 - e^{-k_a \tau}} \right)$$
- Steady-state average concentration: $C_{\text{avg,ss}} = \frac{F \cdot D}{CL \cdot \tau}$.
- Accumulation factor: $R = \frac{1}{1 - e^{-k_e \tau}}$.

---

## 2. Two-Compartment Pharmacokinetics (`pharma.pkpd` / `pharma.trial_v2`)

### 2.1 Model Overview
The 2-compartment model accounts for rapid initial vascular distribution followed by slower reversible exchange with a peripheral tissue compartment.

### 2.2 Micro-Constants & Differential System
$$\frac{dA_1}{dt} = - (k_{10} + k_{12}) A_1 + k_{21} A_2$$
$$\frac{dA_2}{dt} = k_{12} A_1 - k_{21} A_2$$
where:
- $A_1(t)$ is the drug amount in the central compartment ($V_1$), with plasma concentration $C_p(t) = A_1(t) / V_1$.
- $A_2(t)$ is the drug amount in the peripheral tissue compartment ($V_2$).
- $k_{10} = \frac{CL}{V_1}$ (central elimination rate constant).
- $k_{12} = \frac{Q}{V_1}$ (inter-compartmental transfer rate from central to peripheral).
- $k_{21} = \frac{Q}{V_2}$ (inter-compartmental transfer rate from peripheral to central).
- $Q$ is inter-compartmental clearance ($L/h$).

### 2.3 Macro-Constants (Biexponential Solution)
Following IV bolus administration ($A_1(0) = D, A_2(0) = 0$):
$$C(t) = A e^{-\alpha t} + B e^{-\beta t}$$
The hybrid distribution ($\alpha$) and terminal disposition ($\beta$) rate constants satisfy:
$$\alpha + \beta = k_{10} + k_{12} + k_{21}$$
$$\alpha \beta = k_{10} k_{21}$$
$$\alpha, \beta = \frac{(k_{10} + k_{12} + k_{21}) \pm \sqrt{(k_{10} + k_{12} + k_{21})^2 - 4 k_{10} k_{21}}}{2}$$
The initial coefficient amplitudes are:
$$A = \frac{D}{V_1} \frac{\alpha - k_{21}}{\alpha - \beta}, \quad B = \frac{D}{V_1} \frac{k_{21} - \beta}{\alpha - \beta}$$

---

## 3. Pharmacodynamics & Effect Compartment (`pharma.pkpd`)

### 3.1 Sigmoid $E_{\max}$ (Hill) Model
The relationship between concentration and pharmacological effect is governed by the Hill equation:
$$E(C) = E_0 + \frac{E_{\max} \cdot C^\gamma}{EC_{50}^\gamma + C^\gamma}$$
where:
- $E_0$ is the baseline pharmacological effect.
- $E_{\max}$ is the maximum achievable drug effect above baseline.
- $EC_{50}$ is the concentration producing 50% of maximum effect.
- $\gamma$ (Hill coefficient) governs the steepness of the concentration-response sigmoidal curve ($\gamma = 1$: hyperbolic; $\gamma > 1$: positive cooperativity; $\gamma < 1$: shallow response).

### 3.2 Effect Compartment ($k_{e0}$) & Hysteresis
To capture temporal delay between plasma drug peak and clinical effect (hysteresis loop), a hypothetical effect compartment is modeled:
$$\frac{dC_e}{dt} = k_{e0} (C_p(t) - C_e(t))$$
where:
- $C_e(t)$ is the active biophase / effect-site concentration.
- $k_{e0}$ is the first-order rate constant of effect equilibration ($h^{-1}$).
- Half-life of equilibration: $t_{1/2,ke0} = \frac{\ln(2)}{k_{e0}}$.

---

## 4. Adult Covariate Scaling Models

Orbis Lab restricts all covariate modifications strictly to adult physiological bounds (Age 18–90 years, Weight 40–150 kg, Creatinine Clearance 15–150 mL/min). Paediatric populations are strictly unsupported.

### 4.1 Allometric Weight Scaling
Based on Kleiber's law and standard physiological allometry:
$$V_{d,i} = V_{d,\text{ref}} \cdot \left(\frac{W_i}{70}\right)^{1.0}$$
$$CL_i = CL_{\text{ref}} \cdot \left(\frac{W_i}{70}\right)^{0.75}$$
where reference values correspond to a standard 70 kg adult.

### 4.2 Renal Function Adjustment (Cockcroft-Gault Fraction)
For drugs eliminated in whole or in part by glomerular filtration:
$$CL_i = CL_{\text{ref}} \cdot \left( (1 - f_e) + f_e \cdot \frac{\text{CrCl}_i}{120} \right)$$
where:
- $f_e$ is the fraction of drug eliminated unchanged by the kidneys ($0.0 \le f_e \le 1.0$).
- $120\text{ mL/min}$ is baseline reference creatinine clearance.
- Renal impairment tiers:
  - Normal: $\text{CrCl} \ge 90\text{ mL/min}$
  - Mild impairment: $60 \le \text{CrCl} < 90\text{ mL/min}$
  - Moderate impairment: $30 \le \text{CrCl} < 60\text{ mL/min}$
  - Severe impairment: $15 \le \text{CrCl} < 30\text{ mL/min}$

### 4.3 Age Scaling
In elderly adult populations ($\text{Age} > 65$ years), renal and hepatic metabolic reserve declines:
$$CL_{\text{age}} = CL_i \cdot \left(1.0 - 0.005 \cdot (\text{Age} - 65)\right)$$
capped at a minimum of 40% of baseline clearance.

---

## 5. Virtual Trial v2 Population Methodology (`pharma.trial_v2`)

### 5.1 Inter-Individual Variability (IIV)
Pharmacokinetic parameters across virtual cohorts are modeled with log-normal distributions to preserve non-negativity:
$$P_i = P_{\text{pop}} \cdot \exp(\eta_{P,i}), \quad \eta_{P,i} \sim \mathcal{N}(0, \omega_P^2)$$
where $\omega_P = \sqrt{\ln(1 + CV^2)}$.

### 5.2 Synthetic Adult Demographic Sampling
Virtual subjects are generated with realistic physiological distributions:
- Weight $W_i \sim \mathcal{N}(74.0, 14.0^2)\text{ kg}$, bounded $[40.0, 140.0]$.
- Age $A_i \sim \mathcal{N}(48.0, 16.0^2)\text{ yr}$, bounded $[18.0, 85.0]$.
- $\text{CrCl}_i$ derived from age and weight distribution with log-normal variability ($\sim 105 \pm 28\text{ mL/min}$, bounded $[15.0, 150.0]$).

### 5.3 Distribution Analytics & Percentiles
For cohort sample sizes $N \in [10, 1000]$:
- Time curves compute 5th, 25th, 50th (median), 75th, and 95th percentiles at each evaluation knot.
- Population summary metrics calculate mean, standard deviation, interquartile range (IQR), and non-parametric 90% confidence bounds $[P_5, P_{95}]$.

---

## 6. Simplifications, Caveats & First-Order Error Analysis

| Model Assumption | Simplification in Engine | First-Order Error & Clinical Caveat |
| :--- | :--- | :--- |
| **Compartment Structure** | 1-compartment model assumes instantaneous mixing across all tissues. | Neglects distribution phase $\alpha$. For highly lipophilic drugs (e.g. fentanyl, propofol), peak concentrations immediately post-dose are underestimated by ~20–40%. |
| **Linear Elimination** | Elimination rate is strictly first-order ($CL$ is constant over dose). | Fails when metabolic enzymes or transporters saturate (Michaelis-Menten kinetics, e.g. phenytoin, high-dose ethanol, aspirin). Overdoses will exhibit disproportionate non-linear accumulation. |
| **Protein Binding** | Models simulate total drug concentration, assuming constant free fraction ($f_u$). | Critical illness, severe hypoalbuminemia, or uraemia alters $f_u$ by ~10–50%, altering free active drug exposure without changing measured total drug. |
| **Bioavailability Variance** | Bioavailability $F$ is treated as constant across doses and meals. | Food effect (high-fat meal delay or enhancement) can shift $t_{\max}$ by 1–3 hours and $F$ by 20–50% in real physiology. |
| **Absorption Kinetics** | First-order absorption rate $k_a$ assumes uniform GI transit. | Gastric emptying delays, enteric coatings, and colon transit variability create multi-peak or delayed absorption profiles not modeled here. |
| **Pediatric Kinetics** | Strict prohibition on pediatric modeling. | Maturation of CYP enzymes and glomerular filtration in infants is non-allometric; adults-only formulas must NEVER be extrapolated to children. |

---

## 7. G5 Provenance & Educational Verification Status

All 12 compounds in the Orbis Lab drug library (`backend/data/pharma_drugs.yaml`) are calibrated for educational demonstration and relative dynamic range:
- **Validation Status:** `unverified` across all compounds.
- **Retrieved On:** Strictly blank (`""`) per G5 provenance rules.
- **Verification Statement:** Parameters represent game-balanced educational approximations designed to illustrate pharmacological principles (therapeutic window, half-life, renal clearance adjustment, effect delays), NOT verified patient clinical guidelines or FDA package insert references. Real-world dosing must be determined by qualified healthcare clinicians.
