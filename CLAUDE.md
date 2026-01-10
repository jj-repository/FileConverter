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
- Admin key authentication for cache endpoints
- Symlink path traversal protection in archive extraction
- JSON parsing error handling in data converter

### Frontend
- Context isolation
- Sandbox mode
- No node integration
- CSP headers
- Secure default host binding (127.0.0.1)

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

## Recent Fixes (January 2026)

- Fixed audio converter stderr handling to prevent potential deadlocks on timeout
- Strengthened symlink path traversal protection in archive extraction
- Changed run_server.py default host from 0.0.0.0 to 127.0.0.1 for security
- Added admin authentication to /api/cache/info endpoint
- Added proper JSON parsing error handling in data converter
- Fixed SVG temp file not being cleaned up after image conversion

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

---

## Review Status

> **Last Full Review:** 2026-01-10
> **Status:** ✅ Production Ready

### Security Review ✅
- [x] Path traversal protection in archive extraction
- [x] Symlink attack prevention (tar/zip extraction)
- [x] Input validation on all API endpoints
- [x] Rate limiting configured
- [x] CORS properly configured
- [x] Admin authentication on sensitive endpoints
- [x] Context isolation in Electron
- [x] Sandbox mode enabled
- [x] No nodeIntegration
- [x] Localhost-only backend binding (127.0.0.1)

### Backend Review ✅
- [x] All converters handle errors gracefully
- [x] Subprocess stderr properly consumed (prevents deadlocks)
- [x] Timeouts on all external operations
- [x] JSON parsing errors handled
- [x] File size limits enforced

### Frontend Review ✅
- [x] TypeScript types complete
- [x] React components properly structured
- [x] Toast notifications for user feedback
- [x] i18n implemented

## Quality Standards

**Target:** Desktop file converter - reliable, secure, user-friendly

| Aspect | Standard | Status |
|--------|----------|--------|
| Security | No file system escapes, safe subprocess handling | ✅ Met |
| Reliability | All converters handle edge cases | ✅ Met |
| UX | Clear feedback on success/failure | ✅ Met |
| Performance | Reasonable conversion times | ✅ Met |
| Documentation | CLAUDE.md current | ✅ Met |

## Intentional Design Decisions

| Decision | Rationale |
|----------|-----------|
| Separate backend (FastAPI) | Python has better libraries for file conversion than Node.js |
| HTTP between frontend/backend | Simpler than IPC; backend could be used standalone |
| No settings persistence yet | MVP feature; not critical for core functionality |
| Update opens browser | Simpler than in-app download; avoids signature verification complexity |
| Bundled Python backend | Self-contained distribution; no Python install required |

## Won't Fix (Accepted Limitations)

| Issue | Reason |
|-------|--------|
| No settings UI | Low priority; works fine with defaults |
| Update system partial | Opens releases page; full auto-update adds complexity |
| Large app size (~200MB) | Electron + Python runtime; acceptable for desktop app |
| Backend startup delay | Health check polling; typically <2 seconds |

## Completed Optimizations

- ✅ Subprocess stderr handling (prevents deadlocks)
- ✅ Symlink traversal protection
- ✅ Secure default host binding
- ✅ Admin auth on cache endpoints
- ✅ JSON error handling

**DO NOT further optimize:** Conversion speed is limited by underlying tools (ffmpeg, etc.). The architecture is appropriate for the use case.
