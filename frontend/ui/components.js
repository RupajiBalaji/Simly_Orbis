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

export const PROVENANCE_METADATA = {
  engine: {
    label: 'Engine',
    badgeClass: 'chip-engine',
    title: 'Deterministic Engine Calculation',
    description: 'Evaluated deterministically by pure Python backend engine (Bateman oral PK, Henderson-Hasselbalch, Tsiolkovsky orbital mechanics, or Hill Emax differential solver). Zero LLM hallucination.',
    modelCard: '/docs/model_cards/pharma_pk.md',
    verification: 'Verified Pure Engine Math'
  },
  game: {
    label: 'Game',
    badgeClass: 'chip-game',
    title: 'Apparatus / Game State',
    description: 'Interactive laboratory instrument measurement, sensor telemetry, or simplified educational apparatus reading.',
    modelCard: null,
    verification: 'Game-Balanced Usability'
  },
  lit: {
    label: 'Lit',
    badgeClass: 'chip-lit',
    title: 'Literature Reference Benchmark',
    description: 'Published primary scientific literature benchmark value. Governed under rule R3/G5: all rows remain strictly labelled unverified pending formal human expert certification.',
    modelCard: '/docs/model_cards/pharma_pk.md',
    verification: 'N/A: unverified'
  },
  ai: {
    label: 'AI',
    badgeClass: 'chip-ai',
    title: 'AI Proposed Parameter (Dr. Orbis)',
    description: 'Natural language instruction interpretation and mentor dialogue suggestions. Bounded and validated by deterministic backend safety guards.',
    modelCard: null,
    verification: 'Bounded by Engine Guards'
  }
};

let _popoverHideTimeout = null;

export function scheduleHidePopover(delay = 200) {
  if (_popoverHideTimeout) clearTimeout(_popoverHideTimeout);
  _popoverHideTimeout = setTimeout(() => {
    hideProvenancePopover();
  }, delay);
}

export function cancelHidePopover() {
  if (_popoverHideTimeout) {
    clearTimeout(_popoverHideTimeout);
    _popoverHideTimeout = null;
  }
}

export function hideProvenancePopover() {
  const popover = document.getElementById('provenance-popover-instance');
  if (popover) {
    popover.classList.remove('visible');
    popover.setAttribute('aria-hidden', 'true');
  }
  document.querySelectorAll('.source-chip[aria-expanded="true"]').forEach((chip) => {
    chip.setAttribute('aria-expanded', 'false');
  });
}

export function showProvenancePopover(targetEl) {
  cancelHidePopover();
  let popover = document.getElementById('provenance-popover-instance');
  if (!popover) {
    popover = document.createElement('div');
    popover.id = 'provenance-popover-instance';
    popover.className = 'provenance-popover';
    popover.setAttribute('role', 'dialog');
    popover.setAttribute('aria-label', 'Provenance Information');
    document.body.appendChild(popover);

    popover.addEventListener('mouseenter', () => cancelHidePopover());
    popover.addEventListener('mouseleave', () => scheduleHidePopover());
  }

  const rawType = targetEl.getAttribute('data-source-type') || 
                  (targetEl.textContent.toLowerCase().includes('engine') ? 'engine' :
                   targetEl.textContent.toLowerCase().includes('lit') ? 'lit' :
                   targetEl.textContent.toLowerCase().includes('game') ? 'game' :
                   targetEl.textContent.toLowerCase().includes('ai') ? 'ai' : 'engine');
  const cleanType = String(rawType).toLowerCase().trim();
  const meta = PROVENANCE_METADATA[cleanType] || PROVENANCE_METADATA.engine;
  const customDetails = targetEl.getAttribute('data-provenance-details');
  const customModelCard = targetEl.getAttribute('data-model-card') || meta.modelCard;

  const modelCardLink = customModelCard 
    ? `<a href="${customModelCard}" target="_blank" rel="noopener" class="btn btn-secondary" style="min-height:28px; padding:2px 8px; font-size:11px; text-decoration:none;">View Model Card ↗</a>`
    : '';

  const isUnverified = meta.verification === 'N/A: unverified' || targetEl.getAttribute('data-verification') === 'unverified';
  const verificationBadge = isUnverified
    ? '<span class="badge badge-warn">N/A: unverified</span>'
    : `<span class="badge badge-ok">${meta.verification}</span>`;

  popover.innerHTML = `
    <div class="provenance-popover-header">
      <span class="provenance-popover-title">
        <span class="source-chip ${meta.badgeClass}">[${meta.label}]</span>
        <span>${meta.title}</span>
      </span>
      <button type="button" class="provenance-popover-close" aria-label="Close popover">&times;</button>
    </div>
    <div class="provenance-popover-body">
      ${customDetails || meta.description}
    </div>
    <div class="provenance-popover-footer">
      <div>${verificationBadge}</div>
      <div>${modelCardLink}</div>
    </div>
  `;

  popover.querySelector('.provenance-popover-close')?.addEventListener('click', (e) => {
    e.stopPropagation();
    hideProvenancePopover();
  });

  // Calculate positioning
  const rect = targetEl.getBoundingClientRect();
  const popoverWidth = 320;
  let top = rect.bottom + 6;
  let left = rect.left + (rect.width / 2) - (popoverWidth / 2);

  if (left < 10) left = 10;
  if (left + popoverWidth > window.innerWidth - 10) {
    left = window.innerWidth - popoverWidth - 10;
  }
  if (top + 180 > window.innerHeight) {
    top = Math.max(10, rect.top - 180);
  }

  popover.style.top = `${Math.round(top)}px`;
  popover.style.left = `${Math.round(left)}px`;
  popover.classList.add('visible');
  popover.removeAttribute('aria-hidden');
  targetEl.setAttribute('aria-expanded', 'true');
}

export function toggleProvenancePopover(targetEl) {
  const isExpanded = targetEl.getAttribute('aria-expanded') === 'true';
  if (isExpanded) {
    hideProvenancePopover();
  } else {
    showProvenancePopover(targetEl);
  }
}

export function createSourceChip({ type = 'engine', label = null, details = null, modelCard = null, verification = null }) {
  const cleanType = String(type).toLowerCase().replace(/[^a-z]/g, '') || 'engine';
  const meta = PROVENANCE_METADATA[cleanType] || PROVENANCE_METADATA.engine;
  const chip = document.createElement('button');
  chip.type = 'button';
  chip.className = `source-chip chip-${cleanType}`;
  chip.setAttribute('data-source-type', cleanType);
  chip.setAttribute('role', 'button');
  chip.setAttribute('tabindex', '0');
  chip.setAttribute('aria-haspopup', 'dialog');
  chip.setAttribute('aria-expanded', 'false');
  chip.setAttribute('aria-label', `Source: [${meta.label}]. Click or hover for provenance details.`);
  chip.textContent = `[${label || meta.label}]`;

  if (details) chip.setAttribute('data-provenance-details', details);
  if (modelCard) chip.setAttribute('data-model-card', modelCard);
  if (verification) chip.setAttribute('data-verification', verification);

  chip.addEventListener('click', (e) => {
    e.stopPropagation();
    toggleProvenancePopover(chip);
  });
  chip.addEventListener('mouseenter', () => {
    showProvenancePopover(chip);
  });
  chip.addEventListener('mouseleave', () => {
    scheduleHidePopover();
  });
  chip.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      toggleProvenancePopover(chip);
    } else if (e.key === 'Escape') {
      hideProvenancePopover();
    }
  });

  return chip;
}

export function initProvenancePopovers(root = document) {
  const chips = root.querySelectorAll('.source-chip');
  chips.forEach((chip) => {
    if (chip.dataset.popoverBound === 'true') return;
    chip.dataset.popoverBound = 'true';
    if (!chip.getAttribute('tabindex')) chip.setAttribute('tabindex', '0');
    if (!chip.getAttribute('role')) chip.setAttribute('role', 'button');
    if (!chip.getAttribute('aria-haspopup')) chip.setAttribute('aria-haspopup', 'dialog');
    if (!chip.getAttribute('aria-expanded')) chip.setAttribute('aria-expanded', 'false');

    chip.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleProvenancePopover(chip);
    });
    chip.addEventListener('mouseenter', () => {
      showProvenancePopover(chip);
    });
    chip.addEventListener('mouseleave', () => {
      scheduleHidePopover();
    });
    chip.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        toggleProvenancePopover(chip);
      } else if (e.key === 'Escape') {
        hideProvenancePopover();
      }
    });
  });

  // Global listeners
  if (!window._provenanceGlobalBound) {
    window._provenanceGlobalBound = true;
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.provenance-popover') && !e.target.closest('.source-chip')) {
        hideProvenancePopover();
      }
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        hideProvenancePopover();
      }
    });
    window.addEventListener('resize', () => {
      hideProvenancePopover();
    });
  }
}

export function createReadout({ label, value, unit = '', sourceChip = 'engine' }) {
  const card = document.createElement('div');
  card.className = 'readout-card';

  const header = document.createElement('div');
  header.className = 'readout-header';

  const lbl = document.createElement('span');
  lbl.className = 'readout-label';
  lbl.textContent = label;

  const chip = createSourceChip({ type: sourceChip });

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
