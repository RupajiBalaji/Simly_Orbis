/**
 * Dose Response & PK/PD Analytics Panel (frontend/lab/game/dose_panel.js)
 * Interactive concentration-time chart, target therapeutic window band,
 * PD effect curve overlay, 2-regimen comparison, adult covariate controls,
 * and scientific prediction interface.
 * Educational simulation platform. Not medical advice. Not clinical evidence.
 */

import { api } from '../api.js';
import { state } from '../state.js';
import { toast } from './toast.js';

export const DRUGS_V2_CATALOG = {
  paracetamol: {
    name: "Paracetamol",
    model_type: "one_compartment",
    routes_allowed: ["oral", "iv_infusion"],
    max_game_dose_mg: 1000.0,
    target_window_low: 10.0,
    target_window_high: 20.0,
    fe: 0.05,
    is_nti: false,
  },
  ibuprofen: {
    name: "Ibuprofen",
    model_type: "one_compartment",
    routes_allowed: ["oral"],
    max_game_dose_mg: 800.0,
    target_window_low: 15.0,
    target_window_high: 30.0,
    fe: 0.01,
    is_nti: false,
  },
  caffeine: {
    name: "Caffeine",
    model_type: "one_compartment",
    routes_allowed: ["oral"],
    max_game_dose_mg: 300.0,
    target_window_low: 2.0,
    target_window_high: 8.0,
    fe: 0.02,
    is_nti: false,
  },
  aspirin: {
    name: "Aspirin",
    model_type: "one_compartment",
    routes_allowed: ["oral"],
    max_game_dose_mg: 1000.0,
    target_window_low: 15.0,
    target_window_high: 30.0,
    fe: 0.02,
    is_nti: false,
  },
  amoxicillin: {
    name: "Amoxicillin",
    model_type: "one_compartment",
    routes_allowed: ["oral", "iv_bolus"],
    max_game_dose_mg: 1000.0,
    target_window_low: 2.0,
    target_window_high: 10.0,
    fe: 0.70,
    is_nti: false,
  },
  metformin: {
    name: "Metformin",
    model_type: "two_compartment",
    routes_allowed: ["oral"],
    max_game_dose_mg: 1000.0,
    target_window_low: 1.0,
    target_window_high: 3.0,
    fe: 0.90,
    is_nti: false,
  },
  atenolol: {
    name: "Atenolol",
    model_type: "one_compartment",
    routes_allowed: ["oral", "iv_bolus"],
    max_game_dose_mg: 100.0,
    target_window_low: 0.2,
    target_window_high: 1.0,
    fe: 0.85,
    is_nti: false,
  },
  theophylline: {
    name: "Theophylline",
    model_type: "one_compartment",
    routes_allowed: ["oral", "iv_infusion"],
    max_game_dose_mg: 400.0,
    target_window_low: 10.0,
    target_window_high: 20.0,
    fe: 0.10,
    is_nti: true,
  },
  gentamicin: {
    name: "Gentamicin",
    model_type: "two_compartment",
    routes_allowed: ["iv_bolus", "iv_infusion"],
    max_game_dose_mg: 350.0,
    target_window_low: 4.0,
    target_window_high: 12.0,
    fe: 0.95,
    is_nti: true,
  },
  vancomycin: {
    name: "Vancomycin",
    model_type: "two_compartment",
    routes_allowed: ["iv_infusion"],
    max_game_dose_mg: 1500.0,
    target_window_low: 15.0,
    target_window_high: 25.0,
    fe: 0.85,
    is_nti: true,
  },
  midazolam: {
    name: "Midazolam",
    model_type: "two_compartment",
    routes_allowed: ["oral", "iv_bolus"],
    max_game_dose_mg: 15.0,
    target_window_low: 0.05,
    target_window_high: 0.20,
    fe: 0.01,
    is_nti: false,
  },
  digoxin: {
    name: "Digoxin",
    model_type: "two_compartment",
    routes_allowed: ["oral", "iv_bolus"],
    max_game_dose_mg: 0.50,
    target_window_low: 0.0008,
    target_window_high: 0.0020,
    fe: 0.75,
    is_nti: true,
  },
};

export class DosePanel {
  constructor() {
    this.panelEl = document.getElementById('dose-lab-panel');
    this.isOpen = false;
    this.selectedDrug = 'theophylline';
    this.selectedRoute = 'oral';
    this.weightKg = 70.0;
    this.ageYr = 35.0;
    this.crclMlMin = 100.0;
    this.doseMg = 300.0;
    this.nDoses = 1;
    this.intervalH = 8.0;
    this.infusionDurationH = 1.0;
    this.samplingSchedule = '0,1,2,4,8,12,24';

    this.lastResult = null;
    this.lastCurve = [];
    this.lastEffectCurve = [];
    this.comparisonCurve = null;
    this.targetWindow = { low: 10.0, high: 20.0, toxic: 30.0 };

    this.canvas = null;
    this.ctx = null;

    this.initDOM();
  }

  initDOM() {
    if (!this.panelEl) return;

    this.panelEl.innerHTML = `
      <div class="dose-panel-header">
        <div class="dose-title-wrap">
          <span class="dose-badge">💊 PHARMA DEPTH</span>
          <h3>Dose Response Lab</h3>
        </div>
        <button type="button" class="btn-close-dose" id="btn-close-dose" title="Minimize Panel">✕</button>
      </div>

      <div class="dose-disclaimer">
        Educational simulation, not medical advice. Simplified pharmacokinetic & pharmacodynamic models.
      </div>

      <!-- Main Scrollable Body -->
      <div class="dose-panel-body">
        <!-- 1. Patient Demographics & Adult Covariates -->
        <section class="dose-section">
          <div class="section-title">👤 Patient Demographics & Adult Covariates</div>
          <div class="preset-pill-row">
            <button type="button" class="btn-preset active" id="btn-preset-std">Standard (70kg, 35y, 100mL/min)</button>
            <button type="button" class="btn-preset" id="btn-preset-renal">Renal Impaired (30mL/min)</button>
            <button type="button" class="btn-preset" id="btn-preset-elderly">Elderly (78y, 45mL/min)</button>
          </div>

          <div class="dose-slider-grid">
            <div class="slider-field">
              <div class="slider-header">
                <label for="cov-weight">Weight (40–150 kg)</label>
                <span class="slider-val" id="cov-weight-val">70.0 kg</span>
              </div>
              <input type="range" id="cov-weight" min="40" max="150" step="1" value="70" />
            </div>

            <div class="slider-field">
              <div class="slider-header">
                <label for="cov-age">Age (18–90 yr)</label>
                <span class="slider-val" id="cov-age-val">35 yr</span>
              </div>
              <input type="range" id="cov-age" min="18" max="90" step="1" value="35" />
            </div>

            <div class="slider-field">
              <div class="slider-header">
                <label for="cov-crcl">CrCl (15–150 mL/min)</label>
                <span class="slider-val" id="cov-crcl-val">100.0 mL/min</span>
              </div>
              <input type="range" id="cov-crcl" min="15" max="150" step="1" value="100" />
            </div>
          </div>

          <div class="dose-btn-row" style="margin-top: 8px;">
            <button type="button" class="btn-secondary" id="btn-ack-renal">✓ Acknowledge Renal Function</button>
            <button type="button" class="btn-secondary" id="btn-apply-cov">Apply Covariates</button>
          </div>
        </section>

        <!-- 2. Drug Selection & Regimen -->
        <section class="dose-section">
          <div class="section-title">🧪 Formulary Drug & Regimen</div>
          <div class="form-row">
            <label for="select-drug">Drug Compound</label>
            <select id="select-drug" class="dose-select"></select>
          </div>

          <div class="form-row">
            <label>Administration Route</label>
            <div id="route-options-container" class="route-pills-row"></div>
          </div>

          <div class="form-row">
            <div class="slider-header">
              <label for="dose-amount">Dose Amount (mg)</label>
              <span class="slider-val" id="dose-amount-val">300 mg</span>
            </div>
            <input type="range" id="dose-amount" min="10" max="400" step="10" value="300" />
          </div>

          <div class="grid-two-col">
            <div class="form-field">
              <label for="dose-ndoses">Doses Count</label>
              <input type="number" id="dose-ndoses" min="1" max="6" value="1" class="dose-input" />
            </div>
            <div class="form-field">
              <label for="dose-interval">Interval (h)</label>
              <input type="number" id="dose-interval" min="2" max="24" value="8" class="dose-input" />
            </div>
          </div>

          <div class="form-row" id="infusion-duration-row" style="display:none; margin-top:8px;">
            <div class="slider-header">
              <label for="infusion-duration">Infusion Duration (h)</label>
              <span class="slider-val" id="infusion-duration-val">1.0 h</span>
            </div>
            <input type="range" id="infusion-duration" min="0.25" max="4.0" step="0.25" value="1.0" />
          </div>
        </section>

        <!-- 3. Scientific Prediction & Sampling -->
        <section class="dose-section">
          <div class="section-title">🎯 Scientific Window Prediction & Sampling</div>
          <div class="grid-two-col">
            <div class="form-field">
              <label for="pred-cmax">Predicted Cmax (mg/L)</label>
              <input type="number" id="pred-cmax" step="0.1" value="8.5" class="dose-input" />
            </div>
            <div class="form-field">
              <label for="pred-time">Window Duration (h)</label>
              <input type="number" id="pred-time" step="0.5" value="0.0" class="dose-input" />
            </div>
          </div>

          <div class="form-row" style="margin-top:8px;">
            <label for="sampling-select">Sampling Protocol</label>
            <select id="sampling-select" class="dose-select">
              <option value="0,1,2,4,8,12,24">Standard Multi-Point (0, 1, 2, 4, 8, 12, 24 h)</option>
              <option value="1,4,8,12,24">TDM Monitoring (1, 4, 8, 12, 24 h)</option>
              <option value="0.5,1,2,4">Rapid Phase (0.5, 1, 2, 4 h)</option>
            </select>
          </div>

          <div class="dose-btn-row" style="margin-top:10px;">
            <button type="button" class="btn-primary" id="btn-submit-prediction">📝 Record Prediction</button>
            <button type="button" class="btn-primary" id="btn-run-sim" style="background: linear-gradient(135deg, #0ea5e9, #38bdf8);">⚡ Simulate PK/PD</button>
          </div>
        </section>

        <!-- 4. Interactive PK/PD Curves Canvas Chart -->
        <section class="dose-section">
          <div class="section-title" style="display:flex; justify-content:space-between; align-items:center;">
            <span>📈 Concentration & Effect Curves</span>
            <span class="legend-chip"><span class="color-dot teal"></span> Simulated <span class="color-dot purple"></span> Target Window</span>
          </div>

          <div class="chart-canvas-wrap">
            <canvas id="dose-chart-canvas" width="400" height="210"></canvas>
          </div>

          <!-- Summary Metric Badges (DOM Elements for QA / Test Asserts) -->
          <div class="metric-readouts-grid">
            <div class="metric-card">
              <span class="metric-label">Cmax</span>
              <span class="metric-val" id="dose-chart-cmax">-- mg/L</span>
            </div>
            <div class="metric-card">
              <span class="metric-label">Tmax</span>
              <span class="metric-val" id="dose-chart-tmax">-- h</span>
            </div>
            <div class="metric-card">
              <span class="metric-label">AUC (0-24h)</span>
              <span class="metric-val" id="dose-chart-auc">-- mg·h/L</span>
            </div>
            <div class="metric-card">
              <span class="metric-label">Half-life</span>
              <span class="metric-val" id="dose-chart-halflife">-- h</span>
            </div>
            <div class="metric-card">
              <span class="metric-label">In Window</span>
              <span class="metric-val" id="dose-chart-window-time">-- h</span>
            </div>
            <div class="metric-card">
              <span class="metric-label">Status</span>
              <span class="metric-val" id="dose-chart-status">Ready</span>
            </div>
          </div>

          <div class="dose-btn-row" style="margin-top:12px;">
            <button type="button" class="btn-secondary" id="btn-compare-regimens">📊 Compare Regimens (Overlay)</button>
            <button type="button" class="btn-secondary" id="btn-debrief-pkpd">📋 Debrief Session</button>
          </div>
        </section>
      </div>
    `;

    this.canvas = document.getElementById('dose-chart-canvas');
    if (this.canvas) {
      this.ctx = this.canvas.getContext('2d');
    }

    this.bindEvents();
    this.populateDrugs();
    this.drawChart();
  }

  populateDrugs() {
    const sel = document.getElementById('select-drug');
    if (!sel) return;
    sel.innerHTML = '';
    for (const [key, item] of Object.entries(DRUGS_V2_CATALOG)) {
      const opt = document.createElement('option');
      opt.value = key;
      opt.textContent = `${item.name}${item.is_nti ? ' [NTI]' : ''} (${item.model_type.replace('_', ' ')})`;
      if (key === this.selectedDrug) opt.selected = true;
      sel.appendChild(opt);
    }
    this.updateRouteOptions();
  }

  updateRouteOptions() {
    const container = document.getElementById('route-options-container');
    const drug = DRUGS_V2_CATALOG[this.selectedDrug];
    if (!container || !drug) return;
    container.innerHTML = '';

    drug.routes_allowed.forEach((route) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = `route-pill ${route === this.selectedRoute ? 'active' : ''}`;
      btn.textContent = route.replace('_', ' ').toUpperCase();
      btn.onclick = () => {
        this.selectedRoute = route;
        this.updateRouteOptions();
        this.updateDoseSlider();
        this.updateInfusionRow();
      };
      container.appendChild(btn);
    });

    if (!drug.routes_allowed.includes(this.selectedRoute)) {
      this.selectedRoute = drug.routes_allowed[0];
      this.updateRouteOptions();
    }
    this.updateDoseSlider();
    this.updateInfusionRow();
  }

  updateInfusionRow() {
    const row = document.getElementById('infusion-duration-row');
    if (row) {
      row.style.display = this.selectedRoute === 'iv_infusion' ? 'block' : 'none';
    }
  }

  updateDoseSlider() {
    const drug = DRUGS_V2_CATALOG[this.selectedDrug];
    const slider = document.getElementById('dose-amount');
    const valLabel = document.getElementById('dose-amount-val');
    if (drug && slider && valLabel) {
      const maxD = drug.max_game_dose_mg;
      slider.max = maxD;
      slider.step = maxD <= 10 ? 0.05 : (maxD <= 100 ? 5 : 10);
      slider.value = Math.min(this.doseMg, maxD);
      this.doseMg = parseFloat(slider.value);
      valLabel.textContent = `${this.doseMg} mg`;
    }
  }

  bindEvents() {
    const btnClose = document.getElementById('btn-close-dose');
    if (btnClose) btnClose.onclick = () => this.close();

    // Covariates
    const wSlider = document.getElementById('cov-weight');
    const wVal = document.getElementById('cov-weight-val');
    if (wSlider) {
      wSlider.oninput = (e) => {
        this.weightKg = Math.max(40.0, Math.min(150.0, parseFloat(e.target.value)));
        if (wVal) wVal.textContent = `${this.weightKg.toFixed(1)} kg`;
      };
    }

    const aSlider = document.getElementById('cov-age');
    const aVal = document.getElementById('cov-age-val');
    if (aSlider) {
      aSlider.oninput = (e) => {
        this.ageYr = Math.max(18.0, Math.min(90.0, parseFloat(e.target.value)));
        if (aVal) aVal.textContent = `${this.ageYr.toFixed(0)} yr`;
      };
    }

    const cSlider = document.getElementById('cov-crcl');
    const cVal = document.getElementById('cov-crcl-val');
    if (cSlider) {
      cSlider.oninput = (e) => {
        this.crclMlMin = Math.max(15.0, Math.min(150.0, parseFloat(e.target.value)));
        if (cVal) cVal.textContent = `${this.crclMlMin.toFixed(1)} mL/min`;
      };
    }

    // Presets
    const pStd = document.getElementById('btn-preset-std');
    const pRen = document.getElementById('btn-preset-renal');
    const pEld = document.getElementById('btn-preset-elderly');
    if (pStd) {
      pStd.onclick = () => {
        this.setCovariatesUI(70.0, 35.0, 100.0);
        this.setActivePreset(pStd);
      };
    }
    if (pRen) {
      pRen.onclick = () => {
        this.setCovariatesUI(65.0, 68.0, 30.0);
        this.setActivePreset(pRen);
      };
    }
    if (pEld) {
      pEld.onclick = () => {
        this.setCovariatesUI(60.0, 78.0, 45.0);
        this.setActivePreset(pEld);
      };
    }

    // Dose Slider
    const dSlider = document.getElementById('dose-amount');
    const dVal = document.getElementById('dose-amount-val');
    if (dSlider) {
      dSlider.oninput = (e) => {
        this.doseMg = parseFloat(e.target.value);
        if (dVal) dVal.textContent = `${this.doseMg} mg`;
      };
    }

    // Infusion Duration Slider
    const durSlider = document.getElementById('infusion-duration');
    const durVal = document.getElementById('infusion-duration-val');
    if (durSlider) {
      durSlider.oninput = (e) => {
        this.infusionDurationH = Math.max(0.25, parseFloat(e.target.value));
        if (durVal) durVal.textContent = `${this.infusionDurationH.toFixed(2)} h`;
      };
    }

    // Drug Selector Change
    const drugSelect = document.getElementById('select-drug');
    if (drugSelect) {
      drugSelect.onchange = (e) => {
        this.selectedDrug = e.target.value;
        this.updateRouteOptions();
        const d = DRUGS_V2_CATALOG[this.selectedDrug];
        if (d) {
          this.targetWindow = {
            low: d.target_window_low,
            high: d.target_window_high,
            toxic: d.target_window_high * 1.5,
          };
          this.drawChart();
        }
      };
    }

    // Action Execution Buttons
    const btnAckRenal = document.getElementById('btn-ack-renal');
    if (btnAckRenal) {
      btnAckRenal.onclick = async () => {
        if (!state.session?.session_id) return;
        const res = await api.applyAction(state.session.session_id, 'check_renal', 'patient_monitor', {});
        toast.showSuccess(res.message);
      };
    }

    const btnApplyCov = document.getElementById('btn-apply-cov');
    if (btnApplyCov) {
      btnApplyCov.onclick = async () => {
        if (!state.session?.session_id) return;
        const res = await api.applyAction(state.session.session_id, 'set_covariates', 'patient_monitor', {
          weight_kg: this.weightKg,
          age_yr: this.ageYr,
          crcl_ml_min: this.crclMlMin,
        });
        toast.showSuccess(res.message);
      };
    }

    const btnPredict = document.getElementById('btn-submit-prediction');
    if (btnPredict) {
      btnPredict.onclick = async () => {
        if (!state.session?.session_id) return;
        const cmaxInp = document.getElementById('pred-cmax');
        const timeInp = document.getElementById('pred-time');
        const cmax = parseFloat(cmaxInp?.value || 10.0);
        const winT = parseFloat(timeInp?.value || 0.0);
        const res = await api.applyAction(state.session.session_id, 'predict_window', 'prediction_slate', {
          predicted_cmax: cmax,
          predicted_time_in_window_h: winT,
        });
        toast.showSuccess(res.message);
      };
    }

    const btnRunSim = document.getElementById('btn-run-sim');
    if (btnRunSim) {
      btnRunSim.onclick = async () => {
        await this.executeFullSimulationSequence();
      };
    }

    const btnComp = document.getElementById('btn-compare-regimens');
    if (btnComp) {
      btnComp.onclick = async () => {
        if (!state.session?.session_id) return;
        if (this.lastCurve && this.lastCurve.length > 0) {
          this.comparisonCurve = [...this.lastCurve];
        }
        const res = await api.applyAction(state.session.session_id, 'compare_regimens', 'pkpd_chart_display', {});
        toast.showInfo('Active regimen saved as comparison overlay.');
        this.drawChart();
      };
    }

    const btnDebrief = document.getElementById('btn-debrief-pkpd');
    if (btnDebrief) {
      btnDebrief.onclick = async () => {
        if (!state.session?.session_id) return;
        const res = await api.applyAction(state.session.session_id, 'debrief_pkpd', 'debrief_station', {});
        toast.showSuccess(res.message);
      };
    }
  }

  setCovariatesUI(wt, age, crcl) {
    this.weightKg = wt;
    this.ageYr = age;
    this.crclMlMin = crcl;
    const wSlider = document.getElementById('cov-weight');
    const wVal = document.getElementById('cov-weight-val');
    const aSlider = document.getElementById('cov-age');
    const aVal = document.getElementById('cov-age-val');
    const cSlider = document.getElementById('cov-crcl');
    const cVal = document.getElementById('cov-crcl-val');
    if (wSlider) wSlider.value = wt;
    if (wVal) wVal.textContent = `${wt.toFixed(1)} kg`;
    if (aSlider) aSlider.value = age;
    if (aVal) aVal.textContent = `${age.toFixed(0)} yr`;
    if (cSlider) cSlider.value = crcl;
    if (cVal) cVal.textContent = `${crcl.toFixed(1)} mL/min`;
  }

  setActivePreset(activeBtn) {
    const btns = [document.getElementById('btn-preset-std'), document.getElementById('btn-preset-renal'), document.getElementById('btn-preset-elderly')];
    btns.forEach((b) => b?.classList.remove('active'));
    activeBtn?.classList.add('active');
  }

  async executeFullSimulationSequence() {
    if (!state.session?.session_id) return;
    const sId = state.session.session_id;

    // Synchronize actions before run
    await api.applyAction(sId, 'set_covariates', 'patient_monitor', {
      weight_kg: this.weightKg,
      age_yr: this.ageYr,
      crcl_ml_min: this.crclMlMin,
    });
    if (this.crclMlMin < 60.0) {
      await api.applyAction(sId, 'check_renal', 'patient_monitor', {});
    }
    await api.applyAction(sId, 'select_drug', 'infusion_pump', { drug_id: this.selectedDrug });
    await api.applyAction(sId, 'set_route', 'infusion_pump', { route: this.selectedRoute });
    await api.applyAction(sId, 'set_dose', 'infusion_pump', { dose_mg: this.doseMg });

    const nDoses = parseInt(document.getElementById('dose-ndoses')?.value || 1);
    const interval = parseFloat(document.getElementById('dose-interval')?.value || 8);
    await api.applyAction(sId, 'set_regimen', 'infusion_pump', {
      n_doses: nDoses,
      interval_h: interval,
      infusion_duration_h: this.infusionDurationH,
    });

    const schedSelect = document.getElementById('sampling-select');
    const sched = schedSelect?.value || '0,1,2,4,8,12,24';
    await api.applyAction(sId, 'set_sampling', 'sampling_schedule', { schedule: sched });

    const cmaxInp = document.getElementById('pred-cmax');
    const timeInp = document.getElementById('pred-time');
    const cmax = parseFloat(cmaxInp?.value || 10.0);
    const winT = parseFloat(timeInp?.value || 0.0);
    await api.applyAction(sId, 'predict_window', 'prediction_slate', {
      predicted_cmax: cmax,
      predicted_time_in_window_h: winT,
    });

    // Run simulation
    const simRes = await api.applyAction(sId, 'run_simulation', 'pkpd_chart_display', {});
    this.processSimulationResult(simRes);
  }

  processSimulationResult(actionResult) {
    const visuals = actionResult.visuals || [];
    const readout = visuals.find((v) => v.label === 'PK/PD RESULTS' || v.curve);

    if (readout && readout.curve) {
      this.lastCurve = readout.curve;
      this.lastEffectCurve = readout.effect_curve || [];
      if (readout.window) {
        this.targetWindow = {
          low: readout.window.low,
          high: readout.window.high,
          toxic: readout.window.high * 1.5,
        };
      }
    }

    // Extract metrics from readout value / unit or state
    let cmaxStr = '--';
    let aucStr = '--';
    if (readout?.value) {
      const match = String(readout.value).match(/Cmax:\s*([\d.]+)/i);
      if (match) cmaxStr = `${parseFloat(match[1]).toFixed(2)} mg/L`;
    }
    if (readout?.unit) {
      const match = String(readout.unit).match(/AUC:\s*([\d.]+)/i);
      if (match) aucStr = `${parseFloat(match[1]).toFixed(1)} mg·h/L`;
    }

    // Direct calculation from curve if needed
    if (this.lastCurve.length > 0) {
      const peak = Math.max(...this.lastCurve.map((p) => p.c));
      const peakPt = this.lastCurve.find((p) => p.c === peak);
      cmaxStr = `${peak.toFixed(2)} mg/L`;
      const tmaxStr = `${(peakPt?.t || 0).toFixed(1)} h`;

      // Update DOM Badges
      const elCmax = document.getElementById('dose-chart-cmax');
      const elTmax = document.getElementById('dose-chart-tmax');
      const elAuc = document.getElementById('dose-chart-auc');
      const elHalf = document.getElementById('dose-chart-halflife');
      const elWin = document.getElementById('dose-chart-window-time');
      const elStat = document.getElementById('dose-chart-status');

      if (elCmax) elCmax.textContent = cmaxStr;
      if (elTmax) elTmax.textContent = tmaxStr;
      if (elAuc) {
        if (aucStr !== '--') {
          elAuc.textContent = aucStr;
        } else {
          let trapezoid = 0;
          for (let i = 1; i < this.lastCurve.length; i++) {
            trapezoid += 0.5 * (this.lastCurve[i].c + this.lastCurve[i-1].c) * (this.lastCurve[i].t - this.lastCurve[i-1].t);
          }
          elAuc.textContent = `${trapezoid.toFixed(1)} mg·h/L`;
        }
      }
      if (elStat) {
        if (peak > this.targetWindow.toxic) {
          elStat.textContent = 'TOXICITY RISK';
          elStat.style.color = '#ef4444';
        } else if (peak >= this.targetWindow.low && peak <= this.targetWindow.high) {
          elStat.textContent = 'THERAPEUTIC';
          elStat.style.color = '#10b981';
        } else {
          elStat.textContent = 'SUBTHERAPEUTIC';
          elStat.style.color = '#f59e0b';
        }
      }
    }

    this.drawChart();
    if (actionResult.message) toast.showSuccess(actionResult.message);
  }

  drawChart() {
    if (!this.canvas || !this.ctx) return;
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;
    const padL = 42;
    const padR = 36;
    const padT = 20;
    const padB = 28;

    ctx.clearRect(0, 0, w, h);

    // Background
    ctx.fillStyle = '#090d16';
    ctx.fillRect(0, 0, w, h);

    // Coordinate scales
    const tMax = 24.0;
    let cMaxScale = Math.max(
      this.targetWindow.toxic * 1.15,
      ...this.lastCurve.map((p) => p.c),
      ...(this.comparisonCurve ? this.comparisonCurve.map((p) => p.c) : [0]),
      20.0
    );

    const toX = (t) => padL + (t / tMax) * (w - padL - padR);
    const toY = (c) => h - padB - (c / cMaxScale) * (h - padT - padB);

    // Target Window Band (Green / Teal shading)
    const yLow = toY(this.targetWindow.low);
    const yHigh = toY(this.targetWindow.high);
    ctx.fillStyle = 'rgba(20, 184, 166, 0.15)';
    ctx.fillRect(padL, yHigh, w - padL - padR, yLow - yHigh);

    ctx.strokeStyle = 'rgba(20, 184, 166, 0.5)';
    ctx.lineWidth = 1;
    ctx.strokeRect(padL, yHigh, w - padL - padR, yLow - yHigh);

    // Toxic Threshold Line (Red dashed)
    const yToxic = toY(this.targetWindow.toxic);
    ctx.strokeStyle = '#ef4444';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(padL, yToxic);
    ctx.lineTo(w - padR, yToxic);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = '#ef4444';
    ctx.font = '10px monospace';
    ctx.textAlign = 'right';
    ctx.fillText('TOXIC', w - padR - 4, yToxic - 3);

    // Axes & Grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padL, padT);
    ctx.lineTo(padL, h - padB);
    ctx.lineTo(w - padR, h - padB);
    ctx.stroke();

    // Ticks & Labels
    ctx.fillStyle = '#64748b';
    ctx.font = '10px monospace';
    ctx.textAlign = 'center';
    for (let t = 0; t <= 24; t += 6) {
      const x = toX(t);
      ctx.fillText(`${t}h`, x, h - padB + 14);
    }
    ctx.textAlign = 'right';
    for (let c = 0; c <= cMaxScale; c += Math.ceil(cMaxScale / 4)) {
      const y = toY(c);
      ctx.fillText(c.toFixed(0), padL - 6, y + 3);
    }

    // Comparison Curve (Amber / Purple dashed)
    if (this.comparisonCurve && this.comparisonCurve.length > 0) {
      ctx.strokeStyle = '#c084fc';
      ctx.lineWidth = 1.8;
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      this.comparisonCurve.forEach((pt, i) => {
        const x = toX(pt.t);
        const y = toY(pt.c);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Simulated Primary Concentration Curve (Cyan line)
    if (this.lastCurve.length > 0) {
      ctx.strokeStyle = '#38bdf8';
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      this.lastCurve.forEach((pt, i) => {
        const x = toX(pt.t);
        const y = toY(pt.c);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
    }

    // Secondary Y-axis: Effect Curve (Teal dotted)
    if (this.lastEffectCurve.length > 0) {
      const toYEff = (e) => h - padB - (e / 100.0) * (h - padT - padB);
      ctx.strokeStyle = '#34d399';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([2, 2]);
      ctx.beginPath();
      this.lastEffectCurve.forEach((pt, i) => {
        const x = toX(pt.t);
        const y = toYEff(pt.e);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.fillStyle = '#34d399';
      ctx.textAlign = 'left';
      ctx.fillText('100% E', w - padR + 4, padT + 10);
    }
  }

  open() {
    this.isOpen = true;
    if (this.panelEl) this.panelEl.classList.remove('hidden');
    this.drawChart();
  }

  close() {
    this.isOpen = false;
    if (this.panelEl) this.panelEl.classList.add('hidden');
  }

  toggle() {
    if (this.isOpen) this.close();
    else this.open();
  }
}
