import logging
import re
import uuid
from pathlib import Path
from urllib.parse import quote

import aiofiles
from fastapi import UploadFile

from app.config import settings

logger = logging.getLogger(__name__)


def make_safe_filename(filename: str) -> str:
    """
    Create a safe filename by removing/replacing dangerous characters.

    SECURITY: Removes characters that could cause issues in Content-Disposition
    headers or filesystem operations.
    """
    # Remove null bytes and control characters
    filename = re.sub(r"[\x00-\x1f\x7f]", "", filename)
    # Remove/replace characters problematic in headers
    filename = filename.replace('"', "'").replace("\\", "_")
    # Keep only safe characters for filenames
    return filename


def make_content_disposition(filename: str, disposition: str = "attachment") -> str:
    """
    Create a properly encoded Content-Disposition header value.

    Uses RFC 5987 encoding for non-ASCII filenames to ensure compatibility
    across browsers and prevent header injection.

    Args:
        filename: The filename to include in the header
        disposition: Either "attachment" or "inline"

    Returns:
        Properly formatted Content-Disposition header value
    """
    # Sanitize the filename first
    safe_filename = make_safe_filename(filename)

    # Check if filename contains non-ASCII characters
    try:
        safe_filename.encode("ascii")
        is_ascii = True
    except UnicodeEncodeError:
        is_ascii = False

    if is_ascii:
        # Simple ASCII filename - use standard format with proper escaping
        # Escape any remaining special characters
        escaped = safe_filename.replace("\\", "\\\\").replace('"', '\\"')
        return f'{disposition}; filename="{escaped}"'
    else:
        # Non-ASCII filename - use RFC 5987 encoding
        # Provide both filename (ASCII fallback) and filename* (UTF-8)
        ascii_fallback = safe_filename.encode("ascii", "replace").decode("ascii")
        ascii_fallback = ascii_fallback.replace("\\", "_").replace('"', "'")
        utf8_encoded = quote(safe_filename, safe="")
        return f"{disposition}; filename=\"{ascii_fallback}\"; filename*=UTF-8''{utf8_encoded}"


def _parse_fps_safe(fps_str: str) -> float:
    """Safely parse FPS from fraction string like '30000/1001'"""
    try:
        fps_str = str(fps_str).strip()
        if "/" in fps_str:
            parts = fps_str.split("/")
            if len(parts) == 2:
                numerator = float(parts[0])
                denominator = float(parts[1])
                if denominator != 0:
                    return round(numerator / denominator, 2)
        return float(fps_str)
    except (ValueError, ZeroDivisionError, AttributeError):
        return 0.0


async def save_upload_file(
    upload_file: UploadFile, destination_dir: Path = settings.TEMP_DIR
) -> Path:
    """Save uploaded file to destination directory with unique filename"""
    # Generate unique filename
    file_extension = Path(upload_file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = destination_dir / unique_filename

    # Save file asynchronously in chunks to avoid loading entire file into memory
    async with aiofiles.open(file_path, "wb") as f:
        while chunk := await upload_file.read(1024 * 1024):  # 1MB chunks
            await f.write(chunk)

    return file_path


def cleanup_file(file_path: Path) -> None:
    """Delete a file if it exists"""
    try:
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {e}")
