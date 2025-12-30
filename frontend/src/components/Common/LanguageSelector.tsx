import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

interface Language {
  code: string;
  name: string;
  flag: string;
}

const languages: Language[] = [
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'pl', name: 'Polski', flag: '🇵🇱' },
];

export const LanguageSelector: React.FC = () => {
  const { i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  const currentLanguage = languages.find((lang) => lang.code === i18n.language) || languages[0];

  const handleLanguageChange = (languageCode: string) => {
    i18n.changeLanguage(languageCode);
    setIsOpen(false);
    // Return focus to button after selection
    buttonRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
      buttonRef.current?.focus();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (!isOpen) {
        setIsOpen(true);
      } else {
        // Focus first item in menu
        const firstButton = menuRef.current?.querySelector('button') as HTMLButtonElement;
        firstButton?.focus();
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (isOpen) {
        // Focus last item in menu
        const buttons = menuRef.current?.querySelectorAll('button');
        const lastButton = buttons?.[buttons.length - 1] as HTMLButtonElement;
        lastButton?.focus();
      }
    }
  };

  const handleMenuKeyDown = (e: React.KeyboardEvent, index: number) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      const buttons = menuRef.current?.querySelectorAll('button');
      const nextButton = buttons?.[index + 1] as HTMLButtonElement;
      if (nextButton) {
        nextButton.focus();
      } else {
        // Wrap to first
        (buttons?.[0] as HTMLButtonElement)?.focus();
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      const buttons = menuRef.current?.querySelectorAll('button');
      const prevButton = buttons?.[index - 1] as HTMLButtonElement;
      if (prevButton) {
        prevButton.focus();
      } else {
        // Wrap to last
        (buttons?.[buttons.length - 1] as HTMLButtonElement)?.focus();
      }
    } else if (e.key === 'Home') {
      e.preventDefault();
      const buttons = menuRef.current?.querySelectorAll('button');
      (buttons?.[0] as HTMLButtonElement)?.focus();
    } else if (e.key === 'End') {
      e.preventDefault();
      const buttons = menuRef.current?.querySelectorAll('button');
      (buttons?.[buttons.length - 1] as HTMLButtonElement)?.focus();
    }
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
        aria-label={`Select language. Current language: ${currentLanguage.name}`}
        aria-expanded={isOpen}
        aria-haspopup="menu"
        aria-controls="language-menu"
      >
        <span className="text-xl" aria-hidden="true">{currentLanguage.flag}</span>
        <span className="hidden sm:inline">{currentLanguage.name}</span>
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div
          id="language-menu"
          ref={menuRef}
          role="menu"
          aria-labelledby="language-selector-button"
          className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-md shadow-lg z-50"
        >
          <div className="py-1">
            {languages.map((language, index) => (
              <button
                key={language.code}
                role="menuitem"
                onClick={() => handleLanguageChange(language.code)}
                onKeyDown={(e) => handleMenuKeyDown(e, index)}
                aria-current={currentLanguage.code === language.code ? 'true' : undefined}
                className={`w-full text-left px-4 py-2 text-sm flex items-center gap-3 hover:bg-gray-100 transition-colors focus:outline-none focus:bg-gray-100 ${
                  currentLanguage.code === language.code
                    ? 'bg-primary-50 text-primary-700 font-medium'
                    : 'text-gray-700'
                }`}
              >
                <span className="text-xl" aria-hidden="true">{language.flag}</span>
                <span>{language.name}</span>
                {currentLanguage.code === language.code && (
                  <svg
                    className="ml-auto w-4 h-4 text-primary-600"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                    aria-hidden="true"
                  >
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
