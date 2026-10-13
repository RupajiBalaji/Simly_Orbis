/**
 * Ask Orbis Autonomous Lab Agent Panel (frontend/lab/game/agent_panel.js)
 *
 * Implements:
 * 1. HUD "Ask Orbis" input bar with shortcut [/] and Web Speech API mic.
 * 2. Experiment-specific suggestion chips.
 * 3. Interactive Plan Card with safety warning badges (green/amber/red) and tooltip explanations.
 * 4. Step-by-step and full plan execution runner driving window.actionMenu.executeAction.
 * 5. Consequence handling: stops on action failure and queries Dr. Orbis mentor.
 */

import { api } from '../api.js';
import { state } from '../state.js';
import { toast } from './toast.js';

export class AskOrbisAgentPanel {
  constructor() {
    this.currentPlan = null;
    this.isRunningPlan = false;
    this.shouldStopExecution = false;
    this.currentStepIdx = 0;
    this.speechRecognition = null;
    this.isListening = false;

    this.chipsByExperiment = {
      pk_ward: [
        'Wear PPE and tare the balance',
        'Weigh 0.5g paracetamol and dissolve in water',
        'Administer dose, advance 1h, and draw blood',
      ],
      titration_bench: [
        'Wear PPE and rinse the burette',
        'Fill burette, pipette 25ml HCl, and add indicator',
        'Titrate 20ml NaOH and swirl flask',
      ],
    };

    this.initDOM();
    this.initSpeech();
    this.initListeners();
  }

  initDOM() {
    // 1. Inject Ask Orbis Bar into lab HUD if not already present
    const hud = document.getElementById('lab-hud');
    if (!hud || document.getElementById('hud-ask-orbis-bar')) return;

    const nextBanner = document.getElementById('hud-next-step-banner');

    const barEl = document.createElement('div');
    barEl.className = 'hud-ask-orbis-bar';
    barEl.id = 'hud-ask-orbis-bar';
    barEl.innerHTML = `
      <div class="ask-orbis-input-wrap">
        <span class="ask-orbis-icon" title="Ask Orbis AI Lab Agent">🤖</span>
        <input
          type="text"
          id="ask-orbis-input"
          placeholder="Ask Orbis: type or speak a lab instruction... (Press / to focus)"
          maxlength="200"
          autocomplete="off"
        />
        <button type="button" class="btn-ask-mic" id="btn-ask-mic" title="Voice Input (Speech-to-Text)">🎤</button>
        <button type="button" class="btn-ask-submit" id="btn-ask-submit" title="Propose Action Plan">Propose Plan ➔</button>
      </div>
      <div class="ask-orbis-examples-row" id="ask-orbis-examples-row">
        <span class="examples-label">Try:</span>
        <div class="example-chips" id="ask-orbis-chips"></div>
      </div>
    `;

    if (nextBanner && nextBanner.nextSibling) {
      hud.insertBefore(barEl, nextBanner.nextSibling);
    } else {
      hud.appendChild(barEl);
    }

    // 2. Inject Proposed Plan Modal into document body if not present
    if (!document.getElementById('ask-orbis-plan-modal')) {
      const modalEl = document.createElement('div');
      modalEl.className = 'ask-orbis-plan-modal hidden';
      modalEl.id = 'ask-orbis-plan-modal';
      modalEl.style.display = 'none';
      modalEl.innerHTML = `
        <div class="plan-card" id="ask-orbis-plan-card">
          <div class="plan-card-header">
            <div class="plan-title-wrap">
              <span class="plan-badge">🤖 PROPOSED LAB PLAN</span>
              <h3 id="plan-card-heading">Action Sequence</h3>
            </div>
            <button type="button" class="btn-close-plan" id="btn-close-plan" title="Close Plan">✕</button>
          </div>
          <div class="plan-card-reply" id="plan-card-reply"></div>
          <div class="plan-steps-list" id="plan-steps-list"></div>
          <div class="plan-execution-progress hidden" id="plan-execution-progress">
            <div class="plan-progress-bar"><div class="plan-progress-fill" id="plan-progress-fill" style="width: 0%;"></div></div>
            <div class="plan-progress-label" id="plan-progress-label">Executing step 1...</div>
          </div>
          <div class="plan-card-actions" id="plan-card-actions">
            <button type="button" class="btn-plan-run" id="btn-plan-run">▶ Run Plan</button>
            <button type="button" class="btn-plan-step" id="btn-plan-step">⏯ Step by Step</button>
            <button type="button" class="btn-plan-cancel" id="btn-plan-cancel">Cancel</button>
            <button type="button" class="btn-plan-stop hidden" id="btn-plan-stop">⏹ Stop</button>
          </div>
        </div>
      `;
      document.body.appendChild(modalEl);
    }
  }

  initSpeech() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const micBtn = document.getElementById('btn-ask-mic');
    if (!SpeechRecognition) {
      if (micBtn) {
        micBtn.title = 'Speech recognition not supported in this browser';
        micBtn.style.opacity = '0.4';
      }
      return;
    }

    try {
      this.speechRecognition = new SpeechRecognition();
      this.speechRecognition.continuous = false;
      this.speechRecognition.interimResults = false;
      this.speechRecognition.lang = 'en-US';

      this.speechRecognition.onstart = () => {
        this.isListening = true;
        if (micBtn) micBtn.classList.add('listening');
        toast.showInfo('Listening... Speak your laboratory instruction');
      };

      this.speechRecognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        const input = document.getElementById('ask-orbis-input');
        if (input) {
          input.value = transcript;
          this.submitRequest(transcript);
        }
      };

      this.speechRecognition.onerror = (err) => {
        this.isListening = false;
        if (micBtn) micBtn.classList.remove('listening');
        if (err.error !== 'no-speech') {
          toast.showInfo(`Speech input error: ${err.error}`);
        }
      };

      this.speechRecognition.onend = () => {
        this.isListening = false;
        if (micBtn) micBtn.classList.remove('listening');
      };
    } catch (err) {
      console.warn('SpeechRecognition initialization error:', err);
    }
  }

  initListeners() {
    const input = document.getElementById('ask-orbis-input');
    const submitBtn = document.getElementById('btn-ask-submit');
    const micBtn = document.getElementById('btn-ask-mic');
    const closeBtn = document.getElementById('btn-close-plan');
    const cancelBtn = document.getElementById('btn-plan-cancel');
    const runBtn = document.getElementById('btn-plan-run');
    const stepBtn = document.getElementById('btn-plan-step');
    const stopBtn = document.getElementById('btn-plan-stop');

    // Shortcut [/] to focus input
    window.addEventListener('keydown', (e) => {
      if (e.key === '/' && document.activeElement !== input) {
        // Prevent typing '/' into input immediately
        e.preventDefault();
        if (input) {
          input.focus();
          input.select();
        }
      }
    });

    if (submitBtn && input) {
      submitBtn.onclick = () => {
        const txt = input.value.trim();
        if (txt) this.submitRequest(txt);
      };
      input.onkeydown = (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          const txt = input.value.trim();
          if (txt) this.submitRequest(txt);
        }
      };
    }

    if (micBtn) {
      micBtn.onclick = () => {
        if (!this.speechRecognition) {
          toast.showInfo('Voice input not supported in this browser.');
          return;
        }
        if (this.isListening) {
          this.speechRecognition.stop();
        } else {
          try {
            this.speechRecognition.start();
          } catch (e) {
            console.warn('Mic start error:', e);
          }
        }
      };
    }

    if (closeBtn) closeBtn.onclick = () => this.closePlanModal();
    if (cancelBtn) cancelBtn.onclick = () => this.closePlanModal();

    if (runBtn) runBtn.onclick = () => this.executePlan(false);
    if (stepBtn) stepBtn.onclick = () => this.executePlan(true);
    if (stopBtn) {
      stopBtn.onclick = () => {
        this.shouldStopExecution = true;
        toast.showInfo('Stopping plan execution after current action...');
      };
    }

    // Subscribe to experiment changes to update suggestion chips and clean up modal
    state.subscribe((event, payload) => {
      if (event === 'session_start' || event === 'experiment_selected') {
        const expId = payload?.experiment_id || state.experiment?.id || 'pk_ward';
        this.updateChips(expId);
      }
      if (event === 'session_finish' || event === 'report' || event === 'lobby') {
        this.closePlanModal();
      }
    });
  }

  updateChips(experimentId) {
    const chipsContainer = document.getElementById('ask-orbis-chips');
    if (!chipsContainer) return;

    chipsContainer.innerHTML = '';
    const chips = this.chipsByExperiment[experimentId] || this.chipsByExperiment.pk_ward;

    chips.forEach((chipText) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'ask-orbis-chip';
      btn.textContent = chipText;
      btn.onclick = () => {
        const input = document.getElementById('ask-orbis-input');
        if (input) input.value = chipText;
        this.submitRequest(chipText);
      };
      chipsContainer.appendChild(btn);
    });
  }

  async submitRequest(text) {
    const session = state.session;
    if (!session || !session.session_id) {
      toast.showInfo('Please enter an active lab experiment first.');
      return;
    }

    toast.showInfo('Dr. Orbis is formulating an action plan...');
    const submitBtn = document.getElementById('btn-ask-submit');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Planning...';
    }

    try {
      const res = await api.planAgent(session.session_id, text);
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Propose Plan ➔';
      }

      if (res.status === 'refused' || res.status === 'invalid') {
        toast.showInfo(res.reply || 'Request could not be executed.');
        if (res.reply) {
          // Open Dr. Orbis mentor to explain
          if (window.drOrbisMentor) {
            window.drOrbisMentor.appendAssistantMessage(res.reply, res.provider_tag, 'refusal');
            window.drOrbisMentor.setCollapsed(false);
          }
        }
        return;
      }

      this.showPlanModal(res);
    } catch (err) {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Propose Plan ➔';
      }
      toast.showInfo(`Planning error: ${err.message}`);
    }
  }

  showPlanModal(planData) {
    this.currentPlan = planData;
    this.isRunningPlan = false;
    this.shouldStopExecution = false;
    this.currentStepIdx = 0;

    const modal = document.getElementById('ask-orbis-plan-modal');
    const replyEl = document.getElementById('plan-card-reply');
    const stepsListEl = document.getElementById('plan-steps-list');
    const progressEl = document.getElementById('plan-execution-progress');
    const runBtn = document.getElementById('btn-plan-run');
    const stepBtn = document.getElementById('btn-plan-step');
    const cancelBtn = document.getElementById('btn-plan-cancel');
    const stopBtn = document.getElementById('btn-plan-stop');

    if (!modal) return;
    modal.style.display = 'flex';

    if (progressEl) progressEl.classList.add('hidden');
    if (runBtn) runBtn.classList.remove('hidden');
    if (stepBtn) stepBtn.classList.remove('hidden');
    if (cancelBtn) cancelBtn.classList.remove('hidden');
    if (stopBtn) stopBtn.classList.add('hidden');

    if (replyEl) {
      replyEl.textContent = `${planData.reply} (${planData.provider_tag} · ${planData.calls_left} calls remaining)`;
    }

    if (stepsListEl) {
      stepsListEl.innerHTML = '';
      planData.steps.forEach((step, idx) => {
        const stepRow = document.createElement('div');
        stepRow.className = 'plan-step-row';
        stepRow.id = `plan-step-row-${idx}`;

        // Determine badge severity
        let badgeHtml = '<span class="step-badge badge-ok" title="Safe protocol step">✓ Safe</span>';
        if (step.predicted_violations && step.predicted_violations.length > 0) {
          const hasCrit = step.predicted_violations.some((v) => v.severity === 'critical' || v.severity === 'major');
          const firstV = step.predicted_violations[0];
          const tooltip = step.predicted_violations.map((v) => `[${v.severity.toUpperCase()}] ${v.title}: ${v.explanation}`).join('\n');
          if (hasCrit) {
            badgeHtml = `<span class="step-badge badge-critical" title="${this.escapeAttr(tooltip)}">⛔ Safety Breach</span>`;
          } else {
            badgeHtml = `<span class="step-badge badge-warning" title="${this.escapeAttr(tooltip)}">⚠️ Warning</span>`;
          }
        }

        const paramsStr = Object.keys(step.params || {}).length > 0 ? ` (${JSON.stringify(step.params)})` : '';

        stepRow.innerHTML = `
          <div class="step-number">${step.step_index}</div>
          <div class="step-details">
            <div class="step-title-line">
              <span class="step-title">${step.friendly_title}</span>
              <span class="step-target">@ ${step.target || 'lab'}</span>
              ${badgeHtml}
            </div>
            <div class="step-why">${step.why || ''} <span class="step-params-hint">${this.escapeHTML(paramsStr)}</span></div>
            ${
              step.predicted_violations && step.predicted_violations.length > 0
                ? `<div class="step-violation-warning">⚠️ ${this.escapeHTML(step.predicted_violations[0].explanation)}</div>`
                : ''
            }
          </div>
        `;
        stepsListEl.appendChild(stepRow);
      });
    }

    modal.classList.remove('hidden');
  }

  closePlanModal() {
    const modal = document.getElementById('ask-orbis-plan-modal');
    if (modal) {
      modal.classList.add('hidden');
      modal.style.display = 'none';
    }
    this.isRunningPlan = false;
    this.shouldStopExecution = true;
  }

  async executePlan(stepByStep = false) {
    if (!this.currentPlan || !this.currentPlan.steps || this.currentPlan.steps.length === 0) return;

    this.isRunningPlan = true;
    this.shouldStopExecution = false;

    const progressEl = document.getElementById('plan-execution-progress');
    const fillEl = document.getElementById('plan-progress-fill');
    const labelEl = document.getElementById('plan-progress-label');
    const runBtn = document.getElementById('btn-plan-run');
    const stepBtn = document.getElementById('btn-plan-step');
    const cancelBtn = document.getElementById('btn-plan-cancel');
    const stopBtn = document.getElementById('btn-plan-stop');

    if (progressEl) progressEl.classList.remove('hidden');
    if (runBtn) runBtn.classList.add('hidden');
    if (stepBtn) stepBtn.classList.add('hidden');
    if (cancelBtn) cancelBtn.classList.add('hidden');
    if (stopBtn) stopBtn.classList.remove('hidden');

    const totalSteps = this.currentPlan.steps.length;

    while (this.currentStepIdx < totalSteps) {
      if (this.shouldStopExecution) {
        toast.showInfo('Plan execution paused by student.');
        break;
      }

      const step = this.currentPlan.steps[this.currentStepIdx];
      const stepRow = document.getElementById(`plan-step-row-${this.currentStepIdx}`);
      if (stepRow) {
        document.querySelectorAll('.plan-step-row').forEach((r) => r.classList.remove('active-step'));
        stepRow.classList.add('active-step');
      }

      const pct = Math.round(((this.currentStepIdx) / totalSteps) * 100);
      if (fillEl) fillEl.style.width = `${pct}%`;
      if (labelEl) labelEl.textContent = `Executing step ${this.currentStepIdx + 1} of ${totalSteps}: ${step.friendly_title}...`;

      try {
        // Execute through the real action pipeline!
        // Camera, animations, sounds, violations, mentor all work seamlessly.
        const res = await window.actionMenu.executeAction(step.action, step.target, step.params);

        if (stepRow) {
          stepRow.classList.add('completed-step');
        }

        // If the action was rejected by the engine (e.g. invalid physical state):
        if (res && res.accepted === false) {
          toast.showInfo(`Step ${this.currentStepIdx + 1} halted: ${res.message}`);
          if (window.drOrbisMentor) {
            window.drOrbisMentor.appendAssistantMessage(
              `Plan stopped at step ${this.currentStepIdx + 1} (${step.friendly_title}): ${res.message}`,
              'Engine',
              'action_rejected'
            );
            window.drOrbisMentor.setCollapsed(false);
          }
          break;
        }
      } catch (err) {
        console.error('Error executing agent plan step:', err);
        toast.showInfo(`Error executing step: ${err.message}`);
        break;
      }

      this.currentStepIdx++;

      if (stepByStep && this.currentStepIdx < totalSteps) {
        // Pause and allow student to click 'Next Step'
        toast.showInfo(`Step ${this.currentStepIdx} finished. Click 'Next Step' to continue.`);
        if (labelEl) labelEl.textContent = `Ready for step ${this.currentStepIdx + 1} of ${totalSteps}`;
        if (stepBtn) {
          stepBtn.textContent = `▶ Next Step (${this.currentStepIdx + 1}/${totalSteps})`;
          stepBtn.classList.remove('hidden');
        }
        if (stopBtn) stopBtn.classList.add('hidden');
        if (cancelBtn) cancelBtn.classList.remove('hidden');
        return;
      }

      // Small pause between automated steps for visual clarity
      await new Promise((r) => setTimeout(r, 450));
    }

    if (this.currentStepIdx >= totalSteps) {
      if (fillEl) fillEl.style.width = '100%';
      if (labelEl) labelEl.textContent = 'All proposed plan steps executed successfully!';
      toast.showInfo('✓ Plan completed successfully!');
      setTimeout(() => {
        this.closePlanModal();
      }, 1200);
    }
  }

  escapeHTML(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  escapeAttr(str) {
    if (!str) return '';
    return str.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
}
