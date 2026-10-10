/**
 * Procedural Laboratory Architecture & Room Builder (frontend/lab/world/room.js)
 * Constructs a bright, clean, modern laboratory room, workbenches, lighting,
 * high-contrast whiteboard, and safety equipment.
 */

import * as THREE from 'three';

export function buildLabRoom(scene) {
  const roomGroup = new THREE.Group();
  roomGroup.name = 'laboratory_room';

  // 1. Materials for a bright, clean, modern laboratory
  const floorMat = new THREE.MeshStandardMaterial({
    color: 0xdbe3ed, // Light grey clean epoxy/tile floor
    roughness: 0.35,
    metalness: 0.05,
  });

  const wallMat = new THREE.MeshStandardMaterial({
    color: 0xf3f6f9, // Bright off-white / light-grey clean lab walls
    roughness: 0.85,
    metalness: 0.02,
  });

  const trimMat = new THREE.MeshStandardMaterial({
    color: 0x64748b, // Clean slate baseboards
    roughness: 0.5,
    metalness: 0.2,
  });

  const counterMat = new THREE.MeshStandardMaterial({
    color: 0x1e293b, // Chemical-resistant dark phenolic resin worktop
    roughness: 0.28,
    metalness: 0.25,
  });

  const frameMat = new THREE.MeshStandardMaterial({
    color: 0xe2e8f0, // Clean white/light-grey powder-coated metal legs
    roughness: 0.4,
    metalness: 0.3,
  });

  // 2. Floor (18m x 16m)
  const floorGeo = new THREE.PlaneGeometry(18, 16);
  const floor = new THREE.Mesh(floorGeo, floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  roomGroup.add(floor);

  // 3. Walls (Back wall at z = -7, Left wall at x = -8, Right wall at x = 8)
  const wallGeo = new THREE.PlaneGeometry(18, 5.2);
  const backWall = new THREE.Mesh(wallGeo, wallMat);
  backWall.position.set(0, 2.6, -7);
  backWall.receiveShadow = true;
  roomGroup.add(backWall);

  const sideWallGeo = new THREE.PlaneGeometry(16, 5.2);
  const leftWall = new THREE.Mesh(sideWallGeo, wallMat);
  leftWall.position.set(-8, 2.6, 0);
  leftWall.rotation.y = Math.PI / 2;
  leftWall.receiveShadow = true;
  roomGroup.add(leftWall);

  const rightWall = new THREE.Mesh(sideWallGeo, wallMat);
  rightWall.position.set(8, 2.6, 0);
  rightWall.rotation.y = -Math.PI / 2;
  rightWall.receiveShadow = true;
  roomGroup.add(rightWall);

  // Ceiling Plane (White reflective ceiling)
  const ceilingGeo = new THREE.PlaneGeometry(18, 16);
  const ceilingMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.9 });
  const ceiling = new THREE.Mesh(ceilingGeo, ceilingMat);
  ceiling.position.set(0, 5.0, 0);
  ceiling.rotation.x = Math.PI / 2;
  roomGroup.add(ceiling);

  // Wall Baseboards/Trims
  const trimGeo = new THREE.BoxGeometry(18, 0.15, 0.08);
  const backTrim = new THREE.Mesh(trimGeo, trimMat);
  backTrim.position.set(0, 0.075, -6.95);
  roomGroup.add(backTrim);

  const leftTrimGeo = new THREE.BoxGeometry(0.08, 0.15, 16);
  const leftTrim = new THREE.Mesh(leftTrimGeo, trimMat);
  leftTrim.position.set(-7.95, 0.075, 0);
  roomGroup.add(leftTrim);

  const rightTrim = new THREE.Mesh(leftTrimGeo, trimMat);
  rightTrim.position.set(7.95, 0.075, 0);
  roomGroup.add(rightTrim);

  // 4. Ceiling Light Troffer Panels (Emissive soft cool-white)
  createCeilingLights(roomGroup);

  // 5. Laboratory Workbenches (Bench height 0.9m + 0.08m top = 0.94m working surface)
  // Center Bench A (Titration & Analysis Station - compact, unobstructed)
  createBench(roomGroup, counterMat, frameMat, 0, 0, -2.0, 4.4, 1.4, 0.9);

  // Left Bench B (Weighing & Reagent Preparation)
  createBench(roomGroup, counterMat, frameMat, -4.5, 0, -4.2, 4.0, 1.4, 0.9);

  // Right Clinical Ward Bay: Clear floor area for Patient Bed, bedside vitals monitor & avatar

  // 6. Whiteboard on Back Wall (High contrast, crisp text)
  createWhiteboard(roomGroup, 0, 2.8, -6.9);

  // 7. Safety Wall Fixtures (Wall & floor mounted, nothing floats!)
  createEyewashStation(roomGroup, -7.85, 1.4, -3.5);
  createFireExtinguisher(roomGroup, -7.85, 1.2, 1.5);
  createSafetyPoster(roomGroup, 7.85, 2.5, -2);
  createLabDoor(roomGroup, 7.85, 1.8, 3.5);

  // 8. Optimized Laboratory Lighting (High performance & realistic PBR)
  // Ambient & sky/floor diffuse fill via HemisphereLight (0 shadow passes, high efficiency)
  const hemiLight = new THREE.HemisphereLight(0xffffff, 0xcfd8dc, 1.8);
  hemiLight.position.set(0, 6, 0);
  roomGroup.add(hemiLight);

  // Key Overhead Directional Sun / Fixture Light with tight shadow bounds (Single shadow caster)
  const dirLight = new THREE.DirectionalLight(0xffffff, 2.2);
  dirLight.position.set(3, 8, 4);
  dirLight.castShadow = true;
  dirLight.shadow.mapSize.width = 1024;
  dirLight.shadow.mapSize.height = 1024;
  dirLight.shadow.camera.near = 1.5;
  dirLight.shadow.camera.far = 18;
  dirLight.shadow.camera.left = -6.0;
  dirLight.shadow.camera.right = 6.0;
  dirLight.shadow.camera.top = 4.5;
  dirLight.shadow.camera.bottom = -4.5;
  dirLight.shadow.bias = -0.001;
  roomGroup.add(dirLight);

  // Single subtle overhead worktop PointLight focused over center bench
  const centerPoint = new THREE.PointLight(0xffffff, 8.0, 12, 2);
  centerPoint.position.set(0, 4.0, -2.0);
  roomGroup.add(centerPoint);

  // Emergency Alarm Beacon (Normally off; triggers pulsing on critical breaches)
  const alarmLight = new THREE.PointLight(0xef4444, 0, 18, 2);
  alarmLight.position.set(0, 4.5, -3.5);
  alarmLight.name = 'alarm_point_light';
  roomGroup.add(alarmLight);

  // Save light references for runtime quality adjustments
  roomGroup.userData.dirLight = dirLight;
  roomGroup.userData.alarmLight = alarmLight;

  scene.add(roomGroup);
  return roomGroup;
}

function createCeilingLights(parent) {
  const trofferMat = new THREE.MeshStandardMaterial({
    color: 0xffffff,
    emissive: 0xffffff,
    emissiveIntensity: 0.8,
    roughness: 0.2,
  });
  const borderMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, roughness: 0.4 });

  // Shared geometries
  const frameGeo = new THREE.BoxGeometry(2.4, 0.06, 0.9);
  const panelGeo = new THREE.PlaneGeometry(2.2, 0.75);

  const trofferPositions = [
    [-4.5, -4.0],
    [0.0, -4.0],
    [4.5, -4.0],
    [-4.5, -1.0],
    [0.0, -1.0],
    [4.5, -1.0],
    [0.0, 2.5],
  ];

  for (const [tx, tz] of trofferPositions) {
    const fixture = new THREE.Group();
    fixture.position.set(tx, 4.95, tz);

    const frame = new THREE.Mesh(frameGeo, borderMat);
    const panel = new THREE.Mesh(panelGeo, trofferMat);
    panel.rotation.x = Math.PI / 2;
    panel.position.y = -0.035;

    fixture.add(frame);
    fixture.add(panel);
    parent.add(fixture);
  }
}

function createBench(parent, topMat, legMat, x, y, z, width, depth, height) {
  const bench = new THREE.Group();
  bench.position.set(x, y, z);

  // Dark chemical-resistant top surface
  const topGeo = new THREE.BoxGeometry(width, 0.08, depth);
  const topMesh = new THREE.Mesh(topGeo, topMat);
  topMesh.position.y = height;
  topMesh.castShadow = true;
  topMesh.receiveShadow = true;
  bench.add(topMesh);

  // 4 Powder-coated metal legs (castShadow turned off for props to optimize shadow rendering)
  const legGeo = new THREE.BoxGeometry(0.08, height, 0.08);
  const dx = width / 2 - 0.12;
  const dz = depth / 2 - 0.12;

  for (const lx of [-dx, dx]) {
    for (const lz of [-dz, dz]) {
      const leg = new THREE.Mesh(legGeo, legMat);
      leg.position.set(lx, height / 2, lz);
      bench.add(leg);
    }
  }

  // Cross structural brace
  const braceGeo = new THREE.BoxGeometry(width - 0.24, 0.05, 0.05);
  const brace = new THREE.Mesh(braceGeo, legMat);
  brace.position.set(0, 0.25, 0);
  bench.add(brace);

  parent.add(bench);
}

function createWhiteboard(parent, x, y, z) {
  const board = new THREE.Group();
  board.position.set(x, y, z);

  // Frame
  const frameGeo = new THREE.BoxGeometry(4.4, 2.3, 0.06);
  const frameMat = new THREE.MeshStandardMaterial({ color: 0x64748b, metalness: 0.8, roughness: 0.2 });
  const frame = new THREE.Mesh(frameGeo, frameMat);
  board.add(frame);

  // High-Resolution Crisp Canvas Whiteboard Surface (2048x1024)
  const canvas = document.createElement('canvas');
  canvas.width = 2048;
  canvas.height = 1024;
  const ctx = canvas.getContext('2d');

  // Crisp White Background
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, 2048, 1024);

  // Header Bar
  ctx.fillStyle = '#0f172a';
  ctx.font = 'bold 74px sans-serif';
  ctx.fillText('ORBIS LAB PROTOCOLS & FORMULAS', 80, 115);

  // Section 1: Standard Protocols
  ctx.strokeStyle = '#9333ea';
  ctx.lineWidth = 8;
  ctx.strokeRect(80, 160, 910, 780);

  ctx.fillStyle = '#7e22ce';
  ctx.font = 'bold 50px sans-serif';
  ctx.fillText('SAFETY & TECHNIQUE RULES', 110, 235);

  ctx.font = 'bold 38px monospace';
  ctx.fillStyle = '#1e293b';
  ctx.fillText('1. WEAR PPE (Goggles, Gloves, Coat)', 110, 315);
  ctx.fillText('2. TARE BALANCE before weighing dose', 110, 405);
  ctx.fillText('3. ACID -> WATER dilution safety (R6)', 110, 495);
  ctx.fillText('4. RINSE BURETTE with titrant first', 110, 585);
  ctx.fillText('5. SORT CHEMICAL vs BIOHAZARD waste', 110, 675);
  ctx.fillText('6. WASH HANDS before report submit', 110, 765);

  // Section 2: Mathematical / Analytical Models
  ctx.strokeStyle = '#0284c7';
  ctx.lineWidth = 8;
  ctx.strokeRect(1030, 160, 930, 780);

  ctx.fillStyle = '#0369a1';
  ctx.font = 'bold 50px sans-serif';
  ctx.fillText('QUANTITATIVE MODELS', 1060, 235);

  ctx.font = 'bold 38px monospace';
  ctx.fillStyle = '#0f172a';
  ctx.fillText('PHARMACOKINETICS (Alex, 70kg):', 1060, 315);
  ctx.fillStyle = '#0284c7';
  ctx.fillText('C(t)=D*ka/(Vd*(ka-ke))*(e^-ke*t-e^-ka*t)', 1060, 375);

  ctx.fillStyle = '#0f172a';
  ctx.fillText('ACID-BASE NEUTRALIZATION:', 1060, 485);
  ctx.fillStyle = '#059669';
  ctx.fillText('HCl + NaOH -> NaCl + H2O', 1060, 545);
  ctx.fillText('Equivalence Point: pH 7.00', 1060, 605);

  ctx.fillStyle = '#0f172a';
  ctx.fillText('BUFFER EQUATION:', 1060, 715);
  ctx.fillStyle = '#d97706';
  ctx.fillText('pH = pKa + log([A-] / [HA])', 1060, 775);

  // Bottom prompt banner
  ctx.fillStyle = '#64748b';
  ctx.font = 'bold 32px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('🔍 CLICK PROTOCOL BOARD TO ZOOM & INSPECT', 1024, 985);
  ctx.textAlign = 'left';

  const texture = new THREE.CanvasTexture(canvas);
  texture.anisotropy = 8;
  const surfaceGeo = new THREE.PlaneGeometry(4.2, 2.1);
  const surfaceMat = new THREE.MeshBasicMaterial({ map: texture });
  const surface = new THREE.Mesh(surfaceGeo, surfaceMat);
  surface.position.z = 0.035;
  board.add(surface);

  board.userData.targetId = 'protocol_board';
  surface.userData.targetId = 'protocol_board';

  parent.add(board);
}

function createEyewashStation(parent, x, y, z) {
  const station = new THREE.Group();
  station.position.set(x, y, z);
  station.rotation.y = Math.PI / 2;

  const metalMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.85, roughness: 0.15 });
  const greenMat = new THREE.MeshStandardMaterial({ color: 0x10b981, roughness: 0.25 });
  const yellowMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, roughness: 0.3 });

  // 1. Heavy-duty wall bracket mounting directly into left wall (x = -8.0)
  const bracketGeo = new THREE.BoxGeometry(0.35, 0.45, 0.18);
  const bracket = new THREE.Mesh(bracketGeo, metalMat);
  bracket.position.set(0, 0, -0.15);
  station.add(bracket);

  // 2. Full vertical stainless-steel pedestal pipe running to the floor (y = 0.0)
  // Station root is at y = 1.4, so pedestal goes down 1.4m to floor
  const pedestalGeo = new THREE.CylinderGeometry(0.035, 0.035, 1.4, 16);
  const pedestal = new THREE.Mesh(pedestalGeo, metalMat);
  pedestal.position.set(0, -0.7, 0);
  station.add(pedestal);

  // Floor mounting flange plate
  const flangeGeo = new THREE.CylinderGeometry(0.16, 0.16, 0.03, 16);
  const flange = new THREE.Mesh(flangeGeo, metalMat);
  flange.position.set(0, -1.39, 0);
  station.add(flange);

  // 3. Eyewash safety bowl (Green)
  const bowlGeo = new THREE.CylinderGeometry(0.24, 0.16, 0.14, 20);
  const bowl = new THREE.Mesh(bowlGeo, greenMat);
  bowl.position.set(0, 0.07, 0);
  station.add(bowl);

  // Dual spray heads
  const headGeo = new THREE.CylinderGeometry(0.025, 0.025, 0.05, 12);
  for (const hx of [-0.06, 0.06]) {
    const head = new THREE.Mesh(headGeo, metalMat);
    head.position.set(hx, 0.12, 0);
    station.add(head);
  }

  // Yellow Push Flag Paddle
  const flagGeo = new THREE.BoxGeometry(0.02, 0.12, 0.14);
  const flag = new THREE.Mesh(flagGeo, yellowMat);
  flag.position.set(0.2, 0.08, 0);
  station.add(flag);

  parent.add(station);
}

function createFireExtinguisher(parent, x, y, z) {
  const ext = new THREE.Group();
  ext.position.set(x, y, z);
  ext.rotation.y = Math.PI / 2;

  const metalMat = new THREE.MeshStandardMaterial({ color: 0x64748b, metalness: 0.8, roughness: 0.2 });
  const redMat = new THREE.MeshStandardMaterial({ color: 0xdc2626, roughness: 0.3, metalness: 0.2 });

  // Wall mounting bracket
  const bracket = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.35, 0.08), metalMat);
  bracket.position.set(0, 0, -0.1);
  ext.add(bracket);

  // Tank Body
  const bodyGeo = new THREE.CylinderGeometry(0.11, 0.11, 0.55, 20);
  const body = new THREE.Mesh(bodyGeo, redMat);
  ext.add(body);

  const topGeo = new THREE.SphereGeometry(0.11, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2);
  const top = new THREE.Mesh(topGeo, redMat);
  top.position.y = 0.275;
  ext.add(top);

  // Handle and Valve
  const valve = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.1, 0.08), metalMat);
  valve.position.set(0, 0.38, 0);
  ext.add(valve);

  parent.add(ext);
}

function createSafetyPoster(parent, x, y, z) {
  const poster = new THREE.Group();
  poster.position.set(x, y, z);
  poster.rotation.y = -Math.PI / 2;

  // High-Resolution Safety Poster (512x680)
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 680;
  const ctx = canvas.getContext('2d');

  // Deep Navy Background with Gold Border
  ctx.fillStyle = '#0f172a';
  ctx.fillRect(0, 0, 512, 680);

  ctx.strokeStyle = '#f59e0b';
  ctx.lineWidth = 12;
  ctx.strokeRect(12, 12, 488, 656);

  ctx.fillStyle = '#f59e0b';
  ctx.font = 'bold 42px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('SAFETY FIRST', 256, 80);

  ctx.fillStyle = '#38bdf8';
  ctx.font = 'bold 26px sans-serif';
  ctx.fillText('ORBIS LAB PROTOCOLS', 256, 130);

  ctx.fillStyle = '#f8fafc';
  ctx.font = 'bold 24px sans-serif';
  ctx.textAlign = 'left';
  ctx.fillText('MANDATORY PPE BEFORE WORK:', 48, 200);

  ctx.font = '22px monospace';
  ctx.fillStyle = '#e2e8f0';
  ctx.fillText('• Eye Protection (R1 Goggles)', 60, 250);
  ctx.fillText('• Chemical Gloves (R2 Nitrile)', 60, 300);
  ctx.fillText('• Lab Coat Buttoned (R3 Coat)', 60, 350);
  ctx.fillText('• Wash Hands Prior to Exit', 60, 400);

  ctx.strokeStyle = '#ef4444';
  ctx.lineWidth = 4;
  ctx.strokeRect(40, 460, 432, 160);

  ctx.fillStyle = '#ef4444';
  ctx.font = 'bold 26px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('LAB SAFETY ENFORCEMENT', 256, 510);

  ctx.fillStyle = '#fca5a5';
  ctx.font = '20px monospace';
  ctx.fillText('2 CRITICAL BREACHES = FAIL', 256, 560);
  ctx.fillText('Report is recorded in run log', 256, 595);

  const texture = new THREE.CanvasTexture(canvas);
  texture.anisotropy = 4;
  const geo = new THREE.PlaneGeometry(1.2, 1.6);
  const mat = new THREE.MeshBasicMaterial({ map: texture });
  const mesh = new THREE.Mesh(geo, mat);
  poster.add(mesh);

  parent.add(poster);
}

function createLabDoor(parent, x, y, z) {
  const door = new THREE.Group();
  door.position.set(x, y, z);
  door.rotation.y = -Math.PI / 2;

  const doorMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.4, metalness: 0.3 });
  const doorGeo = new THREE.BoxGeometry(1.6, 2.8, 0.08);
  const doorMesh = new THREE.Mesh(doorGeo, doorMat);
  door.add(doorMesh);

  // Door Window
  const winGeo = new THREE.PlaneGeometry(0.6, 0.9);
  const winMat = new THREE.MeshStandardMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.7, roughness: 0.1 });
  const winMesh = new THREE.Mesh(winGeo, winMat);
  winMesh.position.set(0, 0.4, 0.045);
  door.add(winMesh);

  // Door Handle
  const handleMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, metalness: 0.9, roughness: 0.1 });
  const handle = new THREE.Mesh(new THREE.CylinderGeometry(0.015, 0.015, 0.25, 12), handleMat);
  handle.rotation.x = Math.PI / 2;
  handle.position.set(0.6, 0, 0.08);
  door.add(handle);

  parent.add(door);
}
