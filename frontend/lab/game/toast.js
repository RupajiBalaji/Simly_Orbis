/**
 * Educational Violation Toasts & Alerts (frontend/lab/game/toast.js)
 * Displays pedagogical explanations when safety rules are breached.
 */

export class ToastManager {
  constructor() {
    this.container = document.getElementById('toast-container');
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      document.body.appendChild(this.container);
    }
    this.activeTimer = null;
  }

  showInfo(message, durationMs = 3000) {
    this.clear(); // At most 1 active toast at any time

    const toast = document.createElement('div');
    toast.className = 'toast toast-info';
    toast.textContent = message;
    this.container.appendChild(toast);

    this.activeTimer = setTimeout(() => {
      toast.remove();
      this.activeTimer = null;
    }, durationMs);
  }

  showSuccess(message, durationMs = 3000) {
    this.showInfo(`✓ ${message}`, durationMs);
  }

  showError(message, durationMs = 4000) {
    this.showInfo(`⚠️ ${message}`, durationMs);
  }

  showViolation(violation) {
    this.clear(); // At most 1 active toast at any time

    try {
      window.dispatchEvent(new CustomEvent('lab_violation_toast', { detail: violation }));
    } catch (_) {}

    const toast = document.createElement('div');
    toast.className = 'toast toast-violation';

    const header = document.createElement('div');
    header.className = 'toast-violation-title';
    header.innerHTML = `<span>⚠️ ${violation.title}</span><span>[${(violation.severity || 'warning').toUpperCase()}]</span>`;

    const body = document.createElement('div');
    body.className = 'toast-violation-body';
    body.textContent = violation.explanation;

    toast.appendChild(header);
    toast.appendChild(body);

    const isUrgent = violation.severity === 'critical' || violation.severity === 'major';
    if (isUrgent) {
      const btn = document.createElement('button');
      btn.className = 'toast-btn-dismiss';
      btn.textContent = 'I Understand';
      btn.onclick = () => {
        toast.remove();
        if (this.activeTimer) {
          clearTimeout(this.activeTimer);
          this.activeTimer = null;
        }
      };
      toast.appendChild(btn);
    } else {
      this.activeTimer = setTimeout(() => {
        toast.remove();
        this.activeTimer = null;
      }, 3000);
    }

    this.container.appendChild(toast);
  }

  clear() {
    if (this.activeTimer) {
      clearTimeout(this.activeTimer);
      this.activeTimer = null;
    }
    if (this.container) {
      this.container.innerHTML = '';
    }
  }
}

export const toast = new ToastManager();
