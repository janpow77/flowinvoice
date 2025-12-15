/**
 * i18n Configuration
 *
 * Internationalization setup for FlowAudit.
 */

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import { de } from './de';
import { en } from './en';

// Supported languages
export const languages = [
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'en', name: 'English', flag: '🇬🇧' },
] as const;

export type LanguageCode = typeof languages[number]['code'];

// Initialize i18next
i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      de: { translation: de },
      en: { translation: en },
    },
    fallbackLng: 'de',
    supportedLngs: ['de', 'en'],
    debug: false,
    interpolation: {
      escapeValue: false, // React already escapes
    },
    detection: {
      order: ['localStorage', 'navigator'],
      lookupLocalStorage: 'flowaudit-language',
      caches: ['localStorage'],
    },
  });

// Helper to change language
export const changeLanguage = (lng: LanguageCode) => {
  i18n.changeLanguage(lng);
  localStorage.setItem('flowaudit-language', lng);
};

// Get current language
export const getCurrentLanguage = (): LanguageCode => {
  return (i18n.language || 'de') as LanguageCode;
};

export default i18n;
