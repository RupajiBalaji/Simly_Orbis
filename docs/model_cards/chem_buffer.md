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

### 2.4 Buffer System Constants & G5 Provenance Table
All thermodynamic dissociation constants are specified at standard reference temperature $25^\circ\text{C}$ (298.15 K) under Governance Rule G5 / R5:

| System ID | Conjugate Pair | $\text{p}K_a$ (at $25^\circ\text{C}$) | Optimal Buffer Range | Provenance Label | `retrieved_on` | Physical Caveats & Limitations |
|:---|:---|:---:|:---:|:---|:---:|:---|
| `acetate` | Acetic acid / Sodium acetate | 4.76 | 3.76 – 5.76 | game-balanced approximate, not label or literature data, human verification needed | *blank* | Carboxylate buffer; slight temperature dependence ($\approx -0.0002\text{ K}^{-1}$). |
| `phosphate` | $\text{H}_2\text{PO}_4^- / \text{HPO}_4^{2-}$ | 7.20 | 6.20 – 8.20 | game-balanced approximate, not label or literature data, human verification needed | *blank* | Second dissociation step $K_{a2}$; moderate ionic strength dependence. |
| `bicarbonate` | $\text{H}_2\text{CO}_3 / \text{HCO}_3^-$ | 6.35 | 5.35 – 7.35 | game-balanced approximate, not label or literature data, human verification needed | *blank* | **Modeled strictly as a closed system with no atmospheric $\text{CO}_2$ gas exchange.** Open-air $\text{CO}_2$ stripping is neglected. |
| `tris` | Tris base / Tris-HCl | 8.06 | 7.06 – 9.06 | game-balanced approximate, not label or literature data, human verification needed | *blank* | **$\text{p}K_a$ exhibits strong temperature dependence ($d\text{p}K_a/dT \approx -0.028\text{ K}^{-1}$); $\text{p}K_a$ drops by $\approx 0.28$ units from $20^\circ\text{C}$ to $30^\circ\text{C}$.** |
| `formate` | Formic acid / Sodium formate | 3.75 | 2.75 – 4.75 | game-balanced approximate, not label or literature data, human verification needed | *blank* | Low molecular weight carboxylic buffer. |
| `water` | $\text{H}_2\text{O} \rightleftharpoons \text{H}^+ + \text{OH}^-$ ($K_w$) | 14.00 ($1.0\times 10^{-14}$) | N/A | game-balanced approximate, not label or literature data, human verification needed | *blank* | Auto-protolysis product at $25^\circ\text{C}$. |

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
- **Engine Self-Consistency Checks:** The engine's `reality_checks()` output represents **engine self-consistency checks (analytic identities), not validation**. It evaluates analytic electroneutrality charge-balance closure and Van Slyke capacity identity at equimolar $\text{pH} = \text{p}K_a$.
- **Validation File:** `validation/chem_tolerances.yaml` (SHA-256 frozen in `validation/chem_tolerances.sha256`). Notice: `chem_tolerances.yaml` has a frozen hash but contains **no reference rows** from external experimental benchmark datasets.
- **Verified Status:** Strictly `verified_by: "unverified"`, `retrieved_on: ""` per governance rule R3 & R5.
- **Reference Literature:** 
  - Van Slyke DD. *J Biol Chem*. 1922;52(2):525-570.
  - Haynes WM, ed. *CRC Handbook of Chemistry and Physics*. 97th ed. CRC Press; 2016.
  - Atkins & de Paula, *Physical Chemistry*, 10th Ed., Oxford University Press, 2014, Chapter 6. Game-balanced approximate, not label or literature data, human verification needed.

---

## 6. Changelog
- `1.0.0`: Initial release implementing exact charge-balance solver, Van Slyke buffer capacity, acid/base stress simulation, and Buffer Bench integration (Phase P3-T2 & P3-T5).
