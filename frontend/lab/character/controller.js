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
      // Spawn facing the Digital Balance
      this.rig.root.position.set(-3.8, 0, -3.2);
      this.faceTarget(new THREE.Vector3(-4.5, 0.94, -4.2));
    } else {
      // Spawn facing the Burette Stand
      this.rig.root.position.set(0, 0, -1.0);
      this.faceTarget(new THREE.Vector3(0, 0.94, -2.0));
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

    // 1. Walk to station
    const distToStation = this.rig.root.position.distanceTo(stationPos);
    if (distToStation > 0.3) {
      this.moveTo(stationPos, () => {
        // 2. Face apparatus
        this.faceTarget(apparatusWorldPos);
        // 3. Play gesture clip
        this.animator.playClip(clipName, apparatusWorldPos, durationMs, onFinished);
      });
    } else {
      this.faceTarget(apparatusWorldPos);
      this.animator.playClip(clipName, apparatusWorldPos, durationMs, onFinished);
    }
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
