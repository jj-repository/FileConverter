const { app, BrowserWindow, ipcMain, Menu, shell, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const https = require('https');
const BackendManager = require('./backend-manager.cjs');
const { runUpdate } = require('./update-manager.cjs');
const {
  DOWNLOAD_MAX_BYTES,
  isPathInAllowedRoots,
  isDownloadPathSafe,
} = require('./helpers.cjs');

let mainWindow;
let backendManager;

const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

// Version and Update Constants
const pkg = require('../package.json');
const APP_VERSION = pkg.version;
const GITHUB_REPO = 'jj-repository/FileConverter';
const GITHUB_RELEASES_URL = `https://github.com/${GITHUB_REPO}/releases`;

// Settings file for app preferences
const settingsFile = path.join(app.getPath('userData'), 'settings.json');

const defaultSettings = {
  autoCheckUpdates: false
};

function loadSettings() {
  try {
    if (fs.existsSync(settingsFile)) {
      const data = fs.readFileSync(settingsFile, 'utf8');
      return { ...defaultSettings, ...JSON.parse(data) };
    }
  } catch (e) {
    console.error('Failed to load settings:', e);
  }
  return { ...defaultSettings };
}

function saveSettings(settings) {
  try {
    fs.writeFileSync(settingsFile, JSON.stringify(settings, null, 2), 'utf8');
  } catch (e) {
    console.error('Failed to save settings:', e);
  }
}

let appSettings = defaultSettings;

// Compare version strings
function versionNewer(latest, current) {
  const parseVersion = (v) => v.replace(/^v/, '').split('.').map(n => parseInt(n, 10) || 0);
  const latestParts = parseVersion(latest);
  const currentParts = parseVersion(current);

  for (let i = 0; i < Math.max(latestParts.length, currentParts.length); i++) {
    const l = latestParts[i] || 0;
    const c = currentParts[i] || 0;
    if (l > c) return true;
    if (l < c) return false;
  }
  return false;
}

// Check + apply update via full auto-update flow (download + SHA256 verify + relaunch)
function checkForUpdates(silent = false) {
  runUpdate({ silent, parentWindow: mainWindow });
}

function showAboutDialog() {
  if (!mainWindow) return;
  const aboutWindow = new BrowserWindow({
    width: 360,
    height: 360,
    parent: mainWindow,
    modal: true,
    resizable: false,
    minimizable: false,
    maximizable: false,
    title: 'About FileConverter',
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      devTools: false,
    },
  });
  aboutWindow.setMenu(null);

  const aboutHtml = path.join(__dirname, 'about.html');
  const mascotFile = path.join(__dirname, 'takodachi.webp');
  const mascotUrl = 'file://' + mascotFile.replace(/\\/g, '/');
  const qs = `?v=${encodeURIComponent(APP_VERSION)}&mascot=${encodeURIComponent(mascotUrl)}`;
  aboutWindow.loadFile(aboutHtml, { search: qs });
}

// Create application menu with update options
function createAppMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        { role: 'quit' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'Check for Updates...',
          click: () => checkForUpdates(false)
        },
        {
          label: 'Check for Updates on Startup',
          type: 'checkbox',
          checked: appSettings.autoCheckUpdates,
          click: (menuItem) => {
            appSettings.autoCheckUpdates = menuItem.checked;
            saveSettings(appSettings);
          }
        },
        { type: 'separator' },
        {
          label: 'Open Logs Folder',
          click: () => {
            const logDir = path.join(app.getPath('userData'), 'logs');
            try {
              fs.mkdirSync(logDir, { recursive: true });
            } catch (_) { /* ignore */ }
            shell.openPath(logDir);
          }
        },
        {
          label: 'View on GitHub',
          click: () => shell.openExternal(`https://github.com/${GITHUB_REPO}`)
        },
        {
          label: 'About FileConverter',
          click: () => showAboutDialog(),
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      preload: path.join(__dirname, 'preload.cjs'),
      devTools: isDev // Only enable DevTools in development
    },
    icon: path.join(__dirname, '../build/icon.png'),
    title: 'FileConverter'
  });

  // Set Content Security Policy
  // unsafe-inline required for Vite HMR in dev; removed in production builds.
  const scriptSrc = isDev ? "script-src 'self' 'unsafe-inline'" : "script-src 'self'";
  const styleSrc = isDev ? "style-src 'self' 'unsafe-inline'" : "style-src 'self'";
  mainWindow.webContents.session.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': [
          `default-src 'self'; ${scriptSrc}; ${styleSrc}; img-src 'self' data: blob:; connect-src 'self' http://localhost:* ws://localhost:*;`
        ]
      }
    });
  });

  // Set up application menu
  createAppMenu();

  // Load the app
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    // DevTools disabled by default - press F12 to open manually if needed
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  // Prevent DevTools from opening automatically
  mainWindow.webContents.on('devtools-opened', () => {
    // Only allow DevTools if explicitly opened by user (F12)
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    const { shell } = require('electron');
    try {
      const parsed = new URL(url);
      if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
        shell.openExternal(url);
      }
    } catch (_err) {
      /* ignore malformed URL */
    }
    return { action: 'deny' };
  });

  mainWindow.webContents.on('will-navigate', (event, url) => {
    const allowed = isDev
      ? url.startsWith('http://localhost:') || url.startsWith('http://127.0.0.1:')
      : url.startsWith('file://');
    if (!allowed) {
      event.preventDefault();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

async function startBackend() {
  try {
    const logDir = path.join(app.getPath('userData'), 'logs');
    backendManager = new BackendManager(isDev, logDir);
    await backendManager.start();
    console.log('Backend server started successfully');
  } catch (error) {
    console.error('Failed to start backend:', error);
    // Show error dialog
    const { dialog } = require('electron');
    const logDir = path.join(app.getPath('userData'), 'logs');
    dialog.showErrorBox(
      'Backend Error',
      `Failed to start the backend server:\n${error.message}\n\nThe application will continue, but file conversion may not work.\n\nLogs: ${logDir}`
    );
  }
}

async function stopBackend() {
  if (backendManager) {
    await backendManager.stop();
    console.log('Backend server stopped');
  }
}

// App lifecycle
app.whenReady().then(async () => {
  // Load settings before creating window
  appSettings = loadSettings();

  await startBackend();
  createWindow();

  // Check for updates on startup if enabled (with delay)
  if (appSettings.autoCheckUpdates) {
    setTimeout(() => {
      checkForUpdates(true);
    }, 4000);  // 4 second delay to let UI initialize
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

let isQuitting = false;
app.on('before-quit', async (event) => {
  if (isQuitting) return;
  isQuitting = true;
  event.preventDefault();
  try {
    await stopBackend();
  } catch (e) {
    console.error('Error stopping backend:', e);
  }
  app.quit();
});

// IPC handlers
ipcMain.handle('get-backend-status', async () => {
  if (backendManager) {
    return {
      running: backendManager.isRunning(),
      port: backendManager.getPort()
    };
  }
  return { running: false, port: null };
});

ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

ipcMain.handle('check-for-updates', () => {
  checkForUpdates(false);
});

ipcMain.handle('get-app-path', () => {
  return app.getAppPath();
});

// File/Folder selection dialogs
ipcMain.handle('select-output-directory', async () => {
  const { dialog } = require('electron');
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory', 'createDirectory'],
    title: 'Select Output Directory'
  });

  if (!result.canceled && result.filePaths.length > 0) {
    return result.filePaths[0];
  }
  return null;
});

ipcMain.handle('select-folder-files', async () => {
  const { dialog } = require('electron');
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory'],
    title: 'Select Folder to Convert'
  });

  if (!result.canceled && result.filePaths.length > 0) {
    const fs = require('fs');
    const folderPath = result.filePaths[0];

    // Read all files in the directory
    const files = fs.readdirSync(folderPath);
    const filePaths = files
      .map(file => path.join(folderPath, file))
      .filter(filePath => {
        const stats = fs.statSync(filePath);
        return stats.isFile(); // Only include files, not subdirectories
      });

    return filePaths;
  }
  return [];
});

ipcMain.handle('read-file-as-buffer', async (event, filePath) => {
  try {
    const realPath = fs.realpathSync(filePath);
    const allowedRoots = [
      require('os').homedir(),
      app.getPath('userData'),
      app.getPath('downloads'),
      app.getPath('temp'),
    ];
    if (!isPathInAllowedRoots(realPath, allowedRoots)) {
      throw new Error('Access denied: path outside allowed directories');
    }
    const stats = fs.statSync(realPath);
    if (!stats.isFile()) {
      throw new Error('Not a regular file');
    }
    if (stats.size > DOWNLOAD_MAX_BYTES) {
      throw new Error(`File too large: ${stats.size} bytes exceeds ${DOWNLOAD_MAX_BYTES}`);
    }
    return fs.readFileSync(realPath);
  } catch (err) {
    console.error('read-file-as-buffer rejected:', err.message);
    throw err;
  }
});

ipcMain.handle('show-item-in-folder', async (event, filePath) => {
  const { shell } = require('electron');
  const fs = require('fs');

  // Validate path exists and is safe
  try {
    const realPath = fs.realpathSync(filePath);

    // Validate path is within expected directories (use path.relative to avoid prefix-confusion)
    const homePath = require('os').homedir();
    const appPath = app.getPath('userData');
    const downloadsPath = app.getPath('downloads');
    if (!isPathInAllowedRoots(realPath, [homePath, appPath, downloadsPath])) {
      return { success: false, error: 'Access denied: path outside allowed directories' };
    }

    // Only allow if file actually exists
    if (fs.existsSync(realPath)) {
      shell.showItemInFolder(realPath);
    }
  } catch (err) {
    console.error('Invalid file path:', err);
  }
});

// Download file from URL and save to specified directory
ipcMain.handle('download-file', async (event, { url, directory, filename }) => {
  const fs = require('fs');
  const https = require('https');
  const http = require('http');

  try {
    // SECURITY: Validate URL is http/https
    const parsedUrl = new URL(url);
    if (!['http:', 'https:'].includes(parsedUrl.protocol)) {
      throw new Error('Invalid URL protocol. Only http and https are allowed.');
    }

    // SECURITY: Only allow localhost (internal backend API) or external HTTPS
    // Block private network ranges to prevent SSRF attacks
    const hostname = parsedUrl.hostname.toLowerCase();
    const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1';
    const isPrivateNetwork =
      hostname.startsWith('192.168.') ||
      hostname.startsWith('10.') ||
      hostname.startsWith('172.16.') || hostname.startsWith('172.17.') ||
      hostname.startsWith('172.18.') || hostname.startsWith('172.19.') ||
      hostname.startsWith('172.20.') || hostname.startsWith('172.21.') ||
      hostname.startsWith('172.22.') || hostname.startsWith('172.23.') ||
      hostname.startsWith('172.24.') || hostname.startsWith('172.25.') ||
      hostname.startsWith('172.26.') || hostname.startsWith('172.27.') ||
      hostname.startsWith('172.28.') || hostname.startsWith('172.29.') ||
      hostname.startsWith('172.30.') || hostname.startsWith('172.31.') ||
      hostname.startsWith('169.254.') ||   // link-local
      hostname === '0.0.0.0' ||
      hostname === '::1' ||                 // IPv6 loopback
      hostname === '[::1]' ||
      /^fc[0-9a-f]{2}:/i.test(hostname) ||  // IPv6 unique local fc00::/7
      /^fd[0-9a-f]{2}:/i.test(hostname) ||
      hostname.startsWith('fe80:');          // IPv6 link-local

    // Allow localhost for internal API, but block other private IPs
    if (isPrivateNetwork) {
      throw new Error('Cannot download from private network addresses');
    }

    // SECURITY: Sanitize filename to prevent path traversal
    const sanitizedFilename = path.basename(filename);
    if (sanitizedFilename !== filename || sanitizedFilename.includes('..')) {
      throw new Error('Invalid filename');
    }

    // SECURITY: Validate directory exists and resolve to absolute path
    const realDirectory = fs.realpathSync(directory);
    const outputPath = path.join(realDirectory, sanitizedFilename);

    // SECURITY: Ensure output path is within the specified directory.
    if (!isDownloadPathSafe(realDirectory, outputPath)) {
      throw new Error('Path traversal detected');
    }

    // Create write stream
    const fileStream = fs.createWriteStream(outputPath);

    return new Promise((resolve, reject) => {
      // Enforce HTTPS for external (non-localhost) downloads
      if (!isLocalhost && parsedUrl.protocol !== 'https:') {
        fileStream.destroy();
        reject(new Error('Only HTTPS is allowed for external downloads'));
        return;
      }

      // Use http or https based on URL
      const protocol = parsedUrl.protocol === 'https:' ? https : http;

      protocol.get(url, (response) => {
        if (response.statusCode !== 200) {
          fileStream.destroy();
          response.resume(); // drain the response to free the socket
          reject(new Error(`Failed to download: ${response.statusCode}`));
          return;
        }

        let bytesReceived = 0;
        response.on('data', (chunk) => {
          bytesReceived += chunk.length;
          if (bytesReceived > DOWNLOAD_MAX_BYTES) {
            fileStream.destroy();
            response.destroy();
            fs.unlink(outputPath, () => {});
            reject(new Error('Download exceeded maximum allowed size (500 MB)'));
          }
        });
        response.pipe(fileStream);

        fileStream.on('finish', () => {
          fileStream.close();
          resolve({ success: true, path: outputPath });
        });

        fileStream.on('error', (err) => {
          fs.unlink(outputPath, () => {}); // Delete incomplete file
          reject(err);
        });
      }).on('error', (err) => {
        reject(err);
      });
    });
  } catch (err) {
    console.error('Download error:', err);
    throw err;
  }
});
