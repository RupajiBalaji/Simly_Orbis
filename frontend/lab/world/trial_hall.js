/**
 * Virtual Trial Hall & 1000-Patient Crowd Arena (frontend/lab/world/trial_hall.js)
 * Constructs the interactive wall screen in pk_ward and the glass observation gallery
 * with an InstancedMesh crowd of up to 1000 capsule-people (ONE draw call).
 */

import * as THREE from 'three';

const COLOR_NEUTRAL = new THREE.Color(0x94a3b8);
const COLOR_HELPED = new THREE.Color(0x10b981);   // Green: in therapeutic range
const COLOR_SUB = new THREE.Color(0xf59e0b);      // Amber: subtherapeutic
const COLOR_TOXIC = new THREE.Color(0xef4444);    // Red: toxic exposure

/**
 * Creates the large interactive wall display screen in pk_ward.
 */
export function createVirtualTrialScreen() {
  const group = new THREE.Group();
  group.name = 'virtual_trial_screen';

  // 1. Sleek metallic casing / bezel (3.2m x 1.8m x 0.08m)
  const bezelMat = new THREE.MeshStandardMaterial({
    color: 0x0f172a,
    roughness: 0.3,
    metalness: 0.8,
  });
  const bezelGeo = new THREE.BoxGeometry(3.2, 1.8, 0.08);
  const bezelMesh = new THREE.Mesh(bezelGeo, bezelMat);
  bezelMesh.castShadow = true;
  group.add(bezelMesh);

  // 2. Cyan glowing frame accent
  const borderMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });
  const borderGeo = new THREE.BoxGeometry(3.24, 1.84, 0.04);
  const borderMesh = new THREE.Mesh(borderGeo, borderMat);
  borderMesh.position.z = -0.01;
  group.add(borderMesh);

  // 3. Screen surface with dynamic 2D canvas texture
  const canvas = document.createElement('canvas');
  canvas.width = 1024;
  canvas.height = 576;
  const ctx = canvas.getContext('2d');

  let lastTrialResults = null;

  function drawScreenGraphic(statusText = 'No trial run yet', resultsData = null) {
    if (resultsData) lastTrialResults = resultsData;
    const currentResults = resultsData || lastTrialResults;

    ctx.fillStyle = '#090d16';
    ctx.fillRect(0, 0, 1024, 576);

    // Glowing subtle grid
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.12)';
    ctx.lineWidth = 1;
    for (let x = 0; x < 1024; x += 48) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, 576);
      ctx.stroke();
    }
    for (let y = 0; y < 576; y += 48) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(1024, y);
      ctx.stroke();
    }

    // Top Header (Shortened & legible)
    ctx.fillStyle = '#38bdf8';
    ctx.font = 'bold 40px "JetBrains Mono", monospace';
    ctx.fillText('⬡ VIRTUAL TRIAL ARENA', 48, 68);

    ctx.fillStyle = '#cbd5e1';
    ctx.font = 'bold 22px Inter, sans-serif';
    ctx.fillText('Cohort Population Simulation • N=20–1000', 48, 104);

    // Center visual: stylized crowd matrix representation
    ctx.fillStyle = '#1e293b';
    ctx.fillRect(48, 130, 490, 320);
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.4)';
    ctx.lineWidth = 2;
    ctx.strokeRect(48, 130, 490, 320);

    // Dot matrix pattern: neutral grey dots until real trial run completes
    const outcomes = currentResults?.outcomes || null;
    let dotIdx = 0;

    for (let r = 0; r < 14; r++) {
      for (let c = 0; c < 24; c++) {
        const dotX = 68 + c * 19.5;
        const dotY = 152 + r * 19.5;

        if (outcomes && dotIdx < outcomes.length) {
          const outcome = outcomes[dotIdx];
          ctx.fillStyle = outcome === 1 ? '#10b981' : outcome === 2 ? '#ef4444' : '#f59e0b';
        } else if (outcomes) {
          ctx.fillStyle = '#64748b';
        } else {
          // Neutral grey dots when no trial run yet
          ctx.fillStyle = '#64748b';
        }
        dotIdx++;

        ctx.beginPath();
        ctx.arc(dotX, dotY, 4.5, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // Center badge if no trial run yet
    if (!currentResults) {
      ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
      ctx.fillRect(150, 260, 280, 50);
      ctx.strokeStyle = 'rgba(148, 163, 184, 0.5)';
      ctx.lineWidth = 1.5;
      ctx.strokeRect(150, 260, 280, 50);
      ctx.fillStyle = '#94a3b8';
      ctx.font = 'bold 20px "JetBrains Mono", monospace';
      ctx.textAlign = 'center';
      ctx.fillText('No trial run yet', 290, 292);
      ctx.textAlign = 'left';
    }

    // Right Side Info Panel
    if (!currentResults) {
      ctx.fillStyle = '#f8fafc';
      ctx.font = 'bold 26px Inter, sans-serif';
      ctx.fillText('Virtual Cohort Engine', 565, 170);

      ctx.fillStyle = '#e2e8f0';
      ctx.font = '20px Inter, sans-serif';
      ctx.fillText('• Demographic Variation (CV 18-30%)', 565, 218);
      ctx.fillText('• Impaired Liver Subgroup (0.6x)', 565, 256);
      ctx.fillText('• Vectorized Bateman (< 0.2s)', 565, 294);
      ctx.fillText('• 1,000-Patient 3D Crowd Arena', 565, 332);
      ctx.fillStyle = '#94a3b8';
      ctx.fillText('• Status: No trial run yet', 565, 370);
    } else {
      const s = currentResults.summary;
      const helpedCount = s.group_counts?.in_range ?? s.group_counts?.helped ?? 0;
      const toxicCount = s.group_counts?.toxic ?? 0;
      const subCount = s.group_counts?.subtherapeutic ?? 0;
      const medPeak = s.median_peak ?? s.peak_concentration?.median ?? 0;
      const avgPeak = s.mean_peak ?? s.peak_concentration?.mean ?? 0;

      ctx.fillStyle = '#f8fafc';
      ctx.font = 'bold 26px Inter, sans-serif';
      ctx.fillText(`Real Cohort (N=${s.n_patients})`, 565, 170);

      ctx.fillStyle = '#10b981';
      ctx.font = 'bold 20px Inter, sans-serif';
      ctx.fillText(`• ${helpedCount} In Range (${s.pct_in_range ?? 0}%)`, 565, 218);

      ctx.fillStyle = '#ef4444';
      ctx.fillText(`• ${toxicCount} Above Range (Toxic) (${s.pct_toxic ?? 0}%)`, 565, 256);

      ctx.fillStyle = '#f59e0b';
      ctx.fillText(`• ${subCount} Below Range (${s.pct_subtherapeutic ?? 0}%)`, 565, 294);

      ctx.fillStyle = '#cbd5e1';
      ctx.font = '20px Inter, sans-serif';
      ctx.fillText(`• Peak Median: ${Number(medPeak).toFixed(1)} mg/L`, 565, 332);
      ctx.fillText(`• Peak Mean: ${Number(avgPeak).toFixed(1)} mg/L`, 565, 370);
    }

    // Status / Click prompt banner
    ctx.fillStyle = '#9333ea';
    ctx.fillRect(48, 475, 928, 65);
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 24px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';

    if (!currentResults) {
      ctx.fillText(`▶ CLICK TO RUN VIRTUAL TRIAL (${statusText})`, 512, 516);
    } else {
      const s = currentResults.summary;
      const helpedCount = s.group_counts?.in_range ?? s.group_counts?.helped ?? 0;
      const toxicCount = s.group_counts?.toxic ?? 0;
      const subCount = s.group_counts?.subtherapeutic ?? 0;
      ctx.fillText(`▶ TRIAL COMPLETE: ${helpedCount} IN RANGE, ${subCount} BELOW, ${toxicCount} TOXIC`, 512, 516);
    }
    ctx.textAlign = 'left';
  }

  drawScreenGraphic('No trial run yet', null);

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;

  const screenMat = new THREE.MeshBasicMaterial({ map: texture });
  const screenGeo = new THREE.PlaneGeometry(3.1, 1.7);
  const screenMesh = new THREE.Mesh(screenGeo, screenMat);
  screenMesh.position.z = 0.045;
  group.add(screenMesh);

  group.userData.screenCanvas = canvas;
  group.userData.screenTexture = texture;
  group.userData.updateStatus = (msg) => {
    drawScreenGraphic(msg, lastTrialResults);
    texture.needsUpdate = true;
  };
  group.userData.updateResults = (summary, outcomes) => {
    drawScreenGraphic('Trial Finished', { summary, outcomes });
    texture.needsUpdate = true;
  };

  return group;
}

/**
 * Builds the glass observation gallery and the InstancedMesh crowd of 1000 patients.
 */
export function buildViewingGalleryAndCrowd(parentScene) {
  const trialGroup = new THREE.Group();
  trialGroup.name = 'virtual_trial_hall';

  // 1. Arena Floor / Platform (x: -5.5 to +5.5, z: 4.2 to 11.2, height: 0.18m)
  const platformMat = new THREE.MeshStandardMaterial({
    color: 0x0f172a, // Deep slate dark platform
    roughness: 0.4,
    metalness: 0.3,
  });
  const platformGeo = new THREE.BoxGeometry(11.0, 0.22, 7.5);
  const platformMesh = new THREE.Mesh(platformGeo, platformMat);
  platformMesh.position.set(0, 0.11, 7.7);
  platformMesh.receiveShadow = true;
  trialGroup.add(platformMesh);

  // Glowing neon edge trim around the arena
  const trimMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });
  const trimGeo = new THREE.BoxGeometry(11.1, 0.04, 7.6);
  const trimMesh = new THREE.Mesh(trimGeo, trimMat);
  trimMesh.position.set(0, 0.21, 7.7);
  trialGroup.add(trimMesh);

  // Back Arena Digital Sign
  const signMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });
  const signGeo = new THREE.PlaneGeometry(8.0, 0.6);
  const signMesh = new THREE.Mesh(signGeo, signMat);
  signMesh.position.set(0, 2.5, 11.45);
  signMesh.rotation.y = Math.PI;
  trialGroup.add(signMesh);

  // 2. Glass Observation Gallery Railing at z = 2.15 (between ward and arena)
  const galleryGroup = new THREE.Group();
  galleryGroup.position.set(0, 0, 2.15);

  const glassMat = new THREE.MeshStandardMaterial({
    color: 0xe0f2fe,
    roughness: 0.08,
    metalness: 0.15,
    transparent: true,
    opacity: 0.35,
    depthWrite: false,
  });
  const chromeMat = new THREE.MeshStandardMaterial({
    color: 0xe2e8f0,
    roughness: 0.2,
    metalness: 0.9,
  });

  // Top Handrail
  const railGeo = new THREE.CylinderGeometry(0.04, 0.04, 10.4, 16);
  const railMesh = new THREE.Mesh(railGeo, chromeMat);
  railMesh.rotation.z = Math.PI / 2;
  railMesh.position.set(0, 1.15, 0);
  galleryGroup.add(railMesh);

  // Glass Panels
  const glassGeo = new THREE.BoxGeometry(10.2, 0.95, 0.03);
  const glassMesh = new THREE.Mesh(glassGeo, glassMat);
  glassMesh.position.set(0, 0.6, 0);
  galleryGroup.add(glassMesh);

  // Vertical Support Posts
  const postGeo = new THREE.CylinderGeometry(0.035, 0.035, 1.15, 12);
  for (let px = -5.0; px <= 5.0; px += 2.5) {
    const post = new THREE.Mesh(postGeo, chromeMat);
    post.position.set(px, 0.575, 0);
    galleryGroup.add(post);
  }

  trialGroup.add(galleryGroup);

  // 3. The Crowd: InstancedMesh of 1000 small capsule-people (ONE draw call!)
  const maxPatients = 1000;
  // Capsule: radius 0.09m, length 0.24m (total height 0.42m)
  const capsuleGeo = new THREE.CapsuleGeometry(0.09, 0.24, 6, 12);
  capsuleGeo.translate(0, 0.21, 0); // Stand directly on floor plane y=0.22

  const crowdMat = new THREE.MeshStandardMaterial({
    color: 0xffffff,
    roughness: 0.45,
    metalness: 0.15,
  });

  const crowdMesh = new THREE.InstancedMesh(capsuleGeo, crowdMat, maxPatients);
  crowdMesh.name = 'trial_crowd_instances';
  crowdMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  crowdMesh.castShadow = true;
  crowdMesh.receiveShadow = true;

  // Grid configuration: 25 rows (Z) x 40 columns (X) = 1000 instances
  const cols = 40;
  const rows = 25;
  const xSpan = 9.2;
  const zSpan = 6.2;
  const xStart = -xSpan / 2;
  const zStart = 4.6;
  const dx = xSpan / (cols - 1);
  const dz = zSpan / (rows - 1);

  const dummy = new THREE.Object3D();
  const instancePositions = [];

  for (let i = 0; i < maxPatients; i++) {
    const c = i % cols;
    const r = Math.floor(i / cols);
    const px = xStart + c * dx;
    const pz = zStart + r * dz;
    const py = 0.22;

    dummy.position.set(px, py, pz);
    dummy.scale.set(1, 1, 1);
    dummy.updateMatrix();

    crowdMesh.setMatrixAt(i, dummy.matrix);
    crowdMesh.setColorAt(i, COLOR_NEUTRAL);
    instancePositions.push(new THREE.Vector3(px, py, pz));
  }

  crowdMesh.instanceColor.needsUpdate = true;
  crowdMesh.instanceMatrix.needsUpdate = true;
  crowdMesh.count = maxPatients;

  trialGroup.add(crowdMesh);
  parentScene.add(trialGroup);

  // Active animation state
  let waveAnimActive = false;
  let waveAnimStart = 0;
  let waveDuration = 1400; // ms
  let waveOutcomes = null;
  let waveCallback = null;
  let waveProgressCallback = null;
  let lastProgressUpdate = 0;

  function resetColors() {
    waveAnimActive = false;
    for (let i = 0; i < maxPatients; i++) {
      crowdMesh.setColorAt(i, COLOR_NEUTRAL);
    }
    if (crowdMesh.instanceColor) {
      crowdMesh.instanceColor.needsUpdate = true;
    }
  }

  function setVisibleCount(n) {
    const clamped = Math.max(20, Math.min(maxPatients, n));
    crowdMesh.count = clamped;
  }

  function getColorForOutcome(code) {
    if (code === 1) return COLOR_HELPED;
    if (code === 2) return COLOR_TOXIC;
    return COLOR_SUB;
  }

  function applyInstantResults(outcomes, onComplete) {
    const n = Math.min(outcomes.length, maxPatients);
    crowdMesh.count = n;

    let helped = 0;
    let toxic = 0;
    let below = 0;

    for (let i = 0; i < n; i++) {
      const code = outcomes[i];
      if (code === 1) helped++;
      else if (code === 2) toxic++;
      else below++;

      crowdMesh.setColorAt(i, getColorForOutcome(code));
    }
    if (crowdMesh.instanceColor) {
      crowdMesh.instanceColor.needsUpdate = true;
    }
    if (onComplete) onComplete({ helped, toxic, below, total: n });
  }

  function startWave(outcomes, skipAnimation, onProgress, onComplete) {
    const n = Math.min(outcomes.length, maxPatients);
    crowdMesh.count = n;

    if (skipAnimation) {
      applyInstantResults(outcomes, onComplete);
      return;
    }

    resetColors();
    waveAnimActive = true;
    waveAnimStart = performance.now();
    waveOutcomes = outcomes;
    waveCallback = onComplete;
    waveProgressCallback = onProgress;
    lastProgressUpdate = 0;
  }

  // Update function called from scene render loop
  function update(now) {
    if (!waveAnimActive || !waveOutcomes) return;

    const elapsed = now - waveAnimStart;
    const progress = Math.min(1.0, elapsed / waveDuration);
    const n = Math.min(waveOutcomes.length, maxPatients);

    // Wave travels across rows from front (r=0) to back (r=rows-1)
    const currentRowThreshold = progress * (rows + 1);

    let helped = 0;
    let toxic = 0;
    let below = 0;

    for (let i = 0; i < n; i++) {
      const r = Math.floor(i / cols);
      const code = waveOutcomes[i];

      if (r <= currentRowThreshold) {
        crowdMesh.setColorAt(i, getColorForOutcome(code));
        if (code === 1) helped++;
        else if (code === 2) toxic++;
        else below++;
      } else {
        crowdMesh.setColorAt(i, COLOR_NEUTRAL);
      }
    }

    if (crowdMesh.instanceColor) {
      crowdMesh.instanceColor.needsUpdate = true;
    }

    // Throttled progress callback (~100ms) to eliminate per-frame DOM thrash
    if (now - lastProgressUpdate > 100) {
      lastProgressUpdate = now;
      if (waveProgressCallback) {
        waveProgressCallback({ helped, toxic, below, total: n, progress });
      }
    }

    if (progress >= 1.0) {
      waveAnimActive = false;
      if (waveProgressCallback) {
        waveProgressCallback({ helped, toxic, below, total: n, progress: 1.0 });
      }
      if (waveCallback) {
        waveCallback({ helped, toxic, below, total: n });
      }
    }
  }

  return {
    trialGroup,
    crowdMesh,
    setVisibleCount,
    resetColors,
    applyInstantResults,
    startWave,
    update,
  };
}
