"""
Utility to detect and return paths to bundled binaries (FFmpeg, Pandoc).
Falls back to system binaries if bundled ones are not found.
"""

import platform
import shutil
import sys
from pathlib import Path


_PLATFORM_DIRS = {
    "Windows": ("windows", ".exe"),
    "Linux": ("linux", ""),
    "Darwin": ("macos", ""),
}


def get_bundled_binary_path(binary_name: str) -> str:
    """
    Get the path to a bundled binary (ffmpeg, ffprobe, pandoc, typst).

    Looks for the binary in a list of candidate roots:
      - PyInstaller _MEIPASS (when binaries are bundled into the spec).
      - Electron extraResources, three levels above _MEIPASS
        (<install>/resources/backend/dist/backend-server/ -> <install>/resources/).
      - Project root (dev mode).

    Falls back to PATH lookup, then the bare name.
    """
    info = _PLATFORM_DIRS.get(platform.system())
    if info is None:
        return shutil.which(binary_name) or binary_name
    platform_dir, ext = info
    binary_filename = f"{binary_name}{ext}"

    candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        mei = Path(sys._MEIPASS)
        candidates.append(mei)
        candidates.append(mei.parent.parent.parent)
    else:
        candidates.append(Path(__file__).parent.parent.parent.parent)

    for root in candidates:
        bundled = root / "resources" / "bin" / platform_dir / binary_filename
        if bundled.exists() and bundled.is_file():
            return str(bundled.absolute())

    system_binary = shutil.which(binary_name)
    if system_binary:
        return system_binary

    return binary_name


def get_ffmpeg_path() -> str:
    """Get the path to ffmpeg binary."""
    return get_bundled_binary_path("ffmpeg")


def get_ffprobe_path() -> str:
    """Get the path to ffprobe binary."""
    return get_bundled_binary_path("ffprobe")


def get_pandoc_path() -> str:
    """Get the path to pandoc binary."""
    return get_bundled_binary_path("pandoc")


def get_typst_path() -> str:
    """Get the path to typst binary (used by pandoc as --pdf-engine)."""
    return get_bundled_binary_path("typst")
