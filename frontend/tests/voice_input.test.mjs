import test from 'node:test';
import assert from 'node:assert/strict';
import { detectVoiceSupport, configureVoiceFallback } from '../lab/game/voice_input.js';

function makeMockButton() {
  const attrs = {};
  return {
    disabled: false,
    title: '',
    style: {},
    setAttribute(k, v) { attrs[k] = v; },
    getAttribute(k) { return attrs[k]; },
  };
}

test('unsupported browser falls back to typed input and disables mic', () => {
  const win = {};
  const micBtn = makeMockButton();
  const inputEl = { disabled: true, placeholder: '' };

  const support = detectVoiceSupport(win);
  assert.equal(support.supported, false);

  const res = configureVoiceFallback({ win, micBtn, inputEl });
  assert.equal(res.supported, false);
  assert.equal(res.mode, 'typed-fallback');
  assert.equal(res.recognition, null);
  assert.equal(micBtn.disabled, true);
  assert.equal(micBtn.getAttribute('aria-disabled'), 'true');
  assert.equal(inputEl.disabled, false);
});

test('supported browser initializes speech recognition and delivers transcript', () => {
  let received = '';
  class MockSpeechRecognition {
    start() {
      this.onresult({ results: [[{ transcript: 'put on goggles' }]] });
    }
  }
  const win = { webkitSpeechRecognition: MockSpeechRecognition };
  const micBtn = makeMockButton();
  const res = configureVoiceFallback({
    win,
    micBtn,
    onResult: (t) => { received = t; },
  });
  assert.equal(res.supported, true);
  assert.equal(res.mode, 'voice');
  assert.equal(micBtn.disabled, false);
  res.recognition.start();
  assert.equal(received, 'put on goggles');
});
