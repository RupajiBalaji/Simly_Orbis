# Simly Orbis Chemistry Physical Models & Numerical Implementations

**Version:** 0.6.0-dev  
**Engines:** `chem.kinetics`, `chem.buffer`  
**Governance:** Educational Simulation &bull; Unverified  

---

## 1. Overview & Architecture

The Simly Orbis Chemistry District provides physical chemistry simulation engines designed to power interactive laboratory benches:
- **`chem.kinetics`**: Reaction kinetics engine supporting 0th, 1st, and 2nd order rate laws, consecutive reactions ($A \xrightarrow{k_1} B \xrightarrow{k_2} C$), Arrhenius temperature dependence $k(T)$, dual analytical and Runge-Kutta 4th-order (RK4) integration, linear regression transformations, and experimental observation generation with seeded Gaussian noise.
- **`chem.buffer`**: Aqueous buffer equilibrium and capacity engine implementing exact charge-balance electroneutrality root-finding, Van Slyke buffer capacity $\beta(\text{pH})$, maximum buffer capacity at $\text{pH} = \text{p}K_a$, and strong acid ($HCl$) and strong base ($NaOH$) stress titration curves.

Both engines adhere to strict governance rules:
- Educational simulation only; not for industrial process safety or clinical/medical advice.
- Deterministic numerical solvers with frozen validation tolerances in `validation/chem_tolerances.yaml`.

---

## 2. Reaction Kinetics Engine (`chem.kinetics`)

### 2.1 Integrated Rate Equations
For a reaction of the form $A \to \text{Products}$:

#### Zero-Order Kinetics ($n = 0$):
$$\frac{d[A]}{dt} = -k_0$$
$$[A](t) = \max\left(0, [A]_0 - k_0 t\right)$$
$$t_{1/2} = \frac{[A]_0}{2 k_0}$$

#### First-Order Kinetics ($n = 1$):
$$\frac{d[A]}{dt} = -k_1 [A]$$
$$[A](t) = [A]_0 \exp(-k_1 t)$$
$$t_{1/2} = \frac{\ln(2)}{k_1} \approx \frac{0.693147}{k_1}$$

#### Second-Order Kinetics ($n = 2$):
$$\frac{d[A]}{dt} = -k_2 [A]^2$$
$$[A](t) = \frac{[A]_0}{1 + k_2 [A]_0 t}$$
$$t_{1/2} = \frac{1}{k_2 [A]_0}$$

### 2.2 Consecutive Reaction Kinetics ($A \xrightarrow{k_1} B \xrightarrow{k_2} C$)
For intermediate species $B$ formation and decay:
$$[A](t) = [A]_0 \exp(-k_1 t)$$
$$[B](t) = \begin{cases} [A]_0 \frac{k_1}{k_2 - k_1} \left( \exp(-k_1 t) - \exp(-k_2 t) \right) & \text{if } k_1 \ne k_2 \\ [A]_0 k_1 t \exp(-k_1 t) & \text{if } k_1 = k_2 \end{cases}$$
$$[C](t) = [A]_0 - [A](t) - [B](t)$$

Peak time $t_{\max}$ and peak concentration $[B]_{\max}$ for $k_1 \ne k_2$:
$$t_{\max} = \frac{\ln(k_1 / k_2)}{k_1 - k_2}$$
$$[B]_{\max} = [A]_0 \left( \frac{k_1}{k_2} \right)^{\frac{k_2}{k_2 - k_1}}$$

### 2.3 Temperature Dependence (Arrhenius Equation)
$$k(T) = A \exp\left(-\frac{E_a}{R T}\right)$$
Two-temperature ratio form:
$$\ln\left(\frac{k_2}{k_1}\right) = \frac{E_a}{R} \left( \frac{1}{T_1} - \frac{1}{T_2} \right)$$
where $R = 8.314462618\text{ J}/(\text{mol}\cdot\text{K})$ (CODATA 2018).

### 2.4 Numerical Integration (RK4)
For general rate forms $\frac{d\mathbf{y}}{dt} = \mathbf{f}(t, \mathbf{y})$:
$$\mathbf{k}_1 = \mathbf{f}(t_n, \mathbf{y}_n)$$
$$\mathbf{k}_2 = \mathbf{f}\left(t_n + \frac{h}{2}, \mathbf{y}_n + \frac{h}{2}\mathbf{k}_1\right)$$
$$\mathbf{k}_3 = \mathbf{f}\left(t_n + \frac{h}{2}, \mathbf{y}_n + \frac{h}{2}\mathbf{k}_2\right)$$
$$\mathbf{k}_4 = \mathbf{f}(t_n + h, \mathbf{y}_n + h\mathbf{k}_3)$$
$$\mathbf{y}_{n+1} = \mathbf{y}_n + \frac{h}{6}(\mathbf{k}_1 + 2\mathbf{k}_2 + 2\mathbf{k}_3 + \mathbf{k}_4)$$
Local truncation error is $\mathcal{O}(h^5)$, global error $\mathcal{O}(h^4)$.

### 2.5 Linearised Transformations & Regression
To identify reaction orders from experimental time-series:
- Order 0: $[A]$ vs $t$, slope $= -k$, intercept $= [A]_0$
- Order 1: $\ln[A]$ vs $t$, slope $= -k$, intercept $= \ln[A]_0$
- Order 2: $1/[A]$ vs $t$, slope $= +k$, intercept $= 1/[A]_0$

Correlation coefficient $R^2$:
$$R^2 = \frac{\left(\sum (x_i - \bar{x})(y_i - \bar{y})\right)^2}{\sum(x_i - \bar{x})^2 \sum(y_i - \bar{y})^2}$$

---

## 3. Aqueous Buffer Equilibrium & Capacity (`chem.buffer`)

### 3.1 Electroneutrality Charge Balance
For a monoprotic weak acid $HA$ and sodium salt $NaA$ with added strong acid ($HCl$) and strong base ($NaOH$):
Mass balance:
$$C_{\text{total}} = [HA] + [A^-]$$
Dissociation equilibrium:
$$K_a = \frac{[H^+][A^-]}{[HA]} \implies [A^-] = C_{\text{total}} \frac{K_a}{[H^+] + K_a}, \quad [HA] = C_{\text{total}} \frac{[H^+]}{[H^+] + K_a}$$
Aqueous charge balance:
$$[H^+] + [Na^+]_{\text{total}} = [OH^-] + [A^-] + [Cl^-]$$
where $[OH^-] = \frac{K_w}{[H^+]}$, $[Na^+]_{\text{total}} = C_{\text{salt}} + C_{NaOH}$, and $[Cl^-] = C_{HCl}$.

Net residual function solved via Brent's / bisection method:
$$F([H^+]) = [H^+] - \frac{K_w}{[H^+]} + [Na^+]_{\text{total}} - [Cl^-] - C_{\text{total}} \frac{K_a}{[H^+] + K_a} = 0$$

### 3.2 Van Slyke Buffer Capacity ($\beta$)
The differential buffer capacity $\beta = \frac{dC_{\text{base}}}{d\text{pH}} = -\frac{dC_{\text{acid}}}{d\text{pH}}$ is derived analytically from electroneutrality:
$$\beta = \ln(10) \left( [H^+] + [OH^-] + C_{\text{total}} \frac{K_a [H^+]}{([H^+] + K_a)^2} \right)$$
Maximum buffer capacity occurs at $[H^+] = K_a$ ($\text{pH} = \text{p}K_a$):
$$\beta_{\max} = \ln(10) \left( 2\sqrt{K_w} + \frac{C_{\text{total}}}{4} \right) \approx 0.5756 \cdot C_{\text{total}}$$

### 3.3 Henderson-Hasselbalch Approximation
$$\text{pH} \approx \text{p}K_a + \log_{10}\left(\frac{[A^-]}{[HA]}\right)$$
Valid only when $[H^+] \ll [HA]$ and $[OH^-] \ll [A^-]$ ($4 < \text{pH} < 10$ and $C > 0.01\text{ M}$). The engine solves exact charge balance and reports Henderson-Hasselbalch discrepancy.

---

## 4. Simplifications & First-Order Error Analysis

| Model Aspect | Simplification Applied | Physical Reality | First-Order Error Bound |
|---|---|---|---|
| Ionic Activity | $\gamma_i = 1.0$ (Ideal dilution) | Extended Debye-Hückel / Davies equation | $\Delta\text{pH} \approx 0.02\text{--}0.08$ at $I = 0.1\text{ M}$ |
| Water Self-Ionization | $K_w = 1.0 \times 10^{-14}$ constant | Temperature-dependent $K_w(T)$ | $< 0.01\text{ pH}$ for $T = 20\text{--}25^\circ\text{C}$ |
| Temperature Effects on $K_a$ | Constant $K_a$ over temperature | van 't Hoff equation $\Delta H^\circ$ | $\approx \pm 0.05\text{ p}K_a$ per $10^\circ\text{C}$ |
| Reversible Kinetics | Irreversible $A \to P$ assumption | Equilibrium back-reaction $P \to A$ | Negligible for $K_{eq} > 10^3$ |
| Numerical Dispersion (RK4) | Fixed step size $h \le 0.05\text{ s}$ | Adaptive step-size embedded RK45 | Local truncation error $< 10^{-10}\text{ M}$ |
