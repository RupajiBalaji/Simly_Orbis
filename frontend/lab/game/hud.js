/**
 * In-Game HUD Interface & Protocol Checklist (frontend/lab/game/hud.js)
 * Coordinates the protocol checklist, PPE pills, safety score, and event log.
 */

import { state } from '../state.js';

export class LabHUD {
  constructor() {
    this.container = document.getElementById('lab-hud');
    this.clockEl = document.getElementById('hud-clock');
    this.scoreEl = document.getElementById('hud-safety-score');
    this.expBadgeEl = document.getElementById('hud-exp-badge');
    this.protocolListEl = document.getElementById('protocol-steps-list');
    this.eventLogListEl = document.getElementById('event-log-list');

    this.ppeBadges = {
      goggles: document.getElementById('ppe-badge-goggles'),
      gloves: document.getElementById('ppe-badge-gloves'),
      coat: document.getElementById('ppe-badge-coat'),
    };

    this.selectedTargetEl = document.getElementById('selected-target-name');

    // Panel collapse toggles
    this.checklistPanel = document.getElementById('hud-protocol-panel');
    this.logPanel = document.getElementById('hud-right-panel');
    const btnToggleChecklist = document.getElementById('btn-toggle-checklist');
    const btnToggleLog = document.getElementById('btn-toggle-log');

    if (btnToggleChecklist && this.checklistPanel) {
      btnToggleChecklist.onclick = () => {
        this.checklistPanel.classList.toggle('collapsed');
        btnToggleChecklist.textContent = this.checklistPanel.classList.contains('collapsed') ? '▶' : '◀';
      };
    }

    if (btnToggleLog && this.logPanel) {
      btnToggleLog.onclick = () => {
        this.logPanel.classList.toggle('collapsed');
        btnToggleLog.textContent = this.logPanel.classList.contains('collapsed') ? '▲' : '▼';
      };
    }

    // Subscribe to state changes
    state.subscribe((event, payload) => {
      if (event === 'session_updated') {
        this.updateSession(payload);
      } else if (event === 'experiment_updated') {
        this.updateExperiment(payload);
      } else if (event === 'target_selected') {
        this.updateSelectedTarget(payload);
      }
    });
  }

  show() {
    if (this.container) this.container.classList.remove('hidden');
  }

  hide() {
    if (this.container) this.container.classList.add('hidden');
  }

  formatStepTitle(stepId) {
    const map = {
      wear_ppe: 'Wear Protective Equipment (PPE)',
      tare_balance: 'Tare Analytical Balance',
      weigh_dose: 'Weigh Active Drug Dose',
      dissolve_dose: 'Dissolve Drug Dose in Water',
      label_cup: 'Label Oral Dosing Cup',
      administer_oral: 'Administer Oral Suspension',
      advance_time: 'Advance Simulated Clock',
      label_tube: 'Label Blood Sample Tube',
      label_tubes: 'Label Sampling Tubes',
      draw_blood: 'Collect Venous Blood Sample',
      run_assay: 'Run Centrifuge Drug Assay',
      rinse_burette: 'Rinse & Condition Burette',
      fill_burette: 'Fill Burette to Zero Mark',
      pipette_analyte: 'Pipette Analyte into Flask',
      add_indicator: 'Add pH Indicator Drops',
      titrate: 'Titrate to Equivalence Endpoint',
      swirl: 'Swirl Conical Flask',
      record_endpoint: 'Record Final Volume & pH',
      dispose_waste: 'Dispose Laboratory Waste',
      wash_hands: 'Wash Hands at Sink',
      submit_report: 'Submit Experimental Report',
    };
    return map[stepId] || stepId.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  }

  updateExperiment(exp) {
    if (!exp) return;
    if (this.expBadgeEl) {
      this.expBadgeEl.textContent = exp.title || exp.id;
    }
    this.renderProtocol(exp.protocol || [], []);
  }

  updateSession(session) {
    if (!session) return;

    // Clock
    if (this.clockEl) {
      this.clockEl.textContent = `t=${(session.clock_h || 0).toFixed(1)} h`;
    }

    // Safety Score
    if (this.scoreEl && session.score_parts) {
      const safetyScore = session.score_parts.safety ?? 40;
      this.scoreEl.textContent = `${safetyScore} pts`;
    }

    // PPE indicators
    const ppeSet = new Set(session.ppe || []);
    for (const [key, el] of Object.entries(this.ppeBadges)) {
      if (el) {
        if (ppeSet.has(key)) {
          el.classList.add('equipped');
        } else {
          el.classList.remove('equipped');
        }
      }
    }

    // Protocol progress
    if (state.experiment) {
      this.renderProtocol(state.experiment.protocol || [], session.protocol_progress || []);
    }

    // Event Log
    this.renderEventLog(session.events || []);
  }

  updateSelectedTarget(targetId) {
    if (this.selectedTargetEl) {
      const name = targetId ? targetId.replace(/_/g, ' ').toUpperCase() : 'NO APPARATUS SELECTED';
      this.selectedTargetEl.textContent = name;
    }
  }

  renderProtocol(protocolSteps, completedSteps) {
    if (!this.protocolListEl) return;
    this.protocolListEl.innerHTML = '';

    const completedSet = new Set(completedSteps);
    let foundCurrent = false;

    protocolSteps.forEach((step, idx) => {
      const item = document.createElement('div');
      item.className = 'protocol-step-item';

      const isDone = completedSet.has(step.id);
      const isCurrent = !isDone && !foundCurrent;
      if (isDone) {
        item.classList.add('completed');
      } else if (isCurrent) {
        item.classList.add('current');
        foundCurrent = true;
      }

      const numSpan = document.createElement('span');
      numSpan.className = 'step-indicator';
      numSpan.textContent = isDone ? '✓' : `${idx + 1}.`;

      const contentDiv = document.createElement('div');
      contentDiv.className = 'step-content-wrap';

      const titleSpan = document.createElement('div');
      titleSpan.className = 'step-title';
      titleSpan.textContent = this.formatStepTitle(step.id);
      contentDiv.appendChild(titleSpan);

      // Render hint text ONLY under the active step
      if (isCurrent && (step.hint || step.description)) {
        const hintSpan = document.createElement('div');
        hintSpan.className = 'step-hint-text';
        hintSpan.textContent = step.hint || step.description;
        contentDiv.appendChild(hintSpan);
      }

      item.appendChild(numSpan);
      item.appendChild(contentDiv);
      this.protocolListEl.appendChild(item);
    });
  }

  renderEventLog(events) {
    if (!this.eventLogListEl) return;
    this.eventLogListEl.innerHTML = '';

    const recent = events.slice(-8).reverse();
    recent.forEach((ev) => {
      const entry = document.createElement('div');
      entry.className = 'log-entry';
      if (ev.severity === 'critical' || ev.severity === 'major') {
        entry.classList.add('violation');
      }

      const timeSpan = document.createElement('span');
      timeSpan.className = 'log-time';
      timeSpan.textContent = `[${(ev.timestamp_h || 0).toFixed(1)}h]`;

      const msgSpan = document.createElement('span');
      msgSpan.textContent = ` ${ev.message || ev.action}`;

      entry.appendChild(timeSpan);
      entry.appendChild(msgSpan);
      this.eventLogListEl.appendChild(entry);
    });
  }
}
