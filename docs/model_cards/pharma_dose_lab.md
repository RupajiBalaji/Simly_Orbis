# Model Card: pharma.dose_lab (Interactive Clinical Dose Lab & Regimen Overlay)

**Engine ID:** `pharma.dose_lab`  
**Engine Version:** `0.7.0-dev`  
**Status:** Educational Simulation &bull; Unverified  

---

## 1. Purpose & Intended Use
- **Purpose:** Interactive pharmacokinetic dosing workbench that overlays multi-dose concentration-time curves against compound-specific therapeutic target windows ($C_{\text{target,low}}$ to $C_{\text{target,high}}$) and toxicity thresholds ($C_{\text{toxic}}$).
- **Intended Use:** Teaching therapeutic index, steady-state accumulation, peak-to-trough fluctuations, renal clearance adjustments, and multi-regimen comparison in STEM and clinical pharmacology curricula.
- **Out-of-Scope Use:** Patient dosing calculations, bedside medical prescription, paediatric treatment planning, or hospital therapeutic drug monitoring.

---

## 2. Mathematical Equations
For multiple oral doses of amount $D$ administered at interval $\tau$:
$$C(t) = \frac{D \cdot F \cdot k_a}{V_d (k_a - k_e)} \sum_{k=0}^{n-1} \left( e^{-k_e (t - k\tau)} - e^{-k_a (t - k\tau)} \right) \cdot H(t - k\tau)$$
where $H(u)$ is the Heaviside step function.

Patient covariate adjustments:
- Clearance scaled allometrically by $(W/70)^{0.75}$ and renal fraction Cockcroft-Gault adjustment.
- Steady-state accumulation ratio:
  $$R_{\text{ac}} = \frac{1}{1 - e^{-k_e \tau}}$$
- Time to steady state ($\approx 95\%$):
  $$t_{\text{ss}} \approx 4.3 \times t_{1/2}$$

Target Window Compliance Metrics:
- Time within therapeutic window: $T_{\text{therapeutic}} = \int_0^T \mathbb{I}(C_{\text{target,low}} \le C(t) \le C_{\text{target,high}}) dt$.
- Time above toxic threshold: $T_{\text{toxic}} = \int_0^T \mathbb{I}(C(t) > C_{\text{toxic}}) dt$.

---

## 3. Assumptions & Parameter Ranges
- **Assumptions:** Linear first-order elimination and absorption kinetics; constant physiological volume and clearance during the simulation window.
- **Adult Covariates:**
  - Age: $18$ to $90$ years
  - Weight: $40$ to $150\text{ kg}$
  - Creatinine Clearance: $15$ to $150\text{ mL/min}$
- **Regimen Bounds:**
  - Dose: $1\text{ mg}$ to $5000\text{ mg}$
  - Interval ($\tau$): $4\text{ h}$ to $48\text{ h}$
  - Number of doses: $1$ to $20$

---

## 4. Known Error Sources & Limitations
- Assumes constant compliance with exact dosing intervals (no missed or delayed doses).
- Does not model active metabolites or organ pathology beyond renal clearance reduction.
- Strictly unverified for human patient dosing.

---

## 5. Validation Status & Provenance
- **Validation Status:** Unverified (awaiting human expert clinical review).
- **Provenance:** G5 game-balanced educational approximations with blank `retrieved_on`.

---

## 6. Changelog
- `0.7.0-dev`: Initial interactive Dose Lab with debounced reactive backend recalculation, multi-regimen overlay, and renal adjustment controls.
