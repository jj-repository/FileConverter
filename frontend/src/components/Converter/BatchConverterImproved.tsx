import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { BatchDropZone } from '../FileUpload/BatchDropZone';
import { Button } from '../Common/Button';
import { Card } from '../Common/Card';
import { batchAPI, BatchConversionResult } from '../../services/api';
import { ConversionStatus } from '../../types/conversion';
import { useWebSocket } from '../../hooks/useWebSocket';

const ALL_FORMATS = ['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp', 'tiff', 'ico', 'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv', 'mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'wma', 'txt', 'pdf', 'docx', 'md', 'html', 'rtf'];

export const BatchConverter: React.FC = () => {
  const { t } = useTranslation();
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [outputFormat, setOutputFormat] = useState<string>('pdf');
  const [outputDirectory, setOutputDirectory] = useState<string | null>(null);
  const [status, setStatus] = useState<ConversionStatus>('idle');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [results, setResults] = useState<BatchConversionResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [_zipUrl, setZipUrl] = useState<string | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);

  const { progress } = useWebSocket(sessionId);

  useEffect(() => {
    if (progress) {
      setStatus(progress.status);
      setShowFeedback(true);
    }
  }, [progress]);

  const handleFilesSelect = (files: File[]) => {
    setSelectedFiles(files);
    setStatus('idle');
    setError(null);
    setResults([]);
    setZipUrl(null);
    setShowFeedback(false);
  };

  const handleSelectFolder = async () => {
    if (!window.electron?.selectFolderFiles) {
      alert('Folder selection is only available in the desktop app');
      return;
    }

    try {
      const filePaths = await window.electron.selectFolderFiles();
      if (filePaths.length > 0) {
        // Convert file paths to File objects
        const files = await Promise.all(
          filePaths.map(async (filePath) => {
            const response = await fetch(`file://${filePath}`);
            const blob = await response.blob();
            const fileName = filePath.split('/').pop() || filePath.split('\\').pop() || 'file';
            return new File([blob], fileName);
          })
        );
        handleFilesSelect(files);
      }
    } catch (err) {
      console.error('Error selecting folder:', err);
      setError('Failed to load folder files');
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

  const handleRemoveFile = (index: number) => {
    setSelectedFiles(files => files.filter((_, i) => i !== index));
  };

  const handleConvert = async () => {
    if (selectedFiles.length === 0) return;

    try {
      setStatus('converting');
      setError(null);
      setResults([]);
      setShowFeedback(true);

      const response = await batchAPI.convert(selectedFiles, {
        outputFormat,
      });

      setSessionId(response.session_id);
      setResults(response.results);

      if (response.successful > 0) {
        setStatus('completed');
      } else {
        setStatus('failed');
        setError('All conversions failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Batch conversion failed');
      setStatus('failed');
      setShowFeedback(true);
    }
  };

  const handleDownloadAll = async () => {
    if (!sessionId || results.length === 0) return;

    try {
      const successfulFiles = results
        .filter(r => r.success && r.output_file)
        .map(r => r.output_file!);

      if (successfulFiles.length === 0) {
        setError('No files to download');
        return;
      }

      const response = await batchAPI.createZip(sessionId, successfulFiles);
      setZipUrl(response.download_url);

      // Automatically trigger download
      window.location.href = response.download_url;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create ZIP file');
    }
  };

  const handleDownloadSingle = (downloadUrl: string) => {
    window.location.href = downloadUrl;
  };

  const handleReset = () => {
    setSelectedFiles([]);
    setStatus('idle');
    setResults([]);
    setError(null);
    setSessionId(null);
    setZipUrl(null);
    setShowFeedback(false);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024 * 1024) {
      return (bytes / 1024).toFixed(2) + ' KB';
    }
    return (bytes / 1024 / 1024).toFixed(2) + ' MB';
  };

  const getFileIcon = (filename: string): string => {
    const ext = filename.split('.').pop()?.toLowerCase() || '';
    if (['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp', 'tiff', 'ico'].includes(ext)) return '🖼️';
    if (['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv'].includes(ext)) return '🎥';
    if (['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'wma'].includes(ext)) return '🎵';
    if (['txt', 'pdf', 'docx', 'md', 'html', 'rtf'].includes(ext)) return '📄';
    return '📁';
  };

  const totalFileSize = selectedFiles.reduce((sum, file) => sum + file.size, 0);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Card>
        <h2 className="text-2xl font-bold text-gray-800 mb-6">Batch Converter</h2>

        {selectedFiles.length === 0 ? (
          <div className="space-y-4">
            <BatchDropZone
              onFilesSelect={handleFilesSelect}
              acceptedFormats={ALL_FORMATS}
              maxFiles={100}
            />

            {window.electron?.isElectron && (
              <div className="flex gap-4">
                <Button onClick={handleSelectFolder} variant="secondary" className="flex-1">
                  📁 Select Entire Folder
                </Button>
              </div>
            )}

            {window.electron?.isElectron && (
              <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
                <p className="text-sm text-blue-800">
                  💡 <strong>Desktop Features:</strong> You can select an entire folder or set a custom output location
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="flex justify-between items-center mb-3">
                <div>
                  <p className="font-medium text-gray-700">
                    Selected Files ({selectedFiles.length})
                  </p>
                  <p className="text-sm text-gray-500">
                    Total size: {formatFileSize(totalFileSize)}
                  </p>
                </div>
                <Button onClick={handleReset} variant="secondary" className="text-sm">
                  Clear All
                </Button>
              </div>

              <div className="max-h-64 overflow-y-auto space-y-2">
                {selectedFiles.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between bg-white p-3 rounded border border-gray-200"
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <span className="text-2xl">{getFileIcon(file.name)}</span>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-gray-800 truncate">{file.name}</p>
                        <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                      </div>
                    </div>
                    {status === 'idle' && (
                      <button
                        onClick={() => handleRemoveFile(index)}
                        className="text-red-600 hover:text-red-700 p-1"
                        aria-label={`Remove ${file.name} from batch`}
                      >
                        ✕
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4">
              <div>
                <label htmlFor="batch-output-format" className="block text-sm font-medium text-gray-700 mb-2">
                  Output Format (All files will be converted to this format)
                </label>
                <select
                  id="batch-output-format"
                  value={outputFormat}
                  onChange={(e) => setOutputFormat(e.target.value)}
                  className="input"
                  disabled={status === 'converting'}
                  aria-label="Select output format for batch conversion"
                >
                  <optgroup label="Image">
                    <option value="png">PNG</option>
                    <option value="jpg">JPG</option>
                    <option value="webp">WEBP</option>
                  </optgroup>
                  <optgroup label="Video">
                    <option value="mp4">MP4</option>
                    <option value="webm">WEBM</option>
                  </optgroup>
                  <optgroup label="Audio">
                    <option value="mp3">MP3</option>
                    <option value="wav">WAV</option>
                  </optgroup>
                  <optgroup label="Document">
                    <option value="pdf">PDF</option>
                    <option value="docx">DOCX</option>
                    <option value="txt">TXT</option>
                  </optgroup>
                </select>
              </div>

              {window.electron?.isElectron && (
                <div>
                  <label htmlFor="batch-output-directory" className="block text-sm font-medium text-gray-700 mb-2">
                    Output Directory (Optional)
                  </label>
                  <div className="flex gap-2">
                    <input
                      id="batch-output-directory"
                      type="text"
                      value={outputDirectory || t('common.defaultDownloads')}
                      readOnly
                      className="input flex-1"
                      disabled={status === 'converting'}
                      aria-label="Output directory path"
                    />
                    <Button
                      onClick={handleSelectOutputDirectory}
                      variant="secondary"
                      disabled={status === 'converting'}
                      aria-label="Browse for output directory"
                    >
                      Browse
                    </Button>
                  </div>
                </div>
              )}
            </div>

            {progress && status === 'converting' && showFeedback && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm text-gray-600">
                  <span>{progress.message}</span>
                  <span>{progress.progress.toFixed(0)}%</span>
                </div>
                <div
                  role="progressbar"
                  aria-valuenow={progress.progress}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label={progress.message || 'Batch conversion progress'}
                  className="w-full bg-gray-200 rounded-full h-3"
                >
                  <div
                    className="bg-primary-600 h-3 rounded-full transition-all duration-300"
                    style={{ width: `${progress.progress}%` }}
                    aria-hidden="true"
                  />
                </div>
                <p className="text-xs text-gray-500 text-center">
                  Processing files in parallel...
                </p>
              </div>
            )}

            {error && showFeedback && (
              <div
                role="alert"
                aria-live="assertive"
                className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg"
              >
                <p className="font-medium">Conversion Error</p>
                <p className="text-sm mt-1">{error}</p>
              </div>
            )}

            {status === 'completed' && results.length > 0 && showFeedback && (
              <div className="space-y-3">
                <div
                  role="status"
                  aria-live="polite"
                  className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg"
                >
                  <p className="font-medium">Batch conversion completed!</p>
                  <p className="text-sm mt-1">
                    {results.filter(r => r.success).length} of {results.length} files converted successfully
                  </p>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="font-medium text-gray-700 mb-3">Results</h3>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {results.map((result, index) => (
                      <div
                        key={index}
                        className={`flex items-center justify-between p-3 rounded border ${
                          result.success
                            ? 'bg-white border-green-200'
                            : 'bg-red-50 border-red-200'
                        }`}
                      >
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-800 truncate">
                            {result.success ? '✓' : '✗'} {result.filename}
                          </p>
                          {result.error && (
                            <p className="text-xs text-red-600 mt-1">{result.error}</p>
                          )}
                        </div>
                        {result.success && result.download_url && (
                          <Button
                            onClick={() => handleDownloadSingle(result.download_url!)}
                            variant="secondary"
                            className="text-sm ml-2"
                          >
                            Download
                          </Button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            <div className="flex gap-4">
              {status === 'idle' ? (
                <Button onClick={handleConvert} className="flex-1">
                  Convert All {selectedFiles.length} Files
                </Button>
              ) : status === 'converting' ? (
                <Button disabled loading className="flex-1">
                  Converting... ({progress?.progress.toFixed(0) || 0}%)
                </Button>
              ) : status === 'completed' ? (
                <>
                  <Button onClick={handleDownloadAll} className="flex-1">
                    Download All as ZIP
                  </Button>
                  <Button onClick={handleReset} variant="secondary">
                    Convert More
                  </Button>
                </>
              ) : status === 'failed' ? (
                <>
                  <Button onClick={handleConvert} className="flex-1">
                    Retry
                  </Button>
                  <Button onClick={handleReset} variant="secondary">
                    Reset
                  </Button>
                </>
              ) : null}
            </div>
          </div>
        )}
      </Card>

      <Card className="bg-blue-50 border border-blue-200">
        <h3 className="font-semibold text-blue-900 mb-2">Batch Conversion Tips</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Upload up to <strong>100 files</strong> at once (increased from 20)</li>
          <li>• All files will be converted to the same output format</li>
          <li>• Files can be of different types (images, videos, audio, documents)</li>
          <li>• Files are processed in parallel for faster conversion</li>
          <li>• Download individual files or all files as a ZIP archive</li>
          <li>• <strong>Desktop app:</strong> Select entire folders or set custom output location</li>
        </ul>
      </Card>
    </div>
  );
};
