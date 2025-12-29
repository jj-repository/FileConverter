export interface ElectronAPI {
  getBackendStatus: () => Promise<{ running: boolean; port: number | null }>;
  getAppVersion: () => Promise<string>;
  getAppPath: () => Promise<string>;
  selectOutputDirectory: () => Promise<string | null>;
  selectFolderFiles: () => Promise<string[]>;
  showItemInFolder: (filePath: string) => Promise<void>;
  downloadFile: (options: { url: string; directory: string; filename: string }) => Promise<{ success: boolean; path: string }>;
  platform: string;
  isElectron: boolean;
}

declare global {
  interface Window {
    electron?: ElectronAPI;
  }
}

export {};
