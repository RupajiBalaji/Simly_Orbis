/**
 * Procedural Laboratory Apparatus Builders (frontend/lab/world/apparatus.js)
 * Builds believable 3D procedural apparatus for pk_ward and titration_bench.
 * Each object has userData.targetId mapped directly to backend apparatus IDs.
 */

import * as THREE from 'three';

// Shared materials cache
const glassMat = new THREE.MeshStandardMaterial({
  color: 0xffffff,
  roughness: 0.1,
  metalness: 0.1,
  transparent: true,
  opacity: 0.35,
  depthWrite: false,
});

const plasticMat = new THREE.MeshStandardMaterial({
  color: 0x334155,
  roughness: 0.4,
  metalness: 0.2,
});

const metalMat = new THREE.MeshStandardMaterial({
  color: 0x94a3b8,
  roughness: 0.2,
  metalness: 0.85,
});

/**
 * Normalizes raw apparatus input from backend (either array of objects or object keyed by id).
 * Always returns an array of { id, type, ...props }.
 */
export function normalizeApparatus(rawApparatus) {
  if (!rawApparatus) return [];
  if (Array.isArray(rawApparatus)) {
    return rawApparatus.map((item) => {
      if (!item || typeof item !== 'object') return { id: String(item), type: String(item) };
      return {
        id: item.id || item.name || '',
        type: item.type || item.id || '',
        ...item,
      };
    });
  }
  if (typeof rawApparatus === 'object') {
    return Object.entries(rawApparatus).map(([id, val]) => {
      const obj = val && typeof val === 'object' ? val : {};
      return {
        id,
        type: obj.type || id,
        ...obj,
      };
    });
  }
  return [];
}

export function formatApparatusTitle(id) {
  const titles = {
    digital_balance: 'Digital Balance',
    dosing_cup: 'Dosing Cup',
    water_jug: 'Water Jug',
    patient_bed: 'Patient Alex',
    tube_rack: 'Sample Tube Rack',
    label_pen: 'Label Pen',
    assay_analyzer: 'Centrifuge Analyzer',
    burette: 'Burette Stand',
    conical_flask: 'Conical Flask',
    pipette: 'Pipette',
    indicator_bottles: 'pH Indicators',
    acid_bottle_hcl: '0.1M HCl',
    acid_bottle_acetic: '0.1M Acetic Acid',
    naoh_bottle: '0.1M NaOH',
    ph_meter: 'pH Meter',
    wash_bottle: 'Wash Bottle',
    sink: 'Utility Sink',
    biohazard_bin: 'Biohazard Bin',
    chemical_waste_bin: 'Chemical Waste',
    ward_clock: 'Clinical Clock',
  };
  return titles[id] || (id ? id.replace(/_/g, ' ') : '');
}

export function getApparatusTagHeight(id) {
  if (id === 'burette') return 1.7;
  if (id === 'patient_bed') return 1.1;
  if (id === 'conical_flask') return 0.55;
  if (id === 'assay_analyzer') return 0.75;
  if (id === 'water_jug' || id === 'wash_bottle') return 0.55;
  if (id === 'sink') return 0.6;
  if (id && id.includes('bin')) return 0.7;
  return 0.45;
}

export function createNameTag(label) {
  const canvas = document.createElement('canvas');
  canvas.width = 256;
  canvas.height = 64;
  const ctx = canvas.getContext('2d');

  ctx.fillStyle = 'rgba(15, 23, 42, 0.92)';
  ctx.strokeStyle = '#c084fc';
  ctx.lineWidth = 3;

  ctx.beginPath();
  if (ctx.roundRect) {
    ctx.roundRect(6, 6, 244, 52, 10);
  } else {
    ctx.rect(6, 6, 244, 52);
  }
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = '#f8fafc';
  ctx.font = 'bold 22px sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(label, 128, 32);

  const texture = new THREE.CanvasTexture(canvas);
  const spriteMat = new THREE.SpriteMaterial({ map: texture, depthTest: false });
  const sprite = new THREE.Sprite(spriteMat);
  sprite.scale.set(0.52, 0.14, 1.0);
  sprite.userData.isNameTag = true;
  return sprite;
}

export function buildApparatus(rawApparatus, scene) {
  const container = new THREE.Group();
  container.name = 'apparatus_container';

  const lookup = {};
  const apparatusList = normalizeApparatus(rawApparatus);

  for (const item of apparatusList) {
    const id = item.id;
    const type = item.type;
    let group = null;

    if (id === 'digital_balance' || type === 'balance' || type === 'digital_balance') {
      group = buildDigitalBalance(id);
      group.position.set(-4.5, 0.94, -4.2);
      group.userData.stationPos = new THREE.Vector3(-4.85, 0, -3.75);
    } else if (id === 'dosing_cup' || type === 'cup' || type === 'container' || type === 'dosing_cup') {
      group = buildDosingCup(id);
      group.position.set(-3.6, 0.94, -4.0);
      group.userData.stationPos = new THREE.Vector3(-3.8, 0, -3.5);
    } else if (id === 'water_jug' || type === 'source' || type === 'water_jug') {
      group = buildWaterJug(id);
      group.position.set(-5.3, 0.94, -4.3);
      group.userData.stationPos = new THREE.Vector3(-4.5, 0, -3.75);
    } else if (id === 'patient_bed' || type === 'patient_station' || type === 'patient_bed') {
      group = buildPatientBed(id);
      group.position.set(4.5, 0, -3.8);
      group.userData.stationPos = new THREE.Vector3(3.4, 0, -3.3);
    } else if (id.startsWith('tube_') || type === 'sample_tube' || id === 'tube_rack' || type === 'tube_rack') {
      if (!lookup['tube_rack']) {
        const rack = buildTubeRack('tube_rack');
        rack.position.set(-3.0, 0.94, -4.3);
        rack.userData.stationPos = new THREE.Vector3(-3.2, 0, -3.5);
        rack.userData.targetId = 'tube_rack';
        rack.userData.title = 'Sample Tube Rack';
        rack.userData.interactive = true;
        const tag = createNameTag('Sample Tube Rack');
        tag.position.set(0, getApparatusTagHeight('tube_rack'), 0);
        rack.add(tag);
        container.add(rack);
        lookup['tube_rack'] = rack;
        if (rack.userData.tubes) {
          for (const [tId, tGroup] of Object.entries(rack.userData.tubes)) {
            lookup[tId] = tGroup;
          }
        }
      }
      continue;
    } else if (id === 'label_pen' || type === 'tool' || type === 'label_pen') {
      group = buildLabelPen(id);
      group.position.set(-4.0, 0.94, -3.7);
      group.userData.stationPos = new THREE.Vector3(-4.0, 0, -3.2);
    } else if (id === 'assay_analyzer' || type === 'analyzer' || type === 'assay_analyzer') {
      group = buildAssayAnalyzer(id);
      group.position.set(-5.5, 0.94, -3.5);
      group.userData.stationPos = new THREE.Vector3(-5.2, 0, -2.8);
    } else if (id === 'biohazard_bin' || (type === 'waste_bin' && id.includes('bio'))) {
      group = buildWasteBin(id, 'biohazard');
      group.position.set(-2.0, 0, -5.2);
      group.userData.stationPos = new THREE.Vector3(-2.0, 0, -4.2);
    } else if (id === 'chemical_waste_bin' || (type === 'waste_bin' && (id.includes('chem') || !id.includes('bio')))) {
      group = buildWasteBin(id, 'chemical');
      group.position.set(2.0, 0, -5.2);
      group.userData.stationPos = new THREE.Vector3(2.0, 0, -4.2);
    } else if (id === 'sink' || type === 'sink' || type === 'utility') {
      if (id === 'sink' || !lookup['sink']) {
        group = buildSink('sink');
        group.position.set(-7.2, 0.9, -1.0);
        group.userData.stationPos = new THREE.Vector3(-6.2, 0, -1.0);
      }
    } else if (id === 'burette' || type === 'burette') {
      group = buildBurette(id);
      group.position.set(0, 0.94, -1.85);
      group.userData.stationPos = new THREE.Vector3(-0.48, 0, -1.65);
    } else if (id === 'conical_flask' || type === 'flask' || type === 'conical_flask') {
      group = buildConicalFlask(id);
      group.position.set(0.04, 0.94, -1.85);
      group.userData.stationPos = new THREE.Vector3(-0.48, 0, -1.65);
    } else if (id === 'pipette' || type === 'pipette') {
      group = buildPipette(id);
      group.position.set(-1.0, 0.94, -1.85);
      group.userData.stationPos = new THREE.Vector3(-0.8, 0, -1.5);
    } else if (id === 'indicator_bottles' || type === 'indicator_shelf') {
      group = buildIndicatorBottles(id);
      group.position.set(1.1, 0.94, -2.2);
      group.userData.stationPos = new THREE.Vector3(0.8, 0, -1.2);
    } else if (id.includes('acid') || type === 'acid_bottles') {
      group = buildReagentBottles(id, 'acid');
      const posX = id.includes('acetic') ? -1.9 : -1.6;
      group.position.set(posX, 0.94, -2.2);
      group.userData.stationPos = new THREE.Vector3(-1.2, 0, -1.2);
    } else if (id.includes('naoh') || id.includes('base') || type === 'base_bottle') {
      group = buildReagentBottles(id, 'base');
      group.position.set(1.8, 0.94, -2.2);
      group.userData.stationPos = new THREE.Vector3(1.2, 0, -1.2);
    } else if (id === 'ph_meter' || type === 'ph_meter') {
      group = buildPhMeter(id);
      group.position.set(-0.8, 0.94, -2.3);
      group.userData.stationPos = new THREE.Vector3(-0.5, 0, -1.2);
    } else if (id === 'wash_bottle' || type === 'wash_bottle') {
      group = buildWashBottle(id);
      group.position.set(1.4, 0.94, -1.7);
      group.userData.stationPos = new THREE.Vector3(1.0, 0, -1.0);
    } else {
      console.warn(`Unmapped apparatus: id='${id}', type='${type}'`);
    }

    if (group) {
      group.userData.targetId = id;
      group.userData.apparatusType = type;
      group.userData.title = item.name || formatApparatusTitle(id);
      group.userData.interactive = true;

      // Floating Name Tag (Toggleable with 'N')
      const tag = createNameTag(formatApparatusTitle(id));
      tag.position.set(0, getApparatusTagHeight(id), 0);
      group.add(tag);

      container.add(group);
      lookup[id] = group;
    }
  }

  // Add ward clock on back wall
  if (!lookup['ward_clock']) {
    const clock = buildWardClock('ward_clock');
    clock.position.set(0, 4.0, -6.9);
    container.add(clock);
    lookup['ward_clock'] = clock;
  }

  scene.add(container);
  return { container, lookup };
}

// ---------------------------------------------------------------------------
// Digital Analytical Balance
// ---------------------------------------------------------------------------
function buildDigitalBalance(id) {
  const g = new THREE.Group();

  // Base
  const baseGeo = new THREE.BoxGeometry(0.5, 0.1, 0.6);
  const base = new THREE.Mesh(baseGeo, plasticMat);
  g.add(base);

  // Pan (Stainless Steel)
  const panGeo = new THREE.CylinderGeometry(0.18, 0.18, 0.02, 32);
  const pan = new THREE.Mesh(panGeo, metalMat);
  pan.position.y = 0.06;
  g.add(pan);

  // Draft shield glass
  const shieldGeo = new THREE.BoxGeometry(0.42, 0.35, 0.42);
  const shield = new THREE.Mesh(shieldGeo, glassMat);
  shield.position.set(0, 0.22, -0.05);
  g.add(shield);

  // Digital Screen Canvas Texture
  const canvas = document.createElement('canvas');
  canvas.width = 256;
  canvas.height = 96;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#020617';
  ctx.fillRect(0, 0, 256, 96);
  ctx.fillStyle = '#38bdf8';
  ctx.font = 'bold 36px monospace';
  ctx.textAlign = 'right';
  ctx.fillText('0.000 g', 230, 60);

  const tex = new THREE.CanvasTexture(canvas);
  const screenGeo = new THREE.PlaneGeometry(0.3, 0.1);
  const screenMat = new THREE.MeshBasicMaterial({ map: tex });
  const screen = new THREE.Mesh(screenGeo, screenMat);
  screen.position.set(0, 0.055, 0.28);
  screen.rotation.x = -Math.PI / 6;
  g.add(screen);

  g.userData.canvas = canvas;
  g.userData.ctx = ctx;
  g.userData.tex = tex;
  g.userData.readoutTarget = 'digital_balance';

  return g;
}

// ---------------------------------------------------------------------------
// Dosing Cup & Liquid
// ---------------------------------------------------------------------------
function buildDosingCup(id) {
  const g = new THREE.Group();

  const cupGeo = new THREE.CylinderGeometry(0.1, 0.08, 0.16, 24, 1, true);
  const cup = new THREE.Mesh(cupGeo, glassMat);
  cup.position.y = 0.08;
  g.add(cup);

  // Cup bottom
  const btmGeo = new THREE.CircleGeometry(0.08, 24);
  const btm = new THREE.Mesh(btmGeo, glassMat);
  btm.rotation.x = Math.PI / 2;
  g.add(btm);

  // Interior Liquid mesh
  const liqGeo = new THREE.CylinderGeometry(0.095, 0.078, 0.001, 24);
  const liqMat = new THREE.MeshStandardMaterial({
    color: 0xf1f5f9,
    transparent: true,
    opacity: 0.0,
    roughness: 0.1,
  });
  const liq = new THREE.Mesh(liqGeo, liqMat);
  liq.position.y = 0.01;
  g.add(liq);

  // Label text holder
  const lblGeo = new THREE.PlaneGeometry(0.12, 0.04);
  const lblMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0 });
  const lblMesh = new THREE.Mesh(lblGeo, lblMat);
  lblMesh.position.set(0, 0.08, 0.102);
  g.add(lblMesh);

  g.userData.liquidMesh = liq;
  g.userData.labelMesh = lblMesh;
  g.userData.maxVolume = 100;
  g.userData.fullHeight = 0.14;

  return g;
}

// ---------------------------------------------------------------------------
// Water Jug
// ---------------------------------------------------------------------------
function buildWaterJug(id) {
  const g = new THREE.Group();

  const bodyGeo = new THREE.CylinderGeometry(0.2, 0.22, 0.45, 24);
  const body = new THREE.Mesh(bodyGeo, glassMat);
  body.position.y = 0.225;
  g.add(body);

  // Water inside jug
  const liqGeo = new THREE.CylinderGeometry(0.19, 0.21, 0.35, 24);
  const liqMat = new THREE.MeshStandardMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.5, roughness: 0.1 });
  const liq = new THREE.Mesh(liqGeo, liqMat);
  liq.position.y = 0.18;
  g.add(liq);

  // Handle
  const handleGeo = new THREE.TorusGeometry(0.16, 0.025, 8, 24, Math.PI);
  const handle = new THREE.Mesh(handleGeo, glassMat);
  handle.position.set(0.24, 0.22, 0);
  handle.rotation.z = -Math.PI / 2;
  g.add(handle);

  return g;
}

// ---------------------------------------------------------------------------
// Patient Bed & Clinical Bedside Monitor
// ---------------------------------------------------------------------------
function buildPatientBed(id) {
  const g = new THREE.Group();

  // Metal Frame
  const frameGeo = new THREE.BoxGeometry(2.4, 0.4, 1.2);
  const frame = new THREE.Mesh(frameGeo, metalMat);
  frame.position.y = 0.2;
  g.add(frame);

  // Mattress
  const matGeo = new THREE.BoxGeometry(2.3, 0.25, 1.15);
  const matMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, roughness: 0.6 });
  const mattress = new THREE.Mesh(matGeo, matMat);
  mattress.position.y = 0.5;
  g.add(mattress);

  // Patient Torso Contour under blanket
  const torsoGeo = new THREE.BoxGeometry(1.1, 0.18, 0.68);
  const torsoMat = new THREE.MeshStandardMaterial({ color: 0x93c5fd, roughness: 0.6 }); // patient gown
  const torso = new THREE.Mesh(torsoGeo, torsoMat);
  torso.position.set(0.1, 0.68, 0);
  g.add(torso);

  // Layered Hospital Duvet / Blanket
  const blanketGeo = new THREE.BoxGeometry(1.45, 0.16, 1.16);
  const blanketMat = new THREE.MeshStandardMaterial({ color: 0xf1f5f9, roughness: 0.8 });
  const blanket = new THREE.Mesh(blanketGeo, blanketMat);
  blanket.position.set(-0.35, 0.68, 0);
  g.add(blanket);

  // Turned-Down Sheet Collar Fold at chest
  const collarGeo = new THREE.BoxGeometry(0.16, 0.04, 1.08);
  const collarMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.5 });
  const collar = new THREE.Mesh(collarGeo, collarMat);
  collar.position.set(0.42, 0.77, 0);
  g.add(collar);

  // Pillow
  const pillowGeo = new THREE.BoxGeometry(0.42, 0.12, 0.82);
  const pillow = new THREE.Mesh(pillowGeo, collarMat);
  pillow.position.set(0.85, 0.66, 0);
  g.add(pillow);

  // Stylized Patient Figure (Alex) with Face & Exposed Venipuncture Arm
  const patientGroup = new THREE.Group();
  const skinMat = new THREE.MeshStandardMaterial({ color: 0xfed7aa, roughness: 0.5 }); // warm skin
  const hairMat = new THREE.MeshStandardMaterial({ color: 0x451a03, roughness: 0.8 }); // brown hair
  const darkMat = new THREE.MeshBasicMaterial({ color: 0x334155 }); // facial features
  const lipMat = new THREE.MeshBasicMaterial({ color: 0xfb7185 }); // soft lips

  // Head
  const headGeo = new THREE.SphereGeometry(0.16, 20, 20);
  const head = new THREE.Mesh(headGeo, skinMat);
  head.position.set(0.85, 0.82, 0);
  patientGroup.add(head);

  // Hair
  const hairGeo = new THREE.BoxGeometry(0.25, 0.12, 0.28);
  const hair = new THREE.Mesh(hairGeo, hairMat);
  hair.position.set(0.88, 0.90, 0);
  patientGroup.add(hair);

  // Face Features (Eyes closed resting, nose, lips)
  const leftEye = new THREE.Mesh(new THREE.BoxGeometry(0.038, 0.010, 0.02), darkMat);
  leftEye.position.set(0.78, 0.84, 0.13);
  patientGroup.add(leftEye);

  const rightEye = new THREE.Mesh(new THREE.BoxGeometry(0.038, 0.010, 0.02), darkMat);
  rightEye.position.set(0.88, 0.84, 0.13);
  patientGroup.add(rightEye);

  const nose = new THREE.Mesh(new THREE.BoxGeometry(0.020, 0.032, 0.025), skinMat);
  nose.position.set(0.83, 0.80, 0.15);
  patientGroup.add(nose);

  const mouth = new THREE.Mesh(new THREE.BoxGeometry(0.045, 0.010, 0.015), lipMat);
  mouth.position.set(0.83, 0.75, 0.14);
  patientGroup.add(mouth);

  // Exposed Arm for Blood Draw (resting on sterile arm-support pad outside blanket)
  const padGeo = new THREE.BoxGeometry(0.65, 0.05, 0.22);
  const padMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.4 });
  const armPad = new THREE.Mesh(padGeo, padMat);
  armPad.position.set(0.24, 0.64, 0.48);
  patientGroup.add(armPad);

  // Upper arm emerging from under collar
  const upperArmGeo = new THREE.CylinderGeometry(0.048, 0.044, 0.28, 12);
  const upperArm = new THREE.Mesh(upperArmGeo, skinMat);
  upperArm.position.set(0.44, 0.74, 0.36);
  upperArm.rotation.set(0.2, 0, Math.PI / 3);
  patientGroup.add(upperArm);

  // Cyan Tourniquet Band
  const tourniquetGeo = new THREE.CylinderGeometry(0.051, 0.051, 0.03, 12);
  const tourniquetMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, roughness: 0.3 });
  const tourniquet = new THREE.Mesh(tourniquetGeo, tourniquetMat);
  tourniquet.position.set(0.38, 0.72, 0.41);
  tourniquet.rotation.set(0.2, 0, Math.PI / 3);
  patientGroup.add(tourniquet);

  // Forearm extended along arm support pad exposing antecubital vein
  const forearmGeo = new THREE.CylinderGeometry(0.040, 0.036, 0.30, 12);
  const forearm = new THREE.Mesh(forearmGeo, skinMat);
  forearm.position.set(0.22, 0.69, 0.48);
  forearm.rotation.z = Math.PI / 2;
  patientGroup.add(forearm);

  // Relaxed hand and curled fingers
  const handGeo = new THREE.BoxGeometry(0.075, 0.032, 0.075);
  const hand = new THREE.Mesh(handGeo, skinMat);
  hand.position.set(0.04, 0.68, 0.48);
  patientGroup.add(hand);

  const fingersGeo = new THREE.BoxGeometry(0.035, 0.018, 0.065);
  const fingers = new THREE.Mesh(fingersGeo, skinMat);
  fingers.position.set(-0.015, 0.67, 0.48);
  patientGroup.add(fingers);

  g.add(patientGroup);
  g.userData.patientMesh = head; // tinted on vitals changes

  // Bedside Monitor Pole & Screen
  const poleGeo = new THREE.CylinderGeometry(0.03, 0.03, 1.8, 12);
  const pole = new THREE.Mesh(poleGeo, metalMat);
  pole.position.set(1.1, 0.9, -0.7);
  g.add(pole);

  // Monitor Display Canvas
  const monCanvas = document.createElement('canvas');
  monCanvas.width = 256;
  monCanvas.height = 200;
  const mctx = monCanvas.getContext('2d');
  mctx.fillStyle = '#0f172a';
  mctx.fillRect(0, 0, 256, 200);
  mctx.fillStyle = '#10b981';
  mctx.font = 'bold 22px monospace';
  mctx.fillText('HR: 70 bpm', 20, 48);
  mctx.fillText('SpO2: 99%', 20, 92);
  mctx.fillStyle = '#38bdf8';
  mctx.font = '16px monospace';
  mctx.fillText('ALEX (70 kg)', 20, 140);
  mctx.fillStyle = '#a855f7';
  mctx.fillText('Normal Sinus', 20, 175);

  const monTex = new THREE.CanvasTexture(monCanvas);
  const monGroup = new THREE.Group();
  monGroup.position.set(1.0, 1.6, -0.7);
  monGroup.rotation.y = -Math.PI / 4; // Angled toward camera & room center

  const monGeo = new THREE.BoxGeometry(0.6, 0.45, 0.08);
  const monMesh = new THREE.Mesh(monGeo, plasticMat);
  monGroup.add(monMesh);

  const monScreenGeo = new THREE.PlaneGeometry(0.54, 0.39);
  const monScreenMat = new THREE.MeshBasicMaterial({ map: monTex });
  const monScreen = new THREE.Mesh(monScreenGeo, monScreenMat);
  monScreen.position.z = 0.045;
  monGroup.add(monScreen);

  g.add(monGroup);

  g.userData.monitorCanvas = monCanvas;
  g.userData.monitorCtx = mctx;
  g.userData.monitorTex = monTex;

  return g;
}

// ---------------------------------------------------------------------------
// Blood Sample Tube Rack (3 Tubes)
// ---------------------------------------------------------------------------
function buildTubeRack(id) {
  const g = new THREE.Group();

  // Wooden / Acrylic Rack Base
  const rackMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, roughness: 0.4 });
  const baseGeo = new THREE.BoxGeometry(0.4, 0.04, 0.15);
  const base = new THREE.Mesh(baseGeo, rackMat);
  g.add(base);

  const topGeo = new THREE.BoxGeometry(0.4, 0.04, 0.15);
  const top = new THREE.Mesh(topGeo, rackMat);
  top.position.y = 0.16;
  g.add(top);

  const postGeo = new THREE.CylinderGeometry(0.015, 0.015, 0.16, 8);
  for (const px of [-0.18, 0.18]) {
    for (const pz of [-0.05, 0.05]) {
      const p = new THREE.Mesh(postGeo, rackMat);
      p.position.set(px, 0.08, pz);
      g.add(p);
    }
  }

  // 3 Glass Collection Tubes
  g.userData.tubes = {};

  const tubeX = [-0.11, 0, 0.11];
  for (let i = 0; i < 3; i++) {
    const tubeId = `tube_${i + 1}`;
    const tubeGroup = new THREE.Group();
    tubeGroup.position.set(tubeX[i], 0.02, 0);

    const tubeGeo = new THREE.CylinderGeometry(0.028, 0.028, 0.18, 16, 1, true);
    const tubeMesh = new THREE.Mesh(tubeGeo, glassMat);
    tubeMesh.position.y = 0.09;
    tubeGroup.add(tubeMesh);

    // Liquid in tube (initially empty)
    const liqGeo = new THREE.CylinderGeometry(0.026, 0.026, 0.001, 16);
    const liqMat = new THREE.MeshStandardMaterial({
      color: 0x991b1b,
      transparent: true,
      opacity: 0.0,
      roughness: 0.2,
    });
    const liq = new THREE.Mesh(liqGeo, liqMat);
    liq.position.y = 0.01;
    tubeGroup.add(liq);

    // Rubber stopper
    const capGeo = new THREE.CylinderGeometry(0.03, 0.026, 0.03, 16);
    const capMat = new THREE.MeshStandardMaterial({ color: 0x64748b, roughness: 0.5 });
    const cap = new THREE.Mesh(capGeo, capMat);
    cap.position.y = 0.19;
    tubeGroup.add(cap);

    // Label decal
    const lblGeo = new THREE.PlaneGeometry(0.04, 0.06);
    const lblMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0 });
    const lblMesh = new THREE.Mesh(lblGeo, lblMat);
    lblMesh.position.set(0, 0.1, 0.03);
    tubeGroup.add(lblMesh);

    tubeGroup.userData.liquidMesh = liq;
    tubeGroup.userData.labelMesh = lblMesh;
    tubeGroup.userData.fullHeight = 0.14;
    tubeGroup.userData.targetId = tubeId;

    g.add(tubeGroup);
    g.userData.tubes[tubeId] = tubeGroup;
  }

  return g;
}

// ---------------------------------------------------------------------------
// Centrifuge & Spectrophotometer Assay Analyzer
// ---------------------------------------------------------------------------
function buildAssayAnalyzer(id) {
  const g = new THREE.Group();

  // Machine Body
  const bodyGeo = new THREE.BoxGeometry(0.65, 0.35, 0.55);
  const body = new THREE.Mesh(bodyGeo, plasticMat);
  body.position.y = 0.175;
  g.add(body);

  // Rotor Lid
  const lidGeo = new THREE.CylinderGeometry(0.18, 0.18, 0.04, 24);
  const lid = new THREE.Mesh(lidGeo, metalMat);
  lid.position.set(-0.12, 0.36, 0);
  g.add(lid);

  // Digital Analyzer Canvas Screen
  const canvas = document.createElement('canvas');
  canvas.width = 256;
  canvas.height = 128;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#090d16';
  ctx.fillRect(0, 0, 256, 128);
  ctx.fillStyle = '#38bdf8';
  ctx.font = 'bold 20px monospace';
  ctx.fillText('PLASMA ANALYZER', 20, 36);
  ctx.fillStyle = '#f8fafc';
  ctx.font = 'bold 28px monospace';
  ctx.fillText('STANDBY', 20, 84);

  const tex = new THREE.CanvasTexture(canvas);
  const screenGeo = new THREE.PlaneGeometry(0.26, 0.16);
  const screenMat = new THREE.MeshBasicMaterial({ map: tex });
  const screen = new THREE.Mesh(screenGeo, screenMat);
  screen.position.set(0.16, 0.28, 0.28);
  screen.rotation.x = -Math.PI / 8;
  g.add(screen);

  // Status Indicator Glow Light
  const glowGeo = new THREE.SphereGeometry(0.02, 12, 12);
  const glowMat = new THREE.MeshBasicMaterial({ color: 0x10b981 });
  const glowOrb = new THREE.Mesh(glowGeo, glowMat);
  glowOrb.position.set(0.24, 0.34, 0.24);
  g.add(glowOrb);

  g.userData.canvas = canvas;
  g.userData.ctx = ctx;
  g.userData.tex = tex;
  g.userData.statusLight = glowOrb;

  return g;
}

// ---------------------------------------------------------------------------
// Waste Bins (Biohazard & Chemical)
// ---------------------------------------------------------------------------
function buildWasteBin(id, type) {
  const g = new THREE.Group();

  const isBio = type === 'biohazard';
  const binColor = isBio ? 0xdc2626 : 0xf59e0b;
  const binMat = new THREE.MeshStandardMaterial({ color: binColor, roughness: 0.5 });

  const bodyGeo = new THREE.CylinderGeometry(0.22, 0.18, 0.65, 24);
  const body = new THREE.Mesh(bodyGeo, binMat);
  body.position.y = 0.325;
  g.add(body);

  const lidGeo = new THREE.CylinderGeometry(0.24, 0.24, 0.06, 24);
  const lidMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.4 });
  const lid = new THREE.Mesh(lidGeo, lidMat);
  lid.position.y = 0.66;
  g.add(lid);

  // Label Placard
  const canvas = document.createElement('canvas');
  canvas.width = 128;
  canvas.height = 128;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = isBio ? '#fee2e2' : '#fef3c7';
  ctx.fillRect(0, 0, 128, 128);
  ctx.fillStyle = '#0f172a';
  ctx.font = 'bold 16px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(isBio ? 'BIOHAZARD' : 'CHEMICAL', 64, 45);
  ctx.fillText('WASTE ONLY', 64, 75);

  const tex = new THREE.CanvasTexture(canvas);
  const placardGeo = new THREE.PlaneGeometry(0.18, 0.18);
  const placardMat = new THREE.MeshBasicMaterial({ map: tex });
  const placard = new THREE.Mesh(placardGeo, placardMat);
  placard.position.set(0, 0.4, 0.21);
  g.add(placard);

  return g;
}

// ---------------------------------------------------------------------------
// Laboratory Stainless Steel Sink & Gooseneck Tap
// ---------------------------------------------------------------------------
function buildSink(id) {
  const g = new THREE.Group();

  // Sink Basin
  const basinGeo = new THREE.BoxGeometry(0.8, 0.3, 0.6);
  const basin = new THREE.Mesh(basinGeo, metalMat);
  basin.position.y = -0.15;
  g.add(basin);

  // Gooseneck Tap
  const curve = new THREE.QuadraticBezierCurve3(
    new THREE.Vector3(0, 0, -0.2),
    new THREE.Vector3(0, 0.4, -0.2),
    new THREE.Vector3(0, 0.35, 0)
  );
  const tubeGeo = new THREE.TubeGeometry(curve, 16, 0.02, 8, false);
  const tap = new THREE.Mesh(tubeGeo, metalMat);
  g.add(tap);

  return g;
}

// ---------------------------------------------------------------------------
// Burette & Retort Stand
// ---------------------------------------------------------------------------
function buildBurette(id) {
  const g = new THREE.Group();
  g.scale.set(1.15, 1.15, 1.15);

  // Retort Stand Base & Porcelain Contrast Tile
  const baseGeo = new THREE.BoxGeometry(0.36, 0.025, 0.28);
  const base = new THREE.Mesh(baseGeo, plasticMat);
  base.position.y = 0.0125;
  g.add(base);

  const tileGeo = new THREE.BoxGeometry(0.20, 0.005, 0.20);
  const tileMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
  const tile = new THREE.Mesh(tileGeo, tileMat);
  tile.position.set(0.04, 0.0275, 0);
  g.add(tile);

  // Steel Retort Rod
  const rodGeo = new THREE.CylinderGeometry(0.012, 0.012, 0.88, 12);
  const rod = new THREE.Mesh(rodGeo, metalMat);
  rod.position.set(-0.12, 0.45, 0);
  g.add(rod);

  // Upper Clamp Arm
  const clampGeo = new THREE.BoxGeometry(0.18, 0.025, 0.025);
  const clamp = new THREE.Mesh(clampGeo, metalMat);
  clamp.position.set(-0.03, 0.60, 0);
  g.add(clamp);

  // Lower Stabilizer Clamp
  const clamp2 = new THREE.Mesh(clampGeo.clone(), metalMat);
  clamp2.position.set(-0.03, 0.35, 0);
  g.add(clamp2);

  // Burette Glass Tube (50 mL graduated)
  const tubeGeo = new THREE.CylinderGeometry(0.020, 0.020, 0.58, 20, 1, true);
  const tube = new THREE.Mesh(tubeGeo, glassMat);
  tube.position.set(0.04, 0.52, 0);
  g.add(tube);

  // Funnel Rim at Top Opening
  const rimGeo = new THREE.CylinderGeometry(0.030, 0.020, 0.03, 20);
  const rim = new THREE.Mesh(rimGeo, glassMat);
  rim.position.set(0.04, 0.82, 0);
  g.add(rim);

  // Stopcock Glass Housing (Fused seamlessly into the glass tube)
  const scHousingGeo = new THREE.CylinderGeometry(0.024, 0.024, 0.04, 16);
  const scHousing = new THREE.Mesh(scHousingGeo, glassMat);
  scHousing.position.set(0.04, 0.21, 0);
  g.add(scHousing);

  // Stopcock Valve Tap (PTFE barrel + neat ergonomic handle)
  const valveKeyGeo = new THREE.CylinderGeometry(0.010, 0.010, 0.05, 12);
  const ptfeMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, roughness: 0.3 });
  const valveKey = new THREE.Mesh(valveKeyGeo, ptfeMat);
  valveKey.rotation.x = Math.PI / 2;
  valveKey.position.set(0.04, 0.21, 0);
  g.add(valveKey);

  const handleGeo = new THREE.BoxGeometry(0.042, 0.012, 0.012);
  const handleMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, roughness: 0.4 });
  const handle = new THREE.Mesh(handleGeo, handleMat);
  handle.position.set(0.04, 0.21, 0.03);
  g.add(handle);

  // Burette Tip (tapered delivery jet extending right down over flask)
  const tipGeo = new THREE.CylinderGeometry(0.012, 0.003, 0.08, 12);
  const tip = new THREE.Mesh(tipGeo, glassMat);
  tip.position.set(0.04, 0.15, 0);
  g.add(tip);

  // Burette Interior Liquid
  const liqGeo = new THREE.CylinderGeometry(0.018, 0.018, 1.0, 16);
  liqGeo.translate(0, 0.5, 0);
  const liqMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, transparent: true, opacity: 0.0 });
  const liq = new THREE.Mesh(liqGeo, liqMat);
  liq.position.set(0.04, 0.22, 0);
  liq.scale.set(1.0, 0.001, 1.0);
  liq.visible = false;
  g.add(liq);

  g.userData.liquidMesh = liq;
  g.userData.valveMesh = handle;
  g.userData.maxVolume = 50.0;
  g.userData.fullHeight = 0.56;

  return g;
}

// ---------------------------------------------------------------------------
// 250 mL Conical Erlenmeyer Flask
// ---------------------------------------------------------------------------
function buildConicalFlask(id) {
  const g = new THREE.Group();
  g.scale.set(1.15, 1.15, 1.15);

  // Glass Erlenmeyer Cone & Neck
  const coneGeo = new THREE.ConeGeometry(0.18, 0.26, 24, 1, true);
  const cone = new THREE.Mesh(coneGeo, glassMat);
  cone.position.y = 0.13;
  g.add(cone);

  const neckGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.12, 24, 1, true);
  const neck = new THREE.Mesh(neckGeo, glassMat);
  neck.position.y = 0.32;
  g.add(neck);

  // Base disc
  const btmGeo = new THREE.CircleGeometry(0.18, 24);
  const btm = new THREE.Mesh(btmGeo, glassMat);
  btm.rotation.x = Math.PI / 2;
  g.add(btm);

  // Interior Liquid mesh (starts completely empty, volume 0 = invisible)
  const liqGeo = new THREE.CylinderGeometry(0.165, 0.168, 0.02, 24);
  const liqMat = new THREE.MeshStandardMaterial({
    color: 0xf8fafc,
    transparent: true,
    opacity: 0.0,
    roughness: 0.1,
  });
  const liq = new THREE.Mesh(liqGeo, liqMat);
  liq.position.y = 0.01;
  liq.visible = false;
  g.add(liq);

  g.userData.liquidMesh = liq;
  g.userData.maxVolume = 250.0;
  g.userData.fullHeight = 0.20;
  g.userData.isConicalFlask = true;

  return g;
}

// ---------------------------------------------------------------------------
// Volumetric Pipette
// ---------------------------------------------------------------------------
function buildPipette(id) {
  const g = new THREE.Group();

  // Silicone Pipette Rest Pad on Bench
  const restPadGeo = new THREE.BoxGeometry(0.18, 0.014, 0.36);
  const restPadMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, roughness: 0.5 });
  const restPad = new THREE.Mesh(restPadGeo, restPadMat);
  restPad.position.y = 0.007;
  g.add(restPad);

  // Pipette Glass Stem resting horizontally on the pad
  const stemGeo = new THREE.CylinderGeometry(0.007, 0.007, 0.30, 12);
  const stem = new THREE.Mesh(stemGeo, glassMat);
  stem.rotation.x = Math.PI / 2;
  stem.position.set(0, 0.02, 0.02);
  g.add(stem);

  // Pipette Suction Bulb
  const bulbGeo = new THREE.SphereGeometry(0.028, 14, 14);
  const bulbMat = new THREE.MeshStandardMaterial({ color: 0xdc2626, roughness: 0.6 });
  const bulb = new THREE.Mesh(bulbGeo, bulbMat);
  bulb.position.set(0, 0.025, -0.14);
  g.add(bulb);

  return g;
}

// ---------------------------------------------------------------------------
// Indicator Bottles (Phenolphthalein, Methyl Orange, Bromothymol Blue)
// ---------------------------------------------------------------------------
function buildIndicatorBottles(id) {
  const g = new THREE.Group();

  const colors = [0xec4899, 0xf97316, 0x3b82f6]; // pink, orange, blue
  for (let i = 0; i < 3; i++) {
    const bGroup = new THREE.Group();
    bGroup.position.set((i - 1) * 0.14, 0, 0);

    const botGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.12, 16);
    const bot = new THREE.Mesh(botGeo, glassMat);
    bot.position.y = 0.06;
    bGroup.add(bot);

    const liqGeo = new THREE.CylinderGeometry(0.036, 0.036, 0.08, 16);
    const liqMat = new THREE.MeshStandardMaterial({ color: colors[i], transparent: true, opacity: 0.7 });
    const liq = new THREE.Mesh(liqGeo, liqMat);
    liq.position.y = 0.05;
    bGroup.add(liq);

    // Dropper cap
    const capGeo = new THREE.CylinderGeometry(0.02, 0.02, 0.04, 12);
    const cap = new THREE.Mesh(capGeo, plasticMat);
    cap.position.y = 0.14;
    bGroup.add(cap);

    g.add(bGroup);
  }

  return g;
}

// ---------------------------------------------------------------------------
// Reagent Bottles (Acid & Base)
// ---------------------------------------------------------------------------
function buildReagentBottles(id, type) {
  const g = new THREE.Group();

  const isAcid = type === 'acid';
  const botMat = isAcid
    ? new THREE.MeshStandardMaterial({ color: 0x78350f, roughness: 0.3 }) // amber glass
    : new THREE.MeshStandardMaterial({ color: 0xf1f5f9, roughness: 0.4 }); // white HDPE

  const botGeo = new THREE.CylinderGeometry(0.07, 0.07, 0.24, 20);
  const bot = new THREE.Mesh(botGeo, botMat);
  bot.position.y = 0.12;
  g.add(bot);

  const capGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.04, 16);
  const cap = new THREE.Mesh(capGeo, plasticMat);
  cap.position.y = 0.26;
  g.add(cap);

  return g;
}

// ---------------------------------------------------------------------------
// Digital pH Meter
// ---------------------------------------------------------------------------
function buildPhMeter(id) {
  const g = new THREE.Group();

  const bodyGeo = new THREE.BoxGeometry(0.24, 0.08, 0.22);
  const body = new THREE.Mesh(bodyGeo, plasticMat);
  body.position.y = 0.04;
  g.add(body);

  // Digital Display Canvas
  const canvas = document.createElement('canvas');
  canvas.width = 128;
  canvas.height = 64;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#0f172a';
  ctx.fillRect(0, 0, 128, 64);
  ctx.fillStyle = '#34d399';
  ctx.font = 'bold 26px monospace';
  ctx.textAlign = 'center';
  ctx.fillText('pH 7.00', 64, 42);

  const tex = new THREE.CanvasTexture(canvas);
  const screenGeo = new THREE.PlaneGeometry(0.16, 0.08);
  const screenMat = new THREE.MeshBasicMaterial({ map: tex });
  const screen = new THREE.Mesh(screenGeo, screenMat);
  screen.position.set(0, 0.085, 0.04);
  screen.rotation.x = -Math.PI / 6;
  g.add(screen);

  // Electrode arm & probe
  const armGeo = new THREE.CylinderGeometry(0.008, 0.008, 0.25, 8);
  const arm = new THREE.Mesh(armGeo, metalMat);
  arm.position.set(0.16, 0.14, 0);
  g.add(arm);

  const probeGeo = new THREE.CylinderGeometry(0.006, 0.006, 0.14, 8);
  const probe = new THREE.Mesh(probeGeo, glassMat);
  probe.position.set(0.16, 0.04, 0.1);
  g.add(probe);

  g.userData.canvas = canvas;
  g.userData.ctx = ctx;
  g.userData.tex = tex;

  return g;
}

// ---------------------------------------------------------------------------
// Squeeze Wash Bottle
// ---------------------------------------------------------------------------
function buildWashBottle(id) {
  const g = new THREE.Group();

  const botGeo = new THREE.CylinderGeometry(0.06, 0.06, 0.2, 16);
  const botMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.6, transparent: true, opacity: 0.6 });
  const bot = new THREE.Mesh(botGeo, botMat);
  bot.position.y = 0.1;
  g.add(bot);

  // Spout tube
  const curve = new THREE.QuadraticBezierCurve3(
    new THREE.Vector3(0, 0.2, 0),
    new THREE.Vector3(0, 0.28, 0.06),
    new THREE.Vector3(0, 0.25, 0.12)
  );
  const spoutGeo = new THREE.TubeGeometry(curve, 12, 0.006, 8, false);
  const spout = new THREE.Mesh(spoutGeo, plasticMat);
  g.add(spout);

  return g;
}

// ---------------------------------------------------------------------------
// Wall Ward Clock
// ---------------------------------------------------------------------------
function buildWardClock(id) {
  const g = new THREE.Group();

  const faceGeo = new THREE.BoxGeometry(0.8, 0.35, 0.05);
  const face = new THREE.Mesh(faceGeo, plasticMat);
  g.add(face);

  const canvas = document.createElement('canvas');
  canvas.width = 256;
  canvas.height = 112;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#020617';
  ctx.fillRect(0, 0, 256, 112);
  ctx.fillStyle = '#f59e0b';
  ctx.font = 'bold 44px monospace';
  ctx.textAlign = 'center';
  ctx.fillText('00:00 h', 128, 70);

  const tex = new THREE.CanvasTexture(canvas);
  const screenGeo = new THREE.PlaneGeometry(0.72, 0.28);
  const screenMat = new THREE.MeshBasicMaterial({ map: tex });
  const screen = new THREE.Mesh(screenGeo, screenMat);
  screen.position.z = 0.028;
  g.add(screen);

  g.userData.canvas = canvas;
  g.userData.ctx = ctx;
  g.userData.tex = tex;

  return g;
}

function buildLabelPen(id) {
  const g = new THREE.Group();
  const penGeo = new THREE.CylinderGeometry(0.008, 0.008, 0.15, 8);
  const pen = new THREE.Mesh(penGeo, plasticMat);
  pen.rotation.z = Math.PI / 2;
  pen.position.y = 0.008;
  g.add(pen);
  return g;
}
