/**
 * Procedural Stylized Humanoid Rig, Toon Shading & PPE Accessories
 * (frontend/lab/character/avatar.js)
 *
 * Art Direction: Friendly, stylized, Kerbal-like proportions.
 * MeshToonMaterial with 3-tone gradient map, inverted-hull outlines,
 * articulated fingers that curl when gripping, responsive facial expressions,
 * eye pupil tracking, breathing sway, and PPE accessories.
 */

import * as THREE from 'three';
import { TwoBoneIK } from './ik.js';

/**
 * Creates a shared 3-tone gradient map texture for MeshToonMaterial.
 */
let _cachedGradientTex = null;
export function getOrCreateToonGradient() {
  if (_cachedGradientTex) return _cachedGradientTex;
  const canvas = document.createElement('canvas');
  canvas.width = 3;
  canvas.height = 1;
  const ctx = canvas.getContext('2d');
  // 3 tones: shadow (0.42), midtone (0.75), highlight (1.0)
  ctx.fillStyle = '#6b7280';
  ctx.fillRect(0, 0, 1, 1);
  ctx.fillStyle = '#cbd5e1';
  ctx.fillRect(1, 0, 1, 1);
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(2, 0, 1, 1);

  const tex = new THREE.CanvasTexture(canvas);
  tex.minFilter = THREE.NearestFilter;
  tex.magFilter = THREE.NearestFilter;
  tex.generateMipmaps = false;
  _cachedGradientTex = tex;
  return tex;
}

/**
 * Creates a soft radial contact shadow texture for the blob shadow.
 */
let _cachedBlobShadowTex = null;
export function getOrCreateBlobShadowTexture() {
  if (_cachedBlobShadowTex) return _cachedBlobShadowTex;
  const canvas = document.createElement('canvas');
  canvas.width = 128;
  canvas.height = 128;
  const ctx = canvas.getContext('2d');
  const grad = ctx.createRadialGradient(64, 64, 8, 64, 64, 60);
  grad.addColorStop(0, 'rgba(15, 23, 42, 0.65)');
  grad.addColorStop(0.5, 'rgba(30, 41, 59, 0.35)');
  grad.addColorStop(1, 'rgba(30, 41, 59, 0.0)');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 128, 128);

  const tex = new THREE.CanvasTexture(canvas);
  _cachedBlobShadowTex = tex;
  return tex;
}

/**
 * Helper to add an inverted-hull toon outline to a mesh.
 */
export function addInvertedHullOutline(mesh, outlineColor = 0x1e1b4b, scale = 1.035) {
  if (!mesh || !mesh.geometry) return null;
  const outlineMat = new THREE.MeshBasicMaterial({
    color: outlineColor,
    side: THREE.BackSide,
  });
  const outlineMesh = new THREE.Mesh(mesh.geometry, outlineMat);
  outlineMesh.scale.set(scale, scale, scale);
  outlineMesh.userData.isOutline = true;
  mesh.add(outlineMesh);
  return outlineMesh;
}

export function createHumanoidAvatar() {
  const root = new THREE.Group();
  root.name = 'avatar_character';

  const gradientMap = getOrCreateToonGradient();

  // 1. Stylized Toon Materials
  const skinMat = new THREE.MeshToonMaterial({
    color: 0xfbd0b5,
    gradientMap,
  });
  const clothesMat = new THREE.MeshToonMaterial({
    color: 0x312e81, // deep brand indigo scrubs
    gradientMap,
  });
  const pantsMat = new THREE.MeshToonMaterial({
    color: 0x1e1b4b, // darker indigo trousers
    gradientMap,
  });
  const shoeMat = new THREE.MeshToonMaterial({
    color: 0x0f172a, // dark slate footwear
    gradientMap,
  });
  const soleMat = new THREE.MeshToonMaterial({
    color: 0xffffff, // clean white sole
    gradientMap,
  });
  const hairMat = new THREE.MeshToonMaterial({
    color: 0x3b2f2f, // warm stylized brunette hair
    gradientMap,
  });
  const coatMat = new THREE.MeshToonMaterial({
    color: 0xf8fafc, // bright white lab coat
    gradientMap,
  });
  const coatTrimMat = new THREE.MeshToonMaterial({
    color: 0x0ea5e9, // stylized teal collar accent
    gradientMap,
  });
  const gloveMat = new THREE.MeshToonMaterial({
    color: 0x06b6d4, // nitrile cyan gloves
    gradientMap,
  });

  const allOutlines = [];

  // Helper to build a rounded capsule mesh with optional outline
  function makeCapsule(radius, length, mat, addOutline = true) {
    const geo = new THREE.CapsuleGeometry(radius, length, 12, 16);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    if (addOutline) {
      const ol = addInvertedHullOutline(mesh, 0x1e1b4b, 1.04);
      if (ol) allOutlines.push(ol);
    }
    return mesh;
  }

  // 2. Blob Contact Shadow (Active in Low Tier when shadow maps are disabled)
  const shadowGeo = new THREE.PlaneGeometry(0.85, 0.85);
  const shadowMat = new THREE.MeshBasicMaterial({
    map: getOrCreateBlobShadowTexture(),
    transparent: true,
    opacity: 0.65,
    depthWrite: false,
  });
  const blobShadow = new THREE.Mesh(shadowGeo, shadowMat);
  blobShadow.rotation.x = -Math.PI / 2;
  blobShadow.position.y = 0.012;
  blobShadow.userData.isBlobShadow = true;
  blobShadow.visible = false; // Enabled dynamically in Low tier
  root.add(blobShadow);

  // 3. Pelvis / Hips (Rounded capsule shape)
  const pelvis = new THREE.Group();
  pelvis.position.y = 0.95;
  root.add(pelvis);

  const pelvisMesh = makeCapsule(0.12, 0.12, pantsMat);
  pelvisMesh.rotation.z = Math.PI / 2;
  pelvis.add(pelvisMesh);

  // 4. Torso / Chest (Rounded forms)
  const torso = new THREE.Group();
  torso.position.y = 0.14;
  pelvis.add(torso);

  const torsoMesh = makeCapsule(0.15, 0.22, clothesMat);
  torsoMesh.position.y = 0.22;
  torso.add(torsoMesh);

  // Lab Coat Shell (With flared hem and collar lapels, toggled via PPE)
  const coatGroup = new THREE.Group();
  coatGroup.name = 'lab_coat_group';
  coatGroup.visible = false;

  // Main coat torso
  const coatBody = makeCapsule(0.165, 0.24, coatMat);
  coatBody.position.y = 0.22;
  coatGroup.add(coatBody);

  // Flared coat hem extending past hips
  const hemGeo = new THREE.CylinderGeometry(0.17, 0.24, 0.38, 16, 1, true);
  const hemMesh = new THREE.Mesh(hemGeo, coatMat);
  hemMesh.position.y = -0.05;
  hemMesh.castShadow = true;
  coatGroup.add(hemMesh);
  const hemOl = addInvertedHullOutline(hemMesh, 0x1e1b4b, 1.035);
  if (hemOl) allOutlines.push(hemOl);

  // Coat Collar Lapels
  const lapelGeo = new THREE.BoxGeometry(0.14, 0.16, 0.04);
  const leftLapel = new THREE.Mesh(lapelGeo, coatTrimMat);
  leftLapel.position.set(-0.08, 0.35, 0.14);
  leftLapel.rotation.set(-0.2, 0.2, -0.35);
  coatGroup.add(leftLapel);

  const rightLapel = new THREE.Mesh(lapelGeo, coatTrimMat);
  rightLapel.position.set(0.08, 0.35, 0.14);
  rightLapel.rotation.set(-0.2, -0.2, 0.35);
  coatGroup.add(rightLapel);

  torso.add(coatGroup);
  const coatMesh = coatGroup; // Backward compatibility with rig.coatMesh

  // 5. Neck & Stylized Kerbal-like Head
  const neck = new THREE.Group();
  neck.position.y = 0.46;
  torso.add(neck);

  const head = new THREE.Group();
  head.position.y = 0.16;
  neck.add(head);

  // Rounded Head sphere
  const headGeo = new THREE.SphereGeometry(0.19, 28, 22);
  const headMesh = new THREE.Mesh(headGeo, skinMat);
  headMesh.scale.set(1.0, 1.05, 0.98);
  headMesh.castShadow = true;
  head.add(headMesh);
  const headOl = addInvertedHullOutline(headMesh, 0x1e1b4b, 1.035);
  if (headOl) allOutlines.push(headOl);

  // Stylized Hair: main cap + cute front fringe / clumps
  const hairGroup = new THREE.Group();
  const hairCapGeo = new THREE.SphereGeometry(0.198, 24, 18, 0, Math.PI * 2, 0, Math.PI * 0.58);
  const hairCap = new THREE.Mesh(hairCapGeo, hairMat);
  hairCap.position.set(0, 0.04, -0.015);
  hairGroup.add(hairCap);

  // Stylized front hair clumps
  function makeHairTuft(x, y, z, sx, sy, sz, rx, ry, rz) {
    const tuftGeo = new THREE.CapsuleGeometry(0.035, 0.09, 8, 8);
    const tuft = new THREE.Mesh(tuftGeo, hairMat);
    tuft.position.set(x, y, z);
    tuft.scale.set(sx, sy, sz);
    tuft.rotation.set(rx, ry, rz);
    tuft.castShadow = true;
    hairGroup.add(tuft);
  }
  makeHairTuft(-0.08, 0.15, 0.14, 1.0, 1.1, 0.9, 0.4, -0.2, -0.3);
  makeHairTuft(0.0, 0.17, 0.15, 1.1, 1.0, 0.9, 0.35, 0.0, 0.0);
  makeHairTuft(0.08, 0.15, 0.14, 1.0, 1.1, 0.9, 0.4, 0.2, 0.3);
  makeHairTuft(-0.16, 0.06, 0.04, 0.9, 1.2, 0.9, 0.1, 0.0, -0.2);
  makeHairTuft(0.16, 0.06, 0.04, 0.9, 1.2, 0.9, 0.1, 0.0, 0.2);
  head.add(hairGroup);

  // 6. Eyes: Sclera (White), Pupil (Dark Indigo with Iris Rim), Highlight
  const scleraMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
  const pupilMat = new THREE.MeshBasicMaterial({ color: 0x1e1b4b });
  const glintMat = new THREE.MeshBasicMaterial({ color: 0xffffff });

  function buildEye(isLeft) {
    const eyeRoot = new THREE.Group();
    const side = isLeft ? -1 : 1;
    eyeRoot.position.set(side * 0.072, 0.03, 0.155);

    // White sclera
    const scleraGeo = new THREE.SphereGeometry(0.042, 16, 16);
    const sclera = new THREE.Mesh(scleraGeo, scleraMat);
    sclera.scale.set(0.9, 1.0, 0.45);
    eyeRoot.add(sclera);

    // Pupil
    const pupilGeo = new THREE.SphereGeometry(0.024, 16, 16);
    const pupil = new THREE.Mesh(pupilGeo, pupilMat);
    pupil.position.set(0, 0, 0.016);
    pupil.scale.set(1.0, 1.0, 0.3);
    eyeRoot.add(pupil);

    // Specular glint
    const glintGeo = new THREE.SphereGeometry(0.008, 8, 8);
    const glint = new THREE.Mesh(glintGeo, glintMat);
    glint.position.set(side * -0.007, 0.009, 0.024);
    pupil.add(glint);

    head.add(eyeRoot);
    return { eyeRoot, sclera, pupil };
  }

  const leftEyeData = buildEye(true);
  const rightEyeData = buildEye(false);
  const leftEye = leftEyeData.eyeRoot;
  const rightEye = rightEyeData.eyeRoot;

  // Eyebrows (Articulated for expressions)
  const browMat = new THREE.MeshBasicMaterial({ color: 0x3b2f2f });
  const browGeo = new THREE.CapsuleGeometry(0.012, 0.05, 6, 8);

  const leftBrow = new THREE.Mesh(browGeo, browMat);
  leftBrow.position.set(-0.072, 0.09, 0.155);
  leftBrow.rotation.z = 0.08;
  head.add(leftBrow);

  const rightBrow = new THREE.Mesh(browGeo, browMat);
  rightBrow.position.set(0.072, 0.09, 0.155);
  rightBrow.rotation.z = -0.08;
  head.add(rightBrow);

  // Cute Rounded Nose
  const noseGeo = new THREE.SphereGeometry(0.022, 12, 12);
  const nose = new THREE.Mesh(noseGeo, skinMat);
  nose.position.set(0, -0.015, 0.18);
  nose.scale.set(1.0, 0.85, 0.9);
  head.add(nose);

  // 7. Expressive Mouth Shapes (neutral, smile, "oh", flinch)
  const mouthGroup = new THREE.Group();
  mouthGroup.position.set(0, -0.065, 0.165);

  const mouthMat = new THREE.MeshBasicMaterial({ color: 0x881337 }); // pleasant dark berry
  const mouthOpenMat = new THREE.MeshBasicMaterial({ color: 0x4c0519 });

  // Mouth Shape A: Neutral (soft pleasant curve)
  const neutralGeo = new THREE.TorusGeometry(0.028, 0.007, 8, 16, Math.PI * 0.85);
  const mouthNeutral = new THREE.Mesh(neutralGeo, mouthMat);
  mouthNeutral.rotation.set(0.2, 0, Math.PI * 1.07);
  mouthGroup.add(mouthNeutral);

  // Mouth Shape B: Smile (cheerful open grin)
  const smileGeo = new THREE.TorusGeometry(0.038, 0.010, 8, 16, Math.PI * 0.9);
  const mouthSmile = new THREE.Mesh(smileGeo, mouthMat);
  mouthSmile.rotation.set(0.2, 0, Math.PI * 1.05);
  mouthSmile.visible = false;
  mouthGroup.add(mouthSmile);

  // Mouth Shape C: "Oh" (curious / surprised circular open mouth)
  const ohGeo = new THREE.TorusGeometry(0.022, 0.010, 8, 16, Math.PI * 2);
  const mouthOh = new THREE.Mesh(ohGeo, mouthOpenMat);
  mouthOh.rotation.x = 0.2;
  mouthOh.visible = false;
  mouthGroup.add(mouthOh);

  // Mouth Shape D: Flinch (grimace / wavy line on safety breach)
  const flinchGeo = new THREE.BoxGeometry(0.055, 0.012, 0.01);
  const mouthFlinch = new THREE.Mesh(flinchGeo, mouthMat);
  mouthFlinch.rotation.set(0.2, 0, -0.08);
  mouthFlinch.visible = false;
  mouthGroup.add(mouthFlinch);

  head.add(mouthGroup);
  const mouth = mouthNeutral; // For backwards compatibility

  // 8. Visible Safety Goggles with clear refractive lenses
  const gogglesGroup = new THREE.Group();
  gogglesGroup.name = 'safety_goggles';
  gogglesGroup.visible = false;

  const goggleRimMat = new THREE.MeshToonMaterial({ color: 0x0f172a, gradientMap });
  const goggleLensMat = new THREE.MeshPhysicalMaterial({
    color: 0x38bdf8,
    transparent: true,
    opacity: 0.65,
    roughness: 0.05,
    metalness: 0.1,
    transmission: 0.75,
    ior: 1.45,
    thickness: 0.08,
    depthWrite: false,
  });

  // Left & Right goggle rims and lenses
  function buildGoggleEyepiece(isLeft) {
    const side = isLeft ? -1 : 1;
    const ep = new THREE.Group();
    ep.position.set(side * 0.072, 0.032, 0.165);

    const rimGeo = new THREE.TorusGeometry(0.048, 0.010, 10, 24);
    const rim = new THREE.Mesh(rimGeo, goggleRimMat);
    ep.add(rim);

    const lensGeo = new THREE.CylinderGeometry(0.045, 0.045, 0.012, 24);
    const lens = new THREE.Mesh(lensGeo, goggleLensMat);
    lens.rotation.x = Math.PI / 2;
    ep.add(lens);

    return ep;
  }
  gogglesGroup.add(buildGoggleEyepiece(true));
  gogglesGroup.add(buildGoggleEyepiece(false));

  // Goggle strap wrapping around head
  const strapGeo = new THREE.CylinderGeometry(0.198, 0.198, 0.024, 28, 1, true);
  const strap = new THREE.Mesh(strapGeo, goggleRimMat);
  strap.position.set(0, 0.032, 0);
  gogglesGroup.add(strap);

  head.add(gogglesGroup);

  // 9. Arms & Hands with Articulated Finger Groups that curl when gripping
  function buildArm(isLeft) {
    const side = isLeft ? 1 : -1;

    const shoulder = new THREE.Group();
    shoulder.position.set(side * 0.22, 0.4, 0);
    torso.add(shoulder);

    const upperArm = new THREE.Group();
    shoulder.add(upperArm);

    const upperMesh = makeCapsule(0.048, 0.22, clothesMat);
    upperMesh.position.y = -0.16;
    upperArm.add(upperMesh);

    const elbow = new THREE.Group();
    elbow.position.y = -0.32;
    upperArm.add(elbow);

    const forearmMesh = makeCapsule(0.044, 0.19, skinMat);
    forearmMesh.position.y = -0.14;
    elbow.add(forearmMesh);

    const hand = new THREE.Group();
    hand.position.y = -0.28;
    elbow.add(hand);

    // Palm
    const palmMesh = makeCapsule(0.036, 0.04, skinMat);
    palmMesh.position.set(0, -0.04, 0);
    hand.add(palmMesh);

    // Articulated Finger Group (curls around socket during grip)
    const fingerGroup = new THREE.Group();
    fingerGroup.position.set(0, -0.055, 0.02);

    const fingerGeo = new THREE.CapsuleGeometry(0.013, 0.042, 6, 8);
    const fingersMesh = new THREE.Mesh(fingerGeo, skinMat);
    fingersMesh.rotation.x = 0.25;
    fingersMesh.castShadow = true;
    fingerGroup.add(fingersMesh);

    // Thumb
    const thumbGeo = new THREE.CapsuleGeometry(0.012, 0.032, 6, 8);
    const thumbMesh = new THREE.Mesh(thumbGeo, skinMat);
    thumbMesh.position.set(side * -0.025, 0.015, 0.015);
    thumbMesh.rotation.set(0.3, 0, side * -0.6);
    thumbMesh.castShadow = true;
    fingerGroup.add(thumbMesh);

    hand.add(fingerGroup);

    const ik = new TwoBoneIK(shoulder, elbow, hand, isLeft);
    return {
      shoulder,
      upperArm,
      elbow,
      hand,
      handMesh: palmMesh,
      fingerGroup,
      fingersMesh,
      thumbMesh,
      forearmMesh,
      ik,
    };
  }

  const leftArm = buildArm(true);
  const rightArm = buildArm(false);

  // Held Item Sockets
  const heldItemSocket = new THREE.Group();
  heldItemSocket.name = 'right_held_item_socket';
  heldItemSocket.position.set(0, -0.08, 0.05);
  rightArm.hand.add(heldItemSocket);

  const leftHeldItemSocket = new THREE.Group();
  leftHeldItemSocket.name = 'left_held_item_socket';
  leftHeldItemSocket.position.set(0, -0.08, 0.05);
  leftArm.hand.add(leftHeldItemSocket);

  // 10. Legs, Feet & Shoes
  function buildLeg(isLeft) {
    const side = isLeft ? 1 : -1;

    const hip = new THREE.Group();
    hip.position.set(side * 0.11, -0.08, 0);
    pelvis.add(hip);

    const thighMesh = makeCapsule(0.058, 0.30, pantsMat);
    thighMesh.position.y = -0.21;
    hip.add(thighMesh);

    const knee = new THREE.Group();
    knee.position.y = -0.42;
    hip.add(knee);

    const shinMesh = makeCapsule(0.052, 0.30, pantsMat);
    shinMesh.position.y = -0.21;
    knee.add(shinMesh);

    const foot = new THREE.Group();
    foot.position.y = -0.42;
    knee.add(foot);

    // Stylized Sneaker/Safety Shoe
    const footGroup = new THREE.Group();
    footGroup.position.set(0, -0.04, 0.035);

    // Shoe body
    const shoeBodyGeo = new THREE.CapsuleGeometry(0.045, 0.11, 8, 12);
    const shoeBody = new THREE.Mesh(shoeBodyGeo, shoeMat);
    shoeBody.rotation.x = Math.PI / 2;
    shoeBody.castShadow = true;
    footGroup.add(shoeBody);

    // White sole
    const soleGeo = new THREE.BoxGeometry(0.095, 0.024, 0.19);
    const sole = new THREE.Mesh(soleGeo, soleMat);
    sole.position.set(0, -0.038, 0);
    sole.castShadow = true;
    footGroup.add(sole);

    foot.add(footGroup);

    return { hip, knee, foot, footMesh: shoeBody };
  }

  const leftLeg = buildLeg(true);
  const rightLeg = buildLeg(false);

  // 11. Rig Handle Object
  const rig = {
    root,
    pelvis,
    torso,
    neck,
    head,
    leftEye,
    rightEye,
    leftBrow,
    rightBrow,
    mouth,
    mouthNeutral,
    mouthSmile,
    mouthOh,
    mouthFlinch,
    leftArm,
    rightArm,
    leftHand: leftArm.hand,
    rightHand: rightArm.hand,
    leftLeg,
    rightLeg,
    heldItemSocket,
    leftHeldItemSocket,
    coatMesh,
    gogglesGroup,
    skinMat,
    gloveMat,
    clothesMat,
    blobShadow,
    allOutlines,

    currentExpression: 'neutral',
    lookTarget: null,
    isFirstPersonHands: false,
    _hasCoat: false,

    setFirstPersonHandsMode(enabled) {
      this.isFirstPersonHands = Boolean(enabled);
      pelvisMesh.visible = !enabled;
      torsoMesh.visible = !enabled;
      neck.visible = !enabled;
      head.visible = !enabled;
      leftLeg.hip.visible = !enabled;
      rightLeg.hip.visible = !enabled;
      if (blobShadow) {
        blobShadow.visible = !enabled && (window.sceneManager?.quality === 'low');
      }
      if (coatMesh) {
        coatMesh.visible = !enabled && Boolean(this._hasCoat);
      }
      leftArm.shoulder.visible = true;
      rightArm.shoulder.visible = true;
      if (heldItemSocket) heldItemSocket.visible = true;
      if (leftHeldItemSocket) leftHeldItemSocket.visible = true;
    },

    // Dynamic Opacity / Fade (fades to 40% when camera is occluded)
    setOpacity(opacity = 1.0) {
      root.traverse((obj) => {
        if (obj.isMesh && obj.material && !obj.userData.isBlobShadow) {
          const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
          mats.forEach((m) => {
            if (m.userData.origTransparent === undefined) {
              m.userData.origTransparent = m.transparent;
              m.userData.origOpacity = m.opacity !== undefined ? m.opacity : 1.0;
            }
            if (opacity >= 0.99) {
              m.transparent = m.userData.origTransparent;
              m.opacity = m.userData.origOpacity;
            } else {
              m.transparent = true;
              m.opacity = opacity;
            }
          });
        }
      });
    },

    // PPE State Updater
    updatePPE(ppeSet) {
      const ppe = ppeSet instanceof Set ? ppeSet : new Set(ppeSet || []);
      this._hasCoat = ppe.has('coat');

      // Goggles
      gogglesGroup.visible = !this.isFirstPersonHands && ppe.has('goggles');

      // Lab Coat
      coatMesh.visible = !this.isFirstPersonHands && this._hasCoat;

      // Nitrile Gloves (recolor palm, fingers, and thumb)
      const hasGloves = ppe.has('gloves');
      const targetMat = hasGloves ? gloveMat : skinMat;
      leftArm.handMesh.material = targetMat;
      leftArm.fingersMesh.material = targetMat;
      leftArm.thumbMesh.material = targetMat;

      rightArm.handMesh.material = targetMat;
      rightArm.fingersMesh.material = targetMat;
      rightArm.thumbMesh.material = targetMat;
    },

    // Eye Blink
    setBlink(isClosed) {
      const sy = isClosed ? 0.08 : 1.0;
      leftEyeData.sclera.scale.y = sy;
      leftEyeData.pupil.scale.y = sy;
      rightEyeData.sclera.scale.y = sy;
      rightEyeData.pupil.scale.y = sy;
    },

    // Expressions: 'neutral', 'smile', 'oh', 'flinch'
    setExpression(name) {
      this.currentExpression = name;
      mouthNeutral.visible = name === 'neutral';
      mouthSmile.visible = name === 'smile';
      mouthOh.visible = name === 'oh';
      mouthFlinch.visible = name === 'flinch';

      if (name === 'smile') {
        leftBrow.position.y = 0.098;
        rightBrow.position.y = 0.098;
        leftBrow.rotation.z = 0.15;
        rightBrow.rotation.z = -0.15;
      } else if (name === 'flinch') {
        leftBrow.position.y = 0.082;
        rightBrow.position.y = 0.082;
        leftBrow.rotation.z = -0.22;
        rightBrow.rotation.z = 0.22;
        head.rotation.x = -0.12; // flinch back
      } else if (name === 'oh') {
        leftBrow.position.y = 0.104;
        rightBrow.position.y = 0.104;
        leftBrow.rotation.z = 0.0;
        rightBrow.rotation.z = 0.0;
      } else {
        // neutral
        leftBrow.position.y = 0.09;
        rightBrow.position.y = 0.09;
        leftBrow.rotation.z = 0.08;
        rightBrow.rotation.z = -0.08;
        head.rotation.x = 0.0;
      }
    },

    // Hand Grip Curling
    setGrip(isGripping, isLeft = false) {
      const arm = isLeft ? leftArm : rightArm;
      if (!arm.fingerGroup) return;
      if (isGripping) {
        // Curl fingers around socket
        arm.fingerGroup.rotation.x = -0.95;
        arm.fingerGroup.position.set(0, -0.065, 0.04);
        arm.thumbMesh.rotation.set(0.6, 0, (isLeft ? 1 : -1) * -0.9);
      } else {
        // Relax fingers
        arm.fingerGroup.rotation.x = 0;
        arm.fingerGroup.position.set(0, -0.055, 0.02);
        arm.thumbMesh.rotation.set(0.3, 0, (isLeft ? 1 : -1) * -0.6);
      }
    },

    // Eyes & Head Look At Target (clamped to natural human neck angles)
    lookAt(targetWorldPos) {
      if (!targetWorldPos) return;
      this.lookTarget = targetWorldPos.clone();

      // Convert target to neck parent (torso) space
      const localTgt = torso.worldToLocal(targetWorldPos.clone());
      const dx = localTgt.x;
      const dy = localTgt.y - neck.position.y;
      const dz = localTgt.z;

      const yaw = Math.max(-0.7, Math.min(0.7, Math.atan2(dx, dz)));
      const pitch = Math.max(-0.4, Math.min(0.35, -Math.atan2(dy, Math.hypot(dx, dz))));

      head.rotation.y = yaw;
      head.rotation.x = pitch;

      // Pupil tracking: slightly offset pupils in direction of target
      const pupilShiftX = Math.max(-0.012, Math.min(0.012, yaw * 0.018));
      const pupilShiftY = Math.max(-0.010, Math.min(0.010, -pitch * 0.018));
      leftEyeData.pupil.position.x = pupilShiftX;
      leftEyeData.pupil.position.y = pupilShiftY;
      rightEyeData.pupil.position.x = pupilShiftX;
      rightEyeData.pupil.position.y = pupilShiftY;
    },

    // Quality Tier Hook: Outlines & Blob Shadows
    setQualityFeatures(tier) {
      const isLow = tier === 'low';
      // Outlines off in Low
      allOutlines.forEach((ol) => {
        ol.visible = !isLow;
      });
      // Blob shadow active in Low
      blobShadow.visible = isLow;
    },
  };

  root.userData.rig = rig;
  return rig;
}
