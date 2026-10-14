/**
 * Avatar Locomotion, Waypoint Navigation & Station Controller (frontend/lab/character/controller.js)
 * Coordinates character walking to apparatus stations, facing targets, and executing clips.
 */

import * as THREE from 'three';
import { createHumanoidAvatar } from './avatar.js';
import { AvatarAnimator } from './animation.js';
import { soundFX } from '../audio/sound_fx.js';

export class CharacterController {
  constructor(scene) {
    this.scene = scene;
    this.rig = createHumanoidAvatar();
    this.animator = new AvatarAnimator(this.rig);

    this.scene.add(this.rig.root);

    // Initial default spawn position in center of room
    this.rig.root.position.set(0, 0, 0);
    this.rig.root.rotation.y = 0;

    // Locomotion state
    this.isWalking = false;
    this.isManualWalking = false;
    this.targetPos = new THREE.Vector3();
    this.moveSpeed = 2.4; // m/s
    this.onArrival = null;

    // Free WASD & Arrow keyboard input state
    this.keysDown = {
      KeyW: false,
      KeyA: false,
      KeyS: false,
      KeyD: false,
      ArrowUp: false,
      ArrowLeft: false,
      ArrowDown: false,
      ArrowRight: false,
      ShiftLeft: false,
      ShiftRight: false,
    };
    this.joystickInput = new THREE.Vector2(0, 0);

    this.onKeyDown = (e) => {
      const tag = e.target?.tagName?.toUpperCase();
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || e.target?.isContentEditable) return;
      const k = e.key?.toLowerCase();
      if (e.code === 'KeyW' || k === 'w') this.keysDown.KeyW = true;
      if (e.code === 'KeyA' || k === 'a') this.keysDown.KeyA = true;
      if (e.code === 'KeyS' || k === 's') this.keysDown.KeyS = true;
      if (e.code === 'KeyD' || k === 'd') this.keysDown.KeyD = true;
      if (e.code === 'ArrowUp' || e.key === 'ArrowUp') this.keysDown.ArrowUp = true;
      if (e.code === 'ArrowDown' || e.key === 'ArrowDown') this.keysDown.ArrowDown = true;
      if (e.code === 'ArrowLeft' || e.key === 'ArrowLeft') this.keysDown.ArrowLeft = true;
      if (e.code === 'ArrowRight' || e.key === 'ArrowRight') this.keysDown.ArrowRight = true;
      if (e.shiftKey || e.code === 'ShiftLeft' || e.code === 'ShiftRight') this.keysDown.ShiftLeft = true;
    };

    this.onKeyUp = (e) => {
      const k = e.key?.toLowerCase();
      if (e.code === 'KeyW' || k === 'w') this.keysDown.KeyW = false;
      if (e.code === 'KeyA' || k === 'a') this.keysDown.KeyA = false;
      if (e.code === 'KeyS' || k === 's') this.keysDown.KeyS = false;
      if (e.code === 'KeyD' || k === 'd') this.keysDown.KeyD = false;
      if (e.code === 'ArrowUp' || e.key === 'ArrowUp') this.keysDown.ArrowUp = false;
      if (e.code === 'ArrowDown' || e.key === 'ArrowDown') this.keysDown.ArrowDown = false;
      if (e.code === 'ArrowLeft' || e.key === 'ArrowLeft') this.keysDown.ArrowLeft = false;
      if (e.code === 'ArrowRight' || e.key === 'ArrowRight') this.keysDown.ArrowRight = false;
      if (!e.shiftKey && (e.code === 'ShiftLeft' || e.code === 'ShiftRight')) this.keysDown.ShiftLeft = false;
    };

    window.addEventListener('keydown', this.onKeyDown);
    window.addEventListener('keyup', this.onKeyUp);

    // Carried mesh
    this.heldItem = null;
  }

  setJoystickInput(x, y) {
    this.joystickInput.set(x, y);
  }

  canMoveTo(newPos) {
    // 1. Room boundaries
    const maxZ = window.sceneManager?.isGalleryMode ? 7.2 : 1.70;
    if (newPos.x < -7.1 || newPos.x > 7.1 || newPos.z < -6.3 || newPos.z > maxZ) {
      return false;
    }

    // 2. Obstacle boxes from cameraRig
    const blockerBoxes = window.sceneManager?.cameraRig?.blockerBoxes || [];
    const r = 0.15;
    for (let i = 0; i < blockerBoxes.length; i++) {
      const box = blockerBoxes[i];
      // Only obstacles that occupy floor/bench height (y <= 0.95) block the avatar
      if (box.min.y <= 0.95) {
        if (
          newPos.x >= box.min.x - r &&
          newPos.x <= box.max.x + r &&
          newPos.z >= box.min.z - r &&
          newPos.z <= box.max.z + r
        ) {
          return false;
        }
      }
    }
    return true;
  }

  spawnForExperiment(experimentId) {
    if (experimentId === 'pk_ward') {
      // Spawn standing at the balance station framing avatar, balance & ward in clear walkway
      this.rig.root.position.set(-3.85, 0, -2.85);
      this.faceTarget(new THREE.Vector3(-4.5, 0.94, -4.2));
    } else {
      // Spawn to the side of the Burette Stand in clear walkway
      this.rig.root.position.set(-0.25, 0, -0.90);
      this.faceTarget(new THREE.Vector3(0.02, 1.25, -1.85));
    }
    this.animator.playClip('idle');
  }

  updatePPE(ppeSet) {
    this.rig.updatePPE(ppeSet);
  }

  moveTo(targetPos, onArrival = null) {
    this.targetPos.copy(targetPos);
    this.targetPos.y = 0; // stay on floor
    this.onArrival = onArrival;
    this.isWalking = true;
    this.animator.playClip('walk');
  }

  walkToStation(stationId, onArrival = null) {
    const app = window.sceneManager?.getApparatus(stationId);
    if (app && app.userData?.stationPos) {
      this.moveTo(app.userData.stationPos, onArrival);
      return true;
    }
    return false;
  }

  faceTarget(targetWorldPos) {
    const dir = targetWorldPos.clone().sub(this.rig.root.position);
    dir.y = 0;
    if (dir.lengthSq() > 0.001) {
      const angle = Math.atan2(dir.x, dir.z);
      this.rig.root.rotation.y = angle;
    }
  }

  carryItem(itemMesh, leftItemMesh = null) {
    if (this.heldItem || this.leftHeldItem) {
      this.dropHeldItem();
    }
    if (itemMesh) {
      this.heldItem = itemMesh;
      if (itemMesh.parent) {
        itemMesh.parent.remove(itemMesh);
      }
      itemMesh.position.set(0, 0, 0);
      itemMesh.rotation.set(0, 0, 0);
      this.rig.heldItemSocket.add(itemMesh);
      this.rig?.setGrip?.(true, false);
    }
    if (leftItemMesh && this.rig.leftHeldItemSocket) {
      this.leftHeldItem = leftItemMesh;
      if (leftItemMesh.parent) {
        leftItemMesh.parent.remove(leftItemMesh);
      }
      leftItemMesh.position.set(0, 0, 0);
      leftItemMesh.rotation.set(0, 0, 0);
      this.rig.leftHeldItemSocket.add(leftItemMesh);
      this.rig?.setGrip?.(true, true);
    }
  }

  dropHeldItem(parentContainer, returnPos) {
    if (this.heldItem) {
      this.rig.heldItemSocket.remove(this.heldItem);
      if (parentContainer) {
        this.heldItem.position.copy(returnPos || new THREE.Vector3());
        parentContainer.add(this.heldItem);
      }
      this.heldItem = null;
      this.rig?.setGrip?.(false, false);
    }
    if (this.leftHeldItem && this.rig.leftHeldItemSocket) {
      this.rig.leftHeldItemSocket.remove(this.leftHeldItem);
      this.leftHeldItem = null;
      this.rig?.setGrip?.(false, true);
    }
  }

  setAvatarOpacity(opacity = 1.0) {
    if (this.rig && typeof this.rig.setOpacity === 'function') {
      this.rig.setOpacity(opacity);
    }
  }

  setFirstPersonHandsMode(enabled) {
    if (this.rig && typeof this.rig.setFirstPersonHandsMode === 'function') {
      this.rig.setFirstPersonHandsMode(enabled);
    }
  }

  executeActionAtStation(apparatusObject, clipName, durationMs, onFinished, onArrival = null) {
    if (this.isWalking) {
      this.isWalking = false;
      this.onArrival = null;
    }
    const stationPos = apparatusObject.userData.stationPos || new THREE.Vector3(0, 0, 0);
    const apparatusWorldPos = new THREE.Vector3();
    apparatusObject.getWorldPosition(apparatusWorldPos);

    const wrappedFinished = () => {
      this.dropHeldItem();
      if (onFinished) onFinished();
    };

    const startGesture = () => {
      this.faceTarget(apparatusWorldPos);
      if (typeof onArrival === 'function') {
        onArrival();
      }
      const props = this.createHeldProp(clipName);
      if (props) {
        if (props.isGroup || props.isMesh) {
          this.carryItem(props);
        } else if (props.right || props.left) {
          this.carryItem(props.right, props.left);
        }
      }
      this.animator.playClip(clipName, apparatusWorldPos, durationMs, wrappedFinished);
    };

    // 1. Walk to station
    const distToStation = this.rig.root.position.distanceTo(stationPos);
    if (distToStation > 0.3) {
      this.moveTo(stationPos, startGesture);
    } else {
      startGesture();
    }
  }

  createHeldProp(clipName) {
    const propGroup = new THREE.Group();

    if (clipName === 'weigh') {
      // 1. Right Hand: Stainless Steel Laboratory Spatula with blade & powder tip
      const spatulaGroup = new THREE.Group();
      const handleGeo = new THREE.CylinderGeometry(0.0035, 0.0035, 0.16, 12);
      const metalMat = new THREE.MeshStandardMaterial({ color: 0xcfd8dc, metalness: 0.88, roughness: 0.18 });
      const handle = new THREE.Mesh(handleGeo, metalMat);
      handle.rotation.x = Math.PI / 2.8;
      spatulaGroup.add(handle);

      const bladeGeo = new THREE.BoxGeometry(0.015, 0.002, 0.045);
      const blade = new THREE.Mesh(bladeGeo, metalMat);
      blade.position.set(0, -0.04, 0.09);
      blade.rotation.x = Math.PI / 4;
      spatulaGroup.add(blade);

      const powderTipGeo = new THREE.ConeGeometry(0.007, 0.005, 8);
      const powderTipMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.95 });
      const powderTip = new THREE.Mesh(powderTipGeo, powderTipMat);
      powderTip.position.set(0, -0.038, 0.10);
      spatulaGroup.add(powderTip);

      // 2. Left Hand: Dosing / Weighing Cup with white powder inside
      const cupGroup = new THREE.Group();
      const cupGeo = new THREE.CylinderGeometry(0.036, 0.028, 0.068, 16);
      const cupMat = new THREE.MeshStandardMaterial({ color: 0xe0f2fe, transparent: true, opacity: 0.72, roughness: 0.15 });
      const cup = new THREE.Mesh(cupGeo, cupMat);
      cup.position.set(0, -0.01, 0);
      cupGroup.add(cup);

      const powderInCupGeo = new THREE.CylinderGeometry(0.026, 0.024, 0.025, 12);
      const powderInCup = new THREE.Mesh(powderInCupGeo, powderTipMat);
      powderInCup.position.set(0, -0.022, 0);
      cupGroup.add(powderInCup);

      return { right: spatulaGroup, left: cupGroup };
    }

    if (clipName === 'dissolve' || clipName === 'administer') {
      // Dosing cup
      const cupGeo = new THREE.CylinderGeometry(0.035, 0.028, 0.065, 16);
      const cupMat = new THREE.MeshStandardMaterial({ color: 0xe0f2fe, transparent: true, opacity: 0.7, roughness: 0.1 });
      const cup = new THREE.Mesh(cupGeo, cupMat);
      cup.position.set(0, -0.02, 0);
      propGroup.add(cup);

      const liqGeo = new THREE.CylinderGeometry(0.032, 0.026, 0.04, 16);
      const liqMat = new THREE.MeshStandardMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.85 });
      const liq = new THREE.Mesh(liqGeo, liqMat);
      liq.position.set(0, -0.03, 0);
      propGroup.add(liq);
      return propGroup;
    }

    if (clipName === 'write_label') {
      // Laboratory marker pen
      const penGeo = new THREE.CylinderGeometry(0.007, 0.007, 0.13, 12);
      const penMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.4 });
      const pen = new THREE.Mesh(penGeo, penMat);
      pen.rotation.x = Math.PI / 3;
      propGroup.add(pen);
      return propGroup;
    }

    if (clipName === 'draw_blood') {
      // Venipuncture Syringe with blood chamber
      const barrelGeo = new THREE.CylinderGeometry(0.014, 0.014, 0.09, 12);
      const barrelMat = new THREE.MeshStandardMaterial({ color: 0xffffff, transparent: true, opacity: 0.7 });
      const barrel = new THREE.Mesh(barrelGeo, barrelMat);
      propGroup.add(barrel);

      const bloodGeo = new THREE.CylinderGeometry(0.012, 0.012, 0.06, 12);
      const bloodMat = new THREE.MeshStandardMaterial({ color: 0x991b1b, roughness: 0.2 });
      const blood = new THREE.Mesh(bloodGeo, bloodMat);
      blood.position.y = -0.01;
      propGroup.add(blood);

      const needleGeo = new THREE.CylinderGeometry(0.002, 0.002, 0.04, 8);
      const needleMat = new THREE.MeshStandardMaterial({ color: 0xcfd8dc, metalness: 0.9, roughness: 0.1 });
      const needle = new THREE.Mesh(needleGeo, needleMat);
      needle.position.y = -0.065;
      propGroup.add(needle);
      return propGroup;
    }

    if (clipName === 'pipette_analyte') {
      // Pipette with rubber bulb
      const pipGeo = new THREE.CylinderGeometry(0.006, 0.004, 0.18, 12);
      const pipMat = new THREE.MeshStandardMaterial({ color: 0xffffff, transparent: true, opacity: 0.75 });
      const pip = new THREE.Mesh(pipGeo, pipMat);
      propGroup.add(pip);

      const bulbGeo = new THREE.SphereGeometry(0.018, 12, 12);
      const bulbMat = new THREE.MeshStandardMaterial({ color: 0xef4444, roughness: 0.6 });
      const bulb = new THREE.Mesh(bulbGeo, bulbMat);
      bulb.position.y = 0.09;
      propGroup.add(bulb);
      return propGroup;
    }

    if (clipName === 'add_indicator') {
      // Dropper bottle
      const botGeo = new THREE.CylinderGeometry(0.02, 0.02, 0.07, 12);
      const botMat = new THREE.MeshStandardMaterial({ color: 0x78350f, roughness: 0.3 });
      const bot = new THREE.Mesh(botGeo, botMat);
      propGroup.add(bot);

      const dropBulb = new THREE.Mesh(new THREE.SphereGeometry(0.012, 10, 10), new THREE.MeshStandardMaterial({ color: 0x1e293b }));
      dropBulb.position.y = 0.045;
      propGroup.add(dropBulb);
      return propGroup;
    }

    if (clipName === 'run_assay') {
      // Specimen tube
      const tubeGeo = new THREE.CylinderGeometry(0.012, 0.012, 0.08, 12);
      const tubeMat = new THREE.MeshStandardMaterial({ color: 0xffffff, transparent: true, opacity: 0.7 });
      const tube = new THREE.Mesh(tubeGeo, tubeMat);
      propGroup.add(tube);

      const capGeo = new THREE.CylinderGeometry(0.013, 0.013, 0.018, 12);
      const capMat = new THREE.MeshStandardMaterial({ color: 0x7c3aed, roughness: 0.3 });
      const cap = new THREE.Mesh(capGeo, capMat);
      cap.position.y = 0.045;
      propGroup.add(cap);
      return propGroup;
    }

    return null;
  }

  update(dt) {
    // While a plan or action animation runs, player movement is locked and the Stop button still works.
    const isActionLocked = (this.animator.currentClip !== 'idle' && this.animator.currentClip !== 'walk') ||
                           Boolean(window.state?.isPending) ||
                           Boolean(window.agentPanel?.isRunningPlan);

    // 1. Manual keyboard / joystick free locomotion
    const rawFwd = !isActionLocked ? ((this.keysDown.KeyW || this.keysDown.ArrowUp ? 1 : 0) - (this.keysDown.KeyS || this.keysDown.ArrowDown ? 1 : 0) + this.joystickInput.y) : 0;
    const rawRight = !isActionLocked ? ((this.keysDown.KeyD || this.keysDown.ArrowRight ? 1 : 0) - (this.keysDown.KeyA || this.keysDown.ArrowLeft ? 1 : 0) + this.joystickInput.x) : 0;
    const isSprinting = this.keysDown.ShiftLeft || this.keysDown.ShiftRight;

    if (Math.hypot(rawFwd, rawRight) > 0.08) {
      // User manual control overrides any automated moveTo navigation
      this.onArrival = null;

      // Determine camera horizontal orientation
      const cam = window.sceneManager?.camera;
      let camAngle = 0;
      if (cam) {
        camAngle = Math.atan2(cam.position.x - this.rig.root.position.x, cam.position.z - this.rig.root.position.z) + Math.PI;
      }
      const fwdX = Math.sin(camAngle);
      const fwdZ = Math.cos(camAngle);
      const rightX = Math.cos(camAngle);
      const rightZ = -Math.sin(camAngle);

      const moveDirX = fwdX * rawFwd + rightX * rawRight;
      const moveDirZ = fwdZ * rawFwd + rightZ * rawRight;
      const len = Math.hypot(moveDirX, moveDirZ);
      const normX = moveDirX / len;
      const normZ = moveDirZ / len;

      const speed = isSprinting ? 4.0 : 2.4;
      const stepX = normX * speed * dt;
      const stepZ = normZ * speed * dt;

      // Smoothly rotate character to face travel heading
      const targetAngle = Math.atan2(normX, normZ);
      let diff = targetAngle - this.rig.root.rotation.y;
      while (diff < -Math.PI) diff += Math.PI * 2;
      while (diff > Math.PI) diff -= Math.PI * 2;
      this.rig.root.rotation.y += diff * Math.min(1.0, dt * 12.0);

      // Slide-based collision check
      const cur = this.rig.root.position;
      const tryBoth = new THREE.Vector3(cur.x + stepX, 0, cur.z + stepZ);
      if (this.canMoveTo(tryBoth)) {
        cur.copy(tryBoth);
      } else {
        const tryX = new THREE.Vector3(cur.x + stepX, 0, cur.z);
        if (this.canMoveTo(tryX)) {
          cur.copy(tryX);
        } else {
          const tryZ = new THREE.Vector3(cur.x, 0, cur.z + stepZ);
          if (this.canMoveTo(tryZ)) {
            cur.copy(tryZ);
          }
        }
      }

      this.isManualWalking = true;
      this.isWalking = true;
      if (this.animator.currentClip !== 'walk') {
        this.animator.playClip('walk');
      }

      // Footstep audio cadence
      const stepInterval = isSprinting ? 0.26 : 0.38;
      this.footstepTimer = (this.footstepTimer || 0) + dt;
      if (this.footstepTimer >= stepInterval) {
        this.footstepTimer = 0;
        soundFX.playFootstep();
      }
    } else if (this.isManualWalking) {
      // Manual walking stopped
      this.isManualWalking = false;
      this.isWalking = false;
      if (this.animator.currentClip === 'walk') {
        this.animator.playClip('idle');
      }
    } else if (this.isWalking) {
      // 2. Automated click-to-walk / waypoint navigation
      this.footstepTimer = (this.footstepTimer || 0) + dt;
      if (this.footstepTimer >= 0.38) {
        this.footstepTimer = 0;
        soundFX.playFootstep();
      }

      const currentPos = this.rig.root.position;
      const toTarget = this.targetPos.clone().sub(currentPos);
      toTarget.y = 0;
      const dist = toTarget.length();

      if (dist <= 0.08) {
        // Arrived at destination
        this.rig.root.position.copy(this.targetPos);
        this.isWalking = false;
        if (this.animator.currentClip === 'walk') {
          this.animator.playClip('idle');
        }
        const arrivalCallback = this.onArrival;
        this.onArrival = null;
        if (arrivalCallback) arrivalCallback();
      } else {
        // Rotate towards movement direction
        const moveAngle = Math.atan2(toTarget.x, toTarget.z);
        this.rig.root.rotation.y = moveAngle;

        // Step forward
        const stepDist = Math.min(dist, this.moveSpeed * dt);
        const step = toTarget.normalize().multiplyScalar(stepDist);
        this.rig.root.position.add(step);
      }
    }

    // 3. Animator update
    this.animator.update(dt);
  }
}
