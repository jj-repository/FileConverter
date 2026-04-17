import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { DropZone } from '../FileUpload/DropZone';
import { Button } from '../Common/Button';
import { Card } from '../Common/Card';
import { archiveAPI } from '../../services/api';
import { useConverter } from '../../hooks/useConverter';
import { ARCHIVE_FORMATS } from '../../config/constants';


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
                  <p className="text-primary-600 font-semibold text-lg">{t('common.dropToReplace')}</p>
                </div>
              </div>
            )}

            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">
                <span className="font-medium">{t('common.file')}:</span> {converter.selectedFile.name}
              </p>
              <p className="text-sm text-gray-600">
                <span className="font-medium">{t('common.size')}:</span>{' '}
                {(converter.selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
              <p className="text-xs text-gray-500 mt-2">
                💡 {t('dropzone.dragActive')}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor={converter.ids.outputFormat} className="block text-sm font-medium text-gray-700 mb-2">
                  {t('common.outputFormat')}
                </label>
                <select
                  id={converter.ids.outputFormat}
                  value={converter.outputFormat}
                  onChange={(e) => converter.setOutputFormat(e.target.value)}
                  className="input"
                  disabled={converter.status === 'converting'}
                  aria-label="Select output format for archive conversion"
                >
                  {ARCHIVE_FORMATS.map((format) => (
                    <option key={format} value={format}>
                      {format.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="compression-level" className="block text-sm font-medium text-gray-700 mb-2">
                  {t('converter.archive.compressionLevelLabel', { level: compressionLevel })}
                </label>
                <input
                  id="compression-level"
                  type="range"
                  min="0"
                  max="9"
                  value={compressionLevel}
                  onChange={(e) => setCompressionLevel(Number(e.target.value))}
                  className="w-full"
                  disabled={converter.status === 'converting'}
                  aria-label={`Compression level: ${compressionLevel}`}
                  aria-valuemin={0}
                  aria-valuemax={9}
                  aria-valuenow={compressionLevel}
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>{t('converter.archive.faster')}</span>
                  <span>{t('converter.archive.smaller')}</span>
                </div>
              </div>
            </div>

            <div>
              <label htmlFor={converter.ids.customFilename} className="block text-sm font-medium text-gray-700 mb-2">
                {t('common.customFilename')}
              </label>
              <input
                id={converter.ids.customFilename}
                type="text"
                value={converter.customFilename}
                onChange={(e) => converter.setCustomFilename(e.target.value)}
                placeholder={t('common.customFilenamePlaceholder')}
                className="input w-full"
                disabled={converter.status === 'converting'}
                aria-describedby="filename-hint"
              />
              <p id="filename-hint" className="text-xs text-gray-500 mt-1">
                {t('common.customFilenameHint')}
              </p>
            </div>

            {window.electron?.isElectron && (
              <div>
                <label htmlFor={converter.ids.outputDirectory} className="block text-sm font-medium text-gray-700 mb-2">
                  {t('common.outputDirectory')}
                </label>
                <div className="flex gap-2">
                  <input
                    id={converter.ids.outputDirectory}
                    type="text"
                    value={converter.outputDirectory || t('common.defaultDownloads')}
                    readOnly
                    className="input flex-1"
                    disabled={converter.status === 'converting'}
                    aria-describedby="output-directory-hint"
                    aria-label="Output directory path"
                  />
                  <Button
                    onClick={converter.handleSelectOutputDirectory}
                    variant="secondary"
                    disabled={converter.status === 'converting'}
                    aria-label="Browse for output directory"
                  >
                    {t('common.browse')}
                  </Button>
                </div>
                <p id="output-directory-hint" className="text-xs text-gray-500 mt-1">
                  {t('common.outputDirectoryHint')}
                </p>
              </div>
            )}

            {converter.status === 'converting' && converter.showFeedback && (
              <div className="space-y-2">
                {converter.isUploading ? (
                  <>
                    <div className="flex justify-between text-sm text-gray-600">
                      <span>{t('common.uploadingFile')}</span>
                      <span>{converter.uploadProgress}%</span>
                    </div>
                    <div
                      {...converter.getUploadProgressAriaAttributes()}
                      className="w-full bg-gray-200 rounded-full h-2"
                    >
                      <div
                        className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${converter.uploadProgress}%` }}
                        aria-hidden="true"
                      />
                    </div>
                  </>
                ) : (
                  <>
                    <div className="flex justify-between text-sm text-gray-600">
                      <span>{converter.progress?.message || t('common.processing')}</span>
                      <span>{converter.progress?.progress.toFixed(0) || 0}%</span>
                    </div>
                    <div
                      {...converter.getProgressAriaAttributes()}
                      className="w-full bg-gray-200 rounded-full h-2"
                    >
                      <div
                        className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${converter.progress?.progress || 0}%` }}
                        aria-hidden="true"
                      />
                    </div>
                  </>
                )}
              </div>
            )}

            {converter.error && converter.showFeedback && (
              <div
                {...converter.getStatusAriaAttributes()}
                className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg"
              >
                {converter.error}
              </div>
            )}

            {converter.status === 'completed' && converter.showFeedback && (
              <div
                {...converter.getStatusAriaAttributes()}
                className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg"
              >
                {t('converter.archive.completed')}
              </div>
            )}

            <div className="flex gap-4">
              {converter.status === 'idle' || converter.status === 'failed' ? (
                <>
                  <Button onClick={handleConvert} className="flex-1">
                    {t('converter.archive.convertArchive')}
                  </Button>
                  <Button onClick={converter.handleReset} variant="secondary">
                    {t('common.reset')}
                  </Button>
                </>
              ) : converter.status === 'converting' ? (
                <Button disabled loading className="flex-1">
                  {t('common.converting')}
                </Button>
              ) : converter.status === 'completed' ? (
                <>
                  <Button onClick={converter.handleDownload} className="flex-1">
                    {t('common.download')}
                  </Button>
                  <Button onClick={converter.handleReset} variant="secondary">
                    {t('common.convertAnother')}
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
