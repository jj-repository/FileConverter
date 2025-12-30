import React from 'react';
import { FileType } from '../../types/conversion';

interface Tab {
  id: FileType;
  label: string;
  icon: string;
}

const tabs: Tab[] = [
  { id: 'image', label: 'Images', icon: '🖼️' },
  { id: 'video', label: 'Videos', icon: '🎥' },
  { id: 'audio', label: 'Audio', icon: '🎵' },
  { id: 'document', label: 'Documents', icon: '📄' },
  { id: 'data', label: 'Data', icon: '📊' },
  { id: 'batch', label: 'Batch', icon: '📦' },
];

interface TabNavigationProps {
  activeTab: FileType;
  onTabChange: (tab: FileType) => void;
}

export const TabNavigation: React.FC<TabNavigationProps> = ({ activeTab, onTabChange }) => {
  return (
    <div className="border-b border-gray-200 mb-8">
      <nav className="flex space-x-8" aria-label="Tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`
              py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200
              ${
                activeTab === tab.id
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }
            `}
          >
            <span className="flex items-center gap-2">
              <span className="text-xl">{tab.icon}</span>
              {tab.label}
            </span>
          </button>
        ))}
      </nav>
    </div>
  );
};
