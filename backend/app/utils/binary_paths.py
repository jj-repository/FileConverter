"""
Utility to detect and return paths to bundled binaries (FFmpeg, Pandoc).
Falls back to system binaries if bundled ones are not found.
"""
import os
import sys
import platform
import shutil
from pathlib import Path


def get_bundled_binary_path(binary_name: str) -> str:
    """
    Get the path to a bundled binary (ffmpeg, ffprobe, or pandoc).

    Args:
        binary_name: Name of the binary (ffmpeg, ffprobe, or pandoc)

    Returns:
        Path to the binary (bundled if available, system otherwise)
    """
    # Determine if running in a packaged environment
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        base_path = Path(sys._MEIPASS)
    else:
        # Running in development mode
        base_path = Path(__file__).parent.parent.parent.parent  # Go up to project root

    # Determine platform-specific binary directory and extension
    system = platform.system()
    if system == "Windows":
        bin_dir = base_path / "resources" / "bin" / "windows"
        binary_name_with_ext = f"{binary_name}.exe"
    elif system == "Linux":
        bin_dir = base_path / "resources" / "bin" / "linux"
        binary_name_with_ext = binary_name
    elif system == "Darwin":  # macOS
        bin_dir = base_path / "resources" / "bin" / "macos"
        binary_name_with_ext = binary_name
    else:
        # Unsupported platform, fall back to system binary
        return shutil.which(binary_name) or binary_name

    # Check if bundled binary exists
    bundled_binary = bin_dir / binary_name_with_ext
    if bundled_binary.exists() and bundled_binary.is_file():
        return str(bundled_binary.absolute())

    # Fall back to system binary
    system_binary = shutil.which(binary_name)
    if system_binary:
        return system_binary

    # Last resort: return the binary name and hope it's in PATH
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
