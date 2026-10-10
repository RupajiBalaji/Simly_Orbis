/**
 * Real-Time Performance & Directive Debug Overlay (frontend/lab/demo/debug_overlay.js)
 * Displays FPS, draw calls, last executed action payload, and visual directives (F3 shortcut).
 */

import { state } from '../state.js';

export class DebugOverlay {
  constructor() {
    this.container = document.getElementById('debug-overlay');
    this.timer = null;

    window.addEventListener('keydown', (e) => {
      if (e.key === 'F3') {
        e.preventDefault();
        this.toggle();
      }
    });

    state.subscribe((event, payload) => {
      if (event === 'debug_overlay_changed') {
        if (payload) this.show();
        else this.hide();
      }
    });
  }

  toggle() {
    state.toggleDebugOverlay();
  }

  show() {
    if (this.container) {
      this.container.classList.add('active');
      this.timer = setInterval(() => this.update(), 250);
      this.update();
    }
  }

  hide() {
    if (this.container) {
      this.container.classList.remove('active');
      if (this.timer) clearInterval(this.timer);
    }
  }

  update() {
    if (!this.container) return;

    const stats = state.stats || {};
    const session = state.session;
    const exp = state.experiment;
    const directives = stats.lastDirectives || [];

    const lastAction = stats.lastAction;
    let rendererStr = this.cachedRenderer;
    if (!rendererStr) {
      try {
        const gl = window.sceneManager?.renderer?.getContext();
        if (gl) {
          const dbg = gl.getExtension('WEBGL_debug_renderer_info');
          rendererStr = dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
          this.cachedRenderer = rendererStr;
          console.log('[DEBUG OVERLAY] Unmasked WebGL Renderer:', rendererStr);
        }
      } catch (e) {
        rendererStr = 'WebGL Standard';
      }
    }

    this.container.innerHTML = `
      <div style="font-weight:bold; color:#f8fafc; border-bottom:1px solid rgba(255,255,255,0.2); margin-bottom:4px; padding-bottom:2px;">
        ⚙ ORBIS LAB DEBUG [F3]
      </div>
      <div>FPS: <span style="color:#10b981; font-weight:bold;">${stats.fps || 60}</span></div>
      <div>Draw Calls: <span style="color:#38bdf8;">${stats.drawCalls || 0}</span></div>
      <div>GPU: <span style="color:#a855f7; font-size:0.65rem;" title="${rendererStr}">${(rendererStr || 'WebGL').slice(0, 30)}...</span></div>
      <div>Exp: <span style="color:#c084fc;">${exp?.id || 'none'}</span></div>
      <div>Session: <span style="color:#94a3b8;">${session?.session_id ? session.session_id.slice(0, 8) : 'none'}</span></div>
      <div>Clock: <span style="color:#f59e0b;">t=${(session?.clock_h || 0).toFixed(2)}h</span></div>
      <div style="margin-top:4px; border-top:1px solid rgba(255,255,255,0.1); padding-top:2px;">
        <span style="color:#cbd5e1;">Last Action:</span> ${lastAction ? `<span style="color:#10b981;">${lastAction.message?.slice(0, 30)}...</span>` : 'none'}
      </div>
      <div>Directives: <span style="color:#ec4899;">${directives.length} active</span></div>
      ${
        directives.length > 0
          ? `<pre style="font-size:0.62rem; color:#94a3b8; max-height:60px; overflow:hidden;">${JSON.stringify(directives[0], null, 1)}</pre>`
          : ''
      }
    `;
  }
}
