import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { DropZone } from '../FileUpload/DropZone';
import { Button } from '../Common/Button';
import { Card } from '../Common/Card';
import { subtitleAPI } from '../../services/api';
import { ConversionStatus } from '../../types/conversion';
import { useWebSocket } from '../../hooks/useWebSocket';

const SUBTITLE_FORMATS = ['srt', 'vtt', 'ass', 'ssa', 'sub'];

const ENCODINGS = [
  { value: 'utf-8', label: 'UTF-8 (Default)' },
  { value: 'utf-16', label: 'UTF-16' },
  { value: 'latin-1', label: 'Latin-1' },
  { value: 'ascii', label: 'ASCII' },
];

const FPS_PRESETS = [
  { value: 23.976, label: '23.976 (Film)' },
  { value: 24, label: '24 (Cinema)' },
  { value: 25, label: '25 (PAL)' },
  { value: 29.97, label: '29.97 (NTSC)' },
  { value: 30, label: '30' },
  { value: 60, label: '60' },
];

export const SubtitleConverter: React.FC = () => {
  const { t } = useTranslation();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [outputFormat, setOutputFormat] = useState<string>('srt');
  const [encoding, setEncoding] = useState<string>('utf-8');
  const [fps, setFps] = useState<number>(23.976);
  const [keepHtmlTags, setKeepHtmlTags] = useState<boolean>(false);
  const [timingOffset, setTimingOffset] = useState<number>(0);
  const [adjustTimingMode, setAdjustTimingMode] = useState<boolean>(false);
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

      let response;

      if (adjustTimingMode) {
        // Adjust timing only
        response = await subtitleAPI.adjustTiming(selectedFile, timingOffset);
      } else {
        // Format conversion
        response = await subtitleAPI.convert(selectedFile, {
          outputFormat,
          encoding,
          fps,
          keepHtmlTags,
        });
      }

      setSessionId(response.session_id);

      if (response.status === 'completed' && response.download_url) {
        setDownloadUrl(response.download_url);
        setStatus('completed');
        setShowFeedback(true);

        // Auto-download if output directory is selected
        if (outputDirectory && window.electron?.downloadFile && response.download_url) {
          setTimeout(async () => {
            await autoDownload(response.download_url!);
          }, 200);
        }
      } else if (response.status === 'failed') {
        setError(response.error || 'Conversion failed');
        setStatus('failed');
      }
    } catch (err: any) {
      console.error('Subtitle conversion error:', err);
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

      const result = await window.electron.downloadFile({
        url: `http://localhost:8000${url}`,
        directory: outputDirectory,
        filename: filename
      });

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

    if (outputDirectory && window.electron?.downloadFile) {
      try {
        const urlParts = downloadUrl.split('/');
        const defaultFilename = urlParts[urlParts.length - 1] || `converted.${outputFormat}`;
        const filename = customFilename ? `${customFilename}.${outputFormat}` : defaultFilename;

        const result = await window.electron.downloadFile({
          url: `http://localhost:8000${downloadUrl}`,
          directory: outputDirectory,
          filename: filename
        });

        if (result.success) {
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

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Card>
        <h2 className="text-2xl font-bold text-gray-800 mb-6">{t('converter.subtitle.title')}</h2>

        <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>Supported formats:</strong> SRT (SubRip), VTT (WebVTT), ASS/SSA (Advanced SubStation Alpha), SUB (MicroDVD)
          </p>
        </div>

        {!selectedFile ? (
          <DropZone
            onFileSelect={handleFileSelect}
            acceptedFormats={SUBTITLE_FORMATS}
            fileType="subtitle"
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
                  <p className="text-primary-600 font-semibold text-lg">Drop to replace file</p>
                </div>
              </div>
            )}

            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">
                <span className="font-medium">File:</span> {selectedFile.name}
              </p>
              <p className="text-sm text-gray-600">
                <span className="font-medium">Size:</span>{' '}
                {(selectedFile.size / 1024).toFixed(2)} KB
              </p>
              <p className="text-xs text-gray-500 mt-2">
                💡 {t('dropzone.dragActive')}
              </p>
            </div>

            <div className="border-b border-gray-200">
              <div className="flex space-x-4">
                <button
                  className={`py-2 px-4 font-medium border-b-2 transition-colors ${
                    !adjustTimingMode
                      ? 'border-primary-600 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                  onClick={() => setAdjustTimingMode(false)}
                >
                  Convert Format
                </button>
                <button
                  className={`py-2 px-4 font-medium border-b-2 transition-colors ${
                    adjustTimingMode
                      ? 'border-primary-600 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                  onClick={() => setAdjustTimingMode(true)}
                >
                  Adjust Timing
                </button>
              </div>
            </div>

            {!adjustTimingMode ? (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Output Format
                    </label>
                    <select
                      value={outputFormat}
                      onChange={(e) => setOutputFormat(e.target.value)}
                      className="input"
                      disabled={status === 'converting'}
                    >
                      {SUBTITLE_FORMATS.map((format) => (
                        <option key={format} value={format}>
                          {format.toUpperCase()}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Encoding
                    </label>
                    <select
                      value={encoding}
                      onChange={(e) => setEncoding(e.target.value)}
                      className="input"
                      disabled={status === 'converting'}
                    >
                      {ENCODINGS.map((enc) => (
                        <option key={enc.value} value={enc.value}>
                          {enc.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {outputFormat === 'sub' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Frame Rate (FPS)
                      </label>
                      <select
                        value={fps}
                        onChange={(e) => setFps(Number(e.target.value))}
                        className="input"
                        disabled={status === 'converting'}
                      >
                        {FPS_PRESETS.map((preset) => (
                          <option key={preset.value} value={preset.value}>
                            {preset.label}
                          </option>
                        ))}
                      </select>
                      <p className="text-xs text-gray-500 mt-1">
                        Required for SUB format timing
                      </p>
                    </div>
                  )}

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      HTML Tags
                    </label>
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={keepHtmlTags}
                        onChange={(e) => setKeepHtmlTags(e.target.checked)}
                        className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                        disabled={status === 'converting'}
                      />
                      <span className="text-sm text-gray-600">
                        Keep HTML formatting tags
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      Preserve &lt;b&gt;, &lt;i&gt;, etc.
                    </p>
                  </div>
                </div>
              </>
            ) : (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Time Offset (milliseconds)
                  </label>
                  <input
                    type="number"
                    value={timingOffset}
                    onChange={(e) => setTimingOffset(Number(e.target.value))}
                    placeholder="e.g., 2000 (delay) or -2000 (advance)"
                    className="input w-full"
                    disabled={status === 'converting'}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Positive = delay subtitles, Negative = advance subtitles
                  </p>
                  <p className="text-xs text-gray-500">
                    Example: +2000ms delays by 2 seconds, -1500ms advances by 1.5 seconds
                  </p>
                </div>
              </>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Custom Filename (Optional)
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
                  Output Directory (Optional)
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
                    Browse
                  </Button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  💡 When set, files will be saved directly to this directory
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
                {adjustTimingMode
                  ? `Subtitle timing adjusted by ${timingOffset}ms successfully!`
                  : 'Subtitle conversion completed successfully!'}
              </div>
            )}

            <div className="flex gap-4">
              {status === 'idle' || status === 'failed' ? (
                <>
                  <Button onClick={handleConvert} className="flex-1">
                    {adjustTimingMode ? 'Adjust Timing' : 'Convert Subtitle'}
                  </Button>
                  <Button onClick={handleReset} variant="secondary">
                    Reset
                  </Button>
                </>
              ) : status === 'converting' ? (
                <Button disabled loading className="flex-1">
                  {adjustTimingMode ? 'Adjusting...' : 'Converting...'}
                </Button>
              ) : status === 'completed' ? (
                <>
                  <Button onClick={handleDownload} className="flex-1">
                    Download
                  </Button>
                  <Button onClick={handleReset} variant="secondary">
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
