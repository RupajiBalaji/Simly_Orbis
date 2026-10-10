/**
 * Analytical Two-Bone Inverse Kinematics (frontend/lab/character/ik.js)
 * Computes shoulder and elbow rotations to position the avatar's hand at a 3D target.
 */

import * as THREE from 'three';

export class TwoBoneIK {
  constructor(shoulderBone, elbowBone, handBone, isLeft = false) {
    this.shoulder = shoulderBone;
    this.elbow = elbowBone;
    this.hand = handBone;
    this.isLeft = isLeft;

    // Bone segment lengths
    this.l1 = 0.32; // upper arm length
    this.l2 = 0.28; // forearm length

    this.shoulderWorldPos = new THREE.Vector3();
    this.targetDir = new THREE.Vector3();
  }

  solve(targetWorldPos, poleHint = null) {
    this.shoulder.getWorldPosition(this.shoulderWorldPos);
    this.targetDir.subVectors(targetWorldPos, this.shoulderWorldPos);

    let dist = this.targetDir.length();
    const maxReach = this.l1 + this.l2 - 0.01;
    const minReach = Math.abs(this.l1 - this.l2) + 0.01;
    dist = Math.max(minReach, Math.min(dist, maxReach));

    // Law of cosines for elbow interior angle
    const cosElbow = (this.l1 * this.l1 + this.l2 * this.l2 - dist * dist) / (2 * this.l1 * this.l2);
    const elbowAngle = Math.PI - Math.acos(Math.max(-1, Math.min(1, cosElbow)));

    // Law of cosines for shoulder angle offset
    const cosShoulder = (this.l1 * this.l1 + dist * dist - this.l2 * this.l2) / (2 * this.l1 * dist);
    const shoulderAngleOffset = Math.acos(Math.max(-1, Math.min(1, cosShoulder)));

    // Apply orientation
    const localTarget = targetWorldPos.clone();
    this.shoulder.parent.worldToLocal(localTarget);

    const baseDir = localTarget.clone().sub(this.shoulder.position).normalize();

    // Shoulder pitch & yaw
    const yaw = Math.atan2(baseDir.x, -baseDir.z);
    const pitch = -Math.asin(Math.max(-1, Math.min(1, baseDir.y))) + shoulderAngleOffset;

    this.shoulder.rotation.set(pitch, yaw, this.isLeft ? 0.2 : -0.2);
    this.elbow.rotation.set(-elbowAngle, 0, 0);
  }
}
