from fastapi import UploadFile, HTTPException
from pathlib import Path
from typing import Set
import os
import logging
import sys

logger = logging.getLogger(__name__)

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    # SECURITY WARNING: Log at ERROR level and print to stderr to ensure visibility
    security_warning = (
        "SECURITY WARNING: python-magic is not installed. MIME type validation is DISABLED. "
        "This is a significant security risk - attackers can upload malicious files with "
        "renamed extensions. Install python-magic for production use: pip install python-magic"
    )
    logger.error(security_warning)
    print(f"\n{'='*80}\n{security_warning}\n{'='*80}\n", file=sys.stderr)

from app.config import settings


def validate_file_size(file: UploadFile, file_type: str) -> None:
    """Validate file size based on file type"""
    # Get file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Seek back to start

    # Check against limits
    if file_type == "image" and file_size > settings.IMAGE_MAX_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Image file too large. Maximum size: {settings.IMAGE_MAX_SIZE / 1024 / 1024}MB"
        )
    elif file_type == "video" and file_size > settings.VIDEO_MAX_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Video file too large. Maximum size: {settings.VIDEO_MAX_SIZE / 1024 / 1024}MB"
        )
    elif file_type == "audio" and file_size > settings.AUDIO_MAX_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Audio file too large. Maximum size: {settings.AUDIO_MAX_SIZE / 1024 / 1024}MB"
        )
    elif file_type == "document" and file_size > settings.DOCUMENT_MAX_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Document file too large. Maximum size: {settings.DOCUMENT_MAX_SIZE / 1024 / 1024}MB"
        )
    elif file_type == "archive" and file_size > settings.ARCHIVE_MAX_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Archive file too large. Maximum size: {settings.ARCHIVE_MAX_SIZE / 1024 / 1024}MB"
        )
    elif file_type == "spreadsheet" and file_size > settings.SPREADSHEET_MAX_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Spreadsheet file too large. Maximum size: {settings.SPREADSHEET_MAX_SIZE / 1024 / 1024}MB"
        )
    elif file_type == "subtitle" and file_size > settings.SUBTITLE_MAX_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Subtitle file too large. Maximum size: {settings.SUBTITLE_MAX_SIZE / 1024 / 1024}MB"
        )
    elif file_type == "ebook" and file_size > settings.EBOOK_MAX_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"eBook file too large. Maximum size: {settings.EBOOK_MAX_SIZE / 1024 / 1024}MB"
        )
    elif file_type == "font" and file_size > settings.FONT_MAX_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Font file too large. Maximum size: {settings.FONT_MAX_SIZE / 1024 / 1024}MB"
        )
    elif file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )


def validate_file_extension(filename: str, allowed_formats: Set[str]) -> str:
    """Validate file extension against allowed formats"""
    filename_lower = filename.lower()

    # Check for compound extensions (e.g., .tar.gz, .tar.bz2)
    if filename_lower.endswith('.tar.gz') and 'tar.gz' in allowed_formats:
        return 'tar.gz'
    elif filename_lower.endswith('.tar.bz2') and 'tar.bz2' in allowed_formats:
        return 'tar.bz2'
    elif filename_lower.endswith('.tgz') and 'tgz' in allowed_formats:
        return 'tgz'
    elif filename_lower.endswith('.tbz2') and 'tbz2' in allowed_formats:
        return 'tbz2'

    # Standard single extension
    file_extension = Path(filename).suffix.lower().lstrip('.')

    if file_extension not in allowed_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {file_extension}. Allowed formats: {', '.join(allowed_formats)}"
        )

    return file_extension


def validate_mime_type(file_path: Path, expected_types: Set[str]) -> None:
    """
    Validate MIME type of uploaded file using python-magic.

    SECURITY: MIME validation is ALWAYS enforced regardless of DEBUG mode.
    If python-magic is not available, file uploads are rejected to prevent
    file type spoofing attacks.

    Ensure python-magic is installed: pip install python-magic
    """
    if not MAGIC_AVAILABLE:
        # SECURITY: Always fail if MIME validation is unavailable
        # Never skip validation, even in DEBUG mode
        raise HTTPException(
            status_code=503,
            detail="File type validation unavailable. Install python-magic: pip install python-magic"
        )

    try:
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(str(file_path))

        # Check if MIME type matches expected types
        is_valid = any(expected in mime_type for expected in expected_types)

        if not is_valid:
            logger.warning(f"MIME type mismatch: expected {expected_types}, got {mime_type}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Detected MIME type: {mime_type}"
            )
    except HTTPException:
        raise
    except Exception as e:
        # Log the error - MIME validation errors are security-relevant
        logger.error(f"MIME type validation error: {e}")
        # Fail closed on validation errors
        raise HTTPException(
            status_code=400,
            detail="File type validation failed. Please try again with a valid file."
        )


def get_file_type_from_format(file_format: str) -> str:
    """Determine file type category from format"""
    if file_format in settings.IMAGE_FORMATS:
        return "image"
    elif file_format in settings.VIDEO_FORMATS:
        return "video"
    elif file_format in settings.AUDIO_FORMATS:
        return "audio"
    elif file_format in settings.DOCUMENT_FORMATS:
        return "document"
    else:
        raise HTTPException(status_code=400, detail=f"Unknown file format: {file_format}")


def validate_download_filename(filename: str, base_dir: Path) -> Path:
    """
    Validate filename for download to prevent path traversal attacks.

    SECURITY:
    - Rejects path separators and null bytes
    - Rejects parent directory references
    - Rejects symlinks to prevent escaping the base directory
    - Validates the resolved path is within base_dir

    Args:
        filename: The requested filename
        base_dir: The allowed base directory

    Returns:
        Validated absolute path

    Raises:
        HTTPException: If filename is invalid or contains path traversal
    """
    # Check for path separators and null bytes
    if not filename or "/" in filename or "\\" in filename or "\x00" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Check for parent directory references
    if ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Construct the full path
    file_path = base_dir / filename

    # SECURITY: Check if the path is a symlink BEFORE resolving
    # This prevents symlink attacks that could escape the base directory
    if file_path.is_symlink():
        logger.warning(f"Symlink access attempt blocked: {filename}")
        raise HTTPException(status_code=403, detail="Access denied")

    # Resolve to absolute path
    try:
        resolved_path = file_path.resolve(strict=True)  # strict=True raises if path doesn't exist
        resolved_base = base_dir.resolve()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except (OSError, RuntimeError):
        raise HTTPException(status_code=400, detail="Invalid file path")

    # Ensure the resolved path is within the base directory
    try:
        resolved_path.relative_to(resolved_base)
    except ValueError:
        logger.warning(f"Path traversal attempt blocked: {filename}")
        raise HTTPException(status_code=403, detail="Access denied")

    # Check it's a regular file (not directory, device, etc.)
    if not resolved_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")

    return resolved_path


def validate_subprocess_path(file_path: Path, allowed_dirs: list) -> Path:
    """
    Validate that a file path is within allowed directories before passing to subprocess.

    SECURITY: Prevents processing of arbitrary files on the system by ensuring
    the path is within one of the allowed directories.

    Args:
        file_path: The path to validate
        allowed_dirs: List of allowed directory paths

    Returns:
        The validated resolved path

    Raises:
        HTTPException: If path is outside allowed directories
    """
    try:
        resolved_path = file_path.resolve()
    except (OSError, RuntimeError):
        raise HTTPException(status_code=400, detail="Invalid file path")

    # Check if the resolved path is within any allowed directory
    for allowed_dir in allowed_dirs:
        try:
            allowed_resolved = Path(allowed_dir).resolve()
            resolved_path.relative_to(allowed_resolved)
            return resolved_path  # Path is valid
        except ValueError:
            continue  # Not in this directory, try next

    # Path not in any allowed directory
    logger.warning(f"Subprocess path validation failed: {file_path}")
    raise HTTPException(status_code=403, detail="File access denied")
