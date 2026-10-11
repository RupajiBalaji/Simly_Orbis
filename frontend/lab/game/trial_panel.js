/**
 * Virtual Trial Control Panel & Analytics HUD (frontend/lab/game/trial_panel.js)
 * Manages the trial parameter sliders, execution calls, canvas charts (redrawn only
 * on data change), comparative regimen analysis, and crowd status counters.
 */

import { api } from '../api.js';
import { state } from '../state.js';
import { toast } from './toast.js';

export class TrialPanel {
  constructor(trialHallController, scene) {
    this.trialHall = trialHallController;
    this.scene = scene;
    this.isOpen = false;
    this.lastResult = null;
    this.isComparing = false;

    this.panelEl = document.getElementById('virtual-trial-panel');
    this.crowdHudEl = document.getElementById('trial-crowd-hud');
    this.compareModalEl = document.getElementById('trial-compare-modal');

    this.initDOM();
  }

  initDOM() {
    if (!this.panelEl) return;

    this.panelEl.innerHTML = `
      <div class="trial-panel-header">
        <div class="trial-title-wrap">
          <span class="trial-badge">💊 PHARMA.TRIAL</span>
          <h3>Virtual Clinical Trial</h3>
        </div>
        <button type="button" class="btn-close-trial" id="btn-close-trial" title="Exit viewing gallery">✕ Exit</button>
      </div>

      <div class="trial-disclaimer">
        Statistical simulation with simplified parameters. Educational only. Not clinical evidence.
      </div>

      <div class="trial-sliders-section">
        <div class="trial-slider-row">
          <div class="slider-label-wrap">
            <label for="trial-dose">Dose per administration</label>
            <span class="slider-val" id="trial-dose-val">500 mg</span>
          </div>
          <input type="range" id="trial-dose" min="100" max="2000" step="50" value="500" />
        </div>

        <div class="trial-slider-row">
          <div class="slider-label-wrap">
            <label for="trial-doses">Number of doses</label>
            <span class="slider-val" id="trial-doses-val">1 dose</span>
          </div>
          <input type="range" id="trial-doses" min="1" max="6" step="1" value="1" />
        </div>

        <div class="trial-slider-row">
          <div class="slider-label-wrap">
            <label for="trial-interval">Dosing interval</label>
            <span class="slider-val" id="trial-interval-val">6.0 h</span>
          </div>
          <input type="range" id="trial-interval" min="2" max="24" step="1" value="6" />
        </div>

        <div class="trial-slider-row">
          <div class="slider-label-wrap">
            <label for="trial-patients">Cohort size (Patients)</label>
            <span class="slider-val" id="trial-patients-val">500</span>
          </div>
          <input type="range" id="trial-patients" min="20" max="1000" step="20" value="500" />
        </div>

        <div class="trial-slider-row">
          <div class="slider-label-wrap">
            <label for="trial-liver">Impaired liver clearance</label>
            <span class="slider-val" id="trial-liver-val">10%</span>
          </div>
          <input type="range" id="trial-liver" min="0" max="50" step="5" value="10" />
        </div>
      </div>

      <div class="trial-actions-row">
        <button type="button" class="btn-primary trial-btn-run" id="btn-run-trial">⚡ Run Trial</button>
        <button type="button" class="btn-secondary trial-btn-compare" id="btn-compare-trial">⚖️ Compare vs Standard</button>
      </div>

      <!-- Live Results Area -->
      <div id="trial-results-area" class="trial-results-area hidden">
        <div class="trial-regimen-banner" id="trial-regimen-banner">
          Simulated Regimen: Paracetamol 500 mg × 1 dose (Cohort: 500 patients)
        </div>
        <div class="headline-stats-grid">
          <div class="headline-stat-cell stat-green">
            <span class="h-label">In Range (Efficacy)</span>
            <span class="h-val" id="stat-pct-in-range">0%</span>
          </div>
          <div class="headline-stat-cell stat-red">
            <span class="h-label">Toxicity Rate</span>
            <span class="h-val" id="stat-pct-toxic">0%</span>
          </div>
          <div class="headline-stat-cell stat-amber">
            <span class="h-label">Subtherapeutic</span>
            <span class="h-val" id="stat-pct-sub">0%</span>
          </div>
          <div class="headline-stat-cell stat-cyan">
            <span class="h-label">Mean Peak</span>
            <span class="h-val" id="stat-mean-peak">0.0 mg/L</span>
          </div>
        </div>

        <div class="trial-verdict-box" id="trial-verdict-text">
          Evaluating population exposure...
        </div>

        <!-- Canvas Visualizations -->
        <div class="trial-charts-wrap">
          <div class="trial-chart-box">
            <div class="chart-title">Percentile Concentration Bands (P5–P95)</div>
            <canvas id="trial-percentile-canvas" width="310" height="130"></canvas>
          </div>
          <div class="trial-chart-box">
            <div class="chart-title">Peak Concentration Distribution (Histogram)</div>
            <canvas id="trial-hist-canvas" width="310" height="100"></canvas>
          </div>
        </div>
      </div>
    `;

    // Crowd HUD overlay (Counters & Legend)
    if (this.crowdHudEl) {
      this.crowdHudEl.innerHTML = `
        <div class="crowd-hud-container">
          <div class="crowd-legend">
            <span class="legend-pill pill-green">● In range (≥60% in green zone)</span>
            <span class="legend-pill pill-amber">● Below range</span>
            <span class="legend-pill pill-red">● Above range (toxic)</span>
          </div>
          <div class="crowd-legend-desc">In range = concentration in the green zone for at least 60% of the dosing window.</div>
          <div class="crowd-regimen-badge" id="crowd-regimen-badge">Simulated Regimen: Paracetamol 500 mg × 1 dose</div>
          <div class="crowd-counters">
            <div class="counter-item">
              <span class="counter-num green-text" id="cnt-helped">0</span>
              <span class="counter-lbl">In range</span>
            </div>
            <div class="counter-item">
              <span class="counter-num amber-text" id="cnt-below">0</span>
              <span class="counter-lbl">Below range</span>
            </div>
            <div class="counter-item">
              <span class="counter-num red-text" id="cnt-toxic">0</span>
              <span class="counter-lbl">Above range (toxic)</span>
            </div>
            <div class="counter-item">
              <span class="counter-num total-text" id="cnt-total">500</span>
              <span class="counter-lbl">total cohort</span>
            </div>
          </div>
        </div>
      `;
    }

    // Compare Modal
    if (this.compareModalEl) {
      this.compareModalEl.innerHTML = `
        <div class="compare-modal-box">
          <div class="compare-header">
            <h3>⚖️ Clinical Regimen Comparative Analysis</h3>
            <button type="button" class="btn-close-modal" id="btn-close-compare">&times;</button>
          </div>
          <div id="compare-modal-content" class="compare-content"></div>
        </div>
      `;
      const btnCloseComp = document.getElementById('btn-close-compare');
      if (btnCloseComp) {
        btnCloseComp.onclick = () => this.hideCompareModal();
      }
    }

    this.bindEvents();
  }

  bindEvents() {
    // Sliders sync
    const setupSlider = (id, valId, unit, isFloat = false) => {
      const input = document.getElementById(id);
      const label = document.getElementById(valId);
      if (input && label) {
        input.oninput = () => {
          const v = isFloat ? parseFloat(input.value).toFixed(1) : input.value;
          label.textContent = `${v} ${unit}`.trim();
          if (id === 'trial-patients' && this.trialHall) {
            this.trialHall.setVisibleCount(parseInt(input.value, 10));
            const cntTotal = document.getElementById('cnt-total');
            if (cntTotal) cntTotal.textContent = input.value;
          }
        };
      }
    };

    setupSlider('trial-dose', 'trial-dose-val', 'mg');
    setupSlider('trial-doses', 'trial-doses-val', input => input === '1' ? 'dose' : 'doses');
    setupSlider('trial-interval', 'trial-interval-val', 'h', true);
    setupSlider('trial-patients', 'trial-patients-val', '');
    setupSlider('trial-liver', 'trial-liver-val', '%');

    // Action buttons
    const btnClose = document.getElementById('btn-close-trial');
    if (btnClose) btnClose.onclick = () => this.close();

    const btnRun = document.getElementById('btn-run-trial');
    if (btnRun) btnRun.onclick = () => this.runTrialSimulation();

    const btnCompare = document.getElementById('btn-compare-trial');
    if (btnCompare) btnCompare.onclick = () => this.runTrialComparison();
  }

  prefillCurrentRegimen() {
    // If patient was given a dose in current session, prefill it!
    const patientBed = state.session?.apparatus_state?.patient_bed;
    const doses = patientBed?.patient?.doses_administered || [];

    const doseInput = document.getElementById('trial-dose');
    const doseVal = document.getElementById('trial-dose-val');
    const dosesInput = document.getElementById('trial-doses');
    const dosesVal = document.getElementById('trial-doses-val');
    const intervalInput = document.getElementById('trial-interval');
    const intervalVal = document.getElementById('trial-interval-val');

    if (doses.length > 0 && doseInput && doseVal) {
      const lastDose = doses[doses.length - 1];
      const mg = Math.round(lastDose.dose_mg || 500);
      doseInput.value = mg;
      doseVal.textContent = `${mg} mg`;

      if (dosesInput && dosesVal) {
        const nD = Math.max(1, Math.min(6, doses.length > 1 ? doses.length : 4));
        dosesInput.value = nD;
        dosesVal.textContent = `${nD} ${nD === 1 ? 'dose' : 'doses'}`;
      }
    } else {
      // Default instructive mixed regimen within 3g daily: 500 mg x 4 doses q6h (2,000 mg/day)
      if (doseInput && doseVal) {
        doseInput.value = 500;
        doseVal.textContent = '500 mg';
      }
      if (dosesInput && dosesVal) {
        dosesInput.value = 4;
        dosesVal.textContent = '4 doses';
      }
      if (intervalInput && intervalVal) {
        intervalInput.value = 6;
        intervalVal.textContent = 'q6h';
      }
    }
  }

  open() {
    this.isOpen = true;
    this.prefillCurrentRegimen();

    // Auto-collapse HUD panels (checklist, event log, mentor) to keep viewing gallery unobstructed
    this.savedPanelStates = {
      checklist: document.getElementById('hud-protocol-panel')?.classList.contains('collapsed'),
      log: document.getElementById('hud-right-panel')?.classList.contains('collapsed'),
      mentor: window.drOrbisMentor?.isCollapsed ?? false,
    };
    window.labHUD?.setChecklistCollapsed(true);
    window.labHUD?.setLogCollapsed(true);
    window.drOrbisMentor?.setCollapsed(true);

    if (this.panelEl) this.panelEl.classList.remove('hidden');
    if (this.crowdHudEl) this.crowdHudEl.classList.remove('hidden');

    // Move camera to viewing gallery
    if (this.scene) {
      this.scene.setStationCamera('trial_gallery');
    }

    // Update screen display
    const screenObj = this.scene?.getApparatus('virtual_trial_screen');
    if (screenObj?.userData?.updateStatus) {
      screenObj.userData.updateStatus('VIEWING GALLERY ACTIVE');
    }
  }

  close() {
    this.isOpen = false;
    if (this.panelEl) this.panelEl.classList.add('hidden');
    if (this.crowdHudEl) this.crowdHudEl.classList.add('hidden');
    this.hideCompareModal();

    // Restore HUD panel states on exit
    if (this.savedPanelStates) {
      window.labHUD?.setChecklistCollapsed(this.savedPanelStates.checklist);
      window.labHUD?.setLogCollapsed(this.savedPanelStates.log);
      window.drOrbisMentor?.setCollapsed(this.savedPanelStates.mentor);
    }

    // Reset camera to default ward view
    if (this.scene) {
      this.scene.resetCameraView();
    }

    const screenObj = this.scene?.getApparatus('virtual_trial_screen');
    if (screenObj?.userData?.updateStatus) {
      screenObj.userData.updateStatus('READY FOR COHORT RUN');
    }
  }

  getFormParams() {
    const dose_mg = parseFloat(document.getElementById('trial-dose')?.value || 500);
    const n_doses = parseInt(document.getElementById('trial-doses')?.value || 1, 10);
    const interval_h = parseFloat(document.getElementById('trial-interval')?.value || 6.0);
    const n_patients = parseInt(document.getElementById('trial-patients')?.value || 500, 10);
    const pct_reduced_liver = parseFloat(document.getElementById('trial-liver')?.value || 10);

    return {
      drug_id: 'paracetamol',
      dose_mg,
      n_doses,
      interval_h,
      n_patients,
      seed: 42,
      pct_reduced_liver,
    };
  }

  async runTrialSimulation() {
    const btnRun = document.getElementById('btn-run-trial');
    if (btnRun) {
      btnRun.disabled = true;
      btnRun.textContent = 'Simulating...';
    }

    try {
      const params = this.getFormParams();
      const result = await api.runTrial(params);
      this.lastResult = result;
      state.lastTrialResult = result.summary; // Store for final lab report tie-in!

      const summary = result.summary;
      const series = result.series;

      // Unhide results area
      const resultsArea = document.getElementById('trial-results-area');
      if (resultsArea) resultsArea.classList.remove('hidden');

      // Update regimen banners
      const regDesc = `Simulated Regimen: Paracetamol ${params.dose_mg} mg × ${params.n_doses} dose(s) q${params.interval_h}h (Cohort: ${summary.n_patients} pts, ${params.pct_reduced_liver}% impaired liver)`;
      const regBanner = document.getElementById('trial-regimen-banner');
      if (regBanner) regBanner.textContent = regDesc;
      const crowdReg = document.getElementById('crowd-regimen-badge');
      if (crowdReg) crowdReg.textContent = `Simulated Regimen: Paracetamol ${params.dose_mg} mg × ${params.n_doses} dose(s) q${params.interval_h}h`;

      // Update headline numbers
      document.getElementById('stat-pct-in-range').textContent = `${summary.pct_in_range}%`;
      document.getElementById('stat-pct-toxic').textContent = `${summary.pct_toxic}%`;
      document.getElementById('stat-pct-sub').textContent = `${summary.pct_subtherapeutic}%`;
      document.getElementById('stat-mean-peak').textContent = `${summary.mean_peak} mg/L`;

      // Plain-code insight generated from the data (no AI)
      const verdictEl = document.getElementById('trial-verdict-text');
      if (verdictEl) {
        let insight = '';
        if (summary.median_peak < summary.green_low) {
          insight = `Median peak ${summary.median_peak.toFixed(1)} mg/L is below the ${summary.green_low.toFixed(1)} mg/L therapeutic minimum, so one ${params.dose_mg} mg dose is too low for most patients.`;
          verdictEl.style.borderColor = '#f59e0b';
          verdictEl.style.color = '#fde68a';
        } else if (summary.pct_toxic > 5.0) {
          insight = `Median peak ${summary.median_peak.toFixed(1)} mg/L exceeds the ${summary.red_threshold.toFixed(1)} mg/L safety ceiling, causing ${summary.pct_toxic}% toxic exposure across the cohort.`;
          verdictEl.style.borderColor = '#ef4444';
          verdictEl.style.color = '#fca5a5';
        } else {
          insight = `Median peak ${summary.median_peak.toFixed(1)} mg/L maintains safe therapeutic coverage (green window) for ${summary.pct_in_range}% of virtual patients with 0% toxicity.`;
          verdictEl.style.borderColor = '#10b981';
          verdictEl.style.color = '#6ee7b7';
        }
        verdictEl.textContent = insight;
      }

      // Redraw canvas charts
      this.drawPercentileChart(series.time_h, series, summary);
      this.drawHistogram(series.hist_bins, series.hist_counts, summary);

      // Trigger 3D InstancedMesh color wave!
      if (this.trialHall && series.outcomes) {
        const cntHelped = document.getElementById('cnt-helped');
        const cntBelow = document.getElementById('cnt-below');
        const cntToxic = document.getElementById('cnt-toxic');
        const cntTotal = document.getElementById('cnt-total');

        if (cntTotal) cntTotal.textContent = summary.n_patients;

        this.trialHall.startWave(
          series.outcomes,
          state.skipAnimation,
          (progressData) => {
            if (cntHelped) cntHelped.textContent = progressData.helped;
            if (cntBelow) cntBelow.textContent = progressData.below;
            if (cntToxic) cntToxic.textContent = progressData.toxic;
          },
          (finalData) => {
            if (cntHelped) cntHelped.textContent = finalData.helped;
            if (cntBelow) cntBelow.textContent = finalData.below;
            if (cntToxic) cntToxic.textContent = finalData.toxic;
          }
        );
      }

      // Update Virtual Trial Wall Screen with real result counts and colored matrix
      const screenObj = this.scene?.getApparatus('virtual_trial_screen');
      if (screenObj?.userData?.updateResults) {
        screenObj.userData.updateResults(summary, series.outcomes);
      }

      toast.showSuccess(`Trial completed across ${summary.n_patients} virtual patients!`);
    } catch (err) {
      console.error('Trial execution error:', err);
      toast.showError(`Trial execution failed: ${err.message}`);
    } finally {
      if (btnRun) {
        btnRun.disabled = false;
        btnRun.textContent = '⚡ Run Trial';
      }
    }
  }

  async runTrialComparison() {
    const btnComp = document.getElementById('btn-compare-trial');
    if (btnComp) {
      btnComp.disabled = true;
      btnComp.textContent = 'Comparing...';
    }

    try {
      const regA = this.getFormParams();
      const compRes = await api.compareTrial(regA);

      this.showCompareModal(compRes);
    } catch (err) {
      console.error('Compare execution error:', err);
      toast.showError(`Comparison failed: ${err.message}`);
    } finally {
      if (btnComp) {
        btnComp.disabled = false;
        btnComp.textContent = '⚖️ Compare vs Standard';
      }
    }
  }

  showCompareModal(compData) {
    if (!this.compareModalEl) return;
    const content = document.getElementById('compare-modal-content');
    if (!content) return;

    const tA = compData.trial_a.summary;
    const tB = compData.trial_b.summary;
    const cmp = compData.comparison;

    const diffInSign = cmp.diff_pct_in_range > 0 ? '+' : '';
    const diffToxSign = cmp.diff_pct_toxic > 0 ? '+' : '';
    const diffHelpedSign = cmp.diff_helped_patients > 0 ? '+' : '';

    content.innerHTML = `
      <div class="compare-verdict-banner">
        <strong>Verdict:</strong> ${cmp.verdict}
      </div>

      <div class="compare-columns-grid">
        <div class="compare-col col-a">
          <h4>Regimen A (Your Dose: ${tA.n_patients} pts)</h4>
          <div class="comp-row"><span>Dose Settings:</span><strong>${compData.trial_a.params.dose_mg} mg × ${compData.trial_a.params.n_doses}</strong></div>
          <div class="comp-row"><span>In Therapeutic Range:</span><strong class="green-text">${tA.pct_in_range}%</strong></div>
          <div class="comp-row"><span>Cohort Toxicity:</span><strong class="red-text">${tA.pct_toxic}%</strong></div>
          <div class="comp-row"><span>Subtherapeutic:</span><strong class="amber-text">${tA.pct_subtherapeutic}%</strong></div>
          <div class="comp-row"><span>Mean Peak Cmax:</span><strong>${tA.mean_peak} mg/L</strong></div>
          <div class="comp-row"><span>In-Range Patients:</span><strong>${tA.group_counts.in_range} pts</strong></div>

          <!-- Distribution Bar -->
          <div style="margin: 12px 0 6px;">
            <div style="display:flex; justify-content:space-between; font-size:0.72rem; color:#94a3b8; margin-bottom:4px;">
              <span>Outcome Distribution</span>
              <span>${tA.pct_in_range}% in / ${tA.pct_subtherapeutic}% sub / ${tA.pct_toxic}% tox</span>
            </div>
            <div style="height:14px; display:flex; border-radius:4px; overflow:hidden; background:#1e293b;">
              <div style="width:${tA.pct_in_range}%; background:#10b981;" title="In Range ${tA.pct_in_range}%"></div>
              <div style="width:${tA.pct_subtherapeutic}%; background:#f59e0b;" title="Subtherapeutic ${tA.pct_subtherapeutic}%"></div>
              <div style="width:${tA.pct_toxic}%; background:#ef4444;" title="Toxic ${tA.pct_toxic}%"></div>
            </div>
          </div>
          <button type="button" class="btn-wave-action" id="btn-wave-a" style="width:100%; padding:7px 12px; margin-top:8px; border-radius:6px; background:rgba(16,185,129,0.2); border:1px solid #10b981; color:#6ee7b7; font-size:0.8rem; font-weight:700; cursor:pointer;">
            🌊 View Regimen A Crowd Wave
          </button>
        </div>

        <div class="compare-col col-b">
          <h4>Regimen B (Standard 500 mg Single)</h4>
          <div class="comp-row"><span>Dose Settings:</span><strong>500 mg × 1</strong></div>
          <div class="comp-row"><span>In Therapeutic Range:</span><strong class="green-text">${tB.pct_in_range}%</strong></div>
          <div class="comp-row"><span>Cohort Toxicity:</span><strong class="red-text">${tB.pct_toxic}%</strong></div>
          <div class="comp-row"><span>Subtherapeutic:</span><strong class="amber-text">${tB.pct_subtherapeutic}%</strong></div>
          <div class="comp-row"><span>Mean Peak Cmax:</span><strong>${tB.mean_peak} mg/L</strong></div>
          <div class="comp-row"><span>In-Range Patients:</span><strong>${tB.group_counts.in_range} pts</strong></div>

          <!-- Distribution Bar -->
          <div style="margin: 12px 0 6px;">
            <div style="display:flex; justify-content:space-between; font-size:0.72rem; color:#94a3b8; margin-bottom:4px;">
              <span>Outcome Distribution</span>
              <span>${tB.pct_in_range}% in / ${tB.pct_subtherapeutic}% sub / ${tB.pct_toxic}% tox</span>
            </div>
            <div style="height:14px; display:flex; border-radius:4px; overflow:hidden; background:#1e293b;">
              <div style="width:${tB.pct_in_range}%; background:#10b981;" title="In Range ${tB.pct_in_range}%"></div>
              <div style="width:${tB.pct_subtherapeutic}%; background:#f59e0b;" title="Subtherapeutic ${tB.pct_subtherapeutic}%"></div>
              <div style="width:${tB.pct_toxic}%; background:#ef4444;" title="Toxic ${tB.pct_toxic}%"></div>
            </div>
          </div>
          <button type="button" class="btn-wave-action" id="btn-wave-b" style="width:100%; padding:7px 12px; margin-top:8px; border-radius:6px; background:rgba(56,189,248,0.2); border:1px solid #38bdf8; color:#7dd3fc; font-size:0.8rem; font-weight:700; cursor:pointer;">
            🌊 View Standard Regimen Wave
          </button>
        </div>
      </div>

      <div class="compare-deltas-bar">
        <div class="delta-cell">
          <span class="d-label">Δ In-Range Efficacy</span>
          <span class="d-val ${cmp.diff_pct_in_range >= 0 ? 'green-text' : 'red-text'}">${diffInSign}${cmp.diff_pct_in_range}%</span>
        </div>
        <div class="delta-cell">
          <span class="d-label">Δ Toxicity Risk</span>
          <span class="d-val ${cmp.diff_pct_toxic <= 0 ? 'green-text' : 'red-text'}">${diffToxSign}${cmp.diff_pct_toxic}%</span>
        </div>
        <div class="delta-cell">
          <span class="d-label">Δ Net In-Range Patients</span>
          <span class="d-val ${cmp.diff_helped_patients >= 0 ? 'green-text' : 'red-text'}">${diffHelpedSign}${cmp.diff_helped_patients}</span>
        </div>
        <div class="delta-cell">
          <span class="d-label">Δ Toxic Patients</span>
          <span class="d-val ${cmp.diff_toxic_patients <= 0 ? 'green-text' : 'red-text'}">${cmp.diff_toxic_patients > 0 ? '+' : ''}${cmp.diff_toxic_patients}</span>
        </div>
      </div>
    `;

    document.getElementById('btn-wave-a')?.addEventListener('click', () => {
      if (this.trialHall && compData.trial_a?.series?.outcomes) {
        this.trialHall.startWave(
          compData.trial_a.series.outcomes,
          false,
          (p) => {
            const cntH = document.getElementById('cnt-helped');
            const cntB = document.getElementById('cnt-below');
            const cntT = document.getElementById('cnt-toxic');
            if (cntH) cntH.textContent = p.helped;
            if (cntB) cntB.textContent = p.below;
            if (cntT) cntT.textContent = p.toxic;
          }
        );
        toast.showInfo('Displaying Regimen A cohort wave across gallery crowd.');
      }
    });

    document.getElementById('btn-wave-b')?.addEventListener('click', () => {
      if (this.trialHall && compData.trial_b?.series?.outcomes) {
        this.trialHall.startWave(
          compData.trial_b.series.outcomes,
          false,
          (p) => {
            const cntH = document.getElementById('cnt-helped');
            const cntB = document.getElementById('cnt-below');
            const cntT = document.getElementById('cnt-toxic');
            if (cntH) cntH.textContent = p.helped;
            if (cntB) cntB.textContent = p.below;
            if (cntT) cntT.textContent = p.toxic;
          }
        );
        toast.showInfo('Displaying Standard Regimen B cohort wave across gallery crowd.');
      }
    });

    this.compareModalEl.classList.remove('hidden');
  }

  hideCompareModal() {
    if (this.compareModalEl) this.compareModalEl.classList.add('hidden');
  }

  drawPercentileChart(times, series, summary) {
    const canvas = document.getElementById('trial-percentile-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#0a0d18';
    ctx.fillRect(0, 0, w, h);

    const padLeft = 32;
    const padRight = 10;
    const padTop = 12;
    const padBottom = 22;
    const chartW = w - padLeft - padRight;
    const chartH = h - padTop - padBottom;

    const maxConc = Math.max(35.0, Math.max(...series.p95) * 1.15);

    const xMap = (t) => padLeft + (t / 24.0) * chartW;
    const yMap = (c) => padTop + chartH - (c / maxConc) * chartH;

    // Green therapeutic zone (10 to 20 mg/L)
    const yGreenLow = yMap(summary.green_low);
    const yGreenHigh = yMap(summary.green_high);
    ctx.fillStyle = 'rgba(16, 185, 129, 0.15)';
    ctx.fillRect(padLeft, yGreenHigh, chartW, yGreenLow - yGreenHigh);

    // Red toxic threshold line (30 mg/L)
    const yRed = yMap(summary.red_threshold);
    ctx.strokeStyle = '#ef4444';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(padLeft, yRed);
    ctx.lineTo(padLeft + chartW, yRed);
    ctx.stroke();
    ctx.setLineDash([]);

    // P5–P95 Outer shaded band (light purple)
    ctx.fillStyle = 'rgba(168, 85, 247, 0.12)';
    ctx.beginPath();
    for (let i = 0; i < times.length; i++) {
      const x = xMap(times[i]);
      const y = yMap(series.p95[i]);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    for (let i = times.length - 1; i >= 0; i--) {
      const x = xMap(times[i]);
      const y = yMap(series.p5[i]);
      ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fill();

    // P25–P75 Inner shaded band (medium purple)
    ctx.fillStyle = 'rgba(168, 85, 247, 0.28)';
    ctx.beginPath();
    for (let i = 0; i < times.length; i++) {
      const x = xMap(times[i]);
      const y = yMap(series.p75[i]);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    for (let i = times.length - 1; i >= 0; i--) {
      const x = xMap(times[i]);
      const y = yMap(series.p25[i]);
      ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fill();

    // P50 Median Line (solid cyan/purple)
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let i = 0; i < times.length; i++) {
      const x = xMap(times[i]);
      const y = yMap(series.p50[i]);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Axes & Labels
    ctx.fillStyle = '#64748b';
    ctx.font = '9px monospace';
    ctx.fillText('0h', padLeft, h - 6);
    ctx.fillText('12h', padLeft + chartW / 2 - 8, h - 6);
    ctx.fillText('24h', padLeft + chartW - 16, h - 6);

    ctx.fillText('0', 6, padTop + chartH);
    ctx.fillText('20', 6, yGreenHigh + 3);
    ctx.fillText('30', 6, yRed + 3);
  }

  drawHistogram(binEdges, counts, summary) {
    const canvas = document.getElementById('trial-hist-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#0a0d18';
    ctx.fillRect(0, 0, w, h);

    const padLeft = 32;
    const padRight = 10;
    const padTop = 10;
    const padBottom = 20;
    const chartW = w - padLeft - padRight;
    const chartH = h - padTop - padBottom;

    const maxCount = Math.max(1, Math.max(...counts));
    const nBins = counts.length;
    const barW = chartW / nBins;

    for (let i = 0; i < nBins; i++) {
      const c = counts[i];
      const barH = (c / maxCount) * chartH;
      const x = padLeft + i * barW;
      const y = padTop + chartH - barH;

      const binMid = (binEdges[i] + binEdges[i + 1]) / 2;
      const isToxic = binMid > summary.red_threshold;

      ctx.fillStyle = isToxic ? '#ef4444' : '#10b981';
      ctx.fillRect(x + 1, y, Math.max(1, barW - 2), barH);
    }

    // Baseline
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padLeft, padTop + chartH);
    ctx.lineTo(padLeft + chartW, padTop + chartH);
    ctx.stroke();

    // Labels
    ctx.fillStyle = '#64748b';
    ctx.font = '9px monospace';
    ctx.fillText('0 mg/L', padLeft, h - 6);
    ctx.fillText(`${binEdges[binEdges.length - 1].toFixed(0)} mg/L`, padLeft + chartW - 38, h - 6);
    ctx.fillText(`max: ${maxCount}`, 4, padTop + 8);
  }
}
