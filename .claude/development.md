# Development

## Run
```bash
# Frontend
cd frontend && npm install
npm run dev              # Vite dev server
npm run electron:dev     # Full Electron + Vite

# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# Build
cd frontend && npm run electron:build
```

## Testing
```bash
npm run test             # Vitest unit tests
npm run test:watch
npm run test:coverage
npm run test:ui
npm run test:e2e         # Playwright
npm run test:e2e:headed
npm run test:e2e:debug
```

## Platform Notes
- Linux: AppImage/deb, system or bundled Python
- Windows: NSIS installer, bundled Python dist

## Common Tasks

### Adding update functionality
1. `package.json`: add `repository.url` → GitHub
2. `main.js`: import `https`, add `checkForUpdates()`, IPC handlers (`check-for-updates`, `download-update`), menu item
3. `preload.js`: expose `checkForUpdates`, `onUpdateAvailable`
4. React: UpdateContext/Provider, toast on update, `auto_check_updates` setting

### Adding settings persistence
1. `settings.json` in `app.getPath('userData')`
2. IPC handlers load/save
3. Expose via preload
4. React settings context
