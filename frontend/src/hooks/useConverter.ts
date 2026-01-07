import { useState, useEffect, useCallback } from 'react';
import { ConversionStatus } from '../types/conversion';
import { useWebSocket } from './useWebSocket';
import { API_BASE_URL, AUTO_DOWNLOAD_DELAY, FORCE_RERENDER_DELAY } from '../config/constants';
import { getFriendlyErrorMessage } from '../utils/errorMessages';

/**
 * Sanitize filename to prevent path traversal attacks
 * Removes path separators, parent directory references, and null bytes
 */
const sanitizeFilename = (filename: string): string => {
  // Remove path separators and parent directory references
  return filename
    .replace(/[/\\]/g, '_')  // Replace path separators with underscore
    .replace(/\.\./g, '_')   // Remove parent directory references
    .replace(/\0/g, '')      // Remove null bytes
    .replace(/^\.+/, '');    // Remove leading dots
};

interface UseConverterOptions {
  defaultOutputFormat: string;
  onConversionComplete?: (downloadUrl: string) => void;
}

interface ConvertOptions {
  [key: string]: any;
}

interface ConversionResponse {
  session_id: string;
  status: ConversionStatus;
  download_url?: string;
  error?: string;
}

export const useConverter = (options: UseConverterOptions) => {
  const { defaultOutputFormat, onConversionComplete } = options;

  // State management
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [outputFormat, setOutputFormat] = useState<string>(defaultOutputFormat);
  const [outputDirectory, setOutputDirectory] = useState<string | null>(null);
  const [status, setStatus] = useState<ConversionStatus>('idle');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [isDraggingOver, setIsDraggingOver] = useState(false);
  const [customFilename, setCustomFilename] = useState<string>('');
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isUploading, setIsUploading] = useState<boolean>(false);

  const { progress } = useWebSocket(sessionId);

  // Update status from WebSocket progress
  useEffect(() => {
    if (progress) {
      setStatus(progress.status);
      setShowFeedback(true);
    }
  }, [progress]);

  // File selection handler
  const handleFileSelect = useCallback((file: File) => {
    setSelectedFile(file);
    setStatus('idle');
    setError(null);
    setDownloadUrl(null);
    setShowFeedback(false);
    setIsDraggingOver(false);
    setUploadProgress(0);
    setIsUploading(false);
  }, []);

  // Drag and drop handlers
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  // Output directory selection
  const handleSelectOutputDirectory = useCallback(async () => {
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
      const rawError = err instanceof Error ? err.message : 'Failed to select output directory';
      setError(getFriendlyErrorMessage(rawError));
    }
  }, []);

  // Auto-download functionality
  const autoDownload = useCallback(async (url: string) => {
    if (!outputDirectory || !window.electron?.downloadFile) return;

    try {
      const urlParts = url.split('/');
      const defaultFilename = urlParts[urlParts.length - 1] || `converted.${outputFormat}`;
      const filename = customFilename ? `${customFilename}.${outputFormat}` : defaultFilename;

      const result = await window.electron.downloadFile({
        url: `${API_BASE_URL}${url}`,
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
      alert(`Failed to save file: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  }, [outputDirectory, outputFormat, customFilename]);

  // Upload progress callback
  const handleUploadProgress = useCallback((progress: number) => {
    setUploadProgress(progress);
    if (progress === 100) {
      setIsUploading(false);
    }
  }, []);

  // Generic conversion handler
  const handleConvert = useCallback(async (
    converterAPI: { convert: (file: File, options: ConvertOptions) => Promise<ConversionResponse> },
    conversionOptions: ConvertOptions
  ) => {
    if (!selectedFile) return;

    try {
      setStatus('converting');
      setError(null);
      setShowFeedback(true);
      setUploadProgress(0);
      setIsUploading(true);

      const response = await converterAPI.convert(selectedFile, {
        outputFormat,
        ...conversionOptions,
        onUploadProgress: handleUploadProgress,
      });

      setSessionId(response.session_id);

      if (response.status === 'completed' && response.download_url) {
        setDownloadUrl(response.download_url);
        setStatus('completed');
        setShowFeedback(true);

        // Trigger callback if provided
        if (onConversionComplete) {
          onConversionComplete(response.download_url);
        }

        // Auto-download if output directory is selected
        if (outputDirectory && window.electron?.downloadFile && response.download_url) {
          setTimeout(async () => {
            await autoDownload(response.download_url!);
          }, AUTO_DOWNLOAD_DELAY);
        }

        // Force re-render
        setTimeout(() => {
          setStatus('completed');
          setShowFeedback(true);
        }, FORCE_RERENDER_DELAY);
      } else if (response.status === 'failed') {
        const rawError = response.error || 'Conversion failed';
        setError(getFriendlyErrorMessage(rawError));
        setStatus('failed');
      }
    } catch (err: any) {
      const rawError = err.response?.data?.detail || err.message || 'Conversion failed';
      setError(getFriendlyErrorMessage(rawError));
      setStatus('failed');
      setShowFeedback(true);
    } finally {
      setIsUploading(false);
    }
  }, [selectedFile, outputFormat, outputDirectory, autoDownload, onConversionComplete, handleUploadProgress]);

  // Download handler
  const handleDownload = useCallback(async () => {
    if (!downloadUrl) return;

    // If user selected an output directory and we're in Electron, download to that directory
    if (outputDirectory && window.electron?.downloadFile) {
      try {
        const urlParts = downloadUrl.split('/');
        const defaultFilename = urlParts[urlParts.length - 1] || `converted.${outputFormat}`;
        // Sanitize filename to prevent path traversal attacks
        const safeCustomFilename = customFilename ? sanitizeFilename(customFilename) : null;
        const filename = safeCustomFilename ? `${safeCustomFilename}.${outputFormat}` : sanitizeFilename(defaultFilename);

        const result = await window.electron.downloadFile({
          url: `${API_BASE_URL}${downloadUrl}`,
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
        alert(`Failed to download file: ${err instanceof Error ? err.message : 'Unknown error'}`);
      }
    } else {
      // Browser download - validate URL is same-origin to prevent open redirect
      if (downloadUrl.startsWith('/') || downloadUrl.startsWith(window.location.origin)) {
        window.location.href = downloadUrl;
      }
    }
  }, [downloadUrl, outputDirectory, outputFormat, customFilename]);

  // Reset handler
  const handleReset = useCallback(() => {
    setSelectedFile(null);
    setStatus('idle');
    setDownloadUrl(null);
    setError(null);
    setSessionId(null);
    setShowFeedback(false);
    setUploadProgress(0);
    setIsUploading(false);
  }, []);

  // Accessibility helpers
  const getProgressAriaAttributes = () => ({
    role: 'progressbar' as const,
    'aria-valuenow': progress?.progress || 0,
    'aria-valuemin': 0,
    'aria-valuemax': 100,
    'aria-label': progress?.message || 'Conversion progress',
  });

  const getUploadProgressAriaAttributes = () => ({
    role: 'progressbar' as const,
    'aria-valuenow': uploadProgress,
    'aria-valuemin': 0,
    'aria-valuemax': 100,
    'aria-label': 'Upload progress',
  });

  const getStatusAriaAttributes = () => ({
    role: status === 'failed' ? ('alert' as const) : ('status' as const),
    'aria-live': (status === 'failed' ? 'assertive' : 'polite') as 'assertive' | 'polite',
    'aria-atomic': true,
  });

  return {
    // State
    selectedFile,
    outputFormat,
    outputDirectory,
    status,
    sessionId,
    downloadUrl,
    error,
    showFeedback,
    isDraggingOver,
    customFilename,
    progress,
    uploadProgress,
    isUploading,

    // Setters
    setOutputFormat,
    setCustomFilename,

    // Handlers
    handleFileSelect,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    handleSelectOutputDirectory,
    handleConvert,
    handleDownload,
    handleReset,

    // Accessibility helpers
    getProgressAriaAttributes,
    getUploadProgressAriaAttributes,
    getStatusAriaAttributes,
  };
};
