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
  backWall.userData.isWall = true;
  backWall.userData.camBlocker = true;
  roomGroup.add(backWall);

  const sideWallGeo = new THREE.PlaneGeometry(16, 5.2);
  const leftWall = new THREE.Mesh(sideWallGeo, wallMat);
  leftWall.position.set(-8, 2.6, 0);
  leftWall.rotation.y = Math.PI / 2;
  leftWall.receiveShadow = true;
  leftWall.userData.isWall = true;
  leftWall.userData.camBlocker = true;
  roomGroup.add(leftWall);

  const rightWall = new THREE.Mesh(sideWallGeo, wallMat);
  rightWall.position.set(8, 2.6, 0);
  rightWall.rotation.y = -Math.PI / 2;
  rightWall.receiveShadow = true;
  rightWall.userData.isWall = true;
  rightWall.userData.camBlocker = true;
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

  // 8. Lived-in Laboratory Features (Subway Tiles, Windows & Light Shafts, Reagent Shelves, Lockers, Fume Hood)
  createWallTiles(roomGroup);
  createWindowsWithLightShafts(roomGroup);
  createReagentShelves(roomGroup);
  createLockers(roomGroup);
  createFumeHood(roomGroup);

  // 9. Optimized Laboratory Lighting (High performance & realistic PBR)
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

  // Cozy warm accent point light over prep & weighing station
  const warmAccentLight = new THREE.PointLight(0xfef08a, 10.0, 9, 2);
  warmAccentLight.position.set(-4.5, 2.6, -3.8);
  warmAccentLight.name = 'warm_accent_light';
  roomGroup.add(warmAccentLight);

  // Emergency Alarm Beacon (Normally off; triggers pulsing on critical breaches)
  const alarmLight = new THREE.PointLight(0xef4444, 0, 18, 2);
  alarmLight.position.set(0, 4.5, -3.5);
  alarmLight.name = 'alarm_point_light';
  roomGroup.add(alarmLight);

  // Save light references for runtime quality adjustments
  roomGroup.userData.dirLight = dirLight;
  roomGroup.userData.alarmLight = alarmLight;
  roomGroup.userData.warmAccentLight = warmAccentLight;

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
  topMesh.userData.camBlocker = true;
  bench.userData.camBlocker = true;
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
  board.userData.camBlocker = true;

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

// ---------------------------------------------------------------------------
// Lived-In Laboratory Architecture Fixtures
// ---------------------------------------------------------------------------

let _cachedTileTexture = null;
function getOrCreateSubwayTileTexture() {
  if (_cachedTileTexture) return _cachedTileTexture;
  const canvas = document.createElement('canvas');
  canvas.width = 256;
  canvas.height = 256;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#f8fafc';
  ctx.fillRect(0, 0, 256, 256);

  ctx.strokeStyle = '#cbd5e1';
  ctx.lineWidth = 3;
  const tileW = 64;
  const tileH = 32;

  for (let y = 0; y <= 256; y += tileH) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(256, y);
    ctx.stroke();

    const row = Math.floor(y / tileH);
    const offset = (row % 2) * (tileW / 2);
    for (let x = offset; x <= 256 + tileW; x += tileW) {
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(x, y + tileH);
      ctx.stroke();
    }
  }

  const tex = new THREE.CanvasTexture(canvas);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(8, 2.5);
  _cachedTileTexture = tex;
  return tex;
}

function createWallTiles(parent) {
  const tileMat = new THREE.MeshStandardMaterial({
    map: getOrCreateSubwayTileTexture(),
    roughness: 0.3,
    metalness: 0.05,
  });

  // Back wall wainscot (height 1.8m)
  const backGeo = new THREE.PlaneGeometry(18, 1.8);
  const backTiles = new THREE.Mesh(backGeo, tileMat);
  backTiles.position.set(0, 0.9, -6.98);
  backTiles.receiveShadow = true;
  parent.add(backTiles);

  // Left wall wainscot
  const leftGeo = new THREE.PlaneGeometry(16, 1.8);
  const leftTiles = new THREE.Mesh(leftGeo, tileMat);
  leftTiles.position.set(-7.98, 0.9, 0);
  leftTiles.rotation.y = Math.PI / 2;
  leftTiles.receiveShadow = true;
  parent.add(leftTiles);

  // Right wall wainscot
  const rightTiles = new THREE.Mesh(leftGeo, tileMat);
  rightTiles.position.set(7.98, 0.9, 0);
  rightTiles.rotation.y = -Math.PI / 2;
  rightTiles.receiveShadow = true;
  parent.add(rightTiles);

  // Decorative top wainscot capping rail
  const railMat = new THREE.MeshStandardMaterial({ color: 0x475569, roughness: 0.4 });
  const railGeo = new THREE.BoxGeometry(18, 0.05, 0.06);
  const backRail = new THREE.Mesh(railGeo, railMat);
  backRail.position.set(0, 1.82, -6.96);
  parent.add(backRail);
}

function createWindowsWithLightShafts(parent) {
  const winGroup = new THREE.Group();
  winGroup.position.set(-7.95, 3.2, 0);
  winGroup.rotation.y = Math.PI / 2;

  // Sky Backdrop outside window
  const skyGeo = new THREE.PlaneGeometry(6.4, 2.8);
  const skyMat = new THREE.MeshBasicMaterial({ color: 0x93c5fd });
  const sky = new THREE.Mesh(skyGeo, skyMat);
  sky.position.set(0, 0, -0.06);
  winGroup.add(sky);

  // Window Panes Frame (White powder-coated aluminum)
  const frameMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3 });
  const outerFrame = new THREE.Mesh(new THREE.BoxGeometry(6.2, 2.6, 0.08), frameMat);
  winGroup.add(outerFrame);

  // Glass panes
  const glassMat = new THREE.MeshPhysicalMaterial({
    color: 0xffffff,
    transparent: true,
    opacity: 0.35,
    roughness: 0.05,
    transmission: 0.85,
    ior: 1.5,
  });
  const glass = new THREE.Mesh(new THREE.PlaneGeometry(6.0, 2.4), glassMat);
  glass.position.set(0, 0, 0.01);
  winGroup.add(glass);

  // Window mullions (muntin bars)
  const mullionMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.5 });
  for (let x of [-2.0, 0, 2.0]) {
    const bar = new THREE.Mesh(new THREE.BoxGeometry(0.06, 2.4, 0.09), mullionMat);
    bar.position.set(x, 0, 0.02);
    winGroup.add(bar);
  }
  const hBar = new THREE.Mesh(new THREE.BoxGeometry(6.0, 0.06, 0.09), mullionMat);
  hBar.position.set(0, 0, 0.02);
  winGroup.add(hBar);

  // Volumetric Soft Light Shaft (Tapered polygon angling down towards center)
  const beamGeo = new THREE.CylinderGeometry(1.6, 3.4, 5.5, 16, 1, true);
  const beamMat = new THREE.MeshBasicMaterial({
    color: 0xbae6fd,
    transparent: true,
    opacity: 0.12,
    blending: THREE.AdditiveBlending,
    side: THREE.DoubleSide,
    depthWrite: false,
  });
  const lightShaft = new THREE.Mesh(beamGeo, beamMat);
  lightShaft.rotation.x = Math.PI / 4.2;
  lightShaft.rotation.z = -Math.PI / 6;
  lightShaft.position.set(0, -1.8, 2.4);
  winGroup.add(lightShaft);

  parent.add(winGroup);
}

function createReagentShelves(parent) {
  const shelfGroup = new THREE.Group();
  shelfGroup.position.set(-2.2, 2.5, -6.92);

  const bracketMat = new THREE.MeshStandardMaterial({ color: 0x64748b, metalness: 0.8, roughness: 0.3 });
  const woodMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.4 });

  // 2 Shelves
  for (let y of [0, 0.55]) {
    const shelf = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.035, 0.28), woodMat);
    shelf.position.set(0, y, 0.14);
    shelf.castShadow = true;
    shelfGroup.add(shelf);

    // Shelf brackets
    for (let x of [-1.0, 0, 1.0]) {
      const b = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.18, 0.26), bracketMat);
      b.position.set(x, y - 0.09, 0.13);
      shelfGroup.add(b);
    }
  }

  // Colorful labeled reagent bottles on shelves
  const bottleColors = [0xd97706, 0x2563eb, 0x0d9488, 0x7c3aed, 0x059669, 0xd97706, 0x2563eb, 0x0284c7];
  const labelMat = new THREE.MeshBasicMaterial({ color: 0xffffff });

  let idx = 0;
  for (let y of [0.02, 0.57]) {
    for (let x = -0.95; x <= 0.95; x += 0.38) {
      const col = bottleColors[idx % bottleColors.length];
      idx++;
      const botMat = new THREE.MeshStandardMaterial({
        color: col,
        roughness: 0.15,
        transparent: true,
        opacity: 0.85,
      });

      const bMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 0.16, 16), botMat);
      bMesh.position.set(x, y + 0.08, 0.14);
      bMesh.castShadow = true;
      shelfGroup.add(bMesh);

      // White paper label strip
      const lbl = new THREE.Mesh(new THREE.CylinderGeometry(0.046, 0.046, 0.07, 16, 1, true), labelMat);
      lbl.position.set(x, y + 0.08, 0.14);
      shelfGroup.add(lbl);

      // Black cap
      const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.035, 16), bracketMat);
      cap.position.set(x, y + 0.17, 0.14);
      shelfGroup.add(cap);
    }
  }

  parent.add(shelfGroup);
}

function createLockers(parent) {
  const lockersGroup = new THREE.Group();
  lockersGroup.position.set(7.92, 1.25, -0.6);
  lockersGroup.rotation.y = -Math.PI / 2;

  const lockerMat = new THREE.MeshStandardMaterial({
    color: 0x0f766e, // Stylized brand teal lockers
    roughness: 0.45,
    metalness: 0.3,
  });
  const handleMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, metalness: 0.9, roughness: 0.1 });
  const ventMat = new THREE.MeshBasicMaterial({ color: 0x134e4a });

  // 3 Lockers in a row
  for (let i = -1; i <= 1; i++) {
    const x = i * 0.48;
    const body = new THREE.Mesh(new THREE.BoxGeometry(0.46, 2.1, 0.52), lockerMat);
    body.position.set(x, 0, 0.26);
    body.castShadow = true;
    lockersGroup.add(body);

    // Handle
    const h = new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.12, 0.03), handleMat);
    h.position.set(x + 0.16, 0.05, 0.54);
    lockersGroup.add(h);

    // Ventilation louvers / slits
    for (let v = 0; v < 3; v++) {
      const vent = new THREE.Mesh(new THREE.BoxGeometry(0.24, 0.015, 0.005), ventMat);
      vent.position.set(x, 0.85 - v * 0.035, 0.525);
      lockersGroup.add(vent);
    }
  }

  parent.add(lockersGroup);
}

function createFumeHood(parent) {
  const hoodGroup = new THREE.Group();
  hoodGroup.position.set(4.2, 0, -6.85);

  const bodyMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, roughness: 0.3, metalness: 0.2 });
  const sashGlassMat = new THREE.MeshPhysicalMaterial({
    color: 0x38bdf8,
    transparent: true,
    opacity: 0.35,
    roughness: 0.05,
    transmission: 0.85,
    ior: 1.5,
  });
  const worktopMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.25 });
  const ductMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.8, roughness: 0.2 });

  // Base cabinet (1.6m wide, 0.9m tall, 0.9m deep)
  const base = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.9, 0.85), bodyMat);
  base.position.set(0, 0.45, 0.425);
  base.castShadow = true;
  hoodGroup.add(base);

  // Black phenolic workbed inside
  const bed = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.05, 0.8), worktopMat);
  bed.position.set(0, 0.925, 0.425);
  hoodGroup.add(bed);

  // Upper hood canopy & side walls
  const leftWall = new THREE.Mesh(new THREE.BoxGeometry(0.06, 1.4, 0.85), bodyMat);
  leftWall.position.set(-0.77, 1.65, 0.425);
  hoodGroup.add(leftWall);

  const rightWall = new THREE.Mesh(new THREE.BoxGeometry(0.06, 1.4, 0.85), bodyMat);
  rightWall.position.set(0.77, 1.65, 0.425);
  hoodGroup.add(rightWall);

  const topCanopy = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.4, 0.85), bodyMat);
  topCanopy.position.set(0, 2.15, 0.425);
  topCanopy.castShadow = true;
  hoodGroup.add(topCanopy);

  // Transparent Sliding Sash Glass
  const sash = new THREE.Mesh(new THREE.PlaneGeometry(1.48, 0.75), sashGlassMat);
  sash.position.set(0, 1.45, 0.84);
  hoodGroup.add(sash);

  // Interior overhead light (clean cool white glow)
  const interiorLight = new THREE.PointLight(0xecfeff, 3.5, 3.5, 2);
  interiorLight.position.set(0, 2.05, 0.45);
  hoodGroup.add(interiorLight);

  // Stainless exhaust ventilation duct extending through ceiling
  const duct = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.18, 2.6, 20), ductMat);
  duct.position.set(0, 3.6, 0.425);
  hoodGroup.add(duct);

  parent.add(hoodGroup);
}
