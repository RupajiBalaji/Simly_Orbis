# Model Card: chem.buffer (Aqueous Buffer Equilibrium & Capacity)

**Engine ID:** `chem.buffer`  
**Engine Version:** `1.0.0`  
**Status:** Educational Simulation &bull; Unverified  

---

## 1. Purpose & Intended Use
- **Purpose:** Solves exact aqueous electroneutrality charge balance for weak acid / conjugate base buffer pairs, calculates differential Van Slyke buffer capacity $\beta(\text{pH})$, and simulates strong acid ($HCl$) and strong base ($NaOH$) stress titration curves.
- **Intended Use:** Chemistry laboratory education, teaching buffer design, target pH formulation, Henderson-Hasselbalch limitations, and buffer exhaustion thresholds.
- **Out-of-Scope Use:** Industrial bioprocess pH control, parenteral formulation design, blood gas clinical diagnostic calculations, or polyprotic ampholyte mixtures.

---

## 2. Mathematical Equations
### 2.1 Exact Charge Balance Solver
$$[H^+] + [Na^+]_{\text{total}} = [OH^-] + [A^-] + [Cl^-]$$
where:
$$[OH^-] = \frac{K_w}{[H^+]}, \quad [A^-] = C_{\text{total}} \frac{K_a}{[H^+] + K_a}$$
Solved via Brent's method with tolerance $\epsilon < 10^{-12}\text{ M}$.

### 2.2 Van Slyke Buffer Capacity ($\beta$)
$$\beta = \ln(10) \left( [H^+] + [OH^-] + C_{\text{total}} \frac{K_a [H^+]}{([H^+] + K_a)^2} \right)$$
Maximum buffer capacity at $\text{pH} = \text{p}K_a$:
$$\beta_{\max} = \ln(10) \left( 2\sqrt{K_w} + \frac{C_{\text{total}}}{4} \right)$$

### 2.3 Henderson-Hasselbalch Formula (Educational Reference)
$$\text{pH} = \text{p}K_a + \log_{10}\left(\frac{[A^-]}{[HA]}\right)$$

---

## 3. Assumptions & Parameter Bounds
- **Assumptions:** Ideal aqueous solution ($\gamma_i = 1.0$), monoprotic weak acid model, constant temperature $25^\circ\text{C}$ ($K_w = 1.0 \times 10^{-14}$).
- **Valid Parameter Bounds:**
  - Weak Acid $\text{p}K_a$: $1.0$ to $14.0$
  - Acid Concentration $[HA]$: $0.0001$ to $5.0\text{ M}$
  - Conjugate Base Concentration $[A^-]$: $0.0001$ to $5.0\text{ M}$
  - Buffer Volume: $10.0$ to $1000.0\text{ mL}$
  - Stress Titrant Concentration: $0.01$ to $5.0\text{ M}$

---

## 4. Known Error Sources & Limitations
- Neglects Debye-Hückel ionic activity coefficients; deviation is $\approx 0.05\text{ pH}$ units at ionic strength $I = 0.1\text{ M}$.
- Polyprotic dissociation equilibria (e.g., full 3-step phosphate) are simplified to single dominant conjugate pair transitions.
- Atmospheric carbon dioxide absorption / carbonic acid buffer buffering is not modeled.

---

## 5. Validation Status & Provenance
- **Validation File:** `validation/chem_tolerances.yaml` (SHA-256 frozen in `validation/chem_tolerances.sha256`).
- **Verified Status:** `verified_by: "unverified"`, `retrieved_on: ""` per governance rule R3 & R5.
- **Reference Literature:** 
  - Van Slyke DD. *J Biol Chem*. 1922;52(2):525-570.
  - Haynes WM, ed. *CRC Handbook of Chemistry and Physics*. 97th ed. CRC Press; 2016.
  - Atkins & de Paula, *Physical Chemistry*, 10th Ed., Oxford University Press, 2014, Chapter 6. Game-balanced approximate, human verification needed.

---

## 6. Changelog
- `1.0.0`: Initial release implementing exact charge-balance solver, Van Slyke buffer capacity, acid/base stress simulation, and Buffer Bench integration (Phase P3-T2 & P3-T5).
