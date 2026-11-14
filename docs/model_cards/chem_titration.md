# Model Card: chem.titration (Acid-Base Neutralization & Buffer Dynamics)

**Engine ID:** `chem.titration`  
**Engine Version:** `0.4.1-dev`  
**Status:** Educational Simulation &bull; Unverified  

---

## 1. Purpose & Intended Use
- **Purpose:** Simulates pH curves for strong acid - strong base and weak acid - strong base titrations using mass-action equilibria and charge balance.
- **Intended Use:** Chemistry laboratory education, teaching titration stoichiometry, equivalence point determination, and indicator color transitions (Phenolphthalein).
- **Out-of-Scope Use:** Industrial chemical engineering, hazardous material process design, or multi-protic poly-ampholyte equilibria.

---

## 2. Mathematical Equations
### 2.1 Strong Acid - Strong Base ($HCl + NaOH$)
Before equivalence point ($V_b < V_{eq} = \frac{C_a V_a}{C_b}$):
$$[\text{H}^+] = \frac{C_a V_a - C_b V_b}{V_a + V_b}, \quad \text{pH} = -\log_{10}[\text{H}^+]$$
At equivalence point ($V_b = V_{eq}$):
$$[\text{H}^+] = \sqrt{K_w} = 1.0 \times 10^{-7}\text{ M}, \quad \text{pH} = 7.00$$
Past equivalence point ($V_b > V_{eq}$):
$$[\text{OH}^-] = \frac{C_b V_b - C_a V_a}{V_a + V_b}, \quad \text{pH} = 14.00 + \log_{10}[\text{OH}^-]$$

### 2.2 Weak Acid - Strong Base ($CH_3COOH + NaOH$)
Buffer region ($0 < V_b < V_{eq}$):
$$\text{pH} = pK_a + \log_{10}\left( \frac{C_b V_b}{C_a V_a - C_b V_b} \right)$$
At equivalence point ($V_b = V_{eq}$):
$$\text{pH} = \frac{1}{2}\left( pK_w + pK_a + \log_{10} C_{\text{salt}} \right), \quad C_{\text{salt}} = \frac{C_a V_a}{V_a + V_{eq}}$$

---

## 3. Assumptions & Parameter Ranges
- **Assumptions:** Ideal aqueous solutions, activity coefficients $\gamma_i = 1.0$ (infinite dilution limit), constant temperature $25^\circ\text{C}$ ($K_w = 1.0 \times 10^{-14}$).
- **Valid Parameter Bounds:**
  - Acid Volume ($V_a$): $1.0$ to $100.0\text{ mL}$
  - Analyte Concentration ($C_a$): $0.001$ to $2.0\text{ M}$
  - Titrant Concentration ($C_b$): $0.001$ to $2.0\text{ M}$
  - Acid $pK_a$: $1.0$ to $12.0$

---

## 4. Known Error Sources & Limitations
- Neglects Debye-Hückel ionic strength activity corrections at high salt concentrations ($I > 0.1\text{ M}$).
- Single-step equilibrium only; does not simulate carbonate absorption or polyprotic titration curves.

---

## 5. Validation Status & Provenance
- **Validation Status:** Unverified benchmark rows in `validation/data/chem_titration_references.csv` (8 rows).
- **Tolerances:** $\pm 5\%$ for mass conservation, $\pm 0.1\text{ pH}$ unit per `validation/tolerances.yaml`.

---

## 6. Changelog
- `0.2.0-dev`: Initial Henderson-Hasselbalch engine and 5-step lab playthrough.
- `0.4.1-dev`: Model card formalized per MVP Specification Section 14.4.
