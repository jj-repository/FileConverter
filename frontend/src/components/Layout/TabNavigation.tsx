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

  return (
    <div className="border-b border-gray-200 mb-8 overflow-x-auto">
      <nav className="flex space-x-8 min-w-min" aria-label="Tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
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
