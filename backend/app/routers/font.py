"""
Font Conversion Router
Handles font format conversion endpoints
"""

import logging
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.config import settings
from app.middleware.error_handler import sanitize_error_message
from app.models.conversion import ConversionResponse, ConversionStatus, FileInfo
from app.services.font_converter import FontConverter
from app.utils.file_handler import (
    cleanup_file,
    make_content_disposition,
    save_upload_file,
)
from app.utils.validation import (
    FONT_MIME_TYPES,
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
font_converter = FontConverter()


@router.post(
    "/convert",
    response_model=ConversionResponse,
    dependencies=[Depends(check_rate_limit)],
)
async def convert_font(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    subset_text: Optional[str] = Form(None),
    optimize: bool = Form(True),
):
    """
    Convert font file to target format

    Supported formats: TTF, OTF, WOFF, WOFF2

    Args:
        file: Font file to convert
        output_format: Target format (ttf, otf, woff, woff2)
        subset_text: Optional text to subset (keep only these characters)
        optimize: Whether to optimize the font (default: True)

    Returns:
        Conversion response with download URL
    """
    session_id = str(uuid.uuid4())
    session_validator.register_session(session_id)

    try:
        # Validate file extension
        input_format = validate_file_extension(file.filename, settings.FONT_FORMATS)

        # Validate output format
        if output_format not in settings.FONT_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid output format: {output_format}. Supported: {', '.join(settings.FONT_FORMATS)}",
            )

        # Validate file size
        validate_file_size(file, "font")

        # Save uploaded file using standard handler
        input_path = await save_upload_file(file, settings.TEMP_DIR)

        # Validate MIME type to prevent file type spoofing
        validate_mime_type(input_path, FONT_MIME_TYPES)

        # Convert
        output_path = await font_converter.convert_with_cache(
            input_path=input_path,
            output_format=output_format,
            options={
                "subset_text": subset_text,
                "optimize": optimize,
            },
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
            download_url=f"/api/font/download/{output_path.name}",
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


@router.post(
    "/optimize",
    response_model=ConversionResponse,
    dependencies=[Depends(check_rate_limit)],
)
async def optimize_font(
    file: UploadFile = File(...),
):
    """
    Optimize a font by removing unnecessary data

    Args:
        file: Font file to optimize

    Returns:
        Conversion response with download URL
    """
    session_id = str(uuid.uuid4())
    session_validator.register_session(session_id)

    try:
        # Validate file extension
        input_format = validate_file_extension(file.filename, settings.FONT_FORMATS)

        # Validate file size
        validate_file_size(file, "font")

        # Save uploaded file using standard handler
        input_path = await save_upload_file(file, settings.TEMP_DIR)

        # Optimize
        output_path = await font_converter.optimize_font(
            input_path=input_path, session_id=session_id
        )

        # Clean up input file
        cleanup_file(input_path)

        # Return response
        return ConversionResponse(
            session_id=session_id,
            status=ConversionStatus.COMPLETED,
            message="Optimization successful",
            output_file=output_path.name,
            download_url=f"/api/font/download/{output_path.name}",
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Optimization error: {e}")
        # Clean up on error
        if "input_path" in locals():
            cleanup_file(input_path)
        raise HTTPException(
            status_code=500,
            detail=f"Optimization failed: {sanitize_error_message(str(e))}",
        )


# MIME type mapping for font formats (used for download responses)
FONT_MIME_MAP = {
    "ttf": "font/ttf",
    "otf": "font/otf",
    "woff": "font/woff",
    "woff2": "font/woff2",
}


@router.get("/download/{filename}", dependencies=[Depends(check_rate_limit)])
async def download_font(filename: str):
    """
    Download converted font file

    Args:
        filename: Name of the converted file

    Returns:
        FileResponse with the converted file
    """
    file_path = validate_download_filename(filename, settings.UPLOAD_DIR)

    # Determine MIME type from extension
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    media_type = FONT_MIME_MAP.get(ext, "application/octet-stream")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
        headers={"Content-Disposition": make_content_disposition(filename)},
        background=BackgroundTask(_cleanup_after_download, str(file_path)),
    )


@router.get("/formats", dependencies=[Depends(check_rate_limit)])
async def get_font_formats():
    """
    Get supported font formats

    Returns:
        Dictionary with input and output formats
    """
    return {
        "input_formats": sorted(list(settings.FONT_FORMATS)),
        "output_formats": sorted(list(settings.FONT_FORMATS)),
        "notes": {
            "ttf": "TrueType Font - Most compatible desktop format",
            "otf": "OpenType Font - Advanced features, better for complex typography",
            "woff": "Web Open Font Format - Optimized for web use",
            "woff2": "WOFF2 - Better compression than WOFF, modern browsers only",
        },
    }


@router.post("/info", response_model=FileInfo, dependencies=[Depends(check_rate_limit)])
async def get_font_info(file: UploadFile = File(...)):
    """
    Get information about a font file

    Args:
        file: Font file to analyze

    Returns:
        FileInfo with font metadata
    """
    try:
        # Validate file extension
        input_format = validate_file_extension(file.filename, settings.FONT_FORMATS)

        # Validate file size
        validate_file_size(file, "font")

        # Save uploaded file using standard handler
        temp_path = await save_upload_file(file, settings.TEMP_DIR)

        # Get info
        converter = FontConverter()
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
