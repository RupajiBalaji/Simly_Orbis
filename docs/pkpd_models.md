# Pharmacokinetic & Pharmacodynamic Mathematical Models (`pharma.pkpd`)

> **DISCLAIMER: Educational simulation platform. Not medical advice. Not clinical evidence.**
> Simly Orbis is an interactive laboratory learning simulator designed to build scientific intuition. It does not output clinical dosing recommendations for real patients and does not replace animal studies, physical bench trials, or human clinical trials.

This document specifies the mathematical formulations, differential equations, analytical solutions, covariate scaling rules, and explicit assumptions implemented in the `backend/app/pharma/pkpd` simulation engine.

---

## 1. Overview & Scope

The `pharma.pkpd` engine simulates time-concentration profiles and pharmacodynamic effect curves for therapeutic drugs across single- and multiple-dose regimens in adult patients.

### Scope & Constraints
- **Target Population**: Adults aged 18–90 years, body weight 40–150 kg, creatinine clearance ($CrCl$) 15–150 mL/min.
- **Pediatric Exclusion**: Paediatric pharmacokinetics are strictly unsupported and rejected by input validation.
- **Administration Routes**: Oral (first-order absorption), Intravenous (IV) bolus, and Constant-rate IV infusion.
- **Compartmental Topologies**: 1-compartment open model and 2-compartment open mammillary model with first-order linear elimination from the central compartment.

---

## 2. Pharmacokinetic Compartmental Physics

### 2.1 One-Compartment Oral Absorption Model

The classical Bateman open one-compartment model describes a drug absorbed from the gastrointestinal tract into the systemic central volume with first-order absorption rate constant $k_a$ and first-order elimination rate constant $k_{el} = \frac{CL}{V_d}$.

#### Differential Equations
$$\frac{dA_d}{dt} = -k_a \cdot A_d$$
$$\frac{dA_c}{dt} = k_a \cdot A_d - \left(\frac{CL}{V_d}\right) \cdot A_c$$

where $A_d(t)$ is drug amount in the gut absorption depot, $A_c(t)$ is drug amount in the central compartment, and systemic plasma concentration is:
$$C_p(t) = \frac{A_c(t)}{V_d}$$

#### Analytical Single-Dose Solution
$$C_p(t) = \frac{F \cdot \text{Dose} \cdot k_a}{V_d \cdot (k_a - k_{el})} \left(e^{-k_{el} \cdot t} - e^{-k_a \cdot t}\right)$$

where $F$ is systemic bioavailability ($0 < F \le 1$).

#### Key Metric Derivations
- **Time to Peak Concentration ($T_{\max}$)**:
  $$T_{\max} = \frac{\ln(k_a / k_{el})}{k_a - k_{el}}$$
- **Peak Concentration ($C_{\max}$)**:
  $$C_{\max} = C_p(T_{\max})$$
- **Total Area Under the Curve ($\text{AUC}_{0-\infty}$)**:
  $$\text{AUC}_{0-\infty} = \frac{F \cdot \text{Dose}}{CL}$$

---

### 2.2 Two-Compartment Model (IV Bolus & Infusion)

The two-compartment open mammillary model describes disposition between a central compartment ($V_c$) and a peripheral tissue compartment ($V_p$) linked by intercompartmental clearance $Q$.

#### Differential Equations
$$\frac{dA_c}{dt} = R_{inf}(t) - \left(\frac{CL + Q}{V_c}\right) A_c + \left(\frac{Q}{V_p}\right) A_p$$
$$\frac{dA_p}{dt} = \left(\frac{Q}{V_c}\right) A_c - \left(\frac{Q}{V_p}\right) A_p$$

where $R_{inf}(t) = \frac{\text{Dose}}{t_{inf}}$ during an active infusion ($0 \le t \le t_{inf}$) and zero otherwise.

#### Micro-Constants
$$k_{10} = \frac{CL}{V_c}, \quad k_{12} = \frac{Q}{V_c}, \quad k_{21} = \frac{Q}{V_p}$$

#### Hybrid Rate Constants ($\alpha$ and $\beta$)
The roots of the characteristic polynomial determine the rapid distribution rate ($\alpha$) and terminal elimination rate ($\beta$):
$$\alpha + \beta = k_{10} + k_{12} + k_{21}$$
$$\alpha \cdot \beta = k_{10} \cdot k_{21}$$
$$\alpha, \beta = \frac{(k_{10} + k_{12} + k_{21}) \pm \sqrt{(k_{10} + k_{12} + k_{21})^2 - 4 k_{10} k_{21}}}{2}$$
where $\alpha > \beta$.

#### Analytical IV Bolus Solution
$$C_p(t) = A \cdot e^{-\alpha \cdot t} + B \cdot e^{-\beta \cdot t}$$
where coefficients are:
$$A = \frac{\text{Dose}}{V_c} \cdot \frac{\alpha - k_{21}}{\alpha - \beta}, \quad B = \frac{\text{Dose}}{V_c} \cdot \frac{k_{21} - \beta}{\alpha - \beta}$$

#### Terminal Half-Life
$$t_{1/2,\beta} = \frac{\ln(2)}{\beta}$$

---

### 2.3 Multiple-Dose Superposition & Steady-State Accumulation

Under linear pharmacokinetics, multi-dose regimens at fixed dosing interval $\tau$ are simulated via exact analytical linear superposition:
$$C_{p,multi}(t) = \sum_{n=0}^{N-1} C_{p,single}(t - n\tau) \cdot H(t - n\tau)$$
where $H(x)$ is the Heaviside step function.

#### Accumulation Ratio ($R_{accum}$)
At steady state, accumulation for a 1-compartment model is:
$$R_{accum} = \frac{1}{1 - e^{-k_{el} \cdot \tau}}$$

---

## 3. Pharmacodynamic Modeling ($E_{\max}$ Model)

Therapeutic and biomarker responses are modeled using the Hill sigmoidal $E_{\max}$ pharmacodynamic relationship:

$$E(C_p) = E_0 + \frac{E_{\max} \cdot C_p^\gamma}{EC_{50}^\gamma + C_p^\gamma}$$

where:
- $E_0$: Baseline physiological response in the absence of drug.
- $E_{\max}$: Maximum drug-induced effect above baseline.
- $EC_{50}$: Plasma concentration producing 50% of maximum effect.
- $\gamma$: Hill sigmoidicity coefficient ($\gamma = 1.0$ for hyperbolic, $\gamma > 1$ for sigmoidal switches).

---

## 4. Covariate Scaling & Patient Allometry

Patient physiological covariates dynamically modify central clearance and volume of distribution relative to a standard adult ($70\text{ kg}$, age $40\text{ yr}$, $CrCl = 100\text{ mL/min}$).

### 4.1 Allometric Weight Scaling
Allometric scaling reflects physiological scaling laws across body mass:
$$V_{scaled} = V_{ref} \cdot \left(\frac{WT}{70}\right)^{1.0}$$
$$CL_{scaled,allometric} = CL_{ref} \cdot \left(\frac{WT}{70}\right)^{0.75}$$

### 4.2 Renal Function Scaling (Cockcroft-Gault)
Clearance of renally eliminated drugs is adjusted using estimated creatinine clearance ($CrCl$) and the fraction excreted unchanged in urine ($f_e$):
$$CL_{adj} = CL_{scaled} \cdot \left[(1 - f_e) + f_e \cdot \frac{CrCl}{100}\right]$$

### 4.3 Adult Bounds & Guardrails
- **Age**: 18 to 90 years.
- **Weight**: 40 to 150 kg.
- **CrCl**: 15 to 150 mL/min.
- Values outside these bounds are clamped with an educational warning or rejected. Pediatric inputs are explicitly prohibited.

---

## 5. Calibrated Drug Library (v2)

| Drug | Model Topology | Default Route | Reference CL (L/h) | Reference Vc (L) | Target Window (mg/L) | Toxic Cutoff (mg/L) | $f_e$ (Renal fraction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Theophylline** | 1-Compartment | Oral | 2.8 | 35.0 | 10.0 – 20.0 | > 20.0 | 0.10 |
| **Vancomycin** | 2-Compartment | IV Infusion | 4.0 | 25.0 ($V_p = 35$) | 15.0 – 20.0 (trough) | > 25.0 | 0.85 |
| **Gentamicin** | 1-Compartment | IV Infusion / Bolus | 4.5 | 18.0 | 4.0 – 10.0 (peak) | > 12.0 peak / > 2.0 trough | 0.90 |

---

## 6. Numerical Verification & Analytic Integrity

1. **Analytical vs RK4 Equivalence**: Automated tests in `backend/tests/test_pharma_pkpd.py` verify that explicit 4th-order Runge-Kutta numerical integration matches analytical closed-form equations within $< 1.0\%$ relative tolerance across single- and multi-dose regimens.
2. **Deterministic Reproducibility**: Given identical patient covariates and dosing parameters, simulation outputs yield bitwise identical floating-point vectors.
3. **Frozen Baseline Hashes**: SHA-256 reference hashes protect all calibration datasets in `validation/data/` from unrecorded modification.
