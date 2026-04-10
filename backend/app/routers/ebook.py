"""
eBook Conversion Router
Handles EPUB and other eBook format conversion endpoints
"""

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.config import settings
from app.middleware.error_handler import sanitize_error_message
from app.models.conversion import ConversionResponse, ConversionStatus, FileInfo
from app.services.ebook_converter import EbookConverter
from app.utils.file_handler import (
    cleanup_file,
    make_content_disposition,
    save_upload_file,
)
from app.utils.validation import (
    EBOOK_MIME_TYPES,
    validate_download_filename,
    validate_file_extension,
    validate_file_size,
    validate_mime_type,
)
from app.utils.websocket_security import check_rate_limit, session_validator


def _cleanup_after_download(path: str):
    try:
        Path(path).unlink(missing_ok=True)
    except Exception:
        pass


router = APIRouter()
logger = logging.getLogger(__name__)
ebook_converter = EbookConverter()


@router.post(
    "/convert",
    response_model=ConversionResponse,
    dependencies=[Depends(check_rate_limit)],
)
async def convert_ebook(
    file: UploadFile = File(...),
    output_format: str = Form(...),
):
    """
    Convert eBook file to target format

    Supported conversions:
    - EPUB → TXT, HTML, PDF
    - TXT, HTML → EPUB

    Args:
        file: eBook file to convert
        output_format: Target format (epub, txt, html, pdf)

    Returns:
        Conversion response with download URL
    """
    session_id = str(uuid.uuid4())
    session_validator.register_session(session_id)

    try:
        # Validate file extension
        input_format = validate_file_extension(file.filename, settings.EBOOK_FORMATS)

        # Validate output format
        if output_format not in settings.EBOOK_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid output format: {output_format}. Supported: {', '.join(settings.EBOOK_FORMATS)}",
            )

        # Validate file size
        validate_file_size(file, "ebook")

        # Save uploaded file using standard handler
        input_path = await save_upload_file(file, settings.TEMP_DIR)

        # Validate MIME type to prevent file type spoofing
        validate_mime_type(input_path, EBOOK_MIME_TYPES)

        # Convert
        output_path = await ebook_converter.convert_with_cache(
            input_path=input_path,
            output_format=output_format,
            options={},
            session_id=session_id,
        )

        # Clean up input file
        cleanup_file(input_path)

        # Return response
        return ConversionResponse(
            session_id=session_id,
            status=ConversionStatus.COMPLETED,
            message="Conversion successful",
            output_file=output_path.name,
            download_url=f"/api/ebook/download/{output_path.name}",
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        # Clean up on error
        if "input_path" in locals():
            cleanup_file(input_path)
        raise HTTPException(
            status_code=500,
            detail=f"Conversion failed: {sanitize_error_message(str(e))}",
        )


# MIME type mapping for ebook formats (used for download responses)
EBOOK_MIME_MAP = {
    "epub": "application/epub+zip",
    "txt": "text/plain",
    "html": "text/html",
    "pdf": "application/pdf",
}


@router.get("/download/{filename}", dependencies=[Depends(check_rate_limit)])
async def download_ebook(filename: str):
    """
    Download converted eBook file

    Args:
        filename: Name of the converted file

    Returns:
        FileResponse with the converted file
    """
    file_path = validate_download_filename(filename, settings.UPLOAD_DIR)

    # Determine MIME type from extension
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    media_type = EBOOK_MIME_MAP.get(ext, "application/octet-stream")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
        headers={"Content-Disposition": make_content_disposition(filename)},
        background=BackgroundTask(_cleanup_after_download, str(file_path)),
    )


@router.get("/formats", dependencies=[Depends(check_rate_limit)])
async def get_ebook_formats():
    """
    Get supported eBook formats

    Returns:
        Dictionary with input and output formats
    """
    return {
        "input_formats": sorted(list(settings.EBOOK_FORMATS)),
        "output_formats": sorted(list(settings.EBOOK_FORMATS)),
        "notes": {
            "epub": "EPUB is the standard eBook format",
            "txt": "Plain text extraction (loses formatting)",
            "html": "Single HTML file with basic styling",
            "pdf": "PDF with text content (loses advanced formatting)",
        },
    }


@router.post("/info", response_model=FileInfo, dependencies=[Depends(check_rate_limit)])
async def get_ebook_info(file: UploadFile = File(...)):
    """
    Get information about an eBook file

    Args:
        file: eBook file to analyze

    Returns:
        FileInfo with eBook metadata
    """
    try:
        # Validate file extension
        input_format = validate_file_extension(file.filename, settings.EBOOK_FORMATS)

        # Validate file size
        validate_file_size(file, "ebook")

        # Save uploaded file using standard handler
        temp_path = await save_upload_file(file, settings.TEMP_DIR)

        # Get info
        converter = EbookConverter()
        info = await converter.get_info(temp_path)

        # Clean up
        cleanup_file(temp_path)

        # Wrap extra fields into metadata for FileInfo model
        metadata = {
            k: v for k, v in info.items() if k not in ("filename", "size", "format")
        }
        return FileInfo(
            filename=info["filename"],
            size=info["size"],
            format=info["format"],
            metadata=metadata or None,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Info extraction error: {e}")
        if "temp_path" in locals():
            cleanup_file(temp_path)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract info: {sanitize_error_message(str(e))}",
        )
