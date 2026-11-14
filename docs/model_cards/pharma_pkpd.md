# Model Card: pharma.pkpd (Two-Compartment PK/PD, Multi-Dose & Covariates)

**Engine ID:** `pharma.pkpd`  
**Engine Version:** `0.4.1-dev`  
**Status:** Educational Simulation &bull; Unverified  

---

## 1. Purpose & Intended Use
- **Purpose:** Simulates multi-compartment disposition kinetics (IV bolus, constant zero-order IV infusion, oral), repetitive multiple-dose accumulation to steady state, Hill pharmacodynamic drug response, and adult covariate scaling.
- **Intended Use:** Advanced pharmacology education, narrow therapeutic window demonstration (Theophylline, Digoxin, Vancomycin, Gentamicin, Warfarin), and renal dosage titration.
- **Out-of-Scope Use:** Real patient dosing calculations, paediatric medicine, clinical decision support.

---

## 2. Mathematical Equations
### 2.1 Two-Compartment Biexponential Kinetics (IV Bolus)
$$C(t) = A e^{-\alpha t} + B e^{-\beta t}$$
where hybrid constants $\alpha, \beta$ satisfy $\alpha + \beta = k_{10} + k_{12} + k_{21}$ and $\alpha \beta = k_{10} k_{21}$, with $k_{10} = \frac{CL}{V_1}$, $k_{12} = \frac{Q}{V_1}$, $k_{21} = \frac{Q}{V_2}$.

### 2.2 Constant-Rate IV Infusion ($0 \le t \le T_{\text{inf}}$)
$$C(t) = \frac{R_0}{CL} \left( 1 - e^{-k_{10} t} \right)$$
Post-infusion ($t > T_{\text{inf}}$): $C(t) = C(T_{\text{inf}}) e^{-k_{10} (t - T_{\text{inf}})}$.

### 2.3 Multiple-Dose Superposition
For dose index $k$ at time $\tau_k \le t$:
$$C_{\text{multi}}(t) = \sum_{k=0}^{n-1} C_{\text{single}}(t - k\tau)$$

### 2.4 Pharmacodynamics: Hill $E_{\max}$ Model
$$E(C) = E_0 + \frac{E_{\max} \cdot C^\gamma}{EC_{50}^\gamma + C^\gamma}$$

### 2.5 Adult Covariates & Cockcroft-Gault
$$CL_{\text{scaled}} = CL_{\text{pop}} \cdot \left(\frac{\text{Weight}}{70}\right)^{0.75} \cdot \left[ (1 - f_e) + f_e \cdot \frac{CrCl}{120} \right]$$
where $CrCl = \frac{(140 - \text{Age}) \cdot \text{Weight}}{72 \cdot S_{cr}} \cdot (0.85 \text{ if female})$.

---

## 3. Assumptions & Parameter Ranges
- **Assumptions:** Adult-only physiology, linear distribution and elimination, instantaneous equilibrium between plasma and biophase effect compartment.
- **Valid Parameter Bounds:**
  - Age: $18$ to $90\text{ years}$ (pediatric queries rejected)
  - Weight: $40$ to $150\text{ kg}$
  - $CrCl$: $15$ to $150\text{ mL/min}$
  - Hill Coefficient ($\gamma$): $0.5$ to $5.0$

---

## 4. Known Error Sources & Limitations
- Assumes Cockcroft-Gault equation holds without actual body weight / ideal body weight correction for extreme BMI.
- Direct effect model only; does not simulate indirect response turnover or receptor hysteresis.

---

## 5. Validation Status & Provenance
- **Validation Status:** Analytical checks pass; reference profiles in `validation/data/pkpd_references.csv` unverified.
- **Tolerances:** $\pm 20\%$ for analytical identities, $\pm 30\%$ for hold-out drug profiles per `validation/pkpd_tolerances.yaml`.

---

## 6. Changelog
- `0.4.0-dev`: Initial two-compartment, infusion, superposition, Hill PD, Nelder-Mead calibration framework.
- `0.4.1-dev`: Formal Model Card documentation under `docs/model_cards/`.
