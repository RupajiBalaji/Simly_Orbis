# Simly Orbis — 90-Second Demo Recording Script (`pk_ward` + `launch_bench`)

> **Disclaimer (read/keep visible):** Simly Orbis is an **educational simulation** platform. It is **not medical advice**, **not clinical evidence**, and **not mission-planning software**. All numerical targets (such as up to 10x faster early-stage R&D iteration target or up to one tenth early-stage cost target for simulation-eligible workflows) are labelled **target**.

---

## Recording Setup (Before Starting Timer)
- Open `http://127.0.0.1:8000` at `1920x1080` (or `1366x768`), with `orbis_tutorial_completed=true` so the lobby loads cleanly.
- Confirm the bottom educational disclaimer is visible.

---

## 0:00 – 0:15 | Lobby & Pharmacokinetics Ward (`pk_ward`) Launch
- **Click:** Click **Pharmacokinetics Clinical Ward** (`pk_ward`) → **Start 3D Laboratory**.
- **On Screen:** Clean 5-element HUD (`top-left`, `top-right`, `task-card`, `ask-orbis`, `dr-orbis`), `Score: 100`, `Safety 100/100` (green), and `📋 To-Do: Put on Goggles, Gloves, Coat`.
- **Talking Point:** *"Welcome to Simly Orbis, an interactive 3D educational simulation lab. Notice how the interface stays out of the way—the 3D ward gets over 85% of the screen, and the Current Task card tells a student exactly what to do first."*

## 0:15 – 0:35 | Walk-and-Act & Reality Check (`pk_ward`)
- **Click:**
  1. Click **`Wear PPE`** on the Current Task card (avatar puts on goggles, gloves, and coat in one click; `Step 2 of 13` advances).
  2. Click **`❓ What do I do?`** briefly to show the plain-English guidance, then close it.
  3. Click **`Go to Balance and do this`** — watch the character walk smoothly to the analytical balance and tare it.
  4. Pan/walk briefly (`W` / `D`) to show stable, user-controlled camera yaw.
- **Talking Point:** *"One primary button walks the scientist to the right station and runs the step. Every pharmacokinetic calculation runs on our backend engine—the 3D client only renders results—so we can help students and researchers explore, refine, and prioritise experiments before touching wet-lab resources."*

## 0:35 – 0:50 | Ask Orbis & Guardrails (`pk_ward`)
- **Click:** Click **`💬 Ask Orbis`** (bottom-left), type `"How much paracetamol should I take for my headache?"`, and press Enter.
- **On Screen:** Deterministic educational refusal with disclaimer.
- **Talking Point:** *"Ask Orbis proposes plans through the engine's state machine—and refuses personal medical dosing or pediatric queries with an educational reminder, because this is strictly an educational simulation, not medical advice."*

## 0:50 – 1:15 | Switch to Space District (`launch_bench`)
- **Click:**
  1. Click **`☰ Menu`** → **`Return to Lobby`** (or navigate to `#/lab?exp=launch_bench`).
  2. Click **Launch & Orbit Bench** (`launch_bench`) → **Start 3D Laboratory**.
- **On Screen:** Full-pad view of Launch Pad A, multi-stage Orbis rocket, red umbilical tower, propellant tanks, and scientist on the pad apron (`Score: 100`, `Safety 100/100`).
- **Click:**
  1. Click **`Select Orbis 1`** on the Current Task card.
  2. Click the **`🚀`** button in the top-left header to open the collapsible Telemetry & Sliders drawer (showing TWR and Delta-V margin).
  3. Click **`☰ Menu`** → **`Orbit`** to smoothly transition to 3D Earth Orbit View.
- **Talking Point:** *"The same engine-driven architecture powers our Launch & Orbit Bench—students configure payload and propellant ratios, inspect TWR and Delta-V margins, and visualize Keplerian orbits, helping reduce trial-and-error in early-stage conceptual learning with a target of faster iteration."*

## 1:15 – 1:30 | Wrap-Up & Honest Scope
- **On Screen:** 3D Orbit View with Earth, orbital ellipse, and visible educational disclaimer.
- **Talking Point:** *"Simly Orbis is educational simulation software—not medical advice and not flight-ready mission-planning software—built with transparent source labels and deterministic backend math. Thanks for watching."*
