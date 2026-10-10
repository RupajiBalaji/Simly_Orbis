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
  }

  showInfo(message, durationMs = 3000) {
    const toast = document.createElement('div');
    toast.className = 'toast toast-info';
    toast.textContent = message;
    this.container.appendChild(toast);

    setTimeout(() => {
      toast.remove();
    }, durationMs);
  }

  showViolation(violation) {
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
      btn.onclick = () => toast.remove();
      toast.appendChild(btn);
    } else {
      setTimeout(() => {
        toast.remove();
      }, 5000);
    }

    this.container.appendChild(toast);
  }
}

export const toast = new ToastManager();
