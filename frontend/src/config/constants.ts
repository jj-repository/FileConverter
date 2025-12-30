/**
 * Application-wide constants and configuration
 */

// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Timing Configuration
export const AUTO_DOWNLOAD_DELAY = 200; // ms
export const FORCE_RERENDER_DELAY = 100; // ms

// File Size Limits
export const MAX_FILE_SIZE_MB = 500;

// Default Values
export const DEFAULT_IMAGE_QUALITY = 95;
export const DEFAULT_VIDEO_CODEC = 'libx264';
export const DEFAULT_AUDIO_BITRATE = '192k';

// Electron Integration
export const ELECTRON_DOWNLOAD_CONFIG = {
  defaultDirectory: 'Downloads',
  showItemInFolderPrompt: true,
};
