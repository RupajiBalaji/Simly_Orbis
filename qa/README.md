# Simly Orbis QA Test Harness (`qa/`)

Developer-only end-to-end automated testing and visual proof harness for Simly Orbis.

---

## 1. Quick Start

Run the full end-to-end playthrough suite with one command:

```bash
python qa/run.py
```

### CLI Options
- `--headful`: Launch a visible Chromium browser window instead of headless mode.
- `--port <PORT>`: Bind the local FastAPI backend to a specific port (defaults to a dynamic free port).
- `--ci`: CI execution mode (reports FPS metrics without performance gating).

---

## 2. Prerequisites

1. Python 3.11+
2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   pip install playwright
   python -m playwright install chromium
   ```

---

## 3. What the QA Harness Executes

1. **Server Lifecycle**: Finds a free TCP port, launches `uvicorn app.main:app` in-memory with pure reproducible state, and polls health until ready.
2. **Lobby Inspection**: Opens the World Hub, verifies district cards, captures `lobby.png`.
3. **Pharmacokinetics Ward (`pk_ward`)**:
   - Opens experiment brief modal -> captures `pk_ward_brief.png`.
   - Launches 3D laboratory, initializes WebGL scene -> captures `pk_ward_first_view.png`.
   - Character walks between stations -> captures `pk_ward_mid_walk.png`.
   - Executes 5 clinical protocol actions:
     - Tare & Weigh 500 mg paracetamol (`pk_ward_action_1_weigh.png`)
     - Dissolve in water solvent (`pk_ward_action_2_dissolve.png`)
     - Label cup and administer oral dose to patient Alex (`pk_ward_action_3_administer.png`)
     - Advance ward clock 1.0 h and draw blood sample (`pk_ward_action_4_blood.png`)
     - Run plasma assay on centrifuge (`pk_ward_action_5_assay.png`)
   - Completes waste disposal and hand washing, submits final report -> captures `pk_ward_report.png` and verifies assigned letter grade.
4. **Titration Bench (`titration_bench`)**:
   - Returns to lobby and opens chemistry brief -> captures `titration_brief.png`.
   - Launches 3D bench laboratory -> captures `titration_first_view.png`.
   - Character walks to burette station -> captures `titration_mid_walk.png`.
   - Executes 5 titration protocol actions:
     - Rinse burette with NaOH titrant (`titration_action_1_rinse.png`)
     - Fill burette to 50 mL and pipette 25 mL HCl analyte (`titration_action_2_pipette.png`)
     - Add phenolphthalein indicator drops (`titration_action_3_indicator.png`)
     - Dispense 20 mL titrant pre-equivalence (`titration_action_4_titrate.png`)
     - Swirl flask and reach sharp color-transition endpoint (`titration_action_5_endpoint.png`)
   - Submits final chemistry report -> captures `titration_report.png` and verifies assigned letter grade.
5. **Acceptance Camera Rig Framing (`__camTest`)**:
   - Runs automated camera rig acceptance suite across all apparatus stations.
   - Measures free viewport framing percentage (&ge; 98.0%), maximum missing duration (&le; 300 ms), static blocker penetrations (0), and HUD panel occlusions (0).
6. **Telemetry Sampling (`__stats`)**:
   - Samples instantaneous WebGL render loop FPS and draw calls.
   - Measures min, median, average, and maximum frame rates.

---

## 4. Failure Invariants (Strict Gating)

The QA harness exits with code 1 upon any of the following failure conditions:
- **Console Errors**: Any unhandled JavaScript error on `window` or `console.error`.
- **Network Failures**: Any HTTP response with status code &ge; 400.
- **Blank / Uniform Image**: Any checkpoint screenshot with pixel intensity standard deviation below 5.0.
- **Duplicate Screenshot Collision**: Any two checkpoint screenshots sharing an identical MD5 checksum.
- **Camera Rig Failure**: Avatar outside free viewport rectangle or `__camTest` failure.
- **Ungraded Report**: Final clinical or chemistry laboratory report submitted without a letter grade.

---

## 5. Output Artifacts (`qa/out/<timestamp>/`)

Each run writes to an isolated timestamped directory:
- `playthrough.webm`: Full video recording of the browser session.
- `*.png`: 17 distinct named checkpoint screenshots.
- `report.json`: Machine-readable audit payload with timing, metrics, and MD5 hashes.
- `report.md`: Markdown summary table including checkpoint filenames, hashes, and FPS metrics.
