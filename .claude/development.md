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

### Frontend
```bash
npm run test             # Vitest unit tests
npm run test:watch
npm run test:coverage
npm run test:ui
npm run test:e2e         # Playwright
npm run test:e2e:headed
npm run test:e2e:debug
```

### Backend
```bash
cd backend
pip install -r requirements-dev.txt   # pytest + asyncio + cov + httpx
python -m pytest tests/               # default suite (matrix excluded via -m "not matrix")
```

### Conversion matrix (tests/matrix/)
End-to-end sweep of every `input→output` pair each converter advertises
(~670 pairs, ~50s). Finds broken conversions in one run instead of one upload
at a time. Excluded from the default suite; run explicitly:
```bash
python scripts/run_matrix.py          # full sweep
python scripts/run_matrix.py -k image # one category
```
Writes `tests/matrix/conversion-matrix.md` (pass/fail grid + failure details).
Known-but-unfixed gaps live in `tests/matrix/known_gaps.py` (xfailed, so only
NEW regressions turn the suite red). Fix a converter → rerun the sweep then
`python scripts/gen_known_gaps.py` to shrink the baseline. See
`tests/matrix/README.md` for the current list of gaps found.

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
