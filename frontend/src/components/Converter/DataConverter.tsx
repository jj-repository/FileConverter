import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { DropZone } from '../FileUpload/DropZone';
import { Button } from '../Common/Button';
import { Card } from '../Common/Card';
import { dataAPI } from '../../services/api';
import { useConverter } from '../../hooks/useConverter';

const DATA_FORMATS = ['csv', 'json', 'xml', 'yaml', 'yml', 'toml', 'ini', 'jsonl'];

const ENCODINGS = [
  { value: 'utf-8', label: 'UTF-8 (Default)' },
  { value: 'utf-16', label: 'UTF-16' },
  { value: 'ascii', label: 'ASCII' },
  { value: 'latin-1', label: 'Latin-1' },
];

const DELIMITERS = [
  { value: ',', label: 'Comma (,)' },
  { value: ';', label: 'Semicolon (;)' },
  { value: '\t', label: 'Tab' },
  { value: '|', label: 'Pipe (|)' },
];

export const DataConverter: React.FC = () => {
  const { t } = useTranslation();
  const [encoding, setEncoding] = useState<string>('utf-8');
  const [delimiter, setDelimiter] = useState<string>(',');
  const [pretty, setPretty] = useState<boolean>(true);

  const converter = useConverter({ defaultOutputFormat: 'csv' });

  const handleConvert = async () => {
    await converter.handleConvert(dataAPI, { encoding, delimiter, pretty });
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Card>
        <h2 className="text-2xl font-bold text-gray-800 mb-6">{t('converter.data.title')}</h2>

        {!converter.selectedFile ? (
          <DropZone
            onFileSelect={converter.handleFileSelect}
            acceptedFormats={DATA_FORMATS}
            fileType="data"
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
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('common.outputFormat')}
                </label>
                <select
                  value={converter.outputFormat}
                  onChange={(e) => converter.setOutputFormat(e.target.value)}
                  className="input"
                  disabled={converter.status === 'converting'}
                >
                  {DATA_FORMATS.map((format) => (
                    <option key={format} value={format}>
                      {format.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('common.encoding')}
                </label>
                <select
                  value={encoding}
                  onChange={(e) => setEncoding(e.target.value)}
                  className="input"
                  disabled={converter.status === 'converting'}
                >
                  {ENCODINGS.map((enc) => (
                    <option key={enc.value} value={enc.value}>
                      {enc.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('converter.data.delimiterLabel')}
                </label>
                <select
                  value={delimiter}
                  onChange={(e) => setDelimiter(e.target.value)}
                  className="input"
                  disabled={converter.status === 'converting'}
                >
                  {DELIMITERS.map((delim) => (
                    <option key={delim.value} value={delim.value}>
                      {delim.label}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  {t('converter.data.delimiterHint')}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('converter.data.prettyPrint')}
                </label>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={pretty}
                    onChange={(e) => setPretty(e.target.checked)}
                    className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                    disabled={converter.status === 'converting'}
                  />
                  <span className="text-sm text-gray-600">
                    {t('converter.data.prettyPrint')}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {t('converter.data.prettyHint')}
                </p>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('common.customFilename')}
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
                  {t('common.outputDirectory')}
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
                    {t('common.browse')}
                  </Button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  💡 {t('common.outputDirectoryHint')}
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
                {t('messages.conversionSuccess')}
              </div>
            )}

            <div className="flex gap-4">
              {converter.status === 'idle' || converter.status === 'failed' ? (
                <>
                  <Button onClick={handleConvert} className="flex-1">
                    {t('converter.data.convertData')}
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
