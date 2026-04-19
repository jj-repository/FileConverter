# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for the FileConverter backend.

Correctness is enforced by the --smoke-test step in CI (see run_server.py
and .github/workflows/build-release.yml): after PyInstaller produces the
frozen exe, the CI runs `backend-server --smoke-test`, which imports
app.main. Any ImportError fails the build before it reaches a user.

That smoke test lets this spec stay minimal. We only run collect_submodules
on packages known to use dynamic/re-exported imports (web stack, ebook
tooling). Heavy packages like pandas/PIL/lxml are handled by PyInstaller's
built-in hooks, so we don't pay for walking them ourselves — doing so blew
the Windows 60-minute step budget.
"""

import os

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

HERE = os.getcwd()

# Bundle our own package sources and any JSON config they ship.
app_datas = []
app_dir = os.path.join(HERE, 'app')
for root, dirs, files in os.walk(app_dir):
    if '__pycache__' in root:
        continue
    for f in files:
        if f.endswith(('.py', '.json')):
            src = os.path.join(root, f)
            dst = os.path.dirname(os.path.relpath(src, HERE))
            app_datas.append((src, dst))

static_dirs = [('app/static', 'app/static')]

# Packages with dynamic or re-exported imports PyInstaller's static
# analyzer misses. Expand only if smoke-test surfaces a new ModuleNotFound.
SUBMODULE_PACKAGES = [
    'fastapi', 'starlette', 'slowapi', 'uvicorn',
    'pydantic', 'pydantic_settings', 'pydantic_core',
    'websockets',
    'ebooklib',
]

# Packages that ship non-Python data files (templates, fonts, schemas)
# which must land next to their code in the frozen tree.
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
    pathex=[HERE],
    binaries=[],
    datas=app_datas + static_dirs + collected_datas,
    hiddenimports=[
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
