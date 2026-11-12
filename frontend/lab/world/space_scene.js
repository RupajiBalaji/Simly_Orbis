/**
 * Simly Orbis 3D Space Scene: Launch & Orbit Bench (frontend/lab/world/space_scene.js)
 * Procedural Launch Pad (Pad 39A), Umbilical Tower, Multi-Stage Rocket,
 * Procedural Engine Flame & Exhaust, 3D Earth Globe, Keplerian Orbit Paths,
 * and 5 Failure Mode Visualizations.
 */

import * as THREE from 'three';
import { soundFX } from '../audio/sound_fx.js';

export class SpaceScene {
  constructor(scene, camera, controls) {
    this.parentScene = scene;
    this.camera = camera;
    this.controls = controls;

    this.group = new THREE.Group();
    this.group.name = 'space_scene_group';
    this.parentScene.add(this.group);

    this.active = false;
    this.currentViewMode = 'pad'; // 'pad' | 'orbit'
    this.isTransitioningView = false;
    this.viewTransition = null;

    // Sub-groups
    this.padGroup = new THREE.Group();
    this.rocketGroup = new THREE.Group();
    this.boosterGroup = new THREE.Group();
    this.upperStageGroup = new THREE.Group();
    this.fairingGroup = new THREE.Group();
    this.flameGroup = new THREE.Group();
    this.smokeParticles = [];
    this.orbitGroup = new THREE.Group();
    this.earthMesh = null;
    this.orbitLineMesh = null;
    this.satelliteMesh = null;

    // State & telemetry
    this.telemetry = {
      altitude_km: 0.0,
      velocity_kms: 0.0,
      twr: 1.35,
      apoapsis_km: 0.0,
      periapsis_km: 0.0,
      period_min: 0.0,
      available_dv: 9500.0,
      required_dv: 9300.0,
      margin_pct: 2.1,
      current_stage: 1,
    };

    this.lookup = {};
    this.hudElement = null;
    this.activeFailureMode = null;
    this.flightState = 'prelaunch'; // 'prelaunch' | 'ascent' | 'orbit' | 'suborbital' | 'failed'
    this.flightTime = 0.0;

    // View Presets
    this.viewPresets = {
      pad: {
        pos: new THREE.Vector3(12.0, 7.5, 16.0),
        target: new THREE.Vector3(0.0, 5.0, 0.0),
        fov: 50,
      },
      orbit: {
        pos: new THREE.Vector3(0.0, 45.0, 110.0),
        target: new THREE.Vector3(0.0, 0.0, 0.0),
        fov: 55,
      },
    };
  }

  init() {
    this.buildStarfield();
    this.buildLaunchPad();
    this.buildRocketModel();
    this.buildEarthAndOrbit();
    this.buildHUD();
    this.group.visible = false;
  }

  activate() {
    this.active = true;
    this.group.visible = true;
    if (this.hudElement) {
      this.hudElement.style.display = 'flex';
    }
    this.setViewMode('pad', true);
  }

  deactivate() {
    this.active = false;
    this.group.visible = false;
    if (this.hudElement) {
      this.hudElement.style.display = 'none';
    }
  }

  // ---------------------------------------------------------------------------
  // 1. Procedural Environment & Launch Pad
  // ---------------------------------------------------------------------------

  buildStarfield() {
    const starCount = 800;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(starCount * 3);
    const colors = new Float32Array(starCount * 3);

    for (let i = 0; i < starCount; i++) {
      const u = Math.random();
      const v = Math.random();
      const theta = 2.0 * Math.PI * u;
      const phi = Math.acos(2.0 * v - 1.0);
      const r = 250.0 + Math.random() * 50.0;

      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = r * Math.cos(phi);

      const tint = 0.8 + Math.random() * 0.2;
      colors[i * 3] = tint;
      colors[i * 3 + 1] = tint * 0.95;
      colors[i * 3 + 2] = 1.0;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const starMaterial = new THREE.PointsMaterial({
      size: 1.8,
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
    });

    const starfield = new THREE.Points(geometry, starMaterial);
    this.group.add(starfield);
  }

  buildLaunchPad() {
    this.padGroup.name = 'launch_pad_group';

    // Concrete Octagonal Platform
    const padGeo = new THREE.CylinderGeometry(11, 12, 1.2, 8);
    const padMat = new THREE.MeshStandardMaterial({
      color: 0x1e293b,
      roughness: 0.85,
      metalness: 0.15,
    });
    const padMesh = new THREE.Mesh(padGeo, padMat);
    padMesh.position.y = 0.6;
    padMesh.receiveShadow = true;
    this.padGroup.add(padMesh);

    // Hazard Stripes Rim
    const rimGeo = new THREE.TorusGeometry(10.8, 0.2, 8, 32);
    const rimMat = new THREE.MeshStandardMaterial({
      color: 0xf59e0b,
      roughness: 0.5,
      metalness: 0.4,
    });
    const rimMesh = new THREE.Mesh(rimGeo, rimMat);
    rimMesh.rotation.x = Math.PI / 2;
    rimMesh.position.y = 1.22;
    this.padGroup.add(rimMesh);

    // Flame Trench Opening
    const trenchGeo = new THREE.CylinderGeometry(3.2, 3.8, 2.5, 16, 1, true);
    const trenchMat = new THREE.MeshStandardMaterial({
      color: 0x09090b,
      roughness: 0.95,
      metalness: 0.05,
      side: THREE.DoubleSide,
    });
    const trenchMesh = new THREE.Mesh(trenchGeo, trenchMat);
    trenchMesh.position.y = 0.0;
    this.padGroup.add(trenchMesh);

    // Launch Umbilical Tower (LUT)
    const lutGroup = new THREE.Group();
    lutGroup.position.set(-5.5, 0, 0);

    const towerHeight = 24.0;
    const towerGeo = new THREE.BoxGeometry(2.0, towerHeight, 2.0);
    const towerMat = new THREE.MeshStandardMaterial({
      color: 0xb91c1c, // Launch Tower Red
      roughness: 0.4,
      metalness: 0.6,
    });
    const towerMesh = new THREE.Mesh(towerGeo, towerMat);
    towerMesh.position.y = towerHeight / 2.0;
    lutGroup.add(towerMesh);

    // Lattice cross-braces
    for (let h = 3; h < towerHeight; h += 3.5) {
      const braceGeo = new THREE.BoxGeometry(2.4, 0.15, 2.4);
      const braceMat = new THREE.MeshStandardMaterial({ color: 0x64748b });
      const brace = new THREE.Mesh(braceGeo, braceMat);
      brace.position.y = h;
      lutGroup.add(brace);
    }

    // Swing Arms
    const arm1Geo = new THREE.BoxGeometry(4.2, 0.4, 0.5);
    const armMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.8 });
    const arm1 = new THREE.Mesh(arm1Geo, armMat);
    arm1.position.set(2.2, 14.0, 0);
    lutGroup.add(arm1);

    const arm2 = new THREE.Mesh(arm1Geo, armMat);
    arm2.position.set(2.2, 7.0, 0);
    lutGroup.add(arm2);

    // Lightning Mast & Beacon
    const mastGeo = new THREE.CylinderGeometry(0.08, 0.25, 4.0, 8);
    const mastMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0 });
    const mast = new THREE.Mesh(mastGeo, mastMat);
    mast.position.y = towerHeight + 2.0;
    lutGroup.add(mast);

    const beaconGeo = new THREE.SphereGeometry(0.2, 8, 8);
    const beaconMat = new THREE.MeshBasicMaterial({ color: 0xff0000 });
    const beacon = new THREE.Mesh(beaconGeo, beaconMat);
    beacon.position.y = towerHeight + 4.1;
    lutGroup.add(beacon);
    this.beaconMesh = beacon;

    this.padGroup.add(lutGroup);

    // Hold-Down Clamps
    for (let a = 0; a < 4; a++) {
      const angle = (a * Math.PI) / 2.0 + Math.PI / 4.0;
      const clampGeo = new THREE.BoxGeometry(0.6, 1.2, 0.8);
      const clampMat = new THREE.MeshStandardMaterial({ color: 0x475569, metalness: 0.7 });
      const clamp = new THREE.Mesh(clampGeo, clampMat);
      clamp.position.set(Math.cos(angle) * 2.6, 1.6, Math.sin(angle) * 2.6);
      clamp.rotation.y = -angle;
      this.padGroup.add(clamp);
    }

    // Registration for raycasting & directives
    this.padGroup.userData.targetId = 'launch_pad';
    this.lookup['launch_pad'] = this.padGroup;
    this.lookup['pad_39a'] = this.padGroup;
    this.group.add(this.padGroup);
  }

  // ---------------------------------------------------------------------------
  // 2. Procedural Multi-Stage Rocket
  // ---------------------------------------------------------------------------

  buildRocketModel() {
    this.rocketGroup.name = 'rocket_vehicle_group';
    this.rocketGroup.position.set(0, 1.2, 0);

    // Materials
    const hullWhiteMat = new THREE.MeshStandardMaterial({
      color: 0xf8fafc,
      roughness: 0.25,
      metalness: 0.1,
    });
    const brandPurpleMat = new THREE.MeshStandardMaterial({
      color: 0x7c3aed, // Orbis Purple
      roughness: 0.3,
      metalness: 0.4,
    });
    const brandTealMat = new THREE.MeshStandardMaterial({
      color: 0x06b6d4, // Orbis Teal
      roughness: 0.3,
      metalness: 0.3,
    });
    const engineBellMat = new THREE.MeshStandardMaterial({
      color: 0x334155,
      metalness: 0.85,
      roughness: 0.2,
    });

    // --- Stage 1: Booster Stage ---
    this.boosterGroup = new THREE.Group();
    this.boosterGroup.name = 'stage_1_booster';

    const s1Height = 8.5;
    const s1Radius = 1.35;
    const s1Geo = new THREE.CylinderGeometry(s1Radius, s1Radius, s1Height, 24);
    const s1Mesh = new THREE.Mesh(s1Geo, hullWhiteMat);
    s1Mesh.position.y = s1Height / 2.0;
    this.boosterGroup.add(s1Mesh);

    // Livery Band
    const ringGeo = new THREE.CylinderGeometry(s1Radius + 0.02, s1Radius + 0.02, 0.8, 24);
    const ringMesh = new THREE.Mesh(ringGeo, brandPurpleMat);
    ringMesh.position.y = s1Height * 0.75;
    this.boosterGroup.add(ringMesh);

    // Engine Cluster (4 outer bells + 1 center)
    const bellGeo = new THREE.CylinderGeometry(0.18, 0.42, 0.85, 16, 1, true);
    for (const [bx, bz] of [[0.6, 0.6], [-0.6, 0.6], [0.6, -0.6], [-0.6, -0.6], [0, 0]]) {
      const bell = new THREE.Mesh(bellGeo, engineBellMat);
      bell.position.set(bx, 0.0, bz);
      this.boosterGroup.add(bell);
    }

    // Aerodynamic Stabilizer Fins
    for (let f = 0; f < 4; f++) {
      const fAngle = (f * Math.PI) / 2.0;
      const finGeo = new THREE.BoxGeometry(0.08, 1.2, 0.7);
      const finMesh = new THREE.Mesh(finGeo, brandPurpleMat);
      finMesh.position.set(Math.cos(fAngle) * (s1Radius + 0.35), 0.7, Math.sin(fAngle) * (s1Radius + 0.35));
      finMesh.rotation.y = -fAngle;
      this.boosterGroup.add(finMesh);
    }

    this.rocketGroup.add(this.boosterGroup);

    // --- Interstage Adapter ---
    const isHeight = 1.0;
    const isGeo = new THREE.CylinderGeometry(1.15, s1Radius, isHeight, 24);
    const isMat = new THREE.MeshStandardMaterial({ color: 0x475569, metalness: 0.5 });
    const isMesh = new THREE.Mesh(isGeo, isMat);
    isMesh.position.y = s1Height + isHeight / 2.0;
    this.boosterGroup.add(isMesh);

    // --- Stage 2: Upper Stage ---
    this.upperStageGroup = new THREE.Group();
    this.upperStageGroup.name = 'stage_2_upper';
    this.upperStageGroup.position.y = s1Height + isHeight;

    const s2Height = 4.2;
    const s2Radius = 1.15;
    const s2Geo = new THREE.CylinderGeometry(s2Radius, s2Radius, s2Height, 24);
    const s2Mesh = new THREE.Mesh(s2Geo, hullWhiteMat);
    s2Mesh.position.y = s2Height / 2.0;
    this.upperStageGroup.add(s2Mesh);

    // Teal Livery Band
    const s2RingGeo = new THREE.CylinderGeometry(s2Radius + 0.02, s2Radius + 0.02, 0.5, 24);
    const s2Ring = new THREE.Mesh(s2RingGeo, brandTealMat);
    s2Ring.position.y = s2Height * 0.65;
    this.upperStageGroup.add(s2Ring);

    // Vacuum Engine Bell
    const vacBellGeo = new THREE.CylinderGeometry(0.25, 0.7, 1.1, 16, 1, true);
    const vacBell = new THREE.Mesh(vacBellGeo, engineBellMat);
    vacBell.position.y = 0.0;
    this.upperStageGroup.add(vacBell);

    // --- Fairing & Payload ---
    this.fairingGroup = new THREE.Group();
    this.fairingGroup.position.y = s2Height;

    const fairingHeight = 3.6;
    const fairingGeo = new THREE.ConeGeometry(s2Radius, fairingHeight, 24);
    const fairingMesh = new THREE.Mesh(fairingGeo, hullWhiteMat);
    fairingMesh.position.y = fairingHeight / 2.0;
    this.fairingGroup.add(fairingMesh);

    // Fairing Tip Indicator
    const tipGeo = new THREE.SphereGeometry(0.12, 12, 12);
    const tipMesh = new THREE.Mesh(tipGeo, brandTealMat);
    tipMesh.position.y = fairingHeight;
    this.fairingGroup.add(tipMesh);

    this.upperStageGroup.add(this.fairingGroup);
    this.rocketGroup.add(this.upperStageGroup);

    // --- Procedural Engine Flame ---
    this.flameGroup = new THREE.Group();
    const flameGeo = new THREE.ConeGeometry(0.9, 3.2, 16);
    flameGeo.rotateX(Math.PI);
    const flameMat = new THREE.MeshBasicMaterial({
      color: 0xffaa00,
      transparent: true,
      opacity: 0.0,
      blending: THREE.AdditiveBlending,
    });
    this.flameMesh = new THREE.Mesh(flameGeo, flameMat);
    this.flameMesh.position.y = -1.6;
    this.flameGroup.add(this.flameMesh);

    // Inner Core Flame
    const coreGeo = new THREE.ConeGeometry(0.4, 2.4, 16);
    coreGeo.rotateX(Math.PI);
    const coreMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.0,
      blending: THREE.AdditiveBlending,
    });
    this.coreFlameMesh = new THREE.Mesh(coreGeo, coreMat);
    this.coreFlameMesh.position.y = -1.2;
    this.flameGroup.add(this.coreFlameMesh);

    this.rocketGroup.add(this.flameGroup);

    // Register lookup
    this.rocketGroup.userData.targetId = 'rocket';
    this.lookup['rocket'] = this.rocketGroup;
    this.group.add(this.rocketGroup);
  }

  // ---------------------------------------------------------------------------
  // 3. Earth Globe & Kepler Orbit Visuals
  // ---------------------------------------------------------------------------

  buildEarthAndOrbit() {
    this.orbitGroup.name = 'orbit_group';
    this.orbitGroup.position.set(0, 0, 0);

    // Stylized Earth Sphere (Radius 22.0)
    const earthRadius = 22.0;
    const earthGeo = new THREE.SphereGeometry(earthRadius, 48, 48);
    const earthMat = new THREE.MeshStandardMaterial({
      color: 0x1d4ed8, // Deep blue ocean
      roughness: 0.6,
      metalness: 0.1,
    });
    this.earthMesh = new THREE.Mesh(earthGeo, earthMat);
    this.orbitGroup.add(this.earthMesh);

    // Stylized Continents Layer (Outer Green/Cyan shell)
    const contGeo = new THREE.SphereGeometry(earthRadius + 0.1, 32, 32);
    const contMat = new THREE.MeshStandardMaterial({
      color: 0x059669,
      roughness: 0.8,
      transparent: true,
      opacity: 0.65,
      wireframe: true,
    });
    const continents = new THREE.Mesh(contGeo, contMat);
    this.orbitGroup.add(continents);

    // Atmosphere Glow Rim
    const atmoGeo = new THREE.SphereGeometry(earthRadius + 1.2, 32, 32);
    const atmoMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.18,
      side: THREE.BackSide,
      blending: THREE.AdditiveBlending,
    });
    const atmoMesh = new THREE.Mesh(atmoGeo, atmoMat);
    this.orbitGroup.add(atmoMesh);

    // Initial nominal LEO orbit path (200 km)
    this.updateOrbitPath(200.0, 200.0, 0x00e5ff);

    // Satellite Mesh on Orbit
    const satGroup = new THREE.Group();
    const satBodyGeo = new THREE.BoxGeometry(0.8, 0.6, 0.6);
    const satMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.8 }); // Gold foil
    const satBody = new THREE.Mesh(satBodyGeo, satMat);
    satGroup.add(satBody);

    // Solar panels
    const panelGeo = new THREE.BoxGeometry(1.6, 0.05, 0.5);
    const panelMat = new THREE.MeshStandardMaterial({ color: 0x1e3a8a, metalness: 0.5 });
    const panel1 = new THREE.Mesh(panelGeo, panelMat);
    panel1.position.x = 1.2;
    satGroup.add(panel1);
    const panel2 = new THREE.Mesh(panelGeo, panelMat);
    panel2.position.x = -1.2;
    satGroup.add(panel2);

    this.satelliteMesh = satGroup;
    this.orbitGroup.add(this.satelliteMesh);

    // Earth and orbit are placed far in Pad View, moved to center in Orbit View
    this.orbitGroup.position.set(0, -60, 0);
    this.orbitGroup.scale.set(0.01, 0.01, 0.01); // hidden in pad view
    this.group.add(this.orbitGroup);
  }

  updateOrbitPath(peKm, apKm, colorHex = 0x00e5ff) {
    if (this.orbitLineMesh) {
      this.orbitGroup.remove(this.orbitLineMesh);
      this.orbitLineMesh.geometry.dispose();
      this.orbitLineMesh = null;
    }

    const earthR = 22.0;
    const scale = 22.0 / 6371.0; // scale factor
    const rPe = earthR + peKm * scale;
    const rAp = earthR + apKm * scale;
    const a = (rPe + rAp) / 2.0;
    const c = a - rPe; // focal distance
    const b = Math.sqrt(Math.max(0.1, a ** 2 - c ** 2));

    const numPoints = 128;
    const points = [];
    for (let i = 0; i <= numPoints; i++) {
      const theta = (2.0 * Math.PI * i) / numPoints;
      // Orbit centered with Earth at focus (-c, 0)
      const x = a * Math.cos(theta) - c;
      const z = b * Math.sin(theta);
      points.push(new THREE.Vector3(x, 0, z));
    }

    const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
    const lineMat = new THREE.LineBasicMaterial({
      color: colorHex,
      linewidth: 2,
      transparent: true,
      opacity: 0.9,
    });
    this.orbitLineMesh = new THREE.LineLoop(lineGeo, lineMat);
    this.orbitGroup.add(this.orbitLineMesh);
    this.orbitPoints = points;
  }

  // ---------------------------------------------------------------------------
  // 4. View Mode Transitions (Pad View <-> Orbit View)
  // ---------------------------------------------------------------------------

  setViewMode(mode, instant = false) {
    this.currentViewMode = mode;
    const targetPreset = this.viewPresets[mode];
    if (!targetPreset) return;

    if (instant) {
      this.camera.position.copy(targetPreset.pos);
      this.controls.target.copy(targetPreset.target);
      this.camera.fov = targetPreset.fov;
      this.camera.updateProjectionMatrix();

      if (mode === 'orbit') {
        this.padGroup.visible = false;
        this.rocketGroup.visible = false;
        this.orbitGroup.position.set(0, 0, 0);
        this.orbitGroup.scale.set(1, 1, 1);
      } else {
        this.padGroup.visible = true;
        this.rocketGroup.visible = true;
        this.orbitGroup.position.set(0, -60, 0);
        this.orbitGroup.scale.set(0.01, 0.01, 0.01);
      }
      this.updateViewButtonLabel();
      return;
    }

    // Smooth tween transition
    this.isTransitioningView = true;
    this.viewTransition = {
      startTime: performance.now(),
      duration: 1800,
      startPos: this.camera.position.clone(),
      endPos: targetPreset.pos.clone(),
      startTarget: this.controls.target.clone(),
      endTarget: targetPreset.target.clone(),
      startFov: this.camera.fov,
      endFov: targetPreset.fov,
      targetMode: mode,
    };
  }

  toggleViewMode() {
    const nextMode = this.currentViewMode === 'pad' ? 'orbit' : 'pad';
    this.setViewMode(nextMode, false);
  }

  updateViewButtonLabel() {
    const btn = document.getElementById('space-view-toggle-btn');
    if (btn) {
      btn.textContent = this.currentViewMode === 'pad' ? '🛰️ Switch to Orbit View' : '🚀 Switch to Pad View';
    }
  }

  // ---------------------------------------------------------------------------
  // 5. Space HUD Overlay
  // ---------------------------------------------------------------------------

  buildHUD() {
    let container = document.getElementById('space-hud-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'space-hud-container';
      container.style.cssText = `
        position: absolute;
        top: 60px;
        left: 20px;
        right: 20px;
        display: none;
        justify-content: space-between;
        align-items: flex-start;
        pointer-events: none;
        z-index: 50;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
      `;
      document.body.appendChild(container);
    }
    this.hudElement = container;
    this.renderHUDContent();
  }

  renderHUDContent() {
    if (!this.hudElement) return;

    const t = this.telemetry;
    const marginClass = t.margin_pct >= 5.0 ? '#10b981' : t.margin_pct >= 0 ? '#f59e0b' : '#ef4444';
    const dvPct = Math.min(100, Math.max(0, (t.available_dv / (t.required_dv * 1.2)) * 100));

    this.hudElement.innerHTML = `
      <div style="background: rgba(15, 23, 42, 0.88); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px; padding: 12px 16px; min-width: 280px; pointer-events: auto; box-shadow: 0 4px 16px rgba(0,0,0,0.4);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 4px;">
          <span style="font-weight: 700; color: #38bdf8; font-size: 0.85rem; letter-spacing: 0.05em;">🚀 LAUNCH BENCH TELEMETRY</span>
          <span style="font-size: 0.72rem; padding: 2px 6px; border-radius: 4px; background: ${marginClass}22; color: ${marginClass}; font-weight: 600;">
            STAGE ${t.current_stage}
          </span>
        </div>
        
        <!-- Delta-V Budget Bar -->
        <div style="margin-bottom: 8px;">
          <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #94a3b8; margin-bottom: 2px;">
            <span>Delta-V Budget</span>
            <span style="font-family: monospace; color: #f8fafc;">${t.available_dv.toFixed(0)} / ${t.required_dv.toFixed(0)} m/s</span>
          </div>
          <div style="background: rgba(255,255,255,0.1); height: 6px; border-radius: 3px; overflow: hidden;">
            <div style="background: ${marginClass}; width: ${dvPct}%; height: 100%; transition: width 0.3s ease;"></div>
          </div>
          <div style="display: flex; justify-content: flex-end; font-size: 0.7rem; color: ${marginClass}; margin-top: 2px;">
            Margin: ${t.margin_pct >= 0 ? '+' : ''}${t.margin_pct.toFixed(1)}%
          </div>
        </div>

        <!-- Readouts Grid -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 0.75rem;">
          <div style="background: rgba(255,255,255,0.03); padding: 4px 6px; border-radius: 4px;">
            <span style="color: #64748b; font-size: 0.68rem; display: block;">LIFTOFF TWR</span>
            <span style="font-family: monospace; font-weight: 600; color: ${t.twr >= 1.0 ? '#38bdf8' : '#ef4444'};">${t.twr.toFixed(2)}</span>
          </div>
          <div style="background: rgba(255,255,255,0.03); padding: 4px 6px; border-radius: 4px;">
            <span style="color: #64748b; font-size: 0.68rem; display: block;">SPEED</span>
            <span style="font-family: monospace; font-weight: 600; color: #f8fafc;">${t.velocity_kms.toFixed(2)} km/s</span>
          </div>
          <div style="background: rgba(255,255,255,0.03); padding: 4px 6px; border-radius: 4px;">
            <span style="color: #64748b; font-size: 0.68rem; display: block;">PERIAPSIS</span>
            <span style="font-family: monospace; font-weight: 600; color: #f8fafc;">${t.periapsis_km.toFixed(0)} km</span>
          </div>
          <div style="background: rgba(255,255,255,0.03); padding: 4px 6px; border-radius: 4px;">
            <span style="color: #64748b; font-size: 0.68rem; display: block;">APOAPSIS</span>
            <span style="font-family: monospace; font-weight: 600; color: #f8fafc;">${t.apoapsis_km.toFixed(0)} km</span>
          </div>
        </div>
      </div>

      <!-- View Toggle Button -->
      <div style="pointer-events: auto;">
        <button id="space-view-toggle-btn" type="button" style="
          background: rgba(15, 23, 42, 0.9);
          border: 1px solid rgba(56, 189, 248, 0.4);
          color: #38bdf8;
          padding: 8px 14px;
          border-radius: 6px;
          font-weight: 600;
          font-size: 0.8rem;
          cursor: pointer;
          box-shadow: 0 4px 12px rgba(0,0,0,0.3);
          transition: all 0.2s ease;
        ">
          🛰️ Switch to Orbit View
        </button>
      </div>
    `;

    const btn = document.getElementById('space-view-toggle-btn');
    if (btn) {
      btn.onclick = () => this.toggleViewMode();
      this.updateViewButtonLabel();
    }
  }

  // ---------------------------------------------------------------------------
  // 6. Visual Directives Execution
  // ---------------------------------------------------------------------------

  applyDirective(directive) {
    if (!directive) return;

    switch (directive.type) {
      case 'rocket':
        this.handleRocketDirective(directive.rocket);
        break;
      case 'flame':
        this.handleFlameDirective(directive.flame);
        break;
      case 'orbit_path':
        this.handleOrbitPathDirective(directive.orbit_path);
        break;
      case 'stage_sep':
        this.handleStageSeparation(directive.stage_sep);
        break;
      case 'failure':
        this.handleFailureMode(directive.failure);
        break;
      case 'readout':
        this.handleReadoutDirective(directive);
        break;
      default:
        break;
    }
  }

  handleRocketDirective(rocketData) {
    if (!rocketData) return;
    if (rocketData.total_mass_t) {
      this.telemetry.total_mass_t = rocketData.total_mass_t;
    }
    this.renderHUDContent();
  }

  handleFlameDirective(flameData) {
    if (!flameData) return;
    const intensity = Math.max(0, Math.min(1.0, flameData.intensity ?? 1.0));
    const hex = flameData.exhaust_color_hex || '#ffaa00';
    const color = parseInt(hex.replace('#', '0x'), 16);

    if (this.flameMesh && this.coreFlameMesh) {
      this.flameMesh.material.opacity = intensity * 0.9;
      this.flameMesh.material.color.setHex(color);
      this.coreFlameMesh.material.opacity = intensity * 0.95;
    }

    if (intensity > 0) {
      soundFX?.playCentrifugeHum?.(2.0);
    }
  }

  handleOrbitPathDirective(pathPoints) {
    if (!pathPoints || pathPoints.length === 0) return;
    let peKm = 200.0;
    let apKm = 200.0;
    if (Array.isArray(pathPoints)) {
      const alts = pathPoints.map((p) => p.altitude_km || 200.0);
      peKm = Math.min(...alts);
      apKm = Math.max(...alts);
    }
    this.updateOrbitPath(peKm, apKm, 0x00e5ff);
    this.telemetry.periapsis_km = peKm;
    this.telemetry.apoapsis_km = apKm;
    this.renderHUDContent();

    // Auto transition to orbit view on successful orbital insertion
    if (this.currentViewMode === 'pad' && apKm >= 150.0) {
      setTimeout(() => {
        this.setViewMode('orbit', false);
      }, 1200);
    }
  }

  handleStageSeparation(stageIndex) {
    this.telemetry.current_stage = 2;
    soundFX?.playGlassClink?.();

    // Animate stage 1 falling away
    const booster = this.boosterGroup;
    let elapsed = 0;
    const sepInterval = setInterval(() => {
      elapsed += 33;
      booster.position.y -= 0.15;
      booster.rotation.x += 0.02;
      booster.rotation.z += 0.015;
      if (elapsed > 2000) {
        clearInterval(sepInterval);
        booster.visible = false;
      }
    }, 33);

    // Switch flame color to hydrolox vacuum blue
    this.handleFlameDirective({ intensity: 0.85, exhaust_color_hex: '#00d4ff' });
    this.renderHUDContent();
  }

  handleFailureMode(failureType) {
    this.activeFailureMode = failureType;
    this.flightState = 'failed';

    if (failureType === 'no_liftoff') {
      // Rocket shakes on pad, smoke billows, does not lift off
      let shakeTime = 0;
      const shakeInterval = setInterval(() => {
        shakeTime += 33;
        this.rocketGroup.position.x = (Math.random() - 0.5) * 0.15;
        this.rocketGroup.position.z = (Math.random() - 0.5) * 0.15;
        if (shakeTime > 2500) {
          clearInterval(shakeInterval);
          this.rocketGroup.position.set(0, 1.2, 0);
          this.handleFlameDirective({ intensity: 0.0 });
        }
      }, 33);
    } else if (failureType === 'suborbital_fall') {
      // Arcs up then falls back
      let t = 0;
      const fallInterval = setInterval(() => {
        t += 0.033;
        this.rocketGroup.position.y = Math.max(0, 1.2 + 8.0 * Math.sin(t * 1.5) - 4.0 * (t ** 2));
        this.rocketGroup.rotation.z = -t * 0.8;
        if (t > 2.5) {
          clearInterval(fallInterval);
          this.handleFlameDirective({ intensity: 0.0 });
        }
      }, 33);
    } else if (failureType === 'transfer_failed') {
      // Draw decayed red orbit
      this.updateOrbitPath(80.0, 180.0, 0xef4444);
    }
  }

  handleReadoutDirective(directive) {
    if (directive.label === 'LIFTOFF TWR') {
      this.telemetry.twr = parseFloat(directive.value) || 1.35;
    } else if (directive.label === 'ACHIEVED ORBIT') {
      this.telemetry.velocity_kms = 7.78;
    }
    this.renderHUDContent();
  }

  // ---------------------------------------------------------------------------
  // 7. Per-Frame Animation Loop Update
  // ---------------------------------------------------------------------------

  update(dt) {
    if (!this.active) return;
    this.flightTime += dt;

    // Red obstruction beacon blink
    if (this.beaconMesh) {
      this.beaconMesh.visible = Math.floor(this.flightTime * 2.0) % 2 === 0;
    }

    // Flame flicker
    if (this.flameMesh && this.flameMesh.material.opacity > 0.05) {
      const flicker = 0.9 + Math.random() * 0.2;
      this.flameMesh.scale.set(flicker, flicker * 1.1, flicker);
    }

    // Earth slow axial rotation in Orbit View
    if (this.earthMesh) {
      this.earthMesh.rotation.y += 0.0015;
    }

    // Satellite motion along orbit path
    if (this.satelliteMesh && this.orbitPoints && this.orbitPoints.length > 0) {
      const idx = Math.floor((this.flightTime * 8.0) % this.orbitPoints.length);
      const pt = this.orbitPoints[idx];
      if (pt) {
        this.satelliteMesh.position.copy(pt);
      }
    }

    // Smooth view camera tween
    if (this.isTransitioningView && this.viewTransition) {
      const elapsed = performance.now() - this.viewTransition.startTime;
      const p = Math.min(1.0, elapsed / this.viewTransition.duration);
      // Smooth cubic ease in-out
      const ease = p < 0.5 ? 4 * p * p * p : 1 - ((-2 * p + 2) ** 3) / 2;

      this.camera.position.lerpVectors(this.viewTransition.startPos, this.viewTransition.endPos, ease);
      this.controls.target.lerpVectors(this.viewTransition.startTarget, this.viewTransition.endTarget, ease);
      this.camera.fov = this.viewTransition.startFov + (this.viewTransition.endFov - this.viewTransition.startFov) * ease;
      this.camera.updateProjectionMatrix();

      // Show/hide groups halfway through transition
      if (p >= 0.5) {
        if (this.viewTransition.targetMode === 'orbit') {
          this.padGroup.visible = false;
          this.rocketGroup.visible = false;
          this.orbitGroup.position.set(0, 0, 0);
          this.orbitGroup.scale.set(1, 1, 1);
        } else {
          this.padGroup.visible = true;
          this.rocketGroup.visible = true;
          this.orbitGroup.position.set(0, -60, 0);
          this.orbitGroup.scale.set(0.01, 0.01, 0.01);
        }
      }

      if (p >= 1.0) {
        this.isTransitioningView = false;
        this.viewTransition = null;
        this.updateViewButtonLabel();
      }
    }
  }
}
