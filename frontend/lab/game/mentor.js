/**
 * Dr. Orbis AI Lab Mentor (frontend/lab/game/mentor.js)
 * Real-time pedagogical lab guide, violation auto-explainer, step hinter,
 * and report debrief generator.
 */

import { api } from '../api.js';
import { state } from '../state.js';
import { toast } from './toast.js';

export class DrOrbisMentor {
  constructor() {
    this.isCollapsed = true;
    this.isTyping = false;
    this.messages = [];
    this.callsLeft = 30;
    this.lastMode = 'idle';
    this.lastLatencyMs = 0;
    this.lastViolationId = null;

    this.containerEl = document.getElementById('dr-orbis-container');
    this.initDOM();
    this.setupListeners();
  }

  initDOM() {
    if (!this.containerEl) return;

    this.containerEl.innerHTML = `
      <div class="mentor-docked-card" id="mentor-docked-card">
        <!-- Mentor Header with Animated Avatar -->
        <div class="mentor-header" id="mentor-header">
          <div class="mentor-avatar-wrap">
            <div class="mentor-avatar-orb" id="mentor-avatar-orb">
              <span class="mentor-avatar-face">👨‍🔬</span>
              <span class="mentor-pulse-ring"></span>
            </div>
            <div class="mentor-title-block">
              <span class="mentor-name">Dr. Orbis</span>
              <span class="mentor-role">Lab Mentor</span>
            </div>
          </div>
          <div class="mentor-header-controls">
            <span class="mentor-source-badge badge-neutral" id="mentor-source-tag">Ready</span>
            <button type="button" class="btn-toggle-mentor" id="btn-toggle-mentor" title="Minimize / Expand Mentor">▼</button>
          </div>
        </div>

        <!-- Collapsible Content -->
        <div class="mentor-body" id="mentor-body">
          <!-- Speech Bubble / Message Area -->
          <div class="mentor-messages-list" id="mentor-messages-list">
            <div class="mentor-msg-bubble system-msg">
              <div class="msg-author">Dr. Orbis</div>
              <div class="msg-text">Welcome to the laboratory! I am Dr. Orbis, your scientific mentor. Click <strong>Step Hint</strong> or ask me questions anytime.</div>
            </div>
          </div>

          <!-- Typing Indicator -->
          <div class="mentor-typing-indicator hidden" id="mentor-typing-indicator" style="display: none;">
            <span>Dr. Orbis is thinking</span>
            <span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>
          </div>

          <!-- Action Controls & Input -->
          <div class="mentor-input-controls">
            <div class="mentor-quick-bar">
              <button type="button" class="btn-mentor-hint" id="btn-mentor-hint">💡 Step Hint</button>
              <button type="button" class="btn-mentor-explain" id="btn-mentor-explain">🔍 Explain Status</button>
            </div>

            <form class="mentor-ask-form" id="mentor-ask-form">
              <div class="mentor-input-row">
                <input
                  type="text"
                  id="mentor-question-input"
                  placeholder="Ask Dr. Orbis a question..."
                  maxlength="200"
                  autocomplete="off"
                />
                <button type="submit" class="btn-mentor-send" id="btn-mentor-send" title="Send question">➔</button>
              </div>
              <div class="mentor-char-counter" id="mentor-char-counter">0/200 chars</div>
            </form>
          </div>

          <!-- Under-The-Hood Area -->
          <div class="mentor-under-the-hood">
            <span>Mode: <strong id="uth-mode">idle</strong></span>
            <span>Calls Left: <strong id="uth-calls-left">30/30</strong></span>
            <span>Latency: <strong id="uth-latency">0ms</strong></span>
          </div>
        </div>
      </div>
    `;

    // Header toggle
    const toggleBtn = document.getElementById('btn-toggle-mentor');
    const header = document.getElementById('mentor-header');
    const body = document.getElementById('mentor-body');

    window.drOrbisMentor = this;

    header?.addEventListener('click', (e) => {
      if (e.target.closest('#btn-mentor-hint') || e.target.closest('#mentor-ask-form')) return;
      this.setCollapsed(!this.isCollapsed);
    });

    this.setCollapsed(true);

    // Quick buttons
    document.getElementById('btn-mentor-hint')?.addEventListener('click', () => this.query('hint'));
    document.getElementById('btn-mentor-explain')?.addEventListener('click', () => this.query('explain'));

    // Question form & character counter
    const input = document.getElementById('mentor-question-input');
    const counter = document.getElementById('mentor-char-counter');
    const form = document.getElementById('mentor-ask-form');

    input?.addEventListener('input', () => {
      if (counter) counter.textContent = `${input.value.length}/200 chars`;
    });

    form?.addEventListener('submit', (e) => {
      e.preventDefault();
      const q = input?.value?.trim();
      if (!q) return;
      if (input) input.value = '';
      if (counter) counter.textContent = '0/200 chars';
      this.query('ask', q);
    });
  }

  setupListeners() {
    // 1. Auto-explain after every violation toast
    window.addEventListener('lab_violation_toast', (e) => {
      const v = e.detail;
      if (v && v.rule_id !== this.lastViolationId) {
        this.lastViolationId = v.rule_id;
        // Trigger auto-explain
        setTimeout(() => {
          this.query('explain');
        }, 600);
      }
    });

    // 2. State session updates
    state.subscribe((event, payload) => {
      if (event === 'session_updated') {
        if (payload.violations && payload.violations.length > 0) {
          const latest = payload.violations[payload.violations.length - 1];
          if (latest.rule_id !== this.lastViolationId) {
            this.lastViolationId = latest.rule_id;
            setTimeout(() => this.query('explain'), 800);
          }
        }
      }
    });
  }

  async query(mode, question = null) {
    const sessionId = state.session?.session_id;
    if (!sessionId) {
      toast.showWarning('No active lab session found.');
      return;
    }

    if (this.isTyping) return; // Concurrency limit

    // Ensure expanded if user interacts or auto-explains
    if (this.isCollapsed) {
      this.isCollapsed = false;
      document.getElementById('mentor-body')?.classList.remove('hidden');
      const toggleBtn = document.getElementById('btn-toggle-mentor');
      if (toggleBtn) toggleBtn.textContent = '▼';
    }

    this.isTyping = true;
    this.lastMode = mode;
    this.updateUnderTheHood(mode, this.callsLeft, this.lastLatencyMs);

    const typingIndicator = document.getElementById('mentor-typing-indicator');
    if (typingIndicator) {
      typingIndicator.classList.remove('hidden');
      typingIndicator.style.display = 'flex';
    }

    const tStart = performance.now();

    try {
      const res = await api.queryMentor(sessionId, mode, question);
      const latency = Math.round(performance.now() - tStart);
      this.lastLatencyMs = latency;
      this.callsLeft = res.calls_left ?? this.callsLeft;

      this.updateUnderTheHood(mode, this.callsLeft, latency);
      this.updateSourceBadge(res.source, res.provider_tag || res.provider);

      // Render response with typing animation
      await this.appendMessage({
        sender: 'Dr. Orbis',
        text: res.message,
        source: res.source,
        provider: res.provider,
        providerTag: res.provider_tag,
        fallbackReason: res.fallback_reason,
        mode: mode,
        question: question,
      });
    } catch (err) {
      console.error('Mentor query error:', err);
      const latency = Math.round(performance.now() - tStart);
      this.updateUnderTheHood(mode, this.callsLeft, latency);
      this.updateSourceBadge('fallback');

      await this.appendMessage({
        sender: 'Dr. Orbis',
        text: `Dr. Orbis: Let's focus on current protocol step. Keep glassware stable and follow safety guidelines.`,
        source: 'fallback',
        provider: null,
        providerTag: 'Rule-based',
        fallbackReason: 'Network error',
        mode: mode,
      });
    } finally {
      this.isTyping = false;
      if (typingIndicator) {
        typingIndicator.classList.add('hidden');
        typingIndicator.style.display = 'none';
      }
      this.updateUnderTheHood('idle', this.callsLeft, this.lastLatencyMs);
    }
  }

  async appendMessage({ sender, text, source, provider, providerTag, fallbackReason, mode, question }) {
    const list = document.getElementById('mentor-messages-list');
    if (!list) return;

    // If student asked a question, show student bubble first
    if (question) {
      const studentBubble = document.createElement('div');
      studentBubble.className = 'mentor-msg-bubble student-msg';
      studentBubble.innerHTML = `
        <div class="msg-author">You</div>
        <div class="msg-text">${this.escapeHTML(question)}</div>
      `;
      list.appendChild(studentBubble);
    }

    const bubble = document.createElement('div');
    bubble.className = `mentor-msg-bubble mentor-response ${source === 'ai' ? 'msg-ai' : 'msg-rule'}`;

    const tagLabel = source === 'ai'
      ? (providerTag || (provider === 'gemini' ? 'AI - Gemini' : (provider === 'claude' ? 'AI - Claude' : 'AI')))
      : 'Rule-based';
    const tagClass = source === 'ai' ? 'badge-ai' : 'badge-rule';

    bubble.innerHTML = `
      <div class="msg-header">
        <span class="msg-author">${sender}</span>
        <span class="mentor-badge ${tagClass}">${tagLabel}</span>
      </div>
      <div class="msg-text" id="active-typing-text"></div>
      ${fallbackReason ? `<div class="msg-note">${this.escapeHTML(fallbackReason)}</div>` : ''}
    `;

    list.appendChild(bubble);
    list.scrollTop = list.scrollHeight;

    const textEl = bubble.querySelector('#active-typing-text');
    if (!textEl) return;
    textEl.removeAttribute('id');

    // Typewriter effect respecting state.skipAnimation
    if (state.skipAnimation) {
      textEl.textContent = text;
    } else {
      await this.typeWriter(textEl, text, list);
    }
    list.scrollTop = list.scrollHeight;
  }

  typeWriter(el, fullText, scrollContainer) {
    return new Promise((resolve) => {
      let idx = 0;
      const speedMs = 12; // Snappy typing speed
      const timer = setInterval(() => {
        if (state.skipAnimation || idx >= fullText.length) {
          el.textContent = fullText;
          clearInterval(timer);
          resolve();
          return;
        }
        el.textContent = fullText.slice(0, idx + 1);
        idx += 2; // Type in pairs for swift response
        if (scrollContainer) scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }, speedMs);
    });
  }

  setCollapsed(collapsed) {
    this.isCollapsed = Boolean(collapsed);
    const body = document.getElementById('mentor-body');
    const toggleBtn = document.getElementById('btn-toggle-mentor');
    if (body) body.classList.toggle('hidden', this.isCollapsed);
    if (toggleBtn) toggleBtn.textContent = this.isCollapsed ? '▲' : '▼';
  }

  updateUnderTheHood(mode, callsLeft, latencyMs) {
    const modeEl = document.getElementById('uth-mode');
    const callsEl = document.getElementById('uth-calls-left');
    const latEl = document.getElementById('uth-latency');

    if (modeEl) modeEl.textContent = mode;
    if (callsEl) callsEl.textContent = `${callsLeft}/30`;
    if (latEl) latEl.textContent = `${latencyMs}ms`;
  }

  updateSourceBadge(source, providerTag = null) {
    const badge = document.getElementById('mentor-source-tag');
    if (!badge) return;
    if (source === 'ai') {
      badge.textContent = providerTag ? `🤖 ${providerTag}` : '🤖 AI';
      badge.className = 'mentor-source-badge badge-ai';
    } else {
      badge.textContent = '📋 Rule-Based';
      badge.className = 'mentor-source-badge badge-rule';
    }
  }

  escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
}
