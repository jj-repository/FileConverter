from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.config import settings
from app.models.conversion import ConversionResponse, FileInfo
from app.routers.base_router import handle_convert, handle_download, handle_formats, handle_info
from app.services.archive_converter import ArchiveConverter
from app.utils.validation import ARCHIVE_MIME_TYPES
from app.utils.websocket_security import check_rate_limit

router = APIRouter()
converter = ArchiveConverter()

ARCHIVE_MIME_MAP = {
    "zip": "application/zip",
    "tar": "application/x-tar",
    "tar.gz": "application/gzip",
    "tgz": "application/gzip",
    "tar.bz2": "application/x-bzip2",
    "tbz2": "application/x-bzip2",
    "gz": "application/gzip",
    "7z": "application/x-7z-compressed",
}


@router.post(
    "/convert", response_model=ConversionResponse, dependencies=[Depends(check_rate_limit)]
)
async def convert_archive(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    compression_level: Annotated[
        Optional[int], Form(ge=0, le=9, description="Compression level (0=none, 9=maximum)")
    ] = 6,
):
    """Convert an archive to a different format."""
    return await handle_convert(
        file,
        output_format,
        {"compression_level": compression_level},
        converter=converter,
        formats=settings.ARCHIVE_FORMATS,
        category="archive",
        mime_types=ARCHIVE_MIME_TYPES,
        api_prefix="archive",
    )


@router.get("/download/{filename}", dependencies=[Depends(check_rate_limit)])
async def download_archive(filename: str):
    """Download converted archive file."""
    return await handle_download(filename, ARCHIVE_MIME_MAP)


@router.get("/formats", dependencies=[Depends(check_rate_limit)])
async def get_supported_formats():
    """Get list of supported archive formats."""
    return await handle_formats(converter)


@router.post("/info", response_model=FileInfo, dependencies=[Depends(check_rate_limit)])
async def get_archive_info(file: UploadFile = File(...)):
    """Get metadata about an archive file."""
    return await handle_info(
        file,
        converter=converter,
        formats=settings.ARCHIVE_FORMATS,
        category="archive",
        metadata_getter="get_archive_info",
    )
