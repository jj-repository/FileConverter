"""
Font Conversion Router
Handles font format conversion endpoints
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional
import uuid
import logging

from app.config import settings
from app.services.font_converter import FontConverter
from app.utils.file_handler import save_upload_file, make_content_disposition
from app.utils.validation import validate_file_size, validate_file_extension, validate_download_filename, validate_mime_type, FONT_MIME_TYPES
from app.models.conversion import ConversionResponse
from app.utils.websocket_security import session_validator, check_rate_limit
from app.middleware.error_handler import sanitize_error_message

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/convert", response_model=ConversionResponse, dependencies=[Depends(check_rate_limit)])
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
                detail=f"Invalid output format: {output_format}. Supported: {', '.join(settings.FONT_FORMATS)}"
            )

        # Validate file size
        validate_file_size(file, "font")

        # Save uploaded file using standard handler
        input_path = await save_upload_file(file, settings.TEMP_DIR)

        # Validate MIME type to prevent file type spoofing
        validate_mime_type(input_path, FONT_MIME_TYPES)

        # Convert
        converter = FontConverter()
        output_path = await converter.convert_with_cache(
            input_path=input_path,
            output_format=output_format,
            options={
                'subset_text': subset_text,
                'optimize': optimize,
            },
            session_id=session_id
        )

        # Clean up input file
        input_path.unlink(missing_ok=True)

        # Return response
        return ConversionResponse(
            session_id=session_id,
            status="completed",
            message="Conversion successful",
            output_file=output_path.name,
            download_url=f"/api/font/download/{output_path.name}"
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        # Clean up on error
        if 'input_path' in locals():
            input_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {sanitize_error_message(str(e))}")


@router.post("/optimize", response_model=ConversionResponse, dependencies=[Depends(check_rate_limit)])
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
        converter = FontConverter()
        output_path = await converter.optimize_font(
            input_path=input_path,
            session_id=session_id
        )

        # Clean up input file
        input_path.unlink(missing_ok=True)

        # Return response
        return ConversionResponse(
            session_id=session_id,
            status="completed",
            message="Optimization successful",
            output_file=output_path.name,
            download_url=f"/api/font/download/{output_path.name}"
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Optimization error: {e}")
        # Clean up on error
        if 'input_path' in locals():
            input_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Optimization failed: {sanitize_error_message(str(e))}")


# MIME type mapping for font formats (used for download responses)
FONT_MIME_MAP = {
    "ttf": "font/ttf",
    "otf": "font/otf",
    "woff": "font/woff",
    "woff2": "font/woff2",
}


@router.get("/download/{filename}")
async def download_font(filename: str):
    """
    Download converted font file

    Args:
        filename: Name of the converted file

    Returns:
        FileResponse with the converted file
    """
    file_path = validate_download_filename(filename, settings.UPLOAD_DIR)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Determine MIME type from extension
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    media_type = FONT_MIME_MAP.get(ext, "application/octet-stream")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
        headers={"Content-Disposition": make_content_disposition(filename)}
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
            "woff2": "WOFF2 - Better compression than WOFF, modern browsers only"
        }
    }


@router.post("/info", dependencies=[Depends(check_rate_limit)])
async def get_font_info(file: UploadFile = File(...)):
    """
    Get information about a font file

    Args:
        file: Font file to analyze

    Returns:
        Dictionary with font metadata
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
        temp_path.unlink(missing_ok=True)

        return info

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Info extraction error: {e}")
        if 'temp_path' in locals():
            temp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to extract info: {sanitize_error_message(str(e))}")
