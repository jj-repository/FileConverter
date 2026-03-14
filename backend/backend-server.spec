# -*- mode: python ; coding: utf-8 -*-

import os

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

a = Analysis(
    ['run_server.py'],
    pathex=[os.getcwd()],
    binaries=[],
    datas=app_datas + static_dirs,
    hiddenimports=[
        'uvicorn', 'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto',
        'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl', 'uvicorn.protocols.http.httptools_impl',
        'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.websockets_impl',
        'uvicorn.lifespan', 'uvicorn.lifespan.on', 'uvicorn.lifespan.off',
        'uvicorn.main', 'uvicorn.config', 'uvicorn.server',
        'multipart', 'python_multipart',
        'pydantic', 'pydantic_settings', 'pydantic_core',
        'pydantic.deprecated', 'pydantic.deprecated.decorator',
        'fastapi', 'starlette',
        'app.main', 'app.config',
        'app.routers.image', 'app.routers.video', 'app.routers.audio',
        'app.routers.document', 'app.routers.batch', 'app.routers.websocket',
        'app.routers.data', 'app.routers.archive', 'app.routers.spreadsheet',
        'app.routers.subtitle', 'app.routers.ebook', 'app.routers.font',
        'app.routers.cache', 'app.routers.version',
        'app.services.image_converter', 'app.services.video_converter',
        'app.services.audio_converter', 'app.services.document_converter',
        'app.services.batch_converter',
        'app.utils.binary_paths', 'app.utils.file_handler', 'app.utils.validation',
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
