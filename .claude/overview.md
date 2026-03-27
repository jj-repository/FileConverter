# Overview

v1.2.4 — Desktop app for converting files between formats. Electron frontend + FastAPI backend bundled for distribution.

## Files
- `frontend/electron/main.js` — Electron main process
- `frontend/electron/backend-manager.js` — Python backend orchestration
- `frontend/electron/preload.js` — context bridge IPC
- `frontend/src/App.tsx` — main React component
- `frontend/src/components/Common/Toast.tsx` — notification system
- `frontend/src/components/converters/` — converter components
- `frontend/src/i18n/` — internationalization
- `backend/app/main.py` — FastAPI app
- `backend/app/config.py` — config + rate limiting
- `backend/app/routers/` — API endpoints
