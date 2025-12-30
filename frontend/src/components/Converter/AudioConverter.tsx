import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { DropZone } from '../FileUpload/DropZone';
import { Button } from '../Common/Button';
import { Card } from '../Common/Card';
import { audioAPI } from '../../services/api';
import { useConverter } from '../../hooks/useConverter';

const AUDIO_FORMATS = ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'wma', 'opus', 'alac', 'ape', 'mka'];

const BITRATES = [
  { value: '64k', label: '64 kbps (Low)' },
  { value: '128k', label: '128 kbps (Standard)' },
  { value: '192k', label: '192 kbps (Good)' },
  { value: '256k', label: '256 kbps (High)' },
  { value: '320k', label: '320 kbps (Highest)' },
];

const SAMPLE_RATES = [
  { value: null, label: 'Original' },
  { value: 22050, label: '22.05 kHz' },
  { value: 44100, label: '44.1 kHz (CD Quality)' },
  { value: 48000, label: '48 kHz (Studio)' },
  { value: 96000, label: '96 kHz (Hi-Res)' },
];

const CHANNEL_OPTIONS = [
  { value: null, label: 'Original' },
  { value: 1, label: 'Mono' },
  { value: 2, label: 'Stereo' },
];

export const AudioConverter: React.FC = () => {
  const { t } = useTranslation();
  const [bitrate, setBitrate] = useState<string>('192k');
  const [sampleRate, setSampleRate] = useState<number | null>(null);
  const [channels, setChannels] = useState<number | null>(null);

  const converter = useConverter({ defaultOutputFormat: 'mp3' });

  const handleConvert = async () => {
    const options: any = { bitrate };

    if (sampleRate !== null) {
      options.sampleRate = sampleRate;
    }

    if (channels !== null) {
      options.channels = channels;
    }

    await converter.handleConvert(audioAPI, options);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024 * 1024) {
      return (bytes / 1024).toFixed(2) + ' KB';
    }
    return (bytes / 1024 / 1024).toFixed(2) + ' MB';
  };

  const isLosslessFormat = (format: string) => {
    return ['flac', 'wav'].includes(format);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Card>
        <h2 className="text-2xl font-bold text-gray-800 mb-6">{t('converter.audio.title')}</h2>

        {!converter.selectedFile ? (
          <DropZone
            onFileSelect={converter.handleFileSelect}
            acceptedFormats={AUDIO_FORMATS}
            fileType="audio"
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
                <span className="font-medium">{t('common.size')}:</span> {formatFileSize(converter.selectedFile.size)}
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
                  {AUDIO_FORMATS.map((format) => (
                    <option key={format} value={format}>
                      {format.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('converter.audio.bitrateLabel')}
                </label>
                <select
                  value={bitrate}
                  onChange={(e) => setBitrate(e.target.value)}
                  className="input"
                  disabled={converter.status === 'converting' || isLosslessFormat(converter.outputFormat)}
                >
                  {BITRATES.map((b) => (
                    <option key={b.value} value={b.value}>
                      {b.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('converter.audio.sampleRateLabel')}
                </label>
                <select
                  value={sampleRate?.toString() || ''}
                  onChange={(e) => setSampleRate(e.target.value ? Number(e.target.value) : null)}
                  className="input"
                  disabled={converter.status === 'converting'}
                >
                  {SAMPLE_RATES.map((sr) => (
                    <option key={sr.label} value={sr.value?.toString() || ''}>
                      {sr.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('converter.audio.channelsLabel')}
                </label>
                <select
                  value={channels?.toString() || ''}
                  onChange={(e) => setChannels(e.target.value ? Number(e.target.value) : null)}
                  className="input"
                  disabled={converter.status === 'converting'}
                >
                  {CHANNEL_OPTIONS.map((ch) => (
                    <option key={ch.label} value={ch.value?.toString() || ''}>
                      {ch.label}
                    </option>
                  ))}
                </select>
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
                    {t('converter.audio.convertAudio')}
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
