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
    │   └── scene.js           Three.js WebGLRenderer, OrbitControls, hover raycasting, camera transitions
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
