import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from starlette.background import BackgroundTask

from app.config import settings
from app.middleware.error_handler import sanitize_error_message
from app.models.conversion import ConversionResponse, ConversionStatus, FileInfo
from app.routers.base_router import (
    cleanup_after_download,
    handle_convert,
    handle_info_raw,
)
from app.services.font_converter import FontConverter
from app.utils.file_handler import cleanup_file, make_content_disposition, save_upload_file
from app.utils.validation import (
    FONT_MIME_TYPES,
    validate_download_filename,
    validate_file_extension,
    validate_file_size,
    validate_mime_type,
)
from app.utils.websocket_security import check_rate_limit, session_validator

router = APIRouter()
converter = FontConverter()

FONT_MIME_MAP = {
    "ttf": "font/ttf",
    "otf": "font/otf",
    "woff": "font/woff",
    "woff2": "font/woff2",
}


@router.post(
    "/convert", response_model=ConversionResponse, dependencies=[Depends(check_rate_limit)]
)
async def convert_font(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    subset_text: Optional[str] = Form(None),
    optimize: bool = Form(True),
):
    """Convert font file to target format (TTF, OTF, WOFF, WOFF2)."""
    return await handle_convert(
        file,
        output_format,
        {"subset_text": subset_text, "optimize": optimize},
        converter=converter,
        formats=settings.FONT_FORMATS,
        category="font",
        mime_types=FONT_MIME_TYPES,
        api_prefix="font",
    )


@router.post(
    "/optimize", response_model=ConversionResponse, dependencies=[Depends(check_rate_limit)]
)
async def optimize_font(file: UploadFile = File(...)):
    """Optimize a font by removing unnecessary data."""
    session_id = str(uuid.uuid4())
    session_validator.register_session(session_id)
    input_path = None

    try:
        validate_file_extension(file.filename, settings.FONT_FORMATS)
        validate_file_size(file, "font")
        input_path = await save_upload_file(file, settings.TEMP_DIR)
        validate_mime_type(input_path, FONT_MIME_TYPES)

        output_path = await converter.optimize_font(
            input_path=input_path,
            session_id=session_id,
        )
        cleanup_file(input_path)
        input_path = None

        return ConversionResponse(
            session_id=session_id,
            status=ConversionStatus.COMPLETED,
            message="Optimization successful",
            output_file=output_path.name,
            download_url=f"/api/font/download/{output_path.name}",
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Optimization failed: {sanitize_error_message(str(e))}",
        )
    finally:
        if input_path:
            cleanup_file(input_path)


@router.get("/download/{filename}", dependencies=[Depends(check_rate_limit)])
async def download_font(filename: str):
    """Download converted font file."""
    from fastapi.responses import FileResponse

    file_path = validate_download_filename(filename, settings.UPLOAD_DIR)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    media_type = FONT_MIME_MAP.get(ext, "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type,
        headers={"Content-Disposition": make_content_disposition(filename)},
        background=BackgroundTask(cleanup_after_download, str(file_path)),
    )


@router.get("/formats", dependencies=[Depends(check_rate_limit)])
async def get_font_formats():
    """Get supported font formats."""
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
    """Get information about a font file."""
    return await handle_info_raw(
        file,
        converter=converter,
        formats=settings.FONT_FORMATS,
        category="font",
    )
