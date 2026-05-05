/**
 * Application-wide constants and configuration
 */

// API Configuration
// Under Electron's loadFile() the page is served from file://, so `/api` would
// resolve to a non-existent file:// URL. main.cjs passes the actual backend
// port via the query string (`?backendPort=...`), which we honour here. The
// `VITE_API_URL` env var still wins (used by the web build).
function resolveApiBaseUrl(): string {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL;
  if (typeof window !== 'undefined') {
    const port = new URLSearchParams(window.location.search).get('backendPort');
    if (port) return `http://localhost:${port}`;
  }
  return 'http://localhost:8000';
}

export const API_BASE_URL = resolveApiBaseUrl();

// Timing Configuration
export const AUTO_DOWNLOAD_DELAY = 200; // ms
export const FORCE_RERENDER_DELAY = 100; // ms

// File Size Limits
export const MAX_FILE_SIZE_MB = 500;

// Default Values
export const DEFAULT_IMAGE_QUALITY = 95;
export const DEFAULT_VIDEO_CODEC = 'libx264';
export const DEFAULT_AUDIO_BITRATE = '192k';

// Supported Formats (single source of truth for frontend)
export const IMAGE_FORMATS = ['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp', 'tiff', 'ico', 'heic', 'heif', 'svg', 'tga'];
export const VIDEO_FORMATS = ['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv', 'm4v', '3gp', '3g2', 'mts', 'm2ts', 'vob', 'ts', 'ogv'];
export const AUDIO_FORMATS = ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'wma', 'opus', 'alac', 'ape', 'mka'];
export const DOCUMENT_FORMATS = ['txt', 'pdf', 'docx', 'md', 'html', 'rtf', 'odt'];
export const DATA_FORMATS = ['csv', 'json', 'xml', 'yaml', 'yml', 'toml', 'ini', 'jsonl'];
export const ARCHIVE_FORMATS = ['zip', 'tar', 'tar.gz', 'tgz', 'tar.bz2', 'tbz2', 'gz', '7z'];
export const SPREADSHEET_FORMATS = ['xlsx', 'xls', 'ods', 'csv', 'tsv'];
export const SUBTITLE_FORMATS = ['srt', 'vtt', 'ass', 'ssa', 'sub'];
export const EBOOK_FORMATS = ['epub', 'txt', 'html', 'pdf'];
export const FONT_FORMATS = ['ttf', 'otf', 'woff', 'woff2'];

// Electron Integration
export const ELECTRON_DOWNLOAD_CONFIG = {
  defaultDirectory: 'Downloads',
  showItemInFolderPrompt: true,
};
