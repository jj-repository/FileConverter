import React from 'react';
import { useTranslation } from 'react-i18next';
import { FileType } from '../../types/conversion';

interface Tab {
  id: FileType;
  translationKey: string;
  icon: string;
}

const tabs: Tab[] = [
  { id: 'image', translationKey: 'nav.images', icon: '🖼️' },
  { id: 'video', translationKey: 'nav.videos', icon: '🎥' },
  { id: 'audio', translationKey: 'nav.audio', icon: '🎵' },
  { id: 'document', translationKey: 'nav.documents', icon: '📄' },
  { id: 'batch', translationKey: 'nav.batch', icon: '📦' },
  { id: 'data', translationKey: 'nav.data', icon: '📊' },
  { id: 'archive', translationKey: 'nav.archives', icon: '🗜️' },
  { id: 'spreadsheet', translationKey: 'nav.spreadsheets', icon: '📈' },
  { id: 'subtitle', translationKey: 'nav.subtitles', icon: '💬' },
  { id: 'ebook', translationKey: 'nav.ebooks', icon: '📚' },
  { id: 'font', translationKey: 'nav.fonts', icon: '🔤' },
];

interface TabNavigationProps {
  activeTab: FileType;
  onTabChange: (tab: FileType) => void;
}

export const TabNavigation: React.FC<TabNavigationProps> = ({ activeTab, onTabChange }) => {
  const { t } = useTranslation();

  const handleKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>, index: number) => {
    if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight' && event.key !== 'Home' && event.key !== 'End') {
      return;
    }
    event.preventDefault();
    let nextIndex = index;
    if (event.key === 'ArrowLeft') nextIndex = (index - 1 + tabs.length) % tabs.length;
    if (event.key === 'ArrowRight') nextIndex = (index + 1) % tabs.length;
    if (event.key === 'Home') nextIndex = 0;
    if (event.key === 'End') nextIndex = tabs.length - 1;
    const next = tabs[nextIndex];
    onTabChange(next.id);
    const el = document.getElementById(`${next.id}-tab`);
    el?.focus();
  };

  return (
    <div className="border-b border-gray-200 mb-8 overflow-x-auto">
      <nav className="flex space-x-8 min-w-min" role="tablist" aria-label="Tabs">
        {tabs.map((tab, index) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`${tab.id}-panel`}
            id={`${tab.id}-tab`}
            tabIndex={activeTab === tab.id ? 0 : -1}
            onKeyDown={(e) => handleKeyDown(e, index)}
            onClick={() => onTabChange(tab.id)}
            className={`
              py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 whitespace-nowrap
              ${
                activeTab === tab.id
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }
            `}
          >
            <span className="flex items-center gap-2">
              <span className="text-xl">{tab.icon}</span>
              {t(tab.translationKey)}
            </span>
          </button>
        ))}
      </nav>
    </div>
  );
};
