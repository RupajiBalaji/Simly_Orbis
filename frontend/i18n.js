/**
 * Simly Orbis i18n Localization Engine (frontend/i18n.js)
 * Standard: Section 7.8 & Section 18 (P1-T8) of Simly Orbis MVP Build Specification.
 */

let currentLocale = localStorage.getItem('orbis_locale') || 'en';
const dictionaries = {};

/**
 * Register dictionary for a locale
 */
export function registerDictionary(locale, dict) {
  dictionaries[locale] = dict;
}

/**
 * Resolve nested key from an object (e.g. 'lobby.select_district')
 */
function resolveKey(obj, keyPath) {
  if (!obj || typeof obj !== 'object') return null;
  const parts = keyPath.split('.');
  let cur = obj;
  for (const part of parts) {
    if (cur && typeof cur === 'object' && part in cur) {
      cur = cur[part];
    } else {
      return null;
    }
  }
  return (typeof cur === 'string') ? cur : null;
}

/**
 * Translate helper: t(key, params)
 * Fallback priority: currentLocale -> 'en' -> raw key
 */
export function t(key, params = {}) {
  let text = resolveKey(dictionaries[currentLocale], key);
  if (text === null && currentLocale !== 'en') {
    text = resolveKey(dictionaries['en'], key);
  }
  if (text === null) {
    return key;
  }

  // Interpolation: replace {paramName} with value
  return text.replace(/{([^{}]+)}/g, (match, paramName) => {
    const trimmed = paramName.trim();
    return params[trimmed] !== undefined ? String(params[trimmed]) : match;
  });
}

/**
 * Switch active locale and update all data-i18n elements in DOM
 */
export async function setLocale(locale) {
  currentLocale = locale;
  localStorage.setItem('orbis_locale', locale);

  if (!dictionaries[locale]) {
    try {
      const res = await fetch(`/locales/${locale}.json`);
      if (res.ok) {
        dictionaries[locale] = await res.json();
      }
    } catch (_) {}
  }

  applyTranslations();
  window.dispatchEvent(new CustomEvent('orbis_locale_changed', { detail: { locale } }));
  return currentLocale;
}

export function getLocale() {
  return currentLocale;
}

/**
 * Update all DOM elements with data-i18n attributes
 */
export function applyTranslations(root = document) {
  root.querySelectorAll('[data-i18n]').forEach((el) => {
    const key = el.getAttribute('data-i18n');
    const translated = t(key);
    if (translated && translated !== key) {
      if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        el.placeholder = translated;
      } else {
        el.textContent = translated;
      }
    }
  });

  root.querySelectorAll('[data-i18n-title]').forEach((el) => {
    const key = el.getAttribute('data-i18n-title');
    const translated = t(key);
    if (translated && translated !== key) {
      el.title = translated;
    }
  });
}

/**
 * Initialize i18n engine on app startup
 */
export async function initI18n() {
  try {
    const resEn = await fetch('/locales/en.json');
    if (resEn.ok) {
      registerDictionary('en', await resEn.json());
    }
  } catch (_) {}

  if (currentLocale !== 'en') {
    try {
      const resOther = await fetch(`/locales/${currentLocale}.json`);
      if (resOther.ok) {
        registerDictionary(currentLocale, await resOther.json());
      }
    } catch (_) {
      currentLocale = 'en';
    }
  }

  applyTranslations();
}
