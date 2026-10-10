/**
 * Procedural Laboratory Architecture & Room Builder (frontend/lab/world/room.js)
 * Constructs the 3D room, benches, wall apparatus, lighting, and safety fixtures.
 */

import * as THREE from 'three';

export function buildLabRoom(scene) {
  const roomGroup = new THREE.Group();
  roomGroup.name = 'laboratory_room';

  // 1. Materials (Reused for performance)
  const floorMat = new THREE.MeshStandardMaterial({
    color: 0x120c24,
    roughness: 0.35,
    metalness: 0.15,
  });

  const wallMat = new THREE.MeshStandardMaterial({
    color: 0x1a1236,
    roughness: 0.8,
    metalness: 0.05,
  });

  const trimMat = new THREE.MeshStandardMaterial({
    color: 0x31205a,
    roughness: 0.4,
    metalness: 0.4,
  });

  const counterMat = new THREE.MeshStandardMaterial({
    color: 0x0f172a, // dark phenolic resin
    roughness: 0.25,
    metalness: 0.3,
  });

  const frameMat = new THREE.MeshStandardMaterial({
    color: 0x221742,
    roughness: 0.5,
    metalness: 0.6,
  });

  // 2. Floor (16m x 14m)
  const floorGeo = new THREE.PlaneGeometry(18, 16);
  const floor = new THREE.Mesh(floorGeo, floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  roomGroup.add(floor);

  // Floor Grid Overlay
  const gridHelper = new THREE.GridHelper(18, 18, 0x9333ea, 0x2e1065);
  gridHelper.position.y = 0.01;
  gridHelper.material.opacity = 0.35;
  gridHelper.material.transparent = true;
  roomGroup.add(gridHelper);

  // 3. Walls (Back wall at z = -7, Left wall at x = -8, Right wall at x = 8)
  const wallGeo = new THREE.PlaneGeometry(18, 5);
  const backWall = new THREE.Mesh(wallGeo, wallMat);
  backWall.position.set(0, 2.5, -7);
  backWall.receiveShadow = true;
  roomGroup.add(backWall);

  const sideWallGeo = new THREE.PlaneGeometry(16, 5);
  const leftWall = new THREE.Mesh(sideWallGeo, wallMat);
  leftWall.position.set(-8, 2.5, 0);
  leftWall.rotation.y = Math.PI / 2;
  leftWall.receiveShadow = true;
  roomGroup.add(leftWall);

  const rightWall = new THREE.Mesh(sideWallGeo, wallMat);
  rightWall.position.set(8, 2.5, 0);
  rightWall.rotation.y = -Math.PI / 2;
  rightWall.receiveShadow = true;
  roomGroup.add(rightWall);

  // Wall Baseboards/Trims
  const trimGeo = new THREE.BoxGeometry(18, 0.15, 0.08);
  const backTrim = new THREE.Mesh(trimGeo, trimMat);
  backTrim.position.set(0, 0.075, -6.95);
  roomGroup.add(backTrim);

  // 4. Laboratory Workbenches
  // Center Bench A (Titration & Analysis Station)
  createBench(roomGroup, counterMat, frameMat, 0, 0, -2, 5.5, 1.6, 0.9);

  // Left Bench B (Weighing & Reagent Preparation)
  createBench(roomGroup, counterMat, frameMat, -4.5, 0, -4.2, 4.0, 1.4, 0.9);

  // Right Ward Station (Patient Bed area or secondary bench)
  createBench(roomGroup, counterMat, frameMat, 4.5, 0, -4.2, 4.0, 1.4, 0.9);

  // 5. Whiteboard on Back Wall
  createWhiteboard(roomGroup, 0, 2.8, -6.9);

  // 6. Safety Wall Fixtures
  createEyewashStation(roomGroup, -7.8, 1.6, -3.5);
  createFireExtinguisher(roomGroup, -7.8, 1.2, 1.5);
  createSafetyPoster(roomGroup, 7.85, 2.5, -2);
  createLabDoor(roomGroup, 7.85, 1.8, 3.5);

  // 7. Lighting
  // Ambient fill
  const ambLight = new THREE.AmbientLight(0x2a1b4e, 1.8);
  roomGroup.add(ambLight);

  // Key Overhead Directional Light (casts soft shadows)
  const dirLight = new THREE.DirectionalLight(0xfff5ea, 2.2);
  dirLight.position.set(4, 7, 3);
  dirLight.castShadow = true;
  dirLight.shadow.mapSize.width = 1024;
  dirLight.shadow.mapSize.height = 1024;
  dirLight.shadow.camera.near = 1;
  dirLight.shadow.camera.far = 18;
  dirLight.shadow.camera.left = -9;
  dirLight.shadow.camera.right = 9;
  dirLight.shadow.camera.top = 9;
  dirLight.shadow.camera.bottom = -9;
  dirLight.shadow.bias = -0.001;
  roomGroup.add(dirLight);

  // Cool Cyan Point Fill (modern lab aesthetic)
  const cyanFill = new THREE.PointLight(0x06b6d4, 1.4, 12);
  cyanFill.position.set(-3, 3.5, -2);
  roomGroup.add(cyanFill);

  // Warm Magenta Accent Light
  const magFill = new THREE.PointLight(0xec4899, 1.2, 12);
  magFill.position.set(3, 3.5, -2);
  roomGroup.add(magFill);

  // Alarm Beacon Light (normally off or very dim; pulsed on critical violations)
  const alarmLight = new THREE.PointLight(0xef4444, 0, 15);
  alarmLight.position.set(0, 4.2, -4);
  alarmLight.name = 'alarm_point_light';
  roomGroup.add(alarmLight);

  scene.add(roomGroup);
  return roomGroup;
}

function createBench(parent, topMat, legMat, x, y, z, width, depth, height) {
  const bench = new THREE.Group();
  bench.position.set(x, y, z);

  // Top Surface
  const topGeo = new THREE.BoxGeometry(width, 0.08, depth);
  const topMesh = new THREE.Mesh(topGeo, topMat);
  topMesh.position.y = height;
  topMesh.castShadow = true;
  topMesh.receiveShadow = true;
  bench.add(topMesh);

  // 4 Legs / Metal Frame
  const legGeo = new THREE.BoxGeometry(0.06, height, 0.06);
  const dx = width / 2 - 0.1;
  const dz = depth / 2 - 0.1;

  for (const lx of [-dx, dx]) {
    for (const lz of [-dz, dz]) {
      const leg = new THREE.Mesh(legGeo, legMat);
      leg.position.set(lx, height / 2, lz);
      leg.castShadow = true;
      bench.add(leg);
    }
  }

  // Cross brace
  const braceGeo = new THREE.BoxGeometry(width - 0.2, 0.04, 0.04);
  const brace = new THREE.Mesh(braceGeo, legMat);
  brace.position.set(0, 0.25, 0);
  bench.add(brace);

  parent.add(bench);
}

function createWhiteboard(parent, x, y, z) {
  const board = new THREE.Group();
  board.position.set(x, y, z);

  // Frame
  const frameGeo = new THREE.BoxGeometry(4.2, 2.2, 0.05);
  const frameMat = new THREE.MeshStandardMaterial({ color: 0x475569, metalness: 0.8, roughness: 0.2 });
  const frame = new THREE.Mesh(frameGeo, frameMat);
  board.add(frame);

  // Canvas Whiteboard Surface
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 256;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#f8fafc';
  ctx.fillRect(0, 0, 512, 256);

  ctx.fillStyle = '#0f172a';
  ctx.font = 'bold 18px sans-serif';
  ctx.fillText('ORBIS LAB PROTOCOLS', 24, 38);

  ctx.strokeStyle = '#9333ea';
  ctx.lineWidth = 2;
  ctx.strokeRect(20, 52, 220, 180);

  ctx.font = '13px monospace';
  ctx.fillStyle = '#334155';
  ctx.fillText('1. WEAR PPE (R1-R3)', 32, 80);
  ctx.fillText('2. TARE BALANCE (R4)', 32, 105);
  ctx.fillText('3. ACID -> WATER (R6)', 32, 130);
  ctx.fillText('4. RINSE BURETTE (R7)', 32, 155);
  ctx.fillText('5. SORT WASTE (R9)', 32, 180);

  // Mathematical diagram
  ctx.fillStyle = '#0284c7';
  ctx.fillText('C(t) = D*ka/(Vd*(ka-ke))', 260, 80);
  ctx.fillText('HCl + NaOH -> NaCl + H2O', 260, 110);
  ctx.fillText('Equivalence: pH 7.00', 260, 140);
  ctx.fillText('Buffer: pH = pKa + log([A-]/[HA])', 260, 170);

  const texture = new THREE.CanvasTexture(canvas);
  const surfaceGeo = new THREE.PlaneGeometry(4.0, 2.0);
  const surfaceMat = new THREE.MeshBasicMaterial({ map: texture });
  const surface = new THREE.Mesh(surfaceGeo, surfaceMat);
  surface.position.z = 0.03;
  board.add(surface);

  parent.add(board);
}

function createEyewashStation(parent, x, y, z) {
  const station = new THREE.Group();
  station.position.set(x, y, z);
  station.rotation.y = Math.PI / 2;

  const bowlGeo = new THREE.CylinderGeometry(0.2, 0.15, 0.12, 16);
  const greenMat = new THREE.MeshStandardMaterial({ color: 0x10b981, roughness: 0.3 });
  const bowl = new THREE.Mesh(bowlGeo, greenMat);
  station.add(bowl);

  const pipeGeo = new THREE.CylinderGeometry(0.02, 0.02, 0.4, 8);
  const metalMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.9, roughness: 0.1 });
  const pipe = new THREE.Mesh(pipeGeo, metalMat);
  pipe.position.y = -0.22;
  station.add(pipe);

  parent.add(station);
}

function createFireExtinguisher(parent, x, y, z) {
  const ext = new THREE.Group();
  ext.position.set(x, y, z);
  ext.rotation.y = Math.PI / 2;

  const bodyGeo = new THREE.CylinderGeometry(0.1, 0.1, 0.5, 16);
  const redMat = new THREE.MeshStandardMaterial({ color: 0xdc2626, roughness: 0.3, metalness: 0.2 });
  const body = new THREE.Mesh(bodyGeo, redMat);
  ext.add(body);

  const topGeo = new THREE.SphereGeometry(0.1, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2);
  const top = new THREE.Mesh(topGeo, redMat);
  top.position.y = 0.25;
  ext.add(top);

  parent.add(ext);
}

function createSafetyPoster(parent, x, y, z) {
  const poster = new THREE.Group();
  poster.position.set(x, y, z);
  poster.rotation.y = -Math.PI / 2;

  const canvas = document.createElement('canvas');
  canvas.width = 256;
  canvas.height = 340;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#1e1b4b';
  ctx.fillRect(0, 0, 256, 340);

  ctx.strokeStyle = '#f59e0b';
  ctx.lineWidth = 6;
  ctx.strokeRect(6, 6, 244, 328);

  ctx.fillStyle = '#f59e0b';
  ctx.font = 'bold 22px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('SAFETY FIRST', 128, 48);

  ctx.fillStyle = '#f8fafc';
  ctx.font = '14px sans-serif';
  ctx.fillText('Mandatory Lab PPE:', 128, 90);
  ctx.fillText('• Eye Protection (R1)', 128, 125);
  ctx.fillText('• Nitrile Gloves (R2)', 128, 155);
  ctx.fillText('• Cotton Lab Coat (R3)', 128, 185);
  ctx.fillText('• Wash Hands at Exit', 128, 220);

  ctx.fillStyle = '#ef4444';
  ctx.font = 'bold 16px sans-serif';
  ctx.fillText('2 CRITICALS = FAIL', 128, 275);

  const texture = new THREE.CanvasTexture(canvas);
  const geo = new THREE.PlaneGeometry(1.0, 1.33);
  const mat = new THREE.MeshBasicMaterial({ map: texture });
  const mesh = new THREE.Mesh(geo, mat);
  poster.add(mesh);

  parent.add(poster);
}

function createLabDoor(parent, x, y, z) {
  const door = new THREE.Group();
  door.position.set(x, y, z);
  door.rotation.y = -Math.PI / 2;

  const doorGeo = new THREE.BoxGeometry(1.6, 2.8, 0.08);
  const doorMat = new THREE.MeshStandardMaterial({ color: 0x1f163b, roughness: 0.5, metalness: 0.3 });
  const doorMesh = new THREE.Mesh(doorGeo, doorMat);
  door.add(doorMesh);

  // Door Window
  const winGeo = new THREE.PlaneGeometry(0.6, 0.8);
  const winMat = new THREE.MeshStandardMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.6, roughness: 0.1 });
  const winMesh = new THREE.Mesh(winGeo, winMat);
  winMesh.position.set(0, 0.4, 0.045);
  door.add(winMesh);

  parent.add(door);
}
