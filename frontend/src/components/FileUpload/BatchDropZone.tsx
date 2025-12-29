import React, { useCallback } from 'react';
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

  return (
    <div
      {...getRootProps()}
      className={`
        border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors duration-200
        ${isDragActive && !isDragReject ? 'border-primary-500 bg-primary-50' : ''}
        ${isDragReject ? 'border-red-500 bg-red-50' : ''}
        ${!isDragActive && !isDragReject ? 'border-gray-300 hover:border-gray-400' : ''}
      `}
    >
      <input {...getInputProps()} />

      <div className="flex flex-col items-center gap-4">
        <div className="text-6xl">
          📁
        </div>

        {isDragActive && !isDragReject ? (
          <p className="text-primary-600 font-medium">Drop the files here...</p>
        ) : isDragReject ? (
          <p className="text-red-600 font-medium">Some files have invalid types!</p>
        ) : (
          <>
            <p className="text-gray-700 font-medium">
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
