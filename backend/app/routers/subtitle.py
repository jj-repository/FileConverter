from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from pathlib import Path
import uuid
from typing import Optional

from app.services.subtitle_converter import SubtitleConverter
from app.utils.file_handler import save_upload_file, cleanup_file
from app.utils.validation import validate_file_size, validate_file_extension, validate_download_filename
from app.models.conversion import ConversionResponse, ConversionStatus, FileInfo
from app.config import settings
from app.utils.websocket_security import session_validator


router = APIRouter()
subtitle_converter = SubtitleConverter()


@router.post("/convert", response_model=ConversionResponse)
async def convert_subtitle(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    encoding: Optional[str] = Form("utf-8"),
    fps: Optional[float] = Form(23.976),
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

        # Convert subtitle
        options = {
            "encoding": encoding,
            "fps": fps,
            "keep_html_tags": keep_html_tags,
        }

        output_path = await subtitle_converter.convert(
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

        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@router.post("/adjust-timing", response_model=ConversionResponse)
async def adjust_subtitle_timing(
    file: UploadFile = File(...),
    offset_ms: int = Form(...),
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

        raise HTTPException(status_code=500, detail=f"Timing adjustment failed: {str(e)}")


@router.get("/download/{filename}")
async def download_subtitle(filename: str):
    """Download converted subtitle file"""
    # Validate filename to prevent path traversal
    file_path = validate_download_filename(filename, settings.UPLOAD_DIR)

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="text/plain"
    )


@router.get("/formats")
async def get_supported_formats():
    """Get list of supported subtitle formats"""
    formats = await subtitle_converter.get_supported_formats()
    return {
        "input_formats": formats["input"],
        "output_formats": formats["output"],
    }


@router.post("/info", response_model=FileInfo)
async def get_subtitle_info(file: UploadFile = File(...)):
    """Get metadata about a subtitle file"""
    try:
        # Validate file
        validate_file_size(file, "subtitle")
        input_format = validate_file_extension(file.filename, settings.SUBTITLE_FORMATS)

        # Save file temporarily
        temp_path = await save_upload_file(file, settings.TEMP_DIR)

        # Get metadata
        metadata = await subtitle_converter.get_subtitle_info(temp_path)

        # Clean up
        cleanup_file(temp_path)

        return FileInfo(
            filename=file.filename,
            size=temp_path.stat().st_size if temp_path.exists() else 0,
            format=input_format,
            metadata=metadata
        )

    except Exception as e:
        if 'temp_path' in locals():
            cleanup_file(temp_path)
        raise HTTPException(status_code=500, detail=f"Failed to get subtitle info: {str(e)}")
