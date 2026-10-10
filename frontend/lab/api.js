/**
 * Orbis Lab REST API Client (frontend/lab/api.js)
 * Interacts with the backend authoritative world-brain engine.
 */

const BASE_URL = '';

async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  
  try {
    const res = await fetch(url, { ...options, headers });
    if (!res.ok) {
      let errorMsg = `Server error (${res.status})`;
      try {
        const errJson = await res.json();
        errorMsg = errJson.detail || errorMsg;
      } catch (_) {}
      throw new Error(errorMsg);
    }
    return await res.json();
  } catch (err) {
    console.error(`API request failed on ${path}:`, err);
    throw err;
  }
}

export const api = {
  async getExperiments() {
    return await request('/api/lab/experiments');
  },

  async getExperiment(experimentId) {
    return await request(`/api/lab/experiments/${encodeURIComponent(experimentId)}`);
  },

  async createSession(experimentId, nickname = 'Researcher') {
    return await request('/api/lab/sessions', {
      method: 'POST',
      body: JSON.stringify({ experiment_id: experimentId, nickname }),
    });
  },

  async getSession(sessionId) {
    return await request(`/api/lab/sessions/${encodeURIComponent(sessionId)}`);
  },

  async getAvailableActions(sessionId) {
    return await request(`/api/lab/sessions/${encodeURIComponent(sessionId)}/available-actions`);
  },

  async applyAction(sessionId, action, target = null, params = {}) {
    return await request(`/api/lab/sessions/${encodeURIComponent(sessionId)}/actions`, {
      method: 'POST',
      body: JSON.stringify({ action, target, params }),
    });
  },

  async finishSession(sessionId) {
    return await request(`/api/lab/sessions/${encodeURIComponent(sessionId)}/finish`, {
      method: 'POST',
    });
  },

  async getLeaderboard(experimentId) {
    return await request(`/api/lab/leaderboard?experiment_id=${encodeURIComponent(experimentId)}`);
  },
};
