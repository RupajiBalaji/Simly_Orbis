/**
 * Voice Input Helper with Web Speech API Feature Detection & Typed Fallback (P7-T3).
 * Purely client-side; never uploads or stores audio.
 */

export function detectVoiceSupport(win = typeof window !== 'undefined' ? window : globalThis) {
  if (!win) return { supported: false, Constructor: null };
  const Constructor = win.SpeechRecognition || win.webkitSpeechRecognition || null;
  return {
    supported: typeof Constructor === 'function',
    Constructor: typeof Constructor === 'function' ? Constructor : null,
  };
}

export function configureVoiceFallback({
  win = typeof window !== 'undefined' ? window : globalThis,
  micBtn = null,
  inputEl = null,
  onStart = () => {},
  onResult = () => {},
  onError = () => {},
  onEnd = () => {},
} = {}) {
  const { supported, Constructor } = detectVoiceSupport(win);

  if (!supported || !Constructor) {
    if (micBtn) {
      micBtn.disabled = true;
      micBtn.setAttribute('aria-disabled', 'true');
      micBtn.title = 'Voice input not supported in this browser — type your instruction instead';
      if (micBtn.style) micBtn.style.opacity = '0.4';
    }
    if (inputEl) {
      inputEl.disabled = false;
      if (!inputEl.placeholder) {
        inputEl.placeholder = 'Type your laboratory instruction...';
      }
    }
    return { supported: false, mode: 'typed-fallback', recognition: null };
  }

  try {
    const recognition = new Constructor();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    recognition.onstart = () => onStart();
    recognition.onresult = (event) => {
      const transcript = event?.results?.[0]?.[0]?.transcript || '';
      if (transcript) onResult(transcript);
    };
    recognition.onerror = (err) => onError(err?.error || 'unknown');
    recognition.onend = () => onEnd();
    if (micBtn) {
      micBtn.disabled = false;
      micBtn.setAttribute('aria-disabled', 'false');
    }
    return { supported: true, mode: 'voice', recognition };
  } catch (_err) {
    if (micBtn) {
      micBtn.disabled = true;
      micBtn.setAttribute('aria-disabled', 'true');
      if (micBtn.style) micBtn.style.opacity = '0.4';
    }
    return { supported: false, mode: 'typed-fallback', recognition: null };
  }
}
