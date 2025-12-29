# GitHub Actions Release Build Guide

## Overview

This project uses GitHub Actions to automatically build platform-specific installers for **Linux**, **Windows**, and **macOS**. Each platform gets its own optimized build with only the binaries it needs.

## How It Works

### 🎯 Key Concept: Platform-Specific Builds

Instead of bundling binaries for all platforms in every build (1.2 GB), GitHub Actions builds separately on each platform:

- **Linux build** on `ubuntu-latest` → Only Linux binaries → **~620 MB**
- **Windows build** on `windows-latest` → Only Windows binaries → **~640 MB**
- **macOS build** on `macos-latest` → Only macOS binaries → **~650 MB**

### 📦 What Gets Built

Each platform build includes:
- ✅ Electron app with Chromium runtime
- ✅ React frontend (compiled)
- ✅ Python backend (PyInstaller executable)
- ✅ FFmpeg + FFprobe (platform-specific)
- ✅ Pandoc (platform-specific)

**Total downloads for users:**
- Linux: AppImage (~620 MB) or .deb package
- Windows: .exe installer (~640 MB)
- macOS: .dmg disk image (~650 MB)

## Workflow Triggers

The build workflow runs automatically when you:

### 1. Push a Version Tag

```bash
git tag v1.0.0
git push origin v1.0.0
```

This triggers:
1. Builds on all 3 platforms (in parallel)
2. Creates a GitHub Release
3. Uploads all installers to the release

### 2. Manual Trigger

Go to GitHub Actions → "Build and Release" → "Run workflow"

## Build Process Breakdown

### Step 1: Checkout & Setup
- Checks out your code
- Installs Node.js 20
- Installs Python 3.11

### Step 2: Build Frontend
```bash
cd frontend
npm ci
npm run build
```
Creates the React production build

### Step 3: Setup Python Backend
```bash
cd backend
python -m venv venv
pip install -r requirements.txt
pip install pyinstaller
```

### Step 4: Build Backend Executable
```bash
pyinstaller backend-server.spec --clean
```
Creates standalone Python executable (~31 MB)

### Step 5: Download Platform Binaries

**On Linux (ubuntu-latest):**
```bash
wget ffmpeg-release-amd64-static.tar.xz
wget pandoc-3.6.1-linux-amd64.tar.gz
# Extract to resources/bin/linux/
```

**On Windows (windows-latest):**
```powershell
Invoke-WebRequest ffmpeg-master-latest-win64-gpl.zip
Invoke-WebRequest pandoc-3.6.1-windows-x86_64.zip
# Extract to resources/bin/windows/
```

**On macOS (macos-latest):**
```bash
wget ffmpeg from evermeet.cx
wget pandoc-3.6.1-macOS.zip
# Extract to resources/bin/macos/
```

### Step 6: Build Electron Package

**Linux:**
```bash
electron-builder --linux --publish never
```
Creates: `FileConverter-1.0.0.AppImage` and `fileconverter_1.0.0_amd64.deb`

**Windows:**
```bash
electron-builder --win --publish never
```
Creates: `FileConverter Setup 1.0.0.exe`

**macOS:**
```bash
electron-builder --mac --publish never
```
Creates: `FileConverter-1.0.0.dmg` and `FileConverter-1.0.0-mac.zip`

### Step 7: Upload Artifacts
Each platform uploads its build artifacts to GitHub Actions

### Step 8: Create Release (on tags only)
Downloads all artifacts and creates a GitHub Release with all installers

## Using the Workflow

### First-Time Setup

1. **Push your code to GitHub:**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/FileConverter.git
git push -u origin main
```

2. **Create your first release:**
```bash
# Make sure everything is committed
git tag -a v1.0.0 -m "First release"
git push origin v1.0.0
```

3. **Watch the build:**
   - Go to your GitHub repo → Actions tab
   - Watch the "Build and Release" workflow run
   - It will build on all 3 platforms simultaneously

4. **Check the release:**
   - Go to Releases tab
   - You'll see `v1.0.0` with 5-6 downloadable files
   - Users can download the installer for their platform

### Subsequent Releases

```bash
# Make your changes, test them, commit
git add .
git commit -m "Add new features"

# Update version in package.json
# frontend/package.json: "version": "1.1.0"

# Create and push tag
git tag -a v1.1.0 -m "Version 1.1.0"
git push origin v1.1.0

# GitHub Actions automatically builds and publishes!
```

## What Users Download

### Linux Users
Can choose between:
- **AppImage** (recommended): Single executable, no installation needed
  - Download, make executable, run: `./FileConverter-1.0.0.AppImage`
- **DEB package**: For Debian/Ubuntu users
  - Install: `sudo dpkg -i fileconverter_1.0.0_amd64.deb`

### Windows Users
- **EXE installer**: Standard Windows installer
  - Download and run: `FileConverter Setup 1.0.0.exe`
  - Installs to Program Files, creates desktop shortcut

### macOS Users
Can choose between:
- **DMG** (recommended): Drag-and-drop installer
  - Open DMG, drag FileConverter to Applications
- **ZIP**: Direct app bundle
  - Extract and copy to Applications

## Zero Dependencies Required!

Users don't need to install:
- ❌ Python
- ❌ Node.js
- ❌ FFmpeg
- ❌ Pandoc
- ❌ Any other dependencies

Everything is bundled! Just download and run.

## Build Times

Typical build times on GitHub Actions:
- Linux build: ~10-15 minutes
- Windows build: ~10-15 minutes
- macOS build: ~15-20 minutes

Total workflow: ~15-20 minutes (runs in parallel)

## Troubleshooting

### Build fails on Python setup
**Solution:** Make sure `backend/requirements.txt` is up to date:
```bash
cd backend
source venv/bin/activate
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update requirements"
```

### Build fails on frontend build
**Solution:** Check that `package-lock.json` is committed:
```bash
cd frontend
git add package-lock.json
git commit -m "Add package-lock.json"
```

### Binary downloads fail
**Solution:** Update URLs in `.github/workflows/build-release.yml` if FFmpeg/Pandoc release links change

### Release not created
**Solution:** Make sure you pushed a tag (not just a commit):
```bash
git tag v1.0.0
git push origin v1.0.0  # Must push the tag!
```

## Cost Considerations

GitHub Actions free tier (for public repos):
- ✅ 2,000 minutes/month free
- ✅ Unlimited for public repositories
- This workflow uses ~45 minutes per release
- You can do ~44 releases per month for free!

For private repos:
- 2,000 minutes/month free, then paid
- ~45 minutes per release = ~44 free releases

## Advanced: Manual Build Locally

If you want to build locally for testing:

**Linux:**
```bash
cd frontend
npm run build
cd ../backend
pyinstaller backend-server.spec --clean
cd ../frontend
npx electron-builder --linux --dir
```

**The built app is in:** `frontend/dist-electron/linux-unpacked/`

## File Structure in GitHub Release

After the workflow runs, your GitHub Release will contain:

```
v1.0.0
├── FileConverter-1.0.0.AppImage          (Linux - 620 MB)
├── fileconverter_1.0.0_amd64.deb         (Linux - 620 MB)
├── FileConverter Setup 1.0.0.exe         (Windows - 640 MB)
├── FileConverter-1.0.0.dmg               (macOS - 650 MB)
└── FileConverter-1.0.0-mac.zip           (macOS - 650 MB)
```

Total release storage: ~3.2 GB (but users only download one!)

## Summary

✅ **No more bundling all platforms** - Each build is platform-specific
✅ **Automated releases** - Just push a tag
✅ **Professional installers** - AppImage, DEB, EXE, DMG
✅ **Zero user dependencies** - Everything bundled
✅ **Free for public repos** - GitHub Actions provides compute
✅ **Parallel builds** - All platforms build simultaneously

Your users get a simple download → install → run experience! 🚀
