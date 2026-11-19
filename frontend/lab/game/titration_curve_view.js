/**
 * frontend/lab/game/titration_curve_view.js
 * Live Titration Curve with Indicator Transition Band (Spec 9.2 & P3-T3).
 * Renders backend-computed pH vs volume points onto an SVG chart in the HUD.
 */

export function renderTitrationLiveCurve(curveData) {
  if (!curveData) return;

  const section = document.getElementById('hud-titration-curve-section');
  const svg = document.getElementById('titration-curve-svg');
  const summaryEl = document.getElementById('titration-curve-summary');

  if (section) {
    section.style.display = 'block';
  }

  // Ensure right panel is visible when titration curve arrives
  const rightPanel = document.getElementById('hud-right-panel');
  if (rightPanel && rightPanel.classList.contains('collapsed')) {
    rightPanel.classList.remove('collapsed');
  }

  if (summaryEl) {
    summaryEl.textContent = curveData.summary_text || `pH: ${curveData.current_ph.toFixed(2)} | V: ${curveData.titrant_added_ml.toFixed(2)} mL | Equivalence: ${curveData.equivalence_volume_ml.toFixed(2)} mL | Band: ${curveData.indicator_band?.transition_low || 8.2}-${curveData.indicator_band?.transition_high || 10.0}`;
    summaryEl.setAttribute('data-current-ph', String(curveData.current_ph));
    summaryEl.setAttribute('data-current-vol', String(curveData.titrant_added_ml));
    summaryEl.setAttribute('data-equiv-vol', String(curveData.equivalence_volume_ml));
    if (curveData.indicator_band) {
      summaryEl.setAttribute('data-band-low', String(curveData.indicator_band.transition_low));
      summaryEl.setAttribute('data-band-high', String(curveData.indicator_band.transition_high));
    }
  }

  if (!svg) return;

  const w = 260;
  const h = 130;
  const padL = 28;
  const padR = 12;
  const padT = 10;
  const padB = 22;

  const plotW = w - padL - padR;
  const plotH = h - padT - padB;

  const maxVol = 50.0;
  const maxPh = 14.0;

  const toX = (vol) => padL + (vol / maxVol) * plotW;
  const toY = (ph) => padT + (1.0 - (ph / maxPh)) * plotH;

  // Clear previous SVG contents
  while (svg.firstChild) {
    svg.removeChild(svg.firstChild);
  }

  // 1. Indicator transition zone band
  const band = curveData.indicator_band;
  if (band) {
    const yHigh = toY(band.transition_high);
    const yLow = toY(band.transition_low);
    const bandRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    bandRect.setAttribute('x', String(padL));
    bandRect.setAttribute('y', String(yHigh));
    bandRect.setAttribute('width', String(plotW));
    bandRect.setAttribute('height', String(Math.max(2, yLow - yHigh)));
    bandRect.setAttribute('fill', band.color_transition || '#fbcfe8');
    bandRect.setAttribute('fill-opacity', '0.22');
    svg.appendChild(bandRect);

    // Indicator label text
    const bandLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    bandLabel.setAttribute('x', String(padL + 4));
    bandLabel.setAttribute('y', String(Math.max(padT + 10, yHigh + 10)));
    bandLabel.setAttribute('fill', band.color_base || '#ec4899');
    bandLabel.setAttribute('font-size', '8px');
    bandLabel.setAttribute('font-family', 'var(--font-mono, monospace)');
    bandLabel.setAttribute('opacity', '0.85');
    bandLabel.textContent = `${band.name || 'Indicator'} band (${band.transition_low}-${band.transition_high})`;
    svg.appendChild(bandLabel);
  }

  // 2. Equivalence volume guideline
  const eqX = toX(curveData.equivalence_volume_ml || 25.0);
  const eqLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
  eqLine.setAttribute('x1', String(eqX));
  eqLine.setAttribute('y1', String(padT));
  eqLine.setAttribute('x2', String(eqX));
  eqLine.setAttribute('y2', String(padT + plotH));
  eqLine.setAttribute('stroke', '#64748b');
  eqLine.setAttribute('stroke-dasharray', '3,3');
  eqLine.setAttribute('stroke-width', '1');
  svg.appendChild(eqLine);

  // 3. Grid lines & axes
  for (const phVal of [0, 7, 14]) {
    const y = toY(phVal);
    const gLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    gLine.setAttribute('x1', String(padL));
    gLine.setAttribute('y1', String(y));
    gLine.setAttribute('x2', String(padL + plotW));
    gLine.setAttribute('y2', String(y));
    gLine.setAttribute('stroke', 'rgba(255,255,255,0.08)');
    gLine.setAttribute('stroke-width', '1');
    svg.appendChild(gLine);

    const txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    txt.setAttribute('x', String(padL - 4));
    txt.setAttribute('y', String(y + 3));
    txt.setAttribute('text-anchor', 'end');
    txt.setAttribute('fill', '#94a3b8');
    txt.setAttribute('font-size', '8px');
    txt.setAttribute('font-family', 'var(--font-mono, monospace)');
    txt.textContent = String(phVal);
    svg.appendChild(txt);
  }

  // 4. Theoretical curve points
  if (curveData.points && curveData.points.length > 0) {
    const pathD = curveData.points
      .map((pt, i) => `${i === 0 ? 'M' : 'L'} ${toX(pt.volume_ml).toFixed(1)} ${toY(pt.ph).toFixed(1)}`)
      .join(' ');

    const curvePath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    curvePath.setAttribute('d', pathD);
    curvePath.setAttribute('fill', 'none');
    curvePath.setAttribute('stroke', '#38bdf8');
    curvePath.setAttribute('stroke-width', '1.8');
    svg.appendChild(curvePath);
  }

  // 5. Current delivery point marker
  const curX = toX(curveData.titrant_added_ml || 0.0);
  const curY = toY(curveData.current_ph || 1.0);

  const marker = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  marker.setAttribute('cx', String(curX));
  marker.setAttribute('cy', String(curY));
  marker.setAttribute('r', '4.5');
  marker.setAttribute('fill', curveData.current_color || '#f8fafc');
  marker.setAttribute('stroke', '#f43f5e');
  marker.setAttribute('stroke-width', '1.8');
  svg.appendChild(marker);
}

if (typeof window !== 'undefined') {
  window.renderTitrationLiveCurve = renderTitrationLiveCurve;
}
