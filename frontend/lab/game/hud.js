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
      if (isDone) {
        item.classList.add('completed');
      } else if (!foundCurrent) {
        item.classList.add('current');
        foundCurrent = true;
      }

      const numSpan = document.createElement('span');
      numSpan.className = 'step-indicator';
      numSpan.textContent = isDone ? '✓' : `${idx + 1}.`;

      const textSpan = document.createElement('span');
      textSpan.className = 'step-text';
      textSpan.textContent = step.hint || step.description || step.id;

      item.appendChild(numSpan);
      item.appendChild(textSpan);
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
