import { test } from 'node:test';
import assert from 'node:assert';
import { computeMovementVector, criticallyDampedEase } from '../lab/character/movement_math.js';

const EPSILON = 1e-4;
const INV_SQRT2 = 1 / Math.SQRT2; // ~0.70710678

function assertVecClose(actual, expected, msg) {
  assert(
    Math.abs(actual.x - expected.x) < EPSILON,
    `${msg}: actual.x (${actual.x}) != expected.x (${expected.x})`
  );
  assert(
    Math.abs(actual.z - expected.z) < EPSILON,
    `${msg}: actual.z (${actual.z}) != expected.z (${expected.z})`
  );
}

test('movement_math: Yaw 0 deg (Camera at +Z facing -Z)', (t) => {
  const char = { x: 0, y: 0, z: 0 };
  const cam = { x: 0, y: 5, z: 10 };

  // Hand-computed expected values:
  // dx = 0, dz = 10 -> camAngle = atan2(0, 10) + pi = pi
  // fwdX = sin(pi) = 0, fwdZ = cos(pi) = -1 (points in -Z, away from camera)
  // rightX = -fwdZ = 1, rightZ = fwdX = 0 (points in +X, screen-right)

  // 1. W (Forward): moves away from camera along -Z -> (0, -1)
  const moveW = computeMovementVector({ cameraPos: cam, characterPos: char, rawFwd: 1, rawRight: 0 });
  assertVecClose(moveW, { x: 0, z: -1 }, 'Yaw 0 W');

  // 2. S (Backward): moves toward camera along +Z -> (0, 1)
  const moveS = computeMovementVector({ cameraPos: cam, characterPos: char, rawFwd: -1, rawRight: 0 });
  assertVecClose(moveS, { x: 0, z: 1 }, 'Yaw 0 S');

  // 3. D (Right): moves to screen-right along +X -> (1, 0)
  const moveD = computeMovementVector({ cameraPos: cam, characterPos: char, rawFwd: 0, rawRight: 1 });
  assertVecClose(moveD, { x: 1, z: 0 }, 'Yaw 0 D');

  // 4. A (Left): moves to screen-left along -X -> (-1, 0)
  const moveA = computeMovementVector({ cameraPos: cam, characterPos: char, rawFwd: 0, rawRight: -1 });
  assertVecClose(moveA, { x: -1, z: 0 }, 'Yaw 0 A');

  // 5. Diagonal W+D: unnormalized (1, -1), normalized (1/sqrt2, -1/sqrt2)
  const moveWD = computeMovementVector({ cameraPos: cam, characterPos: char, rawFwd: 1, rawRight: 1 });
  assertVecClose(moveWD, { x: INV_SQRT2, z: -INV_SQRT2 }, 'Yaw 0 W+D');

  // 6. Diagonal W+A: unnormalized (-1, -1), normalized (-1/sqrt2, -1/sqrt2)
  const moveWA = computeMovementVector({ cameraPos: cam, characterPos: char, rawFwd: 1, rawRight: -1 });
  assertVecClose(moveWA, { x: -INV_SQRT2, z: -INV_SQRT2 }, 'Yaw 0 W+A');

  // 7. Opposite keys cancelling: W + S -> (0, 0)
  const moveWS = computeMovementVector({ cameraPos: cam, characterPos: char, rawFwd: 0, rawRight: 0 });
  assertVecClose(moveWS, { x: 0, z: 0 }, 'Yaw 0 W+S cancel');

  // 8. Opposite keys cancelling via keys object
  const moveCancelKeys = computeMovementVector({
    cameraPos: cam,
    characterPos: char,
    keys: { KeyW: true, KeyS: true, KeyA: true, KeyD: true },
  });
  assertVecClose(moveCancelKeys, { x: 0, z: 0 }, 'Yaw 0 all cancel');
});

test('movement_math: Yaw 90 deg (Camera at +X facing -X)', (t) => {
  const char = { x: 0, y: 0, z: 0 };
  const cam = { x: 10, y: 5, z: 0 };

  // Hand-computed expected values:
  // dx = 10, dz = 0 -> camAngle = atan2(10, 0) + pi = pi/2 + pi = 3pi/2
  // fwdX = sin(3pi/2) = -1, fwdZ = cos(3pi/2) = 0 (points in -X, away from camera)
  // rightX = -fwdZ = 0, rightZ = fwdX = -1 (points in -Z, screen-right)

  // 1. W (Forward): moves away from camera along -X -> (-1, 0)
  const moveW = computeMovementVector({ cameraPos: cam, characterPos: char, rawFwd: 1, rawRight: 0 });
  assertVecClose(moveW, { x: -1, z: 0 }, 'Yaw 90 W');

  // 2. S (Backward): moves toward camera along +X -> (1, 0)
  const moveS = computeMovementVector({ cameraPos: cam, characterPos: char, rawFwd: -1, rawRight: 0 });
  assertVecClose(moveS, { x: 1, z: 0 }, 'Yaw 90 S');

  // 3. D (Right): moves to screen-right along -Z -> (0, -1)
  const moveD = computeMovementVector({ cameraPos: cam, characterPos: char, rawFwd: 0, rawRight: 1 });
  assertVecClose(moveD, { x: 0, z: -1 }, 'Yaw 90 D');

  // 4. A (Left): moves to screen-left along +Z -> (0, 1)
  const moveA = computeMovementVector({ cameraPos: cam, characterPos: char, rawFwd: 0, rawRight: -1 });
  assertVecClose(moveA, { x: 0, z: 1 }, 'Yaw 90 A');

  // 5. Diagonal W+D: normalized (-1/sqrt2, -1/sqrt2)
  const moveWD = computeMovementVector({ cameraPos: cam, characterPos: char, rawFwd: 1, rawRight: 1 });
  assertVecClose(moveWD, { x: -INV_SQRT2, z: -INV_SQRT2 }, 'Yaw 90 W+D');
});

test('movement_math: Yaw 180 deg (Camera at -Z facing +Z)', (t) => {
  const char = { x: 0, y: 0, z: 0 };
  const cam = { x: 0, y: 5, z: -10 };

  // Hand-computed expected values:
  // dx = 0, dz = -10 -> camAngle = atan2(0, -10) + pi = pi + pi = 2pi
  // fwdX = sin(0) = 0, fwdZ = cos(0) = 1 (points in +Z, away from camera)
  // rightX = -fwdZ = -1, rightZ = fwdX = 0 (points in -X, screen-right)

  // 1. W (Forward): moves away from camera along +Z -> (0, 1)
  const moveW = computeMovementVector({ cameraPos: cam, characterPos: char, rawFwd: 1, rawRight: 0 });
  assertVecClose(moveW, { x: 0, z: 1 }, 'Yaw 180 W');

  // 2. S (Backward): moves toward camera along -Z -> (0, -1)
  const moveS = computeMovementVector({ cameraPos: cam, characterPos: char, rawFwd: -1, rawRight: 0 });
  assertVecClose(moveS, { x: 0, z: -1 }, 'Yaw 180 S');

  // 3. D (Right): moves to screen-right along -X -> (-1, 0)
  const moveD = computeMovementVector({ cameraPos: cam, characterPos: char, rawFwd: 0, rawRight: 1 });
  assertVecClose(moveD, { x: -1, z: 0 }, 'Yaw 180 D');

  // 4. A (Left): moves to screen-left along +X -> (1, 0)
  const moveA = computeMovementVector({ cameraPos: cam, characterPos: char, rawFwd: 0, rawRight: -1 });
  assertVecClose(moveA, { x: 1, z: 0 }, 'Yaw 180 A');

  // 5. Diagonal W+D: normalized (-1/sqrt2, 1/sqrt2)
  const moveWD = computeMovementVector({ cameraPos: cam, characterPos: char, rawFwd: 1, rawRight: 1 });
  assertVecClose(moveWD, { x: -INV_SQRT2, z: INV_SQRT2 }, 'Yaw 180 W+D');
});

test('movement_math: Yaw 270 deg (Camera at -X facing +X)', (t) => {
  const char = { x: 0, y: 0, z: 0 };
  const cam = { x: -10, y: 5, z: 0 };

  // Hand-computed expected values:
  // dx = -10, dz = 0 -> camAngle = atan2(-10, 0) + pi = -pi/2 + pi = pi/2
  // fwdX = sin(pi/2) = 1, fwdZ = cos(pi/2) = 0 (points in +X, away from camera)
  // rightX = -fwdZ = 0, rightZ = fwdX = 1 (points in +Z, screen-right)

  // 1. W (Forward): moves away from camera along +X -> (1, 0)
  const moveW = computeMovementVector({ cameraPos: cam, characterPos: char, rawFwd: 1, rawRight: 0 });
  assertVecClose(moveW, { x: 1, z: 0 }, 'Yaw 270 W');

  // 2. S (Backward): moves toward camera along -X -> (-1, 0)
  const moveS = computeMovementVector({ cameraPos: cam, characterPos: char, rawFwd: -1, rawRight: 0 });
  assertVecClose(moveS, { x: -1, z: 0 }, 'Yaw 270 S');

  // 3. D (Right): moves to screen-right along +Z -> (0, 1)
  const moveD = computeMovementVector({ cameraPos: cam, characterPos: char, rawFwd: 0, rawRight: 1 });
  assertVecClose(moveD, { x: 0, z: 1 }, 'Yaw 270 D');

  // 4. A (Left): moves to screen-left along -Z -> (0, -1)
  const moveA = computeMovementVector({ cameraPos: cam, characterPos: char, rawFwd: 0, rawRight: -1 });
  assertVecClose(moveA, { x: 0, z: -1 }, 'Yaw 270 A');

  // 5. Diagonal W+D: normalized (1/sqrt2, 1/sqrt2)
  const moveWD = computeMovementVector({ cameraPos: cam, characterPos: char, rawFwd: 1, rawRight: 1 });
  assertVecClose(moveWD, { x: INV_SQRT2, z: INV_SQRT2 }, 'Yaw 270 W+D');
});

test('movement_math: first-person mode forward direction', (t) => {
  // First person view looking at diagonal (1/sqrt2, 0, -1/sqrt2)
  const cameraForward = { x: INV_SQRT2, y: 0, z: -INV_SQRT2 };
  const moveW = computeMovementVector({
    isFirstPerson: true,
    cameraForward,
    rawFwd: 1,
    rawRight: 0,
  });
  assertVecClose(moveW, { x: INV_SQRT2, z: -INV_SQRT2 }, 'First person W');

  const moveD = computeMovementVector({
    isFirstPerson: true,
    cameraForward,
    rawFwd: 0,
    rawRight: 1,
  });
  // Right is (-fwdZ, fwdX) = (-(-INV_SQRT2), INV_SQRT2) = (INV_SQRT2, INV_SQRT2)
  assertVecClose(moveD, { x: INV_SQRT2, z: INV_SQRT2 }, 'First person D');
});

test('movement_math: critically damped easing stability & zero overshoot', (t) => {
  const target = 100.0;
  let current = 0.0;
  const k = 8.0;

  // Simulate multiple variable dt frames (16ms, 33ms, 100ms)
  const dts = [0.016, 0.033, 0.1, 0.05, 0.016];
  for (const dt of dts) {
    const nextVal = criticallyDampedEase(current, target, k, dt);
    assert(nextVal > current, `Value must advance towards target: ${nextVal} > ${current}`);
    assert(nextVal <= target, `Value must NEVER overshoot target: ${nextVal} <= ${target}`);
    current = nextVal;
  }
});
