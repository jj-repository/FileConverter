# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for the FileConverter backend.

The set of third-party packages to bundle is derived from requirements.txt —
not hand-maintained here. For each declared distribution we resolve its
top-level import names via importlib.metadata, then run collect_submodules
and collect_data_files on each. This keeps the frozen bundle in sync with
the declared runtime dependencies automatically; adding a dep to
requirements.txt is sufficient.
"""

import os
import re
from importlib.metadata import PackageNotFoundError, distribution

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

HERE = os.getcwd()
REQ_FILE = os.path.join(HERE, 'requirements.txt')


def parse_requirements(path):
    name_re = re.compile(r'^\s*([A-Za-z0-9_.\-]+)')
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.split('#', 1)[0].strip()
            if not line or line.startswith('-'):
                continue
            m = name_re.match(line)
            if m:
                yield m.group(1)


def top_level_packages(dist_name):
    """Return top-level import names for an installed distribution."""
    try:
        dist = distribution(dist_name)
    except PackageNotFoundError:
        print(f"[spec] not installed, skipping: {dist_name}")
        return []

    tl = dist.read_text('top_level.txt')
    if tl:
        return [n.strip() for n in tl.splitlines()
                if n.strip() and not n.startswith('_')]

    names = set()
    for f in dist.files or []:
        parts = f.parts
        if not parts:
            continue
        head = parts[0]
        if head.endswith(('.dist-info', '.egg-info')):
            continue
        names.add(head[:-3] if head.endswith('.py') else head)
    return sorted(n for n in names if not n.startswith('_'))


hidden = []
datas_from_deps = []
seen = set()
for dist_name in parse_requirements(REQ_FILE):
    for pkg in top_level_packages(dist_name):
        if pkg in seen:
            continue
        seen.add(pkg)
        try:
            hidden += collect_submodules(pkg)
        except Exception as e:
            print(f"[spec] collect_submodules({pkg!r}) failed: {e}")
        try:
            datas_from_deps += collect_data_files(pkg)
        except Exception as e:
            print(f"[spec] collect_data_files({pkg!r}) failed: {e}")

hidden += collect_submodules('app')

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


a = Analysis(
    ['run_server.py'],
    pathex=[HERE],
    binaries=[],
    datas=app_datas + static_dirs + datas_from_deps,
    hiddenimports=hidden,
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
