/**
 * Analytical Two-Bone Inverse Kinematics (frontend/lab/character/ik.js)
 * Computes shoulder orientation matrix and elbow flexion angle to position
 * the avatar's hand at an exact 3D target with zero gimbal lock.
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

    this._m = new THREE.Matrix4();
  }

  solve(targetWorldPos, poleHint = null) {
    if (!this.shoulder || !this.elbow || !targetWorldPos) return;

    // 1. Transform target into torso local coordinates
    const torso = this.shoulder.parent;
    if (!torso) return;

    const targetLocal = torso.worldToLocal(targetWorldPos.clone());
    const shoulderLocal = this.shoulder.position.clone();

    // Vector from shoulder pivot to target in torso space
    const toTarget = new THREE.Vector3().subVectors(targetLocal, shoulderLocal);
    const rawDist = toTarget.length();
    if (rawDist < 0.001) return;

    // Clamped reachable distance
    const maxReach = this.l1 + this.l2 - 0.005;
    const minReach = Math.abs(this.l1 - this.l2) + 0.01;
    const dist = Math.max(minReach, Math.min(rawDist, maxReach));

    const u = toTarget.clone().normalize();
    const clampedTarget = shoulderLocal.clone().addScaledVector(u, dist);

    // 2. Law of cosines for shoulder elevation angle offset & elbow interior bend
    const cosShoulder = Math.max(-1, Math.min(1, (this.l1 * this.l1 + dist * dist - this.l2 * this.l2) / (2 * this.l1 * dist)));
    const thetaShoulder = Math.acos(cosShoulder);

    const cosElbow = Math.max(-1, Math.min(1, (this.l1 * this.l1 + this.l2 * this.l2 - dist * dist) / (2 * this.l1 * this.l2)));
    const alphaElbow = Math.acos(cosElbow);
    const thetaElbow = Math.PI - alphaElbow;

    // 3. Natural human pole hint (downward and slightly outward)
    let pole;
    if (poleHint) {
      pole = poleHint.clone().normalize();
    } else {
      pole = this.isLeft
        ? new THREE.Vector3(0.35, -0.75, -0.2).normalize()
        : new THREE.Vector3(-0.35, -0.75, -0.2).normalize();
    }

    // Arm triangle plane normal
    let n = new THREE.Vector3().crossVectors(u, pole);
    if (n.lengthSq() < 1e-4) {
      n.crossVectors(u, new THREE.Vector3(1, 0, 0));
    }
    n.normalize();

    // In-plane perpendicular to target ray u
    const b = new THREE.Vector3().crossVectors(n, u).normalize();

    // Upper arm unit vector in torso space
    const vUpper = new THREE.Vector3()
      .addScaledVector(u, Math.cos(thetaShoulder))
      .addScaledVector(b, Math.sin(thetaShoulder))
      .normalize();

    // Elbow position and forearm unit vector
    const elbowLocal = shoulderLocal.clone().addScaledVector(vUpper, this.l1);
    const vFore = new THREE.Vector3().subVectors(clampedTarget, elbowLocal).normalize();

    // 4. Construct shoulder orientation matrix
    // In rest pose, upper arm points along local (0, -1, 0).
    // So local Y axis points along -vUpper.
    const localY = vUpper.clone().negate();

    // Elbow bends around upper arm's local X axis towards local +Z.
    // So forearm bend direction corresponds to local Z axis:
    let zUnnorm = new THREE.Vector3().subVectors(vFore, vUpper.clone().multiplyScalar(vFore.dot(vUpper)));
    let localZ;
    if (zUnnorm.lengthSq() < 1e-4) {
      localZ = b.clone();
    } else {
      localZ = zUnnorm.normalize();
    }

    const localX = new THREE.Vector3().crossVectors(localY, localZ).normalize();
    localZ.crossVectors(localX, localY).normalize();

    this._m.makeBasis(localX, localY, localZ);
    this.shoulder.quaternion.setFromRotationMatrix(this._m);
    this.elbow.rotation.set(-thetaElbow, 0, 0);
  }
}
