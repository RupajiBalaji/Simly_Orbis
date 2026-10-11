/**
 * Visual Directive Execution Queue (frontend/lab/render/directive_queue.js)
 * Executes character animations, liquid updates, effects, and readouts in sequential order.
 */

import * as THREE from 'three';
import { applyLiquidDirective } from './liquid.js';
import { applyReadoutDirective, applyVitalsDirective, applyLabelDirective, applyHighlightDirective } from './readouts.js';
import { state } from '../state.js';
import { soundFX } from '../audio/sound_fx.js';

export class DirectiveQueue {
  constructor(sceneManager, characterController, effectManager) {
    this.sceneManager = sceneManager;
    this.characterController = characterController;
    this.effectManager = effectManager;
  }

  async processActionResult(actionResult, targetId = null) {
    state.setPending(true);
    state.updateStats({
      lastAction: actionResult,
      lastDirectives: actionResult.visuals || [],
    });

    const isFast = state.skipAnimation;
    const animDirective = actionResult.character_animation;
    const visuals = actionResult.visuals || [];

    // 1. Character Locomotion & Animation
    if (animDirective && this.characterController && !isFast) {
      const animTargetId = animDirective.target || targetId;
      const apparatus = this.sceneManager.getApparatus(animTargetId);
      const clipName = animDirective.name || 'idle';
      const durationMs = animDirective.duration_ms || 1800;

      await new Promise((resolve) => {
        let appWorldPos = null;
        const avWorldPos = this.characterController.rig?.root?.position?.clone() || new THREE.Vector3();

        if (apparatus) {
          appWorldPos = new THREE.Vector3();
          apparatus.getWorldPosition(appWorldPos);
        } else {
          appWorldPos = avWorldPos.clone().add(new THREE.Vector3(0, 1.1, -0.6));
        }

        // Relative action camera trigger upon arrival at station
        const onArrival = () => {
          if (this.sceneManager?.startActionCamera) {
            this.sceneManager.startActionCamera(appWorldPos, avWorldPos, durationMs, clipName, animTargetId);
          }

          if (this.sceneManager?.startActionPerf) {
            this.sceneManager.startActionPerf(clipName);
          }

          const camIndicator = document.getElementById('action-cam-indicator');
          if (camIndicator) {
            const actionLabels = {
              weigh: 'Weighing Active Substance',
              administer_oral: 'Administering Oral Suspension',
              label: 'Labeling Apparatus',
              draw_blood: 'Venous Blood Sampling',
              wash_hands: 'Washing & Decontaminating Hands',
              dissolve: 'Dissolving Powder In Water',
              tare_balance: 'Taring Analytical Balance',
              pipette_analyte: 'Pipetting Acid Analyte',
              titrate: 'Titrating Acid-Base Solution',
            };
            camIndicator.textContent = `🎬 ACTION CAM: ${actionLabels[clipName] || clipName.replace(/_/g, ' ').toUpperCase()}`;
            camIndicator.style.display = 'flex';
          }
        };

        // Trigger procedural sound effects
        if (clipName === 'weigh') {
          soundFX.playClick();
        } else if (clipName === 'titrate' || clipName === 'turn_stopcock' || clipName === 'pour' || clipName === 'dissolve') {
          soundFX.playLiquidTrickle(durationMs / 1000);
        } else if (clipName === 'run_assay') {
          soundFX.playCentrifugeHum(durationMs / 1000);
        } else if (['pipette_analyte', 'add_indicator', 'label', 'draw_blood'].includes(clipName)) {
          soundFX.playGlassClink();
        }

        // Ticking weigh progress (powder pile grows, balance reading rises)
        let weighInterval = null;
        if (clipName === 'weigh' && apparatus?.userData?.updateWeighProgress) {
          const startTime = performance.now();
          const targetWeightG = 0.500;
          weighInterval = setInterval(() => {
            const elapsed = performance.now() - startTime;
            const p = Math.min(1.0, elapsed / (durationMs * 0.85));
            apparatus.userData.updateWeighProgress(p, targetWeightG);
            if (p >= 1.0) {
              clearInterval(weighInterval);
              weighInterval = null;
              soundFX.playBalanceBeep();
            }
          }, 33);
        }

        // Liquid movement tweening and procedural streams/droplets
        let liquidTweenInterval = null;
        if (clipName === 'titrate' || clipName === 'turn_stopcock') {
          const bur = this.sceneManager.getApparatus('burette');
          const flask = this.sceneManager.getApparatus('conical_flask');
          const burDir = visuals.find((v) => v.type === 'liquid' && v.target === 'burette');
          const flaskDir = visuals.find((v) => v.type === 'liquid' && v.target === 'conical_flask');

          setTimeout(() => {
            if (bur && flask && this.effectManager?.createPourStream) {
              const bPos = new THREE.Vector3();
              const fPos = new THREE.Vector3();
              bur.getWorldPosition(bPos);
              flask.getWorldPosition(fPos);
              bPos.y += 0.25; // tip below burette stopcock
              fPos.y += 0.12; // flask opening
              this.effectManager.createPourStream(bPos, fPos, durationMs * 0.65, 0xf8fafc);
              this.effectManager.createDroplets(fPos, durationMs * 0.65, 0xf8fafc);
            }
          }, 250);

          if (bur && flask && burDir && flaskDir) {
            const startBurVol = bur.userData.currentVolume !== undefined ? bur.userData.currentVolume : (burDir.volume_ml + 1.0);
            const targetBurVol = burDir.volume_ml;
            const startFlaskVol = flask.userData.currentVolume !== undefined ? flask.userData.currentVolume : Math.max(0, flaskDir.volume_ml - 1.0);
            const targetFlaskVol = flaskDir.volume_ml;
            const startTime = performance.now();
            const tweenDuration = durationMs * 0.7;

            liquidTweenInterval = setInterval(() => {
              const elapsed = performance.now() - startTime;
              const p = Math.min(1.0, elapsed / tweenDuration);
              const curBur = startBurVol + (targetBurVol - startBurVol) * p;
              const curFlask = startFlaskVol + (targetFlaskVol - startFlaskVol) * p;
              applyLiquidDirective(bur, { target: 'burette', volume_ml: curBur, hex: burDir.hex || '#f8fafc', opacity: 0.8 });
              applyLiquidDirective(flask, { target: 'conical_flask', volume_ml: curFlask, hex: flaskDir.hex || '#f8fafc', opacity: 0.9 });
              bur.userData.currentVolume = curBur;
              flask.userData.currentVolume = curFlask;
              if (p >= 1.0) {
                clearInterval(liquidTweenInterval);
                liquidTweenInterval = null;
              }
            }, 33);
          }
        } else if (clipName === 'dissolve' || clipName === 'pour') {
          const targetApp = apparatus;
          const targetDir = visuals.find((v) => v.type === 'liquid');
          setTimeout(() => {
            if (targetApp && this.effectManager?.createPourStream) {
              const tPos = new THREE.Vector3();
              targetApp.getWorldPosition(tPos);
              const sPos = tPos.clone().add(new THREE.Vector3(0.12, 0.32, 0.05));
              this.effectManager.createPourStream(sPos, tPos, durationMs * 0.65, targetDir?.hex ? parseInt(targetDir.hex.replace('#', '0x')) : 0x38bdf8);
            }
          }, 300);

          if (targetApp && targetDir) {
            const startVol = targetApp.userData.currentVolume !== undefined ? targetApp.userData.currentVolume : 0.0;
            const targetVol = targetDir.volume_ml || 50.0;
            const startTime = performance.now();
            const tweenDuration = durationMs * 0.7;

            liquidTweenInterval = setInterval(() => {
              const elapsed = performance.now() - startTime;
              const p = Math.min(1.0, elapsed / tweenDuration);
              const curVol = startVol + (targetVol - startVol) * p;
              applyLiquidDirective(targetApp, { target: targetDir.target, volume_ml: curVol, hex: targetDir.hex, opacity: targetDir.opacity });
              targetApp.userData.currentVolume = curVol;
              if (p >= 1.0) {
                clearInterval(liquidTweenInterval);
                liquidTweenInterval = null;
              }
            }, 33);
          }
        } else if (clipName === 'wash_hands' && apparatus) {
          setTimeout(() => {
            this.effectManager?.playEffect(apparatus, { name: 'droplets', duration_ms: 1400, color: '#38bdf8' });
          }, 300);
        }

        const onFinished = () => {
          if (liquidTweenInterval) {
            clearInterval(liquidTweenInterval);
            liquidTweenInterval = null;
          }
          if (weighInterval) {
            clearInterval(weighInterval);
            weighInterval = null;
          }
          if (clipName === 'weigh' && apparatus?.userData?.updateWeighProgress) {
            apparatus.userData.updateWeighProgress(1.0, 0.500);
          }
          if (this.sceneManager?.endActionPerf) {
            this.sceneManager.endActionPerf();
          }
          if (this.sceneManager?.endActionCamera) {
            this.sceneManager.endActionCamera();
          }
          const camIndicator = document.getElementById('action-cam-indicator');
          if (camIndicator) {
            camIndicator.style.display = 'none';
          }
          resolve();
        };

        if (apparatus) {
          this.characterController.executeActionAtStation(apparatus, clipName, durationMs, onFinished, onArrival);
        } else {
          // Play in place
          onArrival();
          const prop = this.characterController.createHeldProp ? this.characterController.createHeldProp(clipName) : null;
          if (prop) {
            if (prop.isGroup || prop.isMesh) {
              this.characterController.carryItem(prop);
            } else if (prop.right || prop.left) {
              this.characterController.carryItem(prop.right, prop.left);
            }
          }
          this.characterController.animator.playClip(clipName, null, durationMs, () => {
            if (this.characterController.dropHeldItem) this.characterController.dropHeldItem();
            onFinished();
          });
        }

        // Apply visual directives at midpoint
        setTimeout(() => {
          this.applyVisualDirectives(visuals);
        }, Math.max(100, durationMs * 0.45));
      });
    } else {
      // Instant execution (Skip animation mode)
      this.applyVisualDirectives(visuals);
      if (animDirective && this.characterController) {
        const animTargetId = animDirective.target || targetId;
        const apparatus = this.sceneManager.getApparatus(animTargetId);
        if (apparatus && apparatus.userData.stationPos) {
          this.characterController.rig.root.position.copy(apparatus.userData.stationPos);
        }
      }
    }

    state.setPending(false);
  }

  applyVisualDirectives(visuals) {
    for (const d of visuals) {
      const targetId = d.target || d.patient;
      const apparatus = this.sceneManager.getApparatus(targetId);

      switch (d.type) {
        case 'liquid':
          applyLiquidDirective(apparatus, d);
          break;
        case 'effect':
          this.effectManager.playEffect(apparatus, d);
          break;
        case 'readout':
          applyReadoutDirective(apparatus, d);
          break;
        case 'vitals': {
          const bed = this.sceneManager.getApparatus('patient_bed');
          applyVitalsDirective(bed, d);
          break;
        }
        case 'label':
          applyLabelDirective(apparatus, d);
          break;
        case 'highlight':
          applyHighlightDirective(apparatus);
          break;
        default:
          console.log(`Unknown directive: ${d.type}`);
          break;
      }
    }
  }
}
