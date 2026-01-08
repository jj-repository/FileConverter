from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Query, Depends
from fastapi.responses import FileResponse
from pathlib import Path
import uuid
from typing import Optional, Annotated

from app.services.image_converter import ImageConverter
from app.utils.file_handler import save_upload_file, cleanup_file, make_content_disposition
from app.utils.validation import validate_file_size, validate_file_extension, validate_download_filename
from app.models.conversion import ConversionResponse, ConversionStatus, FileInfo
from app.config import settings
from app.utils.websocket_security import session_validator, check_rate_limit
from app.middleware.error_handler import sanitize_error_message


router = APIRouter()
image_converter = ImageConverter()


@router.post("/convert", response_model=ConversionResponse, dependencies=[Depends(check_rate_limit)])
async def convert_image(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    quality: Annotated[Optional[int], Form(ge=1, le=100, description="Quality for JPEG/WEBP (1-100)")] = 95,
    width: Annotated[Optional[int], Form(ge=1, le=10000, description="Width for resize (1-10000 pixels)")] = None,
    height: Annotated[Optional[int], Form(ge=1, le=10000, description="Height for resize (1-10000 pixels)")] = None,
):
    """
    Convert an image to a different format

    - **file**: Image file to convert
    - **output_format**: Target format (png, jpg, webp, gif, bmp, tiff, ico)
    - **quality**: Quality for JPEG/WEBP (1-100, default: 95)
    - **width**: Optional width for resize (1-10000 pixels)
    - **height**: Optional height for resize (1-10000 pixels)
    """
    session_id = str(uuid.uuid4())
    session_validator.register_session(session_id)

    try:
        # Validate file size
        validate_file_size(file, "image")

        # Validate file extension
        input_format = validate_file_extension(file.filename, settings.IMAGE_FORMATS)

        # Validate output format
        if output_format.lower() not in settings.IMAGE_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported output format: {output_format}"
            )

        # Save uploaded file
        input_path = await save_upload_file(file, settings.TEMP_DIR)

        # Convert image
        options = {
            "quality": quality,
            "width": width,
            "height": height,
        }

        output_path = await image_converter.convert_with_cache(
            input_path=input_path,
            output_format=output_format.lower(),
            options=options,
            session_id=session_id
        )

        # Clean up input file
        cleanup_file(input_path)

        # Generate download URL
        download_url = f"/api/image/download/{output_path.name}"

        return ConversionResponse(
            session_id=session_id,
            status=ConversionStatus.COMPLETED,
            message="Image conversion completed successfully",
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


# MIME type mapping for image formats
IMAGE_MIME_TYPES = {
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


@router.get("/download/{filename}")
async def download_image(filename: str):
    """Download converted image file"""
    # Validate filename to prevent path traversal
    file_path = validate_download_filename(filename, settings.UPLOAD_DIR)

    # Determine MIME type from extension
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    media_type = IMAGE_MIME_TYPES.get(ext, "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type,
        headers={"Content-Disposition": make_content_disposition(filename)}
    )


@router.get("/formats", dependencies=[Depends(check_rate_limit)])
async def get_supported_formats():
    """Get list of supported image formats"""
    formats = await image_converter.get_supported_formats()
    return {
        "input_formats": formats["input"],
        "output_formats": formats["output"],
    }


@router.post("/info", response_model=FileInfo, dependencies=[Depends(check_rate_limit)])
async def get_image_info(file: UploadFile = File(...)):
    """Get metadata about an image file"""
    try:
        # Validate file
        validate_file_size(file, "image")
        input_format = validate_file_extension(file.filename, settings.IMAGE_FORMATS)

        # Save file temporarily
        temp_path = await save_upload_file(file, settings.TEMP_DIR)

        # Get metadata and file size before cleanup
        metadata = await image_converter.get_image_metadata(temp_path)
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
        raise HTTPException(status_code=500, detail=f"Failed to get image info: {sanitize_error_message(str(e))}")
