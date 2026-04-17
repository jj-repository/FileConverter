import uuid
from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.config import settings
from app.middleware.error_handler import sanitize_error_message
from app.models.conversion import ConversionResponse, ConversionStatus, FileInfo
from app.routers.base_router import handle_convert, handle_download, handle_formats, handle_info
from app.services.subtitle_converter import SubtitleConverter
from app.utils.file_handler import cleanup_file, save_upload_file
from app.utils.validation import SUBTITLE_MIME_TYPES, validate_file_extension, validate_file_size
from app.utils.websocket_security import check_rate_limit, session_validator

router = APIRouter()
converter = SubtitleConverter()

SubtitleEncoding = Literal["utf-8", "utf-16", "ascii", "latin-1", "iso-8859-1", "cp1252"]

SUBTITLE_MIME_MAP = {
    "srt": "application/x-subrip",
    "vtt": "text/vtt",
    "ass": "text/x-ass",
    "ssa": "text/x-ssa",
    "sub": "text/x-sub",
}


@router.post(
    "/convert", response_model=ConversionResponse, dependencies=[Depends(check_rate_limit)]
)
async def convert_subtitle(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    encoding: Annotated[
        Optional[SubtitleEncoding], Form(description="Character encoding")
    ] = "utf-8",
    fps: Annotated[
        Optional[float], Form(ge=1.0, le=120.0, description="Frame rate for SUB format (1-120)")
    ] = 23.976,
    keep_html_tags: Optional[bool] = Form(False),
):
    """Convert a subtitle file to a different format."""
    return await handle_convert(
        file,
        output_format,
        {"encoding": encoding, "fps": fps, "keep_html_tags": keep_html_tags},
        converter=converter,
        formats=settings.SUBTITLE_FORMATS,
        category="subtitle",
        mime_types=SUBTITLE_MIME_TYPES,
        api_prefix="subtitle",
    )


@router.post(
    "/adjust-timing", response_model=ConversionResponse, dependencies=[Depends(check_rate_limit)]
)
async def adjust_subtitle_timing(
    file: UploadFile = File(...),
    offset_ms: Annotated[
        int, Form(ge=-3600000, le=3600000, description="Time offset in ms (-1 hour to +1 hour)")
    ] = ...,
):
    """Adjust subtitle timing by offset."""
    session_id = str(uuid.uuid4())
    session_validator.register_session(session_id)
    input_path = None

    try:
        validate_file_size(file, "subtitle")
        validate_file_extension(file.filename, settings.SUBTITLE_FORMATS)
        input_path = await save_upload_file(file, settings.TEMP_DIR)

        output_path = await converter.adjust_timing(
            input_path=input_path,
            offset_ms=offset_ms,
            session_id=session_id,
        )
        cleanup_file(input_path)
        input_path = None

        return ConversionResponse(
            session_id=session_id,
            status=ConversionStatus.COMPLETED,
            message=f"Subtitle timing adjusted by {offset_ms}ms",
            output_file=output_path.name,
            download_url=f"/api/subtitle/download/{output_path.name}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Timing adjustment failed: {sanitize_error_message(str(e))}",
        )
    finally:
        if input_path:
            cleanup_file(input_path)


@router.get("/download/{filename}", dependencies=[Depends(check_rate_limit)])
async def download_subtitle(filename: str):
    """Download converted subtitle file."""
    return await handle_download(filename, SUBTITLE_MIME_MAP, default_mime="text/plain")


@router.get("/formats", dependencies=[Depends(check_rate_limit)])
async def get_supported_formats():
    """Get list of supported subtitle formats."""
    return await handle_formats(converter)


@router.post("/info", response_model=FileInfo, dependencies=[Depends(check_rate_limit)])
async def get_subtitle_info(file: UploadFile = File(...)):
    """Get metadata about a subtitle file."""
    return await handle_info(
        file,
        converter=converter,
        formats=settings.SUBTITLE_FORMATS,
        category="subtitle",
        metadata_getter="get_subtitle_info",
    )
