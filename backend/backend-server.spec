# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.utils.hooks import collect_all, collect_submodules

# Collect all app files
app_datas = []
app_dir = os.path.join(os.getcwd(), 'app')
for root, dirs, files in os.walk(app_dir):
    if '__pycache__' in root:
        continue
    for file in files:
        if file.endswith('.py') or file.endswith('.json'):
            src = os.path.join(root, file)
            dst = os.path.dirname(os.path.relpath(src, os.getcwd()))
            app_datas.append((src, dst))

# Add static directories
static_dirs = [
    ('app/static', 'app/static'),
]

# Runtime third-party packages used by the backend. collect_all pulls
# submodules + data files + binaries for each, which is necessary because
# PyInstaller's static analysis misses re-exports and dynamic imports.
RUNTIME_PACKAGES = [
    # Web stack
    'fastapi', 'starlette', 'slowapi', 'uvicorn', 'websockets',
    'pydantic', 'pydantic_settings', 'pydantic_core',
    # File IO / async
    'aiofiles', 'multipart',
    # Image
    'PIL', 'pillow_heif', 'cairosvg',
    # Data / spreadsheets
    'pandas', 'openpyxl', 'odf',
    # Archive
    'py7zr',
    # Subtitles / media
    'pysubs2', 'ffmpeg',
    # Document / PDF / ebook / markdown
    'pypandoc', 'docx', 'pypdf', 'markdown', 'ebooklib', 'bs4', 'bleach',
    'lxml', 'reportlab',
    # Fonts
    'fontTools', 'brotli',
    # Serialization / security
    'yaml', 'toml', 'defusedxml', 'magic',
]

collected_datas = []
collected_binaries = []
collected_hidden = []

for pkg in RUNTIME_PACKAGES:
    try:
        d, b, h = collect_all(pkg)
        collected_datas += d
        collected_binaries += b
        collected_hidden += h
    except Exception as e:
        # Some modules may not be importable during spec build; fall back to submodules
        print(f"[spec] collect_all({pkg!r}) failed: {e}; falling back to collect_submodules")
        try:
            collected_hidden += collect_submodules(pkg)
        except Exception as e2:
            print(f"[spec] collect_submodules({pkg!r}) also failed: {e2}; skipping")

a = Analysis(
    ['run_server.py'],
    pathex=[os.getcwd()],
    binaries=collected_binaries,
    datas=app_datas + static_dirs + collected_datas,
    hiddenimports=[
        *collected_hidden,
        *collect_submodules('app'),
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'IPython', 'jupyter'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='backend-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='backend-server',
)
