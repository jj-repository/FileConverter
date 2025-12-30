import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { DropZone } from '../FileUpload/DropZone';
import { Button } from '../Common/Button';
import { Card } from '../Common/Card';
import { archiveAPI } from '../../services/api';
import { useConverter } from '../../hooks/useConverter';

const ARCHIVE_FORMATS = ['zip', 'tar', 'tar.gz', 'tgz', 'tar.bz2', 'tbz2', 'gz', '7z'];

export const ArchiveConverter: React.FC = () => {
  const { t } = useTranslation();
  const [compressionLevel, setCompressionLevel] = useState<number>(6);

  const converter = useConverter({ defaultOutputFormat: 'zip' });

  const handleConvert = async () => {
    await converter.handleConvert(archiveAPI, { compressionLevel });
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Card>
        <h2 className="text-2xl font-bold text-gray-800 mb-6">{t('converter.archive.title')}</h2>

        {!converter.selectedFile ? (
          <DropZone
            onFileSelect={converter.handleFileSelect}
            acceptedFormats={ARCHIVE_FORMATS}
            fileType="archive"
          />
        ) : (
          <div
            className="space-y-6 relative"
            onDragOver={converter.handleDragOver}
            onDragLeave={converter.handleDragLeave}
            onDrop={converter.handleDrop}
          >
            {converter.isDraggingOver && (
              <div className="absolute inset-0 z-10 bg-primary-500 bg-opacity-20 border-4 border-primary-500 border-dashed rounded-lg flex items-center justify-center">
                <div className="bg-white px-6 py-4 rounded-lg shadow-lg">
                  <p className="text-primary-600 font-semibold text-lg">Drop to replace file</p>
                </div>
              </div>
            )}

            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">
                <span className="font-medium">File:</span> {converter.selectedFile.name}
              </p>
              <p className="text-sm text-gray-600">
                <span className="font-medium">Size:</span>{' '}
                {(converter.selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
              <p className="text-xs text-gray-500 mt-2">
                💡 {t('dropzone.dragActive')}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Output Format
                </label>
                <select
                  value={converter.outputFormat}
                  onChange={(e) => converter.setOutputFormat(e.target.value)}
                  className="input"
                  disabled={converter.status === 'converting'}
                >
                  {ARCHIVE_FORMATS.map((format) => (
                    <option key={format} value={format}>
                      {format.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Compression Level ({compressionLevel})
                </label>
                <input
                  type="range"
                  min="0"
                  max="9"
                  value={compressionLevel}
                  onChange={(e) => setCompressionLevel(Number(e.target.value))}
                  className="w-full"
                  disabled={converter.status === 'converting'}
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>Faster</span>
                  <span>Smaller</span>
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Custom Filename (Optional)
              </label>
              <input
                type="text"
                value={converter.customFilename}
                onChange={(e) => converter.setCustomFilename(e.target.value)}
                placeholder={t('common.customFilenamePlaceholder')}
                className="input w-full"
                disabled={converter.status === 'converting'}
              />
              <p className="text-xs text-gray-500 mt-1">
                {t('common.customFilenameHint')}
              </p>
            </div>

            {window.electron?.isElectron && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Output Directory (Optional)
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={converter.outputDirectory || t('common.defaultDownloads')}
                    readOnly
                    className="input flex-1"
                    disabled={converter.status === 'converting'}
                  />
                  <Button
                    onClick={converter.handleSelectOutputDirectory}
                    variant="secondary"
                    disabled={converter.status === 'converting'}
                  >
                    Browse
                  </Button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  💡 When set, files will be saved directly to this directory
                </p>
              </div>
            )}

            {converter.status === 'converting' && converter.showFeedback && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm text-gray-600">
                  <span>{converter.progress?.message || t('common.processing')}</span>
                  <span>{converter.progress?.progress.toFixed(0) || 0}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${converter.progress?.progress || 0}%` }}
                  />
                </div>
              </div>
            )}

            {converter.error && converter.showFeedback && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {converter.error}
              </div>
            )}

            {converter.status === 'completed' && converter.showFeedback && (
              <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
                Archive conversion completed successfully!
              </div>
            )}

            <div className="flex gap-4">
              {converter.status === 'idle' || converter.status === 'failed' ? (
                <>
                  <Button onClick={handleConvert} className="flex-1">
                    Convert Archive
                  </Button>
                  <Button onClick={converter.handleReset} variant="secondary">
                    Reset
                  </Button>
                </>
              ) : converter.status === 'converting' ? (
                <Button disabled loading className="flex-1">
                  Converting...
                </Button>
              ) : converter.status === 'completed' ? (
                <>
                  <Button onClick={converter.handleDownload} className="flex-1">
                    Download
                  </Button>
                  <Button onClick={converter.handleReset} variant="secondary">
                    Convert Another
                  </Button>
                </>
              ) : null}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};
