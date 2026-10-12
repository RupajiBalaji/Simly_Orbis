/**
 * Automated Camera Rig Acceptance Test Suite (frontend/lab/world/camera_test.js)
 * Tests character follow across 8 laboratory stations measuring:
 * - Free viewport framing (>= 98%)
 * - Max missing duration (<= 300 ms)
 * - Static mesh blocker penetrations (0)
 * - HUD panel occlusions (0)
 * Exposes window.__camTest() in debug mode.
 */

import * as THREE from 'three';

export async function runCameraAcceptanceTest(options = {}) {
  const sceneManager = window.sceneManager;
  const controller = window.characterController;
  if (!sceneManager || !controller || !sceneManager.cameraRig) {
    console.error('Camera test requires sceneManager, characterController, and cameraRig.');
    return { passed: false, error: 'Subsystems not initialized' };
  }

  sceneManager.cameraRig.setMode('follow');
  sceneManager.cameraRig.recenter(true);

  const stations = options.stations || [
    'digital_balance',
    'patient_bed',
    'tube_rack',
    'assay_analyzer',
    'virtual_trial_screen',
    'sink',
    'chemical_waste_bin',
    'reality_check_board',
  ];

  const sampleIntervalMs = options.sampleIntervalMs || 40;
  const manualOrbit = options.manualOrbit || false; // optional 90 degree orbit test
  const results = {
    resolution: `${window.innerWidth}x${window.innerHeight}`,
    startTime: performance.now(),
    totalSamples: 0,
    insideFreeCount: 0,
    outsideFreeCount: 0,
    maxMissingMs: 0,
    currentMissingMs: 0,
    blockerPenetrations: 0,
    hudOcclusions: 0,
    legs: [],
    samples: [],
  };

  console.log(`[CAM_TEST] Starting Camera Rig Acceptance Test (${results.resolution}, ${stations.length} stations)...`);

  // Helper to test if screen (sx, sy) falls under any visible HUD element
  const checkHUDOcclusion = (sx, sy) => {
    const avatar = controller.rig?.root;
    const W = window.innerWidth;
    const H = window.innerHeight;
    const hudSelectors = [
      '.hud-top-bar',
      '#hud-next-step-banner',
      '#hud-protocol-panel',
      '.mentor-body:not(.hidden)',
      '.hud-bottom-dock',
    ];

    for (const sel of hudSelectors) {
      const el = document.querySelector(sel);
      if (!el) continue;
      const style = window.getComputedStyle(el);
      if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') continue;
      const rect = el.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0) {
        if (sx >= rect.left && sx <= rect.right && sy >= rect.top && sy <= rect.bottom) {
          const rig = sceneManager.cameraRig;
          const avStr = avatar ? `(${avatar.position.x.toFixed(2)}, ${avatar.position.y.toFixed(2)}, ${avatar.position.z.toFixed(2)})` : '(null)';
          console.warn(`[CAM_TEST_HUD_HIT] sel=${sel} rect=[${Math.round(rect.left)}, ${Math.round(rect.top)}, ${Math.round(rect.right)}, ${Math.round(rect.bottom)}] pt=(${Math.round(sx)}, ${Math.round(sy)}) avPos=${avStr} camPos=(${sceneManager.camera.position.x.toFixed(2)}, ${sceneManager.camera.position.y.toFixed(2)}, ${sceneManager.camera.position.z.toFixed(2)}) target=(${rig.target.x.toFixed(2)}, ${rig.target.y.toFixed(2)}, ${rig.target.z.toFixed(2)})`);
          return true;
        }
      }
    }
    return false;
  };

  const sampleFrame = (dtMs) => {
    const avatar = controller.rig?.root;
    if (!avatar) return;

    const W = window.innerWidth;
    const H = window.innerHeight;
    const avPos = avatar.position;
    const camPos = sceneManager.camera.position;
    const freeRect = sceneManager.cameraRig.getFreeViewportRect();

    // Projected avatar eye/torso height
    const vLook = new THREE.Vector3(avPos.x, avPos.y + 1.15, avPos.z);
    const ndc = vLook.clone().project(sceneManager.camera);
    const sx = (ndc.x + 1) * 0.5 * W;
    const sy = (-ndc.y + 1) * 0.5 * H;

    const insideFree =
      sx >= freeRect.left &&
      sx <= freeRect.right &&
      sy >= freeRect.top &&
      sy <= freeRect.bottom &&
      ndc.z >= -1 &&
      ndc.z <= 1;

    const inBlocker = sceneManager.cameraRig.isInsideBlocker(camPos);
    const isOccludedByHUD = checkHUDOcclusion(sx, sy);

    if (results.totalSamples < 5) {
      console.warn(`[CAM_SAMPLE_DEBUG] sample=${results.totalSamples} pt=(${Math.round(sx)}, ${Math.round(sy)}) ndcZ=${ndc.z.toFixed(2)} freeRect=[${Math.round(freeRect.left)}, ${Math.round(freeRect.top)}, ${Math.round(freeRect.right)}, ${Math.round(freeRect.bottom)}] inside=${insideFree} mode=${sceneManager.cameraRig.mode}`);
    }

    results.totalSamples++;
    if (insideFree) {
      results.insideFreeCount++;
      results.currentMissingMs = 0;
    } else {
      results.outsideFreeCount++;
      results.currentMissingMs += dtMs;
      if (results.currentMissingMs > results.maxMissingMs) {
        results.maxMissingMs = results.currentMissingMs;
      }
    }

    if (inBlocker) {
      results.blockerPenetrations++;
    }
    if (isOccludedByHUD) {
      results.hudOcclusions++;
    }

    const sample = {
      t: performance.now() - results.startTime,
      avX: avPos.x.toFixed(2),
      avZ: avPos.z.toFixed(2),
      camX: camPos.x.toFixed(2),
      camY: camPos.y.toFixed(2),
      camZ: camPos.z.toFixed(2),
      sx: Math.round(sx),
      sy: Math.round(sy),
      insideFree,
      inBlocker,
      isOccludedByHUD,
    };

    if (options.onSample) options.onSample(sample);
    return sample;
  };

  // Run legs across all stations
  let currentStationIdx = 0;
  for (const stId of stations) {
    currentStationIdx++;
    const app = sceneManager.getApparatus(stId);
    const stationPos = app?.userData?.stationPos || new THREE.Vector3(0, 0, 0);
    const fromName = currentStationIdx === 1 ? 'start' : stations[currentStationIdx - 2];
    const toName = stId;

    const legStartSamples = results.totalSamples;
    const legStartInside = results.insideFreeCount;
    const legStartBlockers = results.blockerPenetrations;
    const legStartHUD = results.hudOcclusions;
    const legStartTime = performance.now();
    let legMaxMissingMs = 0;
    let legCurMissingMs = 0;

    await new Promise((resolve) => {
      let intervalId = null;
      let lastSampleT = performance.now();

      const onArrival = () => {
        if (intervalId) clearInterval(intervalId);
        // Take a final arrival sample
        sampleFrame(performance.now() - lastSampleT);
        resolve();
      };

      // Start locomotion
      controller.moveTo(stationPos, onArrival);

      intervalId = setInterval(() => {
        const now = performance.now();
        const dtMs = now - lastSampleT;
        lastSampleT = now;
        const s = sampleFrame(dtMs);
        if (!s.insideFree) {
          legCurMissingMs += dtMs;
          if (legCurMissingMs > legMaxMissingMs) legMaxMissingMs = legCurMissingMs;
        } else {
          legCurMissingMs = 0;
        }
      }, sampleIntervalMs);

      // Timeout safety (14 seconds max per leg for headless software rasterizer)
      setTimeout(() => {
        if (intervalId) clearInterval(intervalId);
        resolve();
      }, 14000);
    });

    // If manual orbit test was requested on leg 2, apply a 90 degree yaw rotation
    if (manualOrbit && currentStationIdx === 2) {
      const offset = new THREE.Vector3().subVectors(sceneManager.camera.position, sceneManager.controls.target);
      const angle = Math.PI / 2; // 90 deg
      const newX = offset.x * Math.cos(angle) - offset.z * Math.sin(angle);
      const newZ = offset.x * Math.sin(angle) + offset.z * Math.cos(angle);
      sceneManager.camera.position.set(
        sceneManager.controls.target.x + newX,
        sceneManager.camera.position.y,
        sceneManager.controls.target.z + newZ
      );
      sceneManager.controls.update();
      sceneManager.cameraRig.lastUserOrbitTime = performance.now();
    }

    const legSamples = results.totalSamples - legStartSamples;
    const legInside = results.insideFreeCount - legStartInside;
    const legBlockers = results.blockerPenetrations - legStartBlockers;
    const legHUD = results.hudOcclusions - legStartHUD;
    const legDuration = Math.round(performance.now() - legStartTime);
    const legPct = legSamples > 0 ? ((legInside / legSamples) * 100).toFixed(1) : '100.0';

    const legSummary = {
      leg: `${fromName} -> ${toName}`,
      durationMs: legDuration,
      samples: legSamples,
      freeRectPct: `${legPct}%`,
      maxMissingMs: Math.round(legMaxMissingMs),
      blockerViolations: legBlockers,
      hudViolations: legHUD,
    };
    results.legs.push(legSummary);
    if (options.onLegComplete) options.onLegComplete(legSummary);
  }

  // Final summary calculation
  results.totalDurationMs = Math.round(performance.now() - results.startTime);
  results.freeRectPercent = results.totalSamples > 0
    ? parseFloat(((results.insideFreeCount / results.totalSamples) * 100).toFixed(2))
    : 100.0;

  results.passed =
    results.freeRectPercent >= 98.0 &&
    results.maxMissingMs <= 300 &&
    results.blockerPenetrations === 0 &&
    results.hudOcclusions === 0;

  console.log(`[CAM_TEST] Acceptance Test Completed in ${results.totalDurationMs}ms.`);
  console.log(`[CAM_TEST] Free Viewport Framing: ${results.freeRectPercent}% (Target: >=98%)`);
  console.log(`[CAM_TEST] Max Missing Duration: ${Math.round(results.maxMissingMs)}ms (Target: <=300ms)`);
  console.log(`[CAM_TEST] Blocker Penetrations: ${results.blockerPenetrations} (Target: 0)`);
  console.log(`[CAM_TEST] HUD Occlusions: ${results.hudOcclusions} (Target: 0)`);
  console.log(`[CAM_TEST] Result: ${results.passed ? '[PASS]' : '[FAIL]'}`);

  if (console.table) {
    console.table(results.legs);
  }

  window.__lastCamTestResult = results;
  return results;
}

// Expose globally on window
if (typeof window !== 'undefined') {
  window.__camTest = runCameraAcceptanceTest;
}
