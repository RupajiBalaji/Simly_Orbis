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
    this.initMenuDrawer();
    this.initCoachmarks();
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

    // First-run coachmarks guidance
    if (!localStorage.getItem('orbis_coachmarks_seen')) {
      this.showCoachmarks();
    }
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
    const expTitle = exp.title || exp.name || exp.id || 'Laboratory Simulation';
    const expNameEl = document.getElementById('hud-exp-name');
    if (expNameEl) {
      expNameEl.textContent = expTitle;
    }
    if (this.expBadgeEl) {
      this.expBadgeEl.textContent = expTitle;
    }
    this.renderMenuStations(exp);
    this.renderProtocol(exp.protocol || [], []);
  }

  updateSession(session) {
    if (!session) return;

    // Clock: Human-readable "Time: 0.0 h"
    if (this.clockEl) {
      this.clockEl.textContent = `Time: ${(session.clock_h || 0).toFixed(1)} h`;
    }

    // Total Score & Safety Compliance ("Score: 100", "Safety 100/100")
    const safetyScore = session.score_parts?.safety ?? session.safety_score ?? 100;
    const totalScore = session.score ?? session.total_score ?? safetyScore;
    if (this.scoreEl) {
      this.scoreEl.textContent = `Score: ${totalScore}`;
    }

    const safetyStatusEl = document.getElementById('hud-safety-status');
    if (safetyStatusEl) {
      safetyStatusEl.textContent = `Safety ${safetyScore}/100`;
      safetyStatusEl.classList.remove('warn', 'danger');
      if (safetyScore < 50) {
        safetyStatusEl.classList.add('danger');
      } else if (safetyScore < 80) {
        safetyStatusEl.classList.add('warn');
      }
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

    // Telemetry readouts (Spec 8.4)
    const concEl = document.getElementById('readout-concentration');
    if (concEl) {
      if (session.latest_assay?.concentration_mg_l !== undefined) {
        concEl.textContent = `${session.latest_assay.concentration_mg_l.toFixed(2)} mg/L`;
      } else if (session.dose_mg !== undefined) {
        concEl.textContent = `${session.dose_mg} mg`;
      } else {
        concEl.textContent = '0.00 mg/L';
      }
    }

    const massEl = document.getElementById('readout-mass');
    if (massEl) {
      if (session.weighed_amount_g !== undefined) {
        massEl.textContent = `${session.weighed_amount_g.toFixed(3)} g`;
      } else if (session.volume_ml !== undefined) {
        massEl.textContent = `${session.volume_ml.toFixed(1)} mL`;
      } else {
        massEl.textContent = '0.000 g';
      }
    }

    // Active Rules Panel (Spec 8.4)
    this.updateRulesPanel(session);

    // Event Log
    this.renderEventLog(session.events || []);
  }

  updateRulesPanel(session) {
    const statusBadge = document.getElementById('hud-rules-status-badge');
    const ruleTitle = document.getElementById('rule-title');
    const ruleStatus = document.getElementById('rule-status');
    const ruleReason = document.getElementById('rule-reason');

    const violations = session.violations || [];
    if (violations.length > 0) {
      const latest = violations[violations.length - 1];
      if (statusBadge) {
        statusBadge.textContent = 'Breached';
        statusBadge.className = 'badge badge-danger';
      }
      if (ruleTitle) ruleTitle.textContent = latest.rule_id ? `Rule ${latest.rule_id}` : 'Safety Rule Violation';
      if (ruleStatus) ruleStatus.textContent = `Breached: ${latest.message || latest.rule_id}`;
      if (ruleReason) ruleReason.textContent = latest.explanation || 'Protocol safety rule breached. Algorithmic penalty applied.';
    } else {
      const ppe = session.ppe || [];
      const required = state.experiment?.required_ppe || ['goggles', 'gloves', 'coat'];
      const missing = required.filter((p) => !ppe.includes(p));

      if (missing.length > 0) {
        if (statusBadge) {
          statusBadge.textContent = 'At Risk';
          statusBadge.className = 'badge badge-warn';
        }
        if (ruleTitle) ruleTitle.textContent = 'Rule R1: Mandatory PPE';
        if (ruleStatus) ruleStatus.textContent = `Missing: ${missing.join(', ')}`;
        if (ruleReason) ruleReason.textContent = 'Protects student researcher from chemical splashes and contact dermatitis.';
      } else {
        if (statusBadge) {
          statusBadge.textContent = 'Compliant';
          statusBadge.className = 'badge badge-ok';
        }
        if (ruleTitle) ruleTitle.textContent = 'Rules R1-R10: Active Safety Standards';
        if (ruleStatus) ruleStatus.textContent = 'All laboratory protocol safety requirements satisfied.';
        if (ruleReason) ruleReason.textContent = 'Zero protocol violations detected. Operating within safe simulation boundaries.';
      }
    }
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

    // Touch long-press (500ms hold) to open action wheel
    let touchTimer = null;
    let touchStartX = 0;
    let touchStartY = 0;
    window.addEventListener('touchstart', (e) => {
      if (e.touches.length === 1) {
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
        touchTimer = setTimeout(() => {
          this.triggerProximityInteract();
        }, 500);
      }
    }, { passive: true });

    window.addEventListener('touchmove', (e) => {
      if (touchTimer && e.touches.length === 1) {
        const dx = e.touches[0].clientX - touchStartX;
        const dy = e.touches[0].clientY - touchStartY;
        if (Math.hypot(dx, dy) > 10) {
          clearTimeout(touchTimer);
          touchTimer = null;
        }
      }
    }, { passive: true });

    window.addEventListener('touchend', () => {
      if (touchTimer) {
        clearTimeout(touchTimer);
        touchTimer = null;
      }
    }, { passive: true });
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
    const handle = document.getElementById('bottom-sheet-drag-handle');

    const toggleDock = () => {
      bottomDock.classList.toggle('minimized');
      const isMin = bottomDock.classList.contains('minimized');
      if (btnCollapse) btnCollapse.textContent = isMin ? '▲ Expand' : '▼ Minimize';
      soundFX.playClick();
    };

    if (btnCollapse && bottomDock) {
      btnCollapse.onclick = toggleDock;
    }
    if (handle && bottomDock) {
      handle.onclick = toggleDock;
      handle.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          toggleDock();
        }
      });
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

  /* -------------------------------------------------------------------------
   * Slide-Over Menu Drawer & Progressive Disclosure Settings
   * ------------------------------------------------------------------------- */
  initMenuDrawer() {
    this.menuDrawer = document.getElementById('hud-menu-drawer');
    const btnOpen = document.getElementById('btn-open-menu');
    const btnSettings = document.getElementById('btn-open-settings');
    const btnClose = document.getElementById('btn-close-menu');
    const backdrop = document.getElementById('menu-drawer-backdrop');

    if (btnOpen) btnOpen.onclick = () => this.openMenuDrawer();
    if (btnSettings) btnSettings.onclick = () => this.openMenuDrawer();
    if (btnClose) btnClose.onclick = () => this.closeMenuDrawer();
    if (backdrop) backdrop.onclick = () => this.closeMenuDrawer();

    // Camera mode buttons
    document.getElementById('btn-menu-cam-follow')?.addEventListener('click', () => {
      window.sceneManager?.cameraRig?.setMode('follow');
      this.closeMenuDrawer();
      toast.showInfo('Camera: Follow Mode');
    });
    document.getElementById('btn-menu-cam-first')?.addEventListener('click', () => {
      window.sceneManager?.cameraRig?.setMode('first_person');
      this.closeMenuDrawer();
      toast.showInfo('Camera: First-Person Mode');
    });
    document.getElementById('btn-menu-cam-recenter')?.addEventListener('click', () => {
      window.sceneManager?.cameraRig?.recenter();
      this.closeMenuDrawer();
    });
    document.getElementById('btn-menu-cam-reset')?.addEventListener('click', () => {
      window.sceneManager?.resetCamera();
      this.closeMenuDrawer();
    });

    // Auto-align behind me toggle
    const chkAutoAlign = document.getElementById('chk-auto-align-behind');
    if (chkAutoAlign) {
      const isAuto = localStorage.getItem('orbis_auto_align_behind') === 'true';
      chkAutoAlign.checked = isAuto;
      chkAutoAlign.onchange = (e) => {
        window.sceneManager?.cameraRig?.setAutoAlignBehind(e.target.checked);
        soundFX.playClick();
      };
    }

    // Quality toggle
    const btnQuality = document.getElementById('btn-toggle-quality');
    if (btnQuality) {
      btnQuality.onclick = () => {
        const current = window.sceneManager?.quality || 'high';
        const next = current === 'high' ? 'medium' : current === 'medium' ? 'low' : 'high';
        window.sceneManager?.setQuality(next);
        btnQuality.textContent = `Quality: ${next.toUpperCase()}`;
        soundFX.playClick();
      };
    }

    // Name tags toggle
    const btnTags = document.getElementById('btn-toggle-nametags');
    if (btnTags) {
      btnTags.onclick = () => {
        const isVisible = window.sceneManager?.toggleApparatusTags();
        btnTags.textContent = isVisible ? '🏷️ Name Tags: ON' : '🏷️ Name Tags: OFF';
        soundFX.playClick();
      };
    }

    // Tools & Developer buttons
    document.getElementById('btn-toggle-skip-anim')?.addEventListener('click', () => {
      state.skipAnimation = !state.skipAnimation;
      toast.showInfo(state.skipAnimation ? 'Animations Skipped' : 'Animations Normal');
      soundFX.playClick();
    });

    document.getElementById('btn-director-mode')?.addEventListener('click', () => {
      window.sceneManager?.toggleDirectorMode?.();
      this.closeMenuDrawer();
    });

    document.getElementById('btn-mistake-demo')?.addEventListener('click', () => {
      this.closeMenuDrawer();
      window.actionMenu?.triggerMistakeDemo?.();
    });

    document.getElementById('btn-open-controls')?.addEventListener('click', () => {
      this.closeMenuDrawer();
      this.toggleControlsModal(true);
    });

    document.getElementById('btn-finish-experiment')?.addEventListener('click', () => {
      this.closeMenuDrawer();
      window.actionMenu?.handleFinishExperiment?.();
    });
  }

  openMenuDrawer() {
    if (this.menuDrawer) {
      this.menuDrawer.classList.remove('hidden');
      soundFX.playClick();
    }
  }

  closeMenuDrawer() {
    if (this.menuDrawer) {
      this.menuDrawer.classList.add('hidden');
      soundFX.playClick();
    }
  }

  renderMenuStations(exp) {
    const listEl = document.getElementById('menu-stations-list');
    if (!listEl) return;
    listEl.innerHTML = '';

    const expId = exp?.id || state.experiment?.id || 'pk_ward';
    let stations = [];
    if (expId === 'pk_ward') {
      stations = [
        { id: 'digital_balance', label: '⚖️ Balance & Prep', pos: [-3.8, 0, -3.2] },
        { id: 'patient_bed', label: '🛏️ Patient Alex', pos: [3.2, 0, -3.5] },
        { id: 'tube_rack', label: '🧪 Blood Samples', pos: [-3.2, 0, -3.2] },
        { id: 'assay_analyzer', label: '🔬 Centrifuge Assay', pos: [-5.2, 0, -2.6] },
        { id: 'virtual_trial_screen', label: '👥 Virtual Trial', pos: [3.6, 0, -5.2], isTrial: true },
        { id: 'reality_check_board', label: '⚖️ Reality Check', pos: [-4.5, 0, -5.2], isRealityCheck: true },
        { id: 'sink', label: '🚰 Utility Sink', pos: [-6.2, 0, -1.0] },
        { id: 'chemical_waste_bin', label: '🗑️ Waste Disposal', pos: [2.0, 0, -4.2] },
      ];
    } else if (expId === 'dose_lab') {
      stations = [
        { id: 'infusion_pump', label: '💉 Infusion Pump', pos: [-3.5, 0, -2.2] },
        { id: 'patient_monitor', label: '🩺 Patient Telemetry', pos: [2.5, 0, -2.8] },
        { id: 'pkpd_chart_display', label: '📈 PK/PD Hologram', pos: [0.0, 0, -3.0] },
        { id: 'prediction_slate', label: '📝 Prediction Slate', pos: [-1.8, 0, -2.8] },
        { id: 'sampling_schedule', label: '🧪 Sampling Schedule', pos: [-4.5, 0, -2.8] },
        { id: 'debrief_station', label: '📋 Debrief Station', pos: [4.2, 0, -2.8] },
        { id: 'reality_check_board', label: '⚖️ Reality Check', pos: [-4.5, 0, -5.2], isRealityCheck: true },
        { id: 'sink', label: '🚰 Utility Sink', pos: [-6.2, 0, -1.0] },
      ];
    } else if (expId === 'launch_bench') {
      stations = [
        { id: 'launch_pad', label: '🚀 Launch Pad', pos: [0, 0, 4.0] },
        { id: 'flight_computer', label: '💻 Flight Computer', pos: [-3.0, 0.6, 3.8] },
        { id: 'propellant_tanks', label: '⛽ Propellant Farm', pos: [4.5, 0.6, 3.8] },
        { id: 'range_control', label: '📡 Range Control', pos: [-6.5, 0.6, 3.8] },
        { id: 'tracking_station', label: '🌐 Tracking Station', pos: [8.5, 0.6, 3.8] },
      ];
    } else {
      stations = [
        { id: 'burette', label: '🧪 Burette Stand', pos: [0, 0, -1.0] },
        { id: 'conical_flask', label: '⚗️ Conical Flask', pos: [0, 0, -1.0] },
        { id: 'pipette', label: '🧴 Reagents & Pipette', pos: [-0.8, 0, -1.0] },
        { id: 'indicator_bottles', label: '💧 pH Indicators', pos: [0.8, 0, -1.2] },
        { id: 'ph_meter', label: '⚡ Digital pH Meter', pos: [-0.5, 0, -1.2] },
        { id: 'reality_check_board', label: '⚖️ Reality Check', pos: [-4.5, 0, -5.2], isRealityCheck: true },
        { id: 'sink', label: '🚰 Utility Sink', pos: [-6.2, 0, -1.0] },
        { id: 'chemical_waste_bin', label: '🗑️ Waste Disposal', pos: [2.0, 0, -4.2] },
      ];
    }

    stations.forEach((st) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'menu-action-btn';
      btn.textContent = st.label;
      btn.onclick = () => {
        this.closeMenuDrawer();
        if (window.characterController) {
          const vPos = { x: st.pos[0], y: st.pos[1], z: st.pos[2] };
          window.characterController.moveTo(vPos);
        }
        window.sceneManager?.focusOnStation(st.id);
        if (st.isTrial) state.emit('open_trial_panel');
        if (st.isRealityCheck) state.emit('open_reality_check_panel');
        state.setSelectedTarget(st.id);
      };
      listEl.appendChild(btn);
    });
  }

  /* -------------------------------------------------------------------------
   * 4-Step Coachmarks Tutorial
   * ------------------------------------------------------------------------- */
  initCoachmarks() {
    this.coachmarksOverlay = document.getElementById('hud-coachmarks-overlay');
    this.coachmarkStep = 1;
    this.coachmarkSteps = [
      {
        badge: 'Step 1 of 4',
        title: 'Walk around the Laboratory',
        desc: 'Use WASD or Arrow keys (or the on-screen joystick on mobile) to move your scientist character across stations.',
      },
      {
        badge: 'Step 2 of 4',
        title: 'Track Performance Metrics',
        desc: 'Look at the top-right chips for elapsed time, score, and real-time safety compliance (Safety 100/100).',
      },
      {
        badge: 'Step 3 of 4',
        title: 'Current Task Card',
        desc: 'The bottom card guides your current protocol action. Click the primary button or press Tab to perform the step directly.',
      },
      {
        badge: 'Step 4 of 4',
        title: 'Ask Orbis & Dr. Orbis',
        desc: 'Use Ask Orbis (bottom-left, [/]) for autonomous planning, and Dr. Orbis (bottom-right) for expert mentor advice.',
      },
    ];

    const btnNext = document.getElementById('btn-coachmark-next');
    const btnSkip = document.getElementById('btn-coachmark-skip');

    if (btnNext) {
      btnNext.onclick = () => {
        this.coachmarkStep++;
        if (this.coachmarkStep > this.coachmarkSteps.length) {
          this.dismissCoachmarks();
        } else {
          this.renderCoachmarkStep();
        }
      };
    }

    if (btnSkip) {
      btnSkip.onclick = () => this.dismissCoachmarks();
    }
  }

  showCoachmarks() {
    if (!this.coachmarksOverlay) return;
    this.coachmarkStep = 1;
    this.renderCoachmarkStep();
    this.coachmarksOverlay.classList.remove('hidden');
  }

  renderCoachmarkStep() {
    const stepData = this.coachmarkSteps[this.coachmarkStep - 1];
    if (!stepData) return;

    const badgeEl = document.getElementById('coachmark-step-badge');
    const titleEl = document.getElementById('coachmark-title');
    const descEl = document.getElementById('coachmark-desc');
    const nextBtn = document.getElementById('btn-coachmark-next');

    if (badgeEl) badgeEl.textContent = stepData.badge;
    if (titleEl) titleEl.textContent = stepData.title;
    if (descEl) descEl.textContent = stepData.desc;
    if (nextBtn) {
      nextBtn.textContent = this.coachmarkStep === this.coachmarkSteps.length ? 'Get Started ➔' : 'Next ➔';
    }
  }

  dismissCoachmarks() {
    if (this.coachmarksOverlay) {
      this.coachmarksOverlay.classList.add('hidden');
    }
    localStorage.setItem('orbis_coachmarks_seen', 'true');
    soundFX.playClick();
  }
}
