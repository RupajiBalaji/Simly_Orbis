/**
 * Visual Directive Execution Queue (frontend/lab/render/directive_queue.js)
 * Executes character animations, liquid updates, effects, and readouts in sequential order.
 */

import * as THREE from 'three';
import { applyLiquidDirective } from './liquid.js';
import { applyReadoutDirective, applyVitalsDirective, applyLabelDirective, applyHighlightDirective } from './readouts.js';
import { state } from '../state.js';

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

        // Trigger Action Camera framing avatar upper body, hands & apparatus
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
            }
          }, 33);
        }

        // Procedural streams and droplets effects
        if (clipName === 'wash_hands' && apparatus) {
          setTimeout(() => {
            this.effectManager?.playEffect(apparatus, { name: 'droplets', duration_ms: 1400, color: '#38bdf8' });
          }, 300);
        } else if ((clipName === 'dissolve' || clipName === 'pour') && apparatus) {
          setTimeout(() => {
            this.effectManager?.playEffect(apparatus, { name: 'stream', duration_ms: 1000, color: '#38bdf8' });
          }, 400);
        } else if ((clipName === 'titrate' || clipName === 'turn_stopcock') && apparatus) {
          setTimeout(() => {
            this.effectManager?.playEffect(apparatus, { name: 'droplets', duration_ms: 1000, color: '#f8fafc' });
          }, 400);
        }

        const onFinished = () => {
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
          this.characterController.executeActionAtStation(apparatus, clipName, durationMs, onFinished);
        } else {
          // Play in place
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
