const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const BackendManager = require('./backend-manager');

let mainWindow;
let backendManager;

const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

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

  // Remove menu bar
  mainWindow.setMenuBarVisibility(false);

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
  await startBackend();
  createWindow();

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
  shell.showItemInFolder(filePath);
});

// Download file from URL and save to specified directory
ipcMain.handle('download-file', async (event, { url, directory, filename }) => {
  const fs = require('fs');
  const https = require('https');
  const http = require('http');

  try {
    // Determine output path
    const outputPath = path.join(directory, filename);

    // Create write stream
    const fileStream = fs.createWriteStream(outputPath);

    return new Promise((resolve, reject) => {
      // Use http or https based on URL
      const protocol = url.startsWith('https') ? https : http;

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
