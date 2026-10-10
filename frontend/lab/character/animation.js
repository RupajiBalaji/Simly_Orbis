/**
 * Procedural Animation Clip Library & Tween Engine (frontend/lab/character/animation.js)
 * Implements idle, walk cycles, and gesture clips from the Visual Contract.
 */

import * as THREE from 'three';

export class AvatarAnimator {
  constructor(rig) {
    this.rig = rig;
    this.currentClip = 'idle';
    this.clipTime = 0;
    this.clipDuration = 2.0;
    this.clipTargetPos = null;
    this.onClipComplete = null;

    // Blinking timer
    this.blinkTimer = 2.5;
    this.isBlinking = false;
  }

  playClip(clipName, targetPos = null, durationMs = 1800, onComplete = null) {
    this.currentClip = clipName;
    this.clipTime = 0;
    this.clipDuration = durationMs / 1000;
    this.clipTargetPos = targetPos ? targetPos.clone() : null;
    this.onClipComplete = onComplete;
  }

  update(dt) {
    this.clipTime += dt;

    // Eye Blink
    this.blinkTimer -= dt;
    if (this.blinkTimer <= 0) {
      if (!this.isBlinking) {
        this.isBlinking = true;
        this.rig.setBlink(true);
        this.blinkTimer = 0.15; // 150ms blink
      } else {
        this.isBlinking = false;
        this.rig.setBlink(false);
        this.blinkTimer = 2.0 + Math.random() * 3.0; // Next blink in 2-5s
      }
    }

    // Evaluate active clip
    switch (this.currentClip) {
      case 'idle':
        this.evaluateIdle(this.clipTime);
        break;
      case 'walk':
        this.evaluateWalk(this.clipTime);
        break;
      case 'pour':
        this.evaluatePour(this.clipTime, this.clipDuration, this.clipTargetPos);
        break;
      case 'weigh':
        this.evaluateWeigh(this.clipTime, this.clipDuration, this.clipTargetPos);
        break;
      case 'write_label':
        this.evaluateWriteLabel(this.clipTime, this.clipDuration, this.clipTargetPos);
        break;
      case 'wear_ppe':
        this.evaluateWearPPE(this.clipTime, this.clipDuration);
        break;
      case 'draw_blood':
        this.evaluateDrawBlood(this.clipTime, this.clipDuration, this.clipTargetPos);
        break;
      case 'administer':
        this.evaluateAdminister(this.clipTime, this.clipDuration, this.clipTargetPos);
        break;
      case 'swirl':
        this.evaluateSwirl(this.clipTime, this.clipDuration, this.clipTargetPos);
        break;
      case 'turn_stopcock':
        this.evaluateTurnStopcock(this.clipTime, this.clipDuration, this.clipTargetPos);
        break;
      case 'read':
        this.evaluateRead(this.clipTime, this.clipDuration, this.clipTargetPos);
        break;
      case 'dispose':
        this.evaluateDispose(this.clipTime, this.clipDuration, this.clipTargetPos);
        break;
      case 'wash_hands':
        this.evaluateWashHands(this.clipTime, this.clipDuration);
        break;
      default:
        this.evaluateIdle(this.clipTime);
        break;
    }

    // Check completion for non-looping clips
    if (this.currentClip !== 'idle' && this.currentClip !== 'walk') {
      if (this.clipTime >= this.clipDuration) {
        const callback = this.onClipComplete;
        this.currentClip = 'idle';
        this.clipTime = 0;
        this.onClipComplete = null;
        if (callback) callback();
      }
    }
  }

  // -------------------------------------------------------------------------
  // Idle Animation (Gentle breathing sway)
  // -------------------------------------------------------------------------
  evaluateIdle(t) {
    const breath = Math.sin(t * 2.2);
    this.rig.pelvis.position.y = 0.95 + breath * 0.012;
    this.rig.torso.rotation.x = breath * 0.015;

    // Natural arm rest
    this.rig.leftArm.shoulder.rotation.set(0.05, 0, 0.1);
    this.rig.leftArm.elbow.rotation.set(-0.25, 0, 0);

    this.rig.rightArm.shoulder.rotation.set(0.05, 0, -0.1);
    this.rig.rightArm.elbow.rotation.set(-0.25, 0, 0);

    // Legs straight
    this.rig.leftLeg.hip.rotation.set(0, 0, 0);
    this.rig.leftLeg.knee.rotation.set(0, 0, 0);
    this.rig.rightLeg.hip.rotation.set(0, 0, 0);
    this.rig.rightLeg.knee.rotation.set(0, 0, 0);
  }

  // -------------------------------------------------------------------------
  // Walk Cycle (Rhythmic locomotion)
  // -------------------------------------------------------------------------
  evaluateWalk(t) {
    const freq = 6.0;
    const stride = Math.sin(t * freq);
    const bob = Math.abs(Math.cos(t * freq));

    this.rig.pelvis.position.y = 0.93 + bob * 0.03;

    // Legs
    this.rig.leftLeg.hip.rotation.x = stride * 0.45;
    this.rig.leftLeg.knee.rotation.x = Math.max(0, -stride * 0.5);

    this.rig.rightLeg.hip.rotation.x = -stride * 0.45;
    this.rig.rightLeg.knee.rotation.x = Math.max(0, stride * 0.5);

    // Contralateral Arms
    this.rig.leftArm.shoulder.rotation.set(-stride * 0.35, 0, 0.1);
    this.rig.leftArm.elbow.rotation.set(-0.35, 0, 0);

    this.rig.rightArm.shoulder.rotation.set(stride * 0.35, 0, -0.1);
    this.rig.rightArm.elbow.rotation.set(-0.35, 0, 0);
  }

  // -------------------------------------------------------------------------
  // Gesture Clips
  // -------------------------------------------------------------------------
  evaluatePour(t, dur, targetPos) {
    const progress = Math.min(1.0, t / dur);
    // Reach -> Tilt -> Hold -> Return
    let tilt = 0;
    if (progress < 0.3) {
      tilt = (progress / 0.3) * 0.8;
    } else if (progress < 0.7) {
      tilt = 0.8;
    } else {
      tilt = ((1.0 - progress) / 0.3) * 0.8;
    }

    if (targetPos) {
      this.rig.rightArm.ik.solve(targetPos);
    } else {
      this.rig.rightArm.shoulder.rotation.set(-0.8, -0.2, -0.2);
      this.rig.rightArm.elbow.rotation.set(-0.8, 0, 0);
    }
    this.rig.rightArm.hand.rotation.z = tilt;
  }

  evaluateWeigh(t, dur, targetPos) {
    const p = Math.min(1.0, t / dur);
    const dip = Math.sin(p * Math.PI) * 0.06;

    if (targetPos) {
      const pos = targetPos.clone();
      pos.y -= dip;
      this.rig.rightArm.ik.solve(pos);
    } else {
      this.rig.rightArm.shoulder.rotation.set(-0.6 - dip, 0, -0.2);
      this.rig.rightArm.elbow.rotation.set(-0.9, 0, 0);
    }
  }

  evaluateWriteLabel(t, dur, targetPos) {
    const scribble = Math.sin(t * 16.0) * 0.02;

    if (targetPos) {
      const pos = targetPos.clone();
      pos.x += scribble;
      this.rig.rightArm.ik.solve(pos);
    } else {
      this.rig.rightArm.shoulder.rotation.set(-0.7, 0, -0.2);
      this.rig.rightArm.elbow.rotation.set(-1.0, 0, 0);
    }
  }

  evaluateWearPPE(t, dur) {
    const p = Math.min(1.0, t / dur);
    const lift = Math.sin(p * Math.PI);

    // Hands move up to face/chest
    this.rig.leftArm.shoulder.rotation.set(-1.2 * lift, 0.4 * lift, 0.5 * lift);
    this.rig.leftArm.elbow.rotation.set(-1.4 * lift, 0, 0);

    this.rig.rightArm.shoulder.rotation.set(-1.2 * lift, -0.4 * lift, -0.5 * lift);
    this.rig.rightArm.elbow.rotation.set(-1.4 * lift, 0, 0);
  }

  evaluateDrawBlood(t, dur, targetPos) {
    if (targetPos) {
      this.rig.rightArm.ik.solve(targetPos);
    } else {
      this.rig.rightArm.shoulder.rotation.set(-0.8, -0.3, -0.2);
      this.rig.rightArm.elbow.rotation.set(-0.9, 0, 0);
    }
  }

  evaluateAdminister(t, dur, targetPos) {
    const p = Math.min(1.0, t / dur);
    const reach = Math.sin(p * Math.PI);

    if (targetPos) {
      this.rig.rightArm.ik.solve(targetPos);
    } else {
      this.rig.rightArm.shoulder.rotation.set(-0.7 * reach, -0.2, -0.2);
      this.rig.rightArm.elbow.rotation.set(-0.8 * reach, 0, 0);
    }
  }

  evaluateSwirl(t, dur, targetPos) {
    const angle = t * 10.0;
    const r = 0.035;

    if (targetPos) {
      const pos = targetPos.clone();
      pos.x += Math.cos(angle) * r;
      pos.z += Math.sin(angle) * r;
      this.rig.rightArm.ik.solve(pos);
    } else {
      this.rig.rightArm.shoulder.rotation.set(-0.6, Math.cos(angle) * 0.1, -0.2);
      this.rig.rightArm.elbow.rotation.set(-0.8, 0, 0);
    }
  }

  evaluateTurnStopcock(t, dur, targetPos) {
    const p = Math.min(1.0, t / dur);
    const twist = Math.sin(p * Math.PI) * 1.4;

    if (targetPos) {
      this.rig.rightArm.ik.solve(targetPos);
    } else {
      this.rig.rightArm.shoulder.rotation.set(-0.9, 0, -0.2);
      this.rig.rightArm.elbow.rotation.set(-0.6, 0, 0);
    }
    this.rig.rightArm.hand.rotation.x = twist;
  }

  evaluateRead(t, dur, targetPos) {
    // Head tilts down, right hand gestures
    this.rig.head.rotation.x = 0.35;
    this.rig.rightArm.shoulder.rotation.set(-0.4, 0, -0.2);
    this.rig.rightArm.elbow.rotation.set(-0.5, 0, 0);
  }

  evaluateDispose(t, dur, targetPos) {
    const p = Math.min(1.0, t / dur);
    if (targetPos) {
      this.rig.rightArm.ik.solve(targetPos);
    } else {
      this.rig.rightArm.shoulder.rotation.set(-0.6, 0.2, -0.2);
      this.rig.rightArm.elbow.rotation.set(-0.7, 0, 0);
    }
  }

  evaluateWashHands(t, dur) {
    const rub = Math.sin(t * 14.0) * 0.12;

    this.rig.leftArm.shoulder.rotation.set(-0.7, 0.4, 0.3);
    this.rig.leftArm.elbow.rotation.set(-1.2, 0, 0);
    this.rig.leftArm.hand.position.x = rub;

    this.rig.rightArm.shoulder.rotation.set(-0.7, -0.4, -0.3);
    this.rig.rightArm.elbow.rotation.set(-1.2, 0, 0);
    this.rig.rightArm.hand.position.x = -rub;
  }
}
