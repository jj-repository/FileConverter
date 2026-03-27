# Configuration

## Backend (config.py)
- Rate limiting settings
- CORS origins
- File size limits

## Frontend
- Electron window preferences
- Vite dev server port
- Build output directories

## Build (package.json)
```json
{
  "build": {
    "appId": "com.fileconverter.app",
    "extraResources": [{ "from": "../backend", "to": "backend" }],
    "linux": { "target": ["AppImage", "deb"] },
    "win": { "target": ["nsis"] }
  }
}
```
