/**
 * Particle Effects & Alarm Strobe Renderer (frontend/lab/render/effects.js)
 * Implements directive 'effect' (splash, bubbles, smoke, spark, alarm, glow).
 */

import * as THREE from 'three';

export class EffectManager {
  constructor(scene) {
    this.scene = scene;
    this.activeEffects = [];
    this.alarmStrobeEl = document.getElementById('alarm-strobe-overlay');
  }

  playEffect(apparatusGroup, directive) {
    const name = directive.name || 'glow';
    const durationMs = directive.duration_ms || 1500;

    const origin = new THREE.Vector3();
    if (apparatusGroup) {
      apparatusGroup.getWorldPosition(origin);
      origin.y += 0.2;
    }

    switch (name) {
      case 'splash':
        this.createSplash(origin, durationMs);
        break;
      case 'droplets':
        this.createDroplets(origin, durationMs, directive.color ? parseInt(directive.color.replace('#', '0x')) : 0x38bdf8);
        break;
      case 'stream':
      case 'pour': {
        const targetPos = directive.target_pos ? new THREE.Vector3(...directive.target_pos) : origin.clone().sub(new THREE.Vector3(0, 0.35, 0));
        this.createPourStream(origin, targetPos, durationMs, directive.color ? parseInt(directive.color.replace('#', '0x')) : 0x38bdf8);
        break;
      }
      case 'bubbles':
        this.createBubbles(origin, durationMs);
        break;
      case 'smoke':
        this.createSmoke(origin, durationMs);
        break;
      case 'spark':
        this.createSparks(origin, durationMs);
        break;
      case 'alarm':
        this.triggerAlarm(durationMs);
        break;
      case 'fume_puff':
        this.createFumePuff(origin, durationMs);
        break;
      case 'spill_puddle':
        this.createSpillPuddle(origin, durationMs);
        break;
      case 'runaway_reaction':
        this.createRunawayReaction(origin, durationMs);
        break;
      case 'foam_eruption':
        this.createFoamEruption(origin, durationMs);
        break;
      case 'sparkles':
        this.createSparkles(origin, durationMs, directive.color ? parseInt(directive.color.replace('#', '0x')) : 0x22c55e);
        break;
      case 'confetti':
        this.triggerConfettiShower();
        break;
      case 'camera_shake':
        this.triggerCameraShake(8, durationMs);
        break;
      case 'alarm_flash':
        this.triggerAlarmFlash(durationMs);
        break;
      case 'glow':
      default:
        this.createGlow(origin, durationMs);
        break;
    }
  }

  createSplash(origin, durationMs) {
    const particleCount = 28;
    const geo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const velocities = [];

    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = origin.x;
      positions[i * 3 + 1] = origin.y;
      positions[i * 3 + 2] = origin.z;

      velocities.push(
        new THREE.Vector3(
          (Math.random() - 0.5) * 1.8,
          Math.random() * 2.2 + 0.5,
          (Math.random() - 0.5) * 1.8
        )
      );
    }

    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const mat = new THREE.PointsMaterial({
      color: 0x38bdf8,
      size: 0.04,
      transparent: true,
      opacity: 0.9,
    });

    const points = new THREE.Points(geo, mat);
    this.scene.add(points);

    this.activeEffects.push({
      mesh: points,
      velocities,
      positions,
      startTime: performance.now(),
      durationMs,
      type: 'physics',
    });
  }

  createBubbles(origin, durationMs) {
    const count = 16;
    const geo = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    const velocities = [];

    for (let i = 0; i < count; i++) {
      positions[i * 3] = origin.x + (Math.random() - 0.5) * 0.1;
      positions[i * 3 + 1] = origin.y - 0.05 + Math.random() * 0.05;
      positions[i * 3 + 2] = origin.z + (Math.random() - 0.5) * 0.1;

      velocities.push(
        new THREE.Vector3((Math.random() - 0.5) * 0.05, Math.random() * 0.4 + 0.2, (Math.random() - 0.5) * 0.05)
      );
    }

    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const mat = new THREE.PointsMaterial({
      color: 0xf1f5f9,
      size: 0.03,
      transparent: true,
      opacity: 0.7,
    });

    const points = new THREE.Points(geo, mat);
    this.scene.add(points);

    this.activeEffects.push({
      mesh: points,
      velocities,
      positions,
      startTime: performance.now(),
      durationMs,
      type: 'bubbles',
    });
  }

  createSmoke(origin, durationMs) {
    const count = 20;
    const geo = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    const velocities = [];

    for (let i = 0; i < count; i++) {
      positions[i * 3] = origin.x + (Math.random() - 0.5) * 0.15;
      positions[i * 3 + 1] = origin.y + Math.random() * 0.1;
      positions[i * 3 + 2] = origin.z + (Math.random() - 0.5) * 0.15;

      velocities.push(
        new THREE.Vector3((Math.random() - 0.5) * 0.15, Math.random() * 0.3 + 0.15, (Math.random() - 0.5) * 0.15)
      );
    }

    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const mat = new THREE.PointsMaterial({
      color: 0x94a3b8,
      size: 0.06,
      transparent: true,
      opacity: 0.5,
    });

    const points = new THREE.Points(geo, mat);
    this.scene.add(points);

    this.activeEffects.push({
      mesh: points,
      velocities,
      positions,
      startTime: performance.now(),
      durationMs,
      type: 'smoke',
    });
  }

  createSparks(origin, durationMs) {
    const count = 20;
    const geo = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    const velocities = [];

    for (let i = 0; i < count; i++) {
      positions[i * 3] = origin.x;
      positions[i * 3 + 1] = origin.y;
      positions[i * 3 + 2] = origin.z;

      velocities.push(
        new THREE.Vector3(
          (Math.random() - 0.5) * 2.5,
          Math.random() * 2.0,
          (Math.random() - 0.5) * 2.5
        )
      );
    }

    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const mat = new THREE.PointsMaterial({
      color: 0xf59e0b,
      size: 0.05,
      transparent: true,
      opacity: 1.0,
    });

    const points = new THREE.Points(geo, mat);
    this.scene.add(points);

    this.activeEffects.push({
      mesh: points,
      velocities,
      positions,
      startTime: performance.now(),
      durationMs,
      type: 'physics',
    });
  }

  createGlow(origin, durationMs) {
    const light = new THREE.PointLight(0x14b8a6, 2.5, 3.5);
    light.position.copy(origin);
    this.scene.add(light);

    this.activeEffects.push({
      light,
      startTime: performance.now(),
      durationMs,
      type: 'glow',
    });
  }

  triggerAlarm(durationMs) {
    // 1. Red point light pulse
    const alarmLight = this.scene.getObjectByName('alarm_point_light');
    if (alarmLight) {
      alarmLight.intensity = 3.5;
    }

    // 2. HUD red strobe border
    if (this.alarmStrobeEl) {
      this.alarmStrobeEl.classList.add('active');
    }

    setTimeout(() => {
      if (alarmLight) alarmLight.intensity = 0;
      if (this.alarmStrobeEl) this.alarmStrobeEl.classList.remove('active');
    }, durationMs);
  }

  createPourStream(sourcePos, targetPos, durationMs = 1200, colorHex = 0x38bdf8) {
    const s = sourcePos.clone();
    const e = targetPos.clone();
    const dir = new THREE.Vector3().subVectors(e, s);
    const len = dir.length();
    if (len < 0.04) return;

    const mid = new THREE.Vector3().addVectors(s, e).multiplyScalar(0.5);
    const geo = new THREE.CylinderGeometry(0.010, 0.015, len, 8);
    const mat = new THREE.MeshStandardMaterial({
      color: colorHex,
      transparent: true,
      opacity: 0.8,
      roughness: 0.1,
      metalness: 0.1,
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.copy(mid);

    const up = new THREE.Vector3(0, 1, 0);
    const quat = new THREE.Quaternion().setFromUnitVectors(up, dir.clone().normalize());
    mesh.quaternion.copy(quat);

    this.scene.add(mesh);
    this.activeEffects.push({
      mesh,
      startTime: performance.now(),
      durationMs,
      type: 'stream',
    });
  }

  createDroplets(origin, durationMs = 1500, colorHex = 0x38bdf8) {
    const count = 32;
    const geo = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    const velocities = [];

    for (let i = 0; i < count; i++) {
      positions[i * 3] = origin.x + (Math.random() - 0.5) * 0.05;
      positions[i * 3 + 1] = origin.y - Math.random() * 0.06;
      positions[i * 3 + 2] = origin.z + (Math.random() - 0.5) * 0.05;

      velocities.push(
        new THREE.Vector3(
          (Math.random() - 0.5) * 0.08,
          -(Math.random() * 0.8 + 0.5),
          (Math.random() - 0.5) * 0.08
        )
      );
    }

    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const mat = new THREE.PointsMaterial({
      color: colorHex,
      size: 0.035,
      transparent: true,
      opacity: 0.85,
    });

    const points = new THREE.Points(geo, mat);
    this.scene.add(points);

    this.activeEffects.push({
      mesh: points,
      velocities,
      positions,
      startTime: performance.now(),
      durationMs,
      type: 'droplets',
    });
  }

  createFumePuff(origin, durationMs = 2500) {
    const count = 30;
    const geo = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    const velocities = [];

    for (let i = 0; i < count; i++) {
      positions[i * 3] = origin.x + (Math.random() - 0.5) * 0.12;
      positions[i * 3 + 1] = origin.y + Math.random() * 0.1;
      positions[i * 3 + 2] = origin.z + (Math.random() - 0.5) * 0.12;

      velocities.push(
        new THREE.Vector3(
          (Math.random() - 0.5) * 0.25,
          Math.random() * 0.5 + 0.2,
          (Math.random() - 0.5) * 0.25
        )
      );
    }

    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const mat = new THREE.PointsMaterial({
      color: 0xf59e0b,
      size: 0.08,
      transparent: true,
      opacity: 0.85,
    });

    const points = new THREE.Points(geo, mat);
    this.scene.add(points);

    const canvas = document.getElementById('webgl-canvas');
    if (canvas && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      canvas.classList.add('fume-blur-active');
      setTimeout(() => canvas.classList.remove('fume-blur-active'), 5000);
    }

    this.activeEffects.push({
      mesh: points,
      velocities,
      positions,
      startTime: performance.now(),
      durationMs,
      type: 'smoke',
    });
  }

  createSpillPuddle(origin, durationMs = 5000) {
    const geo = new THREE.CircleGeometry(0.12, 16);
    const mat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.75,
      side: THREE.DoubleSide,
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.rotation.x = -Math.PI / 2;
    mesh.position.set(origin.x, origin.y - 0.18, origin.z);
    this.scene.add(mesh);

    this.createDroplets(origin, 2000, 0x38bdf8);

    this.activeEffects.push({
      mesh,
      startTime: performance.now(),
      durationMs,
      type: 'puddle',
    });
  }

  createRunawayReaction(origin, durationMs = 3000) {
    this.createBubbles(origin, durationMs);
    this.createSmoke(origin, durationMs);
    const steamGeo = new THREE.BufferGeometry();
    const count = 25;
    const positions = new Float32Array(count * 3);
    const velocities = [];
    for (let i = 0; i < count; i++) {
      positions[i * 3] = origin.x + (Math.random() - 0.5) * 0.08;
      positions[i * 3 + 1] = origin.y + Math.random() * 0.05;
      positions[i * 3 + 2] = origin.z + (Math.random() - 0.5) * 0.08;
      velocities.push(new THREE.Vector3((Math.random() - 0.5) * 0.15, Math.random() * 0.8 + 0.4, (Math.random() - 0.5) * 0.15));
    }
    steamGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const steamMat = new THREE.PointsMaterial({ color: 0xffffff, size: 0.09, transparent: true, opacity: 0.8 });
    const steam = new THREE.Points(steamGeo, steamMat);
    this.scene.add(steam);
    this.activeEffects.push({ mesh: steam, velocities, positions, startTime: performance.now(), durationMs, type: 'smoke' });
  }

  createFoamEruption(origin, durationMs = 3500) {
    this.createBubbles(origin, durationMs);
    this.createSmoke(origin, durationMs);
    const foamGeo = new THREE.BufferGeometry();
    const count = 35;
    const positions = new Float32Array(count * 3);
    const velocities = [];
    for (let i = 0; i < count; i++) {
      positions[i * 3] = origin.x + (Math.random() - 0.5) * 0.1;
      positions[i * 3 + 1] = origin.y + Math.random() * 0.05;
      positions[i * 3 + 2] = origin.z + (Math.random() - 0.5) * 0.1;
      velocities.push(new THREE.Vector3((Math.random() - 0.5) * 0.3, Math.random() * 1.0 + 0.6, (Math.random() - 0.5) * 0.3));
    }
    foamGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const foamMat = new THREE.PointsMaterial({ color: 0xfef08a, size: 0.07, transparent: true, opacity: 0.9 });
    const foam = new THREE.Points(foamGeo, foamMat);
    this.scene.add(foam);
    this.activeEffects.push({ mesh: foam, velocities, positions, startTime: performance.now(), durationMs, type: 'physics' });
  }

  createSparkles(origin, durationMs = 1500, colorHex = 0x22c55e) {
    const count = 24;
    const geo = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    const velocities = [];
    for (let i = 0; i < count; i++) {
      positions[i * 3] = origin.x;
      positions[i * 3 + 1] = origin.y + 0.1;
      positions[i * 3 + 2] = origin.z;
      velocities.push(new THREE.Vector3((Math.random() - 0.5) * 0.8, Math.random() * 0.9 + 0.3, (Math.random() - 0.5) * 0.8));
    }
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const mat = new THREE.PointsMaterial({ color: colorHex, size: 0.05, transparent: true, opacity: 0.95 });
    const mesh = new THREE.Points(geo, mat);
    this.scene.add(mesh);
    this.activeEffects.push({ mesh, velocities, positions, startTime: performance.now(), durationMs, type: 'physics' });
  }

  triggerConfettiShower() {
    const origin = new THREE.Vector3(0, 3.5, -2.5);
    const count = 80;
    const geo = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    const velocities = [];
    for (let i = 0; i < count; i++) {
      positions[i * 3] = origin.x + (Math.random() - 0.5) * 4.0;
      positions[i * 3 + 1] = origin.y + Math.random() * 1.0;
      positions[i * 3 + 2] = origin.z + (Math.random() - 0.5) * 3.0;
      velocities.push(new THREE.Vector3((Math.random() - 0.5) * 0.6, -(Math.random() * 1.2 + 0.6), (Math.random() - 0.5) * 0.6));
    }
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const mat = new THREE.PointsMaterial({ color: 0xfacc15, size: 0.06, transparent: true, opacity: 0.95 });
    const mesh = new THREE.Points(geo, mat);
    this.scene.add(mesh);
    this.activeEffects.push({ mesh, velocities, positions, startTime: performance.now(), durationMs: 4000, type: 'physics' });
  }

  triggerCameraShake(magnitude = 8, durationMs = 300) {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const canvas = document.getElementById('webgl-canvas');
    if (canvas) {
      canvas.classList.remove('camera-shake');
      void canvas.offsetWidth;
      canvas.classList.add('camera-shake');
      setTimeout(() => canvas.classList.remove('camera-shake'), durationMs + 50);
    }
  }

  triggerAlarmFlash(durationMs = 350) {
    const hud = document.getElementById('lab-hud');
    if (hud) {
      hud.classList.remove('warning-edge-flash');
      void hud.offsetWidth;
      hud.classList.add('warning-edge-flash');
      setTimeout(() => hud.classList.remove('warning-edge-flash'), durationMs + 50);
    }
  }

  update(dt) {
    const now = performance.now();

    for (let i = this.activeEffects.length - 1; i >= 0; i--) {
      const fx = this.activeEffects[i];
      const elapsed = now - fx.startTime;

      if (elapsed >= fx.durationMs) {
        // Dispose
        if (fx.mesh) {
          this.scene.remove(fx.mesh);
          fx.mesh.geometry.dispose();
          fx.mesh.material.dispose();
        }
        if (fx.light) {
          this.scene.remove(fx.light);
        }
        this.activeEffects.splice(i, 1);
        continue;
      }

      // Physics motion
      if (fx.type === 'physics' && fx.positions) {
        const count = fx.velocities.length;
        for (let j = 0; j < count; j++) {
          fx.velocities[j].y -= 9.8 * dt * 0.6; // gravity
          fx.positions[j * 3] += fx.velocities[j].x * dt;
          fx.positions[j * 3 + 1] += fx.velocities[j].y * dt;
          fx.positions[j * 3 + 2] += fx.velocities[j].z * dt;
        }
        fx.mesh.geometry.attributes.position.needsUpdate = true;
      } else if (fx.type === 'droplets' && fx.positions) {
        const count = fx.velocities.length;
        for (let j = 0; j < count; j++) {
          fx.velocities[j].y -= 9.8 * dt * 0.4;
          fx.positions[j * 3] += fx.velocities[j].x * dt;
          fx.positions[j * 3 + 1] += fx.velocities[j].y * dt;
          fx.positions[j * 3 + 2] += fx.velocities[j].z * dt;
        }
        fx.mesh.geometry.attributes.position.needsUpdate = true;
      } else if ((fx.type === 'bubbles' || fx.type === 'smoke') && fx.positions) {
        const count = fx.velocities.length;
        for (let j = 0; j < count; j++) {
          fx.positions[j * 3] += fx.velocities[j].x * dt;
          fx.positions[j * 3 + 1] += fx.velocities[j].y * dt;
          fx.positions[j * 3 + 2] += fx.velocities[j].z * dt;
        }
        fx.mesh.geometry.attributes.position.needsUpdate = true;
      }
    }
  }
}
