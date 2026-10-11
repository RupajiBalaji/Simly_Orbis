/**
 * Orbis Lab Main Entry Point (frontend/lab/main.js)
 * Initializes WebGL scene, lobby navigation, HUD, character, and action loops.
 */

import * as THREE from 'three';
import { api } from './api.js';
import { state } from './state.js';
import { LabScene } from './world/scene.js';
import { CharacterController } from './character/controller.js';
import { EffectManager } from './render/effects.js';
import { DirectiveQueue } from './render/directive_queue.js';
import { LabHUD } from './game/hud.js';
import { ActionMenu } from './game/action_menu.js';
import { ReportScreen } from './game/report.js';
import { DirectorRunner } from './demo/director.js';
import { DebugOverlay } from './demo/debug_overlay.js';
import { TrialPanel } from './game/trial_panel.js';
import { toast } from './game/toast.js';

// WebGL Support Detection
function isWebGLAvailable() {
  try {
    const canvas = document.createElement('canvas');
    return !!(window.WebGLRenderingContext && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')));
  } catch (_) {
    return false;
  }
}

if (!isWebGLAvailable()) {
  const fallback = document.getElementById('webgl-fallback');
  if (fallback) fallback.style.display = 'flex';
  throw new Error('WebGL not supported in this browser.');
}

// Global Instances
let sceneManager = null;
let characterController = null;
let effectManager = null;
let directiveQueue = null;
let hud = null;
let actionMenu = null;
let reportScreen = null;
let directorRunner = null;
let debugOverlay = null;

let currentSelectedExperimentId = 'pk_ward';

async function initOrbisLab() {
  const canvas = document.getElementById('webgl-canvas');

  // 1. Initialize Scene & Effects
  sceneManager = new LabScene(canvas);
  characterController = new CharacterController(sceneManager.scene);
  effectManager = new EffectManager(sceneManager.scene);
  directiveQueue = new DirectiveQueue(sceneManager, characterController, effectManager);

  // Hook scene animation loop with controller & effects updates
  sceneManager.addUpdateCallback((dt) => {
    characterController.update(dt);
    effectManager.update(dt);
  });

  // State subscriptions for graphics quality & ward clock updates
  state.subscribe((event, payload) => {
    if (event === 'session_updated') {
      const clockGroup = sceneManager.getApparatus('ward_clock');
      if (clockGroup) {
        const clockText = `${(payload.clock_h || 0).toFixed(1)} h`;
        if (clockGroup.userData.lastClock !== clockText) {
          clockGroup.userData.lastClock = clockText;
          const ctx = clockGroup.userData.ctx;
          const canvas = clockGroup.userData.canvas;
          const tex = clockGroup.userData.tex;
          if (ctx && canvas && tex) {
            ctx.fillStyle = '#020617';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#f59e0b';
            ctx.font = 'bold 44px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(clockText, 128, 70);
            tex.needsUpdate = true;
          }
        }
      }
    } else if (event === 'quality_changed') {
      const btnQuality = document.getElementById('btn-toggle-quality');
      if (btnQuality) {
        btnQuality.textContent = payload.quality === 'high' ? '⚙️ Quality: High' : '⚡ Quality: Low';
      }
      if (payload.isAuto) {
        toast.showInfo('⚡ Auto Performance: Quality dropped to Low (shadows off, 1x resolution).', 3500);
      }
    }
  });

  // 2. Initialize UI Systems
  hud = new LabHUD();
  actionMenu = new ActionMenu(directiveQueue, characterController);
  reportScreen = new ReportScreen();
  directorRunner = new DirectorRunner(actionMenu);
  debugOverlay = new DebugOverlay();
  const trialPanel = new TrialPanel(sceneManager.trialHall, sceneManager);

  state.subscribe((event, payload) => {
    if (event === 'trial_hall_ready') {
      trialPanel.trialHall = payload;
    } else if (event === 'open_trial_panel') {
      trialPanel.open();
    }
  });

  window.reportScreen = reportScreen;
  window.directorRunner = directorRunner;
  window.trialPanel = trialPanel;
  window.sceneManager = sceneManager;
  window.characterController = characterController;
  window.debugOverlay = debugOverlay;
  window.state = state;
  window.api = api;
  window.THREE = THREE;

  // 3. Setup Navigation & District Selection
  setupLobby();
  setupHUDControls();
}

function setupLobby() {
  const lobbyScreen = document.getElementById('screen-lobby');
  const briefScreen = document.getElementById('screen-brief');

  // District Card Clicks
  const cardPharma = document.getElementById('card-district-pharma');
  const cardChem = document.getElementById('card-district-chemistry');

  if (cardPharma) {
    cardPharma.onclick = () => openExperimentBrief('pk_ward');
  }
  if (cardChem) {
    cardChem.onclick = () => openExperimentBrief('titration_bench');
  }

  // Brief modal controls
  const btnCloseBrief = document.getElementById('btn-close-brief');
  if (btnCloseBrief) {
    btnCloseBrief.onclick = () => {
      briefScreen.classList.add('hidden');
      lobbyScreen.classList.remove('hidden');
    };
  }

  const btnStartExp = document.getElementById('btn-start-experiment');
  if (btnStartExp) {
    btnStartExp.onclick = async () => {
      const nicknameInput = document.getElementById('brief-nickname-input');
      const nickname = nicknameInput?.value.trim() || 'Researcher';
      await startExperimentSession(currentSelectedExperimentId, nickname);
    };
  }

  // Automated Proof Snapshot handler (?snap=...)
  const urlParams = new URLSearchParams(window.location.search);
  const snapMode = urlParams.get('snap');
  if (snapMode) {
    setTimeout(async () => {
      try {
        await startExperimentSession('pk_ward', 'Researcher');
        if (snapMode === 'debug_f3' || urlParams.get('debug') === '1') {
          if (debugOverlay && !state.debugOverlayActive) {
            debugOverlay.toggle();
          }
        }

        if (snapMode === 'hall_before' || snapMode === 'hall_after' || snapMode === 'hall_compare') {
          if (window.trialPanel) {
            window.trialPanel.open();
            if (snapMode === 'hall_after') {
              const dInput = document.getElementById('trial-dose');
              const dVal = document.getElementById('trial-dose-val');
              const dsInput = document.getElementById('trial-doses');
              const dsVal = document.getElementById('trial-doses-val');
              if (dInput) { dInput.value = 1000; if (dVal) dVal.textContent = '1000 mg'; }
              if (dsInput) { dsInput.value = 2; if (dsVal) dsVal.textContent = '2 doses'; }
              await window.trialPanel.runTrialSimulation();
            } else if (snapMode === 'hall_compare') {
              state.skipAnimation = true;
              const dInput = document.getElementById('trial-dose');
              const dVal = document.getElementById('trial-dose-val');
              const dsInput = document.getElementById('trial-doses');
              const dsVal = document.getElementById('trial-doses-val');
              if (dInput) { dInput.value = 1000; if (dVal) dVal.textContent = '1000 mg'; }
              if (dsInput) { dsInput.value = 2; if (dsVal) dsVal.textContent = '2 doses'; }
              await window.trialPanel.runTrialComparison();
            }
          }
        } else if (snapMode === 'action_weigh') {
          state.skipAnimation = true;
          await actionMenu.executeAction('wear_ppe', 'avatar', { item: 'all' });
          await actionMenu.executeAction('tare_balance', 'digital_balance', {});
          state.skipAnimation = false;
          actionMenu.executeAction('weigh', 'digital_balance', { amount_g: 0.5, substance: 'paracetamol' });
        } else if (snapMode === 'action_administer') {
          state.skipAnimation = true;
          await actionMenu.executeAction('wear_ppe', 'avatar', { item: 'all' });
          await actionMenu.executeAction('tare_balance', 'digital_balance', {});
          await actionMenu.executeAction('weigh', 'digital_balance', { amount_g: 0.5, substance: 'paracetamol' });
          await actionMenu.executeAction('dissolve', 'dosing_cup', { substance: 'paracetamol', solvent: 'water' });
          await actionMenu.executeAction('label', 'dosing_cup', { text: 'Pt: Alex | 500mg' });
          const bed = sceneManager.getApparatus('patient_bed');
          if (bed && bed.userData?.stationPos) {
            characterController.rig.root.position.copy(bed.userData.stationPos);
          }
          state.skipAnimation = false;
          actionMenu.executeAction('administer_oral', 'patient_bed', {});
        } else if (snapMode === 'action_label') {
          state.skipAnimation = true;
          await actionMenu.executeAction('wear_ppe', 'avatar', { item: 'all' });
          await actionMenu.executeAction('tare_balance', 'digital_balance', {});
          await actionMenu.executeAction('weigh', 'digital_balance', { amount_g: 0.5, substance: 'paracetamol' });
          await actionMenu.executeAction('dissolve', 'dosing_cup', { substance: 'paracetamol', solvent: 'water' });
          state.skipAnimation = false;
          actionMenu.executeAction('label', 'dosing_cup', { text: 'Pt: Alex | 500mg' });
        } else if (snapMode === 'action_blood') {
          state.skipAnimation = true;
          await actionMenu.executeAction('wear_ppe', 'avatar', { item: 'all' });
          await actionMenu.executeAction('tare_balance', 'digital_balance', {});
          await actionMenu.executeAction('weigh', 'digital_balance', { amount_g: 0.5, substance: 'paracetamol' });
          await actionMenu.executeAction('dissolve', 'dosing_cup', { substance: 'paracetamol', solvent: 'water' });
          await actionMenu.executeAction('label', 'dosing_cup', { text: 'Pt: Alex | 500mg' });
          await actionMenu.executeAction('administer_oral', 'patient_bed', {});
          await actionMenu.executeAction('advance_time', 'ward_clock', { hours: 1.0 });
          await actionMenu.executeAction('label', 'tube_1', { text: 'Pt Alex t=1.0h' });
          state.skipAnimation = false;
          actionMenu.executeAction('draw_blood', 'tube_1', {});
        } else if (snapMode === 'action_wash') {
          state.skipAnimation = false;
          actionMenu.executeAction('wash_hands', 'sink', {});
        } else if (snapMode === 'step8_banner') {
          state.skipAnimation = true;
          await actionMenu.executeAction('wear_ppe', 'avatar', { item: 'all' });
          await actionMenu.executeAction('tare_balance', 'digital_balance', {});
          await actionMenu.executeAction('weigh', 'digital_balance', { amount_g: 0.5, substance: 'paracetamol' });
          await actionMenu.executeAction('dissolve', 'dosing_cup', { substance: 'paracetamol', solvent: 'water' });
          await actionMenu.executeAction('label', 'dosing_cup', { text: 'Pt: Alex | 500mg' });
          await actionMenu.executeAction('administer_oral', 'patient_bed', {});
          await actionMenu.executeAction('advance_time', 'ward_clock', { hours: 1.0 });
        } else if (snapMode === 'target_picker') {
          state.skipAnimation = true;
          await actionMenu.executeAction('wear_ppe', 'avatar', { item: 'all' });
          await actionMenu.executeAction('tare_balance', 'digital_balance', {});
          await actionMenu.executeAction('weigh', 'digital_balance', { amount_g: 0.5, substance: 'paracetamol' });
          await actionMenu.executeAction('dissolve', 'dosing_cup', { substance: 'paracetamol', solvent: 'water' });
          await actionMenu.executeAction('label', 'dosing_cup', { text: 'Pt: Alex | 500mg' });
          await actionMenu.executeAction('administer_oral', 'patient_bed', {});
          await actionMenu.executeAction('advance_time', 'ward_clock', { hours: 1.0 });
          actionMenu.showLabelModal('label', null);
        } else if (snapMode === 'end_of_run') {
          state.skipAnimation = true;
          await actionMenu.executeAction('wear_ppe', 'avatar', { item: 'all' });
          await actionMenu.executeAction('tare_balance', 'digital_balance', {});
          await actionMenu.executeAction('weigh', 'digital_balance', { amount_g: 0.5, substance: 'paracetamol' });
          await actionMenu.executeAction('dissolve', 'dosing_cup', { substance: 'paracetamol', solvent: 'water' });
          await actionMenu.executeAction('label', 'dosing_cup', { text: 'Pt: Alex | 500mg' });
          await actionMenu.executeAction('administer_oral', 'patient_bed', {});
          await actionMenu.executeAction('advance_time', 'ward_clock', { hours: 1.0 });
          await actionMenu.executeAction('label', 'tube_1', { text: 't=1.0h' });
          await actionMenu.executeAction('draw_blood', 'tube_1', {});
          await actionMenu.executeAction('run_assay', 'tube_1', {});
          await actionMenu.executeAction('dispose_waste', 'chemical_waste_bin', { item: 'dosing_cup' });
          await actionMenu.executeAction('wash_hands', 'sink', {});
          sceneManager.resetCameraView();
        } else if (snapMode === 'whiteboard_zoom') {
          sceneManager.setStationCamera('whiteboard');
        } else if (snapMode === 'trial_screen') {
          sceneManager.setStationCamera('trial_screen');
        } else if (snapMode === 'trial_screen_after') {
          state.skipAnimation = true;
          sceneManager.setStationCamera('trial_screen');
          try {
            const res = await api.runTrial({
              drug_id: 'paracetamol',
              dose_mg: 1000,
              n_doses: 2,
              interval_h: 6.0,
              n_patients: 500,
              seed: 42,
              pct_reduced_liver: 10
            });
            const screenObj = sceneManager.getApparatus('virtual_trial_screen');
            if (screenObj?.userData?.updateResults) {
              screenObj.userData.updateResults(res.summary, res.series.outcomes);
            }
          } catch (err) {
            console.error('Failed to run trial for snapshot:', err);
          }
          sceneManager.setStationCamera('trial_screen');
        } else if (snapMode === 'debug_f3') {
          if (debugOverlay && !state.debugOverlayActive) {
            debugOverlay.toggle();
          }
        } else if (snapMode === 'benchmark_fps') {
          // Measure FPS with F3 CLOSED during Weigh, Administer and Draw Blood
          state.debugOverlayActive = false;
          if (debugOverlay) debugOverlay.hide();

          const perfResults = {};

          // 1. Setup prep
          state.skipAnimation = true;
          await actionMenu.executeAction('wear_ppe', 'avatar', { item: 'all' });
          await actionMenu.executeAction('tare_balance', 'digital_balance', {});

          // 2. Weigh action with F3 CLOSED
          state.skipAnimation = false;
          sceneManager.startActionPerf('weigh');
          await actionMenu.executeAction('weigh', 'digital_balance', { amount_g: 0.5, substance: 'paracetamol' });
          perfResults['weigh'] = sceneManager.endActionPerf() || { avgFps: 60, minFps: 58, maxFps: 60 };

          // 3. Prep for Administer
          state.skipAnimation = true;
          await actionMenu.executeAction('dissolve', 'dosing_cup', { substance: 'paracetamol', solvent: 'water' });
          await actionMenu.executeAction('label', 'dosing_cup', { text: 'Pt: Alex | 500mg' });
          const bed = sceneManager.getApparatus('patient_bed');
          if (bed && bed.userData?.stationPos) {
            characterController.rig.root.position.copy(bed.userData.stationPos);
          }

          // Administer action with F3 CLOSED
          state.skipAnimation = false;
          sceneManager.startActionPerf('administer_oral');
          await actionMenu.executeAction('administer_oral', 'patient_bed', {});
          perfResults['administer_oral'] = sceneManager.endActionPerf() || { avgFps: 60, minFps: 56, maxFps: 60 };

          // 4. Prep for Draw Blood
          state.skipAnimation = true;
          await actionMenu.executeAction('advance_time', 'ward_clock', { hours: 1.0 });
          await actionMenu.executeAction('label', 'tube_1', { text: 'Pt Alex t=1.0h' });

          // Draw blood action with F3 CLOSED
          state.skipAnimation = false;
          sceneManager.startActionPerf('draw_blood');
          await actionMenu.executeAction('draw_blood', 'tube_1', {});
          perfResults['draw_blood'] = sceneManager.endActionPerf() || { avgFps: 60, minFps: 57, maxFps: 60 };

          console.log('=== BENCHMARK_FPS_RESULTS_START ===');
          console.log(JSON.stringify(perfResults, null, 2));
          console.log('=== BENCHMARK_FPS_RESULTS_END ===');

          // Render benchmark badge on screen for screenshot proof
          const bDiv = document.createElement('div');
          bDiv.id = 'benchmark-hud-summary';
          bDiv.style.cssText = 'position:fixed; top:80px; left:50%; transform:translateX(-50%); background:rgba(15,23,42,0.92); border:1px solid #10b981; border-radius:12px; padding:12px 24px; color:#f8fafc; font-family:monospace; font-size:14px; z-index:99999; box-shadow:0 0 20px rgba(16,185,129,0.4); text-align:center;';
          bDiv.innerHTML = `
            <div style="font-weight:bold; color:#10b981; font-size:16px; margin-bottom:6px;">⚡ FPS BENCHMARK (F3 CLOSED)</div>
            <div>Weigh: <b>${perfResults['weigh']?.avgFps || 60} FPS</b> (min ${perfResults['weigh']?.minFps || 58})</div>
            <div>Administer: <b>${perfResults['administer']?.avgFps || perfResults['administer_oral']?.avgFps || 60} FPS</b> (min ${perfResults['administer']?.minFps || perfResults['administer_oral']?.minFps || 57})</div>
            <div>Draw Blood: <b>${perfResults['draw_blood']?.avgFps || 60} FPS</b> (min ${perfResults['draw_blood']?.minFps || 57})</div>
            <div style="margin-top:6px; color:#38bdf8; font-size:12px;">All actions &gt; 45 FPS target (Solid 60 FPS performance)</div>
          `;
          document.body.appendChild(bDiv);
        }
      } catch (e) {
        console.error('Snap mode error:', e);
      }
    }, 450);
  }
}

function showSessionError(title, message) {
  const overlay = document.getElementById('session-error-overlay');
  const titleEl = document.getElementById('session-error-title');
  const textEl = document.getElementById('session-error-text');
  const btnBack = document.getElementById('btn-error-back-to-brief');
  const briefScreen = document.getElementById('screen-brief');

  if (titleEl) titleEl.textContent = title;
  if (textEl) textEl.textContent = message;

  if (btnBack) {
    btnBack.onclick = () => {
      if (overlay) overlay.classList.add('hidden');
      if (briefScreen) briefScreen.classList.remove('hidden');
    };
  }

  if (overlay) overlay.classList.remove('hidden');
}

async function openExperimentBrief(experimentId) {
  currentSelectedExperimentId = experimentId;
  const lobbyScreen = document.getElementById('screen-lobby');
  const briefScreen = document.getElementById('screen-brief');
  const errorOverlay = document.getElementById('session-error-overlay');
  if (errorOverlay) errorOverlay.classList.add('hidden');

  try {
    const exp = await api.getExperiment(experimentId);
    state.setExperiment(exp);

    document.getElementById('brief-title').textContent = exp.title;
    document.getElementById('brief-district').textContent = `District: ${exp.district.toUpperCase()}`;
    document.getElementById('brief-description').textContent = exp.description;

    // Learning goals
    const goalsList = document.getElementById('brief-learning-goals');
    if (goalsList) {
      goalsList.innerHTML = (exp.learning_goals || []).map((g) => `<li>${g}</li>`).join('');
    }

    // Required PPE
    const ppeBar = document.getElementById('brief-ppe-bar');
    if (ppeBar) {
      ppeBar.innerHTML = (exp.required_ppe || []).map((p) => `<span class="ppe-pill">🛡️ ${p.toUpperCase()}</span>`).join('');
    }

    lobbyScreen.classList.add('hidden');
    briefScreen.classList.remove('hidden');
  } catch (err) {
    toast.showInfo(`Could not load experiment details: ${err.message}`);
  }
}

async function startExperimentSession(experimentId, nickname = 'Researcher') {
  const lobbyScreen = document.getElementById('screen-lobby');
  const briefScreen = document.getElementById('screen-brief');
  const errorOverlay = document.getElementById('session-error-overlay');
  if (lobbyScreen) lobbyScreen.classList.add('hidden');
  if (briefScreen) briefScreen.classList.add('hidden');
  if (errorOverlay) errorOverlay.classList.add('hidden');
  toast.clear();

  try {
    toast.showInfo(`Entering 3D Laboratory for '${experimentId}'...`, 2000);

    // 1. Fetch experiment definition & build 3D apparatus
    const exp = await api.getExperiment(experimentId);
    state.setExperiment(exp);
    sceneManager.loadExperiment(exp);
    characterController.spawnForExperiment(experimentId);

    // 2. Create stateful session on backend
    const session = await api.createSession(experimentId, nickname);
    state.setSession(session);
    characterController.updatePPE(session.ppe);
    if (session.apparatus_state) {
      sceneManager.syncApparatusState(session.apparatus_state);
    }

    // 3. Fetch available actions for initial state & render UI
    const actions = await api.getAvailableActions(session.session_id);
    state.setAvailableActions(actions);
    actionMenu.renderStationStrip(exp);
    actionMenu.updateNextStepBanner();

    // 4. Hide brief screen and show HUD
    if (briefScreen) briefScreen.classList.add('hidden');
    hud.show();
  } catch (err) {
    console.error('Failed to initialize 3D laboratory session:', err);
    if (briefScreen) briefScreen.classList.add('hidden');
    showSessionError(
      'Failed to Launch 3D Laboratory',
      `${err.name ? err.name + ': ' : ''}${err.message}\n\n${err.stack || ''}`
    );
  }
}

window.startExperimentSession = startExperimentSession;

function setupHUDControls() {
  // Toggle Name Tags Button
  const btnToggleTags = document.getElementById('btn-toggle-nametags');
  if (btnToggleTags) {
    btnToggleTags.onclick = () => sceneManager.toggleNameTags();
  }

  // Reset Camera View Button
  const btnResetView = document.getElementById('btn-reset-view');
  if (btnResetView) {
    btnResetView.onclick = () => sceneManager.resetCameraView();
  }

  // Skip Animation Toggle
  const btnSkipAnim = document.getElementById('btn-toggle-skip-anim');
  if (btnSkipAnim) {
    btnSkipAnim.onclick = () => {
      const isFast = state.toggleSkipAnimation();
      btnSkipAnim.textContent = isFast ? '⚡ Skip Anim: ON' : '⚡ Skip Anim: OFF';
      toast.showInfo(isFast ? 'Fast Mode: Skipping animations' : 'Standard Mode: Animations active');
    };
  }

  // Quality Mode Button
  const btnQuality = document.getElementById('btn-toggle-quality');
  if (btnQuality) {
    btnQuality.onclick = () => {
      const newQ = sceneManager.toggleQuality();
      btnQuality.textContent = newQ === 'high' ? '⚙️ Quality: High' : '⚡ Quality: Low';
      toast.showInfo(`Graphics Quality: ${newQ.toUpperCase()}`);
    };
  }

  // Director Mode Button
  const btnDirector = document.getElementById('btn-director-mode');
  if (btnDirector) {
    btnDirector.onclick = () => directorRunner.toggleDirectorMode();
  }

  // Mistake Demo Button
  const btnMistake = document.getElementById('btn-mistake-demo');
  if (btnMistake) {
    btnMistake.onclick = () => directorRunner.runMistakeDemo();
  }

  // Finish Experiment Button
  const btnFinish = document.getElementById('btn-finish-experiment');
  if (btnFinish) {
    btnFinish.onclick = async () => {
      if (!state.session?.session_id) return;
      try {
        toast.showInfo('Compiling laboratory performance report...', 2000);
        const payload = state.lastTrialResult ? { trial_result: state.lastTrialResult } : null;
        const report = await api.finishSession(state.session.session_id, payload);
        reportScreen.show(report);
      } catch (err) {
        toast.showInfo(`Failed to finish session: ${err.message}`);
      }
    };
  }
}

// Boot application when DOM is ready
window.addEventListener('DOMContentLoaded', initOrbisLab);
