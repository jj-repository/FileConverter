import React, { useCallback, useRef } from 'react';
import { useDropzone } from 'react-dropzone';

interface BatchDropZoneProps {
  onFilesSelect: (files: File[]) => void;
  acceptedFormats?: string[];
  maxFiles?: number;
}

export const BatchDropZone: React.FC<BatchDropZoneProps> = ({
  onFilesSelect,
  acceptedFormats,
  maxFiles = 100,
}) => {
  const statusMessageRef = useRef<HTMLDivElement>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onFilesSelect(acceptedFiles);
      }
    },
    [onFilesSelect]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: acceptedFormats
      ? {
          'image/*': acceptedFormats.filter(f => ['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp', 'tiff', 'ico'].includes(f)).map(ext => `.${ext}`),
          'video/*': acceptedFormats.filter(f => ['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv'].includes(f)).map(ext => `.${ext}`),
          'audio/*': acceptedFormats.filter(f => ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'wma'].includes(f)).map(ext => `.${ext}`),
          'application/*': acceptedFormats.filter(f => ['pdf', 'docx', 'txt', 'md', 'html', 'rtf'].includes(f)).map(ext => `.${ext}`),
        }
      : undefined,
    maxFiles,
    multiple: true,
  });

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      // Trigger the hidden file input
      const inputElement = e.currentTarget.querySelector('input[type="file"]') as HTMLInputElement;
      if (inputElement) {
        inputElement.click();
      }
    }
  };

  const formatsList = acceptedFormats && acceptedFormats.length > 0
    ? acceptedFormats.join(', ').toUpperCase()
    : 'all formats';

  return (
    <div
      {...getRootProps()}
      role="button"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      aria-label={`Upload multiple files. Maximum ${maxFiles} files. Supported formats: ${formatsList}. Press Enter or Space to browse files, or drag and drop files here.`}
      aria-describedby="batch-dropzone-hint batch-dropzone-status"
      className={`
        border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors duration-200
        focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
        ${isDragActive && !isDragReject ? 'border-primary-500 bg-primary-50' : ''}
        ${isDragReject ? 'border-red-500 bg-red-50' : ''}
        ${!isDragActive && !isDragReject ? 'border-gray-300 hover:border-gray-400' : ''}
      `}
    >
      <input
        {...getInputProps()}
        aria-label={`Select multiple files to convert. Maximum ${maxFiles} files allowed.`}
      />

      <div className="flex flex-col items-center gap-4">
        <div className="text-6xl" aria-hidden="true">
          📁
        </div>

        {/* Screen reader announcement for drag state changes */}
        <div
          id="batch-dropzone-status"
          ref={statusMessageRef}
          role="status"
          aria-live="polite"
          aria-atomic="true"
          className="sr-only"
        >
          {isDragActive && !isDragReject && 'Files are over drop zone. Release to upload.'}
          {isDragReject && 'Some files have invalid types.'}
        </div>

        {isDragActive && !isDragReject ? (
          <p className="text-primary-600 font-medium" aria-hidden="true">Drop the files here...</p>
        ) : isDragReject ? (
          <p className="text-red-600 font-medium" aria-hidden="true">Some files have invalid types!</p>
        ) : (
          <>
            <p id="batch-dropzone-hint" className="text-gray-700 font-medium">
              Drag & drop multiple files here, or click to select
            </p>
            <p className="text-sm text-gray-500">
              Up to {maxFiles} files at once
            </p>
            <p className="text-sm text-gray-500">
              {acceptedFormats && acceptedFormats.length > 0
                ? `Supported formats: ${acceptedFormats.join(', ').toUpperCase()}`
                : 'All formats supported'}
            </p>
          </>
        )}
      </div>
    </div>
  );
};
