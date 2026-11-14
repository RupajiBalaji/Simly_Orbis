/**
 * Director Mode & Mistake Demonstration (frontend/lab/demo/director.js)
 * Scripted automated playthrough for hands-free live presentations.
 */

import { api } from '../api.js';
import { state } from '../state.js';
import { toast } from '../game/toast.js';

export class DirectorRunner {
  constructor(actionMenu) {
    this.actionMenu = actionMenu;
    this.isRunning = false;
    this.banner = document.getElementById('director-banner');

    window.addEventListener('keydown', (e) => {
      const tag = e.target?.tagName?.toUpperCase();
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || e.target?.isContentEditable) {
        return;
      }
      if ((e.key === 'd' || e.key === 'D') && e.shiftKey) {
        this.toggleDirectorMode();
      }
    });
  }

  toggleDirectorMode() {
    this.isRunning = !this.isRunning;
    if (this.banner) {
      if (this.isRunning) this.banner.classList.add('active');
      else this.banner.classList.remove('active');
    }

    if (this.isRunning) {
      toast.showInfo('Director Mode Active: Running automated demonstration...', 3000);
      this.runAutomatedScript();
    } else {
      toast.showInfo('Director Mode Deactivated', 2000);
    }
  }

  async runAutomatedScript() {
    if (!state.session?.session_id || !this.isRunning) return;

    const expId = state.session.experiment_id;

    if (expId === 'pk_ward') {
      await this.runPKWardScript();
    } else if (expId === 'titration_bench') {
      await this.runTitrationScript();
    } else if (expId === 'launch_bench') {
      await this.runLaunchBenchScript();
    } else if (expId === 'dose_lab') {
      await this.runDoseLabScript();
    }
  }

  async runDoseLabScript() {
    const steps = [
      { action: 'select_patient', target: 'preset_standard_70kg', params: {} },
      { action: 'check_renal', target: 'patient_monitor', params: {} },
      { action: 'select_drug', target: 'infusion_pump', params: { drug_id: 'theophylline' } },
      { action: 'set_route', target: 'infusion_pump', params: { route: 'oral' } },
      { action: 'set_dose', target: 'infusion_pump', params: { dose_mg: 300.0 } },
      { action: 'set_regimen', target: 'infusion_pump', params: { n_doses: 1, interval_h: 8.0 } },
      { action: 'set_sampling', target: 'sampling_schedule', params: { schedule: '0,1,2,4,8,12,24' } },
      { action: 'predict_window', target: 'prediction_slate', params: { predicted_cmax: 8.5, predicted_time_in_window_h: 0.0 } },
      { action: 'run_simulation', target: 'pkpd_chart_display', params: {} },
      { action: 'compare_regimens', target: 'pkpd_chart_display', params: {} },
      { action: 'set_covariates', target: 'patient_monitor', params: { weight_kg: 70.0, age_yr: 72.0, crcl_ml_min: 30.0 } },
      { action: 'check_renal', target: 'patient_monitor', params: {} },
      { action: 'set_dose', target: 'infusion_pump', params: { dose_mg: 150.0 } },
      { action: 'run_simulation', target: 'pkpd_chart_display', params: {} },
      { action: 'debrief_pkpd', target: 'debrief_station', params: {} },
    ];

    const stepDelay = this.stepDelay ?? (state.skipAnimation ? 350 : 1200);
    for (const step of steps) {
      if (!this.isRunning) break;
      await this.actionMenu.executeAction(step.action, step.target, step.params);
      await this.sleep(stepDelay);
    }

    if (this.isRunning) {
      toast.showInfo('Director Mode: Submitting final pharmacometric report...', 2000);
      const res = await api.finishSession(state.session.session_id);
      window.reportScreen.show(res);
      this.toggleDirectorMode();
    }
  }

  async runLaunchBenchScript() {
    const steps = [
      { action: 'choose_rocket', target: 'orbis_1', params: {} },
      { action: 'declare_payload', target: 'comm_sat_500kg', params: { payload_kg: 500.0 } },
      { action: 'fuel_rocket', target: 'nominal_fuel', params: {} },
      { action: 'run_checklist', target: 'flight_computer', params: {} },
      { action: 'clear_range', target: 'range_control', params: {} },
      { action: 'launch', target: 'pad_39a', params: { target_alt_km: 200.0 } },
      { action: 'coast', target: 'parking_orbit', params: {} },
      { action: 'burn_transfer', target: 'hohmann_geo', params: {} },
      { action: 'circularize', target: 'circularize_geo', params: {} },
      { action: 'debrief', target: 'tracking_station', params: {} },
    ];

    const stepDelay = this.stepDelay ?? (state.skipAnimation ? 350 : 1200);
    for (const step of steps) {
      if (!this.isRunning) break;
      await this.actionMenu.executeAction(step.action, step.target, step.params);
      await this.sleep(stepDelay);
    }

    if (this.isRunning) {
      toast.showInfo('Director Mode: Submitting final space mission report...', 2000);
      const res = await api.finishSession(state.session.session_id);
      window.reportScreen.show(res);
      this.toggleDirectorMode();
    }
  }

  async runPKWardScript() {
    const steps = [
      { action: 'wear_ppe', target: 'avatar', params: { item: 'goggles' } },
      { action: 'wear_ppe', target: 'avatar', params: { item: 'gloves' } },
      { action: 'wear_ppe', target: 'avatar', params: { item: 'coat' } },
      { action: 'tare_balance', target: 'digital_balance', params: {} },
      { action: 'weigh', target: 'digital_balance', params: { amount_g: 0.5, substance: 'paracetamol' } },
      { action: 'dissolve', target: 'dosing_cup', params: { substance: 'paracetamol', solvent: 'water' } },
      { action: 'label', target: 'dosing_cup', params: { text: 'Pt: Alex | 500mg' } },
      { action: 'administer_oral', target: 'patient_bed', params: {} },
      { action: 'advance_time', target: 'ward_clock', params: { hours: 1.0 } },
      { action: 'label', target: 'tube_1', params: { text: 't=1.0h' } },
      { action: 'draw_blood', target: 'tube_1', params: {} },
      { action: 'run_assay', target: 'tube_1', params: {} },
      { action: 'advance_time', target: 'ward_clock', params: { hours: 2.0 } },
      { action: 'label', target: 'tube_2', params: { text: 't=3.0h' } },
      { action: 'draw_blood', target: 'tube_2', params: {} },
      { action: 'run_assay', target: 'tube_2', params: {} },
      { action: 'dispose_waste', target: 'chemical_waste_bin', params: { item: 'dosing_cup' } },
      { action: 'wash_hands', target: 'sink', params: {} },
    ];

    const stepDelay = this.stepDelay ?? (state.skipAnimation ? 350 : 1200);
    for (const step of steps) {
      if (!this.isRunning) break;
      await this.actionMenu.executeAction(step.action, step.target, step.params);
      await this.sleep(stepDelay);
    }

    if (this.isRunning) {
      toast.showInfo('Director Mode: Submitting final clinical report...', 2000);
      const res = await api.finishSession(state.session.session_id);
      window.reportScreen.show(res);
      this.toggleDirectorMode();
    }
  }

  async runTitrationScript() {
    const steps = [
      { action: 'wear_ppe', target: 'avatar', params: { item: 'goggles' } },
      { action: 'wear_ppe', target: 'avatar', params: { item: 'gloves' } },
      { action: 'wear_ppe', target: 'avatar', params: { item: 'coat' } },
      { action: 'rinse_burette', target: 'burette', params: { solvent: 'naoh' } },
      { action: 'fill_burette', target: 'burette', params: { titrant: 'naoh', volume_ml: 50.0 } },
      { action: 'pipette_analyte', target: 'conical_flask', params: { analyte: 'hcl', volume_ml: 25.0 } },
      { action: 'add_indicator', target: 'conical_flask', params: { indicator: 'phenolphthalein', drops: 3 } },
      { action: 'read_ph_meter', target: 'ph_meter', params: {} },
      { action: 'titrate', target: 'burette', params: { volume_ml: 20.0 } },
      { action: 'swirl', target: 'conical_flask', params: {} },
      { action: 'titrate', target: 'burette', params: { volume_ml: 4.5 } },
      { action: 'swirl', target: 'conical_flask', params: {} },
      { action: 'titrate', target: 'burette', params: { volume_ml: 0.5 } }, // endpoint reached!
      { action: 'swirl', target: 'conical_flask', params: {} },
      { action: 'read_ph_meter', target: 'ph_meter', params: {} },
      { action: 'record_endpoint', target: 'conical_flask', params: { volume_ml: 25.0 } },
      { action: 'dispose_waste', target: 'chemical_waste_bin', params: { item: 'conical_flask' } },
      { action: 'wash_hands', target: 'sink', params: {} },
    ];

    const stepDelay = this.stepDelay ?? (state.skipAnimation ? 350 : 1200);
    for (const step of steps) {
      if (!this.isRunning) break;
      await this.actionMenu.executeAction(step.action, step.target, step.params);
      await this.sleep(stepDelay);
    }

    if (this.isRunning) {
      toast.showInfo('Director Mode: Submitting final chemistry report...', 2000);
      const res = await api.finishSession(state.session.session_id);
      window.reportScreen.show(res);
      this.toggleDirectorMode();
    }
  }

  async runMistakeDemo() {
    const expId = state.session?.experiment_id;
    if (expId === 'dose_lab') {
      toast.showInfo('Mistake Demo: Giving unadjusted gentamicin dose to renal impairment patient (Rule D2)...', 3500);
      await this.actionMenu.executeAction('set_covariates', 'patient_monitor', { weight_kg: 70.0, age_yr: 70.0, crcl_ml_min: 30.0 });
      await this.actionMenu.executeAction('select_drug', 'infusion_pump', { drug_id: 'gentamicin' });
      await this.actionMenu.executeAction('set_route', 'infusion_pump', { route: 'iv_bolus' });
      await this.actionMenu.executeAction('set_dose', 'infusion_pump', { dose_mg: 300.0 });
    } else if (expId === 'launch_bench') {
      toast.showInfo('Mistake Demo: Attempting launch without preflight checklist or range clearance (Rules S1 & S6)...', 3500);
      await this.actionMenu.executeAction('choose_rocket', 'orbis_1', {});
      await this.actionMenu.executeAction('launch', 'pad_39a', {});
    } else if (expId === 'pk_ward') {
      toast.showInfo('Mistake Demo: Intentionally handling chemicals without goggles (violating Rule R1)...', 3500);
      await this.actionMenu.executeAction('weigh', 'digital_balance', { amount_g: 0.5, substance: 'paracetamol' });
    } else {
      toast.showInfo('Mistake Demo: Intentionally handling chemicals without goggles (violating Rule R1)...', 3500);
      await this.actionMenu.executeAction('pipette_analyte', 'conical_flask', { analyte: 'hcl', volume_ml: 25.0 });
    }
  }

  sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
