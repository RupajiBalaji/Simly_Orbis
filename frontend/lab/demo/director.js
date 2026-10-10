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
      if (e.key === 'd' || e.key === 'D') {
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

    for (const step of steps) {
      if (!this.isRunning) break;
      await this.actionMenu.executeAction(step.action, step.target, step.params);
      await this.sleep(1200);
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

    for (const step of steps) {
      if (!this.isRunning) break;
      await this.actionMenu.executeAction(step.action, step.target, step.params);
      await this.sleep(1200);
    }

    if (this.isRunning) {
      toast.showInfo('Director Mode: Submitting final chemistry report...', 2000);
      const res = await api.finishSession(state.session.session_id);
      window.reportScreen.show(res);
      this.toggleDirectorMode();
    }
  }

  async runMistakeDemo() {
    toast.showInfo('Mistake Demo: Intentionally handling chemicals without goggles (violating Rule R1)...', 3500);

    // Skip PPE and directly tare/weigh or pipette analyte
    const expId = state.session?.experiment_id;
    if (expId === 'pk_ward') {
      await this.actionMenu.executeAction('weigh', 'digital_balance', { amount_g: 0.5, substance: 'paracetamol' });
    } else {
      await this.actionMenu.executeAction('pipette_analyte', 'conical_flask', { analyte: 'hcl', volume_ml: 25.0 });
    }
  }

  sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
