# Simly Orbis — Client Rendering Performance Procedure (BLOCKED-HUMAN)

> [!IMPORTANT]
> **Status: BLOCKED-HUMAN.** Real GPU and mobile device FPS/memory measurements cannot be synthesized in headless/software-rendered CI. A human tester must run this procedure on physical hardware and record the observed numbers below.

## 1. Devices Required
1. **Desktop / Laptop (Integrated or Discrete GPU):** Chrome/Edge latest.
2. **Mid-range Mobile Phone (Android/iOS):** Chrome or Safari.

## 2. What to Measure
For both **Oral PK Ward** (`pk_ward`) and **Launch & Orbit Bench** (`launch_bench`):
1. **Initial Load Time (ms):** Time from navigation to first interactive 3D frame (Chrome DevTools → Network / Performance).
2. **Steady-State FPS:** Average and 1%-low FPS over 30 seconds of camera orbit + avatar movement (Chrome DevTools → Rendering → Frame Rendering Stats, or `Performance` recording).
3. **JS Heap Memory (MB):** Peak `performance.memory.usedJSHeapSize` (or DevTools Memory snapshot) after 2 minutes of interaction.
4. **Quality Tier Selected:** Note whether the graphics benchmark selects `HIGH`, `MEDIUM`, or `LOW` on each device.

## 3. Procedure
1. Start the app locally or open the staging URL without headless/software rendering flags.
2. Open DevTools (`F12`) → **Performance** tab, enable **Screenshots** and **Memory**.
3. Start recording, load `/index.html`, enter `pk_ward`, perform 3 protocol actions + orbit camera for 30s, stop recording.
4. Repeat for `launch_bench` and on the mobile device (via USB remote debugging `chrome://inspect`).
5. Record the measured numbers in the table below.

## 4. Results Template (To Be Filled by Human Tester)
| Device / Browser | Scenario | Load (ms) | Avg FPS | 1% Low FPS | Peak JS Heap (MB) | Quality Tier | Date |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Desktop (specify GPU) | `pk_ward` | | | | | | ____-__-__ |
| Desktop (specify GPU) | `launch_bench` | | | | | | ____-__-__ |
| Mobile Phone (specify model) | `pk_ward` | | | | | | ____-__-__ |
| Mobile Phone (specify model) | `launch_bench` | | | | | | ____-__-__ |
