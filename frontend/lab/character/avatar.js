/**
 * Procedural Low-Poly Humanoid Rig & PPE Accessories (frontend/lab/character/avatar.js)
 * Constructs the character skeletal hierarchy and toggles personal protective equipment.
 */

import * as THREE from 'three';
import { TwoBoneIK } from './ik.js';

export function createHumanoidAvatar() {
  const root = new THREE.Group();
  root.name = 'avatar_character';

  // 1. Shared Materials
  const skinMat = new THREE.MeshStandardMaterial({ color: 0xfbd0b5, roughness: 0.6 });
  const clothesMat = new THREE.MeshStandardMaterial({ color: 0x312e81, roughness: 0.5 }); // indigo scrubs
  const pantsMat = new THREE.MeshStandardMaterial({ color: 0x1e1b4b, roughness: 0.7 });
  const shoeMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.4 });
  const hairMat = new THREE.MeshStandardMaterial({ color: 0x3b2f2f, roughness: 0.8 });
  const coatMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.3 }); // lab coat
  const gloveMat = new THREE.MeshStandardMaterial({ color: 0x06b6d4, roughness: 0.2 }); // nitrile cyan

  // 2. Pelvis / Hips
  const pelvis = new THREE.Group();
  pelvis.position.y = 0.95;
  root.add(pelvis);

  const pelvisMesh = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.16, 0.22), pantsMat);
  pelvis.add(pelvisMesh);

  // 3. Torso / Chest
  const torso = new THREE.Group();
  torso.position.y = 0.16;
  pelvis.add(torso);

  const torsoMesh = new THREE.Mesh(new THREE.BoxGeometry(0.36, 0.44, 0.24), clothesMat);
  torsoMesh.position.y = 0.22;
  torso.add(torsoMesh);

  // Lab Coat Shell (Toggled via PPE)
  const coatMesh = new THREE.Mesh(new THREE.BoxGeometry(0.39, 0.62, 0.27), coatMat);
  coatMesh.position.y = 0.16;
  coatMesh.visible = false;
  torso.add(coatMesh);

  // 4. Neck & Head
  const neck = new THREE.Group();
  neck.position.y = 0.46;
  torso.add(neck);

  const head = new THREE.Group();
  head.position.y = 0.16;
  neck.add(head);

  const headMesh = new THREE.Mesh(new THREE.BoxGeometry(0.24, 0.26, 0.24), skinMat);
  head.add(headMesh);

  // Hair
  const hairMesh = new THREE.Mesh(new THREE.BoxGeometry(0.26, 0.1, 0.26), hairMat);
  hairMesh.position.y = 0.12;
  head.add(hairMesh);

  // Eyes (Blinking support)
  const eyeMat = new THREE.MeshBasicMaterial({ color: 0x0f172a });
  const leftEye = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.04, 0.02), eyeMat);
  leftEye.position.set(-0.06, 0.02, 0.125);
  head.add(leftEye);

  const rightEye = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.04, 0.02), eyeMat);
  rightEye.position.set(0.06, 0.02, 0.125);
  head.add(rightEye);

  // Goggles (Toggled via PPE)
  const gogglesGroup = new THREE.Group();
  gogglesGroup.visible = false;

  const goggleLensMat = new THREE.MeshStandardMaterial({
    color: 0x38bdf8,
    transparent: true,
    opacity: 0.65,
    roughness: 0.1,
  });
  const goggleLens = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.08, 0.05), goggleLensMat);
  goggleLens.position.set(0, 0.02, 0.135);
  gogglesGroup.add(goggleLens);

  const goggleStrapMat = new THREE.MeshBasicMaterial({ color: 0x0f172a });
  const goggleStrap = new THREE.Mesh(new THREE.BoxGeometry(0.26, 0.04, 0.26), goggleStrapMat);
  gogglesGroup.add(goggleStrap);

  head.add(gogglesGroup);

  // 5. Arms & Hands with IK
  function buildArm(isLeft) {
    const side = isLeft ? 1 : -1;

    const shoulder = new THREE.Group();
    shoulder.position.set(side * 0.22, 0.4, 0);
    torso.add(shoulder);

    const upperArm = new THREE.Group();
    shoulder.add(upperArm);

    const upperMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.045, 0.32, 12), clothesMat);
    upperMesh.position.y = -0.16;
    upperArm.add(upperMesh);

    const elbow = new THREE.Group();
    elbow.position.y = -0.32;
    upperArm.add(elbow);

    const forearmMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.04, 0.28, 12), skinMat);
    forearmMesh.position.y = -0.14;
    elbow.add(forearmMesh);

    const hand = new THREE.Group();
    hand.position.y = -0.28;
    elbow.add(hand);

    const handMesh = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.1, 0.04), skinMat);
    handMesh.position.y = -0.05;
    hand.add(handMesh);

    const ik = new TwoBoneIK(shoulder, elbow, hand, isLeft);
    return { shoulder, upperArm, elbow, hand, handMesh, ik };
  }

  const leftArm = buildArm(true);
  const rightArm = buildArm(false);

  // Held Item Socket (on right hand)
  const heldItemSocket = new THREE.Group();
  heldItemSocket.position.set(0, -0.08, 0.05);
  rightArm.hand.add(heldItemSocket);

  // 6. Legs & Feet
  function buildLeg(isLeft) {
    const side = isLeft ? 1 : -1;

    const hip = new THREE.Group();
    hip.position.set(side * 0.11, -0.08, 0);
    pelvis.add(hip);

    const thighMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.06, 0.42, 12), pantsMat);
    thighMesh.position.y = -0.21;
    hip.add(thighMesh);

    const knee = new THREE.Group();
    knee.position.y = -0.42;
    hip.add(knee);

    const shinMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.05, 0.42, 12), pantsMat);
    shinMesh.position.y = -0.21;
    knee.add(shinMesh);

    const foot = new THREE.Group();
    foot.position.y = -0.42;
    knee.add(foot);

    const footMesh = new THREE.Mesh(new THREE.BoxGeometry(0.09, 0.08, 0.18), shoeMat);
    footMesh.position.set(0, -0.04, 0.04);
    foot.add(footMesh);

    return { hip, knee, foot };
  }

  const leftLeg = buildLeg(true);
  const rightLeg = buildLeg(false);

  // 7. Rig Handle Object
  const rig = {
    root,
    pelvis,
    torso,
    neck,
    head,
    leftEye,
    rightEye,
    leftArm,
    rightArm,
    leftLeg,
    rightLeg,
    heldItemSocket,
    coatMesh,
    gogglesGroup,
    skinMat,
    gloveMat,

    // PPE State Updater
    updatePPE(ppeSet) {
      const ppe = ppeSet instanceof Set ? ppeSet : new Set(ppeSet || []);

      // Goggles
      gogglesGroup.visible = ppe.has('goggles');

      // Lab Coat
      coatMesh.visible = ppe.has('coat');

      // Nitrile Gloves (recolor hands)
      const hasGloves = ppe.has('gloves');
      const targetMat = hasGloves ? gloveMat : skinMat;
      leftArm.handMesh.material = targetMat;
      rightArm.handMesh.material = targetMat;
    },

    // Eye Blink
    setBlink(isClosed) {
      leftEye.scale.y = isClosed ? 0.1 : 1.0;
      rightEye.scale.y = isClosed ? 0.1 : 1.0;
    },

    // Look at target
    lookAt(targetWorldPos) {
      head.lookAt(targetWorldPos);
    },
  };

  root.userData.rig = rig;
  return rig;
}
