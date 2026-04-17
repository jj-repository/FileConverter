import React, { useCallback, useRef } from 'react';
import { useDropzone } from 'react-dropzone';

interface DropZoneProps {
  onFileSelect: (file: File) => void;
  acceptedFormats?: string[];
  fileType: string;
}

export const DropZone: React.FC<DropZoneProps> = ({
  onFileSelect,
  acceptedFormats,
  fileType,
}) => {
  const statusMessageRef = useRef<HTMLDivElement>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onFileSelect(acceptedFiles[0]);
      }
    },
    [onFileSelect]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: acceptedFormats
      ? {
          [getMimeType(fileType)]: acceptedFormats.map((ext) => `.${ext}`),
        }
      : undefined,
    maxFiles: 1,
    multiple: false,
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
      aria-label={`Upload ${fileType} file. Supported formats: ${formatsList}. Press Enter or Space to browse files, or drag and drop a file here.`}
      aria-describedby="dropzone-hint dropzone-status"
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
        aria-label={`Select ${fileType} file to convert`}
      />

      <div className="flex flex-col items-center gap-4">
        <div className="text-6xl" aria-hidden="true">
          {getFileIcon(fileType)}
        </div>

        {/* Screen reader announcement for drag state changes */}
        <div
          id="dropzone-status"
          ref={statusMessageRef}
          role="status"
          aria-live="polite"
          aria-atomic="true"
          className="sr-only"
        >
          {isDragActive && !isDragReject && 'File is over drop zone. Release to upload.'}
          {isDragReject && 'Invalid file type detected.'}
        </div>

        {isDragActive && !isDragReject ? (
          <p className="text-primary-600 font-medium" aria-hidden="true">Drop the file here...</p>
        ) : isDragReject ? (
          <p className="text-red-600 font-medium" aria-hidden="true">Invalid file type!</p>
        ) : (
          <>
            <p id="dropzone-hint" className="text-gray-700 font-medium">
              Drag & drop a {fileType} file here, or click to select
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

function getMimeType(fileType: string): string {
  switch (fileType) {
    case 'image':
      return 'image/*';
    case 'video':
      return 'video/*';
    case 'audio':
      return 'audio/*';
    case 'document':
      return 'application/*,text/*';
    case 'subtitle':
      return 'text/*,application/x-subrip';
    case 'ebook':
      return 'application/epub+zip,application/x-mobipocket-ebook,text/*';
    case 'font':
      return 'font/*,application/font-woff,application/font-woff2';
    case 'archive':
      return 'application/zip,application/x-tar,application/x-7z-compressed,application/gzip';
    case 'data':
      return 'application/json,application/xml,text/csv,text/*';
    case 'spreadsheet':
      return 'application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv';
    default:
      return '*/*';
  }
}

function getFileIcon(fileType: string): string {
  switch (fileType) {
    case 'image':
      return '🖼️';
    case 'video':
      return '🎥';
    case 'audio':
      return '🎵';
    case 'document':
      return '📄';
    default:
      return '📁';
  }
}
