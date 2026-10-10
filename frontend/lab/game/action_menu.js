/**
 * Context-Aware Action Menu & Parameter Modal (frontend/lab/game/action_menu.js)
 * Displays available interactive actions for the selected station and gathers inputs.
 */

import { api } from '../api.js';
import { state } from '../state.js';
import { toast } from './toast.js';

export class ActionMenu {
  constructor(directiveQueue, characterController) {
    this.directiveQueue = directiveQueue;
    this.characterController = characterController;
    this.container = document.getElementById('action-quick-buttons');
    this.paramModal = document.getElementById('action-param-modal');

    state.subscribe((event, payload) => {
      if (event === 'actions_updated' || event === 'target_selected') {
        this.renderActions();
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

    if (this.container) {
      const btns = this.container.querySelectorAll('.action-btn');
      btns.forEach((b) => (b.disabled = isPending || b.dataset.backendDisabled === 'true'));
    }
  }

  renderActions() {
    if (!this.container) return;
    this.container.innerHTML = '';

    const targetId = state.selectedTargetId;
    const allActions = state.availableActions || [];

    // Filter actions relevant to selected apparatus, or global actions (wear_ppe, wash_hands, advance_time)
    const relevant = allActions.filter((a) => {
      const act = a.action;
      if (act === 'wear_ppe' || act === 'remove_ppe' || act === 'wash_hands' || act === 'advance_time') {
        return true;
      }
      if (!targetId) return true;
      if (a.targets && a.targets.includes(targetId)) return true;
      if (act.includes('burette') && targetId === 'burette') return true;
      if (act.includes('titrate') && (targetId === 'burette' || targetId === 'conical_flask')) return true;
      if (act.includes('balance') && targetId === 'digital_balance') return true;
      if (act.includes('blood') && (targetId.startsWith('tube_') || targetId === 'tube_rack' || targetId === 'patient_bed')) return true;
      if (act.includes('assay') && (targetId.startsWith('tube_') || targetId === 'tube_rack' || targetId === 'assay_analyzer')) return true;
      if (act.includes('waste') && targetId.includes('waste')) return true;
      return false;
    });

    if (relevant.length === 0) {
      const emptyMsg = document.createElement('div');
      emptyMsg.style.fontSize = '0.8rem';
      emptyMsg.style.color = '#94a3b8';
      emptyMsg.textContent = targetId
        ? 'No direct actions for this station. Select another apparatus or take general lab actions.'
        : 'Click on any lab apparatus in 3D to view available actions.';
      this.container.appendChild(emptyMsg);
      return;
    }

    relevant.forEach((item) => {
      const btn = document.createElement('button');
      btn.className = 'action-btn';
      btn.textContent = this.formatActionLabel(item.action);
      btn.dataset.action = item.action;

      if (!item.enabled) {
        btn.disabled = true;
        btn.dataset.backendDisabled = 'true';
        btn.title = item.disabled_reason || 'Action currently unavailable';
      } else {
        btn.onclick = () => this.handleActionClick(item.action, targetId);
      }

      this.container.appendChild(btn);
    });
  }

  formatActionLabel(actionName) {
    const map = {
      wear_ppe: '🛡️ Wear PPE',
      remove_ppe: 'Remove PPE',
      tare_balance: '⚖️ Tare Balance',
      weigh: '⚖️ Weigh Dose',
      dissolve: '💧 Dissolve Powder',
      label: '🏷️ Label Object',
      administer_oral: '💊 Administer Oral',
      advance_time: '⏱️ Advance Time',
      draw_blood: '🩸 Draw Blood',
      run_assay: '🔬 Run Assay',
      rinse_burette: '🧪 Rinse Burette',
      fill_burette: '🧪 Fill Burette',
      pipette_analyte: 'Pipette Analyte',
      add_indicator: '💧 Add Indicator',
      titrate: '🧪 Titrate (Dispense)',
      swirl: 'Swirl Flask',
      read_ph_meter: '⚡ Read pH Meter',
      record_endpoint: '📝 Record Endpoint',
      dispose_waste: '🗑️ Dispose Waste',
      wash_hands: '🧼 Wash Hands',
    };
    return map[actionName] || actionName.replace(/_/g, ' ');
  }

  async handleActionClick(action, targetId) {
    // Check if parameters are required
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
    } else {
      // Execute directly
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
