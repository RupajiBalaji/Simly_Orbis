/**
 * Procedural Bloom Post-Processing Pipeline (frontend/vendor/addons/bloom.js)
 * High-performance, offline-capable bloom for High quality tier.
 * Self-contained Three.js r160 compatible post-processing pass.
 */

import * as THREE from 'three';

export class SimpleBloomPipeline {
  constructor(renderer, scene, camera, width, height) {
    this.renderer = renderer;
    this.scene = scene;
    this.camera = camera;
    this.enabled = true;

    const renderTargetParams = {
      minFilter: THREE.LinearFilter,
      magFilter: THREE.LinearFilter,
      format: THREE.RGBAFormat,
      type: THREE.HalfFloatType,
    };

    const w = Math.max(320, width || 1280);
    const h = Math.max(180, height || 720);

    this.sceneTarget = new THREE.WebGLRenderTarget(w, h, renderTargetParams);
    this.bloomTarget = new THREE.WebGLRenderTarget(Math.floor(w / 2), Math.floor(h / 2), renderTargetParams);

    // Additive composite shader quad
    this.compositeMaterial = new THREE.ShaderMaterial({
      uniforms: {
        tDiffuse: { value: this.sceneTarget.texture },
        tBloom: { value: this.bloomTarget.texture },
        bloomIntensity: { value: 0.55 },
      },
      vertexShader: `
        varying vec2 vUv;
        void main() {
          vUv = uv;
          gl_Position = vec4(position.xy, 0.0, 1.0);
        }
      `,
      fragmentShader: `
        uniform sampler2D tDiffuse;
        uniform sampler2D tBloom;
        uniform float bloomIntensity;
        varying vec2 vUv;
        void main() {
          vec4 base = texture2D(tDiffuse, vUv);
          vec4 glow = texture2D(tBloom, vUv);
          // Soft bloom thresholding
          vec3 bright = max(vec3(0.0), glow.rgb - 0.7) * 2.5;
          gl_FragColor = vec4(base.rgb + bright * bloomIntensity, 1.0);
        }
      `,
      depthTest: false,
      depthWrite: false,
    });

    this.fsQuadGeo = new THREE.PlaneGeometry(2, 2);
    this.fsQuadMesh = new THREE.Mesh(this.fsQuadGeo, this.compositeMaterial);
    this.fsScene = new THREE.Scene();
    this.fsCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    this.fsScene.add(this.fsQuadMesh);
  }

  setSize(width, height) {
    const w = Math.max(320, width);
    const h = Math.max(180, height);
    this.sceneTarget.setSize(w, h);
    this.bloomTarget.setSize(Math.floor(w / 2), Math.floor(h / 2));
  }

  render() {
    if (!this.enabled) {
      this.renderer.render(this.scene, this.camera);
      return;
    }

    // 1. Render primary scene to sceneTarget
    this.renderer.setRenderTarget(this.sceneTarget);
    this.renderer.render(this.scene, this.camera);

    // 2. Downsample to half-res bloom target
    this.renderer.setRenderTarget(this.bloomTarget);
    this.renderer.render(this.scene, this.camera);

    // 3. Composite additive bloom back to default canvas buffer
    this.renderer.setRenderTarget(null);
    this.renderer.render(this.fsScene, this.fsCamera);
  }

  dispose() {
    this.sceneTarget.dispose();
    this.bloomTarget.dispose();
    this.compositeMaterial.dispose();
    this.fsQuadGeo.dispose();
  }
}
