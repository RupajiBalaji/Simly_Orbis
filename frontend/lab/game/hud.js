/**
 * In-Game HUD Interface & Protocol Checklist (frontend/lab/game/hud.js)
 * Coordinates the protocol checklist, PPE pills, safety score, and event log.
 */

import { state } from '../state.js';
import { soundFX } from '../audio/sound_fx.js';
import { toast } from './toast.js';

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

    window.labHUD = this;

    if (btnToggleChecklist && this.checklistPanel) {
      btnToggleChecklist.onclick = () => {
        this.setChecklistCollapsed(!this.checklistPanel.classList.contains('collapsed'));
        soundFX.playClick();
      };
    }

    if (btnToggleLog && this.logPanel) {
      btnToggleLog.onclick = () => {
        this.setLogCollapsed(!this.logPanel.classList.contains('collapsed'));
        soundFX.playClick();
      };
    }

    // Sound FX Controls
    this.btnToggleSound = document.getElementById('btn-toggle-sound');
    this.volumeSlider = document.getElementById('hud-volume-slider');
    if (this.btnToggleSound) {
      this.btnToggleSound.textContent = soundFX.isMuted ? '🔇' : '🔊';
      this.btnToggleSound.onclick = () => {
        const muted = soundFX.toggleMute();
        this.btnToggleSound.textContent = muted ? '🔇' : '🔊';
        soundFX.playClick();
      };
    }
    if (this.volumeSlider) {
      this.volumeSlider.value = Math.round(soundFX.volume * 100);
      this.volumeSlider.oninput = (e) => {
        const val = parseFloat(e.target.value) / 100;
        soundFX.setVolume(val);
        if (soundFX.isMuted && val > 0) {
          soundFX.setMuted(false);
          if (this.btnToggleSound) this.btnToggleSound.textContent = '🔊';
        }
      };
    }

    if (window.innerWidth < 1200) {
      this.setChecklistCollapsed(true);
    }

    window.addEventListener('resize', () => {
      if (window.innerWidth < 1200) {
        this.setChecklistCollapsed(true);
        window.drOrbisMentor?.setCollapsed(true);
      }
    });

    this.lastProgressCount = 0;

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

    // Initialize CP3 interaction subsystems
    this.initProximityAndRadial();
    this.initControlsModal();
    this.initCollapsibleDock();
    this.initTouchJoystick();
  }

  setChecklistCollapsed(collapsed) {
    if (!this.checklistPanel) return;
    this.checklistPanel.classList.toggle('collapsed', Boolean(collapsed));
    const btn = document.getElementById('btn-toggle-checklist');
    if (btn) btn.textContent = this.checklistPanel.classList.contains('collapsed') ? '▶' : '◀';
  }

  setLogCollapsed(collapsed) {
    if (!this.logPanel) return;
    this.logPanel.classList.toggle('collapsed', Boolean(collapsed));
    const btn = document.getElementById('btn-toggle-log');
    if (btn) btn.textContent = this.logPanel.classList.contains('collapsed') ? '▲' : '▼';
  }

  show() {
    if (this.container) this.container.classList.remove('hidden');
    document.getElementById('dr-orbis-container')?.classList.remove('hidden');
    soundFX.startAmbientHum();
  }

  hide() {
    if (this.container) this.container.classList.add('hidden');
    document.getElementById('dr-orbis-container')?.classList.add('hidden');
    soundFX.stopAmbientHum();
    soundFX.stopAlarmLoop();
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
    const curProgressCount = (session.protocol_progress || []).length;
    if (curProgressCount > this.lastProgressCount) {
      if (this.lastProgressCount > 0) {
        soundFX.playSuccessChime();
        const banner = document.getElementById('hud-next-step-banner');
        if (banner) {
          banner.classList.remove('step-pulse-green');
          void banner.offsetWidth;
          banner.classList.add('step-pulse-green');
          setTimeout(() => banner.classList.remove('step-pulse-green'), 850);
        }
      }
      this.lastProgressCount = curProgressCount;
    }

    const hasCritical = (session.violations || []).some(v => v.severity === 'critical');
    if (hasCritical) {
      soundFX.startAlarmLoop();
    } else {
      soundFX.stopAlarmLoop();
    }

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
      titleSpan.textContent = step.title || this.formatStepTitle(step.id);
      contentDiv.appendChild(titleSpan);

      // Render hint text ONLY under the active step
      if (isCurrent && (step.hint_text || step.hint || step.description)) {
        const hintSpan = document.createElement('div');
        hintSpan.className = 'step-hint-text';
        hintSpan.textContent = step.hint_text || step.hint || step.description;
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

  initProximityAndRadial() {
    this.proximityPromptEl = document.getElementById('hud-proximity-prompt');
    this.proximityPromptLabel = document.getElementById('proximity-prompt-label');
    this.radialWheelEl = document.getElementById('hud-radial-wheel');
    this.radialItemsContainer = document.getElementById('radial-items-container');
    this.radialStationTitle = document.getElementById('radial-station-title');
    this.radialBackdrop = document.getElementById('radial-backdrop');
    this.currentProximityStation = null;
    this.isRadialOpen = false;

    if (this.proximityPromptEl) {
      this.proximityPromptEl.onclick = () => this.triggerProximityInteract();
    }
    if (this.radialBackdrop) {
      this.radialBackdrop.onclick = () => this.closeRadialWheel();
    }
  }

  initControlsModal() {
    this.controlsModal = document.getElementById('controls-modal');
    const btnOpenControls = document.getElementById('btn-open-controls');
    const btnCloseControls = document.getElementById('btn-close-controls');
    if (btnOpenControls) {
      btnOpenControls.onclick = () => this.toggleControlsModal();
    }
    if (btnCloseControls) {
      btnCloseControls.onclick = () => this.toggleControlsModal(false);
    }
    if (this.controlsModal) {
      this.controlsModal.onclick = (e) => {
        if (e.target === this.controlsModal) this.toggleControlsModal(false);
      };
    }
  }

  initCollapsibleDock() {
    const btnCollapse = document.getElementById('btn-collapse-bottom-dock');
    const bottomDock = document.getElementById('hud-bottom-dock');
    if (btnCollapse && bottomDock) {
      btnCollapse.onclick = () => {
        bottomDock.classList.toggle('minimized');
        const isMin = bottomDock.classList.contains('minimized');
        btnCollapse.textContent = isMin ? '▲ Expand' : '▼ Minimize';
        soundFX.playClick();
      };
    }
  }

  initTouchJoystick() {
    const zone = document.getElementById('touch-joystick-zone');
    const base = document.getElementById('touch-joystick-base');
    const knob = document.getElementById('touch-joystick-knob');
    if (!zone || !base || !knob) return;

    let active = false;
    let baseRect = null;
    const maxDist = 36;

    const onPointerDown = (e) => {
      active = true;
      baseRect = base.getBoundingClientRect();
      updateKnob(e);
      window.addEventListener('pointermove', onPointerMove);
      window.addEventListener('pointerup', onPointerUp);
    };

    const updateKnob = (e) => {
      if (!active || !baseRect) return;
      const cx = baseRect.left + baseRect.width / 2;
      const cy = baseRect.top + baseRect.height / 2;
      let dx = e.clientX - cx;
      let dy = e.clientY - cy;
      const dist = Math.hypot(dx, dy);
      if (dist > maxDist) {
        dx = (dx / dist) * maxDist;
        dy = (dy / dist) * maxDist;
      }
      knob.style.transform = `translate(${dx}px, ${dy}px)`;
      const nx = dx / maxDist;
      const ny = -dy / maxDist;
      window.characterController?.setJoystickInput(nx, ny);
    };

    const onPointerMove = (e) => {
      updateKnob(e);
    };

    const onPointerUp = () => {
      active = false;
      knob.style.transform = 'translate(0px, 0px)';
      window.characterController?.setJoystickInput(0, 0);
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
    };

    zone.addEventListener('pointerdown', onPointerDown);
  }

  updateProximity(dt) {
    const avatar = window.characterController?.rig?.root;
    const lookup = window.sceneManager?.apparatusLookup;
    if (!avatar || !lookup) return;

    const avPos = avatar.position;
    let closestStation = null;
    let minDistance = Infinity;

    for (const [targetId, appObj] of Object.entries(lookup)) {
      if (!appObj || !appObj.position) continue;
      const pos = appObj.userData?.stationPos || appObj.position;
      const dist = Math.hypot(pos.x - avPos.x, pos.z - avPos.z);
      if (dist < minDistance && dist <= 1.8) {
        minDistance = dist;
        closestStation = { id: targetId, name: this.formatStationName(targetId), obj: appObj, dist };
      }
    }

    if (closestStation) {
      this.currentProximityStation = closestStation;
      if (this.proximityPromptEl) {
        this.proximityPromptEl.classList.remove('hidden');
        if (this.proximityPromptLabel) {
          this.proximityPromptLabel.textContent = `Use ${closestStation.name}`;
        }
      }
    } else {
      if (this.proximityPromptEl) {
        this.proximityPromptEl.classList.add('hidden');
      }
      if (this.isRadialOpen && minDistance > 2.4) {
        this.closeRadialWheel();
      }
      this.currentProximityStation = null;
    }
  }

  formatStationName(targetId) {
    const names = {
      digital_balance: 'Analytical Balance',
      dosing_cup: 'Dosing Cup',
      patient_bed: 'Patient Alex',
      ward_clock: 'Ward Clock',
      tube_rack: 'Sample Tubes',
      assay_analyzer: 'Plasma Analyzer',
      burette: 'Burette Stand',
      conical_flask: 'Conical Flask',
      sink: 'Utility Sink',
      chemical_waste_bin: 'Waste Bin',
      biohazard_bin: 'Biohazard Bin',
      virtual_trial_screen: 'Clinical Trial Screen',
      reality_check_board: 'Reality Check Board',
    };
    return names[targetId] || targetId.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  }

  triggerProximityInteract() {
    if (this.isRadialOpen) {
      this.closeRadialWheel();
      return;
    }
    if (this.currentProximityStation) {
      this.openRadialWheel(this.currentProximityStation.id, this.currentProximityStation.name);
    } else {
      state.showToast?.('Move closer to a station to interact (or use mouse)');
    }
  }

  openRadialWheel(stationId, stationName) {
    if (!this.radialWheelEl || !this.radialItemsContainer) return;
    this.isRadialOpen = true;
    this.radialWheelEl.classList.remove('hidden');
    if (this.radialStationTitle) {
      this.radialStationTitle.textContent = stationName || this.formatStationName(stationId);
    }
    this.radialItemsContainer.innerHTML = '';

    const actions = window.actionMenu?.getActionsForStation(stationId) || [];
    if (actions.length === 0) {
      const emptyDiv = document.createElement('div');
      emptyDiv.className = 'radial-empty-notice';
      emptyDiv.textContent = 'No actions available at this step';
      this.radialItemsContainer.appendChild(emptyDiv);
      return;
    }

    const total = actions.length;
    const radius = total > 4 ? 120 : 100;
    actions.forEach((act, i) => {
      const angle = (i / total) * Math.PI * 2 - Math.PI / 2;
      const x = Math.round(Math.cos(angle) * radius);
      const y = Math.round(Math.sin(angle) * radius);

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'radial-action-item' + (act.enabled ? '' : ' disabled');
      btn.title = act.enabled ? act.label : (act.reason || 'Action disabled for current step');
      btn.style.left = `calc(50% + ${x}px)`;
      btn.style.top = `calc(50% + ${y}px)`;
      btn.innerHTML = `
        <span class="radial-item-icon">${act.icon || '⚗️'}</span>
        <span class="radial-item-label">${act.label}</span>
      `;
      if (act.enabled) {
        btn.onclick = (e) => {
          e.stopPropagation();
          this.closeRadialWheel();
          window.actionMenu?.handleActionClick(act.action, stationId);
        };
      } else {
        btn.onclick = (e) => {
          e.stopPropagation();
          toast.showInfo(act.reason || 'Action disabled for current step');
        };
      }
      this.radialItemsContainer.appendChild(btn);
    });
    soundFX.playClick();
  }

  closeRadialWheel() {
    if (!this.radialWheelEl) return;
    this.isRadialOpen = false;
    this.radialWheelEl.classList.add('hidden');
  }

  toggleControlsModal(forceState) {
    if (!this.controlsModal) return;
    const shouldOpen = forceState !== undefined ? forceState : this.controlsModal.classList.contains('hidden');
    if (shouldOpen) {
      this.controlsModal.classList.remove('hidden');
    } else {
      this.controlsModal.classList.add('hidden');
    }
    soundFX.playClick();
  }
}
