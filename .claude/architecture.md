# Architecture

## Design
```
Electron (React/TS frontend)
    ↕ HTTP localhost
FastAPI (Python backend, bundled)
```

## Frontend Stack
Electron, React 18, TypeScript, Vite, Tailwind CSS, i18next

## Backend Stack
FastAPI, uvicorn, slowapi (rate limiting), Python converters

## IPC Pattern
```javascript
// main.js
ipcMain.handle('action-name', async (event, ...args) => result);
// preload.js
contextBridge.exposeInMainWorld('electron', {
  actionName: (...args) => ipcRenderer.invoke('action-name', ...args)
});
// React
const result = await window.electron.actionName(args);
```

## Backend Manager (`frontend/electron/backend-manager.js`)
- Automatic port detection
- Health check endpoint polling
- Graceful shutdown on app exit
- Process spawning with proper environment

## Toast System (`frontend/src/components/Common/Toast.tsx`)
```typescript
const { showSuccess, showError, showWarning, showInfo, showConfirm } = useToast();
showSuccess('File converted successfully');
showConfirm('Are you sure?', { onConfirm: () => {} });
```
Auto-dismiss, action buttons, stacked, ARIA labels.
