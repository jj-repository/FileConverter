const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electron', {
  // Backend status
  getBackendStatus: () => ipcRenderer.invoke('get-backend-status'),

  // App info
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  getAppPath: () => ipcRenderer.invoke('get-app-path'),

  // File/Folder dialogs
  selectOutputDirectory: () => ipcRenderer.invoke('select-output-directory'),
  selectFolderFiles: () => ipcRenderer.invoke('select-folder-files'),
  showItemInFolder: (filePath) => ipcRenderer.invoke('show-item-in-folder', filePath),

  // File operations
  downloadFile: ({ url, directory, filename }) => ipcRenderer.invoke('download-file', { url, directory, filename }),

  // Platform info
  platform: process.platform,
  isElectron: true
});
