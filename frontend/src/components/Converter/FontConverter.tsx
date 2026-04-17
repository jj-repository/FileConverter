import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { DropZone } from '../FileUpload/DropZone';
import { Button } from '../Common/Button';
import { Card } from '../Common/Card';
import { fontAPI } from '../../services/api';
import { useConverter } from '../../hooks/useConverter';
import { FONT_FORMATS } from '../../config/constants';


export const FontConverter: React.FC = () => {
  const { t } = useTranslation();
  const [subsetText, setSubsetText] = useState<string>('');
  const [optimize, setOptimize] = useState<boolean>(true);

  const converter = useConverter({ defaultOutputFormat: 'woff2' });

  const handleConvert = async () => {
    await converter.handleConvert(fontAPI, {
      subsetText: subsetText || undefined,
      optimize,
    });
  };

  const getStatusColor = () => {
    switch (converter.status) {
      case 'completed':
        return 'text-green-600';
      case 'failed':
        return 'text-red-600';
      case 'converting':
      case 'uploading':
        return 'text-blue-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusText = () => {
    if (converter.progress?.message) return converter.progress.message;

    switch (converter.status) {
      case 'uploading':
        return t('messages.uploadingFile');
      case 'converting':
        return t('converter.font.converting');
      case 'completed':
        return t('converter.font.completed');
      case 'failed':
        return converter.error || t('common.failed');
      default:
        return t('converter.font.readyToConvert');
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-blue-900 mb-2">{t('converter.font.title')}</h3>
        <p className="text-sm text-blue-800">
          {t('converter.font.webInfo')}
        </p>
        <ul className="mt-2 text-sm text-blue-700 list-disc list-inside space-y-1">
          <li><strong>TTF</strong> {t('converter.font.ttfDesc')}</li>
          <li><strong>OTF</strong> {t('converter.font.otfDesc')}</li>
          <li><strong>WOFF</strong>: {t('converter.font.woffDesc')}</li>
          <li><strong>WOFF2</strong>: {t('converter.font.woff2Desc')}</li>
        </ul>
      </div>

      <Card>
        <div className="space-y-6">
          <DropZone
            onFileSelect={converter.handleFileSelect}
            acceptedFormats={FONT_FORMATS}
            fileType="font"
          />

          {converter.selectedFile && (
            <>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">{t('common.selectFile')}:</p>
                <p className="font-medium">{converter.selectedFile.name}</p>
                <p className="text-sm text-gray-500">
                  {(converter.selectedFile.size / 1024).toFixed(2)} KB
                </p>
              </div>

              <div>
                <label htmlFor="output-format" className="block text-sm font-medium text-gray-700 mb-2">
                  {t('common.outputFormat')}
                </label>
                <select
                  id="output-format"
                  value={converter.outputFormat}
                  onChange={(e) => converter.setOutputFormat(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  aria-label="Select output format for font conversion"
                >
                  {FONT_FORMATS.map((format) => (
                    <option key={format} value={format}>
                      {format.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              <div className="border-t pt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-3">{t('converter.font.advancedOptions')}</h4>

                <div className="mb-4">
                  <label htmlFor="subset-text" className="block text-sm font-medium text-gray-700 mb-2">
                    {t('converter.font.subsetText')}
                  </label>
                  <input
                    id="subset-text"
                    type="text"
                    value={subsetText}
                    onChange={(e) => setSubsetText(e.target.value)}
                    placeholder="e.g., ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    aria-describedby="subset-text-hint"
                  />
                  <p id="subset-text-hint" className="text-xs text-gray-500 mt-1">
                    {t('converter.font.subsetTextHint')}
                  </p>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="optimize"
                    checked={optimize}
                    onChange={(e) => setOptimize(e.target.checked)}
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  />
                  <label htmlFor="optimize" className="ml-2 block text-sm text-gray-700">
                    {t('converter.font.optimize')}
                  </label>
                </div>
              </div>

              {window.electron?.isElectron && (
                <div>
                  <label htmlFor="custom-filename" className="block text-sm font-medium text-gray-700 mb-2">
                    {t('common.customFilename')}
                  </label>
                  <input
                    id="custom-filename"
                    type="text"
                    value={converter.customFilename}
                    onChange={(e) => converter.setCustomFilename(e.target.value)}
                    placeholder={`${converter.selectedFile.name.split('.')[0]}.${converter.outputFormat}`}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
              )}

              {window.electron?.isElectron && (
                <div>
                  <label htmlFor="output-directory" className="block text-sm font-medium text-gray-700 mb-2">
                    {t('common.outputDirectory')}
                  </label>
                  <div className="flex gap-2">
                    <input
                      id="output-directory"
                      type="text"
                      value={converter.outputDirectory || 'Default Downloads folder'}
                      readOnly
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg bg-gray-50"
                      aria-label="Output directory path"
                    />
                    <Button
                      onClick={converter.handleSelectOutputDirectory}
                      variant="secondary"
                      aria-label="Browse for output directory"
                    >
                      {t('common.browse')}
                    </Button>
                  </div>
                </div>
              )}

              <Button
                onClick={handleConvert}
                disabled={converter.status === 'uploading' || converter.status === 'converting'}
                className="w-full"
              >
                {converter.status === 'uploading' || converter.status === 'converting'
                  ? t('common.converting')
                  : t('converter.font.convertFont')}
              </Button>

              {converter.showFeedback && (
                <div className={`text-center ${getStatusColor()}`}>
                  <p className="font-medium">{getStatusText()}</p>
                  {converter.isUploading ? (
                    <div className="mt-2">
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
                      <p className="text-sm mt-1">{converter.uploadProgress}%</p>
                    </div>
                  ) : converter.progress ? (
                    <div className="mt-2">
                      <div
                        {...converter.getProgressAriaAttributes()}
                        className="w-full bg-gray-200 rounded-full h-2"
                      >
                        <div
                          className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${converter.progress.progress}%` }}
                          aria-hidden="true"
                        />
                      </div>
                      <p className="text-sm mt-1">{converter.progress.progress}%</p>
                    </div>
                  ) : null}
                </div>
              )}

              {converter.downloadUrl && converter.status === 'completed' && !window.electron?.isElectron && (
                <div className="text-center">
                  <Button onClick={converter.handleDownload} className="mx-auto">
                    {t('converter.font.download')}
                  </Button>
                </div>
              )}
            </>
          )}
        </div>
      </Card>
    </div>
  );
};
