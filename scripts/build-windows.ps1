# Build FileConverter for Windows locally.
# Mirrors .github/workflows/build-release.yml (Windows path) without Defender/runner
# variance. Run from the repo root:  .\scripts\build-windows.ps1
#
# Requires on PATH: python 3.11, node 20+, npm, git, gh (GitHub CLI, authenticated).
# Output: frontend\dist-electron\FileConverter-Setup.exe (+ FileConverter.exe portable).

$ErrorActionPreference = "Stop"

function Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Step "Prereq check"
foreach ($cmd in @("python", "node", "npm", "git", "gh")) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        throw "$cmd not found on PATH"
    }
}
$pyVer = (python --version) 2>&1
if ($pyVer -notmatch "3\.11") {
    Write-Warning "Python $pyVer — CI uses 3.11. Continuing, but build may diverge."
}

Step "Frontend deps + build"
Push-Location frontend
npm ci
npm run build
Pop-Location

Step "Backend venv + deps"
Push-Location backend
if (Test-Path venv) { Remove-Item -Recurse -Force venv }
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller==6.14.2

Step "PyInstaller build"
if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path dist)  { Remove-Item -Recurse -Force dist }
pyinstaller backend-server.spec --clean --log-level INFO

Step "Smoke-test frozen backend"
.\dist\backend-server\backend-server.exe --smoke-test
if ($LASTEXITCODE -ne 0) { throw "Smoke-test failed (exit $LASTEXITCODE)" }

deactivate
Pop-Location

Step "Download FFmpeg + Pandoc + Typst to resources\bin\windows"
New-Item -ItemType Directory -Force -Path resources\bin\windows | Out-Null
Push-Location (New-Item -ItemType Directory -Force -Path ".build-tmp").FullName

# FFmpeg (pinned autobuild + sha256 verify)
$btbnTag = "autobuild-2026-04-18-13-04"
$ffmpegBase = "ffmpeg-n7.1.3-45-g2d6ee37238-win64-gpl-7.1"
$ffmpegZip = "$ffmpegBase.zip"
gh release download $btbnTag --repo BtbN/FFmpeg-Builds -p $ffmpegZip -p "checksums.sha256" --clobber
Rename-Item $ffmpegZip ffmpeg.zip -Force
$expectedLine = Select-String -Path checksums.sha256 -Pattern ([regex]::Escape($ffmpegZip)) | Select-Object -First 1
if (-not $expectedLine) { throw "FFmpeg checksum not found" }
$expected = $expectedLine.Line.Split()[0].ToUpper()
$actual = (Get-FileHash ffmpeg.zip -Algorithm SHA256).Hash
if ($actual -ne $expected) { throw "FFmpeg SHA256 mismatch: expected $expected got $actual" }
Expand-Archive -Path ffmpeg.zip -DestinationPath . -Force
Copy-Item "$ffmpegBase\bin\ffmpeg.exe"  "$repoRoot\resources\bin\windows\" -Force
Copy-Item "$ffmpegBase\bin\ffprobe.exe" "$repoRoot\resources\bin\windows\" -Force

# Pandoc
gh release download 3.6.1 --repo jgm/pandoc -p "pandoc-3.6.1-windows-x86_64.zip" --clobber
Rename-Item "pandoc-3.6.1-windows-x86_64.zip" pandoc.zip -Force
Expand-Archive -Path pandoc.zip -DestinationPath . -Force
Copy-Item "pandoc-3.6.1\pandoc.exe" "$repoRoot\resources\bin\windows\" -Force

# Typst
gh release download "v0.14.2" --repo typst/typst -p "typst-x86_64-pc-windows-msvc.zip" --clobber
Rename-Item "typst-x86_64-pc-windows-msvc.zip" typst.zip -Force
Expand-Archive -Path typst.zip -DestinationPath . -Force
Copy-Item "typst-x86_64-pc-windows-msvc\typst.exe" "$repoRoot\resources\bin\windows\" -Force

Pop-Location
Remove-Item -Recurse -Force .build-tmp

Step "Electron build (Windows)"
Push-Location frontend
npx electron-builder --win --publish never
Pop-Location

Step "Done"
Get-ChildItem frontend\dist-electron\*.exe | Format-Table Name, @{N="MB";E={[math]::Round($_.Length/1MB,1)}}
Write-Host "`nNext: upload these .exe files to the v1.16.0 GitHub release." -ForegroundColor Green
