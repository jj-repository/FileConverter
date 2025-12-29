import React, { useCallback } from 'react';
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
          {getFileIcon(fileType)}
        </div>

        {isDragActive && !isDragReject ? (
          <p className="text-primary-600 font-medium">Drop the file here...</p>
        ) : isDragReject ? (
          <p className="text-red-600 font-medium">Invalid file type!</p>
        ) : (
          <>
            <p className="text-gray-700 font-medium">
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
