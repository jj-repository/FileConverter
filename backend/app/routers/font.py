from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from starlette.background import BackgroundTask

from app.config import settings
from app.models.conversion import ConversionResponse, FileInfo
from app.routers.base_router import (
    cleanup_after_download,
    handle_action,
    handle_convert,
    handle_info_raw,
)
from app.services.font_converter import FontConverter
from app.utils.file_handler import make_content_disposition
from app.utils.validation import (
    FONT_MIME_TYPES,
    validate_download_filename,
)
from app.utils.websocket_security import check_rate_limit

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
    return await handle_action(
        file,
        action=converter.optimize_font,
        formats=settings.FONT_FORMATS,
        category="font",
        mime_types=FONT_MIME_TYPES,
        api_prefix="font",
        action_label="Optimization",
    )


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
