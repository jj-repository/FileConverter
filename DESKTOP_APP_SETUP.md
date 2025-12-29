# FileConverter Desktop App - Setup Guide

This guide explains how to run and build the FileConverter desktop application using Electron.

## Overview

FileConverter is now a **cross-platform desktop application** built with:
- **Electron** - Desktop app framework
- **React + TypeScript** - Frontend UI
- **FastAPI (Python)** - Backend server
- **Tailwind CSS** - Styling

The desktop app bundles both the frontend and backend into a single executable that runs on Windows, macOS, and Linux.

## Prerequisites

### System Requirements
- **Node.js** 18+ (for Electron and frontend)
- **Python** 3.10+ (for backend)
- **FFmpeg** (for video/audio conversion)
- **Pandoc** (for document conversion)

### Install System Dependencies

**Linux (Ubuntu/Debian):**
```bash
sudo apt install ffmpeg pandoc python3 python3-pip nodejs npm
```

**macOS:**
```bash
brew install ffmpeg pandoc python node
```

**Windows:**
- Download and install [FFmpeg](https://ffmpeg.org/download.html)
- Download and install [Pandoc](https://pandoc.org/installing.html)
- Download and install [Python](https://www.python.org/downloads/)
- Download and install [Node.js](https://nodejs.org/)

## Development Setup

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

## Running in Development Mode

### Option 1: Run Everything at Once

```bash
cd frontend
npm run electron:dev
```

This command will:
1. Start the Vite development server (frontend)
2. Wait for it to be ready
3. Launch Electron with the backend server

The app will open automatically with hot-reload enabled for the frontend.

### Option 2: Run Components Separately

**Terminal 1 - Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 2 - Backend:**
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 3 - Electron:**
```bash
cd frontend
npx electron .
```

## Building for Production

### 1. Build the Frontend

```bash
cd frontend
npm run build
```

This creates an optimized production build in `frontend/dist/`.

### 2. Package the Desktop App

```bash
cd frontend
npm run electron:build
```

This will:
1. Build the frontend
2. Package the Electron app with electron-builder
3. Bundle the Python backend
4. Create platform-specific installers

### Output Locations

Packaged apps will be in `frontend/dist-electron/`:

- **Windows**: `.exe` installer
- **macOS**: `.dmg` installer and `.app` bundle
- **Linux**: `.AppImage` and `.deb` packages

### Platform-Specific Builds

To build for a specific platform:

```bash
# Windows
npm run electron:build -- --win

# macOS
npm run electron:build -- --mac

# Linux
npm run electron:build -- --linux
```

## App Structure

```
FileConverter/
├── frontend/
│   ├── electron/              # Electron main process files
│   │   ├── main.js           # Main Electron process
│   │   ├── preload.js        # Preload script
│   │   └── backend-manager.js # Backend process manager
│   ├── src/                   # React frontend source
│   ├── dist/                  # Built frontend (after npm run build)
│   ├── dist-electron/         # Packaged apps (after electron:build)
│   └── package.json
│
├── backend/
│   ├── app/                   # FastAPI application
│   ├── venv/                  # Python virtual environment
│   └── requirements.txt
│
└── DESKTOP_APP_SETUP.md      # This file
```

## How It Works

### Architecture

1. **Electron Main Process** (`electron/main.js`):
   - Creates the application window
   - Manages the backend server lifecycle
   - Handles IPC communication

2. **Backend Manager** (`electron/backend-manager.js`):
   - Spawns the FastAPI server as a child process
   - Monitors server health
   - Manages server shutdown

3. **Frontend** (React App):
   - Loads in the Electron window
   - Communicates with backend via HTTP/WebSocket
   - Same code as the web version

### Backend Integration

- In **development**: Uses the venv Python from `backend/venv`
- In **production**: Bundles the backend code and uses system Python
- The backend server runs on `localhost:8000` by default
- Backend automatically starts when the app launches
- Backend automatically stops when the app closes

## Troubleshooting

### Backend fails to start

**Error**: "Python not found"
- **Solution**: Ensure Python 3.10+ is installed and in PATH
- **Development**: Create the venv: `cd backend && python3 -m venv venv`
- **Production**: Install Python on the target system

### Port already in use

**Error**: "Port 8000 is already in use"
- **Solution**: The backend manager automatically finds an available port
- If issues persist, kill the process using port 8000

### FFmpeg/Pandoc not found

**Error**: Conversion fails
- **Solution**: Install FFmpeg and Pandoc (see Prerequisites)
- Ensure they are in the system PATH

### Build fails on macOS

**Error**: Code signing issues
- **Solution**: Set `CSC_IDENTITY_AUTO_DISCOVERY=false` in environment
- Or configure proper code signing in `package.json`

### Build fails on Linux

**Error**: Missing dependencies
- **Solution**: Install required build tools:
  ```bash
  sudo apt install -y rpm fakeroot dpkg
  ```

## Development Tips

### Hot Reload

- Frontend changes auto-reload (Vite HMR)
- Backend changes require manual restart
- Electron changes require app restart

### Debugging

**Frontend debugging:**
- DevTools open automatically in development
- Use Chrome DevTools as normal

**Backend debugging:**
- Backend logs appear in the terminal
- Check `[Backend]` prefixed console output

**Electron debugging:**
- Use `console.log()` in main.js
- Check the terminal where you ran `npm run electron:dev`

### Opening DevTools

DevTools are automatically opened in development mode. To toggle them:
- **macOS**: `Cmd + Option + I`
- **Windows/Linux**: `Ctrl + Shift + I`

## Distribution

### Creating Installers

The `electron:build` command creates platform-specific installers:

**Windows**:
- NSIS installer (.exe) - Install wizard
- Portable executable available

**macOS**:
- DMG image (.dmg) - Drag-and-drop installer
- .app bundle

**Linux**:
- AppImage (.AppImage) - Universal, no installation required
- Debian package (.deb) - For Ubuntu/Debian

### App Signing (Production)

For production distribution:

**macOS**:
- Requires Apple Developer certificate
- Configure in `package.json` under `build.mac`

**Windows**:
- Requires code signing certificate
- Configure in `package.json` under `build.win`

## Next Steps

1. **Icons**: Replace placeholder icons in `frontend/build/` with proper app icons
2. **Auto-update**: Implement auto-update functionality with electron-updater
3. **Python bundling**: Bundle Python runtime for true standalone builds
4. **Installer customization**: Customize installer UI and options

## Resources

- [Electron Documentation](https://www.electronjs.org/docs)
- [electron-builder Documentation](https://www.electron.build/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vite Documentation](https://vitejs.dev/)

## Support

If you encounter issues:
1. Check this documentation
2. Review console output for errors
3. Ensure all prerequisites are installed
4. Check that ports 5173 and 8000 are available
