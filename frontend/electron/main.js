const { app, BrowserWindow, ipcMain, Menu, shell, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const https = require('https');
const BackendManager = require('./backend-manager');

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
  autoCheckUpdates: true
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

// Check for updates
function checkForUpdates(silent = false) {
  const options = {
    hostname: 'api.github.com',
    path: `/repos/${GITHUB_REPO}/releases/latest`,
    method: 'GET',
    headers: {
      'User-Agent': `FileConverter/${APP_VERSION}`
    }
  };

  const req = https.request(options, (res) => {
    let data = '';
    res.on('data', chunk => data += chunk);
    res.on('end', () => {
      req.setTimeout(0); // Clear timeout on successful response
      try {
        const release = JSON.parse(data);
        const latestVersion = (release.tag_name || '').replace(/^v/, '');

        if (!latestVersion) {
          if (!silent && mainWindow) {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'Update Check',
              message: 'Could not determine latest version.',
              buttons: ['OK']
            });
          }
          return;
        }

        if (versionNewer(latestVersion, APP_VERSION)) {
          if (mainWindow) {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'Update Available',
              message: `A new version is available!\n\nCurrent: v${APP_VERSION}\nLatest: v${latestVersion}`,
              detail: release.body || 'No release notes available.',
              buttons: ['Download Update', 'Later'],
              defaultId: 0
            }).then(result => {
              if (result.response === 0) {
                shell.openExternal(GITHUB_RELEASES_URL);
              }
            });
          }
        } else if (!silent && mainWindow) {
          dialog.showMessageBox(mainWindow, {
            type: 'info',
            title: 'No Updates',
            message: `You are running the latest version (v${APP_VERSION}).`,
            buttons: ['OK']
          });
        }
      } catch (e) {
        if (!silent && mainWindow) {
          dialog.showMessageBox(mainWindow, {
            type: 'error',
            title: 'Update Check Failed',
            message: 'Failed to check for updates.',
            detail: e.message,
            buttons: ['OK']
          });
        }
      }
    });
  });

  req.on('error', (e) => {
    if (!silent && mainWindow) {
      dialog.showMessageBox(mainWindow, {
        type: 'error',
        title: 'Update Check Failed',
        message: 'Failed to check for updates.',
        detail: e.message,
        buttons: ['OK']
      });
    }
  });

  // Add timeout to prevent hanging requests
  req.setTimeout(10000, () => {
    req.destroy();
    if (!silent && mainWindow) {
      dialog.showMessageBox(mainWindow, {
        type: 'error',
        title: 'Update Check Failed',
        message: 'Failed to check for updates.',
        detail: 'Request timed out after 10 seconds.',
        buttons: ['OK']
      });
    }
  });

  req.end();
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
          label: 'View on GitHub',
          click: () => shell.openExternal(`https://github.com/${GITHUB_REPO}`)
        },
        {
          label: 'About FileConverter',
          click: () => {
            if (mainWindow) {
              dialog.showMessageBox(mainWindow, {
                type: 'info',
                title: 'About FileConverter',
                message: `FileConverter v${APP_VERSION}`,
                detail: 'A desktop file conversion application.\n\nBuilt with Electron and Python.',
                buttons: ['OK']
              });
            }
          }
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
      preload: path.join(__dirname, 'preload.js'),
      devTools: isDev // Only enable DevTools in development
    },
    icon: path.join(__dirname, '../build/icon.png'),
    title: 'FileConverter'
  });

  // Set Content Security Policy
  mainWindow.webContents.session.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': [
          "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' http://localhost:* ws://localhost:*;"
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

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

async function startBackend() {
  try {
    backendManager = new BackendManager(isDev);
    await backendManager.start();
    console.log('Backend server started successfully');
  } catch (error) {
    console.error('Failed to start backend:', error);
    // Show error dialog
    const { dialog } = require('electron');
    dialog.showErrorBox(
      'Backend Error',
      `Failed to start the backend server:\n${error.message}\n\nThe application will continue, but file conversion may not work.`
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

app.on('before-quit', async (event) => {
  event.preventDefault();
  await stopBackend();
  process.exit(0);
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

ipcMain.handle('show-item-in-folder', async (event, filePath) => {
  const { shell } = require('electron');
  const fs = require('fs');

  // Validate path exists and is safe
  try {
    const realPath = fs.realpathSync(filePath);
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
      hostname.startsWith('172.30.') || hostname.startsWith('172.31.');

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

    // SECURITY: Ensure output path is within the specified directory
    if (!outputPath.startsWith(realDirectory)) {
      throw new Error('Path traversal detected');
    }

    // Create write stream
    const fileStream = fs.createWriteStream(outputPath);

    return new Promise((resolve, reject) => {
      // Use http or https based on URL
      const protocol = parsedUrl.protocol === 'https:' ? https : http;

      protocol.get(url, (response) => {
        if (response.statusCode !== 200) {
          reject(new Error(`Failed to download: ${response.statusCode}`));
          return;
        }

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
