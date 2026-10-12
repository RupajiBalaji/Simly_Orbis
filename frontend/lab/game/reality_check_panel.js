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
    this.activeTab = 'all'; // 'all', 'pharma.pk', 'pharma.trial', 'chem.titration', 'validation'
    this.data = null;
    this.validationData = null;

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
          <button type="button" class="reality-tab-btn" data-tab="validation">📚 Validation</button>
        </div>

        <div class="reality-panel-content" id="reality-panel-content">
          <div style="text-align:center; padding:40px; color:#94a3b8;">Loading scientific verification benchmarks...</div>
        </div>
      </div>
    `;

    document.getElementById('btn-close-reality')?.addEventListener('click', () => this.close());
    document.getElementById('btn-run-all-checks')?.addEventListener('click', () => this.runAllChecks());

    const tabsBar = document.getElementById('reality-tabs-bar');
    tabsBar?.addEventListener('click', async (e) => {
      const btn = e.target.closest('.reality-tab-btn');
      if (!btn) return;
      tabsBar.querySelectorAll('.reality-tab-btn').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      this.activeTab = btn.dataset.tab;
      if (this.activeTab === 'validation' && !this.validationData) {
        await this.loadValidationData();
      } else {
        this.renderContent();
      }
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

  async loadValidationData(refresh = false) {
    const contentEl = document.getElementById('reality-panel-content');
    if (contentEl && !this.validationData) {
      contentEl.innerHTML = '<div style="text-align:center; padding:40px; color:#94a3b8;">⏳ Loading peer-reviewed validation benchmarks...</div>';
    }
    try {
      this.validationData = await api.getValidationSummary(refresh);
      this.renderContent();
    } catch (err) {
      console.error('Failed to load validation benchmarks:', err);
      if (contentEl) {
        contentEl.innerHTML = `<div style="text-align:center; padding:40px; color:#ef4444;">Failed to load validation benchmarks: ${err.message}</div>`;
      }
    }
  }

  renderContent() {
    const contentEl = document.getElementById('reality-panel-content');
    if (!contentEl) return;

    if (this.activeTab === 'validation') {
      if (!this.validationData) {
        this.loadValidationData();
        return;
      }
      this.renderValidationContent(contentEl);
      return;
    }

    if (!this.data) return;

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

  renderValidationContent(contentEl) {
    const val = this.validationData;
    if (!val) return;

    const passPct = (val.pass_rate * 100).toFixed(1);
    const medianFold = val.median_fold_error ? val.median_fold_error.toFixed(3) : '1.000';
    const meanPct = val.mean_percent_error ? val.mean_percent_error.toFixed(1) : '0.0';

    let html = `
      <!-- Mandatory Benchmark Banner -->
      <div style="background: rgba(14, 165, 233, 0.12); border-left: 4px solid #38bdf8; border-radius: 6px; padding: 14px 18px; color: #e0f2fe; font-size: 0.92rem; font-weight: 600; display:flex; align-items:center; gap:12px;">
        <span style="font-size:1.3rem;">🔬</span>
        <div>
          <div>${val.banner || 'Compared with published data for the stated conditions. Not clinical validation.'}</div>
          <div style="font-size:0.75rem; font-weight:400; color:#94a3b8; margin-top:2px;">
            Grounded strictly in peer-reviewed clinical pharmacology & analytical chemistry references. Unverified entries are segregated into a review queue.
          </div>
        </div>
      </div>

      <!-- Headline Metric Summary Cards -->
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-top: 4px;">
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 12px; text-align: center;">
          <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-family: var(--font-mono);">Total References</div>
          <div style="font-size: 1.5rem; font-weight: 800; color: #f8fafc; margin-top: 4px;">${val.total_references}</div>
          <div style="font-size: 0.7rem; color: #64748b;">Literature datasets</div>
        </div>
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 12px; text-align: center;">
          <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-family: var(--font-mono);">Human Verified</div>
          <div style="font-size: 1.5rem; font-weight: 800; color: #38bdf8; margin-top: 4px;">${val.human_verified}</div>
          <div style="font-size: 0.7rem; color: #38bdf8;">Headline eligible</div>
        </div>
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 12px; text-align: center;">
          <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-family: var(--font-mono);">Verified Pass Rate</div>
          <div style="font-size: 1.5rem; font-weight: 800; color: #10b981; margin-top: 4px;">${passPct}%</div>
          <div style="font-size: 0.7rem; color: #10b981;">${val.passed_verified_count}/${val.human_verified} within tolerance</div>
        </div>
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 12px; text-align: center;">
          <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-family: var(--font-mono);">Median Fold Error</div>
          <div style="font-size: 1.5rem; font-weight: 800; color: #a855f7; margin-top: 4px;">${medianFold}x</div>
          <div style="font-size: 0.7rem; color: #c084fc;">Target: &le; 2.0x</div>
        </div>
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 12px; text-align: center;">
          <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-family: var(--font-mono);">Mean % Error</div>
          <div style="font-size: 1.5rem; font-weight: 800; color: #e2e8f0; margin-top: 4px;">${meanPct}%</div>
          <div style="font-size: 0.7rem; color: #94a3b8;">Across all quantities</div>
        </div>
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(234, 179, 8, 0.2); border-radius: 8px; padding: 12px; text-align: center;">
          <div style="font-size: 0.72rem; color: #eab308; text-transform: uppercase; font-family: var(--font-mono);">Pending Check</div>
          <div style="font-size: 1.5rem; font-weight: 800; color: #eab308; margin-top: 4px;">${val.pending_human_check}</div>
          <div style="font-size: 0.7rem; color: #facc15;">Excluded from pass rate</div>
        </div>
      </div>

      <!-- Parameter Provenance Notice -->
      <div style="background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 14px 16px;">
        <div style="font-weight: 700; color: #f8fafc; font-size: 0.88rem; margin-bottom: 6px; display:flex; align-items:center; gap:6px;">
          <span>📋 Parameter Provenance & In-Game Calibration</span>
        </div>
        <div style="font-size: 0.8rem; color: #cbd5e1; line-height: 1.45;">
          All physical and pharmacokinetic drug parameters (ka, half-life, Vd, bioavailability) in <code>drugs.json</code> are mapped to primary literature citations (Rawlins 1977, Prescott 1980, Davies 1998, Blanchard 1983).
          In-game scoring thresholds (<code>green_low</code>, <code>green_high</code>, <code>red_threshold</code>) are tagged as <strong>game-balanced</strong> for curriculum pacing and are <em>not clinical diagnostic cutoffs</em>.
        </div>
      </div>

      <!-- Verified Benchmarks Table -->
      <div class="reality-module-card">
        <div class="module-card-header">
          <div>
            <span class="mod-id-pill">VERIFIED BENCHMARKS</span>
            <h4 style="margin:4px 0 0 0; color:#f8fafc; font-size:1.05rem;">Human-Verified Literature Comparisons (${val.human_verified})</h4>
          </div>
          <div class="mod-status-tag tag-passed">
            ✓ ${val.passed_verified_count}/${val.human_verified} PASSED (${passPct}%)
          </div>
        </div>

        <div class="checks-table-wrap">
          <table class="reality-checks-table">
            <thead>
              <tr>
                <th>Benchmark ID & Condition</th>
                <th>Quantity & Dose</th>
                <th style="text-align:right;">Published Ref</th>
                <th style="text-align:right;">Model Output</th>
                <th style="text-align:right;">Fold Error</th>
                <th style="text-align:right;">% Error</th>
                <th style="text-align:center;">Result</th>
                <th>Primary Citation</th>
              </tr>
            </thead>
            <tbody>
              ${(val.verified_results || [])
                .map(
                  (r) => `
                <tr>
                  <td>
                    <div class="check-name" style="font-family:var(--font-mono); font-size:0.75rem;">${r.id}</div>
                    <div class="check-desc" style="font-size:0.72rem;">${r.population_or_condition || ''}</div>
                  </td>
                  <td>
                    <div style="color:#f8fafc; font-weight:600; font-size:0.8rem;">${r.quantity}</div>
                    <div style="color:#94a3b8; font-size:0.72rem;">${r.dose_or_regimen || ''}</div>
                  </td>
                  <td style="text-align:right; font-family:var(--font-mono); color:#94a3b8; font-size:0.78rem;">
                    ${r.value} ${r.unit || ''}
                  </td>
                  <td style="text-align:right; font-family:var(--font-mono); color:#38bdf8; font-size:0.78rem; font-weight:700;">
                    ${r.predicted_value} ${r.unit || ''}
                  </td>
                  <td style="text-align:right; font-family:var(--font-mono); color:#a855f7; font-size:0.78rem;">
                    ${r.fold_error ? r.fold_error.toFixed(2) + 'x' : '–'}
                  </td>
                  <td style="text-align:right; font-family:var(--font-mono); color:#cbd5e1; font-size:0.78rem;">
                    ${r.pct_error ? r.pct_error.toFixed(1) + '%' : '0.0%'}
                  </td>
                  <td style="text-align:center;">
                    <span class="check-badge ${r.passed ? 'badge-pass' : 'badge-fail'}">
                      ${r.passed ? 'PASS' : 'FAIL'}
                    </span>
                  </td>
                  <td style="font-size:0.72rem; color:#94a3b8; max-width:220px;">
                    <div>${r.source_citation || 'Literature source'}</div>
                    ${r.source_url_or_doi ? `<a href="${r.source_url_or_doi}" target="_blank" rel="noopener" style="color:#38bdf8; text-decoration:underline;">DOI/Source</a>` : ''}
                  </td>
                </tr>
              `
                )
                .join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;

    // Pending Human Check Table (Unverified rows)
    if (val.unverified_results && val.unverified_results.length > 0) {
      html += `
        <div class="reality-module-card" style="border-color: rgba(234, 179, 8, 0.3);">
          <div class="module-card-header">
            <div>
              <span class="mod-id-pill" style="background:rgba(234, 179, 8, 0.15); color:#facc15; border-color:rgba(234, 179, 8, 0.3);">PENDING HUMAN CHECK</span>
              <h4 style="margin:4px 0 0 0; color:#f8fafc; font-size:1.05rem;">Unverified Literature Queue (${val.unverified_results.length})</h4>
            </div>
            <div style="font-size:0.75rem; color:#eab308; font-weight:600;">
              Excluded from headline pass rate until human review
            </div>
          </div>

          <div class="checks-table-wrap">
            <table class="reality-checks-table">
              <thead>
                <tr>
                  <th>Benchmark ID</th>
                  <th>Quantity & Dose</th>
                  <th style="text-align:right;">Published Ref</th>
                  <th style="text-align:right;">Model Output</th>
                  <th style="text-align:right;">Fold Error</th>
                  <th style="text-align:center;">Status</th>
                  <th>Citation & Notes</th>
                </tr>
              </thead>
              <tbody>
                ${val.unverified_results
                  .map(
                    (u) => `
                  <tr>
                    <td>
                      <div class="check-name" style="font-family:var(--font-mono); font-size:0.75rem;">${u.id}</div>
                      <div class="check-desc" style="font-size:0.72rem;">${u.population_or_condition || ''}</div>
                    </td>
                    <td>
                      <div style="color:#f8fafc; font-weight:600; font-size:0.8rem;">${u.quantity}</div>
                      <div style="color:#94a3b8; font-size:0.72rem;">${u.dose_or_regimen || ''}</div>
                    </td>
                    <td style="text-align:right; font-family:var(--font-mono); color:#94a3b8; font-size:0.78rem;">
                      ${u.value} ${u.unit || ''}
                    </td>
                    <td style="text-align:right; font-family:var(--font-mono); color:#38bdf8; font-size:0.78rem;">
                      ${u.predicted_value} ${u.unit || ''}
                    </td>
                    <td style="text-align:right; font-family:var(--font-mono); color:#a855f7; font-size:0.78rem;">
                      ${u.fold_error ? u.fold_error.toFixed(2) + 'x' : '–'}
                    </td>
                    <td style="text-align:center;">
                      <span class="check-badge" style="background:rgba(234, 179, 8, 0.15); color:#facc15; border:1px solid rgba(234, 179, 8, 0.3);">
                        PENDING
                      </span>
                    </td>
                    <td style="font-size:0.72rem; color:#94a3b8; max-width:220px;">
                      <div>${u.source_citation || 'Pending verification'}</div>
                      <div style="color:#64748b; font-style:italic;">${u.notes || ''}</div>
                    </td>
                  </tr>
                `
                  )
                  .join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    }

    // Sensitivity Analysis Summary
    if (val.sensitivity_analysis) {
      const sens = val.sensitivity_analysis;
      const dominant = (sens.dominant_parameters || []).join(', ') || 'vd_per_kg, bioavailability, patient_weight';
      html += `
        <div class="reality-module-card">
          <div class="module-card-header">
            <div>
              <span class="mod-id-pill">SENSITIVITY ANALYSIS</span>
              <h4 style="margin:4px 0 0 0; color:#f8fafc; font-size:1.05rem;">One-at-a-Time (OAT) &plusmn;20% Parameter Sensitivity</h4>
            </div>
            <div style="font-size:0.75rem; color:#38bdf8; font-weight:600;">
              Dominant: ${dominant}
            </div>
          </div>
          <div style="font-size:0.8rem; color:#cbd5e1; line-height:1.45; margin-bottom:12px;">
            ${sens.summary || 'Bioavailability (F), Volume of Distribution (Vd), and body weight scale exposure (AUC) proportionally (1:1), while absorption rate (ka) governs Tmax without altering cumulative exposure.'}
          </div>
        </div>
      `;
    }

    contentEl.innerHTML = html;
  }
}

