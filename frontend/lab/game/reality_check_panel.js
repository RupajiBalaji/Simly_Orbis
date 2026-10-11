/**
 * Reality Check Panel & Scientific Model Cards (frontend/lab/game/reality_check_panel.js)
 * Manages simulation verification benchmarks, live test execution, analytical checkmarks,
 * and scientific model card documentation.
 */

import { api } from '../api.js';
import { state } from '../state.js';
import { toast } from './toast.js';

export class RealityCheckPanel {
  constructor(scene) {
    this.scene = scene;
    this.isOpen = false;
    this.activeTab = 'all'; // 'all', 'pharma.pk', 'pharma.trial', 'chem.titration'
    this.data = null;

    this.panelEl = document.getElementById('reality-check-panel');
    this.initDOM();
  }

  initDOM() {
    if (!this.panelEl) return;

    this.panelEl.innerHTML = `
      <div class="reality-panel-modal">
        <div class="reality-panel-header">
          <div class="reality-title-wrap">
            <span class="reality-badge">⚖️ SIMULATION AUDIT</span>
            <div style="display:flex; align-items:center; gap:12px;">
              <h3 style="margin:0; font-size:1.3rem; font-weight:800; color:#f8fafc;">Simulation Reality Checks</h3>
              <span class="reality-summary-badge" id="reality-summary-badge">11/11 passed</span>
            </div>
          </div>
          <div style="display:flex; align-items:center; gap:8px;">
            <button type="button" class="btn-run-checks" id="btn-run-all-checks">🔄 Run All Checks</button>
            <button type="button" class="btn-close-reality" id="btn-close-reality">✕ Close</button>
          </div>
        </div>

        <div class="reality-disclaimer-bar">
          Educational simulation only. Not validated for clinical dosing or industrial chemical process control.
        </div>

        <div class="reality-tabs-bar" id="reality-tabs-bar">
          <button type="button" class="reality-tab-btn active" data-tab="all">All Engines (11)</button>
          <button type="button" class="reality-tab-btn" data-tab="pharma.pk">pharma.pk (3)</button>
          <button type="button" class="reality-tab-btn" data-tab="pharma.trial">pharma.trial (4)</button>
          <button type="button" class="reality-tab-btn" data-tab="chem.titration">chem.titration (4)</button>
        </div>

        <div class="reality-panel-content" id="reality-panel-content">
          <div style="text-align:center; padding:40px; color:#94a3b8;">Loading scientific verification benchmarks...</div>
        </div>
      </div>
    `;

    document.getElementById('btn-close-reality')?.addEventListener('click', () => this.close());
    document.getElementById('btn-run-all-checks')?.addEventListener('click', () => this.runAllChecks());

    const tabsBar = document.getElementById('reality-tabs-bar');
    tabsBar?.addEventListener('click', (e) => {
      const btn = e.target.closest('.reality-tab-btn');
      if (!btn) return;
      tabsBar.querySelectorAll('.reality-tab-btn').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      this.activeTab = btn.dataset.tab;
      this.renderContent();
    });
  }

  async open() {
    if (!this.panelEl) return;
    this.isOpen = true;
    this.panelEl.classList.remove('hidden');

    if (!this.data) {
      await this.runAllChecks();
    } else {
      this.renderContent();
    }
  }

  close() {
    if (!this.panelEl) return;
    this.isOpen = false;
    this.panelEl.classList.add('hidden');
    if (this.scene) {
      this.scene.resetCameraView();
    }
  }

  async runAllChecks() {
    const btn = document.getElementById('btn-run-all-checks');
    if (btn) {
      btn.disabled = true;
      btn.textContent = '⏳ Executing Checks...';
    }

    try {
      this.data = await api.getAllRealityChecks();
      const badge = document.getElementById('reality-summary-badge');
      if (badge && this.data) {
        badge.textContent = this.data.summary_badge || '11/11 passed';
      }
      // Update 3D wall board texture if present
      const board = this.scene?.getApparatus('reality_check_board');
      if (board?.userData?.updateBoard) {
        board.userData.updateBoard(this.data.total_passed, this.data.total_checks);
      }
      toast.showSuccess(`Verified ${this.data.total_passed}/${this.data.total_checks} engine reality checks.`);
      this.renderContent();
    } catch (err) {
      console.error('Failed to run reality checks:', err);
      toast.showError('Reality checks execution failed.');
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = '🔄 Run All Checks';
      }
    }
  }

  renderContent() {
    const contentEl = document.getElementById('reality-panel-content');
    if (!contentEl || !this.data) return;

    const modules = this.data.modules || {};
    const moduleKeys = this.activeTab === 'all'
      ? Object.keys(modules)
      : [this.activeTab].filter((k) => modules[k]);

    let html = '';

    for (const key of moduleKeys) {
      const mod = modules[key];
      if (!mod) continue;
      const card = mod.model_card || {};

      html += `
        <div class="reality-module-card">
          <div class="module-card-header">
            <div>
              <span class="mod-id-pill">${mod.module_id}</span>
              <h4 style="margin:4px 0 0 0; color:#f8fafc; font-size:1.1rem;">${mod.name}</h4>
            </div>
            <div class="mod-status-tag ${mod.passed ? 'tag-passed' : 'tag-failed'}">
              ${mod.passed ? '✓ ALL CHECKS PASSED' : '⚠️ BENCHMARK DEVIATION'} (${mod.passed_count}/${mod.total})
            </div>
          </div>

          <!-- Structured Checks Table -->
          <div class="checks-table-wrap">
            <table class="reality-checks-table">
              <thead>
                <tr>
                  <th>Benchmark Name & Description</th>
                  <th style="text-align:right;">Expected</th>
                  <th style="text-align:right;">Actual</th>
                  <th style="text-align:right;">Tolerance</th>
                  <th style="text-align:center;">Result</th>
                </tr>
              </thead>
              <tbody>
                ${mod.checks
                  .map(
                    (c) => `
                  <tr>
                    <td>
                      <div class="check-name">${c.name}</div>
                      <div class="check-desc">${c.description}</div>
                      <div class="check-source">Source: ${c.source_note}</div>
                    </td>
                    <td style="text-align:right; font-family:var(--font-mono); color:#94a3b8;">${c.expected}</td>
                    <td style="text-align:right; font-family:var(--font-mono); color:#38bdf8;">${c.actual}</td>
                    <td style="text-align:right; font-family:var(--font-mono); color:#cbd5e1;">${(c.tolerance * 100).toFixed(1)}%</td>
                    <td style="text-align:center;">
                      <span class="check-badge ${c.passed ? 'badge-pass' : 'badge-fail'}">
                        ${c.passed ? 'PASS' : 'FAIL'}
                      </span>
                    </td>
                  </tr>
                `
                  )
                  .join('')}
              </tbody>
            </table>
          </div>

          <!-- Scientific Model Card Section -->
          <div class="model-card-box">
            <div class="model-card-title">🔬 Scientific Model Card (${mod.module_id})</div>
            <div class="model-card-grid">
              <div class="card-col">
                <strong>Underlying Physical Models:</strong>
                <ul>
                  ${(card.underlying_models || []).map((m) => `<li>${m}</li>`).join('')}
                </ul>
              </div>
              <div class="card-col">
                <strong>Key Assumptions:</strong>
                <ul>
                  ${(card.key_assumptions || []).map((a) => `<li>${a}</li>`).join('')}
                </ul>
              </div>
              <div class="card-col">
                <strong>Known Limitations:</strong>
                <ul>
                  ${(card.known_limitations || []).map((l) => `<li>${l}</li>`).join('')}
                </ul>
              </div>
            </div>
            <div class="card-disclaimer-note">
              <strong>Mandatory Disclaimer:</strong> ${card.disclaimer || 'Educational simulation only.'}
            </div>
          </div>
        </div>
      `;
    }

    contentEl.innerHTML = html;
  }
}
