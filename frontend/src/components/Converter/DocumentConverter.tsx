import React, { useState, useEffect } from 'react';
import { DropZone } from '../FileUpload/DropZone';
import { Button } from '../Common/Button';
import { Card } from '../Common/Card';
import { documentAPI } from '../../services/api';
import { ConversionStatus } from '../../types/conversion';
import { useWebSocket } from '../../hooks/useWebSocket';

const DOCUMENT_FORMATS = ['txt', 'pdf', 'docx', 'md', 'html', 'rtf', 'odt'];

export const DocumentConverter: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [outputFormat, setOutputFormat] = useState<string>('pdf');
  const [preserveFormatting, setPreserveFormatting] = useState<boolean>(true);
  const [toc, setToc] = useState<boolean>(false);
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

  const handleConvert = async () => {
    if (!selectedFile) return;

    try {
      setStatus('converting');
      setError(null);
      setShowFeedback(true);

      const options: any = {
        outputFormat,
        preserveFormatting,
        toc,
      };

      const response = await documentAPI.convert(selectedFile, options);

      console.log('Document conversion response:', response);

      setSessionId(response.session_id);

      if (response.status === 'completed' && response.download_url) {
        console.log('Document conversion completed, download URL:', response.download_url);
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
      console.error('Document conversion error:', err);
      setError(err.response?.data?.detail || err.message || 'Conversion failed');
      setStatus('failed');
      setShowFeedback(true);
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
    setShowFeedback(false);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024 * 1024) {
      return (bytes / 1024).toFixed(2) + ' KB';
    }
    return (bytes / 1024 / 1024).toFixed(2) + ' MB';
  };

  const supportsToc = (format: string) => {
    return ['pdf', 'html', 'docx'].includes(format);
  };

  const getFormatDescription = (format: string) => {
    const descriptions: Record<string, string> = {
      txt: 'Plain Text',
      pdf: 'PDF Document',
      docx: 'Microsoft Word',
      md: 'Markdown',
      html: 'HTML Webpage',
      rtf: 'Rich Text Format',
    };
    return descriptions[format] || format.toUpperCase();
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Card>
        <h2 className="text-2xl font-bold text-gray-800 mb-6">Document Converter</h2>

        {!selectedFile ? (
          <DropZone
            onFileSelect={handleFileSelect}
            acceptedFormats={DOCUMENT_FORMATS}
            fileType="document"
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

            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600">
                <span className="font-medium">File:</span> {selectedFile.name}
              </p>
              <p className="text-sm text-gray-600">
                <span className="font-medium">Size:</span> {formatFileSize(selectedFile.size)}
              </p>
              <p className="text-xs text-gray-500 mt-2">
                💡 Drag and drop another file here to replace
              </p>
            </div>

            <div className="space-y-4">
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
                  {DOCUMENT_FORMATS.map((format) => (
                    <option key={format} value={format}>
                      {getFormatDescription(format)}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-3">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="preserveFormatting"
                    checked={preserveFormatting}
                    onChange={(e) => setPreserveFormatting(e.target.checked)}
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    disabled={status === 'converting'}
                  />
                  <label htmlFor="preserveFormatting" className="ml-2 block text-sm text-gray-700">
                    Preserve formatting (keep styles, fonts, and layout)
                  </label>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="toc"
                    checked={toc}
                    onChange={(e) => setToc(e.target.checked)}
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    disabled={status === 'converting' || !supportsToc(outputFormat)}
                  />
                  <label htmlFor="toc" className="ml-2 block text-sm text-gray-700">
                    Add table of contents
                    {!supportsToc(outputFormat) && (
                      <span className="text-xs text-gray-500 ml-2">(Only for PDF, HTML, DOCX)</span>
                    )}
                  </label>
                </div>
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
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-primary-600 h-3 rounded-full transition-all duration-300 flex items-center justify-end px-2"
                    style={{ width: `${progress?.progress || 0}%` }}
                  >
                    {(progress?.progress || 0) > 10 && (
                      <span className="text-xs text-white font-medium">
                        {progress?.progress.toFixed(0) || 0}%
                      </span>
                    )}
                  </div>
                </div>
                <p className="text-xs text-gray-500 text-center">
                  Document conversion is usually fast - most files complete in seconds
                </p>
              </div>
            )}

            {error && showFeedback && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                <p className="font-medium">Conversion Failed</p>
                <p className="text-sm mt-1">{error}</p>
                {error.includes('Pandoc') && (
                  <p className="text-sm mt-2">
                    <strong>Note:</strong> Document conversion requires Pandoc to be installed on the server.
                  </p>
                )}
              </div>
            )}

            {status === 'completed' && showFeedback && (
              <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
                <p className="font-medium">Conversion completed successfully!</p>
                <p className="text-sm mt-1">Your document is ready to download.</p>
              </div>
            )}

            <div className="flex gap-4">
              {status === 'idle' || status === 'failed' ? (
                <>
                  <Button onClick={handleConvert} className="flex-1">
                    Convert Document
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
                    Download Document
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

      <Card className="bg-blue-50 border border-blue-200">
        <h3 className="font-semibold text-blue-900 mb-2">Document Conversion Tips</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• <strong>PDF:</strong> Best for sharing final documents, preserves layout</li>
          <li>• <strong>DOCX:</strong> Microsoft Word format, editable and widely compatible</li>
          <li>• <strong>Markdown:</strong> Lightweight markup, great for documentation</li>
          <li>• <strong>HTML:</strong> Web format, can be styled with CSS</li>
          <li>• <strong>TXT:</strong> Plain text, universally readable but no formatting</li>
          <li>• <strong>RTF:</strong> Rich text format, compatible with many word processors</li>
          <li>• Preserve formatting keeps styles, fonts, and layout from the original</li>
          <li>• Table of contents is useful for longer documents with headings</li>
        </ul>
      </Card>
    </div>
  );
};
