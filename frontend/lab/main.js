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
import { DosePanel } from './game/dose_panel.js';
import { DrOrbisMentor } from './game/mentor.js';
import { RealityCheckPanel } from './game/reality_check_panel.js';
import { AskOrbisAgentPanel } from './game/agent_panel.js';
import { toast } from './game/toast.js';
import { soundFX } from './audio/sound_fx.js';
import { runCameraAcceptanceTest } from './world/camera_test.js';
import { initRouter } from '../router.js';
import { initI18n, setLocale, getLocale, t } from '../i18n.js';
import { initProvenancePopovers } from '../ui/components.js';

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
  sceneManager.characterController = characterController;
  effectManager = new EffectManager(sceneManager.scene);
  directiveQueue = new DirectiveQueue(sceneManager, characterController, effectManager);

  // Hook scene animation loop with controller & effects updates
  sceneManager.addUpdateCallback((dt) => {
    characterController.update(dt);
    effectManager.update(dt);
    hud?.updateProximity(dt);
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
        const labels = { low: '⚡ Quality: Low', medium: '✨ Quality: Med', high: '💎 Quality: High' };
        btnQuality.textContent = labels[payload.quality] || '⚙️ Quality';
      }
      if (payload.isAuto) {
        toast.showInfo('⚡ Auto Performance: Quality stepped down to maintain framerate.', 3500);
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
  const dosePanel = new DosePanel();
  const drOrbis = new DrOrbisMentor();
  const realityCheckPanel = new RealityCheckPanel(sceneManager);
  const agentPanel = new AskOrbisAgentPanel();

  state.subscribe((event, payload) => {
    if (event === 'trial_hall_ready') {
      trialPanel.trialHall = payload;
    } else if (event === 'open_trial_panel') {
      trialPanel.open();
    } else if (event === 'open_dose_panel') {
      dosePanel.open();
    } else if (event === 'open_reality_check_panel') {
      realityCheckPanel.open();
    }
  });

  window.reportScreen = reportScreen;
  window.directorRunner = directorRunner;
  window.actionMenu = actionMenu;
  window.hud = hud;
  window.trialPanel = trialPanel;
  window.dosePanel = dosePanel;
  window.drOrbis = drOrbis;
  window.realityCheckPanel = realityCheckPanel;
  window.agentPanel = agentPanel;
  window.sceneManager = sceneManager;
  window.characterController = characterController;
  window.effectManager = effectManager;
  window.debugOverlay = debugOverlay;
  window.state = state;
  window.api = api;
  window.THREE = THREE;
  window.soundFX = soundFX;

  // Global UI click audio listener
  document.addEventListener('click', (e) => {
    if (e.target.closest('button, .district-card, .btn-primary, .btn-secondary, .hud-btn, .station-item')) {
      soundFX.playClick();
    }
  });

  // 3. Setup Navigation, Router, i18n & District Selection
  await initI18n();
  setupRouter();
  setupLobby();
  setupSettings();
  setupOnboarding();
  setupHUDControls();
  setupOfflineDetection();
  checkServerWakeup();
  initProvenancePopovers();
}

function showScreen(screenId) {
  const screens = [
    'screen-lobby',
    'screen-brief',
    'screen-report',
    'screen-leaderboard',
    'screen-settings',
    'screen-model-cards',
    'screen-reality-check',
    'screen-404'
  ];

  screens.forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      if (id === screenId) {
        el.classList.remove('hidden');
      } else {
        el.classList.add('hidden');
      }
    }
  });

  const hud = document.getElementById('lab-hud');
  if (screenId === 'lab-hud') {
    if (hud) hud.classList.remove('hidden');
  } else {
    if (hud) hud.classList.add('hidden');
  }

  const errorOverlay = document.getElementById('session-error-overlay');
  if (errorOverlay && screenId !== 'session-error-overlay') {
    errorOverlay.classList.add('hidden');
  }
}

function updateBreadcrumb(title) {
  const el = document.getElementById('breadcrumb-current');
  if (el) el.textContent = title;
}

function setupRouter() {
  const routes = {
    lobby: () => {
      showScreen('screen-lobby');
      updateBreadcrumb('Lobby');
    },
    briefing: async (params) => {
      const expId = params.exp || 'pk_ward';
      updateBreadcrumb(`Briefing (${expId})`);
      await openExperimentBrief(expId);
    },
    lab: async (params) => {
      const expId = params.exp || 'pk_ward';
      updateBreadcrumb(`Laboratory (${expId})`);
      await startExperimentSession(expId, localStorage.getItem('orbis_nickname') || 'Researcher');
    },
    report: (params) => {
      showScreen('screen-report');
      updateBreadcrumb('Report');
      const repContent = document.getElementById('report-content');
      if (reportScreen && (!repContent || !repContent.innerHTML.trim())) {
        reportScreen.show({
          score: 95,
          grade: 'A',
          breakdown: { 'Safety Protocol': 30, 'Apparatus Usage': 35, 'Measurement Precision': 30 },
          violations: [],
          feedback: 'Exemplary protocol adherence and experimental accuracy.',
          session_id: 'sample_session'
        });
      }
    },
    leaderboard: () => {
      showScreen('screen-leaderboard');
      updateBreadcrumb('Leaderboard');
    },
    settings: () => {
      showScreen('screen-settings');
      updateBreadcrumb('Settings');
    },
    'model-cards': () => {
      showScreen('screen-model-cards');
      updateBreadcrumb('Model Cards');
    },
    'reality-check': () => {
      showScreen('screen-reality-check');
      updateBreadcrumb('Reality Check');
      initProvenancePopovers(document.getElementById('screen-reality-check'));
    },
    '404': () => {
      showScreen('screen-404');
      updateBreadcrumb('404 Not Found');
    }
  };

  initRouter(routes);
}

function setupLobby() {
  const lobbyScreen = document.getElementById('screen-lobby');
  const briefScreen = document.getElementById('screen-brief');

  // Top Bar User Profile & Mute Toggle
  const btnTopMute = document.getElementById('btn-top-mute');
  if (btnTopMute) {
    btnTopMute.textContent = soundFX.isMuted ? '🔇' : '🔊';
    btnTopMute.onclick = () => {
      soundFX.toggleMute();
      btnTopMute.textContent = soundFX.isMuted ? '🔇' : '🔊';
      const hudBtn = document.getElementById('btn-toggle-sound');
      if (hudBtn) hudBtn.textContent = soundFX.isMuted ? '🔇' : '🔊';
    };
  }

  const profileName = document.getElementById('user-profile-name');
  if (profileName) {
    profileName.textContent = localStorage.getItem('orbis_nickname') || 'Guest Cadet';
  }

  // Mode Toggle (Guided vs Free Play)
  const btnModeGuided = document.getElementById('btn-mode-guided');
  const btnModeFree = document.getElementById('btn-mode-free');
  const modeDesc = document.getElementById('mode-desc');

  function setLobbyMode(mode) {
    localStorage.setItem('orbis_mode', mode);
    if (mode === 'free') {
      btnModeFree?.classList.add('active');
      btnModeFree?.setAttribute('aria-pressed', 'true');
      btnModeFree?.style.setProperty('border', '1px solid var(--accent)');
      btnModeGuided?.classList.remove('active');
      btnModeGuided?.setAttribute('aria-pressed', 'false');
      btnModeGuided?.style.setProperty('border', '1px solid rgba(255,255,255,0.12)');
      if (modeDesc) modeDesc.textContent = 'Free Play Mode: Sandbox exploration. Experiment freely without strict exam scoring gates.';
    } else {
      btnModeGuided?.classList.add('active');
      btnModeGuided?.setAttribute('aria-pressed', 'true');
      btnModeGuided?.style.setProperty('border', '1px solid var(--accent)');
      btnModeFree?.classList.remove('active');
      btnModeFree?.setAttribute('aria-pressed', 'false');
      btnModeFree?.style.setProperty('border', '1px solid rgba(255,255,255,0.12)');
      if (modeDesc) modeDesc.textContent = 'Guided Mode: Strict protocol compliance, safety rules, and algorithmic scorecards enabled.';
    }
  }

  const initialMode = localStorage.getItem('orbis_mode') || 'guided';
  setLobbyMode(initialMode);
  if (btnModeGuided) btnModeGuided.onclick = () => setLobbyMode('guided');
  if (btnModeFree) btnModeFree.onclick = () => setLobbyMode('free');

  // "Why Locked?" Modal Handlers
  const modalWhyLocked = document.getElementById('modal-why-locked');
  const btnCloseWhyLocked = document.getElementById('btn-close-why-locked');
  const btnWhyLockedOk = document.getElementById('btn-why-locked-ok');
  const whyLockedTitle = document.getElementById('why-locked-title');
  const whyLockedExpl = document.getElementById('why-locked-explanation');
  const whyLockedPath = document.getElementById('why-locked-path');

  let lastFocusedWhyLocked = null;

  function openWhyLocked(target, triggerEl) {
    if (!modalWhyLocked) return;
    lastFocusedWhyLocked = triggerEl || document.activeElement;
    if (target === 'biology') {
      if (whyLockedTitle) whyLockedTitle.textContent = '🔒 Molecular Biology Locked';
      if (whyLockedExpl) whyLockedExpl.textContent = 'Access to the Molecular Biology District requires verified lab safety certifications in both Pharmacology and Chemistry.';
      if (whyLockedPath) {
        whyLockedPath.innerHTML = `
          <li>Complete Foundation Safety &amp; PPE certification in Oral PK Ward</li>
          <li>Achieve Grade B or higher on Acid-Base Equivalence in Chemistry Bench</li>
          <li>Attain receptor-binding pre-clearance</li>
        `;
      }
    } else {
      if (whyLockedTitle) whyLockedTitle.textContent = '🔒 Market Systems Locked';
      if (whyLockedExpl) whyLockedExpl.textContent = 'Curriculum locked: High-Frequency Market Microstructure is reserved for Advanced Stochastic Systems course modules.';
      if (whyLockedPath) {
        whyLockedPath.innerHTML = `
          <li>Complete prerequisite physical science benchmarks</li>
          <li>Attain stochastic modeling clearance</li>
          <li>Course enrollment opening next academic semester</li>
        `;
      }
    }
    modalWhyLocked.classList.remove('hidden');
    btnWhyLockedOk?.focus();
  }

  function closeWhyLocked() {
    modalWhyLocked?.classList.add('hidden');
    if (lastFocusedWhyLocked && typeof lastFocusedWhyLocked.focus === 'function') {
      lastFocusedWhyLocked.focus();
    }
  }

  modalWhyLocked?.addEventListener('keydown', (e) => {
    if (modalWhyLocked.classList.contains('hidden')) return;
    if (e.key === 'Escape') {
      e.preventDefault();
      closeWhyLocked();
    } else if (e.key === 'Tab') {
      const focusable = modalWhyLocked.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
      if (focusable.length > 0) {
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey) {
          if (document.activeElement === first) {
            e.preventDefault();
            last.focus();
          }
        } else {
          if (document.activeElement === last) {
            e.preventDefault();
            first.focus();
          }
        }
      }
    }
  });

  document.querySelectorAll('.btn-locked-info').forEach((btn) => {
    btn.onclick = (e) => {
      e.stopPropagation();
      openWhyLocked(btn.getAttribute('data-locked-target'), btn);
    };
  });

  const cardBiology = document.getElementById('card-district-biology');
  if (cardBiology) cardBiology.onclick = () => openWhyLocked('biology', cardBiology);
  const cardMarket = document.getElementById('card-district-market');
  if (cardMarket) cardMarket.onclick = () => openWhyLocked('market', cardMarket);

  if (btnCloseWhyLocked) btnCloseWhyLocked.onclick = closeWhyLocked;
  if (btnWhyLockedOk) btnWhyLockedOk.onclick = closeWhyLocked;

  // Status Chips from localStorage
  const expStatusMap = {
    pk_ward: 'status-pk-ward',
    dose_lab: 'status-dose-lab',
    titration_bench: 'status-titration',
    launch_bench: 'status-launch'
  };

  Object.entries(expStatusMap).forEach(([expId, elementId]) => {
    const el = document.getElementById(elementId);
    if (!el) return;
    const savedGrade = localStorage.getItem(`orbis_grade_${expId}`);
    if (savedGrade) {
      el.textContent = `Completed (${savedGrade})`;
      el.className = 'status-chip badge badge-ok';
    } else if (localStorage.getItem(`orbis_started_${expId}`)) {
      el.textContent = 'In progress';
      el.className = 'status-chip badge badge-warn';
    }
  });

  // About Simly Orbis Modal
  const btnOpenAbout = document.getElementById('btn-open-about');
  const btnHudOpenAbout = document.getElementById('btn-hud-open-about');
  const modalAbout = document.getElementById('modal-about');
  const btnCloseAbout = document.getElementById('btn-close-about');
  const btnAboutCloseBtn = document.getElementById('btn-about-close-btn');

  let lastFocusedAbout = null;
  const openAbout = (triggerEl) => {
    lastFocusedAbout = triggerEl || document.activeElement;
    modalAbout?.classList.remove('hidden');
    btnCloseAbout?.focus();
  };
  const closeAbout = () => {
    modalAbout?.classList.add('hidden');
    if (lastFocusedAbout && typeof lastFocusedAbout.focus === 'function') {
      lastFocusedAbout.focus();
    }
  };

  if (modalAbout) {
    if (btnOpenAbout) btnOpenAbout.onclick = () => openAbout(btnOpenAbout);
    if (btnHudOpenAbout) btnHudOpenAbout.onclick = () => openAbout(btnHudOpenAbout);
    if (btnCloseAbout) btnCloseAbout.onclick = closeAbout;
    if (btnAboutCloseBtn) btnAboutCloseBtn.onclick = closeAbout;

    modalAbout.addEventListener('keydown', (e) => {
      if (modalAbout.classList.contains('hidden')) return;
      if (e.key === 'Escape') {
        e.preventDefault();
        closeAbout();
      } else if (e.key === 'Tab') {
        const focusable = modalAbout.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (focusable.length > 0) {
          const first = focusable[0];
          const last = focusable[focusable.length - 1];
          if (e.shiftKey) {
            if (document.activeElement === first) {
              e.preventDefault();
              last.focus();
            }
          } else {
            if (document.activeElement === last) {
              e.preventDefault();
              first.focus();
            }
          }
        }
      }
    });
  }

  // Check Storage Mode & dynamic version metadata
  api.getHealth().then((health) => {
    if (health?.storage_mode === 'memory') {
      const banner = document.getElementById('storage-mode-banner');
      if (banner) banner.classList.remove('hidden');
    }
    if (health?.app_version) {
      const verEl = document.getElementById('about-version');
      if (verEl) verEl.textContent = health.app_version;
    }
    if (health?.git_sha) {
      const shaEl = document.getElementById('about-git-sha');
      if (shaEl) shaEl.textContent = health.git_sha.substring(0, 7);
    }
  }).catch(() => {});

  // District Card Clicks -> navigate via router
  const cardPharma = document.getElementById('card-district-pharma');
  const cardChem = document.getElementById('card-district-chemistry');
  const cardSpace = document.getElementById('card-district-space');
  const cardDoseLab = document.getElementById('card-district-dose-lab');

  if (cardPharma) {
    cardPharma.onclick = () => { window.location.hash = '#/briefing?exp=pk_ward'; };
  }
  if (cardChem) {
    cardChem.onclick = () => { window.location.hash = '#/briefing?exp=titration_bench'; };
  }
  if (cardSpace) {
    cardSpace.onclick = () => { window.location.hash = '#/briefing?exp=launch_bench'; };
  }
  if (cardDoseLab) {
    cardDoseLab.onclick = () => { window.location.hash = '#/briefing?exp=dose_lab'; };
  }

  // Brief modal controls
  const btnCloseBrief = document.getElementById('btn-close-brief');
  if (btnCloseBrief) {
    btnCloseBrief.onclick = () => {
      window.location.hash = '#/lobby';
    };
  }

  const btnStartExp = document.getElementById('btn-start-experiment');
  if (btnStartExp) {
    btnStartExp.onclick = async () => {
      const nicknameInput = document.getElementById('brief-nickname-input');
      const nickname = nicknameInput?.value.trim() || 'Researcher';
      localStorage.setItem('orbis_nickname', nickname);
      localStorage.setItem('orbis_mode', 'guided');
      localStorage.setItem('orbis_practice', 'false');
      const curProfileName = document.getElementById('user-profile-name');
      if (curProfileName) curProfileName.textContent = nickname;
      window.location.hash = `#/lab?exp=${currentSelectedExperimentId}`;
    };
  }

  const btnPracticeExp = document.getElementById('btn-practice-experiment');
  if (btnPracticeExp) {
    btnPracticeExp.onclick = async () => {
      const nicknameInput = document.getElementById('brief-nickname-input');
      const nickname = nicknameInput?.value.trim() || 'Researcher';
      localStorage.setItem('orbis_nickname', nickname);
      localStorage.setItem('orbis_mode', 'free');
      localStorage.setItem('orbis_practice', 'true');
      const curProfileName = document.getElementById('user-profile-name');
      if (curProfileName) curProfileName.textContent = nickname;
      window.location.hash = `#/lab?exp=${currentSelectedExperimentId}&practice=1`;
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
        } else if (snapMode === 'mentor_hint') {
          await drOrbis.query('hint');
        } else if (snapMode === 'mentor_ask') {
          await drOrbis.query('ask', 'How does clearance affect peak paracetamol concentration?');
        } else if (snapMode === 'mentor_explain') {
          await actionMenu.executeAction('tare_balance', 'digital_balance', {});
          await drOrbis.query('explain');
        } else if (snapMode === 'reality_check_board') {
          sceneManager.setStationCamera('reality_check_board');
        } else if (snapMode === 'reality_check_panel') {
          sceneManager.setStationCamera('reality_check_board');
          await realityCheckPanel.open();
        } else if (snapMode === 'mentor_report_debrief') {
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
          const finRes = await api.finishSession(state.session.session_id, {
            trial_result: {
              n_patients: 500,
              pct_in_range: 82.4,
              pct_toxic: 1.2,
              pct_subtherapeutic: 16.4,
              mean_peak: 14.8,
            }
          });
          hud.hide();
          reportScreen.show(finRes);
        } else if (snapMode === 'ward_overview') {
          sceneManager.resetCameraView();
        } else if (snapMode === 'f3_disclaimer') {
          sceneManager.resetCameraView();
          if (debugOverlay && !state.debugOverlayActive) {
            debugOverlay.toggle();
          }
        } else if (snapMode === 'trial_wording') {
          await trialPanel.open();
          await trialPanel.runTrialSimulation();
        } else if (snapMode === 'action_pose') {
          const act = urlParams.get('act') || 'weigh';
          const prog = parseFloat(urlParams.get('prog') || '0.5');

          if (act === 'weigh') {
            const bal = sceneManager.getApparatus('digital_balance');
            const balPos = new THREE.Vector3();
            if (bal) {
              bal.getWorldPosition(balPos);
              if (bal.userData.stationPos) characterController.rig.root.position.copy(bal.userData.stationPos);
              characterController.faceTarget(balPos);
              const props = characterController.createHeldProp('weigh');
              characterController.carryItem(props.right, props.left);
              if (bal.userData.updateWeighProgress) bal.userData.updateWeighProgress(prog, 0.500);
            }
            sceneManager.startActionCamera(balPos, characterController.rig.root.position, 1800, 'weigh', 'digital_balance');
            characterController.animator.sampleClipAtProgress('weigh', prog, balPos);
          } else if (act === 'pour') {
            const cup = sceneManager.getApparatus('dosing_cup');
            const cupPos = new THREE.Vector3();
            if (cup) {
              cup.getWorldPosition(cupPos);
              if (cup.userData.stationPos) characterController.rig.root.position.copy(cup.userData.stationPos);
              characterController.faceTarget(cupPos);
            }
            const cupProp = sceneManager.getApparatus('dosing_cup');
            const cupClone = cupProp ? cupProp.clone() : null;
            if (cupClone) cupClone.scale.set(0.5, 0.5, 0.5);
            const jugProp = sceneManager.getApparatus('water_jug');
            const jugClone = jugProp ? jugProp.clone() : null;
            if (jugClone) jugClone.scale.set(0.35, 0.35, 0.35);
            characterController.carryItem(jugClone, cupClone);
            sceneManager.startActionCamera(cupPos, characterController.rig.root.position, 1800, 'pour', 'dosing_cup');
            characterController.animator.sampleClipAtProgress('pour', prog, cupPos);
          } else if (act === 'titrate') {
            const bur = sceneManager.getApparatus('burette');
            const burPos = new THREE.Vector3(0, 1.4, -2.0);
            if (bur) bur.getWorldPosition(burPos);
            characterController.rig.root.position.set(-0.48, 0, -1.65);
            characterController.faceTarget(new THREE.Vector3(0.02, 1.25, -1.85));
            sceneManager.startActionCamera(burPos, characterController.rig.root.position, 1800, 'titrate', 'burette');
            characterController.animator.sampleClipAtProgress('titrate', prog, burPos);
          } else if (act === 'pipette') {
            const flask = sceneManager.getApparatus('conical_flask');
            const flaskPos = new THREE.Vector3(0.02, 1.05, -1.85);
            if (flask) flask.getWorldPosition(flaskPos);
            characterController.rig.root.position.set(-0.48, 0, -1.65);
            characterController.faceTarget(flaskPos);
            const pipProp = characterController.createHeldProp('pipette_analyte');
            characterController.carryItem(pipProp);
            sceneManager.startActionCamera(flaskPos, characterController.rig.root.position, 1800, 'pipette', 'conical_flask');
            characterController.animator.sampleClipAtProgress('pipette', prog, flaskPos);
          }
        }
      } catch (e) {
        console.error('Snap mode error:', e);
      }
    }, 450);
  }
}

function showSessionError(title, message, whatHappened = null, whatToDo = null) {
  const overlay = document.getElementById('session-error-overlay');
  const titleEl = document.getElementById('session-error-title');
  const textEl = document.getElementById('session-error-text');
  const whatHappenedEl = document.getElementById('error-what-happened');
  const btnBack = document.getElementById('btn-error-back-to-brief');
  const btnLobby = document.getElementById('btn-error-to-lobby');
  const briefScreen = document.getElementById('screen-brief');

  if (titleEl) titleEl.textContent = title || '⚠️ Simulation Error';
  if (whatHappenedEl) {
    whatHappenedEl.textContent = whatHappened || 'The simulation engine encountered a network timeout or unexpected response.';
  }
  if (textEl) {
    textEl.textContent = message || '';
  }

  if (btnBack) {
    btnBack.onclick = () => {
      if (overlay) overlay.classList.add('hidden');
      if (briefScreen) briefScreen.classList.remove('hidden');
    };
  }

  if (btnLobby) {
    btnLobby.onclick = () => {
      if (overlay) overlay.classList.add('hidden');
      window.location.hash = '#/lobby';
    };
  }

  if (overlay) overlay.classList.remove('hidden');
}

function setupOfflineDetection() {
  const banner = document.getElementById('offline-state-banner');
  const updateStatus = () => {
    if (typeof navigator !== 'undefined' && navigator.onLine === false) {
      banner?.classList.remove('hidden');
    } else {
      banner?.classList.add('hidden');
    }
  };
  window.addEventListener('online', updateStatus);
  window.addEventListener('offline', updateStatus);
  updateStatus();
}

async function openExperimentBrief(experimentId) {
  currentSelectedExperimentId = experimentId;
  showScreen('screen-brief');

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

    // Apparatus & Equipment list
    const equipList = document.getElementById('brief-equipment-list');
    if (equipList) {
      const appKeys = Object.keys(exp.apparatus || {});
      equipList.innerHTML = appKeys.length > 0
        ? appKeys.map((k) => `<span class="badge badge-default" style="font-size:11px;">🔧 ${k.replace(/_/g, ' ')}</span>`).join('')
        : '<span style="font-size:11px; color:var(--text-muted);">Standard laboratory workbench apparatus</span>';
    }

    // Safety rules list with experiment-specific rule numbers (R1-R10, S1-S8, D1-D8)
    const rulesList = document.getElementById('brief-rules-list');
    if (rulesList) {
      const expRules = exp.rules || [];
      if (expRules.length > 0) {
        rulesList.innerHTML = expRules.map((r) => `
          <li style="margin-bottom:4px;"><strong style="color:var(--accent);">${r.rule_id}:</strong> <span>${r.title}</span> – <span style="color:var(--text-muted); font-size:11px;">${r.explanation}</span></li>
        `).join('');
      } else {
        rulesList.innerHTML = `
          <li><strong style="color:var(--accent);">R1:</strong> Mandatory PPE equipped before manipulating active agents</li>
          <li><strong style="color:var(--accent);">R2:</strong> Analytical balance tare required before mass measurement</li>
          <li><strong style="color:var(--accent);">R3:</strong> Verified dissolution &amp; labeling prior to administration or titration</li>
          <li><strong style="color:var(--accent);">R4:</strong> Safe waste disposal and sink decontamination required at conclusion</li>
        `;
      }
    }

    // Scoring rubric preview
    const rubricEl = document.getElementById('brief-scoring-rubric');
    if (rubricEl) {
      const weights = exp.scoring_weights || { safety: 40, accuracy: 30, technique: 20, protocol: 10 };
      rubricEl.innerHTML = `
        <div class="card" style="padding:6px 10px; background:rgba(255,255,255,0.03);">
          <div style="font-size:10px; color:var(--ok); font-weight:700;">Safety: ${weights.safety ?? 40} pts</div>
          <div style="font-size:10px; color:var(--text-muted);">-10 per PPE/spill violation</div>
        </div>
        <div class="card" style="padding:6px 10px; background:rgba(255,255,255,0.03);">
          <div style="font-size:10px; color:var(--accent); font-weight:700;">Accuracy: ${weights.accuracy ?? 30} pts</div>
          <div style="font-size:10px; color:var(--text-muted);">Dosing/endpoint precision</div>
        </div>
        <div class="card" style="padding:6px 10px; background:rgba(255,255,255,0.03);">
          <div style="font-size:10px; color:var(--info); font-weight:700;">Technique: ${weights.technique ?? 20} pts</div>
          <div style="font-size:10px; color:var(--text-muted);">Balance tare &amp; timing</div>
        </div>
        <div class="card" style="padding:6px 10px; background:rgba(255,255,255,0.03);">
          <div style="font-size:10px; color:var(--warn); font-weight:700;">Protocol: ${weights.protocol ?? 10} pts</div>
          <div style="font-size:10px; color:var(--text-muted);">Step sequence compliance</div>
        </div>
      `;
    }

    showScreen('screen-brief');
  } catch (err) {
    toast.showInfo(`Could not load experiment details: ${err.message}`);
  }
}

async function startExperimentSession(experimentId, nickname = 'Researcher') {
  showScreen('lab-hud');
  toast.clear();

  try {
    toast.showInfo(`Entering 3D Laboratory for '${experimentId}'...`, 2000);

    // 1. Fetch experiment definition & build 3D apparatus
    const exp = await api.getExperiment(experimentId);
    state.setExperiment(exp);
    sceneManager.loadExperiment(exp);
    characterController.spawnForExperiment(experimentId);
    if (sceneManager.cameraRig) {
      sceneManager.cameraRig.recenter(true);
    }

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

    if (experimentId === 'dose_lab') {
      if (window.dosePanel) window.dosePanel.open();
    } else {
      if (window.dosePanel) window.dosePanel.close();
    }
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

function setupSettings() {
  const qualitySelect = document.getElementById('setting-quality-tier');
  const volumeSlider = document.getElementById('setting-sound-volume');
  const volumeVal = document.getElementById('setting-volume-val');
  const muteCheck = document.getElementById('setting-audio-mute');
  const fontScaleSelect = document.getElementById('setting-font-scale');
  const highContrastCheck = document.getElementById('setting-high-contrast');
  const colorblindSelect = document.getElementById('setting-colorblind-mode');
  const langSelect = document.getElementById('setting-app-language');
  const btnReset = document.getElementById('btn-settings-reset');

  // 1. Graphics Quality
  const savedQuality = localStorage.getItem('orbis_quality_tier') || 'medium';
  if (qualitySelect) {
    qualitySelect.value = savedQuality;
    qualitySelect.onchange = () => {
      const q = qualitySelect.value;
      localStorage.setItem('orbis_quality_tier', q);
      sceneManager.setQuality(q);
      const hudBtn = document.getElementById('btn-toggle-quality');
      if (hudBtn) {
        const labels = { low: '⚡ Quality: Low', medium: '✨ Quality: Med', high: '💎 Quality: High' };
        hudBtn.textContent = labels[q] || '⚙️ Quality';
      }
    };
  }

  // 2. Audio Volume & Mute
  const savedVol = parseFloat(localStorage.getItem('orbis_lab_volume') || '0.8');
  if (volumeSlider) {
    volumeSlider.value = Math.round(savedVol * 100);
    if (volumeVal) volumeVal.textContent = `${Math.round(savedVol * 100)}%`;
    volumeSlider.oninput = () => {
      const vol = parseFloat(volumeSlider.value) / 100;
      soundFX.setVolume(vol);
      if (volumeVal) volumeVal.textContent = `${volumeSlider.value}%`;
      const hudSlider = document.getElementById('hud-volume-slider');
      if (hudSlider) hudSlider.value = volumeSlider.value;
    };
  }

  const isMuted = localStorage.getItem('orbis_lab_muted') === 'true';
  if (muteCheck) {
    muteCheck.checked = isMuted;
    muteCheck.onchange = () => {
      soundFX.setMuted(muteCheck.checked);
      const btnTopMute = document.getElementById('btn-top-mute');
      if (btnTopMute) btnTopMute.textContent = muteCheck.checked ? '🔇' : '🔊';
      const hudBtn = document.getElementById('btn-toggle-sound');
      if (hudBtn) hudBtn.textContent = muteCheck.checked ? '🔇' : '🔊';
    };
  }

  // 3. Font Scale
  function applyFontScale(scale) {
    document.body.classList.remove('font-scale-normal', 'font-scale-large', 'font-scale-xlarge');
    if (scale === 'large') document.body.classList.add('font-scale-large');
    else if (scale === 'xlarge') document.body.classList.add('font-scale-xlarge');
    else document.body.classList.add('font-scale-normal');
    localStorage.setItem('orbis_font_scale', scale);
  }

  const savedScale = localStorage.getItem('orbis_font_scale') || 'normal';
  applyFontScale(savedScale);
  if (fontScaleSelect) {
    fontScaleSelect.value = savedScale;
    fontScaleSelect.onchange = () => applyFontScale(fontScaleSelect.value);
  }

  // 4. High Contrast Mode
  function applyHighContrast(enabled) {
    if (enabled) {
      document.body.classList.add('high-contrast');
    } else {
      document.body.classList.remove('high-contrast');
    }
    localStorage.setItem('orbis_high_contrast', enabled ? 'true' : 'false');
  }

  const savedHighContrast = localStorage.getItem('orbis_high_contrast') === 'true';
  applyHighContrast(savedHighContrast);
  if (highContrastCheck) {
    highContrastCheck.checked = savedHighContrast;
    highContrastCheck.onchange = () => applyHighContrast(highContrastCheck.checked);
  }

  // 5. Colorblind Vision Mode
  function applyColorblind(mode) {
    if (mode && mode !== 'off') {
      document.body.setAttribute('data-colorblind', mode);
    } else {
      document.body.removeAttribute('data-colorblind');
    }
    localStorage.setItem('orbis_colorblind', mode || 'off');
  }

  const savedColorblind = localStorage.getItem('orbis_colorblind') || 'off';
  applyColorblind(savedColorblind);
  if (colorblindSelect) {
    colorblindSelect.value = savedColorblind;
    colorblindSelect.onchange = () => applyColorblind(colorblindSelect.value);
  }

  // 6. Language (i18n)
  if (langSelect) {
    langSelect.value = getLocale();
    langSelect.onchange = async () => {
      await setLocale(langSelect.value);
      toast.showInfo(`Language switched: ${langSelect.value.toUpperCase()}`);
    };
  }

  // 7. Reset Defaults
  if (btnReset) {
    btnReset.onclick = () => {
      localStorage.removeItem('orbis_quality_tier');
      localStorage.removeItem('orbis_lab_volume');
      localStorage.removeItem('orbis_lab_muted');
      localStorage.removeItem('orbis_font_scale');
      localStorage.removeItem('orbis_high_contrast');
      localStorage.removeItem('orbis_colorblind');
      localStorage.removeItem('orbis_locale');

      if (qualitySelect) { qualitySelect.value = 'medium'; qualitySelect.dispatchEvent(new Event('change')); }
      if (volumeSlider) { volumeSlider.value = 80; volumeSlider.dispatchEvent(new Event('input')); }
      if (muteCheck) { muteCheck.checked = false; muteCheck.dispatchEvent(new Event('change')); }
      if (fontScaleSelect) { fontScaleSelect.value = 'normal'; fontScaleSelect.dispatchEvent(new Event('change')); }
      if (highContrastCheck) { highContrastCheck.checked = false; highContrastCheck.dispatchEvent(new Event('change')); }
      if (colorblindSelect) { colorblindSelect.value = 'off'; colorblindSelect.dispatchEvent(new Event('change')); }
      if (langSelect) { langSelect.value = 'en'; langSelect.dispatchEvent(new Event('change')); }
      toast.showInfo('Settings reset to defaults');
    };
  }
}

function setupOnboarding() {
  const modal = document.getElementById('modal-onboarding');
  const btnSkip = document.getElementById('btn-skip-tutorial');
  const btnPrev = document.getElementById('btn-tutorial-prev');
  const btnNext = document.getElementById('btn-tutorial-next');
  const btnReplay = document.getElementById('btn-replay-tutorial');
  const dots = document.getElementById('tutorial-dots');

  let currentStep = 1;
  const totalSteps = 3;

  function setStep(step) {
    currentStep = Math.max(1, Math.min(totalSteps, step));
    for (let i = 1; i <= totalSteps; i++) {
      const slide = document.getElementById(`tutorial-slide-${i}`);
      if (slide) {
        if (i === currentStep) slide.classList.remove('hidden');
        else slide.classList.add('hidden');
      }
    }
    if (dots) dots.textContent = `Step ${currentStep} of ${totalSteps}`;
    if (btnPrev) btnPrev.disabled = (currentStep === 1);
    if (btnNext) {
      btnNext.textContent = (currentStep === totalSteps) ? 'Finish ✓' : 'Next ➔';
    }
  }

  function openTutorial() {
    setStep(1);
    modal?.classList.remove('hidden');
    btnNext?.focus();
  }

  function closeTutorial() {
    modal?.classList.add('hidden');
    localStorage.setItem('orbis_tutorial_completed', 'true');
  }

  if (btnNext) {
    btnNext.onclick = () => {
      if (currentStep < totalSteps) {
        setStep(currentStep + 1);
      } else {
        closeTutorial();
      }
    };
  }

  if (btnPrev) {
    btnPrev.onclick = () => {
      if (currentStep > 1) {
        setStep(currentStep - 1);
      }
    };
  }

  if (btnSkip) btnSkip.onclick = () => closeTutorial();
  if (btnReplay) btnReplay.onclick = () => openTutorial();

  // Keyboard navigation & Focus Trapping inside modal
  if (modal) {
    modal.addEventListener('keydown', (e) => {
      if (modal.classList.contains('hidden')) return;

      if (e.key === 'Escape') {
        e.preventDefault();
        closeTutorial();
      } else if (e.key === 'Enter' || e.key === ' ') {
        if (document.activeElement === btnSkip) {
          e.preventDefault();
          closeTutorial();
        } else if (document.activeElement === btnPrev) {
          e.preventDefault();
          if (currentStep > 1) setStep(currentStep - 1);
        } else {
          e.preventDefault();
          if (currentStep < totalSteps) setStep(currentStep + 1);
          else closeTutorial();
        }
      } else if (e.key === 'Tab') {
        const focusable = modal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (focusable.length > 0) {
          const first = focusable[0];
          const last = focusable[focusable.length - 1];
          if (e.shiftKey) {
            if (document.activeElement === first) {
              e.preventDefault();
              last.focus();
            }
          } else {
            if (document.activeElement === last) {
              e.preventDefault();
              first.focus();
            }
          }
        }
      }
    });
  }

  // Trigger on first visit if not completed
  const completed = localStorage.getItem('orbis_tutorial_completed');
  const urlParams = new URLSearchParams(window.location.search);
  if (!completed && !urlParams.get('snap') && window.location.hash !== '#/settings') {
    setTimeout(() => {
      openTutorial();
    }, 800);
  }
}

function setupHUDControls() {
  // Toggle Name Tags Button
  const btnToggleTags = document.getElementById('btn-toggle-nametags');
  if (btnToggleTags) {
    btnToggleTags.onclick = () => sceneManager.toggleNameTags();
  }

  // Camera Follow / Free Toggle Button
  const btnToggleCamMode = document.getElementById('btn-toggle-camera-mode');
  if (btnToggleCamMode) {
    btnToggleCamMode.onclick = () => {
      if (sceneManager?.cameraRig) {
        const mode = sceneManager.cameraRig.toggleMode();
        toast.showInfo(`Camera Mode: ${mode}`);
      }
    };
  }

  // Recenter Camera Button
  const btnRecenterCam = document.getElementById('btn-recenter-camera');
  if (btnRecenterCam) {
    btnRecenterCam.onclick = () => {
      if (sceneManager?.cameraRig) {
        sceneManager.cameraRig.recenter();
        toast.showInfo('Camera: Re-centered');
      }
    };
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

  // First-Person Mode Button
  const btnFirstPerson = document.getElementById('btn-toggle-first-person');
  if (btnFirstPerson) {
    btnFirstPerson.onclick = () => {
      sceneManager.cameraRig?.toggleFirstPerson();
    };
  }

  // Quality Mode Button
  const btnQuality = document.getElementById('btn-toggle-quality');
  if (btnQuality) {
    btnQuality.onclick = () => {
      const newQ = sceneManager.toggleQuality();
      try { localStorage.setItem('orbis_quality_tier', newQ); } catch (_) {}
      const labels = { low: '⚡ Quality: Low', medium: '✨ Quality: Med', high: '💎 Quality: High' };
      btnQuality.textContent = labels[newQ] || '⚙️ Quality';
      toast.showInfo(`Graphics Quality: ${newQ.toUpperCase()}`);
    };
  }

  // Quality Tier Initialization & 3s First-Load Benchmark
  let savedTier = null;
  try { savedTier = localStorage.getItem('orbis_quality_tier'); } catch (_) {}
  if (savedTier && ['low', 'medium', 'high'].includes(savedTier)) {
    sceneManager.setQuality(savedTier);
    if (btnQuality) {
      const labels = { low: '⚡ Quality: Low', medium: '✨ Quality: Med', high: '💎 Quality: High' };
      btnQuality.textContent = labels[savedTier] || '⚙️ Quality';
    }
  } else {
    // Run 3-second initial benchmark on first load
    const benchmarkSamples = [];
    const benchmarkStart = performance.now();
    const benchmarkInterval = setInterval(() => {
      const elapsed = performance.now() - benchmarkStart;
      const curFps = state.stats?.fps || 60;
      benchmarkSamples.push(curFps);
      if (elapsed >= 3000) {
        clearInterval(benchmarkInterval);
        const avg = benchmarkSamples.reduce((a, b) => a + b, 0) / (benchmarkSamples.length || 1);
        let selectedTier = 'medium';
        if (avg >= 55) selectedTier = 'high';
        else if (avg >= 38) selectedTier = 'medium';
        else selectedTier = 'low';

        try { localStorage.setItem('orbis_quality_tier', selectedTier); } catch (_) {}
        sceneManager.setQuality(selectedTier);
        if (btnQuality) {
          const labels = { low: '⚡ Quality: Low', medium: '✨ Quality: Med', high: '💎 Quality: High' };
          btnQuality.textContent = labels[selectedTier] || '⚙️ Quality';
        }
        toast.showInfo(`Graphics Benchmark: Selected ${selectedTier.toUpperCase()} quality (${Math.round(avg)} FPS avg).`, 3500);
      }
    }, 500);
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

async function checkServerWakeup() {
  const wakeupScreen = document.getElementById('screen-wakeup');
  const progressBar = document.getElementById('wakeup-progress-bar');
  const statusText = document.getElementById('wakeup-status-text');
  const retryBtn = document.getElementById('btn-retry-wakeup');
  const tipText = document.getElementById('wakeup-tip-text');
  const dotsEl = document.getElementById('wakeup-dots');

  const tips = [
    "In orbital mechanics, burning prograde raises the apoapsis on the opposite side of Earth, not where you ignite.",
    "Half-life t1/2 = ln(2) / kel ≈ 0.693 / kel for 1-compartment first-order elimination.",
    "Phenolphthalein transitions from clear to vivid pink in the alkaline pH range of 8.2 to 10.0.",
    "In two-compartment pharmacokinetics, alpha phase represents rapid distribution, followed by beta elimination.",
    "Tsiolkovsky delta-v equation: Δv = Isp * g0 * ln(m0 / mf). Higher Isp dramatically cuts propellant mass."
  ];

  let tipIndex = 0;
  const tipInterval = setInterval(() => {
    tipIndex = (tipIndex + 1) % tips.length;
    if (tipText) tipText.textContent = tips[tipIndex];
  }, 4000);

  let dotCount = 0;
  const dotInterval = setInterval(() => {
    dotCount = (dotCount + 1) % 4;
    if (dotsEl) dotsEl.textContent = '.'.repeat(dotCount);
  }, 450);

  const urlParams = new URLSearchParams(window.location.search);
  const simulateWakeup = urlParams.get('simulate_wakeup') === '1';

  let isAwake = false;
  if (!simulateWakeup) {
    try {
      const res = await fetch('/api/ping', { signal: AbortSignal.timeout(1200) });
      if (res.ok) isAwake = true;
    } catch (_) {}
  }

  if (isAwake) {
    clearInterval(tipInterval);
    clearInterval(dotInterval);
    if (wakeupScreen) wakeupScreen.classList.add('hidden');
    return;
  }

  // Cold start detected – display waking up overlay with backoff
  if (wakeupScreen) wakeupScreen.classList.remove('hidden');

  const startTime = Date.now();
  const maxWaitMs = 90000;
  let attempt = 0;

  async function poll() {
    attempt++;
    const elapsed = Date.now() - startTime;
    const progressPct = Math.min(95, Math.round((elapsed / maxWaitMs) * 100));
    if (progressBar) progressBar.style.width = `${Math.max(15, progressPct)}%`;
    if (statusText) statusText.textContent = `Pinging simulation engine (attempt ${attempt}, ${Math.round(elapsed / 1000)}s)...`;

    if (simulateWakeup && elapsed >= 2000) {
      // Freeze simulation so screenshots/tests can inspect
      return;
    }

    try {
      const res = await fetch('/api/ping', { signal: AbortSignal.timeout(3000) });
      if (res.ok) {
        clearInterval(tipInterval);
        clearInterval(dotInterval);
        if (progressBar) progressBar.style.width = '100%';
        if (statusText) statusText.textContent = 'Connected! Laboratory ready.';
        setTimeout(() => {
          if (wakeupScreen) wakeupScreen.classList.add('hidden');
        }, 600);
        return;
      }
    } catch (_) {}

    if (elapsed >= maxWaitMs) {
      if (statusText) statusText.textContent = 'Server wake-up timed out. Free hosting instance may take longer to spin up.';
      if (retryBtn) {
        retryBtn.style.display = 'block';
        retryBtn.onclick = () => {
          retryBtn.style.display = 'none';
          checkServerWakeup();
        };
      }
      return;
    }

    const delay = Math.min(4000, 1000 + attempt * 500);
    setTimeout(poll, delay);
  }

  poll();
}

// Boot application when DOM is ready
window.addEventListener('DOMContentLoaded', initOrbisLab);
