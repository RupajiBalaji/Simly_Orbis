/**
 * Simly Orbis Shared Component Library (frontend/ui/components.js)
 * Standard: Section 7.3 & Section 18 (P1-T2) of Simly Orbis MVP Build Specification.
 */

export function createButton({ label, variant = 'primary', onClick, disabled = false, ariaLabel }) {
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = `btn btn-${variant}`;
  btn.textContent = label;
  if (disabled) btn.disabled = true;
  if (ariaLabel) btn.setAttribute('aria-label', ariaLabel);
  if (onClick) btn.addEventListener('click', onClick);
  return btn;
}

export function createCard({ title, body, variant = 'default' }) {
  const card = document.createElement('div');
  card.className = `card ${variant !== 'default' ? 'card-' + variant : ''}`;
  if (title) {
    const h3 = document.createElement('h3');
    h3.className = 'card-title';
    h3.textContent = title;
    card.appendChild(h3);
  }
  if (body) {
    const p = document.createElement('div');
    p.className = 'card-body';
    if (typeof body === 'string') p.textContent = body;
    else p.appendChild(body);
    card.appendChild(p);
  }
  return card;
}

export function createModal({ title, content, onClose }) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.setAttribute('role', 'dialog');
  overlay.setAttribute('aria-modal', 'true');
  overlay.setAttribute('aria-labelledby', 'modal-title-id');

  const modal = document.createElement('div');
  modal.className = 'modal';

  const header = document.createElement('div');
  header.className = 'modal-header';

  const h2 = document.createElement('h2');
  h2.id = 'modal-title-id';
  h2.className = 'modal-title';
  h2.textContent = title;

  const closeBtn = document.createElement('button');
  closeBtn.type = 'button';
  closeBtn.className = 'modal-close';
  closeBtn.setAttribute('aria-label', 'Close dialog');
  closeBtn.innerHTML = '&times;';

  const close = () => {
    overlay.remove();
    if (onClose) onClose();
  };

  closeBtn.addEventListener('click', close);
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) close();
  });

  header.appendChild(h2);
  header.appendChild(closeBtn);
  modal.appendChild(header);

  const bodyEl = document.createElement('div');
  bodyEl.className = 'modal-body';
  if (typeof content === 'string') bodyEl.textContent = content;
  else bodyEl.appendChild(content);
  modal.appendChild(bodyEl);

  overlay.appendChild(modal);
  document.body.appendChild(overlay);

  // Focus trap: focus close button initially
  closeBtn.focus();
  return { overlay, close };
}

export function showToast({ message, type = 'info', duration = 3000 }) {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.setAttribute('role', 'status');
  toast.setAttribute('aria-live', 'polite');
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.remove();
    if (container.children.length === 0) container.remove();
  }, duration);
}

export function initTabs(containerEl) {
  const tabs = containerEl.querySelectorAll('[role="tab"]');
  const panels = containerEl.querySelectorAll('[role="tabpanel"]');

  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => {
        t.setAttribute('aria-selected', 'false');
        t.setAttribute('tabindex', '-1');
      });
      panels.forEach(p => p.setAttribute('hidden', 'true'));

      tab.setAttribute('aria-selected', 'true');
      tab.removeAttribute('tabindex');
      const targetId = tab.getAttribute('aria-controls');
      const targetPanel = containerEl.querySelector(`#${targetId}`);
      if (targetPanel) targetPanel.removeAttribute('hidden');
    });

    // Keyboard navigation (ArrowLeft / ArrowRight)
    tab.addEventListener('keydown', (e) => {
      let targetIndex = null;
      if (e.key === 'ArrowRight') targetIndex = (index + 1) % tabs.length;
      else if (e.key === 'ArrowLeft') targetIndex = (index - 1 + tabs.length) % tabs.length;

      if (targetIndex !== null) {
        tabs[targetIndex].focus();
        tabs[targetIndex].click();
      }
    });
  });
}

export function createSliderInput({ label, min = 0, max = 100, step = 1, value = 50, unit = '', onChange }) {
  const group = document.createElement('div');
  group.className = 'slider-group';

  const header = document.createElement('div');
  header.className = 'slider-header';

  const lbl = document.createElement('label');
  lbl.className = 'slider-label';
  lbl.textContent = label;
  header.appendChild(lbl);
  group.appendChild(header);

  const controls = document.createElement('div');
  controls.className = 'slider-controls';

  const range = document.createElement('input');
  range.type = 'range';
  range.className = 'slider-input';
  range.min = min;
  range.max = max;
  range.step = step;
  range.value = value;
  range.setAttribute('aria-label', `${label} slider`);

  const num = document.createElement('input');
  num.type = 'number';
  num.className = 'slider-number';
  num.min = min;
  num.max = max;
  num.step = step;
  num.value = value;
  num.setAttribute('aria-label', `${label} value`);

  const unitSpan = document.createElement('span');
  unitSpan.className = 'slider-unit';
  unitSpan.textContent = unit;

  const sync = (newVal) => {
    range.value = newVal;
    num.value = newVal;
    if (onChange) onChange(parseFloat(newVal));
  };

  range.addEventListener('input', (e) => sync(e.target.value));
  num.addEventListener('input', (e) => sync(e.target.value));

  controls.appendChild(range);
  controls.appendChild(num);
  controls.appendChild(unitSpan);
  group.appendChild(controls);

  return group;
}

export function createStepper({ steps = [], currentStep = 0 }) {
  const stepper = document.createElement('nav');
  stepper.className = 'stepper';
  stepper.setAttribute('aria-label', 'Experiment progress steps');

  steps.forEach((title, idx) => {
    const item = document.createElement('div');
    item.className = 'step-item';
    if (idx < currentStep) item.classList.add('completed');
    else if (idx === currentStep) item.classList.add('active');

    const badge = document.createElement('span');
    badge.className = 'step-badge';
    badge.textContent = idx < currentStep ? '✓' : String(idx + 1);

    const stepTitle = document.createElement('span');
    stepTitle.className = 'step-title';
    stepTitle.textContent = title;

    item.appendChild(badge);
    item.appendChild(stepTitle);
    stepper.appendChild(item);
  });

  return stepper;
}

export function createReadout({ label, value, unit = '', sourceChip = 'engine' }) {
  const card = document.createElement('div');
  card.className = 'readout-card';

  const header = document.createElement('div');
  header.className = 'readout-header';

  const lbl = document.createElement('span');
  lbl.className = 'readout-label';
  lbl.textContent = label;

  const chip = document.createElement('span');
  chip.className = `source-chip chip-${sourceChip}`;
  chip.textContent = sourceChip;

  header.appendChild(lbl);
  header.appendChild(chip);
  card.appendChild(header);

  const valEl = document.createElement('div');
  valEl.className = 'readout-val';
  valEl.textContent = String(value);

  if (unit) {
    const u = document.createElement('span');
    u.className = 'readout-unit';
    u.textContent = unit;
    valEl.appendChild(u);
  }

  card.appendChild(valEl);
  return card;
}

export function createBadge({ text, variant = 'neutral' }) {
  const b = document.createElement('span');
  b.className = `badge badge-${variant}`;
  b.textContent = text;
  return b;
}

export function createBanner({ text, variant = 'warn' }) {
  const banner = document.createElement('aside');
  banner.className = 'disclaimer-banner';
  banner.setAttribute('role', 'note');
  banner.innerHTML = `<span aria-hidden="true">⚠️</span><span>${text}</span>`;
  return banner;
}

export function createCommandBar({ placeholder = 'Ask Orbis or enter instruction... (press / to focus)', onCommand }) {
  const bar = document.createElement('form');
  bar.className = 'command-bar';
  bar.setAttribute('role', 'search');

  const input = document.createElement('input');
  input.type = 'text';
  input.className = 'command-input';
  input.placeholder = placeholder;
  input.setAttribute('aria-label', 'Ask Orbis command bar');

  const kbd = document.createElement('kbd');
  kbd.className = 'command-kbd';
  kbd.textContent = '/';

  bar.appendChild(input);
  bar.appendChild(kbd);

  // Global / shortcut focuses the input
  window.addEventListener('keydown', (e) => {
    if (e.key === '/' && document.activeElement !== input) {
      e.preventDefault();
      input.focus();
    }
  });

  bar.addEventListener('submit', (e) => {
    e.preventDefault();
    if (onCommand && input.value.trim()) {
      onCommand(input.value.trim());
      input.value = '';
    }
  });

  return bar;
}
