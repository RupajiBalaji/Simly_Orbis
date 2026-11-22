/**
 * frontend/lab/game/kinetics_view.js
 * Kinetics Bench Interactive UI & Linearised Plots (Spec 9.2 & P3-T4).
 * Renders [A], ln[A], and 1/[A] vs time, displays regression R^2,
 * and handles student rate order / rate constant estimate submission.
 */

export function renderKineticsPanel(session) {
  if (!session || session.experiment_id !== 'kinetics_bench') return;

  let panel = document.getElementById('hud-kinetics-panel');
  if (!panel) {
    const parent = document.getElementById('hud-right-panel');
    if (!parent) return;

    panel = document.createElement('div');
    panel.id = 'hud-kinetics-panel';
    panel.style.cssText = 'padding:10px 14px; border-bottom:1px solid rgba(255,255,255,0.1); background:rgba(0,0,0,0.2);';
    parent.insertBefore(panel, parent.firstChild);
  }

  // Ensure right panel is visible
  const rightPanel = document.getElementById('hud-right-panel');
  if (rightPanel) {
    rightPanel.style.display = 'block';
    rightPanel.classList.remove('collapsed');
  }

  const specDev = session.apparatus_state?.spectrophotometer || {};
  const timeSeries = specDev.time_series || [];
  const fits = specDev.linear_fits || {};

  const r0 = fits.order_0?.r_squared !== undefined ? fits.order_0.r_squared.toFixed(4) : '--';
  const r1 = fits.order_1?.r_squared !== undefined ? fits.order_1.r_squared.toFixed(4) : '--';
  const r2 = fits.order_2?.r_squared !== undefined ? fits.order_2.r_squared.toFixed(4) : '--';

  panel.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
      <span style="font-size:var(--text-xs); font-weight:700; color:var(--accent); text-transform:uppercase;">Kinetics Linearised Analysis</span>
      <span class="source-chip chip-engine">[chem.kinetics]</span>
    </div>

    <div style="font-size:11px; color:var(--text-muted); margin-bottom:8px;">
      Samples Collected: <b>${timeSeries.length}</b> | Last [A]: <b>${specDev.last_reading_m ? specDev.last_reading_m.toFixed(4) + ' M' : 'None'}</b>
    </div>

    <!-- Linear Model Fit R^2 Comparison -->
    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:6px; margin-bottom:10px;">
      <div style="background:rgba(255,255,255,0.04); padding:6px; border-radius:6px; text-align:center;">
        <div style="font-size:9px; color:var(--text-muted);">ORDER 0 ([A])</div>
        <div id="r2-order-0" style="font-family:var(--font-mono); font-size:12px; font-weight:700; color:${fits.order_0?.r_squared > 0.98 ? '#10b981' : '#f8fafc'};">R²: ${r0}</div>
      </div>
      <div style="background:rgba(255,255,255,0.04); padding:6px; border-radius:6px; text-align:center;">
        <div style="font-size:9px; color:var(--text-muted);">ORDER 1 (ln[A])</div>
        <div id="r2-order-1" style="font-family:var(--font-mono); font-size:12px; font-weight:700; color:${fits.order_1?.r_squared > 0.98 ? '#10b981' : '#f8fafc'};">R²: ${r1}</div>
      </div>
      <div style="background:rgba(255,255,255,0.04); padding:6px; border-radius:6px; text-align:center;">
        <div style="font-size:9px; color:var(--text-muted);">ORDER 2 (1/[A])</div>
        <div id="r2-order-2" style="font-family:var(--font-mono); font-size:12px; font-weight:700; color:${fits.order_2?.r_squared > 0.98 ? '#10b981' : '#f8fafc'};">R²: ${r2}</div>
      </div>
    </div>

    <!-- Student Estimation Submission Box -->
    <div style="background:rgba(15,23,42,0.8); border:1px solid rgba(255,255,255,0.08); border-radius:6px; padding:8px;">
      <div style="font-size:10px; font-weight:700; color:var(--text); margin-bottom:6px;">SUBMIT KINETIC ESTIMATE</div>
      <div style="display:flex; gap:6px; margin-bottom:6px;">
        <select id="kinetics-est-order" style="background:#1e293b; color:#fff; border:1px solid #334155; border-radius:4px; padding:2px 6px; font-size:11px;">
          <option value="0">Order 0</option>
          <option value="1" selected>Order 1</option>
          <option value="2">Order 2</option>
        </select>
        <input type="number" id="kinetics-est-k" step="0.001" placeholder="Est. k" value="0.05" style="width:80px; background:#1e293b; color:#fff; border:1px solid #334155; border-radius:4px; padding:2px 6px; font-size:11px;" />
        <button type="button" id="btn-submit-kinetics-estimate" class="btn btn-primary" style="min-height:24px; padding:2px 8px; font-size:11px;">Submit</button>
      </div>
      <div id="kinetics-estimate-feedback" style="font-size:10px; color:var(--text-muted);">
        Analyze linear plots above, then submit your order and rate constant.
      </div>
    </div>
  `;

  const btnSubmit = document.getElementById('btn-submit-kinetics-estimate');
  if (btnSubmit) {
    btnSubmit.onclick = async () => {
      const orderVal = parseInt(document.getElementById('kinetics-est-order').value, 10);
      const kVal = parseFloat(document.getElementById('kinetics-est-k').value);
      if (window.actionMenu) {
        const res = await window.actionMenu.executeAction('submit_order_estimate', 'spectrophotometer', {
          estimated_order: orderVal,
          estimated_k: kVal,
        });
        const fb = document.getElementById('kinetics-estimate-feedback');
        if (fb && res?.message) {
          fb.textContent = res.message;
          fb.style.color = '#10b981';
        }
      }
    };
  }
}

if (typeof window !== 'undefined') {
  window.renderKineticsPanel = renderKineticsPanel;
}
