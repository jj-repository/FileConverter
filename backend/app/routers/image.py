from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.config import settings
from app.models.conversion import ConversionResponse, FileInfo
from app.routers.base_router import handle_convert, handle_download, handle_formats, handle_info
from app.services.image_converter import ImageConverter
from app.utils.validation import IMAGE_MIME_TYPES
from app.utils.websocket_security import check_rate_limit

router = APIRouter()
converter = ImageConverter()

IMAGE_MIME_MAP = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "gif": "image/gif",
    "bmp": "image/bmp",
    "tiff": "image/tiff",
    "ico": "image/x-icon",
    "heic": "image/heic",
    "heif": "image/heif",
    "svg": "image/svg+xml",
    "tga": "image/x-tga",
}


@router.post(
    "/convert", response_model=ConversionResponse, dependencies=[Depends(check_rate_limit)]
)
async def convert_image(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    quality: Annotated[
        Optional[int], Form(ge=1, le=100, description="Quality for JPEG/WEBP (1-100)")
    ] = 95,
    width: Annotated[
        Optional[int], Form(ge=1, le=10000, description="Width for resize (1-10000 pixels)")
    ] = None,
    height: Annotated[
        Optional[int], Form(ge=1, le=10000, description="Height for resize (1-10000 pixels)")
    ] = None,
):
    """Convert an image to a different format."""
    return await handle_convert(
        file,
        output_format,
        {"quality": quality, "width": width, "height": height},
        converter=converter,
        formats=settings.IMAGE_FORMATS,
        category="image",
        mime_types=IMAGE_MIME_TYPES,
        api_prefix="image",
    )


@router.get("/download/{filename}", dependencies=[Depends(check_rate_limit)])
async def download_image(filename: str):
    """Download converted image file."""
    return await handle_download(filename, IMAGE_MIME_MAP)


@router.get("/formats", dependencies=[Depends(check_rate_limit)])
async def get_supported_formats():
    """Get list of supported image formats."""
    return await handle_formats(converter)


@router.post("/info", response_model=FileInfo, dependencies=[Depends(check_rate_limit)])
async def get_image_info(file: UploadFile = File(...)):
    """Get metadata about an image file."""
    return await handle_info(
        file,
        converter=converter,
        formats=settings.IMAGE_FORMATS,
        category="image",
        metadata_getter="get_image_metadata",
    )
