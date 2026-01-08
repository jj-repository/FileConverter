from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from fastapi.responses import FileResponse
from pathlib import Path
import uuid
from typing import Optional, Annotated, Literal

from app.services.subtitle_converter import SubtitleConverter
from app.utils.file_handler import save_upload_file, cleanup_file, make_content_disposition
from app.utils.validation import validate_file_size, validate_file_extension, validate_download_filename, validate_mime_type, SUBTITLE_MIME_TYPES
from app.models.conversion import ConversionResponse, ConversionStatus, FileInfo
from app.config import settings
from app.utils.websocket_security import session_validator, check_rate_limit
from app.middleware.error_handler import sanitize_error_message


router = APIRouter()
subtitle_converter = SubtitleConverter()


# Whitelist types for subtitle parameters
SubtitleEncoding = Literal["utf-8", "utf-16", "ascii", "latin-1", "iso-8859-1", "cp1252"]


@router.post("/convert", response_model=ConversionResponse, dependencies=[Depends(check_rate_limit)])
async def convert_subtitle(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    encoding: Annotated[Optional[SubtitleEncoding], Form(description="Character encoding")] = "utf-8",
    fps: Annotated[Optional[float], Form(ge=1.0, le=120.0, description="Frame rate for SUB format (1-120)")] = 23.976,
    keep_html_tags: Optional[bool] = Form(False),
):
    """
    Convert a subtitle file to a different format

    - **file**: Subtitle file to convert (SRT, VTT, ASS, SSA, SUB)
    - **output_format**: Target format (srt, vtt, ass, ssa, sub)
    - **encoding**: Character encoding (default: utf-8)
    - **fps**: Frame rate for SUB format (default: 23.976)
    - **keep_html_tags**: Keep HTML formatting tags (default: false)
    """
    session_id = str(uuid.uuid4())
    session_validator.register_session(session_id)

    try:
        # Validate file size
        validate_file_size(file, "subtitle")

        # Validate file extension
        input_format = validate_file_extension(file.filename, settings.SUBTITLE_FORMATS)

        # Validate output format
        if output_format.lower() not in settings.SUBTITLE_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported output format: {output_format}"
            )

        # Save uploaded file
        input_path = await save_upload_file(file, settings.TEMP_DIR)

        # Validate MIME type to prevent file type spoofing
        validate_mime_type(input_path, SUBTITLE_MIME_TYPES)

        # Convert subtitle
        options = {
            "encoding": encoding,
            "fps": fps,
            "keep_html_tags": keep_html_tags,
        }

        output_path = await subtitle_converter.convert_with_cache(
            input_path=input_path,
            output_format=output_format.lower(),
            options=options,
            session_id=session_id
        )

        # Clean up input file
        cleanup_file(input_path)

        # Generate download URL
        download_url = f"/api/subtitle/download/{output_path.name}"

        return ConversionResponse(
            session_id=session_id,
            status=ConversionStatus.COMPLETED,
            message="Subtitle conversion completed successfully",
            output_file=output_path.name,
            download_url=download_url
        )

    except HTTPException:
        raise
    except Exception as e:
        # Clean up on error
        if 'input_path' in locals():
            cleanup_file(input_path)
        if 'output_path' in locals():
            cleanup_file(output_path)

        raise HTTPException(status_code=500, detail=f"Conversion failed: {sanitize_error_message(str(e))}")


@router.post("/adjust-timing", response_model=ConversionResponse, dependencies=[Depends(check_rate_limit)])
async def adjust_subtitle_timing(
    file: UploadFile = File(...),
    offset_ms: Annotated[int, Form(ge=-3600000, le=3600000, description="Time offset in ms (-1 hour to +1 hour)")] = ...,
):
    """
    Adjust subtitle timing by offset

    - **file**: Subtitle file to adjust
    - **offset_ms**: Time offset in milliseconds (positive = delay, negative = advance)
    """
    session_id = str(uuid.uuid4())
    session_validator.register_session(session_id)

    try:
        # Validate file size
        validate_file_size(file, "subtitle")

        # Validate file extension
        input_format = validate_file_extension(file.filename, settings.SUBTITLE_FORMATS)

        # Save uploaded file
        input_path = await save_upload_file(file, settings.TEMP_DIR)

        # Adjust timing
        output_path = await subtitle_converter.adjust_timing(
            input_path=input_path,
            offset_ms=offset_ms,
            session_id=session_id
        )

        # Clean up input file
        cleanup_file(input_path)

        # Generate download URL
        download_url = f"/api/subtitle/download/{output_path.name}"

        return ConversionResponse(
            session_id=session_id,
            status=ConversionStatus.COMPLETED,
            message=f"Subtitle timing adjusted by {offset_ms}ms",
            output_file=output_path.name,
            download_url=download_url
        )

    except HTTPException:
        raise
    except Exception as e:
        # Clean up on error
        if 'input_path' in locals():
            cleanup_file(input_path)
        if 'output_path' in locals():
            cleanup_file(output_path)

        raise HTTPException(status_code=500, detail=f"Timing adjustment failed: {sanitize_error_message(str(e))}")


# MIME type mapping for subtitle formats
SUBTITLE_MIME_TYPES = {
    "srt": "application/x-subrip",
    "vtt": "text/vtt",
    "ass": "text/x-ass",
    "ssa": "text/x-ssa",
    "sub": "text/x-sub",
}


@router.get("/download/{filename}")
async def download_subtitle(filename: str):
    """Download converted subtitle file"""
    # Validate filename to prevent path traversal
    file_path = validate_download_filename(filename, settings.UPLOAD_DIR)

    # Determine MIME type from extension
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    media_type = SUBTITLE_MIME_TYPES.get(ext, "text/plain")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type,
        headers={"Content-Disposition": make_content_disposition(filename)}
    )


@router.get("/formats", dependencies=[Depends(check_rate_limit)])
async def get_supported_formats():
    """Get list of supported subtitle formats"""
    formats = await subtitle_converter.get_supported_formats()
    return {
        "input_formats": formats["input"],
        "output_formats": formats["output"],
    }


@router.post("/info", response_model=FileInfo, dependencies=[Depends(check_rate_limit)])
async def get_subtitle_info(file: UploadFile = File(...)):
    """Get metadata about a subtitle file"""
    try:
        # Validate file
        validate_file_size(file, "subtitle")
        input_format = validate_file_extension(file.filename, settings.SUBTITLE_FORMATS)

        # Save file temporarily
        temp_path = await save_upload_file(file, settings.TEMP_DIR)

        # Get metadata and file size before cleanup
        metadata = await subtitle_converter.get_subtitle_info(temp_path)
        file_size = temp_path.stat().st_size

        # Clean up
        cleanup_file(temp_path)

        return FileInfo(
            filename=file.filename,
            size=file_size,
            format=input_format,
            metadata=metadata
        )

    except Exception as e:
        if 'temp_path' in locals():
            cleanup_file(temp_path)
        raise HTTPException(status_code=500, detail=f"Failed to get subtitle info: {sanitize_error_message(str(e))}")
