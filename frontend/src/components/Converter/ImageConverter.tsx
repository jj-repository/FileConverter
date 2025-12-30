import React, { useState, useEffect } from 'react';
import { DropZone } from '../FileUpload/DropZone';
import { Button } from '../Common/Button';
import { Card } from '../Common/Card';
import { imageAPI } from '../../services/api';
import { ConversionStatus } from '../../types/conversion';
import { useWebSocket } from '../../hooks/useWebSocket';

const IMAGE_FORMATS = ['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp', 'tiff', 'ico', 'heic', 'heif', 'svg'];

export const ImageConverter: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [outputFormat, setOutputFormat] = useState<string>('png');
  const [quality, setQuality] = useState<number>(95);
  const [outputDirectory, setOutputDirectory] = useState<string | null>(null);
  const [status, setStatus] = useState<ConversionStatus>('idle');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [isDraggingOver, setIsDraggingOver] = useState(false);
  const [customFilename, setCustomFilename] = useState<string>('');

  const { progress } = useWebSocket(sessionId);

  useEffect(() => {
    if (selectedFile) {
      const objectUrl = URL.createObjectURL(selectedFile);
      setPreview(objectUrl);
      return () => URL.revokeObjectURL(objectUrl);
    }
  }, [selectedFile]);

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

      const response = await imageAPI.convert(selectedFile, {
        outputFormat,
        quality,
      });

      setSessionId(response.session_id);

      console.log('Image conversion response:', response);

      if (response.status === 'completed' && response.download_url) {
        console.log('Image conversion completed, download URL:', response.download_url);
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
      }
    } catch (err: any) {
      console.error('Image conversion error:', err);
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
    setPreview(null);
    setShowFeedback(false);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Card>
        <h2 className="text-2xl font-bold text-gray-800 mb-6">Image Converter</h2>

        {!selectedFile ? (
          <DropZone
            onFileSelect={handleFileSelect}
            acceptedFormats={IMAGE_FORMATS}
            fileType="image"
          />
        ) : (
          <div
            className="space-y-6 relative"
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            {/* Drag and drop overlay */}
            {isDraggingOver && (
              <div className="absolute inset-0 z-10 bg-primary-500 bg-opacity-20 border-4 border-primary-500 border-dashed rounded-lg flex items-center justify-center">
                <div className="bg-white px-6 py-4 rounded-lg shadow-lg">
                  <p className="text-primary-600 font-semibold text-lg">Drop to replace file</p>
                </div>
              </div>
            )}

            {preview && (
              <div className="flex justify-center">
                <img
                  src={preview}
                  alt="Preview"
                  className="max-h-64 rounded-lg shadow-md object-contain"
                />
              </div>
            )}

            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">
                <span className="font-medium">File:</span> {selectedFile.name}
              </p>
              <p className="text-sm text-gray-600">
                <span className="font-medium">Size:</span>{' '}
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
              <p className="text-xs text-gray-500 mt-2">
                💡 Drag and drop another file here to replace
              </p>
            </div>

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
                  {IMAGE_FORMATS.map((format) => (
                    <option key={format} value={format}>
                      {format.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Quality ({quality}%)
                </label>
                <input
                  type="range"
                  min="1"
                  max="100"
                  value={quality}
                  onChange={(e) => setQuality(Number(e.target.value))}
                  className="w-full"
                  disabled={status === 'converting'}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Custom Filename (Optional)
              </label>
              <input
                type="text"
                value={customFilename}
                onChange={(e) => setCustomFilename(e.target.value)}
                placeholder="Leave empty for default name"
                className="input w-full"
                disabled={status === 'converting'}
              />
              <p className="text-xs text-gray-500 mt-1">
                File extension will be added automatically
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
                    value={outputDirectory || 'Default (Downloads)'}
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
                  💡 When set, files will be saved directly to this directory. Otherwise, uses browser download.
                </p>
              </div>
            )}

            {status === 'converting' && showFeedback && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm text-gray-600">
                  <span>{progress?.message || 'Processing...'}</span>
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
                Conversion completed successfully!
              </div>
            )}

            <div className="flex gap-4">
              {status === 'idle' || status === 'failed' ? (
                <>
                  <Button onClick={handleConvert} className="flex-1">
                    Convert Image
                  </Button>
                  <Button onClick={handleReset} variant="secondary">
                    Reset
                  </Button>
                </>
              ) : status === 'converting' ? (
                <Button disabled loading className="flex-1">
                  Converting...
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
