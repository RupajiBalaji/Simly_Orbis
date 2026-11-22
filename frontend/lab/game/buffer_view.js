/**
 * frontend/lab/game/buffer_view.js
 * Buffer Solutions & Capacity Bench Interactive UI (Spec 9.2 & P3-T5).
 * Renders target vs actual pH, Van Slyke buffer capacity beta,
 * acid/base stress curve, and handles student buffer design evaluation.
 */

export function renderBufferPanel(session) {
  if (!session || session.experiment_id !== 'buffer_bench') return;

  let panel = document.getElementById('hud-buffer-panel');
  if (!panel) {
    const parent = document.getElementById('hud-right-panel');
    if (!parent) return;

    panel = document.createElement('div');
    panel.id = 'hud-buffer-panel';
    panel.style.cssText = 'padding:10px 14px; border-bottom:1px solid rgba(255,255,255,0.1); background:rgba(0,0,0,0.2);';
    parent.insertBefore(panel, parent.firstChild);
  }

  // Ensure right panel is visible
  const rightPanel = document.getElementById('hud-right-panel');
  if (rightPanel) {
    rightPanel.style.display = 'block';
    rightPanel.classList.remove('collapsed');
  }

  const beaker = session.apparatus_state?.buffer_beaker || {};
  const burette = session.apparatus_state?.stress_burette || {};
  const phMeter = session.apparatus_state?.ph_meter || {};
  const stressCurve = burette.stress_curve || [];

  const targetPh = beaker.target_ph !== undefined ? beaker.target_ph.toFixed(2) : '4.75';
  const currentPh = phMeter.reading !== null && phMeter.reading !== undefined ? phMeter.reading.toFixed(2) : (beaker.ph !== undefined && beaker.ph !== null ? beaker.ph.toFixed(2) : '--');
  const beta = beaker.buffer_capacity_beta !== undefined && beaker.buffer_capacity_beta !== null ? beaker.buffer_capacity_beta.toFixed(4) : '--';

  let curveSummary = 'No stress additions recorded.';
  if (stressCurve.length > 0) {
    const initial = stressCurve[0];
    const finalPt = stressCurve[stressCurve.length - 1];
    curveSummary = `Titrant: ${burette.titrant?.toUpperCase() || 'HCL'} | Added: ${burette.volume_dispensed_ml?.toFixed(1) || '0.0'} mL | Initial pH: ${initial.ph.toFixed(2)} -> Final: ${finalPt.ph.toFixed(2)}`;
  }

  panel.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
      <span style="font-size:var(--text-xs); font-weight:700; color:var(--accent); text-transform:uppercase;">Buffer Capacity & Equilibrium</span>
      <span class="source-chip chip-engine">[chem.buffer]</span>
    </div>

    <!-- Key Metrics Grid -->
    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:6px; margin-bottom:10px;">
      <div style="background:rgba(255,255,255,0.04); padding:6px; border-radius:6px; text-align:center;">
        <div style="font-size:9px; color:var(--text-muted);">TARGET pH</div>
        <div id="buffer-target-ph" style="font-family:var(--font-mono); font-size:12px; font-weight:700; color:#38bdf8;">${targetPh}</div>
      </div>
      <div style="background:rgba(255,255,255,0.04); padding:6px; border-radius:6px; text-align:center;">
        <div style="font-size:9px; color:var(--text-muted);">CURRENT pH</div>
        <div id="buffer-current-ph" style="font-family:var(--font-mono); font-size:12px; font-weight:700; color:#10b981;">${currentPh}</div>
      </div>
      <div style="background:rgba(255,255,255,0.04); padding:6px; border-radius:6px; text-align:center;">
        <div style="font-size:9px; color:var(--text-muted);">CAPACITY β</div>
        <div id="buffer-beta-val" style="font-family:var(--font-mono); font-size:11px; font-weight:700; color:#fbbf24;">${beta}</div>
      </div>
    </div>

    <!-- Stress Curve Summary Box -->
    <div style="background:rgba(15,23,42,0.8); border:1px solid rgba(255,255,255,0.08); border-radius:6px; padding:8px; margin-bottom:10px;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
        <span style="font-size:10px; font-weight:700; color:var(--text);">ACID/BASE STRESS RESPONSE</span>
        <span style="font-size:9px; color:var(--text-muted);">${stressCurve.length} data points</span>
      </div>
      <div id="buffer-curve-summary" style="font-family:var(--font-mono); font-size:10px; color:#94a3b8; line-height:1.4;">
        ${curveSummary}
      </div>
    </div>

    <!-- Fast Action Controls -->
    <div style="display:flex; gap:6px;">
      <button type="button" id="btn-quick-stress-hcl" class="btn btn-secondary" style="flex:1; min-height:26px; padding:2px 6px; font-size:10px;">+ HCl Stress</button>
      <button type="button" id="btn-quick-stress-naoh" class="btn btn-secondary" style="flex:1; min-height:26px; padding:2px 6px; font-size:10px;">+ NaOH Stress</button>
      <button type="button" id="btn-submit-buffer-eval" class="btn btn-primary" style="flex:1; min-height:26px; padding:2px 6px; font-size:10px;">Evaluate</button>
    </div>
  `;

  // Hook action buttons
  const btnHcl = document.getElementById('btn-quick-stress-hcl');
  if (btnHcl) {
    btnHcl.onclick = async () => {
      if (window.actionMenu) {
        await window.actionMenu.executeAction('stress_buffer', 'stress_burette', {
          titrant: 'hcl',
          titrant_conc_m: 1.0,
          max_added_ml: 15.0,
          num_steps: 25,
        });
      }
    };
  }

  const btnNaoh = document.getElementById('btn-quick-stress-naoh');
  if (btnNaoh) {
    btnNaoh.onclick = async () => {
      if (window.actionMenu) {
        await window.actionMenu.executeAction('stress_buffer', 'stress_burette', {
          titrant: 'naoh',
          titrant_conc_m: 1.0,
          max_added_ml: 15.0,
          num_steps: 25,
        });
      }
    };
  }

  const btnEval = document.getElementById('btn-submit-buffer-eval');
  if (btnEval) {
    btnEval.onclick = async () => {
      if (window.actionMenu) {
        await window.actionMenu.executeAction('submit_buffer_design', 'avatar', {});
      }
    };
  }
}

if (typeof window !== 'undefined') {
  window.renderBufferPanel = renderBufferPanel;
}
