import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { DropZone } from '../FileUpload/DropZone';
import { Button } from '../Common/Button';
import { Card } from '../Common/Card';
import { fontAPI } from '../../services/api';
import { ConversionStatus } from '../../types/conversion';
import { useWebSocket } from '../../hooks/useWebSocket';

const FONT_FORMATS = ['ttf', 'otf', 'woff', 'woff2'];

export const FontConverter: React.FC = () => {
  const { t } = useTranslation();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [outputFormat, setOutputFormat] = useState<string>('woff2');
  const [subsetText, setSubsetText] = useState<string>('');
  const [optimize, setOptimize] = useState<boolean>(true);
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
      console.error('Failed to select output directory:', err);
    }
  };

  const handleConvert = async () => {
    if (!selectedFile) return;

    setStatus('uploading');
    setError(null);
    setShowFeedback(true);

    try {
      const response = await fontAPI.convert(selectedFile, {
        outputFormat,
        subsetText: subsetText || undefined,
        optimize,
      });

      setSessionId(response.session_id);
      setStatus(response.status);

      if (response.download_url) {
        setDownloadUrl(response.download_url);

        // Auto-download for Electron app
        if (window.electron?.downloadFile) {
          const filename = customFilename || `${selectedFile.name.split('.')[0]}.${outputFormat}`;
          await window.electron.downloadFile(
            response.download_url,
            filename,
            outputDirectory || undefined
          );
        }
      }

      if (response.error) {
        setError(response.error);
        setStatus('failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Conversion failed');
      setStatus('failed');
    }
  };

  const getStatusColor = () => {
    switch (status) {
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
    if (progress?.message) return progress.message;

    switch (status) {
      case 'uploading':
        return 'Uploading file...';
      case 'converting':
        return 'Converting font...';
      case 'completed':
        return 'Conversion completed!';
      case 'failed':
        return error || 'Conversion failed';
      default:
        return 'Ready to convert';
    }
  };

  return (
    <div className="space-y-6">
      {/* Information Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-blue-900 mb-2">{t('converter.font.title')}</h3>
        <p className="text-sm text-blue-800">
          Convert between font formats for web and desktop use.
        </p>
        <ul className="mt-2 text-sm text-blue-700 list-disc list-inside space-y-1">
          <li><strong>TTF</strong> (TrueType): Most compatible desktop format</li>
          <li><strong>OTF</strong> (OpenType): Advanced features, better for complex typography</li>
          <li><strong>WOFF</strong>: Web Open Font Format, optimized for web use</li>
          <li><strong>WOFF2</strong>: Better compression, modern browsers only</li>
        </ul>
      </div>

      <Card>
        <div className="space-y-6">
          {/* File Upload */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <DropZone
              onFileSelect={handleFileSelect}
              acceptedFormats={FONT_FORMATS}
              isDraggingOver={isDraggingOver}
            />
          </div>

          {selectedFile && (
            <>
              {/* Selected File Info */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Selected file:</p>
                <p className="font-medium">{selectedFile.name}</p>
                <p className="text-sm text-gray-500">
                  {(selectedFile.size / 1024).toFixed(2)} KB
                </p>
              </div>

              {/* Output Format Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Output Format
                </label>
                <select
                  value={outputFormat}
                  onChange={(e) => setOutputFormat(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  {FONT_FORMATS.map((format) => (
                    <option key={format} value={format}>
                      {format.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              {/* Advanced Options */}
              <div className="border-t pt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Advanced Options</h4>

                {/* Subset Text */}
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Subset Text (Optional)
                  </label>
                  <input
                    type="text"
                    value={subsetText}
                    onChange={(e) => setSubsetText(e.target.value)}
                    placeholder="e.g., ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Include only these characters to reduce file size
                  </p>
                </div>

                {/* Optimize Checkbox */}
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="optimize"
                    checked={optimize}
                    onChange={(e) => setOptimize(e.target.checked)}
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  />
                  <label htmlFor="optimize" className="ml-2 block text-sm text-gray-700">
                    Optimize font (remove unnecessary data)
                  </label>
                </div>
              </div>

              {/* Custom Filename (Electron Only) */}
              {window.electron && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Custom Filename (optional)
                  </label>
                  <input
                    type="text"
                    value={customFilename}
                    onChange={(e) => setCustomFilename(e.target.value)}
                    placeholder={`${selectedFile.name.split('.')[0]}.${outputFormat}`}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  />
                </div>
              )}

              {/* Output Directory (Electron Only) */}
              {window.electron && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Output Directory
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={outputDirectory || 'Default Downloads folder'}
                      readOnly
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg bg-gray-50"
                    />
                    <Button onClick={handleSelectOutputDirectory} variant="secondary">
                      Browse
                    </Button>
                  </div>
                </div>
              )}

              {/* Convert Button */}
              <Button
                onClick={handleConvert}
                disabled={status === 'uploading' || status === 'converting'}
                className="w-full"
              >
                {status === 'uploading' || status === 'converting' ? 'Converting...' : 'Convert Font'}
              </Button>

              {/* Status/Feedback */}
              {showFeedback && (
                <div className={`text-center ${getStatusColor()}`}>
                  <p className="font-medium">{getStatusText()}</p>
                  {progress && (
                    <div className="mt-2">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${progress.progress}%` }}
                        />
                      </div>
                      <p className="text-sm mt-1">{progress.progress}%</p>
                    </div>
                  )}
                </div>
              )}

              {/* Download Link (Web Only) */}
              {downloadUrl && status === 'completed' && !window.electron && (
                <div className="text-center">
                  <a
                    href={downloadUrl}
                    download
                    className="inline-block px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    Download Converted Font
                  </a>
                </div>
              )}
            </>
          )}
        </div>
      </Card>
    </div>
  );
};
