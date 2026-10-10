/**
 * Context-Aware Action Menu & Always-Visible Action Bar (frontend/lab/game/action_menu.js)
 * Implements persistent action bar grouped by station/category, station navigation strip,
 * next step protocol guidance, and parameter modals.
 */

import * as THREE from 'three';
import { api } from '../api.js';
import { state } from '../state.js';
import { toast } from './toast.js';

export class ActionMenu {
  constructor(directiveQueue, characterController) {
    this.directiveQueue = directiveQueue;
    this.characterController = characterController;
    this.container = document.getElementById('action-quick-buttons');
    this.groupsContainer = document.getElementById('action-groups-container');
    this.stationStrip = document.getElementById('station-strip-buttons');
    this.paramModal = document.getElementById('action-param-modal');
    this.nextStepInstruction = document.getElementById('next-step-instruction');
    this.nextStepHint = document.getElementById('next-step-hint');
    this.targetNameEl = document.getElementById('selected-target-name');

    // Compact action bar & drawer elements
    this.stationActionsList = document.getElementById('station-actions-list');
    this.moreActionsDrawer = document.getElementById('more-actions-drawer');
    this.btnToggleMore = document.getElementById('btn-toggle-more-actions');
    this.moreIndicator = document.getElementById('more-actions-indicator');

    if (this.btnToggleMore && this.moreActionsDrawer) {
      this.btnToggleMore.onclick = () => {
        this.moreActionsDrawer.classList.toggle('hidden');
        const isOpen = !this.moreActionsDrawer.classList.contains('hidden');
        if (this.moreIndicator) {
          this.moreIndicator.textContent = isOpen ? '▲' : '▾';
        }
      };
    }

    // Subscribe to state updates
    state.subscribe((event, payload) => {
      if (event === 'actions_updated' || event === 'target_selected') {
        this.renderActions();
      } else if (event === 'session_updated') {
        this.renderActions();
        this.updateNextStepBanner();
      } else if (event === 'experiment_updated') {
        this.renderStationStrip(payload);
        this.updateNextStepBanner();
      } else if (event === 'pending_changed') {
        this.updatePendingState(payload);
      }
    });
  }

  updatePendingState(isPending) {
    const spinner = document.getElementById('action-spinner');
    if (spinner) {
      if (isPending) spinner.classList.add('active');
      else spinner.classList.remove('active');
    }

    const allActionBtns = document.querySelectorAll('.action-btn');
    allActionBtns.forEach((b) => {
      if (isPending) {
        b.disabled = true;
      } else {
        b.disabled = b.dataset.backendDisabled === 'true';
      }
    });
  }

  renderStationStrip(experiment) {
    if (!this.stationStrip) return;
    this.stationStrip.innerHTML = '';

    const expId = experiment?.id || state.experiment?.id || 'pk_ward';
    let stations = [];

    if (expId === 'pk_ward') {
      stations = [
        { id: 'digital_balance', label: '⚖️ Balance & Prep', pos: new THREE.Vector3(-3.8, 0, -3.2), face: new THREE.Vector3(-4.5, 0.94, -4.2) },
        { id: 'patient_bed', label: '🛏️ Patient Alex', pos: new THREE.Vector3(3.2, 0, -3.5), face: new THREE.Vector3(4.5, 0.94, -3.8) },
        { id: 'tube_rack', label: '🧪 Blood Samples', pos: new THREE.Vector3(-3.2, 0, -3.2), face: new THREE.Vector3(-3.0, 0.94, -4.3) },
        { id: 'assay_analyzer', label: '🔬 Centrifuge Assay', pos: new THREE.Vector3(-5.2, 0, -2.6), face: new THREE.Vector3(-5.5, 0.94, -3.5) },
        { id: 'virtual_trial_screen', label: '👥 Virtual Trial', pos: new THREE.Vector3(3.6, 0, -5.2), face: new THREE.Vector3(4.5, 2.6, -6.9), isTrial: true },
        { id: 'sink', label: '🚰 Utility Sink', pos: new THREE.Vector3(-6.2, 0, -1.0), face: new THREE.Vector3(-7.2, 0.94, -1.0) },
        { id: 'chemical_waste_bin', label: '🗑️ Waste Disposal', pos: new THREE.Vector3(2.0, 0, -4.2), face: new THREE.Vector3(2.0, 0, -5.2) },
      ];
    } else {
      stations = [
        { id: 'burette', label: '🧪 Burette Stand', pos: new THREE.Vector3(0, 0, -1.0), face: new THREE.Vector3(0, 0.94, -2.0) },
        { id: 'conical_flask', label: '⚗️ Conical Flask', pos: new THREE.Vector3(0, 0, -1.0), face: new THREE.Vector3(0, 0.94, -1.9) },
        { id: 'pipette', label: '🧴 Reagents & Pipette', pos: new THREE.Vector3(-0.8, 0, -1.0), face: new THREE.Vector3(-1.0, 0.94, -1.8) },
        { id: 'indicator_bottles', label: '💧 pH Indicators', pos: new THREE.Vector3(0.8, 0, -1.2), face: new THREE.Vector3(1.1, 0.94, -2.2) },
        { id: 'ph_meter', label: '⚡ Digital pH Meter', pos: new THREE.Vector3(-0.5, 0, -1.2), face: new THREE.Vector3(-0.8, 0.94, -2.3) },
        { id: 'sink', label: '🚰 Utility Sink', pos: new THREE.Vector3(-6.2, 0, -1.0), face: new THREE.Vector3(-7.2, 0.94, -1.0) },
        { id: 'chemical_waste_bin', label: '🗑️ Waste Disposal', pos: new THREE.Vector3(2.0, 0, -4.2), face: new THREE.Vector3(2.0, 0, -5.2) },
      ];
    }

    stations.forEach((st) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'station-pill-btn';
      btn.textContent = st.label;
      btn.dataset.stationId = st.id;

      if (state.selectedTargetId === st.id) {
        btn.classList.add('active');
      }

      btn.onclick = () => {
        // Update active class
        this.stationStrip.querySelectorAll('.station-pill-btn').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');

        // Move character and focus camera
        if (this.characterController) {
          this.characterController.moveTo(st.pos, () => {
            this.characterController.faceTarget(st.face);
          });
        }
        if (this.directiveQueue?.scene) {
          this.directiveQueue.scene.focusOnStation(st.id);
        }

        if (st.isTrial) {
          state.emit('open_trial_panel');
        }

        state.setSelectedTarget(st.id);
      };

      this.stationStrip.appendChild(btn);
    });
  }

  updateNextStepBanner() {
    const protocol = state.experiment?.protocol || [];
    const completed = new Set(state.session?.protocol_progress || []);

    const nextStep = protocol.find((s) => !completed.has(s.id));
    if (!nextStep) {
      if (this.nextStepInstruction) this.nextStepInstruction.textContent = '🎉 All protocol steps completed! Review findings and Submit Report.';
      if (this.nextStepHint) this.nextStepHint.textContent = 'Click [Finish Report] in the top right to view grading breakdown.';
      return;
    }

    const stepIdx = protocol.indexOf(nextStep) + 1;
    if (this.nextStepInstruction) {
      this.nextStepInstruction.textContent = `Step ${stepIdx}: ${this.formatProtocolTitle(nextStep.id)}`;
    }
    if (this.nextStepHint) {
      this.nextStepHint.textContent = nextStep.hint || 'Complete protocol actions following safety standards.';
    }

    // Update pulsing beacon / glow over next step apparatus
    if (this.directiveQueue?.scene && this.directiveQueue?.effectManager) {
      const targetApparatusId = this.mapStepToApparatus(nextStep.id);
      const targetMesh = this.directiveQueue.scene.getApparatus(targetApparatusId);
      if (targetMesh) {
        this.directiveQueue.effectManager.playEffect(targetMesh, { name: 'glow', duration_ms: 2500 });
      }
    }
  }

  mapStepToApparatus(stepId) {
    if (stepId.includes('balance') || stepId.includes('weigh')) return 'digital_balance';
    if (stepId.includes('dissolve') || stepId.includes('cup')) return 'dosing_cup';
    if (stepId.includes('oral') || stepId.includes('patient')) return 'patient_bed';
    if (stepId.includes('blood') || stepId.includes('draw')) return 'tube_rack';
    if (stepId.includes('assay')) return 'assay_analyzer';
    if (stepId.includes('burette')) return 'burette';
    if (stepId.includes('flask') || stepId.includes('pipette') || stepId.includes('indicator') || stepId.includes('titrate')) return 'conical_flask';
    if (stepId.includes('waste')) return 'chemical_waste_bin';
    if (stepId.includes('wash') || stepId.includes('hand')) return 'sink';
    return null;
  }

  formatProtocolTitle(stepId) {
    const map = {
      wear_ppe: 'Wear Personal Protective Equipment (PPE)',
      tare_balance: 'Tare Digital Balance to 0.000g',
      weigh_dose: 'Weigh 0.500g Paracetamol Powder',
      dissolve_dose: 'Dissolve Dose in Water Jug',
      label_cup: 'Label Dosing Cup with Patient Details',
      administer_oral: 'Administer Oral Suspension to Alex',
      advance_time: 'Advance Clinical Ward Clock',
      label_tubes: 'Label Venous Blood Sampling Tubes',
      draw_blood: 'Perform Timed Blood Plasma Sampling',
      run_assay: 'Centrifuge & Assay Plasma Concentrations',
      rinse_burette: 'Rinse Burette with Standard Titrant',
      fill_burette: 'Fill Burette to Zero Calibration Mark',
      pipette_analyte: 'Pipette 10.0 mL Acid Analyte into Flask',
      add_indicator: 'Add pH Color Indicator Solution',
      titrate: 'Titrate Drop-Wise with Continuous Swirling',
      record_endpoint: 'Record Precise Equivalence Endpoint',
      dispose_waste: 'Segregate & Dispose Chemical Waste',
      wash_hands: 'Wash Hands Thoroughly at Utility Sink',
      submit_report: 'Submit Complete Experimental Report',
    };
    return map[stepId] || stepId.replace(/_/g, ' ');
  }

  renderActions() {
    if (!this.groupsContainer && !this.container) return;

    // 1. Hide actions that never apply to the current experiment
    let allActions = state.availableActions || [];
    const expAllowed = state.experiment?.allowed_actions;
    if (expAllowed && Array.isArray(expAllowed)) {
      allActions = allActions.filter((item) => expAllowed.includes(item.action));
    }

    const targetId = state.selectedTargetId;

    if (this.targetNameEl) {
      this.targetNameEl.textContent = targetId ? `STATION: ${targetId.toUpperCase().replace(/_/g, ' ')}` : 'GENERAL LAB';
    }

    // 2. Populate compact primary row for active station
    if (this.stationActionsList) {
      this.stationActionsList.innerHTML = '';

      if (targetId === 'virtual_trial_screen') {
        const btnTrial = document.createElement('button');
        btnTrial.type = 'button';
        btnTrial.className = 'compact-action-btn primary-action';
        btnTrial.innerHTML = '<span>👥 Run Virtual Trial & Enter Gallery</span>';
        btnTrial.onclick = () => state.emit('open_trial_panel');
        this.stationActionsList.appendChild(btnTrial);
        return;
      }

      const stationAffinities = {
        burette: ['rinse_burette', 'fill_burette', 'titrate'],
        conical_flask: ['pipette_analyte', 'add_indicator', 'titrate', 'swirl', 'record_endpoint'],
        digital_balance: ['tare_balance', 'weigh'],
        patient_bed: ['administer_oral', 'draw_blood'],
        tube_rack: ['label', 'draw_blood', 'run_assay'],
        assay_analyzer: ['run_assay'],
        dosing_cup: ['dissolve', 'label'],
        ward_clock: ['advance_time'],
        ph_meter: ['read_ph_meter', 'record_endpoint'],
        sink: ['wash_hands'],
        chemical_waste_bin: ['dispose_waste'],
        biohazard_bin: ['dispose_waste'],
      };

      const validAffinities = targetId && stationAffinities[targetId]
        ? new Set(stationAffinities[targetId])
        : null;

      let primaryActions = [];
      if (validAffinities) {
        primaryActions = allActions.filter((a) => validAffinities.has(a.action));
      }

      // If station has no specific actions or none found, show top enabled actions
      if (primaryActions.length === 0) {
        primaryActions = allActions.filter((a) => a.enabled).slice(0, 4);
      }

      // Sort primary actions so enabled appear first
      primaryActions.sort((a, b) => (b.enabled ? 1 : 0) - (a.enabled ? 1 : 0));

      primaryActions.forEach((item) => {
        this.stationActionsList.appendChild(this.createActionButton(item, targetId));
      });
    }

    // 3. Populate "More Actions" drawer with categorized full groups
    const groups = {
      safety: { title: '🛡️ Safety & Hygiene', items: [] },
      station: { title: '⚙️ Station Operations', items: [] },
      clinical: { title: '📊 Measurement & Clinical', items: [] },
      disposal: { title: '🗑️ Disposal & Submit', items: [] },
    };

    allActions.forEach((item) => {
      const act = item.action;
      if (act === 'wear_ppe' || act === 'remove_ppe' || act === 'wash_hands') {
        groups.safety.items.push(item);
      } else if (
        act.includes('balance') ||
        act === 'weigh' ||
        act === 'dissolve' ||
        act === 'label' ||
        act.includes('burette') ||
        act === 'pipette_analyte' ||
        act === 'add_indicator' ||
        act === 'titrate' ||
        act === 'swirl'
      ) {
        groups.station.items.push(item);
      } else if (
        act === 'administer_oral' ||
        act === 'advance_time' ||
        act === 'draw_blood' ||
        act === 'run_assay' ||
        act === 'read_ph_meter' ||
        act === 'record_endpoint'
      ) {
        groups.clinical.items.push(item);
      } else {
        groups.disposal.items.push(item);
      }
    });

    if (this.groupsContainer) {
      this.groupsContainer.innerHTML = '';

      Object.entries(groups).forEach(([key, group]) => {
        if (group.items.length === 0) return;

        // Sort items so enabled actions appear first
        const sortedItems = [...group.items].sort((a, b) => (b.enabled ? 1 : 0) - (a.enabled ? 1 : 0));

        const groupDiv = document.createElement('div');
        groupDiv.className = 'action-group';

        const titleDiv = document.createElement('div');
        titleDiv.className = 'action-group-title';
        titleDiv.textContent = group.title;
        groupDiv.appendChild(titleDiv);

        const btnRow = document.createElement('div');
        btnRow.className = 'action-group-buttons';

        sortedItems.forEach((item) => {
          const btn = this.createActionButton(item, targetId);
          btnRow.appendChild(btn);
        });

        groupDiv.appendChild(btnRow);
        this.groupsContainer.appendChild(groupDiv);
      });
    }

    // Also sync #action-quick-buttons for compatibility
    if (this.container && this.container !== this.groupsContainer) {
      this.container.innerHTML = '';
      allActions
        .sort((a, b) => (b.enabled ? 1 : 0) - (a.enabled ? 1 : 0))
        .forEach((item) => {
          this.container.appendChild(this.createActionButton(item, targetId));
        });
    }
  }

  createActionButton(item, targetId) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = `action-btn ${item.enabled ? 'enabled' : 'disabled'}`;
    btn.textContent = this.formatActionLabel(item.action);
    btn.dataset.action = item.action;

    if (!item.enabled) {
      btn.disabled = true;
      btn.dataset.backendDisabled = 'true';
      btn.title = item.disabled_reason || 'Action currently locked by protocol or safety prerequisite.';
    } else {
      btn.title = `Execute ${item.label || item.action}`;
      btn.onclick = () => this.handleActionClick(item.action, targetId);
    }

    return btn;
  }

  formatActionLabel(actionName) {
    const map = {
      wear_ppe: '🛡️ Wear PPE',
      remove_ppe: '🧤 Remove PPE',
      tare_balance: '⚖️ Tare Balance',
      weigh: '⚖️ Weigh Dose',
      dissolve: '💧 Dissolve Powder',
      label: '🏷️ Label Item',
      administer_oral: '💊 Administer Oral',
      advance_time: '⏱️ Advance Time',
      draw_blood: '🩸 Draw Blood',
      run_assay: '🔬 Run Assay',
      rinse_burette: '🧪 Rinse Burette',
      fill_burette: '🧪 Fill Burette',
      pipette_analyte: '🧪 Pipette Analyte',
      add_indicator: '💧 Add Indicator',
      titrate: '🧪 Titrate',
      swirl: '🔄 Swirl Flask',
      read_ph_meter: '⚡ Read pH Meter',
      record_endpoint: '📝 Record Endpoint',
      dispose_waste: '🗑️ Dispose Waste',
      wash_hands: '🧼 Wash Hands',
      pour: '🫗 Pour Liquid',
      submit_report: '✓ Submit Report',
    };
    return map[actionName] || actionName.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  }

  async handleActionClick(action, targetId) {
    if (action === 'weigh') {
      this.showWeighModal(action, targetId);
    } else if (action === 'titrate') {
      this.showTitrateModal(action, targetId);
    } else if (action === 'advance_time') {
      this.showAdvanceTimeModal(action, targetId);
    } else if (action === 'add_indicator') {
      this.showIndicatorModal(action, targetId);
    } else if (action === 'label') {
      this.showLabelModal(action, targetId);
    } else if (action === 'submit_report') {
      // Trigger finish report
      const btnFinish = document.getElementById('btn-finish-experiment');
      if (btnFinish) btnFinish.click();
    } else {
      await this.executeAction(action, targetId, {});
    }
  }

  showWeighModal(action, targetId) {
    this.openParamModal('Weigh Powder', (container, submit) => {
      container.innerHTML = `
        <div class="param-field">
          <label>Target Substance:</label>
          <input type="text" value="paracetamol" readonly />
        </div>
        <div class="param-field">
          <label>Amount (grams): <span id="weigh-readout">0.500 g</span></label>
          <input type="range" id="weigh-slider" min="0.1" max="1.0" step="0.05" value="0.5" />
        </div>
      `;
      const slider = container.querySelector('#weigh-slider');
      const readout = container.querySelector('#weigh-readout');
      slider.oninput = () => (readout.textContent = `${parseFloat(slider.value).toFixed(3)} g`);

      submit(() => ({
        amount_g: parseFloat(slider.value),
        substance: 'paracetamol',
      }));
    }, action, targetId);
  }

  showTitrateModal(action, targetId) {
    this.openParamModal('Dispense Titrant', (container, submit) => {
      container.innerHTML = `
        <div class="param-field">
          <label>Dispense Volume (mL): <span id="titrate-readout">1.00 mL</span></label>
          <input type="range" id="titrate-slider" min="0.1" max="10.0" step="0.1" value="1.0" />
        </div>
        <div style="display:flex; gap:6px; margin-bottom:12px;">
          <button type="button" class="btn-secondary" id="btn-quick-drop">Drop-wise (0.2 mL)</button>
          <button type="button" class="btn-secondary" id="btn-quick-fast">Fast (5.0 mL)</button>
        </div>
      `;
      const slider = container.querySelector('#titrate-slider');
      const readout = container.querySelector('#titrate-readout');
      slider.oninput = () => (readout.textContent = `${parseFloat(slider.value).toFixed(2)} mL`);

      container.querySelector('#btn-quick-drop').onclick = () => {
        slider.value = 0.2;
        readout.textContent = '0.20 mL';
      };
      container.querySelector('#btn-quick-fast').onclick = () => {
        slider.value = 5.0;
        readout.textContent = '5.00 mL';
      };

      submit(() => ({
        volume_ml: parseFloat(slider.value),
      }));
    }, action, targetId);
  }

  showAdvanceTimeModal(action, targetId) {
    this.openParamModal('Advance Ward Clock', (container, submit) => {
      container.innerHTML = `
        <div class="param-field">
          <label>Advance by (hours): <span id="time-readout">1.00 h</span></label>
          <input type="range" id="time-slider" min="0.25" max="4.0" step="0.25" value="1.0" />
        </div>
      `;
      const slider = container.querySelector('#time-slider');
      const readout = container.querySelector('#time-readout');
      slider.oninput = () => (readout.textContent = `${parseFloat(slider.value).toFixed(2)} h`);

      submit(() => ({
        hours: parseFloat(slider.value),
      }));
    }, action, targetId);
  }

  showIndicatorModal(action, targetId) {
    this.openParamModal('Add Color Indicator', (container, submit) => {
      container.innerHTML = `
        <div class="param-field">
          <label>Indicator Solution:</label>
          <select id="indicator-select">
            <option value="phenolphthalein">Phenolphthalein (Clear -> Pink at pH 8.2)</option>
            <option value="methyl_orange">Methyl Orange (Red -> Yellow at pH 3.1-4.4)</option>
            <option value="bromothymol_blue">Bromothymol Blue (Yellow -> Blue at pH 6.0-7.6)</option>
          </select>
        </div>
        <div class="param-field">
          <label>Drops: 3 drops</label>
        </div>
      `;
      submit(() => ({
        indicator: container.querySelector('#indicator-select').value,
        drops: 3,
        target: 'conical_flask',
      }));
    }, action, targetId);
  }

  showLabelModal(action, targetId) {
    this.openParamModal('Label Apparatus', (container, submit) => {
      container.innerHTML = `
        <div class="param-field">
          <label>Label Text:</label>
          <input type="text" id="label-text-input" value="Pt: Alex" />
        </div>
      `;
      submit(() => ({
        text: container.querySelector('#label-text-input').value,
        target: targetId || 'dosing_cup',
      }));
    }, action, targetId);
  }

  openParamModal(title, setupContent, action, targetId) {
    if (!this.paramModal) return;
    this.paramModal.innerHTML = '';
    this.paramModal.style.display = 'block';

    const titleEl = document.createElement('div');
    titleEl.className = 'param-modal-title';
    titleEl.textContent = title;

    const contentDiv = document.createElement('div');
    const btnsDiv = document.createElement('div');
    btnsDiv.className = 'param-modal-btns';

    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'btn-secondary';
    cancelBtn.textContent = 'Cancel';
    cancelBtn.onclick = () => (this.paramModal.style.display = 'none');

    const okBtn = document.createElement('button');
    okBtn.className = 'btn-primary';
    okBtn.style.padding = '8px 16px';
    okBtn.textContent = 'Confirm Action';

    btnsDiv.appendChild(cancelBtn);
    btnsDiv.appendChild(okBtn);

    this.paramModal.appendChild(titleEl);
    this.paramModal.appendChild(contentDiv);
    this.paramModal.appendChild(btnsDiv);

    setupContent(contentDiv, (getParamsFn) => {
      okBtn.onclick = async () => {
        const params = getParamsFn();
        this.paramModal.style.display = 'none';
        await this.executeAction(action, targetId, params);
      };
    });
  }

  async executeAction(action, targetId, params = {}) {
    if (!state.session?.session_id) return;
    state.setPending(true);

    try {
      const result = await api.applyAction(state.session.session_id, action, targetId, params);

      // Show toast if message
      if (result.message) {
        toast.showInfo(result.message);
      }

      // Check violations
      if (result.violations && result.violations.length > 0) {
        for (const v of result.violations) {
          toast.showViolation(v);
        }
      }

      // Update avatar PPE if action modified it
      if (action === 'wear_ppe' || action === 'remove_ppe') {
        const updated = await api.getSession(state.session.session_id);
        state.setSession(updated);
        if (this.characterController) {
          this.characterController.updatePPE(updated.ppe);
        }
      }

      // Process directives in queue
      await this.directiveQueue.processActionResult(result, targetId);

      // Refresh session & available actions
      const updatedSession = await api.getSession(state.session.session_id);
      state.setSession(updatedSession);

      const updatedActions = await api.getAvailableActions(state.session.session_id);
      state.setAvailableActions(updatedActions);
    } catch (err) {
      toast.showInfo(`Action Failed: ${err.message}`, 4000);
      console.error(err);
    } finally {
      state.setPending(false);
    }
  }
}
