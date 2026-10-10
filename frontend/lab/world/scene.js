/**
 * 3D Scene Manager, Camera, Lighting & Raycasting (frontend/lab/world/scene.js)
 * Manages Three.js renderer lifecycle, OrbitControls, interactive raycaster,
 * and station camera transitions.
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/OrbitControls.js';
import { buildLabRoom } from './room.js';
import { buildApparatus } from './apparatus.js';
import { state } from '../state.js';

export class LabScene {
  constructor(canvasElement) {
    this.canvas = canvasElement;
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;
    this.roomGroup = null;
    this.apparatusLookup = {};
    this.apparatusContainer = null;

    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2(-999, -999);
    this.hoveredObject = null;
    this.selectedObject = null;

    this.isTransitioningCamera = false;
    this.cameraTarget = new THREE.Vector3(0, 1.2, -2.5);
    this.cameraDefaultPos = new THREE.Vector3(0, 3.6, 4.2);

    this.animationFrameId = null;
    this.lastTime = performance.now();
    this.frameCount = 0;
    this.fpsTimer = performance.now();

    this.init();
  }

  init() {
    // 1. Scene & Fog
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0c071d);
    this.scene.fog = new THREE.FogExp2(0x0c071d, 0.035);

    // 2. Camera
    const aspect = window.innerWidth / window.innerHeight;
    this.camera = new THREE.PerspectiveCamera(50, aspect, 0.1, 50);
    this.camera.position.copy(this.cameraDefaultPos);

    // 3. Renderer
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      powerPreference: 'high-performance',
    });
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // capped at 2 for 60fps
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.15;

    // 4. OrbitControls (touch + mouse)
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.06;
    this.controls.maxPolarAngle = Math.PI / 2.05; // do not go below floor
    this.controls.minDistance = 1.2;
    this.controls.maxDistance = 14.0;
    this.controls.target.copy(this.cameraTarget);

    // 5. Room geometry & permanent fixtures
    this.roomGroup = buildLabRoom(this.scene);

    // 6. Event listeners
    this.onWindowResize = this.onWindowResize.bind(this);
    this.onPointerMove = this.onPointerMove.bind(this);
    this.onPointerDown = this.onPointerDown.bind(this);
    this.animate = this.animate.bind(this);

    window.addEventListener('resize', this.onWindowResize, false);
    this.canvas.addEventListener('pointermove', this.onPointerMove, false);
    this.canvas.addEventListener('pointerdown', this.onPointerDown, false);

    // Start render loop
    this.lastTime = performance.now();
    this.animate();
  }

  loadExperiment(experimentDef) {
    if (this.apparatusContainer) {
      this.scene.remove(this.apparatusContainer);
      this.apparatusContainer = null;
      this.apparatusLookup = {};
    }

    const apparatusList = experimentDef?.apparatus || [];
    const { container, lookup } = buildApparatus(apparatusList, this.scene);
    this.apparatusContainer = container;
    this.apparatusLookup = lookup;

    this.resetCameraView();
  }

  getApparatus(targetId) {
    if (!targetId) return null;
    return this.apparatusLookup[targetId] || null;
  }

  focusOnStation(targetId) {
    const obj = this.getApparatus(targetId);
    if (!obj) return;

    const worldPos = new THREE.Vector3();
    obj.getWorldPosition(worldPos);

    // Smooth transition camera target toward station
    this.cameraTarget.set(worldPos.x, worldPos.y + 0.3, worldPos.z);
    this.controls.target.copy(this.cameraTarget);
  }

  resetCameraView() {
    this.cameraTarget.set(0, 1.2, -2.5);
    this.controls.target.copy(this.cameraTarget);
    this.camera.position.copy(this.cameraDefaultPos);
  }

  onWindowResize() {
    if (!this.camera || !this.renderer) return;
    this.camera.aspect = window.innerWidth / window.innerHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  }

  onPointerMove(event) {
    const rect = this.canvas.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    // Raycast apparatus
    if (!this.apparatusContainer) return;

    this.raycaster.setFromCamera(this.mouse, this.camera);
    const intersects = this.raycaster.intersectObjects(this.apparatusContainer.children, true);

    if (intersects.length > 0) {
      // Find top apparatus group with userData.targetId
      let current = intersects[0].object;
      while (current && current.parent !== this.apparatusContainer && !current.userData?.targetId) {
        current = current.parent;
      }

      if (current && current.userData?.targetId) {
        if (this.hoveredObject !== current) {
          this.clearHover();
          this.hoveredObject = current;
          this.applyHoverHighlight(current, true);
          this.canvas.style.cursor = 'pointer';
        }
        return;
      }
    }

    if (this.hoveredObject) {
      this.clearHover();
      this.canvas.style.cursor = 'default';
    }
  }

  onPointerDown(event) {
    if (event.button !== 0) return; // Left click only

    if (this.hoveredObject && this.hoveredObject.userData?.targetId) {
      const targetId = this.hoveredObject.userData.targetId;
      state.setSelectedTarget(targetId);
      this.selectApparatus(this.hoveredObject);
    }
  }

  applyHoverHighlight(obj, enable) {
    obj.traverse((child) => {
      if (child.isMesh && child.material) {
        if (enable) {
          if (!child.userData.origEmissive) {
            child.userData.origEmissive = child.material.emissive ? child.material.emissive.getHex() : 0;
          }
          if (child.material.emissive) {
            child.material.emissive.setHex(0x9333ea);
          }
        } else {
          if (child.material.emissive && child.userData.origEmissive !== undefined) {
            child.material.emissive.setHex(child.userData.origEmissive);
          }
        }
      }
    });
  }

  clearHover() {
    if (this.hoveredObject) {
      this.applyHoverHighlight(this.hoveredObject, false);
      this.hoveredObject = null;
    }
  }

  selectApparatus(obj) {
    if (this.selectedObject) {
      this.applyHoverHighlight(this.selectedObject, false);
    }
    this.selectedObject = obj;
    this.focusOnStation(obj.userData.targetId);
  }

  animate() {
    this.animationFrameId = requestAnimationFrame(this.animate);

    // Pause rendering when tab is hidden to save GPU battery
    if (document.hidden) return;

    const now = performance.now();
    const dt = (now - this.lastTime) / 1000;
    this.lastTime = now;

    // Controls update
    if (this.controls) {
      this.controls.update();
    }

    // Render
    if (this.renderer && this.scene && this.camera) {
      this.renderer.render(this.scene, this.camera);

      // FPS and Draw Calls counter for debug overlay
      this.frameCount++;
      if (now - this.fpsTimer >= 500) {
        const fps = Math.round((this.frameCount * 1000) / (now - this.fpsTimer));
        const drawCalls = this.renderer.info.render.calls;
        state.updateStats({ fps, drawCalls });
        this.frameCount = 0;
        this.fpsTimer = now;
      }
    }
  }

  destroy() {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }
    window.removeEventListener('resize', this.onWindowResize);
    this.canvas.removeEventListener('pointermove', this.onPointerMove);
    this.canvas.removeEventListener('pointerdown', this.onPointerDown);
    this.renderer.dispose();
  }
}
