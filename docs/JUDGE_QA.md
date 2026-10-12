# Judge Q&A & Technical Deep Dive – Simly Orbis

Fifteen honest, detailed technical answers for hackathon judges, educators, and engineers.

---

### 1. Is this actually real-time 3D or pre-rendered video?
**Answer**: Real-time 3D rendered live in WebGL via Three.js. Every mesh, avatar limb, beaker, and analytical balance is generated procedurally with custom parametric geometries and dynamic canvas materials. It achieves a stable 60 FPS on our test laptop (AMD Ryzen, integrated graphics) with zero external 3D model asset files (.gltf / .obj) to download.

---

### 2. What role does the AI actually play? Does it simulate the physics?
**Answer**: The AI **never** computes or invents physics, chemistry, or pharmacological outcomes. The physical equations (Bateman PK superposition, charge-balance equilibrium acid-base solver) are executed deterministically on the FastAPI backend. The AI (Dr. Orbis, powered by Google Gemini) acts strictly as a pedagogical mentor: explaining *why* equations behave the way they do, diagnosing student mistakes, and answering conceptual questions.

---

### 3. How do you verify the accuracy of the pharmacokinetic simulations?
**Answer**: Our `pharma.pk` engine computes the exact analytical Bateman one-compartment oral absorption model:
$$C(t) = \frac{\text{Dose} \cdot k_a}{V_d \cdot (k_a - k_e)} \cdot (e^{-k_e \cdot t} - e^{-k_a \cdot t})$$
with analytical superposition for multiple doses. We check this against textbook equations and internal consistency; not clinical validation, with 15 dedicated automated invariant tests and our in-game **Reality Check** board.

---

### 4. What happens if 1,000 students hit the application at once?
**Answer**: 
1. **Per-IP Rate Limiting**: An in-memory token-bucket limiter caps requests (120 req/min general, 10 req/min AI, 20/min session creation) returning HTTP 429.
2. **Global Daily AI Cap**: An automated tracker enforces `MENTOR_DAILY_CAP` (default 300 calls/day). Once reached, the mentor gracefully switches to instant deterministic rule-based guidance.
3. **Stateless Simulation**: Vectorized simulations in NumPy finish in <20 ms for 1,000 virtual patients.

---

### 5. Why use procedural geometry instead of downloading GLTF 3D models?
**Answer**: 
- **Zero Asset Downloads**: The procedural frontend loads without external 3D model asset downloads; the free demo server on Render may take up to a minute to wake up.
- **Zero Asset Failures**: No 404s, CORS texture issues, or WebGL shader compile timeouts on external assets.
- **Dynamic State-Driven Materials**: Apparatus meshes directly reflect simulation state (e.g., burette liquid volume drops, indicator turns faint pink, balance LCD updates live).

---

### 6. How is scoring calculated and kept fair?
**Answer**: The scoring engine evaluates four deterministic components (Total 100 points):
- **Safety (40 pts)**: Penalized for missing PPE (lab coat, goggles, gloves) or contamination.
- **Accuracy (30 pts)**: Penalized for dosing or titration volume errors outside ±5% tolerance.
- **Technique (20 pts)**: Evaluates order of operations (e.g., taring balance, adding indicator before titrating).
- **Protocol Adherence (10 pts)**: Completing all mandatory checklist steps.

---

### 7. How does the chemistry titration math work?
**Answer**: The `chem.titration` engine evaluates exact acid-base equilibrium equations:
- Strong acid / strong base: Neutralization stoichiometry with auto-ionization of water ($K_w = 1.0 \times 10^{-14}$).
- Weak acid / strong base: Solves the exact quadratic equilibrium polynomial for $[\text{H}^+]$ across the buffer region, equivalence point ($V_{eq}$), and excess titrant region.
- Phenolphthalein color transition is modeled using the Henderson-Hasselbalch sigmoidal indicator ionization curve centered at $pK_{ind} = 9.3$.

---

### 8. What prevents prompt-injection attacks on Dr. Orbis?
**Answer**:
1. Free-text inputs are strictly sanitized and limited to 200 characters, stripping ASCII control characters.
2. The user query is isolated in a separate `<user_data>` XML container in the LLM prompt.
3. A strict system prompt enforces boundary control: requests attempting to override system rules or inquire about unrelated topics (e.g., politics, coding) are politely rejected.

---

### 9. What audio engine are you using? Does it require third-party libraries?
**Answer**: Zero external audio libraries. We use the browser's native **WebAudio API** to synthesize all sound effects entirely in code:
- Balance tare/weigh: Synthesized sine wave beeps (880 Hz / 1760 Hz).
- Liquid pour/drip: Band-pass filtered white noise burst.
- Success chime: Major triad chord progression ($C_5 - E_5 - G_5$).
- Alarm: Alternating two-tone square wave (440 Hz / 880 Hz).

---

### 10. Does Simly Orbis support mobile devices or touch screens?
**Answer**: The UI uses responsive CSS Grid and Flexbox with touch event bindings for action bars and camera touch-dragging. High-DPI screens are supported with dynamic pixel-ratio capping (max 2.0) to preserve battery life and 60 FPS performance.

---

### 11. How does the Virtual Trial population variation work?
**Answer**: We simulate diverse patient cohorts using log-normal distributions:
- Body weight: Median 70 kg, CV 18%.
- Clearance multiplier: Median 1.0, CV 30%.
- Absorption rate ($k_a$): CV 25%.
- Hepatic impairment subgroup: 10% of cohort receives clearance multiplier $\times 0.6$.
All randomness uses seeded NumPy generators for 100% reproducibility.

---

### 12. What happens during cold starts on Render's free tier?
**Answer**: Free-tier cloud instances sleep after 15 minutes of inactivity. When a student visits, our frontend displays a built-in **Wake-Up Overlay** that polls `/api/ping` with exponential backoff and a 90-second animated progress meter, preventing confusing blank screens.

---

### 13. What database is used, and what happens if it's down?
**Answer**: We use **MongoDB Atlas** with a 30-day TTL index on session documents. If MongoDB credentials are not provided or the cluster is unreachable, the backend automatically falls back to an **in-memory thread-safe storage adapter** and displays an honest yellow banner in the lobby: *"⚠️ Demo storage: scores are not saved."*

---

### 14. What are the plans for multi-compartment pharmacokinetics?
**Answer**: While RC1 features the analytical one-compartment Bateman model, the architecture is designed around an extensible `SimModule` base class. In v0.2, we will integrate a vectorized Runge-Kutta 4th-order (RK4) differential equation solver for 2-compartment and physiological-based pharmacokinetic (PBPK) models.

---

### 15. Is Simly Orbis intended for actual medical or clinical diagnosis?
**Answer**: **Strictly no.** Simly Orbis is an educational simulator designed to teach students laboratory intuition and scientific principles. It prominently displays a medical disclaimer on every screen, report, and export: *"Educational simulation. Not medical advice. Not clinical evidence."*
