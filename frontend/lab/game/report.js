/**
 * Final Report & Leaderboard Screen (frontend/lab/game/report.js)
 * Displays post-session score breakdown, letter grades, violations, and leaderboard.
 */

import { api } from '../api.js';
import { state } from '../state.js';

export class ReportScreen {
  constructor() {
    this.screenEl = document.getElementById('screen-report');
    this.contentEl = document.getElementById('report-content');
  }

  show(reportData) {
    if (!this.screenEl || !this.contentEl) return;
    this.screenEl.classList.remove('hidden');

    const score = reportData.score ?? 0;
    const grade = reportData.grade || (score >= 85 ? 'A' : score >= 70 ? 'B' : score >= 50 ? 'C' : 'D');
    const breakdown = reportData.score_breakdown || { safety: 0, accuracy: 0, technique: 0, protocol: 0 };
    const violations = reportData.violations || [];
    const lessons = reportData.lessons_learned || [];

    this.contentEl.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px;">
        <div>
          <h2 style="font-size:1.8rem; font-weight:800; margin-bottom:4px;">Laboratory Performance Report</h2>
          <p style="color:#94a3b8; font-size:0.9rem;">Researcher: <strong style="color:#f8fafc;">${reportData.nickname || 'Researcher'}</strong> | Session ID: ${reportData.session_id ? reportData.session_id.slice(0, 8) : ''}</p>
        </div>
        <div class="report-grade-badge grade-${grade}">${grade}</div>
      </div>

      <div style="text-align:center; margin-bottom:20px;">
        <span style="font-size:2.8rem; font-weight:800; font-family:var(--font-mono); color:#c084fc;">${score}</span>
        <span style="font-size:1.2rem; color:#94a3b8;"> / 100</span>
      </div>

      <div class="score-breakdown-grid">
        <div class="score-cell">
          <div class="score-cell-label">Safety (40%)</div>
          <div class="score-cell-val" style="color:#10b981;">${breakdown.safety || 0} / 40</div>
        </div>
        <div class="score-cell">
          <div class="score-cell-label">Accuracy (30%)</div>
          <div class="score-cell-val" style="color:#38bdf8;">${breakdown.accuracy || 0} / 30</div>
        </div>
        <div class="score-cell">
          <div class="score-cell-label">Technique (20%)</div>
          <div class="score-cell-val" style="color:#ec4899;">${breakdown.technique || 0} / 20</div>
        </div>
        <div class="score-cell">
          <div class="score-cell-label">Protocol (10%)</div>
          <div class="score-cell-val" style="color:#f59e0b;">${breakdown.protocol || 0} / 10</div>
        </div>
      </div>

      ${
        violations.length > 0
          ? `
        <div style="margin-bottom:20px;">
          <h4 style="font-size:0.85rem; color:#f87171; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Safety Breaches Recorded (${violations.length})</h4>
          <div style="display:flex; flex-direction:column; gap:6px;">
            ${violations
              .map(
                (v) => `
              <div style="background:rgba(239,68,68,0.1); border-left:3px solid #ef4444; padding:8px 12px; border-radius:6px; font-size:0.82rem;">
                <strong style="color:#fee2e2;">[${v.severity.toUpperCase()}] ${v.title}:</strong> <span style="color:#fca5a5;">${v.explanation}</span>
              </div>
            `
              )
              .join('')}
          </div>
        </div>
      `
          : `
        <div style="background:rgba(16,185,129,0.1); border-left:3px solid #10b981; padding:10px 14px; border-radius:6px; margin-bottom:20px; font-size:0.85rem; color:#6ee7b7;">
          ✓ Flawless laboratory compliance: Zero safety or protocol violations detected.
        </div>
      `
      }

      <div style="margin-bottom:24px;">
        <h4 style="font-size:0.85rem; color:var(--text-highlight); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">Pedagogical Lessons Learned</h4>
        <ul style="list-style:none; padding-left:4px;">
          ${lessons
            .map(
              (l) => `
            <li style="font-size:0.85rem; color:#cbd5e1; padding:4px 0 4px 16px; position:relative;">
              <span style="position:absolute; left:0; color:#c084fc;">▸</span> ${l}
            </li>
          `
            )
            .join('')}
        </ul>
      </div>

      <div id="report-leaderboard-section" style="margin-bottom:28px;">
        <h4 style="font-size:0.85rem; color:#38bdf8; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">District Leaderboard</h4>
        <div id="report-leaderboard-entries" style="font-size:0.8rem; font-family:var(--font-mono); color:#94a3b8;">Loading standings...</div>
      </div>

      <div style="display:flex; gap:12px;">
        <button type="button" class="btn-secondary" id="btn-report-lobby" style="flex:1;">Return to World Hub</button>
        <button type="button" class="btn-primary" id="btn-report-replay" style="flex:1;">Restart Experiment</button>
      </div>
    `;

    document.getElementById('btn-report-lobby').onclick = () => {
      this.hide();
      document.getElementById('screen-lobby').classList.remove('hidden');
    };

    document.getElementById('btn-report-replay').onclick = () => {
      this.hide();
      window.startExperimentSession(state.experiment?.id, state.session?.nickname);
    };

    // Load leaderboard
    if (state.experiment?.id) {
      api.getLeaderboard(state.experiment.id).then((entries) => {
        const lbEl = document.getElementById('report-leaderboard-entries');
        if (!lbEl) return;
        if (!entries || entries.length === 0) {
          lbEl.textContent = 'No previous rankings recorded yet.';
          return;
        }
        lbEl.innerHTML = entries
          .slice(0, 5)
          .map(
            (e) => `
            <div style="display:flex; justify-content:space-between; padding:4px 0; border-bottom:1px solid rgba(255,255,255,0.06);">
              <span>#${e.rank} ${e.nickname}</span>
              <span>Score: <strong style="color:#f8fafc;">${e.score}</strong> (Grade ${e.grade})</span>
            </div>
          `
          )
          .join('');
      });
    }
  }

  hide() {
    if (this.screenEl) this.screenEl.classList.add('hidden');
  }
}
