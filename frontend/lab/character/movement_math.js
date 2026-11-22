/**
 * Pure mathematical functions for camera-relative character locomotion on the ground plane (XZ).
 * Three.js coordinate convention: Right-handed, Y up, X right, Z forward/out.
 */

/**
 * Computes the normalized camera-relative world movement vector.
 *
 * Forward on ground plane:
 *   Vector pointing from camera towards character: f = (fwdX, fwdZ)
 * Right vector on ground plane:
 *   With forward f = (fwdX, fwdZ) and Up = (0, 1, 0),
 *   right = f x up = (-fwdZ, fwdX) on XZ plane.
 *   Three.js cross product:
 *     (fwdX, 0, fwdZ) x (0, 1, 0) = (0*0 - fwdZ*1, 0, fwdX*1 - 0*0) = (-fwdZ, 0, fwdX)
 *   Therefore: rightX = -fwdZ; rightZ = fwdX;
 *
 * @param {Object} options
 * @param {{x: number, y?: number, z: number}} [options.cameraPos] - World position of the camera.
 * @param {{x: number, y?: number, z: number}} [options.characterPos] - World position of the character.
 * @param {number} [options.rawFwd=0] - Forward input (-1 for backward/S, +1 for forward/W).
 * @param {number} [options.rawRight=0] - Right input (-1 for left/A, +1 for right/D).
 * @param {Object} [options.keys] - Key states (KeyW, KeyS, KeyA, KeyD, ArrowUp, ArrowDown, ArrowLeft, ArrowRight).
 * @param {{x?: number, y?: number}} [options.joystick] - Joystick input (x: -1..1, y: -1..1).
 * @param {boolean} [options.isFirstPerson=false] - Whether camera is in first-person mode.
 * @param {{x: number, y?: number, z: number}} [options.cameraForward] - Camera forward direction vector (for first-person).
 * @returns {{
 *   x: number,
 *   z: number,
 *   length: number,
 *   fwdX: number,
 *   fwdZ: number,
 *   rightX: number,
 *   rightZ: number,
 *   camAngle: number,
 *   rawFwd: number,
 *   rawRight: number
 * }}
 */
export function computeMovementVector(options = {}) {
  let fwdInput = 0;
  let rightInput = 0;

  if (typeof options.rawFwd === 'number' || typeof options.rawRight === 'number') {
    fwdInput = options.rawFwd || 0;
    rightInput = options.rawRight || 0;
  } else {
    const k = options.keys || {};
    const j = options.joystick || {};
    const fwdKey = (k.KeyW || k.ArrowUp ? 1 : 0) - (k.KeyS || k.ArrowDown ? 1 : 0);
    const rightKey = (k.KeyD || k.ArrowRight ? 1 : 0) - (k.KeyA || k.ArrowLeft ? 1 : 0);
    fwdInput = fwdKey + (j.y || 0);
    rightInput = rightKey + (j.x || 0);
  }

  let fwdX = 0;
  let fwdZ = -1;
  let camAngle = 0;

  if (options.isFirstPerson && options.cameraForward) {
    fwdX = options.cameraForward.x || 0;
    fwdZ = options.cameraForward.z || 0;
    const len = Math.hypot(fwdX, fwdZ);
    if (len > 1e-6) {
      fwdX /= len;
      fwdZ /= len;
    } else {
      fwdX = 0;
      fwdZ = -1;
    }
    camAngle = Math.atan2(fwdX, fwdZ);
  } else {
    const camPos = options.cameraPos || { x: 0, y: 5, z: 10 };
    const charPos = options.characterPos || { x: 0, y: 0, z: 0 };
    const dx = camPos.x - charPos.x;
    const dz = camPos.z - charPos.z;

    camAngle = Math.atan2(dx, dz) + Math.PI;
    fwdX = Math.sin(camAngle);
    fwdZ = Math.cos(camAngle);
  }

  // Right vector: f x up = (-fwdZ, fwdX)
  const rightX = -fwdZ;
  const rightZ = fwdX;

  // Unnormalized world motion vector
  const moveDirX = fwdX * fwdInput + rightX * rightInput;
  const moveDirZ = fwdZ * fwdInput + rightZ * rightInput;
  const rawLen = Math.hypot(moveDirX, moveDirZ);

  let normX = 0;
  let normZ = 0;
  let length = 0;

  if (rawLen > 1e-6) {
    // Normalise diagonal keyboard inputs (magnitude sqrt(2) -> 1.0)
    // while preserving analog joystick magnitude < 1.0
    const targetScale = Math.min(1.0, rawLen);
    normX = (moveDirX / rawLen) * targetScale;
    normZ = (moveDirZ / rawLen) * targetScale;
    length = Math.hypot(normX, normZ);
  }

  return {
    x: normX,
    z: normZ,
    length,
    fwdX,
    fwdZ,
    rightX,
    rightZ,
    camAngle,
    rawFwd: fwdInput,
    rawRight: rightInput,
  };
}

/**
 * Computes critically damped exponential easing towards a target vector.
 * Guarantees no overshoot for any positive delta time.
 *
 * @param {number} current - Current scalar value.
 * @param {number} target - Target scalar value.
 * @param {number} k - Damping stiffness constant.
 * @param {number} dt - Frame delta time in seconds.
 * @returns {number} New scalar value.
 */
export function criticallyDampedEase(current, target, k, dt) {
  const clampedDt = Math.min(0.1, Math.max(0.0001, dt));
  const alpha = 1.0 - Math.exp(-k * clampedDt);
  return current + (target - current) * alpha;
}
