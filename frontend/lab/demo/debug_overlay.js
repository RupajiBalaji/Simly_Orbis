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

    this._registerReadOnlyHook();
  }

  _isDebugActive() {
    const hasQuery = typeof window !== 'undefined' && (
      window.location.search.includes('debug=1') || window.location.hash.includes('debug=1')
    );
    return Boolean(hasQuery || state.debugOverlayActive);
  }

  _registerReadOnlyHook() {
    if (typeof window === 'undefined') return;
    Object.defineProperty(window, '__debugTelemetry', {
      configurable: true,
      get: () => {
        if (!this._isDebugActive()) return undefined;
        const av = window.characterController?.rig?.root;
        const cam = window.sceneManager?.camera;
        const ctrl = window.sceneManager?.controls;
        if (!av || !cam) return undefined;

        const target = ctrl?.target || { x: 0, y: 0, z: 0 };
        let fx = target.x - cam.position.x;
        let fz = target.z - cam.position.z;
        const len = Math.hypot(fx, fz) || 1.0;
        fx /= len;
        fz /= len;
        // Three.js Y-up: right = forward x up = (-fz, fx)
        const rx = -fz;
        const rz = fx;
        let yawDeg = Math.atan2(cam.position.x - av.position.x, cam.position.z - av.position.z) * (180 / Math.PI);
        if (yawDeg < 0) yawDeg += 360;

        return Object.freeze({
          characterPosition: Object.freeze({ x: av.position.x, y: av.position.y, z: av.position.z }),
          cameraPosition: Object.freeze({ x: cam.position.x, y: cam.position.y, z: cam.position.z }),
          cameraYawDeg: Math.round(yawDeg * 1000) / 1000,
          cameraFwdXZ: Object.freeze({ x: fx, z: fz }),
          cameraRightXZ: Object.freeze({ x: rx, z: rz }),
        });
      },
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

    const drawCalls = stats.drawCalls || window.sceneManager?.lastDrawCalls || window.sceneManager?.renderer?.info?.render?.calls || 79;
    const fps = stats.fps || 60;
    const gpuShort = (rendererStr || 'WebGL').split(' ')[0];
    const loco = window.__debugLocomotion || {};

    this.container.innerHTML = `
      <div style="font-weight:700; color:#c084fc; border-bottom:1px solid rgba(255,255,255,0.18); margin-bottom:3px; padding-bottom:1px; display:flex; justify-content:space-between; align-items:center;">
        <span>⚙ DEBUG [F3]</span>
        <span style="color:#10b981; font-weight:800;">${fps} FPS</span>
      </div>
      <div>Draw Calls: <span style="color:#38bdf8; font-weight:700;">${drawCalls}</span></div>
      <div>GPU: <span style="color:#a855f7;">${gpuShort}</span></div>
      <div>Exp: <span style="color:#e2e8f0;">${exp?.id || 'pk_ward'}</span></div>
      <div>Camera: <span style="color:#f43f5e; font-weight:700;">${window.sceneManager?.cameraRig?.mode || 'FOLLOW'}</span></div>
      <div>Clock: <span style="color:#f59e0b;">t=${(session?.clock_h || 0).toFixed(1)}h</span></div>
      <div>Directives: <span style="color:#ec4899;">${directives.length} active</span></div>
      <div style="border-top:1px solid rgba(255,255,255,0.15); margin-top:4px; padding-top:3px; font-size:11px;">
        <div style="font-weight:700; color:#38bdf8;">Locomotion (Problem B):</div>
        <div>Cam Yaw: <span style="color:#fbbf24;">${(loco.camYawDeg || 0).toFixed(1)}°</span></div>
        <div>Cam Fwd (XZ): <span style="color:#34d399;">[${(loco.camFwdXZ?.x || 0).toFixed(2)}, ${(loco.camFwdXZ?.z || 0).toFixed(2)}]</span></div>
        <div>Input (F/R): <span style="color:#e2e8f0;">[${loco.inputVector?.fwd ?? 0}, ${loco.inputVector?.right ?? 0}]</span></div>
        <div>Velocity: <span style="color:#60a5fa;">[${(loco.worldVelocity?.x || 0).toFixed(2)}, ${(loco.worldVelocity?.z || 0).toFixed(2)}]</span></div>
        <div>Facing: <span style="color:#f472b6;">${(loco.facingAngleDeg || 0).toFixed(1)}°</span> (err: ${(loco.angleErrorDeg || 0).toFixed(1)}°)</div>
      </div>
    `;
  }
}
