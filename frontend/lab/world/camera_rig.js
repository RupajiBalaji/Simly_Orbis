/**
 * Continuous Follow Camera Rig & Obstacle Avoidance (frontend/lab/world/camera_rig.js)
 * Implements smooth third-person character following, HUD-aware view offset framing,
 * relative local-frame action camera, dead-zone panning, and dynamic blocker collision.
 */

import * as THREE from 'three';
import { state } from '../state.js';

export const CameraMode = {
  FOLLOW: 'FOLLOW',
  STATION: 'STATION',
  FREE: 'FREE',
  FIRST_PERSON: 'FIRST_PERSON',
};

// Relative action camera offsets in local frame of (target apparatus, avatar facing)
const ACTION_SHOT_OFFSETS = {
  weigh: { right: 1.15, back: 1.25, height: 0.38, targetY: 0.18 },
  tare: { right: 1.10, back: 1.20, height: 0.35, targetY: 0.15 },
  pour: { right: 1.10, back: 1.30, height: 0.40, targetY: 0.20 },
  dissolve: { right: 1.10, back: 1.30, height: 0.40, targetY: 0.20 },
  titrate: { right: 1.05, back: 1.25, height: 0.38, targetY: 0.22 },
  pipette: { right: 1.05, back: 1.20, height: 0.35, targetY: 0.18 },
  administer: { right: 1.20, back: 1.30, height: 0.42, targetY: 0.25 },
  draw_blood: { right: 1.20, back: 1.25, height: 0.36, targetY: 0.20 },
  write_label: { right: 1.05, back: 1.15, height: 0.35, targetY: 0.18 },
  label: { right: 1.05, back: 1.15, height: 0.35, targetY: 0.18 },
  wash_hands: { right: 1.10, back: 1.25, height: 0.40, targetY: 0.20 },
  run_assay: { right: 1.10, back: 1.25, height: 0.40, targetY: 0.20 },
  centrifuge: { right: 1.10, back: 1.25, height: 0.40, targetY: 0.20 },
  dispose: { right: 1.10, back: 1.25, height: 0.40, targetY: 0.20 },
};

export class CameraRig {
  constructor(labScene) {
    this.labScene = labScene;
    this.camera = labScene.camera;
    this.controls = labScene.controls;
    this.mode = CameraMode.FOLLOW;

    // Follow smoothing and state
    this.target = new THREE.Vector3().copy(this.controls.target);
    this.desiredTarget = new THREE.Vector3();
    this.lastAvatarPos = new THREE.Vector3();

    // Reusable pre-allocated math objects (zero per-frame allocations)
    this._vDelta = new THREE.Vector3();
    this._vHeading = new THREE.Vector3();
    this._vChasePos = new THREE.Vector3();
    this._vProj = new THREE.Vector3();
    this._vAvLook = new THREE.Vector3();
    this._vRayDir = new THREE.Vector3();
    this._vCamToApp = new THREE.Vector3();
    this._vCamToAv = new THREE.Vector3();
    this._camRight = new THREE.Vector3();
    this._camUp = new THREE.Vector3();
    this._ray = new THREE.Ray();
    this._tmpBox = new THREE.Box3();

    // User interaction tracking
    this.lastUserOrbitTime = 0;
    this.isUserInteracting = false;
    this.userOrbitDetected = false;

    // HUD and viewport tracking
    this.freeViewport = { left: 0, top: 0, right: window.innerWidth, bottom: window.innerHeight, width: window.innerWidth, height: window.innerHeight };
    this.lastViewportUpdate = 0;

    // Action camera relative clip state
    this.activeActionClip = null;
    this.isActionCameraActive = false;
    this.savedStateBeforeAction = null;

    // Collision data
    this.blockerBoxes = [];
    this.blockerMeshes = [];
    this.roomBounds = new THREE.Box3(
      new THREE.Vector3(-7.4, 0.75, -6.6),
      new THREE.Vector3(7.4, 4.8, 2.0)
    );
    this.railingZ = 1.85;

    // Preferences
    this.prefersReducedMotion = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)').matches : false;

    this.initControlsListeners();
    this.updateHUDFrustum();
  }

  initControlsListeners() {
    if (!this.controls) return;
    this.controls.addEventListener('start', () => {
      this.isUserInteracting = true;
      this.lastUserOrbitTime = performance.now();
      this.userOrbitDetected = true;
    });
    this.controls.addEventListener('change', () => {
      if (this.isUserInteracting) {
        this.lastUserOrbitTime = performance.now();
      }
    });
    this.controls.addEventListener('end', () => {
      this.isUserInteracting = false;
      this.lastUserOrbitTime = performance.now();
    });

    // Mobile / touch double-tap to recenter
    let lastTapTime = 0;
    const domEl = this.labScene?.canvas;
    if (domEl) {
      domEl.addEventListener('touchend', () => {
        const currentTime = performance.now();
        const tapLength = currentTime - lastTapTime;
        if (tapLength < 300 && tapLength > 50) {
          this.recenter();
        }
        lastTapTime = currentTime;
      }, { passive: true });
    }
  }

  setMode(mode) {
    if (this.mode === mode) return;
    const oldMode = this.mode;
    this.mode = mode;

    // Restore avatar visibility if leaving first-person
    if (oldMode === CameraMode.FIRST_PERSON && mode !== CameraMode.FIRST_PERSON) {
      const controller = this.labScene?.characterController;
      if (controller) {
        if (typeof controller.setFirstPersonHandsMode === 'function') {
          controller.setFirstPersonHandsMode(false);
        } else {
          controller.setAvatarOpacity(1.0);
        }
        if (controller.rig?.root) controller.rig.root.visible = true;
      }
      this.controls.minDistance = 1.0;
      this.controls.maxDistance = 16.0;
    }

    this.updateHUDModeUI();
    state.notify?.('camera_mode_changed', { mode });
  }

  toggleMode() {
    if (this.mode === CameraMode.FIRST_PERSON) {
      this.setMode(CameraMode.FOLLOW);
      this.recenter(true);
    } else if (this.mode === CameraMode.FOLLOW) {
      this.setMode(CameraMode.FREE);
    } else {
      this.setMode(CameraMode.FOLLOW);
    }
    return this.mode;
  }

  toggleFirstPerson() {
    if (this.mode === CameraMode.FIRST_PERSON) {
      this.setMode(CameraMode.FOLLOW);
      this.recenter(true);
      return CameraMode.FOLLOW;
    } else {
      const controller = this.labScene?.characterController;
      if (controller) {
        if (typeof controller.setFirstPersonHandsMode === 'function') {
          controller.setFirstPersonHandsMode(true);
        } else {
          controller.setAvatarOpacity(0.0);
        }
        if (controller.rig?.root) controller.rig.root.visible = true;
      }
      this.mode = CameraMode.FIRST_PERSON;
      this.controls.minDistance = 0.05;
      this.controls.maxDistance = 8.0;

      const avatar = controller?.rig?.root;
      if (avatar) {
        const avPos = avatar.position;
        const heading = avatar.rotation.y;
        const fwdX = Math.sin(heading);
        const fwdZ = Math.cos(heading);
        const eyePos = new THREE.Vector3(avPos.x - fwdX * 0.04, avPos.y + 1.25, avPos.z - fwdZ * 0.04);
        const lookTarget = new THREE.Vector3(avPos.x + fwdX * 2.5, avPos.y + 1.05, avPos.z + fwdZ * 2.5);
        this.camera.position.copy(eyePos);
        this.controls.target.copy(lookTarget);
        this.target.copy(lookTarget);
        this.controls.update();
      }
      this.updateHUDModeUI();
      return CameraMode.FIRST_PERSON;
    }
  }

  updateHUDModeUI() {
    const btn = document.getElementById('btn-toggle-camera-mode');
    if (btn) {
      if (this.mode === CameraMode.FIRST_PERSON) {
        btn.textContent = '🎥 Cam: 1st Person';
      } else if (this.mode === CameraMode.FOLLOW) {
        btn.textContent = '🎥 Cam: Follow';
      } else {
        btn.textContent = '🎥 Cam: Free';
      }
    }
    const btnFp = document.getElementById('btn-toggle-first-person');
    if (btnFp) {
      btnFp.textContent = this.mode === CameraMode.FIRST_PERSON ? '👁️ 3rd Person' : '👁️ 1st Person';
    }
  }

  buildCollisionData() {
    this.blockerBoxes = [];
    this.blockerMeshes = [];
    if (!this.labScene?.scene) return;

    this.labScene.scene.traverse((obj) => {
      if (obj.userData?.camBlocker) {
        const box = new THREE.Box3().setFromObject(obj);
        // Expand slightly for camera radius padding
        box.expandByScalar(0.08);
        this.blockerBoxes.push(box);
        this.blockerMeshes.push(obj);
      }
    });

    // Compute room bounds if room exists
    if (this.labScene.roomGroup) {
      this.roomBounds.setFromObject(this.labScene.roomGroup);
      this.roomBounds.min.x = Math.max(-7.4, this.roomBounds.min.x + 0.3);
      this.roomBounds.max.x = Math.min(7.4, this.roomBounds.max.x - 0.3);
      this.roomBounds.min.z = Math.max(-6.6, this.roomBounds.min.z + 0.3);
      this.roomBounds.min.y = 0.75;
      this.roomBounds.max.y = 4.8;
    }
  }

  getFreeViewportRect() {
    const W = window.innerWidth;
    const H = window.innerHeight;

    let leftInset = 0;
    let rightInset = 0;
    let topInset = 0;
    let bottomInset = 0;

    const isVis = (el) => {
      if (!el) return false;
      const s = window.getComputedStyle(el);
      return s.display !== 'none' && s.visibility !== 'hidden' && s.opacity !== '0';
    };

    // 1. Top bar & next step banner
    const topBar = document.querySelector('.hud-top-bar');
    if (topBar && isVis(topBar)) {
      const r = topBar.getBoundingClientRect();
      if (r.bottom > 0 && r.bottom < H * 0.35) {
        topInset = Math.max(topInset, r.bottom);
      }
    }
    const nextBanner = document.getElementById('hud-next-step-banner');
    if (nextBanner && isVis(nextBanner)) {
      const r = nextBanner.getBoundingClientRect();
      if (r.bottom > 0 && r.bottom < H * 0.35) {
        topInset = Math.max(topInset, r.bottom);
      } else if (r.top > H * 0.65 && r.top < H) {
        bottomInset = Math.max(bottomInset, H - r.top);
      }
    }

    // 2. Left protocol panel
    const leftPanel = document.getElementById('hud-protocol-panel');
    if (leftPanel && isVis(leftPanel) && !leftPanel.classList.contains('hidden')) {
      const r = leftPanel.getBoundingClientRect();
      if (r.width > 0 && r.right > 0 && r.right < W * 0.45) {
        leftInset = Math.max(leftInset, r.right);
      }
    }

    // 3. Right panel (if expanded)
    const rightPanel = document.getElementById('hud-right-panel');
    if (rightPanel && isVis(rightPanel) && !rightPanel.classList.contains('collapsed')) {
      const r = rightPanel.getBoundingClientRect();
      if (r.width > 0 && r.left < W && r.left > W * 0.55) {
        rightInset = Math.max(rightInset, W - r.left);
      }
    }

    // 4. Mentor card (if expanded)
    const mentorCard = document.getElementById('mentor-docked-card');
    const mentorBody = document.getElementById('mentor-body');
    if (mentorCard && isVis(mentorCard) && mentorBody && isVis(mentorBody)) {
      const r = mentorCard.getBoundingClientRect();
      if (r.left > W * 0.55) {
        rightInset = Math.max(rightInset, W - r.left);
      }
    }

    // 5. Bottom dock (Station strip + Action bar)
    const bottomDock = document.querySelector('.hud-bottom-dock');
    if (bottomDock && isVis(bottomDock)) {
      const r = bottomDock.getBoundingClientRect();
      if (r.top < H && r.height > 0) {
        bottomInset = Math.max(bottomInset, H - r.top);
      }
    }

    const pad = 8;
    const freeLeft = Math.max(0, leftInset + pad);
    const freeRight = Math.min(W, W - rightInset - pad);
    const freeTop = Math.max(0, topInset + pad);
    const freeBottom = Math.max(freeTop + 200, Math.min(H, H - bottomInset - pad));

    const freeWidth = Math.max(200, freeRight - freeLeft);
    const freeHeight = Math.max(200, freeBottom - freeTop);

    return {
      left: freeLeft,
      top: freeTop,
      right: freeRight,
      bottom: freeBottom,
      width: freeWidth,
      height: freeHeight,
      fullWidth: W,
      fullHeight: H,
    };
  }

  updateHUDFrustum() {
    this.freeViewport = this.getFreeViewportRect();
    if (this.camera) {
      this.camera.clearViewOffset();
    }
  }

  isAvatarInDeadZone(avatarPos) {
    if (!this.camera) return true;
    this._vAvLook.copy(avatarPos).add(new THREE.Vector3(0, 1.15, 0));
    this._vProj.copy(this._vAvLook).project(this.camera);

    // Convert NDC [-1, 1] to screen pixels
    const W = window.innerWidth;
    const H = window.innerHeight;
    const sx = (this._vProj.x + 1) * 0.5 * W;
    const sy = (-this._vProj.y + 1) * 0.5 * H;

    const r = this.freeViewport;
    const cx = r.left + r.width * 0.5;
    const cy = r.top + r.height * 0.5;

    // Central 40% dead-zone box
    const halfDeadW = r.width * 0.20;
    const halfDeadH = r.height * 0.20;

    return (
      sx >= cx - halfDeadW &&
      sx <= cx + halfDeadW &&
      sy >= cy - halfDeadH &&
      sy <= cy + halfDeadH &&
      this._vProj.z >= -1 &&
      this._vProj.z <= 1
    );
  }

  recenter(instant = false) {
    const avatar = this.labScene?.characterController?.rig?.root;
    if (!avatar) return;

    this.isActionCameraActive = false;
    this.activeActionClip = null;
    this.mode = CameraMode.FOLLOW;
    if (this.labScene) {
      this.labScene.isActionCameraActive = false;
      this.labScene.cameraTransition = null;
    }

    const avPos = avatar.position;
    const heading = avatar.rotation.y;
    // Forward and Right vectors from heading
    const fwdX = Math.sin(heading);
    const fwdZ = Math.cos(heading);
    const rightX = Math.cos(heading);
    const rightZ = -Math.sin(heading);

    // Place camera behind and slightly to side of avatar (distance 4.2m, height 2.1m)
    const targetPos = new THREE.Vector3(avPos.x, avPos.y + 1.15, avPos.z);
    const camPos = new THREE.Vector3(
      avPos.x - fwdX * 4.0 + rightX * 0.5,
      avPos.y + 2.1,
      avPos.z - fwdZ * 4.0 + rightZ * 0.5
    );

    this.resolveCollision(camPos, targetPos);

    if (instant || state.skipAnimation) {
      this.camera.position.copy(camPos);
      this.controls.target.copy(targetPos);
      this.target.copy(targetPos);
      this.controls.update();
    } else {
      this.labScene.easeCameraTo(camPos, targetPos, 280);
    }
  }

  startRelativeActionCamera(apparatusObj, clipName, durationMs = 1800) {
    if (state.skipAnimation) return;

    const controller = this.labScene.characterController;
    const avatar = controller?.rig?.root;
    if (!avatar || !apparatusObj) return;

    if (!this.isActionCameraActive) {
      this.savedStateBeforeAction = {
        camPos: this.camera.position.clone(),
        target: this.controls.target.clone(),
        mode: this.mode,
      };
      this.isActionCameraActive = true;
      this.labScene.isActionCameraActive = true;
      this.labScene.updateNameTagVisibility();
    }

    const normClip = (clipName || '').toLowerCase();
    let shotKey = Object.keys(ACTION_SHOT_OFFSETS).find((k) => normClip.includes(k)) || 'weigh';
    const offsets = ACTION_SHOT_OFFSETS[shotKey] || ACTION_SHOT_OFFSETS.weigh;

    this.activeActionClip = {
      apparatus: apparatusObj,
      offsets,
      durationMs,
      startTime: performance.now(),
      shotKey,
    };

    // Calculate initial relative target and position
    this.computeRelativeActionPose(this.activeActionClip, this._vChasePos, this.desiredTarget);
    this.resolveCollision(this._vChasePos, this.desiredTarget);
    this.labScene.easeCameraTo(this._vChasePos, this.desiredTarget, 320);
  }

  computeRelativeActionPose(clipState, outCamPos, outTarget) {
    const controller = this.labScene.characterController;
    const avatar = controller?.rig?.root;
    const appObj = clipState.apparatus;

    const appPos = new THREE.Vector3();
    appObj.getWorldPosition(appPos);

    const avPos = avatar ? avatar.position : appPos;
    const heading = avatar ? avatar.rotation.y : 0;
    const fwdX = Math.sin(heading);
    const fwdZ = Math.cos(heading);
    const rightX = Math.cos(heading);
    const rightZ = -Math.sin(heading);

    const off = clipState.offsets;
    outTarget.set(appPos.x, appPos.y + off.targetY, appPos.z);

    // Compute relative camera position from local frame
    outCamPos.set(
      appPos.x + rightX * off.right - fwdX * off.back,
      Math.max(1.15, appPos.y + off.height),
      appPos.z + rightZ * off.right - fwdZ * off.back
    );

    // Occlusion check: if avatar torso still occludes line of sight to target, fade avatar to 40%
    this._vCamToApp.subVectors(outTarget, outCamPos);
    this._vCamToAv.subVectors(new THREE.Vector3(avPos.x, 1.25, avPos.z), outCamPos);
    const proj = this._vCamToAv.dot(this._vCamToApp.clone().normalize());
    const perpDist = Math.sqrt(Math.max(0, this._vCamToAv.lengthSq() - proj * proj));
    const isBetween = proj > 0.2 && proj < this._vCamToApp.length() - 0.2;
    const avatarOccludes = isBetween && perpDist < 0.35;

    if (avatarOccludes && controller) {
      controller.setAvatarOpacity(0.40);
      this.labScene.isAvatarFaded = true;
    }
  }

  endRelativeActionCamera() {
    if (!this.isActionCameraActive) return;
    this.isActionCameraActive = false;
    this.activeActionClip = null;
    this.labScene.isActionCameraActive = false;
    this.labScene.updateNameTagVisibility();

    if (this.labScene.isAvatarFaded && this.labScene.characterController) {
      this.labScene.characterController.setAvatarOpacity(1.0);
      this.labScene.isAvatarFaded = false;
    }

    if (state.skipAnimation) {
      if (this.savedStateBeforeAction) {
        this.camera.position.copy(this.savedStateBeforeAction.camPos);
        this.controls.target.copy(this.savedStateBeforeAction.target);
        this.target.copy(this.savedStateBeforeAction.target);
      }
      return;
    }

    if (this.savedStateBeforeAction) {
      this.labScene.easeCameraTo(
        this.savedStateBeforeAction.camPos,
        this.savedStateBeforeAction.target,
        350
      );
    }
  }

  resolveCollision(camPos, lookTarget) {
    // 1. Keep camera strictly inside room bounds
    const isGallery = this.labScene?.isGalleryMode;
    const maxZ = isGallery ? this.roomBounds.max.z : this.railingZ;

    camPos.x = Math.max(this.roomBounds.min.x, Math.min(this.roomBounds.max.x, camPos.x));
    camPos.y = Math.max(this.roomBounds.min.y, Math.min(this.roomBounds.max.y, camPos.y));
    camPos.z = Math.max(this.roomBounds.min.z, Math.min(maxZ, camPos.z));

    // 2. Raycast from lookTarget to camPos for sightline clearance
    this._vRayDir.subVectors(camPos, lookTarget);
    const rayDist = this._vRayDir.length();
    if (rayDist > 0.1) {
      this._vRayDir.normalize();
      this._ray.set(lookTarget, this._vRayDir);

      for (let i = 0; i < this.blockerBoxes.length; i++) {
        const box = this.blockerBoxes[i];
        const hit = this._ray.intersectBox(box, this._vProj);
        if (hit) {
          const hitDist = lookTarget.distanceTo(hit);
          if (hitDist > 0.2 && hitDist < rayDist) {
            // Blocked: pull camera in front of obstacle along sightline
            const safeDist = Math.max(0.9, hitDist - 0.25);
            camPos.copy(lookTarget).addScaledVector(this._vRayDir, safeDist);
            break;
          }
        }
      }
    }

    // 3. Ensure camPos never penetrates inside any blocker box
    for (let i = 0; i < this.blockerBoxes.length; i++) {
      const box = this.blockerBoxes[i];
      if (box.containsPoint(camPos)) {
        const dy = box.max.y - camPos.y;
        if (dy > 0 && dy < 1.2) {
          camPos.y = box.max.y + 0.15;
        } else {
          // Push horizontally toward look target
          const toTarget = lookTarget.clone().sub(camPos);
          toTarget.y = 0;
          if (toTarget.lengthSq() > 0.001) {
            camPos.add(toTarget.normalize().multiplyScalar(0.40));
          }
        }
      }
    }
  }

  isInsideBlocker(pos) {
    for (let i = 0; i < this.blockerBoxes.length; i++) {
      if (this.blockerBoxes[i].containsPoint(pos)) return true;
    }
    return false;
  }

  update(dt) {
    if (!this.camera || !this.controls) return;
    const clampedDt = Math.min(0.05, Math.max(0.001, dt));
    const now = performance.now();

    // Recompute HUD framing on resize or periodically
    if (now - this.lastViewportUpdate > 250) {
      this.lastViewportUpdate = now;
      this.updateHUDFrustum();
    }

    // 1. If currently inside active relative Action Camera, recompute every frame
    if (this.isActionCameraActive && this.activeActionClip) {
      this.computeRelativeActionPose(this.activeActionClip, this._vChasePos, this.desiredTarget);
      this.resolveCollision(this._vChasePos, this.desiredTarget);

      // Smoothly follow any movement during action
      const k = 6.0;
      const alpha = 1.0 - Math.exp(-k * clampedDt);
      this.camera.position.lerp(this._vChasePos, alpha);
      this.controls.target.lerp(this.desiredTarget, alpha);
      this.target.copy(this.controls.target);
      return;
    }

    // If scene is currently easing (e.g. to a station preset or easing back), sync target and skip follow delta
    if (this.labScene?.cameraTransition) {
      this.target.copy(this.controls.target);
      return;
    }

    // 2. STATION mode: fixed presets, controls only
    if (this.mode === CameraMode.STATION) {
      return;
    }

    // 3. FREE mode: OrbitControls only, no avatar tracking
    if (this.mode === CameraMode.FREE) {
      return;
    }

    // 3b. FIRST_PERSON mode: Camera locked to avatar eye position, mouse controls look direction
    if (this.mode === CameraMode.FIRST_PERSON) {
      const controller = this.labScene?.characterController;
      const avatar = controller?.rig?.root;
      if (avatar) {
        const avPos = avatar.position;
        const heading = avatar.rotation.y;
        const fwdX = Math.sin(heading);
        const fwdZ = Math.cos(heading);
        const eyePos = this._vChasePos.set(avPos.x - fwdX * 0.04, avPos.y + 1.25, avPos.z - fwdZ * 0.04);
        const delta = this._vDelta.subVectors(eyePos, this.camera.position);
        this.camera.position.copy(eyePos);
        this.controls.target.add(delta);
        this.target.copy(this.controls.target);
      }
      return;
    }

    // 4. FOLLOW MODE
    const controller = this.labScene?.characterController;
    const avatar = controller?.rig?.root;
    if (!avatar) return;

    const avPos = avatar.position;
    const isWalking = controller.isWalking;

    // Desired look target: avatar root position + (0, 1.15, 0) per specification
    this.desiredTarget.set(avPos.x, avPos.y + 1.15, avPos.z);

    // HUD-aware framing offset: shift look target so avatar projects to center of free viewport
    const r = this.freeViewport;
    const W = r.fullWidth;
    const H = r.fullHeight;
    const cx = (r.left + r.right) * 0.5;
    const cy = (r.top + r.bottom) * 0.5;
    const shiftX = cx - (W * 0.5);
    const shiftY = cy - (H * 0.5);

    const dist = Math.max(1.0, this.camera.position.distanceTo(this.controls.target));
    const fovRad = (this.camera.fov * Math.PI) / 180;
    const mPixel = (2.0 * dist * Math.tan(fovRad * 0.5)) / H;

    this._vRayDir.subVectors(this.controls.target, this.camera.position).normalize();
    this._vChasePos.set(0, 1, 0);
    this._camRight.crossVectors(this._vRayDir, this._vChasePos).normalize();
    this._camUp.crossVectors(this._camRight, this._vRayDir).normalize();

    this.desiredTarget.addScaledVector(this._camRight, -shiftX * mPixel);
    this.desiredTarget.addScaledVector(this._camUp, shiftY * mPixel);

    // Check dead-zone: only pan if avatar is outside central 40% of free viewport
    const insideDeadZone = this.isAvatarInDeadZone(avPos);

    if (!insideDeadZone || isWalking) {
      // Damping factor: k = 8.0 while walking (minimal trailing lag), 5.0 when idle
      const k = isWalking ? 8.0 : 5.0;
      const alpha = 1.0 - Math.exp(-k * clampedDt);

      // Compute delta to move target
      this._vDelta.copy(this.desiredTarget).sub(this.target).multiplyScalar(alpha);

      // Preserve user's orbit: shift controls.target AND camera.position by the SAME delta
      this.target.add(this._vDelta);
      this.controls.target.copy(this.target);
      this.camera.position.add(this._vDelta);
    }

    // Chase assist: while walking, gently ease camera yaw behind avatar unless user orbited in last 2s
    const userOrbitedRecently = (now - this.lastUserOrbitTime) < 2000;
    if (isWalking && !userOrbitedRecently && !this.prefersReducedMotion) {
      const heading = avatar.rotation.y;
      const fwdX = Math.sin(heading);
      const fwdZ = Math.cos(heading);
      const rightX = Math.cos(heading);
      const rightZ = -Math.sin(heading);

      // Spot behind and slightly to the side of heading (distance 4.2m, height 2.1m)
      this._vChasePos.set(
        this.target.x - fwdX * 4.0 + rightX * 0.4,
        this.target.y + 1.25,
        this.target.z - fwdZ * 4.0 + rightZ * 0.4
      );

      // Gentle yaw alignment (k ~ 2.0)
      const yawAlpha = 1.0 - Math.exp(-2.2 * clampedDt);
      this.camera.position.lerp(this._vChasePos, yawAlpha);
    }

    // Keep camera collision-free every frame
    this.resolveCollision(this.camera.position, this.controls.target);
  }
}
