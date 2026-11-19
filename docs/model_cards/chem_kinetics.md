# Model Card: chem.kinetics (Reaction Kinetics Engine)

**Engine ID:** `chem.kinetics`  
**Engine Version:** `1.0.0`  
**Status:** Educational Simulation &bull; Unverified  

---

## 1. Purpose & Intended Use
- **Purpose:** Simulates chemical reaction rate processes for 0th, 1st, and 2nd order kinetics, consecutive reactions ($A \to B \to C$), and Arrhenius temperature dependence.
- **Intended Use:** Chemistry laboratory education, teaching rate law determination, half-life behavior, integrated rate equations, linearised kinetic transformations ($[A]$, $\ln[A]$, $1/[A]$ vs $t$), and activation energy.
- **Out-of-Scope Use:** Industrial chemical reactor design, explosive / runaway thermal hazard modeling, or enzyme kinetics with cooperative allosteric binding.

---

## 2. Mathematical Equations
### 2.1 Integrated Rate Laws
- **Zero-Order:** $[A](t) = \max(0, [A]_0 - k_0 t)$, $t_{1/2} = \frac{[A]_0}{2 k_0}$
- **First-Order:** $[A](t) = [A]_0 \exp(-k_1 t)$, $t_{1/2} = \frac{\ln(2)}{k_1}$
- **Second-Order:** $[A](t) = \frac{[A]_0}{1 + k_2 [A]_0 t}$, $t_{1/2} = \frac{1}{k_2 [A]_0}$

### 2.2 Consecutive Kinetics ($A \xrightarrow{k_1} B \xrightarrow{k_2} C$)
$$[A](t) = [A]_0 \exp(-k_1 t)$$
$$[B](t) = [A]_0 \frac{k_1}{k_2 - k_1} \left( \exp(-k_1 t) - \exp(-k_2 t) \right) \quad (k_1 \ne k_2)$$
$$[C](t) = [A]_0 - [A](t) - [B](t)$$

### 2.3 Arrhenius Temperature Dependence
$$k(T) = A \exp\left(-\frac{E_a}{R T}\right), \quad R = 8.314462618\text{ J}/(\text{mol}\cdot\text{K})$$

### 2.4 Reaction Constants & G5 Provenance Table
All kinetic rate constants and activation parameters are specified under Governance Rule G5 / R5:

| Parameter | Symbol | Nominal Value | Unit | Provenance Label | `retrieved_on` | Physical Caveats & Scope |
|:---|:---:|:---:|:---:|:---|:---:|:---|
| First-order rate constant (25 °C) | $k_1$ | 0.05 | $\text{s}^{-1}$ | game-balanced approximate, not label or literature data, human verification needed | *blank* | Model unimolecular decomposition; $t_{1/2} = 13.86\text{ s}$. |
| Activation energy | $E_a$ | 45,000.0 | $\text{J}/\text{mol}$ | game-balanced approximate, not label or literature data, human verification needed | *blank* | Governs temperature acceleration; $45.0\text{ kJ}/\text{mol}$. |
| Arrhenius pre-exponential factor | $A$ | $3.5 \times 10^6$ | $\text{s}^{-1}$ | game-balanced approximate, not label or literature data, human verification needed | *blank* | Frequency factor yielding $k=0.05\text{ s}^{-1}$ at $T=298.15\text{ K}$. |
| Second-order rate constant (25 °C) | $k_2$ | 0.05 | $\text{M}^{-1}\text{s}^{-1}$ | game-balanced approximate, not label or literature data, human verification needed | *blank* | Model bimolecular reaction kinetics. |
| Zero-order rate constant (25 °C) | $k_0$ | 0.01 | $\text{M}\cdot\text{s}^{-1}$ | game-balanced approximate, not label or literature data, human verification needed | *blank* | Surface-saturated or enzyme-saturated pseudo zero-order regime. |
| Universal gas constant | $R$ | 8.314462618 | $\text{J}/(\text{mol}\cdot\text{K})$ | CODATA 2018 standard constant | *blank* | Physical constant. |

---

## 3. Assumptions & Parameter Bounds
- **Assumptions:** Homogeneous well-stirred solution, constant temperature (equilibrated thermostat bath), irreversible reactions, ideal solution behavior.
- **Valid Parameter Bounds:**
  - Initial Concentration $[A]_0$: $0.01$ to $5.0\text{ M}$
  - Temperature ($T$): $10.0^\circ\text{C}$ to $80.0^\circ\text{C}$ ($283.15\text{ K}$ to $353.15\text{ K}$)
  - Activation Energy ($E_a$): $10,000$ to $150,000\text{ J}/\text{mol}$
  - Simulation Duration: $1.0$ to $600.0\text{ s}$

---

## 4. Known Error Sources & Limitations
- Reversible back-reactions are neglected; assumes reaction goes to completion.
- Solvent viscosity changes with temperature are not modeled in diffusion-limited regimes.
- RK4 numerical integration truncation error is bounded by $\mathcal{O}(h^4)$, keeping numerical mass conservation error $< 10^{-12}\text{ M}$.

---

## 5. Validation Status & Provenance
- **Engine Self-Consistency Checks:** The engine's `reality_checks()` output represents **engine self-consistency checks (analytic identities), not validation**. It verifies analytic identities (e.g., $t_{1/2} = \ln(2)/k$, mass conservation, and positive monotonicity under Arrhenius scaling).
- **Validation File:** `validation/chem_tolerances.yaml` (SHA-256 frozen in `validation/chem_tolerances.sha256`). Notice: `chem_tolerances.yaml` has a frozen hash but contains **no reference rows** from external experimental benchmark datasets.
- **Verified Status:** Strictly `verified_by: "unverified"`, `retrieved_on: ""` per governance rule R3 & R5.
- **Reference Literature:** Atkins & de Paula, *Physical Chemistry*, 10th Ed., Oxford University Press, 2014, Chapter 20. Game-balanced approximate, not label or literature data, human verification needed.

---

## 6. Changelog
- `1.0.0`: Initial release implementing closed-form and RK4 kinetics, linear fits, and Kinetics Bench integration (Phase P3-T1 & P3-T4).
