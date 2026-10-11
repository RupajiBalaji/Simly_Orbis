/**
 * Procedural WebAudio Sound FX Engine (frontend/lab/audio/sound_fx.js)
 * Synthesizes all sound effects on-demand via Web Audio API oscillators, noise buffers, and filters.
 * Zero external audio assets required.
 */

export class SoundFXManager {
  constructor() {
    this.ctx = null;
    this.masterGain = null;
    this.isMuted = localStorage.getItem('orbis_lab_muted') === 'true';
    this.volume = parseFloat(localStorage.getItem('orbis_lab_volume') || '0.4');
    this.alarmGain = null;
    this.alarmInterval = null;
    this.ambientNodes = null;
  }

  ensureContext() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return null;
      this.ctx = new AudioCtx();
      this.masterGain = this.ctx.createGain();
      this.masterGain.connect(this.ctx.destination);
      this.updateMasterVolume();
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {});
    }
    return this.ctx;
  }

  setMuted(muted) {
    this.isMuted = Boolean(muted);
    localStorage.setItem('orbis_lab_muted', this.isMuted ? 'true' : 'false');
    this.updateMasterVolume();
  }

  toggleMute() {
    this.setMuted(!this.isMuted);
    return this.isMuted;
  }

  setVolume(vol) {
    this.volume = Math.max(0, Math.min(1, parseFloat(vol)));
    localStorage.setItem('orbis_lab_volume', this.volume.toString());
    this.updateMasterVolume();
  }

  updateMasterVolume() {
    if (!this.masterGain || !this.ctx) return;
    const targetGain = this.isMuted ? 0 : this.volume;
    this.masterGain.gain.setValueAtTime(targetGain, this.ctx.currentTime);
  }

  // --- 1. UI Click (crisp 800Hz blip, 30ms) ---
  playClick() {
    const ctx = this.ensureContext();
    if (!ctx || this.isMuted) return;
    try {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(800, ctx.currentTime);
      gain.gain.setValueAtTime(0.18, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.03);
      osc.connect(gain);
      gain.connect(this.masterGain);
      osc.start();
      osc.stop(ctx.currentTime + 0.035);
    } catch (_) {}
  }

  // --- 2. Footsteps (subtle low-pass noise tap when avatar moves, quiet) ---
  playFootstep() {
    const ctx = this.ensureContext();
    if (!ctx || this.isMuted) return;
    try {
      const bufferSize = Math.floor(ctx.sampleRate * 0.05);
      const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < bufferSize; i++) data[i] = Math.random() * 2 - 1;
      const noise = ctx.createBufferSource();
      noise.buffer = buffer;
      const filter = ctx.createBiquadFilter();
      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(260, ctx.currentTime);
      const gain = ctx.createGain();
      gain.gain.setValueAtTime(0.04, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.05);
      noise.connect(filter);
      filter.connect(gain);
      gain.connect(this.masterGain);
      noise.start();
    } catch (_) {}
  }

  // --- 3. Glass Clink (pleasant 2200Hz sine ping with quick decay) ---
  playGlassClink() {
    const ctx = this.ensureContext();
    if (!ctx || this.isMuted) return;
    try {
      const t = ctx.currentTime;
      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      const gain = ctx.createGain();
      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(2200, t);
      osc2.type = 'sine';
      osc2.frequency.setValueAtTime(4400, t);
      gain.gain.setValueAtTime(0.14, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.18);
      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(this.masterGain);
      osc1.start(t);
      osc2.start(t);
      osc1.stop(t + 0.20);
      osc2.stop(t + 0.20);
    } catch (_) {}
  }

  // --- 4. Liquid Trickle / Pour (bandpass-filtered white noise with pitch sweep) ---
  playLiquidTrickle(duration = 1.0) {
    const ctx = this.ensureContext();
    if (!ctx || this.isMuted) return;
    try {
      const t = ctx.currentTime;
      const bufferSize = Math.floor(ctx.sampleRate * Math.max(0.2, duration));
      const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < bufferSize; i++) data[i] = Math.random() * 2 - 1;
      const noise = ctx.createBufferSource();
      noise.buffer = buffer;
      const filter = ctx.createBiquadFilter();
      filter.type = 'bandpass';
      filter.Q.setValueAtTime(3.5, t);
      filter.frequency.setValueAtTime(800, t);
      filter.frequency.linearRampToValueAtTime(1350, t + duration);
      const gain = ctx.createGain();
      gain.gain.setValueAtTime(0.01, t);
      gain.gain.linearRampToValueAtTime(0.08, t + 0.1);
      gain.gain.setValueAtTime(0.08, t + duration - 0.1);
      gain.gain.linearRampToValueAtTime(0.001, t + duration);
      noise.connect(filter);
      filter.connect(gain);
      gain.connect(this.masterGain);
      noise.start(t);
    } catch (_) {}
  }

  // --- 5. Balance Beep (clean 1000Hz double-beep) ---
  playBalanceBeep() {
    const ctx = this.ensureContext();
    if (!ctx || this.isMuted) return;
    try {
      const t = ctx.currentTime;
      [0, 0.10].forEach((delay) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(1000, t + delay);
        gain.gain.setValueAtTime(0.12, t + delay);
        gain.gain.exponentialRampToValueAtTime(0.001, t + delay + 0.06);
        osc.connect(gain);
        gain.connect(this.masterGain);
        osc.start(t + delay);
        osc.stop(t + delay + 0.065);
      });
    } catch (_) {}
  }

  // --- 6. Centrifuge Hum (motor ramp up, sustained tone, ramp down) ---
  playCentrifugeHum(duration = 2.0) {
    const ctx = this.ensureContext();
    if (!ctx || this.isMuted) return;
    try {
      const t = ctx.currentTime;
      const osc = ctx.createOscillator();
      const filter = ctx.createBiquadFilter();
      const gain = ctx.createGain();
      osc.type = 'sawtooth';
      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(350, t);
      osc.frequency.setValueAtTime(120, t);
      osc.frequency.linearRampToValueAtTime(480, t + 0.5);
      osc.frequency.setValueAtTime(480, t + duration - 0.5);
      osc.frequency.linearRampToValueAtTime(80, t + duration);
      gain.gain.setValueAtTime(0.01, t);
      gain.gain.linearRampToValueAtTime(0.09, t + 0.4);
      gain.gain.setValueAtTime(0.09, t + duration - 0.4);
      gain.gain.linearRampToValueAtTime(0.001, t + duration);
      osc.connect(filter);
      filter.connect(gain);
      gain.connect(this.masterGain);
      osc.start(t);
      osc.stop(t + duration);
    } catch (_) {}
  }

  // --- 7. Success Chime (ascending major triad: C5-E5-G5) ---
  playSuccessChime() {
    const ctx = this.ensureContext();
    if (!ctx || this.isMuted) return;
    try {
      const t = ctx.currentTime;
      const notes = [523.25, 659.25, 783.99]; // C5, E5, G5
      notes.forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, t + idx * 0.12);
        gain.gain.setValueAtTime(0.12, t + idx * 0.12);
        gain.gain.exponentialRampToValueAtTime(0.001, t + idx * 0.12 + 0.35);
        osc.connect(gain);
        gain.connect(this.masterGain);
        osc.start(t + idx * 0.12);
        osc.stop(t + idx * 0.12 + 0.38);
      });
    } catch (_) {}
  }

  // --- 8. Warning Buzzer (two low harsh square-wave buzzes 180Hz) ---
  playWarningBuzzer() {
    const ctx = this.ensureContext();
    if (!ctx || this.isMuted) return;
    try {
      const t = ctx.currentTime;
      [0, 0.15].forEach((delay) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'square';
        osc.frequency.setValueAtTime(180, t + delay);
        gain.gain.setValueAtTime(0.10, t + delay);
        gain.gain.exponentialRampToValueAtTime(0.001, t + delay + 0.10);
        osc.connect(gain);
        gain.connect(this.masterGain);
        osc.start(t + delay);
        osc.stop(t + delay + 0.11);
      });
    } catch (_) {}
  }

  // --- 9. Alarm Loop (siren 880Hz / 660Hz until acknowledged) ---
  startAlarmLoop() {
    if (this.alarmInterval) return;
    const ctx = this.ensureContext();
    if (!ctx) return;
    try {
      this.alarmGain = ctx.createGain();
      this.alarmGain.gain.setValueAtTime(this.isMuted ? 0 : 0.10, ctx.currentTime);
      this.alarmGain.connect(this.masterGain);

      let step = 0;
      const tick = () => {
        if (!this.alarmGain || !this.ctx) return;
        const osc = this.ctx.createOscillator();
        osc.type = 'sawtooth';
        const freq = step % 2 === 0 ? 880 : 660;
        step++;
        osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
        osc.connect(this.alarmGain);
        osc.start();
        osc.stop(this.ctx.currentTime + 0.24);
      };
      tick();
      this.alarmInterval = setInterval(tick, 260);
    } catch (_) {}
  }

  stopAlarmLoop() {
    if (this.alarmInterval) {
      clearInterval(this.alarmInterval);
      this.alarmInterval = null;
    }
    if (this.alarmGain) {
      try { this.alarmGain.disconnect(); } catch (_) {}
      this.alarmGain = null;
    }
  }

  // --- 10. Ambient Lab Hum (60Hz + 120Hz low drone at -36dB) ---
  startAmbientHum() {
    if (this.ambientNodes) return;
    const ctx = this.ensureContext();
    if (!ctx) return;
    try {
      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      const gain = ctx.createGain();
      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(60, ctx.currentTime);
      osc2.type = 'sine';
      osc2.frequency.setValueAtTime(120, ctx.currentTime);
      gain.gain.setValueAtTime(0.015, ctx.currentTime);
      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(this.masterGain);
      osc1.start();
      osc2.start();
      this.ambientNodes = { osc1, osc2, gain };
    } catch (_) {}
  }

  stopAmbientHum() {
    if (!this.ambientNodes) return;
    try {
      this.ambientNodes.osc1.stop();
      this.ambientNodes.osc2.stop();
      this.ambientNodes.gain.disconnect();
    } catch (_) {}
    this.ambientNodes = null;
  }

  // --- 11. Grade A Fanfare (triumphant brass-like synth arpeggio) ---
  playFanfare() {
    const ctx = this.ensureContext();
    if (!ctx || this.isMuted) return;
    try {
      const t = ctx.currentTime;
      const freqs = [261.63, 329.63, 392.00, 523.25, 659.25, 783.99, 1046.50];
      freqs.forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const filter = ctx.createBiquadFilter();
        const gain = ctx.createGain();
        osc.type = 'sawtooth';
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(800 + idx * 200, t + idx * 0.10);
        osc.frequency.setValueAtTime(freq, t + idx * 0.10);
        const dur = idx === freqs.length - 1 ? 0.70 : 0.20;
        gain.gain.setValueAtTime(0.12, t + idx * 0.10);
        gain.gain.exponentialRampToValueAtTime(0.001, t + idx * 0.10 + dur);
        osc.connect(filter);
        filter.connect(gain);
        gain.connect(this.masterGain);
        osc.start(t + idx * 0.10);
        osc.stop(t + idx * 0.10 + dur + 0.05);
      });
    } catch (_) {}
  }
}

export const soundFX = new SoundFXManager();
