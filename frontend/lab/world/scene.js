/**
 * 3D Scene Manager, Camera, Lighting & Raycasting (frontend/lab/world/scene.js)
 * Manages Three.js renderer lifecycle, OrbitControls, interactive raycaster,
 * and station camera transitions.
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/OrbitControls.js';
import { buildLabRoom } from './room.js';
import { buildApparatus } from './apparatus.js';
import { applyLiquidDirective } from '../render/liquid.js';
import { applyReadoutDirective } from '../render/readouts.js';
import { buildViewingGalleryAndCrowd } from './trial_hall.js';
import { state } from '../state.js';

export class LabScene {
  constructor(canvasElement) {
    this.canvas = canvasElement;
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;
    this.roomGroup = null;
    this.apparatusLookup = {};
    this.apparatusContainer = null;
    this.trialHall = null;

    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2(-999, -999);
    this.hoveredObject = null;
    this.selectedObject = null;

    this.isTransitioningCamera = false;
    this.cameraTransition = null;
    this.isActionCameraActive = false;
    this.savedCameraPos = null;
    this.savedCameraTarget = null;
    this.isGalleryMode = false;
    this.isWhiteboardZoomed = false;

    this.cameraTarget = new THREE.Vector3(0, 1.15, -1.85);
    this.cameraDefaultPos = new THREE.Vector3(0, 2.05, 1.55);

    this.stationPresets = {
      default: { pos: new THREE.Vector3(0, 2.05, 1.55), target: new THREE.Vector3(0, 1.15, -1.85) },
      burette: { pos: new THREE.Vector3(0.55, 1.70, 0.45), target: new THREE.Vector3(-0.02, 1.50, -1.85) },
      conical_flask: { pos: new THREE.Vector3(0.35, 1.55, -0.45), target: new THREE.Vector3(0.02, 1.25, -1.85) },
      balance: { pos: new THREE.Vector3(-3.20, 1.65, -2.40), target: new THREE.Vector3(-4.45, 1.15, -4.15) },
      patient: { pos: new THREE.Vector3(2.8, 1.65, -3.2), target: new THREE.Vector3(4.3, 1.05, -3.9) },
      analyzer: { pos: new THREE.Vector3(-4.2, 1.8, -2.2), target: new THREE.Vector3(-5.5, 1.15, -3.5) },
      sink: { pos: new THREE.Vector3(-5.4, 1.6, -1.0), target: new THREE.Vector3(-7.2, 1.05, -1.0) },
      whiteboard: { pos: new THREE.Vector3(0, 2.7, -3.8), target: new THREE.Vector3(0, 2.7, -6.9) },
      trial_screen: { pos: new THREE.Vector3(4.5, 2.6, -3.8), target: new THREE.Vector3(4.5, 2.6, -6.9) },
      trial_gallery: { pos: new THREE.Vector3(0, 3.8, 1.6), target: new THREE.Vector3(0, 0.4, 7.5) },
    };

    this.nameTagsVisible = true;

    this.animationFrameId = null;
    this.lastTime = performance.now();
    this.frameCount = 0;
    this.fpsTimer = performance.now();

    this.init();
  }

  init() {
    // 1. Scene & Environment (Bright Clean Laboratory)
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0xf1f5f9);
    this.scene.fog = new THREE.FogExp2(0xf1f5f9, 0.012);

    // 2. Camera
    const aspect = window.innerWidth / window.innerHeight;
    this.camera = new THREE.PerspectiveCamera(50, aspect, 0.1, 50);
    this.camera.position.copy(this.cameraDefaultPos);

    // 3. Renderer (Physically Based Lighting for r160, Capped Pixel Ratio 1.5)
    this.quality = 'high';
    this.autoQualityLocked = false;
    this.hasAutoDowngraded = false;
    this.fpsSamples = [];
    this.updateCallbacks = [];
    this.isTabHidden = false;

    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      powerPreference: 'high-performance',
    });
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5)); // Capped at 1.5 for laptop GPU performance
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.1;

    // 4. OrbitControls (touch + mouse)
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.06;
    this.controls.maxPolarAngle = Math.PI / 2.05; // do not go below floor
    this.controls.minDistance = 1.0;
    this.controls.maxDistance = 16.0;
    this.controls.target.copy(this.cameraTarget);

    // 5. Room geometry & permanent fixtures
    this.roomGroup = buildLabRoom(this.scene);

    // 6. Event listeners
    this.onWindowResize = this.onWindowResize.bind(this);
    this.onPointerMove = this.onPointerMove.bind(this);
    this.onPointerDown = this.onPointerDown.bind(this);
    this.onKeyDown = this.onKeyDown.bind(this);
    this.animate = this.animate.bind(this);

    window.addEventListener('resize', this.onWindowResize, false);
    window.addEventListener('keydown', this.onKeyDown, false);
    document.addEventListener('visibilitychange', () => {
      this.isTabHidden = document.hidden;
    }, false);
    this.canvas.addEventListener('pointermove', this.onPointerMove, false);
    this.canvas.addEventListener('pointerdown', this.onPointerDown, false);

    // Dynamic selective name tags subscription
    state.subscribe((event, payload) => {
      if (event === 'target_selected') {
        this.updateNameTagVisibility(payload, this.getNextStepTargetId());
      } else if (event === 'session_updated') {
        this.updateNameTagVisibility(state.selectedTarget, this.getNextStepTargetId());
      }
    });

    // Start render loop
    this.lastTime = performance.now();
    this.animate();
  }

  addUpdateCallback(cb) {
    if (typeof cb === 'function') {
      this.updateCallbacks.push(cb);
    }
  }

  setQuality(mode, isAuto = false) {
    this.quality = mode;
    const isHigh = mode === 'high';

    const maxRatio = isHigh ? 1.5 : 1.0;
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, maxRatio));
    this.renderer.shadowMap.enabled = isHigh;

    if (this.roomGroup?.userData?.dirLight) {
      this.roomGroup.userData.dirLight.castShadow = isHigh;
    }

    this.scene.traverse((obj) => {
      if (obj.isMesh && obj.material) {
        obj.material.needsUpdate = true;
      }
    });

    this.renderer.setSize(window.innerWidth, window.innerHeight);
    state.notify('quality_changed', { quality: mode, isAuto });
  }

  toggleQuality() {
    this.autoQualityLocked = true; // Manual toggle locks automatic quality adjustment
    this.setQuality(this.quality === 'high' ? 'low' : 'high', false);
    return this.quality;
  }

  onKeyDown(event) {
    if (event.key === 'n' || event.key === 'N') {
      this.toggleNameTags();
    }
  }

  getNextStepTargetId() {
    const exp = state.experiment;
    const session = state.session;
    if (!exp?.protocol) return null;
    const completed = new Set(session?.protocol_progress || []);
    const nextStep = exp.protocol.find((s) => !completed.has(s.id));
    if (!nextStep) return null;

    const stepTargetMap = {
      wear_ppe: 'avatar',
      tare_balance: 'digital_balance',
      weigh_dose: 'digital_balance',
      dissolve_dose: 'dosing_cup',
      label_cup: 'dosing_cup',
      administer_oral: 'patient_bed',
      advance_time: 'ward_clock',
      label_tube: 'tube_rack',
      label_tubes: 'tube_rack',
      draw_blood: 'patient_bed',
      run_assay: 'assay_analyzer',
      rinse_burette: 'burette',
      fill_burette: 'burette',
      pipette_analyte: 'conical_flask',
      add_indicator: 'conical_flask',
      titrate: 'burette',
      swirl: 'conical_flask',
      record_endpoint: 'conical_flask',
      dispose_waste: 'chemical_waste_bin',
      wash_hands: 'sink',
    };
    return stepTargetMap[nextStep.id] || null;
  }

  updateNameTagVisibility(selectedId = null, nextStepTargetId = null) {
    if (!this.apparatusContainer) return;
    const activeSelected = selectedId || state.selectedTarget;
    const activeNext = nextStepTargetId || this.getNextStepTargetId();

    this.apparatusContainer.traverse((child) => {
      if (child.userData?.isNameTag) {
        if (!this.nameTagsVisible) {
          child.visible = false;
          return;
        }
        const parentTargetId = child.parent?.userData?.targetId;
        const matchesSelected = activeSelected && parentTargetId === activeSelected;
        const matchesNext = activeNext && parentTargetId === activeNext;

        // If an apparatus is selected or next step exists, show only matching tag(s)
        if (activeSelected || activeNext) {
          child.visible = Boolean(matchesSelected || matchesNext);
        } else {
          // Default initial fallback: only hero apparatus
          child.visible = parentTargetId === 'burette' || parentTargetId === 'patient_bed';
        }
      }
    });
  }

  toggleNameTags(forceValue) {
    this.nameTagsVisible = forceValue !== undefined ? forceValue : !this.nameTagsVisible;
    this.updateNameTagVisibility();
    const btn = document.getElementById('btn-toggle-nametags');
    if (btn) {
      btn.textContent = this.nameTagsVisible ? '🏷️ Tags: ON' : '🏷️ Tags: OFF';
    }
  }

  loadExperiment(experimentDef) {
    if (this.apparatusContainer) {
      this.scene.remove(this.apparatusContainer);
      this.apparatusContainer = null;
      this.apparatusLookup = {};
    }

    if (this.trialHall) {
      this.scene.remove(this.trialHall.trialGroup);
      this.trialHall = null;
    }

    const apparatusList = experimentDef?.apparatus || [];
    const { container, lookup } = buildApparatus(apparatusList, this.scene);
    this.apparatusContainer = container;
    this.apparatusLookup = lookup;

    if (experimentDef?.id === 'pk_ward') {
      this.trialHall = buildViewingGalleryAndCrowd(this.scene);
      this.addUpdateCallback(() => {
        if (this.trialHall) this.trialHall.update(performance.now());
      });
      state.emit('trial_hall_ready', this.trialHall);
    }

    this.syncApparatusState(experimentDef?.apparatus);
    this.updateNameTagVisibility();
    this.resetCameraView();
  }

  syncApparatusState(apparatusState) {
    if (!apparatusState || !this.apparatusLookup) return;
    const entries = Array.isArray(apparatusState)
      ? apparatusState.map((item) => [item.id, item.state || item])
      : Object.entries(apparatusState);

    for (const [targetId, itemState] of entries) {
      const obj = this.getApparatus(targetId);
      if (!obj || !itemState) continue;
      // 1. Liquid volume & color sync
      if (itemState.volume_ml !== undefined || itemState.color_hex) {
        applyLiquidDirective(obj, {
          target: targetId,
          volume_ml: itemState.volume_ml !== undefined ? itemState.volume_ml : 0.0,
          hex: itemState.color_hex || '#f8fafc',
          opacity: (itemState.volume_ml || 0) > 0 ? 0.85 : 0.0,
        });
      }
      // 2. Screen readouts sync
      if (itemState.weight_g !== undefined) {
        applyReadoutDirective(obj, { target: targetId, value: itemState.weight_g, unit: 'g' });
      }
      if (itemState.ph !== undefined) {
        applyReadoutDirective(obj, { target: targetId, value: itemState.ph, unit: 'pH' });
      }
    }
  }

  getApparatus(targetId) {
    if (!targetId) return null;
    return this.apparatusLookup[targetId] || null;
  }

  focusOnStation(targetId) {
    const obj = this.getApparatus(targetId);
    if (!obj) return;

    const worldPos = new THREE.Vector3();
    obj.getWorldPosition(worldPos);

    this.cameraTarget.set(worldPos.x, worldPos.y + 0.3, worldPos.z);
    this.controls.target.copy(this.cameraTarget);
  }

  checkCameraObstruction() {
    if (!this.camera) return;

    // 1. Gallery Railing collision (railing is at z = 2.15)
    // When inside ward, never allow camera to drift into or behind the railing
    if (!this.isGalleryMode) {
      if (this.camera.position.z > 1.70) {
        this.camera.position.z = 1.70;
      }
    }

    // 2. Room wall bounds
    this.camera.position.x = Math.max(-7.2, Math.min(7.2, this.camera.position.x));
    this.camera.position.z = Math.max(-6.5, this.camera.position.z);
    this.camera.position.y = Math.max(0.70, Math.min(4.5, this.camera.position.y));

    // 3. Bench collision check (benches are at y = 0.94)
    const px = this.camera.position.x;
    const pz = this.camera.position.z;
    const isOverLeftBench = px >= -6.6 && px <= -2.4 && pz >= -5.0 && pz <= -3.4;
    const isOverCenterBench = px >= -2.3 && px <= 2.3 && pz >= -2.8 && pz <= -1.2;
    if (isOverLeftBench || isOverCenterBench) {
      this.camera.position.y = Math.max(1.30, this.camera.position.y);
    }
  }

  easeCameraTo(targetPos, targetLookAt, durationMs = 400, onComplete = null) {
    if (state.skipAnimation || durationMs <= 0) {
      this.camera.position.copy(targetPos);
      this.cameraTarget.copy(targetLookAt);
      this.controls.target.copy(targetLookAt);
      this.checkCameraObstruction();
      if (onComplete) onComplete();
      return;
    }

    this.cameraTransition = {
      startTime: performance.now(),
      duration: durationMs,
      startPos: this.camera.position.clone(),
      endPos: targetPos.clone(),
      startLookAt: this.controls.target.clone(),
      endLookAt: targetLookAt.clone(),
      onComplete,
    };
  }

  updateCameraTransition(now) {
    if (!this.cameraTransition) return;
    const t = Math.min(1.0, (now - this.cameraTransition.startTime) / this.cameraTransition.duration);
    const ease = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

    this.camera.position.lerpVectors(this.cameraTransition.startPos, this.cameraTransition.endPos, ease);
    const curLook = new THREE.Vector3().lerpVectors(this.cameraTransition.startLookAt, this.cameraTransition.endLookAt, ease);
    this.cameraTarget.copy(curLook);
    this.controls.target.copy(curLook);

    if (t >= 1.0) {
      const cb = this.cameraTransition.onComplete;
      this.cameraTransition = null;
      this.checkCameraObstruction();
      if (cb) cb();
    }
  }

  startActionCamera(apparatusPos, avatarPos, durationMs = 1800) {
    if (state.skipAnimation) return;

    if (!this.isActionCameraActive) {
      this.savedCameraPos = this.camera.position.clone();
      this.savedCameraTarget = this.controls.target.clone();
      this.isActionCameraActive = true;
    }

    const appPos = apparatusPos ? apparatusPos.clone() : new THREE.Vector3(0, 1.0, -1.8);
    const avPos = avatarPos ? avatarPos.clone() : new THREE.Vector3(appPos.x, 0, appPos.z + 1.0);

    // Midpoint framing avatar chest/hands and apparatus (~1.15m height)
    const focusTarget = new THREE.Vector3(
      avPos.x * 0.45 + appPos.x * 0.55,
      1.15,
      avPos.z * 0.45 + appPos.z * 0.55
    );

    const toAvatar = new THREE.Vector3().subVectors(avPos, appPos);
    toAvatar.y = 0;
    if (toAvatar.lengthSq() < 0.01) toAvatar.set(0, 0, 1);
    toAvatar.normalize();

    // Side quarter angle
    const flank = new THREE.Vector3(-toAvatar.z, 0, toAvatar.x);
    const testDirA = toAvatar.clone().multiplyScalar(0.7).add(flank.clone().multiplyScalar(0.7)).normalize();
    const testDirB = toAvatar.clone().multiplyScalar(0.7).sub(flank.clone().multiplyScalar(0.7)).normalize();
    const posA = focusTarget.clone().add(testDirA.clone().multiplyScalar(1.95));
    const posB = focusTarget.clone().add(testDirB.clone().multiplyScalar(1.95));

    const chosenPos = Math.abs(posA.x) < Math.abs(posB.x) && posA.z <= 1.70 ? posA : posB;
    chosenPos.y = 1.38; // Medium close shot framing upper body, hands & apparatus (~2m distance)

    // Hard collision clamps
    chosenPos.x = Math.max(-6.8, Math.min(6.8, chosenPos.x));
    chosenPos.z = Math.max(-6.2, Math.min(1.70, chosenPos.z));
    chosenPos.y = Math.max(1.10, Math.min(2.4, chosenPos.y));

    this.easeCameraTo(chosenPos, focusTarget, 350);
  }

  endActionCamera() {
    if (!this.isActionCameraActive) return;
    this.isActionCameraActive = false;

    if (state.skipAnimation) {
      if (this.savedCameraPos && this.savedCameraTarget) {
        this.camera.position.copy(this.savedCameraPos);
        this.cameraTarget.copy(this.savedCameraTarget);
        this.controls.target.copy(this.savedCameraTarget);
      }
      return;
    }

    if (this.savedCameraPos && this.savedCameraTarget) {
      this.easeCameraTo(this.savedCameraPos, this.savedCameraTarget, 400);
    }
  }

  setStationCamera(presetKey) {
    this.isGalleryMode = presetKey === 'trial_gallery';
    const preset = this.stationPresets[presetKey] || this.stationPresets.default;
    this.easeCameraTo(preset.pos, preset.target, 450);
  }

  resetCameraView() {
    this.isGalleryMode = false;
    this.isWhiteboardZoomed = false;
    this.easeCameraTo(this.stationPresets.default.pos, this.stationPresets.default.target, 450);
  }

  onWindowResize() {
    if (!this.camera || !this.renderer) return;
    this.camera.aspect = window.innerWidth / window.innerHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    const maxRatio = this.quality === 'high' ? 1.5 : 1.0;
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, maxRatio));
  }

  onPointerMove(event) {
    const rect = this.canvas.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    // Raycast apparatus and interactive fixtures
    const candidates = [];
    if (this.apparatusContainer) candidates.push(...this.apparatusContainer.children);
    if (this.roomGroup) candidates.push(...this.roomGroup.children);
    if (candidates.length === 0) return;

    this.raycaster.setFromCamera(this.mouse, this.camera);
    const intersects = this.raycaster.intersectObjects(candidates, true);

    if (intersects.length > 0) {
      // Find top apparatus group with userData.targetId
      let current = intersects[0].object;
      while (current && !current.userData?.targetId && current.parent && current.parent !== this.scene) {
        current = current.parent;
      }

      if (current && current.userData?.targetId) {
        if (this.hoveredObject !== current) {
          this.clearHover();
          this.hoveredObject = current;
          this.applyHoverHighlight(current, true);
          this.canvas.style.cursor = 'pointer';
        }
        return;
      }
    }

    if (this.hoveredObject) {
      this.clearHover();
      this.canvas.style.cursor = 'default';
    }
  }

  onPointerDown(event) {
    if (event.button !== 0) return; // Left click only

    if (this.hoveredObject && this.hoveredObject.userData?.targetId) {
      const targetId = this.hoveredObject.userData.targetId;
      if (targetId === 'virtual_trial_screen') {
        state.emit('open_trial_panel');
      } else if (targetId === 'protocol_board') {
        if (this.isWhiteboardZoomed) {
          this.resetCameraView();
          this.isWhiteboardZoomed = false;
        } else {
          this.setStationCamera('whiteboard');
          this.isWhiteboardZoomed = true;
        }
        return;
      }
      this.isWhiteboardZoomed = false;
      state.setSelectedTarget(targetId);
      this.selectApparatus(this.hoveredObject);
    }
  }

  applyHoverHighlight(obj, enable) {
    obj.traverse((child) => {
      if (child.isMesh && child.material) {
        if (enable) {
          if (!child.userData.origEmissive) {
            child.userData.origEmissive = child.material.emissive ? child.material.emissive.getHex() : 0;
          }
          if (child.material.emissive) {
            child.material.emissive.setHex(0x9333ea);
          }
        } else {
          if (child.material.emissive && child.userData.origEmissive !== undefined) {
            child.material.emissive.setHex(child.userData.origEmissive);
          }
        }
      }
    });
  }

  clearHover() {
    if (this.hoveredObject) {
      this.applyHoverHighlight(this.hoveredObject, false);
      this.hoveredObject = null;
    }
  }

  selectApparatus(obj) {
    if (this.selectedObject) {
      this.applyHoverHighlight(this.selectedObject, false);
    }
    this.selectedObject = obj;
    this.focusOnStation(obj.userData.targetId);
  }

  animate() {
    this.animationFrameId = requestAnimationFrame(this.animate);

    // Pause rendering when tab is hidden to save GPU battery
    if (this.isTabHidden) return;

    const now = performance.now();
    const dt = Math.min(0.1, (now - this.lastTime) / 1000);
    this.lastTime = now;

    // Run registered sub-system update callbacks (character, particles, etc.)
    for (let i = 0; i < this.updateCallbacks.length; i++) {
      try {
        this.updateCallbacks[i](dt);
      } catch (err) {
        console.error('Error in scene update callback:', err);
      }
    }

    // Smooth camera transition / Action camera easing
    if (this.cameraTransition) {
      this.updateCameraTransition(now);
    }

    // Controls update
    if (this.controls) {
      this.controls.update();
    }

    // Render
    if (this.renderer && this.scene && this.camera) {
      this.renderer.render(this.scene, this.camera);

      // FPS and Draw Calls counter for debug overlay
      this.frameCount++;
      if (now - this.fpsTimer >= 1000) {
        const fps = Math.round((this.frameCount * 1000) / (now - this.fpsTimer));
        const drawCalls = this.renderer.info.render.calls;
        state.updateStats({ fps, drawCalls });

        // Auto Quality: If average FPS < 25 over a 5s window, step down once to Low quality (never auto-step up)
        if (!this.autoQualityLocked && !this.hasAutoDowngraded && this.quality === 'high') {
          this.fpsSamples.push(fps);
          if (this.fpsSamples.length > 5) {
            this.fpsSamples.shift();
          }
          if (this.fpsSamples.length >= 5) {
            const avgFps = this.fpsSamples.reduce((a, b) => a + b, 0) / this.fpsSamples.length;
            if (avgFps < 25) {
              this.hasAutoDowngraded = true;
              this.setQuality('low', true);
            }
          }
        }

        this.frameCount = 0;
        this.fpsTimer = now;
      }
    }
  }

  destroy() {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }
    window.removeEventListener('resize', this.onWindowResize);
    this.canvas.removeEventListener('pointermove', this.onPointerMove);
    this.canvas.removeEventListener('pointerdown', this.onPointerDown);
    this.renderer.dispose();
  }
}
