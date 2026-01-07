/**
 * Format file size in human-readable format
 * @param bytes File size in bytes
 * @returns Formatted string (e.g., "1.50 MB", "512.00 KB")
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
};

/**
 * Get appropriate icon for a file based on its extension
 * @param filename The filename including extension
 * @returns Emoji icon representing the file type
 */
export const getFileIcon = (filename: string): string => {
  const ext = filename.split('.').pop()?.toLowerCase() || '';

  // Image files
  if (['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp', 'tiff', 'ico', 'heic', 'heif', 'svg', 'tga'].includes(ext)) {
    return '\uD83D\uDDBC\uFE0F'; // framed picture
  }

  // Video files
  if (['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv', 'm4v', '3gp', '3g2', 'mts', 'm2ts', 'vob', 'ts', 'ogv'].includes(ext)) {
    return '\uD83C\uDFA5'; // movie camera
  }

  // Audio files
  if (['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'wma', 'opus', 'alac', 'ape', 'mka'].includes(ext)) {
    return '\uD83C\uDFB5'; // musical note
  }

  // Document files
  if (['txt', 'pdf', 'docx', 'doc', 'md', 'html', 'rtf', 'odt'].includes(ext)) {
    return '\uD83D\uDCC4'; // page facing up
  }

  // Spreadsheet files
  if (['xlsx', 'xls', 'ods', 'csv', 'tsv'].includes(ext)) {
    return '\uD83D\uDCCA'; // bar chart
  }

  // Archive files
  if (['zip', 'tar', 'gz', '7z', 'rar', 'tgz', 'tbz2'].includes(ext)) {
    return '\uD83D\uDCE6'; // package
  }

  // eBook files
  if (['epub', 'mobi', 'azw', 'azw3'].includes(ext)) {
    return '\uD83D\uDCDA'; // books
  }

  // Font files
  if (['ttf', 'otf', 'woff', 'woff2'].includes(ext)) {
    return '\uD83D\uDD24'; // abc
  }

  // Subtitle files
  if (['srt', 'vtt', 'ass', 'ssa', 'sub'].includes(ext)) {
    return '\uD83D\uDCAC'; // speech balloon
  }

  // Data files
  if (['json', 'xml', 'yaml', 'yml', 'toml', 'ini'].includes(ext)) {
    return '\uD83D\uDDC3\uFE0F'; // card file box
  }

  // Default folder icon
  return '\uD83D\uDCC1'; // file folder
};

/**
 * Get file extension from filename
 * @param filename The filename
 * @returns The extension without the dot, lowercase
 */
export const getFileExtension = (filename: string): string => {
  const parts = filename.split('.');
  return parts.length > 1 ? parts.pop()?.toLowerCase() || '' : '';
};

/**
 * Generate a safe filename by removing/replacing invalid characters
 * @param filename Original filename
 * @returns Sanitized filename safe for filesystem operations
 */
export const sanitizeFilename = (filename: string): string => {
  return filename
    .replace(/[/\\]/g, '_')     // Replace path separators
    .replace(/\.\./g, '_')      // Remove parent directory references
    .replace(/\0/g, '')         // Remove null bytes
    .replace(/^\.+/, '')        // Remove leading dots
    .replace(/[<>:"|?*]/g, '_') // Remove Windows invalid chars
    .trim();
};
