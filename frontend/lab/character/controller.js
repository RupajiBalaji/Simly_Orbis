/**
 * Avatar Locomotion, Waypoint Navigation & Station Controller (frontend/lab/character/controller.js)
 * Coordinates character walking to apparatus stations, facing targets, and executing clips.
 */

import * as THREE from 'three';
import { createHumanoidAvatar } from './avatar.js';
import { AvatarAnimator } from './animation.js';

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
    this.targetPos = new THREE.Vector3();
    this.moveSpeed = 2.4; // m/s
    this.onArrival = null;

    // Carried mesh
    this.heldItem = null;
  }

  spawnForExperiment(experimentId) {
    if (experimentId === 'pk_ward') {
      // Spawn facing the Digital Balance at proper reach distance
      this.rig.root.position.set(-4.85, 0, -3.75);
      this.faceTarget(new THREE.Vector3(-4.5, 0.94, -4.2));
    } else {
      // Spawn to the side of the Burette Stand (unobstructed hero apparatus view & reachable)
      this.rig.root.position.set(-0.48, 0, -1.65);
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

  faceTarget(targetWorldPos) {
    const dir = targetWorldPos.clone().sub(this.rig.root.position);
    dir.y = 0;
    if (dir.lengthSq() > 0.001) {
      const angle = Math.atan2(dir.x, dir.z);
      this.rig.root.rotation.y = angle;
    }
  }

  carryItem(itemMesh) {
    if (this.heldItem) {
      this.dropHeldItem();
    }
    this.heldItem = itemMesh;
    if (itemMesh.parent) {
      itemMesh.parent.remove(itemMesh);
    }
    itemMesh.position.set(0, 0, 0);
    itemMesh.rotation.set(0, 0, 0);
    this.rig.heldItemSocket.add(itemMesh);
  }

  dropHeldItem(parentContainer, returnPos) {
    if (!this.heldItem) return;
    this.rig.heldItemSocket.remove(this.heldItem);
    if (parentContainer) {
      this.heldItem.position.copy(returnPos || new THREE.Vector3());
      parentContainer.add(this.heldItem);
    }
    this.heldItem = null;
  }

  executeActionAtStation(apparatusObject, clipName, durationMs, onFinished) {
    const stationPos = apparatusObject.userData.stationPos || new THREE.Vector3(0, 0, 0);
    const apparatusWorldPos = new THREE.Vector3();
    apparatusObject.getWorldPosition(apparatusWorldPos);

    const wrappedFinished = () => {
      this.dropHeldItem();
      if (onFinished) onFinished();
    };

    const startGesture = () => {
      this.faceTarget(apparatusWorldPos);
      const prop = this.createHeldProp(clipName);
      if (prop) {
        this.carryItem(prop);
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
      // Weighing dish with powder
      const dishGeo = new THREE.CylinderGeometry(0.045, 0.035, 0.015, 16);
      const dishMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
      const dish = new THREE.Mesh(dishGeo, dishMat);
      dish.position.set(0, -0.01, 0);
      propGroup.add(dish);

      const powderGeo = new THREE.CylinderGeometry(0.032, 0.032, 0.008, 12);
      const powderMat = new THREE.MeshStandardMaterial({ color: 0xf1f5f9, roughness: 0.9 });
      const powder = new THREE.Mesh(powderGeo, powderMat);
      powder.position.set(0, -0.005, 0);
      propGroup.add(powder);
      return propGroup;
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
    // 1. Locomotion step
    if (this.isWalking) {
      const currentPos = this.rig.root.position;
      const toTarget = this.targetPos.clone().sub(currentPos);
      toTarget.y = 0;
      const dist = toTarget.length();

      if (dist <= 0.08) {
        // Arrived at destination
        this.rig.root.position.copy(this.targetPos);
        this.isWalking = false;
        this.animator.playClip('idle');
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

    // 2. Animator update
    this.animator.update(dt);
  }
}
