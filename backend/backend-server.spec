# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all app files
app_datas = []
app_dir = os.path.join(os.getcwd(), 'app')
for root, dirs, files in os.walk(app_dir):
    # Skip __pycache__ directories
    if '__pycache__' in root:
        continue
    for file in files:
        if file.endswith('.py') or file.endswith('.json'):
            src = os.path.join(root, file)
            # Get the relative path from the current directory
            dst = os.path.dirname(os.path.relpath(src, os.getcwd()))
            app_datas.append((src, dst))

# Add static directories (will be created at runtime)
static_dirs = [
    ('app/static', 'app/static'),
]

# Collect data files from dependencies
fastapi_datas = collect_data_files('fastapi')
pydantic_datas = collect_data_files('pydantic')
pydantic_core_datas = collect_data_files('pydantic_core')

# Collect all uvicorn submodules
uvicorn_imports = collect_submodules('uvicorn')

a = Analysis(
    ['run_server.py'],
    pathex=[os.getcwd()],
    binaries=[],
    datas=app_datas + static_dirs + fastapi_datas + pydantic_datas + pydantic_core_datas,
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'multipart',
        'python_multipart',
        'pydantic_settings',
        'pydantic.deprecated',
        'pydantic.deprecated.decorator',
        'app.main',
        'app.config',
        'app.routers.image',
        'app.routers.video',
        'app.routers.audio',
        'app.routers.document',
        'app.routers.batch',
        'app.routers.websocket',
        'app.services.image_converter',
        'app.services.video_converter',
        'app.services.audio_converter',
        'app.services.document_converter',
        'app.services.batch_converter',
        'app.utils.binary_paths',
        'app.utils.file_handler',
        'app.utils.validation',
    ] + uvicorn_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='backend-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
