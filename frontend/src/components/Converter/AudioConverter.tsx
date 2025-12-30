import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { DropZone } from '../FileUpload/DropZone';
import { Button } from '../Common/Button';
import { Card } from '../Common/Card';
import { audioAPI } from '../../services/api';
import { ConversionStatus } from '../../types/conversion';
import { useWebSocket } from '../../hooks/useWebSocket';

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
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [outputFormat, setOutputFormat] = useState<string>('mp3');
  const [bitrate, setBitrate] = useState<string>('192k');
  const [sampleRate, setSampleRate] = useState<number | null>(null);
  const [channels, setChannels] = useState<number | null>(null);
  const [outputDirectory, setOutputDirectory] = useState<string | null>(null);
  const [status, setStatus] = useState<ConversionStatus>('idle');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [isDraggingOver, setIsDraggingOver] = useState(false);
  const [customFilename, setCustomFilename] = useState<string>('');

  const { progress } = useWebSocket(sessionId);

  useEffect(() => {
    if (progress) {
      setStatus(progress.status);
      setShowFeedback(true);
    }
  }, [progress]);

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setStatus('idle');
    setError(null);
    setDownloadUrl(null);
    setShowFeedback(false);
    setIsDraggingOver(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleSelectOutputDirectory = async () => {
    if (!window.electron?.selectOutputDirectory) {
      alert('Output directory selection is only available in the desktop app');
      return;
    }

    try {
      const directory = await window.electron.selectOutputDirectory();
      if (directory) {
        setOutputDirectory(directory);
      }
    } catch (err) {
      console.error('Error selecting output directory:', err);
      setError('Failed to select output directory');
    }
  };

  const handleConvert = async () => {
    if (!selectedFile) return;

    try {
      setStatus('converting');
      setError(null);
      setShowFeedback(true);
      setDownloadUrl(null);

      const options: any = {
        outputFormat,
        bitrate,
      };

      if (sampleRate !== null) {
        options.sampleRate = sampleRate;
      }

      if (channels !== null) {
        options.channels = channels;
      }

      console.log('Starting audio conversion...', options);

      const response = await audioAPI.convert(selectedFile, options);

      console.log('Audio conversion response:', response);

      setSessionId(response.session_id);

      if (response.status === 'completed' && response.download_url) {
        console.log('Audio conversion completed, download URL:', response.download_url);
        setDownloadUrl(response.download_url);
        setStatus('completed');
        setShowFeedback(true);

        // Auto-download if output directory is selected
        if (outputDirectory && window.electron?.downloadFile && response.download_url) {
          setTimeout(async () => {
            await autoDownload(response.download_url!);
          }, 200);
        }

        // Force re-render
        setTimeout(() => {
          setStatus('completed');
          setShowFeedback(true);
        }, 100);
      } else if (response.status === 'failed') {
        setError(response.error || 'Conversion failed');
        setStatus('failed');
      } else {
        console.log('Audio conversion in progress, status:', response.status);
      }
    } catch (err: any) {
      console.error('Audio conversion error:', err);
      setError(err.response?.data?.detail || err.message || 'Conversion failed');
      setStatus('failed');
      setShowFeedback(true);
    }
  };

  const autoDownload = async (url: string) => {
    if (!outputDirectory || !window.electron?.downloadFile) return;

    try {
      const urlParts = url.split('/');
      const defaultFilename = urlParts[urlParts.length - 1] || `converted.${outputFormat}`;
      const filename = customFilename ? `${customFilename}.${outputFormat}` : defaultFilename;

      console.log('Auto-downloading to:', outputDirectory, filename);

      const result = await window.electron.downloadFile({
        url: `http://localhost:8000${url}`,
        directory: outputDirectory,
        filename: filename
      });

      console.log('Auto-download result:', result);

      if (result.success) {
        if (window.electron.showItemInFolder) {
          const shouldShow = confirm(`✅ File saved to:\n${result.path}\n\nDo you want to show it in folder?`);
          if (shouldShow) {
            await window.electron.showItemInFolder(result.path);
          }
        }
      }
    } catch (err) {
      console.error('Auto-download error:', err);
      alert(`Failed to save file: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleDownload = async () => {
    if (!downloadUrl) return;

    // If user selected an output directory and we're in Electron, download to that directory
    if (outputDirectory && window.electron?.downloadFile) {
      try {
        // Extract filename from download URL or generate one
        const urlParts = downloadUrl.split('/');
        const defaultFilename = urlParts[urlParts.length - 1] || `converted.${outputFormat}`;
        const filename = customFilename ? `${customFilename}.${outputFormat}` : defaultFilename;

        console.log('Downloading to:', outputDirectory, filename);

        const result = await window.electron.downloadFile({
          url: `http://localhost:8000${downloadUrl}`,
          directory: outputDirectory,
          filename: filename
        });

        console.log('Download result:', result);

        if (result.success) {
          // Show success message and offer to show in folder
          if (window.electron.showItemInFolder) {
            const shouldShow = confirm(`File saved successfully to:\n${result.path}\n\nDo you want to show it in folder?`);
            if (shouldShow) {
              await window.electron.showItemInFolder(result.path);
            }
          } else {
            alert(`File saved successfully to:\n${result.path}`);
          }
        }
      } catch (err) {
        console.error('Download error:', err);
        alert(`Failed to download file: ${err instanceof Error ? err.message : 'Unknown error'}`);
      }
    } else {
      // Fall back to browser download
      window.location.href = downloadUrl;
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setStatus('idle');
    setDownloadUrl(null);
    setError(null);
    setSessionId(null);
    setShowFeedback(false);
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

        {!selectedFile ? (
          <DropZone
            onFileSelect={handleFileSelect}
            acceptedFormats={AUDIO_FORMATS}
            fileType="audio"
          />
        ) : (
          <div
            className="space-y-6 relative"
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            {isDraggingOver && (
              <div className="absolute inset-0 z-10 bg-primary-500 bg-opacity-20 border-4 border-primary-500 border-dashed rounded-lg flex items-center justify-center">
                <div className="bg-white px-6 py-4 rounded-lg shadow-lg">
                  <p className="text-primary-600 font-semibold text-lg">{t('common.dropToReplace')}</p>
                </div>
              </div>
            )}

            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">
                <span className="font-medium">{t('common.file')}:</span> {selectedFile.name}
              </p>
              <p className="text-sm text-gray-600">
                <span className="font-medium">{t('common.size')}:</span> {formatFileSize(selectedFile.size)}
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
                  value={outputFormat}
                  onChange={(e) => setOutputFormat(e.target.value)}
                  className="input"
                  disabled={status === 'converting'}
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
                  disabled={status === 'converting' || isLosslessFormat(outputFormat)}
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
                  disabled={status === 'converting'}
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
                  disabled={status === 'converting'}
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
                value={customFilename}
                onChange={(e) => setCustomFilename(e.target.value)}
                placeholder={t('common.customFilenamePlaceholder')}
                className="input w-full"
                disabled={status === 'converting'}
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
                    value={outputDirectory || t('common.defaultDownloads')}
                    readOnly
                    className="input flex-1"
                    disabled={status === 'converting'}
                  />
                  <Button
                    onClick={handleSelectOutputDirectory}
                    variant="secondary"
                    disabled={status === 'converting'}
                  >
                    {t('common.browse')}
                  </Button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  💡 {t('common.outputDirectoryHint')}
                </p>
              </div>
            )}

            {status === 'converting' && showFeedback && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm text-gray-600">
                  <span>{progress?.message || t('common.processing')}</span>
                  <span>{progress?.progress.toFixed(0) || 0}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${progress?.progress || 0}%` }}
                  />
                </div>
              </div>
            )}

            {error && showFeedback && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            {status === 'completed' && showFeedback && (
              <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
                {t('messages.conversionSuccess')}
              </div>
            )}

            <div className="flex gap-4">
              {status === 'idle' || status === 'failed' ? (
                <>
                  <Button onClick={handleConvert} className="flex-1">
                    {t('converter.audio.convertAudio')}
                  </Button>
                  <Button onClick={handleReset} variant="secondary">
                    {t('common.reset')}
                  </Button>
                </>
              ) : status === 'converting' ? (
                <Button disabled loading className="flex-1">
                  {t('common.converting')}
                </Button>
              ) : status === 'completed' ? (
                <>
                  <Button onClick={handleDownload} className="flex-1" disabled={!downloadUrl}>
                    {t('common.download')}
                  </Button>
                  <Button onClick={handleReset} variant="secondary">
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
