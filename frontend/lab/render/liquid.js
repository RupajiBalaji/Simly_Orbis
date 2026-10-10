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

  const volRatio = Math.max(0.001, Math.min(1.0, volume_ml / maxVol));
  const newHeight = volRatio * fullHeight;

  // Update scale & position
  liqMesh.scale.y = Math.max(0.01, volRatio * 100);
  liqMesh.position.y = newHeight / 2;

  // Update color
  if (hex) {
    liqMesh.material.color.setStyle(hex);
  }

  // Update opacity
  if (opacity !== undefined && opacity !== null) {
    liqMesh.material.opacity = opacity;
    liqMesh.material.transparent = opacity < 1.0;
  } else if (volume_ml <= 0) {
    liqMesh.material.opacity = 0.0;
  } else {
    liqMesh.material.opacity = 0.85;
  }
}
