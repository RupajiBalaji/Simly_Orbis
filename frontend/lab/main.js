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

  window.reportScreen = reportScreen;
  window.directorRunner = directorRunner;
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
  const briefScreen = document.getElementById('screen-brief');
  const errorOverlay = document.getElementById('session-error-overlay');
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
        const report = await api.finishSession(state.session.session_id);
        reportScreen.show(report);
      } catch (err) {
        toast.showInfo(`Failed to finish session: ${err.message}`);
      }
    };
  }
}

// Boot application when DOM is ready
window.addEventListener('DOMContentLoaded', initOrbisLab);
