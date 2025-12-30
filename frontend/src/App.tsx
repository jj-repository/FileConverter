import { useState } from 'react';
import { TabNavigation } from './components/Layout/TabNavigation';
import { ImageConverter } from './components/Converter/ImageConverter';
import { VideoConverter } from './components/Converter/VideoConverter';
import { AudioConverter } from './components/Converter/AudioConverter';
import { DocumentConverter } from './components/Converter/DocumentConverter';
import { DataConverter } from './components/Converter/DataConverter';
import { ArchiveConverter } from './components/Converter/ArchiveConverter';
import { SpreadsheetConverter } from './components/Converter/SpreadsheetConverter';
import { SubtitleConverter } from './components/Converter/SubtitleConverter';
import { EbookConverter } from './components/Converter/EbookConverter';
import { BatchConverter } from './components/Converter/BatchConverterImproved';
import { FileType } from './types/conversion';

function App() {
  const [activeTab, setActiveTab] = useState<FileType>('image');

  const renderConverter = () => {
    switch (activeTab) {
      case 'image':
        return <ImageConverter />;
      case 'video':
        return <VideoConverter />;
      case 'audio':
        return <AudioConverter />;
      case 'document':
        return <DocumentConverter />;
      case 'data':
        return <DataConverter />;
      case 'archive':
        return <ArchiveConverter />;
      case 'spreadsheet':
        return <SpreadsheetConverter />;
      case 'subtitle':
        return <SubtitleConverter />;
      case 'ebook':
        return <EbookConverter />;
      case 'batch':
        return <BatchConverter />;
      default:
        return <ImageConverter />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            FileConverter
          </h1>
        </header>

        <div className="max-w-6xl mx-auto">
          <TabNavigation activeTab={activeTab} onTabChange={setActiveTab} />
          {renderConverter()}
        </div>

        <footer className="text-center mt-16 text-gray-500 text-sm">
          <p>Built with FastAPI + React + Tailwind CSS</p>
        </footer>
      </div>
    </div>
  );
}

export default App;
