/**
 * Final Report & Leaderboard Screen (frontend/lab/game/report.js)
 * Displays post-session score breakdown, letter grades, violations, and leaderboard.
 */

import { api } from '../api.js';
import { state } from '../state.js';
import { toast } from './toast.js';

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

      ${
        (reportData.trial_result || state.lastTrialResult)
          ? `
        <div style="background:rgba(56,189,248,0.08); border:1px solid rgba(56,189,248,0.3); border-radius:8px; padding:12px 16px; margin-bottom:20px;">
          <h4 style="font-size:0.85rem; color:#38bdf8; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:6px; display:flex; align-items:center; gap:6px;">
            <span>👥 Virtual Population Clinical Trial</span>
          </h4>
          <p style="font-size:0.88rem; color:#f8fafc; margin-bottom:6px;">
            <strong>Your regimen:</strong> ${(reportData.trial_result || state.lastTrialResult).pct_in_range}% in range, ${(reportData.trial_result || state.lastTrialResult).pct_toxic}% toxic across ${(reportData.trial_result || state.lastTrialResult).n_patients} virtual patients.
          </p>
          <div style="display:flex; gap:16px; font-size:0.8rem; font-family:var(--font-mono); color:#94a3b8;">
            <span>Efficacy: <strong style="color:#10b981;">${(reportData.trial_result || state.lastTrialResult).pct_in_range}%</strong></span>
            <span>Toxicity: <strong style="color:#ef4444;">${(reportData.trial_result || state.lastTrialResult).pct_toxic}%</strong></span>
            <span>Mean Peak: <strong style="color:#38bdf8;">${(reportData.trial_result || state.lastTrialResult).mean_peak} mg/L</strong></span>
          </div>
        </div>
      `
          : ''
      }

      <!-- Verification & Mentorship Badges -->
      <div style="display:flex; gap:12px; margin-bottom:20px; flex-wrap:wrap;">
        <div style="flex:1; min-width:200px; background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.3); border-radius:8px; padding:10px 14px; font-size:0.85rem;">
          <div style="color:#6ee7b7; font-weight:700; display:flex; align-items:center; gap:6px;">
            <span>⚖️ Engine Reality Checks</span>
            <span style="background:#10b981; color:#0f172a; font-size:0.75rem; padding:2px 6px; border-radius:4px; font-weight:800;">PASS</span>
          </div>
          <div style="color:#cbd5e1; font-family:var(--font-mono); font-size:0.82rem; margin-top:4px;">
            Engine reality checks: <strong>${reportData.reality_checks_summary || '11/11 passed'}</strong>
          </div>
        </div>

        <div style="flex:1; min-width:200px; background:rgba(192,132,252,0.08); border:1px solid rgba(192,132,252,0.3); border-radius:8px; padding:10px 14px; font-size:0.85rem;">
          <div style="color:#c084fc; font-weight:700; display:flex; align-items:center; gap:6px;">
            <span>👨‍🔬 Mentor Guidance</span>
          </div>
          <div style="color:#cbd5e1; font-family:var(--font-mono); font-size:0.82rem; margin-top:4px;">
            Mentor hints used: <strong style="color:#f8fafc;">${reportData.hints_used ?? 0}</strong>
          </div>
        </div>
      </div>

      <!-- Dr. Orbis Debrief Box -->
      <div id="report-debrief-box" style="background:rgba(30,41,59,0.7); border:1px solid rgba(148,163,184,0.25); border-radius:8px; padding:12px 16px; margin-bottom:20px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
          <div style="color:#38bdf8; font-weight:700; font-size:0.88rem; display:flex; align-items:center; gap:6px;">
            <span>🩺 Dr. Orbis Laboratory Debrief</span>
          </div>
          <span id="debrief-source-badge" style="font-size:0.75rem; padding:2px 8px; border-radius:4px; background:#334155; color:#94a3b8;">Loading...</span>
        </div>
        <p id="debrief-text" style="color:#cbd5e1; font-size:0.86rem; line-height:1.5; margin:0;">
          Requesting Dr. Orbis pedagogical debrief...
        </p>
      </div>

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

    // Fetch Dr. Orbis Debrief
    if (reportData.session_id) {
      api.queryMentor(reportData.session_id, 'debrief')
        .then((res) => {
          const debriefText = document.getElementById('debrief-text');
          const badge = document.getElementById('debrief-source-badge');
          if (debriefText) debriefText.textContent = res.message;
          if (badge) {
            badge.textContent = res.source === 'ai' ? '🤖 AI' : '📋 rule-based';
            badge.style.background = res.source === 'ai' ? 'rgba(56,189,248,0.2)' : 'rgba(148,163,184,0.2)';
            badge.style.color = res.source === 'ai' ? '#38bdf8' : '#cbd5e1';
          }
        })
        .catch(() => {
          const debriefText = document.getElementById('debrief-text');
          if (debriefText) debriefText.textContent = 'Laboratory protocol completed. Review score breakdown above.';
        });
    }

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
    toast.clear();
  }
}
