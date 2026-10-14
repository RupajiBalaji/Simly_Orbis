/**
 * Glassware Liquid Volume & Color Tweening (frontend/lab/render/liquid.js)
 * Implements directive 'liquid' from the Visual Contract.
 */

import * as THREE from 'three';

export function applyLiquidDirective(apparatusGroup, directive) {
  if (!apparatusGroup) return;

  const { hex, volume_ml = 0, opacity } = directive;

  let liqMesh = apparatusGroup.userData.liquidMesh;

  // If this is a tube rack, lookup specific tube
  if (!liqMesh && apparatusGroup.userData.tubes && directive.target) {
    const tube = apparatusGroup.userData.tubes[directive.target];
    if (tube) {
      liqMesh = tube.userData.liquidMesh;
    }
  }

  if (!liqMesh) return;

  const maxVol = apparatusGroup.userData.maxVolume || 100.0;
  const fullHeight = apparatusGroup.userData.fullHeight || 0.15;
  const volRatio = Math.max(0.0, Math.min(1.0, volume_ml / maxVol));

  if (volume_ml <= 0 || volRatio <= 0.001) {
    liqMesh.visible = false;
    liqMesh.material.opacity = 0.0;
    return;
  }

  liqMesh.visible = true;

  // If this is a conical flask, build exact tapered frustum fitting inside cone
  if (apparatusGroup.userData.isConicalFlask) {
    const h = Math.max(0.02, Math.min(0.20, volRatio * fullHeight));
    const rBottom = 0.168;
    const rTop = Math.max(0.038, rBottom * (1.0 - h / 0.26));
    if (liqMesh.geometry) liqMesh.geometry.dispose();
    liqMesh.geometry = new THREE.CylinderGeometry(rTop, rBottom, h, 24);
    liqMesh.position.y = 0.004 + h / 2;
    liqMesh.scale.set(1.0, 1.0, 1.0);
  } else if (liqMesh.geometry.parameters && liqMesh.geometry.parameters.height === 1.0) {
    const newHeight = Math.max(0.02, volRatio * fullHeight);
    liqMesh.scale.set(1.0, newHeight, 1.0);
    liqMesh.position.y = 0.01;
  } else {
    const newHeight = Math.max(0.02, volRatio * fullHeight);
    liqMesh.scale.y = Math.max(1.0, volRatio * 50);
    liqMesh.position.y = Math.max(0.02, newHeight / 2);
  }

  // Update color
  if (hex) {
    try {
      liqMesh.material.color.set(hex);
    } catch (_) {
      liqMesh.material.color.setStyle(hex);
    }
  }

  // Update opacity
  if (opacity !== undefined && opacity !== null) {
    liqMesh.material.opacity = opacity;
    liqMesh.material.transparent = opacity < 1.0;
  } else {
    liqMesh.material.opacity = 0.85;
    liqMesh.material.transparent = true;
  }

  // Update Surface Meniscus Ring if present
  const meniscus = apparatusGroup.userData.meniscusMesh;
  if (meniscus) {
    if (volume_ml <= 0 || volRatio <= 0.001) {
      meniscus.visible = false;
    } else {
      meniscus.visible = true;
      let topY = liqMesh.position.y;
      if (apparatusGroup.userData.isConicalFlask) {
        const h = Math.max(0.02, Math.min(0.20, volRatio * fullHeight));
        topY = 0.004 + h;
        // Dynamically match radius of conical flask at height h
        const rAtTop = Math.max(0.038, 0.168 * (1.0 - h / 0.26));
        meniscus.scale.set(rAtTop / 0.12, rAtTop / 0.12, 1.0);
      } else {
        const newHeight = Math.max(0.02, volRatio * fullHeight);
        topY = 0.01 + newHeight;
      }
      meniscus.position.y = topY;
      if (hex) {
        try {
          meniscus.material.color.set(hex);
        } catch (_) {
          meniscus.material.color.setStyle(hex);
        }
      }
      meniscus.material.opacity = liqMesh.material.opacity;
      meniscus.material.transparent = liqMesh.material.transparent;
    }
  }
}
