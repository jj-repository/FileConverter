# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**FileConverter** is a desktop application for converting files between formats. It features an Electron frontend with React/TypeScript and a FastAPI Python backend. The application bundles the backend with the Electron app for distribution.

**Version:** 1.2.0 (Frontend and Backend synchronized)

## Files Structure

```
FileConverter/
├── frontend/
│   ├── electron/
│   │   ├── main.js              # Electron main process
│   │   ├── backend-manager.js   # Python backend orchestration
│   │   └── preload.js           # Context bridge for IPC
│   ├── src/
│   │   ├── App.tsx              # Main React component
│   │   ├── components/          # React components
│   │   │   ├── Common/
│   │   │   │   └── Toast.tsx    # Notification system
│   │   │   └── converters/      # Converter components
│   │   ├── electron.d.ts        # TypeScript IPC definitions
│   │   └── i18n/                # Internationalization
│   ├── package.json             # Frontend dependencies
│   └── vite.config.ts           # Vite configuration
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration with rate limiting
│   │   └── routers/             # API endpoints
│   └── requirements.txt         # Python dependencies
└── CLAUDE.md                    # This file
```

## Running the Application

```bash
# Frontend development
cd frontend
npm install
npm run dev                    # Vite dev server
npm run electron:dev           # Full Electron + Vite

# Backend development
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Build for distribution
cd frontend
npm run electron:build

# Run tests
npm run test                   # Unit tests
npm run test:e2e               # Playwright E2E tests
```

## Architecture Overview

### Hybrid Architecture

```
Electron (frontend)
    ↕ HTTP (localhost)
FastAPI (backend, bundled)
```

### Frontend Stack
- **Electron**: Desktop shell
- **React 18**: UI framework
- **TypeScript**: Type safety
- **Vite**: Build tool
- **Tailwind CSS**: Styling
- **i18next**: Internationalization

### Backend Stack
- **FastAPI**: Web framework
- **uvicorn**: ASGI server
- **slowapi**: Rate limiting
- **Python converters**: Format-specific logic

### IPC Pattern

```javascript
// main.js - Register handler
ipcMain.handle('action-name', async (event, ...args) => {
  return result;
});

// preload.js - Expose to renderer
contextBridge.exposeInMainWorld('electron', {
  actionName: (...args) => ipcRenderer.invoke('action-name', ...args)
});

// React - Call from component
const result = await window.electron.actionName(args);
```

## Backend Management

**File:** `frontend/electron/backend-manager.js`

**Features:**
- Automatic port detection
- Health check endpoint polling
- Graceful shutdown on app exit
- Process spawning with proper environment

## Update System

**Status:** Partially implemented (startup check with timeout)

**Implemented:**
- Update check on startup (main.js)
- 10-second request timeout
- Version comparison
- Dialog with Download/Later options

**Needed:**
- IPC handlers for check/download
- React context/hook for update state
- Settings storage for auto_check_updates
- Toast notifications for updates

**Reference:** Follow TextCompare pattern for Electron, adapt for React frontend

## Security Features

### Backend
- Rate limiting via slowapi
- CORS configuration
- Input validation

### Frontend
- Context isolation
- Sandbox mode
- No node integration
- CSP headers

## Testing

### Unit Tests (Vitest)
```bash
npm run test           # Run once
npm run test:watch     # Watch mode
npm run test:coverage  # With coverage
npm run test:ui        # Visual UI
```

### E2E Tests (Playwright)
```bash
npm run test:e2e         # Headless
npm run test:e2e:headed  # With browser
npm run test:e2e:debug   # Debug mode
```

## Toast Notification System

**File:** `frontend/src/components/Common/Toast.tsx`

**Usage:**
```typescript
const { showSuccess, showError, showWarning, showInfo, showConfirm } = useToast();

showSuccess('File converted successfully');
showError('Conversion failed');
showConfirm('Are you sure?', { onConfirm: () => {} });
```

**Features:**
- Auto-dismiss with configurable duration
- Action buttons
- Stacked notifications
- Accessibility (ARIA labels)

## Configuration

### Backend (config.py)
- Rate limiting settings
- CORS origins
- File size limits

### Frontend
- Electron window preferences
- Vite dev server port
- Build output directories

## Build Configuration

```json
{
  "build": {
    "appId": "com.fileconverter.app",
    "extraResources": [
      { "from": "../backend", "to": "backend" }
    ],
    "linux": { "target": ["AppImage", "deb"] },
    "win": { "target": ["nsis"] }
  }
}
```

## Known Issues / Technical Debt

1. **Partial update system**: Basic startup check implemented, needs full UI integration
2. **No settings persistence**: No user preferences storage

## Common Development Tasks

### Adding update functionality

1. **Add to package.json:**
```json
{
  "repository": {
    "type": "git",
    "url": "https://github.com/jj-repository/FileConverter.git"
  }
}
```

2. **Add to main.js:**
- Import `https` module
- Add `checkForUpdates()` function
- Add IPC handlers: `check-for-updates`, `download-update`
- Add menu item

3. **Add to preload.js:**
```javascript
contextBridge.exposeInMainWorld('electron', {
  // ... existing
  checkForUpdates: () => ipcRenderer.invoke('check-for-updates'),
  onUpdateAvailable: (callback) => ipcRenderer.on('update-available', callback)
});
```

4. **Add to React:**
- Create UpdateContext/Provider
- Show toast on update available
- Add settings for auto_check_updates

### Adding settings persistence

1. Create `settings.json` in `app.getPath('userData')`
2. Add IPC handlers for load/save
3. Expose via preload
4. Create React settings context

## Platform Notes

### Linux
- Backend uses system Python or bundled
- AppImage is self-contained

### Windows
- Backend bundled as Python dist
- NSIS installer handles installation
