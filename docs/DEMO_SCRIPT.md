# Live Presentation Demo Script – Simly Orbis

This guide provides timed presentation scripts for live hackathon demos and lightning talks, along with robust fallback contingency plans.

---

## 3-Minute Timed Script (Hackathon Main Stage)

### 0:00 – 1:00 | Minute 1: The Hook (Physical Consequences in 3D)
- **Visual**: Start in the **PK Ward** (`http://localhost:8000`). Frame the avatar, balance, and patient on the bed.
- **Spoken**:
  > *"Every year, clinical pharmacology students study pharmacokinetics from static two-dimensional textbook curves. But in the real world, an error at the analytical balance or an improper dosing interval lands a patient in severe toxicity. Welcome to **Simly Orbis** — where you play the scientist, not the spectator."*
- **Action**:
  1. Click **Weigh Dose** on the action bar.
  2. Point out the **Action Camera** easing to an over-the-shoulder medium shot framing the avatar's hands, spatula, and weighing cup.
  3. Show the analytical balance LCD display rising in real-time as the powder accumulates.
  4. Administer the dose and watch the pharmacokinetic curve advance in real-time.

---

### 1:00 – 2:00 | Minute 2: The Scale (Virtual Clinical Trial with 500 Patients)
- **Visual**: Walk over to or click the **Virtual Trial wall screen** and enter the viewing gallery.
- **Spoken**:
  > *"Treating one patient gives you a single data point. But in drug development, medications are administered to thousands of diverse humans. With one click, Simly Orbis spawns a 500-patient virtual cohort simulated via vectorized Monte Carlo sampling in under 20 milliseconds."*
- **Action**:
  1. Click **Run Cohort (500 Patients)**.
  2. Watch the **color wave** sweep across the crowd gallery: green for therapeutic, yellow for subtherapeutic, red for toxic.
  3. Click **Compare View**.
  4. Highlight the liver-impaired subgroup:
  > *"Notice how 85% of standard-clearance patients are safely in the green zone, but the reduced-liver cohort experiences nearly 60% toxicity. The student doesn't just calculate this — they SEES the crowd turn red."*

---

### 2:00 – 3:00 | Minute 3: The AI Mentor & Reality Check (Pedagogy & Proof)
- **Visual**: Open the **Dr. Orbis AI Mentor** panel and toggle the **Reality Check Board**.
- **Spoken**:
  > *"To ensure students never get stuck, we have Dr. Orbis — an AI mentor powered by Google Gemini. But unlike generic chatbots that hallucinate numbers, Dr. Orbis never invents physics. The deterministic engine is the single source of truth."*
- **Action**:
  1. Click **Step Hint** or ask: *"Why does Cmax spike early?"*
  2. Show the response badge marked **[AI]** with latency and remaining calls.
  3. Point to the **Reality Check board** on the wall screen:
  > *"How do we prove this simulation is real? Our Reality Check board compares every simulation run against analytical textbook solutions. We run 90+ automated tests on every push."*
  4. Click **Finish Report** to display the comprehensive score, safety compliance breakdown, and certificate.

---

## 60-Second Lightning Talk Version

- **0:00 – 0:15**: *"Simly Orbis transforms medical and chemical education from static textbook curves into an interactive 3D laboratory game running at 60 FPS in any browser."* (Click PK Ward, perform Weigh).
- **0:15 – 0:35**: *"We scale from one patient to an entire clinical trial: watch 500 virtual patients simulated with log-normal pharmacokinetic variance, turning green or red based on liver clearance."* (Trigger 500-patient trial, show crowd color wave).
- **0:35 – 0:50**: *"Our AI lab mentor, Dr. Orbis, explains the pharmacology behind every outcome without ever hallucinating physics, backed by published analytical reality checks."* (Trigger Dr. Orbis Step Hint).
- **0:50 – 1:00**: *"Built on FastAPI, procedural Three.js, and strict deterministic engines. Ready for students today."* (Finish Report).

---

## Backup & Contingency Plan

### 1. If LLM / Network is Slow or Unavailable:
- **Automatic Fallback**: Simly Orbis automatically catches timeouts (>8s) and switches to rule-based hints. The response badge cleanly displays **[Rule-Based]**. Explain:
  > *"Notice our graceful degradation: when offline or during API outages, the system automatically falls back to deterministic rule-based guidance without crashing."*

### 2. If Running on a Device Without High-End WebGL:
- **Toggle Low Quality**: Click **Quality: Low** in the HUD top bar to disable dynamic shadows and antialiasing.
- **2D Data Fallback**: The canvas automatically degrades cleanly, and all 2D charts, protocol readouts, and final reports render regardless of WebGL support.

### 3. Autoplay Director Mode:
- **Press 'D' or Click 'Director'**: If you want hands-free execution while talking, trigger Director mode. The avatar will autonomously execute the entire protocol step-by-step.
