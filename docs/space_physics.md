# Space Flight Physics & Orbital Mechanics Engine

Simly Orbis includes a pure-Python, zero-dependency orbital mechanics and launch trajectory simulator (`backend/app/space/orbit.py`). This document explains the underlying physics, analytical models, numerical propagation, and game-balanced approximations.

---

## 1. Constants & Choice of Primary Body

All orbital calculations reference the WGS-84 / standard gravitational parameter for Earth:

- **Earth Standard Gravitational Parameter ($\mu$):** $3.986004418 \times 10^{14}\text{ m}^3/\text{s}^2$
- **Earth Mean Radius ($R_\oplus$):** $6,371,000\text{ m}$ ($6,371\text{ km}$)
  *Note on choice:* Earth's volumetric mean radius ($6,371\text{ km}$) is chosen rather than the equatorial radius ($6,378\text{ km}$) to maintain spherical symmetry in 2D orbital propagation.
- **Standard Surface Gravity ($g_0$):** $9.80665\text{ m}/\text{s}^2$

---

## 2. Core Equations

### 2.1 Tsiolkovsky Rocket Equation ($\Delta v$)
For any rocket stage with initial mass $m_0$ (including dry mass, propellant, and subsequent stages/payload) and burnout mass $m_f = m_0 - m_{\text{propellant}}$:

$$\Delta v = I_{\text{sp}} \cdot g_0 \cdot \ln\left(\frac{m_0}{m_f}\right)$$

For multi-stage vehicles, total ideal $\Delta v$ is the algebraic sum across all stages:

$$\Delta v_{\text{total}} = \sum_{i=1}^N \Delta v_i$$

### 2.2 Vis-Viva Equation
Orbital velocity $v$ at radius $r = R_\oplus + h$ for an orbit with semi-major axis $a$:

$$v = \sqrt{\mu \left(\frac{2}{r} - \frac{1}{a}\right)}$$

For a circular orbit ($r = a$):

$$v_{\text{circ}} = \sqrt{\frac{\mu}{r}}$$

### 2.3 Kepler's Third Law (Orbital Period)
The period $T$ of an orbit with semi-major axis $a$:

$$T = 2\pi \sqrt{\frac{a^3}{\mu}}$$

### 2.4 Hohmann Transfer Maneuver
For coplanar circular orbits between initial radius $r_1$ and final radius $r_2$:

1. **Transfer Semi-major Axis:**
   $$a_{\text{tx}} = \frac{r_1 + r_2}{2}$$

2. **First Burn (Injection at Periapsis $r_1$):**
   $$\Delta v_1 = \sqrt{\mu \left(\frac{2}{r_1} - \frac{1}{a_{\text{tx}}}\right)} - \sqrt{\frac{\mu}{r_1}}$$

3. **Second Burn (Circularization at Apoapsis $r_2$):**
   $$\Delta v_2 = \sqrt{\frac{\mu}{r_2}} - \sqrt{\mu \left(\frac{2}{r_2} - \frac{1}{a_{\text{tx}}}\right)}$$

4. **Total Hohmann Budget:**
   $$\Delta v_{\text{hohmann}} = |\Delta v_1| + |\Delta v_2|$$

5. **Transfer Time ($t_{\text{tx}}$):**
   $$t_{\text{tx}} = \pi \sqrt{\frac{a_{\text{tx}}^3}{\mu}}$$

---

## 3. Ascent Losses & Mission Evaluation

Launching from Earth's surface into Low Earth Orbit (LEO, 200 km) requires more than the bare orbital velocity ($v_{\text{circ}} \approx 7,788\text{ m/s}$ at mean spherical radius $r = R_\oplus + 200\text{ km} = 6,571\text{ km}$). Gravity drag, atmospheric aerodynamic drag, and steering losses consume propellant:

$$\Delta v_{\text{losses}} = 1,500\text{ m/s}$$
$$\Delta v_{\text{req}} = v_{\text{circ}}(200\text{ km}) + \Delta v_{\text{losses}} \approx 7,788 + 1,500 = 9,288\text{ m/s}$$

### Liftoff Thrust-to-Weight Ratio (TWR)
To safely clear Launch Pad A:

$$\text{TWR} = \frac{F_{\text{thrust}}}{m_0 \cdot g_0}$$

- **$\text{TWR} < 1.0$:** Vehicle cannot lift off; pad engine burn and structure damage.
- **$\text{TWR} < 1.15$:** Excessive gravity losses; pad hold warning.
- **$\text{Nominal TWR}$:** $1.20 - 1.60$.

---

## 4. Numerical Propagation & Conservation

For state trajectory verification, `backend/app/space/orbit.py` implements a 4th-order Runge-Kutta (RK4) 2D gravitational propagator:

$$\ddot{\mathbf{r}} = -\frac{\mu}{|\mathbf{r}|^3} \mathbf{r}$$

### Invariant Checks
1. **Specific Mechanical Energy ($E$):**
   $$E = \frac{v^2}{2} - \frac{\mu}{r}$$
   Conserved to within $|(E_t - E_0) / E_0| \le 1.0 \times 10^{-6}$ over a complete Keplerian orbit.
2. **Specific Angular Momentum ($h$):**
   $$h = |\mathbf{r} \times \mathbf{v}| = x v_y - y v_x$$
   Conserved to within $|(h_t - h_0) / h_0| \le 1.0 \times 10^{-6}$.

---

## 5. Educational Simulation Caveats & Bounds

- **Two-Body Approximation:** Assumes spherical Earth point mass; ignores non-spherical harmonics ($J_2$), third-body gravitational perturbations (Moon, Sun), and solar radiation pressure.
- **Ascent Loss Model:** Uses a lumped analytic loss model ($\Delta v_{\text{loss}} = 1,500\text{ m/s}$) for educational pacing rather than full atmospheric integration with dynamic pressure ($q$) and transonic pitch-over.
- **Target Labeling:** All references are educational simulation targets, not certified flight-readiness mission planners.
