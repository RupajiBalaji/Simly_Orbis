/**
 * Digital Readouts, Bedside Vitals, Labels & Highlights (frontend/lab/render/readouts.js)
 * Implements directives: 'readout', 'vitals', 'label', 'highlight'.
 */

import * as THREE from 'three';

export function applyReadoutDirective(apparatusGroup, directive) {
  if (!apparatusGroup) return;

  const { label = '', value = '', unit = '' } = directive;
  const ctx = apparatusGroup.userData.ctx;
  const canvas = apparatusGroup.userData.canvas;
  const tex = apparatusGroup.userData.tex;

  if (ctx && canvas && tex) {
    ctx.fillStyle = '#020617';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = '#38bdf8';
    ctx.font = 'bold 20px monospace';
    ctx.textAlign = 'left';
    ctx.fillText(label.toUpperCase(), 16, 32);

    ctx.fillStyle = '#f8fafc';
    ctx.font = 'bold 36px monospace';
    ctx.textAlign = 'right';
    const valText = typeof value === 'number' ? value.toFixed(2) : String(value);
    ctx.fillText(`${valText} ${unit}`.trim(), canvas.width - 16, canvas.height - 24);

    tex.needsUpdate = true;
  }
}

export function applyVitalsDirective(patientBedGroup, directive) {
  if (!patientBedGroup) return;

  const { hr = 70, spo2 = 99, status = 'Stable', patient = 'Alex' } = directive;

  const mctx = patientBedGroup.userData.monitorCtx;
  const canvas = patientBedGroup.userData.monitorCanvas;
  const tex = patientBedGroup.userData.monitorTex;

  if (mctx && canvas && tex) {
    mctx.fillStyle = '#090d16';
    mctx.fillRect(0, 0, canvas.width, canvas.height);

    // Bedside Header
    mctx.fillStyle = '#38bdf8';
    mctx.font = 'bold 15px monospace';
    mctx.textAlign = 'left';
    mctx.fillText(patient.toUpperCase(), 16, 28);

    // Heart Rate
    mctx.fillStyle = hr > 100 || hr < 50 ? '#ef4444' : '#10b981';
    mctx.font = 'bold 28px monospace';
    mctx.fillText(`HR: ${hr} bpm`, 16, 68);

    // Blood Oxygen SpO2
    mctx.fillStyle = spo2 < 95 ? '#f59e0b' : '#34d399';
    mctx.font = 'bold 24px monospace';
    mctx.fillText(`SpO2: ${spo2}%`, 16, 108);

    // Clinical Status
    mctx.fillStyle = '#c084fc';
    mctx.font = '14px monospace';
    mctx.fillText(status, 16, 142);

    // Simulated ECG strip line
    mctx.strokeStyle = '#10b981';
    mctx.lineWidth = 2;
    mctx.beginPath();
    mctx.moveTo(16, 175);
    for (let x = 16; x < canvas.width - 16; x += 10) {
      const isPeak = (x % 60) === 0;
      const y = isPeak ? 155 : (x % 30 === 0 ? 185 : 175);
      mctx.lineTo(x, y);
    }
    mctx.stroke();

    tex.needsUpdate = true;
  }

  // Tint patient head
  const patientHead = patientBedGroup.userData.patientMesh;
  if (patientHead && patientHead.material) {
    if (status.includes('toxic') || hr > 100) {
      patientHead.material.color.setHex(0xfca5a5); // flushed/distressed
    } else {
      patientHead.material.color.setHex(0xfbd0b5); // calm
    }
  }
}

export function applyLabelDirective(apparatusGroup, directive) {
  if (!apparatusGroup) return;

  const text = directive.text || '';
  let lblMesh = apparatusGroup.userData.labelMesh;

  // If this is a tube rack, lookup specific tube
  if (!lblMesh && apparatusGroup.userData.tubes && directive.target) {
    const tube = apparatusGroup.userData.tubes[directive.target];
    if (tube) {
      lblMesh = tube.userData.labelMesh;
    }
  }

  if (lblMesh) {
    // Generate label texture
    const canvas = document.createElement('canvas');
    canvas.width = 128;
    canvas.height = 48;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, 128, 48);

    ctx.strokeStyle = '#0f172a';
    ctx.lineWidth = 2;
    ctx.strokeRect(2, 2, 124, 44);

    ctx.fillStyle = '#0f172a';
    ctx.font = 'bold 12px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(text.slice(0, 16), 64, 28);

    const tex = new THREE.CanvasTexture(canvas);
    lblMesh.material.map = tex;
    lblMesh.material.opacity = 1.0;
    lblMesh.material.transparent = false;
    lblMesh.material.needsUpdate = true;
  }
}

export function applyHighlightDirective(apparatusGroup) {
  if (!apparatusGroup) return;

  apparatusGroup.traverse((child) => {
    if (child.isMesh && child.material && child.material.emissive) {
      const orig = child.material.emissive.getHex();
      child.material.emissive.setHex(0xec4899); // pulsing magenta
      setTimeout(() => {
        child.material.emissive.setHex(orig);
      }, 1500);
    }
  });
}
