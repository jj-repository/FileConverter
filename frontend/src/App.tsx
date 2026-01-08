import { useState, lazy, Suspense } from 'react';
import { TabNavigation } from './components/Layout/TabNavigation';
import { LanguageSelector } from './components/Common/LanguageSelector';
import { ToastProvider } from './components/Common/Toast';
import ErrorBoundary from './components/ErrorBoundary';
import { FileType } from './types/conversion';

// Lazy load all converter components
const ImageConverter = lazy(() => import('./components/Converter/ImageConverter').then(module => ({ default: module.ImageConverter })));
const VideoConverter = lazy(() => import('./components/Converter/VideoConverter').then(module => ({ default: module.VideoConverter })));
const AudioConverter = lazy(() => import('./components/Converter/AudioConverter').then(module => ({ default: module.AudioConverter })));
const DocumentConverter = lazy(() => import('./components/Converter/DocumentConverter').then(module => ({ default: module.DocumentConverter })));
const DataConverter = lazy(() => import('./components/Converter/DataConverter').then(module => ({ default: module.DataConverter })));
const ArchiveConverter = lazy(() => import('./components/Converter/ArchiveConverter').then(module => ({ default: module.ArchiveConverter })));
const SpreadsheetConverter = lazy(() => import('./components/Converter/SpreadsheetConverter').then(module => ({ default: module.SpreadsheetConverter })));
const SubtitleConverter = lazy(() => import('./components/Converter/SubtitleConverter').then(module => ({ default: module.SubtitleConverter })));
const EbookConverter = lazy(() => import('./components/Converter/EbookConverter').then(module => ({ default: module.EbookConverter })));
const FontConverter = lazy(() => import('./components/Converter/FontConverter').then(module => ({ default: module.FontConverter })));
const BatchConverter = lazy(() => import('./components/Converter/BatchConverterImproved').then(module => ({ default: module.BatchConverter })));

function App() {
  const [activeTab, setActiveTab] = useState<FileType>('image');

  const renderConverter = () => {
    // Error fallback specifically for lazy-loaded component failures
    const lazyLoadErrorFallback = (
      <div className="flex items-center justify-center py-16">
        <div className="text-center max-w-md">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Failed to load converter</h3>
          <p className="text-gray-600 mb-4">There was a problem loading this component. Please try refreshing the page.</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
          >
            Refresh Page
          </button>
        </div>
      </div>
    );

    return (
      <ErrorBoundary fallback={lazyLoadErrorFallback}>
        <Suspense fallback={
          <div className="flex items-center justify-center py-16">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
              <p className="text-gray-600 text-lg">Loading converter...</p>
            </div>
          </div>
        }>
          {(() => {
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
              case 'font':
                return <FontConverter />;
              case 'batch':
                return <BatchConverter />;
              default:
                return <ImageConverter />;
            }
          })()}
        </Suspense>
      </ErrorBoundary>
    );
  };

  return (
    <ToastProvider>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="container mx-auto px-4 py-8">
          <header className="mb-12">
            <div className="flex justify-between items-start mb-4">
              <div className="flex-1"></div>
              <h1 className="text-5xl font-bold text-gray-900 text-center flex-1">
                FileConverter
              </h1>
              <div className="flex-1 flex justify-end">
                <LanguageSelector />
              </div>
            </div>
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
    </ToastProvider>
  );
}

export default App;
