# Model Card: space.orbit (Orbital Mechanics & Rocket Staging)

**Engine ID:** `space.orbit`  
**Engine Version:** `0.4.1-dev`  
**Status:** Educational Simulation &bull; Unverified  

---

## 1. Purpose & Intended Use
- **Purpose:** Simulates multi-stage rocket delta-v budgets, liftoff thrust-to-weight ratios, Keplerian two-body circular orbits, and Hohmann coplanar transfer orbits.
- **Intended Use:** Aerospace STEM education, interactive orbital mechanics demonstration, teaching Tsiolkovsky rocket equation, and orbital velocity transitions.
- **Out-of-Scope Use:** Real-world mission planning, flight trajectory integration, atmospheric reentry simulation, or satellite guidance software.

---

## 2. Mathematical Equations
### 2.1 Tsiolkovsky Rocket Equation
For single-stage or stacked stage $i$:
$$\Delta v_i = I_{sp,i} \cdot g_0 \cdot \ln\left( \frac{m_{0,i}}{m_{f,i}} \right)$$
where $g_0 = 9.80665\text{ m/s}^2$. Total $\Delta v = \sum_i \Delta v_i$.

### 2.2 Keplerian Two-Body Orbital Mechanics
For circular orbit at radius $r = R_E + h$:
$$v_{\text{circ}} = \sqrt{\frac{\mu}{r}}, \quad T = 2\pi \sqrt{\frac{r^3}{\mu}}$$
where Earth gravitational parameter $\mu = 3.986004418 \times 10^{14}\text{ m}^3/\text{s}^2$ and $R_E = 6371\text{ km}$ (WGS-84 volumetric mean).

### 2.3 Coplanar Hohmann Transfer ($r_1 \to r_2$)
Transfer semi-major axis: $a_{\text{tx}} = \frac{r_1 + r_2}{2}$.
$$\Delta v_1 = \sqrt{\mu} \left( \sqrt{\frac{2}{r_1} - \frac{1}{a_{\text{tx}}}} - \frac{1}{\sqrt{r_1}} \right)$$
$$\Delta v_2 = \sqrt{\mu} \left( \frac{1}{\sqrt{r_2}} - \sqrt{\frac{2}{r_2} - \frac{1}{a_{\text{tx}}}} \right)$$
$$\Delta v_{\text{total}} = |\Delta v_1| + |\Delta v_2|, \quad t_{\text{transfer}} = \pi \sqrt{\frac{a_{\text{tx}}^3}{\mu}}$$

---

## 3. Assumptions & Parameter Ranges
- **Assumptions:** Spherical Earth point mass, unperturbed Keplerian two-body orbits ($J_2 = 0$), impulsive velocity changes (instantaneous burns), game-balanced atmospheric/gravity ascent loss parameter ($1500\text{ m/s}$).
- **Valid Parameter Bounds:**
  - Altitude ($h$): $100\text{ km}$ to $100000\text{ km}$
  - Liftoff TWR: $> 1.0$ required
  - Specific impulse ($I_{sp}$): $150\text{ s}$ to $500\text{ s}$

---

## 4. Known Error Sources & Limitations
- Ascent losses are simplified via a single configurable parameter rather than dynamic atmospheric drag integration.
- Does not simulate orbital inclination changes, third-body lunar perturbations, or solar radiation pressure.

---

## 5. Validation Status & Provenance
- **Validation Status:** Analytical checks pass; 5 benchmark references in `validation/data/space_orbit_references.csv` unverified.
- **Tolerances:** $\pm 1\%$ for orbital speed, period, and transfer delta-v per `validation/space_tolerances.yaml`.

---

## 6. Changelog
- `0.3.0-dev`: Initial orbital mechanics and staging engine.
- `0.4.1-dev`: Model card formalized per MVP Specification Section 14.4.
