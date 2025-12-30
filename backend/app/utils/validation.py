from fastapi import UploadFile, HTTPException
from pathlib import Path
from typing import Set
import os

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

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
    """Validate MIME type of uploaded file using python-magic"""
    if not MAGIC_AVAILABLE:
        # python-magic not available, skip MIME validation
        return

    try:
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(str(file_path))

        # Check if MIME type matches expected types
        is_valid = any(expected in mime_type for expected in expected_types)

        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Detected MIME type: {mime_type}"
            )
    except Exception as e:
        # If python-magic fails, skip MIME validation
        # This is optional security layer
        pass


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

    # Resolve to absolute path to handle any symlinks
    try:
        resolved_path = file_path.resolve()
        resolved_base = base_dir.resolve()
    except (OSError, RuntimeError):
        raise HTTPException(status_code=400, detail="Invalid file path")

    # Ensure the resolved path is within the base directory
    try:
        resolved_path.relative_to(resolved_base)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check file exists and is a regular file
    if not resolved_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not resolved_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")

    return resolved_path
