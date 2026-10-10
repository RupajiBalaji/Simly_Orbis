/**
 * Visual Directive Execution Queue (frontend/lab/render/directive_queue.js)
 * Executes character animations, liquid updates, effects, and readouts in sequential order.
 */

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
        if (apparatus) {
          this.characterController.executeActionAtStation(apparatus, clipName, durationMs, resolve);
        } else {
          // Play in place
          this.characterController.animator.playClip(clipName, null, durationMs, resolve);
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
