# Orbis Lab 3D Frontend Architecture

This document describes the 3D client architecture for **Orbis Lab**, built with vanilla JavaScript, modern Three.js ES modules, and procedural asset synthesis.

---

## 🏛️ System Architecture

```
frontend/
├── index.html                 Main application shell (District Lobby, 3D Canvas, HUD, Report)
├── classic.html               Preserved classic 2D PK game
├── lab-console.html           Developer testing console
├── lab.css                    Dark purple UI design system, glassmorphic HUD, action modals
├── vendor/
│   ├── three.module.js        Pinned Three.js ES module (r160)
│   └── addons/
│       └── OrbitControls.js   OrbitControls addon with mouse and touch support
└── lab/
    ├── main.js                Application bootstrapper, WebGL detection, screen transitions
    ├── state.js               Reactive state store (session, experiment, selected target, locks)
    ├── api.js                 REST API client interacting with FastAPI backend
    ├── world/
    │   ├── room.js            Procedural 3D laboratory architecture, benches, lighting, safety fixtures
    │   ├── apparatus.js       Procedural apparatus builders mapped to backend apparatus IDs
    │   ├── scene.js           Three.js WebGLRenderer, OrbitControls, hover raycasting, camera transitions
    │   ├── camera_rig.js      Third-person continuous follow rig, collision resolver, relative action poses
    │   └── camera_test.js     Automated camera acceptance test suite (window.__camTest)
    ├── character/
    │   ├── avatar.js          Procedural humanoid rig with joints and dynamic PPE accessories
    │   ├── ik.js              Two-bone analytical inverse kinematics for reaching apparatus
    │   ├── animation.js       Procedural animation library (idle, walk, gestures, eye blinking)
    │   └── controller.js      Waypoint locomotion, station alignment, and carried objects
    ├── render/
    │   ├── liquid.js          Volumetric liquid height and continuous hex color tweening
    │   ├── effects.js         Particle systems (splash, bubbles, smoke, sparks) and red alarm strobe
    │   ├── readouts.js        Dynamic canvas textures (balance, pH meter, analyzer, bedside vitals monitor)
    │   └── directive_queue.js Sequential directive executor coordinating avatar and physical updates
    ├── game/
    │   ├── hud.js             Protocol checklist, PPE pills, running safety score, real-time event log
    │   ├── action_menu.js     Context-aware action buttons with parameter modals (volume, substance)
    │   ├── toast.js           Pedagogical safety violation toasts with educational explanations
    │   └── report.js          Post-session scorecard (Safety, Accuracy, Technique, Protocol) and leaderboard
    └── demo/
        ├── director.js        Hands-free automated demo runner ('D' key) and intentional mistake demo
        └── debug_overlay.js   F3 performance overlay (FPS, draw calls, active directives, last action)
```

---

## 🧩 How to Add a New Experiment Scene in 5 Steps

Adding a new interactive 3D laboratory experiment (e.g. `space_dock` or `chromatography_bench`) takes 5 straightforward steps:

### 1. Define the Experiment on the Backend
In `backend/app/lab/experiments/`, create your experiment definition:
```python
from app.lab.experiments.base import ExperimentDefinition

my_experiment = ExperimentDefinition(
    id="chromatography_bench",
    title="Thin-Layer Chromatography",
    district="chemistry",
    description="Separate plant pigments using silica plates and solvent chamber.",
    apparatus=[
        {"id": "chamber", "name": "Developing Chamber", "type": "chamber"},
        {"id": "silica_plate", "name": "TLC Plate", "type": "plate"},
    ],
    ...
)
```

### 2. Build Procedural 3D Apparatus
In `frontend/lab/world/apparatus.js`, add a builder function for each new apparatus type:
```javascript
function buildChamber(id) {
  const group = new THREE.Group();
  const glassChamber = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.4, 0.15), glassMat);
  group.add(glassChamber);
  return group;
}
```

### 3. Register Station Coordinates
In `frontend/lab/world/apparatus.js`, inside `buildApparatus()`:
```javascript
case 'chamber':
  group = buildChamber(id);
  group.position.set(0, 0.94, -2.0);
  group.userData.stationPos = new THREE.Vector3(0, 0, -1.0); // Character standing spot
  break;
```

### 4. Wire Visual Directives (If New Effects Needed)
If your experiment emits special visual effects, add them to `frontend/lab/render/effects.js` or `frontend/lab/render/readouts.js`. Liquid volumes, readouts, labels, and avatar animations work automatically out-of-the-box.

### 5. Unlock District Door in Lobby
In `frontend/index.html`, remove the `locked` class and add an unlocked card with click handler in `frontend/lab/main.js`. Your new 3D experiment is now fully playable with character navigation and safety enforcement!

---

## 🎥 Third-Person Follow Camera System (`CameraRig`)

The 3D laboratory features a continuous third-person follow camera rig (`frontend/lab/world/camera_rig.js`) designed to keep the player avatar visible and well-framed at all times:

1. **Modes**:
   - `FOLLOW` (default): Continuously tracks the avatar root with frame-rate independent exponential damping ($k \approx 6$, $1 - e^{-k \cdot dt}$).
   - `STATION`: Fixed camera presets for district lobby, trial viewing gallery, or zoomed inspection boards.
   - `FREE`: Unconstrained manual orbit mode (`OrbitControls`). Toggle with key `C` or the top HUD button; recenter with key `R`.

2. **User Orbit Preservation**:
   - Moving the camera rotates around the character seamlessly: when following locomotion, position and target are shifted by the exact same delta ($\vec{P} \leftarrow \vec{P} + \Delta$, $\vec{T} \leftarrow \vec{T} + \Delta$).
   - **Chase Assist**: When moving forward without mouse interaction for >2 seconds, the camera smoothly eases yaw behind the character.

3. **HUD-Aware Unoccluded Framing**:
   - Rather than viewport shearing (`setViewOffset`), `CameraRig` dynamically measures HUD insets (checklist, mentor dock, action bar) and shifts the world look target along the camera's local right and up axes ($m_{\text{pixel}} = 2 D \tan(\theta/2) / H$).
   - Contains a central 40% dead zone to minimize unnecessary micro-jitter during minor head/arm gestures.

4. **Dynamic Collision Resolution**:
   - Obstacles marked with `userData.camBlocker = true` (lab benches, partitions, monitors) form collision bounding boxes.
   - Raycasts from the target to the camera pull the camera forward when sightlines are obstructed, preventing geometry clipping without hardcoded coordinate rectangles.

5. **Relative Action Camera Shots**:
   - During apparatus interactions (Weigh, Titrate, Pipette, Pour, etc.), action shots compute camera angles in the local frame $(R, F, U)$ of the apparatus and avatar facing.
   - If the avatar's torso occludes the apparatus, avatar opacity automatically fades to 40% for the shot.

6. **Acceptance Testing**:
   - Run `window.__camTest()` in the browser or execute `python qa/run.py` to sample positions across multiple viewport resolutions and verify $\ge 98\%$ framing clearance with zero blocker penetrations.

---

## 🎮 Locomotion, Controls & Interaction System

Simly Orbis features game-feel locomotion and interaction mechanics:

1. **Free Locomotion (`CharacterController`)**:
   - **WASD & Arrow Keys**: Character moves freely in world space relative to the current camera heading.
   - **Shift to Sprint**: Accelerates character movement speed from 2.4 m/s (jog) to 4.0 m/s (sprint).
   - **Touch Joystick**: Dedicated on-screen virtual joystick zone for touchscreens and mobile devices.
   - **Click-to-Walk**: Pointer raycasting to the laboratory floor navigates the avatar to the clicked destination with a visual ripple splash.
   - **Slide Collision**: Tests avatar collision radius (0.22m) against apparatus and bench blocker boxes (`min.y <= 0.95m`), sliding along the unblocked axis.
   - **Rhythmic Footsteps**: Synthesized WebAudio footsteps dynamically timed to gait cadence (0.38s walking, 0.26s sprinting).
   - **Action & Plan Lock**: While an action animation or Ask Orbis plan runs, player movement is locked and the Stop button remains active.

2. **Game-Style Proximity & Radial Wheel**:
   - **Proximity Prompt**: Approaching within 1.6m of an apparatus station triggers a floating HUD prompt: `[E] Use <Apparatus>`.
   - **Radial Action Wheel**: Pressing `E` opens a circular radial action menu centered on screen with station-specific actions. Disabled actions are greyed out with the backend's validation reason displayed on hover.
   - **Collapsible Bottom Dock**: The persistent action bar and quick buttons can be minimized/expanded via the toggle button in the bottom dock.

3. **Views & Shortcuts**:
   - **First-Person Hands View (`V`)**: Toggles an over-the-chest hands view displaying only the avatar's arms and held apparatus/props.
   - **Controls Cheat-Sheet (`H`)**: Displays an on-screen keyboard shortcut modal detailing all navigation, camera, and interaction keys.
   - **Director Mode (`Shift+D`)**: Autoplay presentation mode remapped to `Shift+D` to avoid conflicts with WASD movement. Key listeners ignore movement and shortcuts whenever focus is inside text inputs or modals.

---

## 💎 Graphics Quality Tiers & Benchmark

Simly Orbis features three procedural graphics tiers optimized for budget laptop integrated GPUs:

| Tier | FPS Target | Shadows | Outlines | Bloom | Description |
|---|:---:|:---:|:---:|:---:|---|
| **Low** | 60 FPS | Soft Blob Contact Shadows | Disabled | Off | Maximum performance for low-power devices and SwiftShader WebGL |
| **Medium** | 45+ FPS | Dynamic Soft Shadow Maps (PCFSoft) | Inverted-Hull Toon Outlines | Off | Balanced visual fidelity with crisp stylized toon borders |
| **High** | 45+ FPS | Dynamic Soft Shadow Maps (PCFSoft) | Inverted-Hull Toon Outlines | Procedural Bloom | Full post-processed glow on glass, indicators, and readouts |

- **3-Second Initial Benchmark**: On first load, the client samples frame rates for 3 seconds and automatically selects the optimal tier ($\ge 55$ FPS selects High, $\ge 38$ FPS selects Medium, $< 38$ FPS selects Low).
- **Persistence & Manual Override**: The chosen tier is persisted in `localStorage` (`orbis_quality_tier`) and can be manually toggled anytime via the HUD top bar button.

---

## 🧑‍🔬 Procedural Kerbal-Style Character Rig

The avatar rig (`frontend/lab/character/avatar.js`) is constructed entirely procedurally without external 3D mesh assets:

- **Stylized Toon Shading**: Custom `MeshToonMaterial` paired with a 3-tone gradient map (shadow, midtone, highlight) and inverted-hull back-face silhouette outlines.
- **Expressive Facial Features**: Spherical eyes with pupil tracking directed toward the active camera or apparatus, articulated eyebrows, and 4 swappable mouth shapes (`neutral`, `smile`, `oh`, `flinch`).
- **Articulated Hand Rigging**: Five-finger groups that curl inward around held object sockets when gripping apparatus (`setGrip(true)`).
- **Physical Safety Accessories**: Transparent refractive polycarbonate safety goggles (Fresnel physical transmission), full-length lab coat shell, nitrile gloves (recolored dynamically on PPE change), and dark slate safety shoes with white rubber soles.
