# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

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

# Third-party packages whose submodules must be included (PyInstaller's
# static analyzer misses re-exports and dynamic imports).
SUBMODULE_PACKAGES = [
    'fastapi', 'starlette', 'slowapi', 'uvicorn',
    'pydantic', 'pydantic_settings', 'pydantic_core',
    'websockets',
]

# Packages that ship data files (templates, fonts, schemas) that must be
# shipped alongside their code.
DATA_PACKAGES = [
    'openpyxl', 'reportlab', 'ebooklib', 'odf',
]

collected_hidden = []
for pkg in SUBMODULE_PACKAGES:
    try:
        collected_hidden += collect_submodules(pkg)
    except Exception as e:
        print(f"[spec] collect_submodules({pkg!r}) failed: {e}")

collected_datas = []
for pkg in DATA_PACKAGES:
    try:
        collected_datas += collect_data_files(pkg)
    except Exception as e:
        print(f"[spec] collect_data_files({pkg!r}) failed: {e}")

a = Analysis(
    ['run_server.py'],
    pathex=[os.getcwd()],
    binaries=[],
    datas=app_datas + static_dirs + collected_datas,
    hiddenimports=[
        # Explicit for packages where submodules are known minimal
        'aiofiles', 'multipart', 'python_multipart',
        'bleach', 'bs4', 'markdown',
        'py7zr', 'pypdf', 'pypandoc',
        'docx', 'ebooklib',
        'pysubs2', 'ffmpeg',
        'PIL', 'pillow_heif',
        'pandas', 'openpyxl', 'odf',
        'reportlab', 'fontTools', 'brotli',
        'yaml', 'toml', 'defusedxml', 'magic', 'lxml',
        *collected_hidden,
        *collect_submodules('app'),
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'scipy', 'IPython', 'jupyter',
        'pytest', 'pandas.tests', 'pandas.io.formats.style',
    ],
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
