# Model Card: pharma.pk (Single-Compartment Oral & IV Bolus)

**Engine ID:** `pharma.pk`  
**Engine Version:** `0.4.1-dev`  
**Status:** Educational Simulation &bull; Unverified  

---

## 1. Purpose & Intended Use
- **Purpose:** Simulates single-dose concentration-time curves for small molecule drugs following oral or IV bolus administration.
- **Intended Use:** STEM education, interactive pharmacokinetics coursework, and intuitive exploration of absorption ($k_a$), clearance ($CL$), and volume of distribution ($V$).
- **Out-of-Scope Use:** Clinical dosing, patient prescribing, therapeutic drug monitoring, or regulated drug submission.

---

## 2. Mathematical Equations
For a single-compartment model with first-order absorption and elimination:
$$C(t) = \frac{F \cdot \text{Dose} \cdot k_a}{V_1 (k_a - k_e)} \left( e^{-k_e t} - e^{-k_a t} \right)$$
where $k_e = \frac{CL}{V_1}$, $t_{\max} = \frac{\ln(k_a / k_e)}{k_a - k_e}$, and $C_{\max} = C(t_{\max})$.
For IV bolus ($F=1, k_a \to \infty$):
$$C(t) = \frac{\text{Dose}}{V_1} e^{-k_e t}$$

---

## 3. Assumptions & Parameter Ranges
- **Assumptions:** Well-stirred single compartment, linear elimination kinetics (first-order), instantaneous distribution, constant clearance.
- **Valid Adult Parameter Ranges:**
  - Dose: $0.1\text{ mg}$ to $5000\text{ mg}$
  - Clearance ($CL$): $0.1\text{ L/h}$ to $100.0\text{ L/h}$
  - Volume ($V_1$): $1.0\text{ L}$ to $500.0\text{ L}$
  - Absorption rate ($k_a$): $0.05\text{ h}^{-1}$ to $10.0\text{ h}^{-1}$
  - Bioavailability ($F$): $0.0$ to $1.0$

---

## 4. Known Error Sources & Limitations
- Does not account for non-linear saturable metabolism (Michaelis-Menten kinetics).
- Lacks multicompartment tissue distribution kinetics.
- Adult-only parameter space; paediatric extrapolation strictly unsupported.

---

## 5. Validation Status & Provenance
- **Validation Status:** Unverified (awaiting expert verification).
- **Benchmark References:** 14 literature reference rows in `validation/data/pharma_pk_references.csv` (Portolés 2003, Bramlage 2008, Perera 2011, Blanchard 1983).
- **Acceptance Criteria:** Standard bioequivalence 2-fold margin ($0.5 \le \text{predicted}/\text{observed} \le 2.0$) per `validation/tolerances.yaml`.

---

## 6. Changelog
- `0.2.0-dev`: Initial single-compartment oral simulation and visual contract.
- `0.4.0-dev`: Parameter boundary locking and provenance documentation.
- `0.4.1-dev`: Model card standardized per MVP Specification Section 14.4.
