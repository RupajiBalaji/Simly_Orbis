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
          this.sceneManager.startActionCamera(appWorldPos, avWorldPos, durationMs);
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
        } else if (clipName === 'titrate' && apparatus) {
          setTimeout(() => {
            this.effectManager?.playEffect(apparatus, { name: 'droplets', duration_ms: 1000, color: '#f8fafc' });
          }, 400);
        }

        const onFinished = () => {
          if (this.sceneManager?.endActionCamera) {
            this.sceneManager.endActionCamera();
          }
          resolve();
        };

        if (apparatus) {
          this.characterController.executeActionAtStation(apparatus, clipName, durationMs, onFinished);
        } else {
          // Play in place
          const prop = this.characterController.createHeldProp ? this.characterController.createHeldProp(clipName) : null;
          if (prop) this.characterController.carryItem(prop);
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
