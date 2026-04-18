const { app, dialog, BrowserWindow, shell } = require('electron');
const https = require('https');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { spawn } = require('child_process');

const GITHUB_REPO = 'jj-repository/FileConverter';
const RELEASES_URL = `https://github.com/${GITHUB_REPO}/releases`;

function httpsGet(url, headers = {}, { redirects = 5 } = {}) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const req = https.request({
      hostname: u.hostname,
      path: u.pathname + u.search,
      method: 'GET',
      headers: { 'User-Agent': `FileConverter/${app.getVersion()}`, ...headers },
    }, (res) => {
      if ([301, 302, 303, 307, 308].includes(res.statusCode) && res.headers.location && redirects > 0) {
        res.resume();
        resolve(httpsGet(res.headers.location, headers, { redirects: redirects - 1 }));
        return;
      }
      if (res.statusCode !== 200) {
        reject(new Error(`HTTP ${res.statusCode} on ${url}`));
        res.resume();
        return;
      }
      resolve(res);
    });
    req.on('error', reject);
    req.setTimeout(30000, () => { req.destroy(new Error('Request timed out')); });
    req.end();
  });
}

async function fetchJson(url) {
  const res = await httpsGet(url, { 'Accept': 'application/vnd.github+json' });
  return new Promise((resolve, reject) => {
    let data = '';
    res.on('data', (c) => { data += c; });
    res.on('end', () => { try { resolve(JSON.parse(data)); } catch (e) { reject(e); } });
    res.on('error', reject);
  });
}

async function fetchText(url) {
  const res = await httpsGet(url);
  return new Promise((resolve, reject) => {
    let data = '';
    res.on('data', (c) => { data += c; });
    res.on('end', () => resolve(data));
    res.on('error', reject);
  });
}

async function downloadFile(url, destPath, onProgress) {
  const res = await httpsGet(url);
  const total = parseInt(res.headers['content-length'] || '0', 10);
  const hash = crypto.createHash('sha256');
  let received = 0;
  const out = fs.createWriteStream(destPath);
  return new Promise((resolve, reject) => {
    res.on('data', (chunk) => {
      received += chunk.length;
      hash.update(chunk);
      if (onProgress && total > 0) onProgress(received, total);
    });
    res.pipe(out);
    out.on('finish', () => { out.close(() => resolve({ sha256: hash.digest('hex'), bytes: received })); });
    out.on('error', reject);
    res.on('error', reject);
  });
}

function detectInstallKind() {
  if (process.platform === 'win32') {
    if (process.env.PORTABLE_EXECUTABLE_FILE) return { platform: 'win', kind: 'portable', exePath: process.env.PORTABLE_EXECUTABLE_FILE };
    return { platform: 'win', kind: 'installer', exePath: app.getPath('exe') };
  }
  if (process.platform === 'linux') {
    if (process.env.APPIMAGE) return { platform: 'linux', kind: 'appimage', exePath: process.env.APPIMAGE };
    return { platform: 'linux', kind: 'deb', exePath: app.getPath('exe') };
  }
  return { platform: process.platform, kind: 'unknown', exePath: app.getPath('exe') };
}

function assetNameFor(install) {
  if (install.platform === 'win' && install.kind === 'portable') return 'FileConverter.exe';
  if (install.platform === 'win' && install.kind === 'installer') return 'FileConverter-Setup.exe';
  if (install.platform === 'linux' && install.kind === 'appimage') return 'FileConverter-Linux.AppImage';
  if (install.platform === 'linux' && install.kind === 'deb') return 'FileConverter-Linux.deb';
  return null;
}

function versionNewer(latest, current) {
  const parse = (v) => v.replace(/^v/, '').split('.').map((n) => parseInt(n, 10) || 0);
  const a = parse(latest);
  const b = parse(current);
  for (let i = 0; i < Math.max(a.length, b.length); i++) {
    const l = a[i] || 0, c = b[i] || 0;
    if (l > c) return true;
    if (l < c) return false;
  }
  return false;
}

function createProgressWindow(parent) {
  const win = new BrowserWindow({
    width: 420, height: 130,
    parent, modal: true, resizable: false, minimizable: false, maximizable: false,
    title: 'Downloading Update',
    webPreferences: { nodeIntegration: false, contextIsolation: true, sandbox: true, devTools: false },
  });
  win.setMenu(null);
  const html = `<!doctype html><html><head><meta charset="utf-8"><style>
    body { font-family: system-ui, sans-serif; padding: 16px; margin: 0; background: #fff; color: #111; }
    .label { font-size: 13px; margin-bottom: 10px; }
    .bar { width: 100%; height: 14px; background: #eee; border-radius: 7px; overflow: hidden; }
    .fill { height: 100%; width: 0%; background: linear-gradient(90deg,#3b82f6,#60a5fa); transition: width 160ms ease; }
    .pct { font-size: 12px; color: #555; margin-top: 6px; text-align: right; }
  </style></head><body>
    <div class="label" id="label">Preparing download…</div>
    <div class="bar"><div class="fill" id="fill"></div></div>
    <div class="pct" id="pct">0%</div>
    <script>
      const fill = document.getElementById('fill');
      const pct = document.getElementById('pct');
      const label = document.getElementById('label');
      window.addEventListener('message', (e) => { /* reserved */ });
      window._setProgress = (received, total, text) => {
        const p = total > 0 ? Math.min(100, Math.round(received / total * 100)) : 0;
        fill.style.width = p + '%';
        pct.textContent = p + '% (' + (received/1024/1024).toFixed(1) + ' MB / ' + (total/1024/1024).toFixed(1) + ' MB)';
        if (text) label.textContent = text;
      };
    </script></body></html>`;
  win.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(html));
  return win;
}

async function parseSha256Sums(text, assetName) {
  // SHA256SUMS format: "<hash>  <path/to/asset>"
  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    const [hash, ...pathParts] = trimmed.split(/\s+/);
    const filename = path.basename(pathParts.join(' '));
    if (filename === assetName) return hash.toLowerCase();
  }
  return null;
}

function spawnDetached(cmd, args, opts = {}) {
  const child = spawn(cmd, args, { detached: true, stdio: 'ignore', ...opts });
  child.unref();
}

async function applyPortableWin(newExePath, install) {
  // Write a cmd script that: waits for current process, replaces exe, launches new, deletes self
  const currentExe = install.exePath;
  const scriptPath = path.join(app.getPath('temp'), `fc-update-${Date.now()}.cmd`);
  const script = `@echo off
:wait
tasklist /FI "IMAGENAME eq ${path.basename(currentExe)}" | find /I "${path.basename(currentExe)}" >nul
if not errorlevel 1 (
  timeout /t 1 /nobreak >nul
  goto wait
)
move /Y "${newExePath}" "${currentExe}" >nul
start "" "${currentExe}"
del "%~f0"
`;
  fs.writeFileSync(scriptPath, script, { encoding: 'utf8' });
  spawnDetached('cmd.exe', ['/c', scriptPath], { windowsHide: true });
  app.quit();
}

async function applyInstallerWin(newInstallerPath) {
  // Launch NSIS installer; /S for silent is optional — use user-visible by default
  spawnDetached(newInstallerPath, []);
  app.quit();
}

async function applyAppImage(newAppImagePath, install) {
  const target = install.exePath;
  // Replace in place (same filesystem), chmod +x, relaunch
  fs.copyFileSync(newAppImagePath, target);
  fs.chmodSync(target, 0o755);
  try { fs.unlinkSync(newAppImagePath); } catch (_) { /* ignore */ }
  spawnDetached(target, []);
  app.quit();
}

async function runUpdate({ silent = false, parentWindow = null } = {}) {
  try {
    const release = await fetchJson(`https://api.github.com/repos/${GITHUB_REPO}/releases/latest`);
    const latest = (release.tag_name || '').replace(/^v/, '');
    if (!latest) throw new Error('Could not determine latest version.');

    if (!versionNewer(latest, app.getVersion())) {
      if (!silent) {
        dialog.showMessageBox(parentWindow, {
          type: 'info',
          title: 'No Updates',
          message: `You are running the latest version (v${app.getVersion()}).`,
          buttons: ['OK'],
        });
      }
      return;
    }

    const install = detectInstallKind();
    const assetName = assetNameFor(install);
    if (!assetName) {
      dialog.showMessageBox(parentWindow, {
        type: 'info',
        title: 'Manual Update',
        message: `A new version is available (v${latest}).`,
        detail: `Automatic update is not supported for this install (${install.platform}/${install.kind}). The releases page will open.`,
        buttons: ['Open', 'Cancel'],
        defaultId: 0,
      }).then((r) => { if (r.response === 0) shell.openExternal(RELEASES_URL); });
      return;
    }

    // .deb: we can't install without sudo; point user to releases
    if (install.kind === 'deb') {
      dialog.showMessageBox(parentWindow, {
        type: 'info',
        title: 'Update Available',
        message: `FileConverter v${latest} is available.`,
        detail: 'Install the new .deb manually with "sudo dpkg -i FileConverter-Linux.deb".',
        buttons: ['Open Releases Page', 'Later'],
        defaultId: 0,
      }).then((r) => { if (r.response === 0) shell.openExternal(RELEASES_URL); });
      return;
    }

    const resp = await dialog.showMessageBox(parentWindow, {
      type: 'info',
      title: 'Update Available',
      message: `A new version is available!\n\nCurrent: v${app.getVersion()}\nLatest: v${latest}`,
      detail: release.body || 'No release notes available.',
      buttons: ['Download & Install', 'Later'],
      defaultId: 0,
    });
    if (resp.response !== 0) return;

    const asset = (release.assets || []).find((a) => a.name === assetName);
    const sumsAsset = (release.assets || []).find((a) => a.name === 'SHA256SUMS');
    if (!asset) throw new Error(`Release asset "${assetName}" not found.`);

    const tmpDir = path.join(app.getPath('temp'), `fc-update-${Date.now()}`);
    fs.mkdirSync(tmpDir, { recursive: true });
    const assetPath = path.join(tmpDir, assetName);

    const progressWin = createProgressWindow(parentWindow);

    const { sha256 } = await downloadFile(asset.browser_download_url, assetPath, (received, total) => {
      try { progressWin.webContents.executeJavaScript(`window._setProgress(${received}, ${total}, 'Downloading ${assetName}…');`); } catch (_) { /* window closed */ }
    });

    // Verify SHA256 if SHA256SUMS available
    if (sumsAsset) {
      try {
        progressWin.webContents.executeJavaScript(`window._setProgress(1, 1, 'Verifying…');`);
      } catch (_) { /* ignore */ }
      const sumsText = await fetchText(sumsAsset.browser_download_url);
      const expected = await parseSha256Sums(sumsText, assetName);
      if (expected && expected !== sha256.toLowerCase()) {
        progressWin.close();
        throw new Error(`SHA256 mismatch: expected ${expected}, got ${sha256}`);
      }
    }

    progressWin.close();

    // Apply
    if (install.platform === 'win' && install.kind === 'portable') return applyPortableWin(assetPath, install);
    if (install.platform === 'win' && install.kind === 'installer') return applyInstallerWin(assetPath);
    if (install.platform === 'linux' && install.kind === 'appimage') return applyAppImage(assetPath, install);

    // Fallback: reveal download
    shell.showItemInFolder(assetPath);
  } catch (e) {
    if (!silent) {
      dialog.showMessageBox(parentWindow, {
        type: 'error',
        title: 'Update Failed',
        message: 'Failed to check or apply update.',
        detail: e.message,
        buttons: ['OK'],
      });
    } else {
      console.error('Update check failed:', e.message);
    }
  }
}

module.exports = { runUpdate, detectInstallKind, versionNewer };
