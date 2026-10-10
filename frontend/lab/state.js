/**
 * Orbis Lab State Store (frontend/lab/state.js)
 * Manages active session, experiment definition, selected apparatus, and UI locks.
 */

class LabStateStore {
  constructor() {
    this.session = null;
    this.experiment = null;
    this.availableActions = [];
    this.selectedTargetId = null;
    this.isActionPending = false;
    this.skipAnimation = false;
    this.directorMode = false;
    this.debugOverlayActive = false;
    this.stats = {
      fps: 60,
      drawCalls: 0,
      lastAction: null,
      lastDirectives: [],
    };
    this.subscribers = new Set();
  }

  subscribe(callback) {
    this.subscribers.add(callback);
    return () => this.subscribers.delete(callback);
  }

  notify(event, payload) {
    for (const sub of this.subscribers) {
      try {
        sub(event, payload);
      } catch (e) {
        console.error('State subscriber error:', e);
      }
    }
  }

  setSession(session) {
    this.session = session;
    if (session?.session_id) {
      sessionStorage.setItem('orbis_lab_session_id', session.session_id);
    }
    this.notify('session_updated', session);
  }

  setExperiment(experiment) {
    this.experiment = experiment;
    this.notify('experiment_updated', experiment);
  }

  setAvailableActions(actions) {
    this.availableActions = actions || [];
    this.notify('actions_updated', this.availableActions);
  }

  setSelectedTarget(targetId) {
    this.selectedTargetId = targetId;
    this.notify('target_selected', targetId);
  }

  setPending(isPending) {
    this.isActionPending = isPending;
    this.notify('pending_changed', isPending);
  }

  toggleSkipAnimation() {
    this.skipAnimation = !this.skipAnimation;
    this.notify('skip_animation_changed', this.skipAnimation);
    return this.skipAnimation;
  }

  toggleDirectorMode() {
    this.directorMode = !this.directorMode;
    this.notify('director_mode_changed', this.directorMode);
    return this.directorMode;
  }

  toggleDebugOverlay() {
    this.debugOverlayActive = !this.debugOverlayActive;
    this.notify('debug_overlay_changed', this.debugOverlayActive);
    return this.debugOverlayActive;
  }

  updateStats(partialStats) {
    Object.assign(this.stats, partialStats);
  }
}

export const state = new LabStateStore();
