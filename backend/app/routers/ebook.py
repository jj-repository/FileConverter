from fastapi import APIRouter, Depends, File, Form, UploadFile
from starlette.background import BackgroundTask

from app.config import settings
from app.models.conversion import ConversionResponse, FileInfo
from app.routers.base_router import (
    cleanup_after_download,
    handle_convert,
    handle_info_raw,
)
from app.services.ebook_converter import EbookConverter
from app.utils.file_handler import make_content_disposition
from app.utils.validation import EBOOK_MIME_TYPES, validate_download_filename
from app.utils.websocket_security import check_rate_limit

router = APIRouter()
converter = EbookConverter()

EBOOK_MIME_MAP = {
    "epub": "application/epub+zip",
    "txt": "text/plain",
    "html": "text/html",
    "pdf": "application/pdf",
}


@router.post(
    "/convert", response_model=ConversionResponse, dependencies=[Depends(check_rate_limit)]
)
async def convert_ebook(
    file: UploadFile = File(...),
    output_format: str = Form(...),
):
    """Convert eBook file to target format (EPUB, TXT, HTML, PDF)."""
    return await handle_convert(
        file,
        output_format,
        {},
        converter=converter,
        formats=settings.EBOOK_FORMATS,
        category="ebook",
        mime_types=EBOOK_MIME_TYPES,
        api_prefix="ebook",
    )


@router.get("/download/{filename}", dependencies=[Depends(check_rate_limit)])
async def download_ebook(filename: str):
    """Download converted eBook file."""
    from fastapi.responses import FileResponse

    file_path = validate_download_filename(filename, settings.UPLOAD_DIR)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    media_type = EBOOK_MIME_MAP.get(ext, "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type,
        headers={"Content-Disposition": make_content_disposition(filename)},
        background=BackgroundTask(cleanup_after_download, str(file_path)),
    )


@router.get("/formats", dependencies=[Depends(check_rate_limit)])
async def get_ebook_formats():
    """Get supported eBook formats."""
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
    """Get information about an eBook file."""
    return await handle_info_raw(
        file,
        converter=converter,
        formats=settings.EBOOK_FORMATS,
        category="ebook",
    )
