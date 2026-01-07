import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from './locales/en.json';
import de from './locales/de.json';
import pl from './locales/pl.json';

// Supported languages list
const SUPPORTED_LANGUAGES = ['en', 'de', 'pl'] as const;
type SupportedLanguage = typeof SUPPORTED_LANGUAGES[number];

const isValidLanguage = (lang: string | null): lang is SupportedLanguage => {
  return lang !== null && SUPPORTED_LANGUAGES.includes(lang as SupportedLanguage);
};

// Get saved language from localStorage and validate against supported languages
const savedLanguage = localStorage.getItem('language');
const validatedSavedLanguage = isValidLanguage(savedLanguage) ? savedLanguage : null;
const browserLanguage = navigator.language.split('-')[0]; // Get 'en' from 'en-US'
const defaultLanguage = validatedSavedLanguage || (isValidLanguage(browserLanguage) ? browserLanguage : 'en');

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      de: { translation: de },
      pl: { translation: pl },
    },
    lng: defaultLanguage,
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false, // React already escapes values
    },
  });

// Save language to localStorage when it changes
i18n.on('languageChanged', (lng) => {
  localStorage.setItem('language', lng);
});

export default i18n;
