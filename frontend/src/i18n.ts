import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from './locales/en.json';
import de from './locales/de.json';
import pl from './locales/pl.json';

// Get saved language from localStorage or default to browser language
const savedLanguage = localStorage.getItem('language');
const browserLanguage = navigator.language.split('-')[0]; // Get 'en' from 'en-US'
const defaultLanguage = savedLanguage || (browserLanguage === 'de' || browserLanguage === 'pl' ? browserLanguage : 'en');

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
