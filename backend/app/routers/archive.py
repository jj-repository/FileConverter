from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from fastapi.responses import FileResponse
from pathlib import Path
import uuid
from typing import Optional, Annotated

from app.services.archive_converter import ArchiveConverter
from app.utils.file_handler import save_upload_file, cleanup_file
from app.utils.validation import validate_file_size, validate_file_extension, validate_download_filename
from app.models.conversion import ConversionResponse, ConversionStatus, FileInfo
from app.config import settings
from app.utils.websocket_security import session_validator, check_rate_limit


router = APIRouter()
archive_converter = ArchiveConverter()


@router.post("/convert", response_model=ConversionResponse, dependencies=[Depends(check_rate_limit)])
async def convert_archive(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    compression_level: Annotated[Optional[int], Form(ge=0, le=9, description="Compression level (0=none, 9=maximum)")] = 6,
):
    """
    Convert an archive to a different format

    - **file**: Archive file to convert (ZIP, TAR, TAR.GZ, 7Z, etc.)
    - **output_format**: Target format (zip, tar, tar.gz, 7z, etc.)
    - **compression_level**: Compression level 0-9 (0=none, 9=maximum, default: 6)
    """
    session_id = str(uuid.uuid4())
    session_validator.register_session(session_id)

    try:
        # Validate file size
        validate_file_size(file, "archive")

        # Validate file extension
        input_format = validate_file_extension(file.filename, settings.ARCHIVE_FORMATS)

        # Validate output format
        if output_format.lower() not in settings.ARCHIVE_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported output format: {output_format}"
            )

        # Save uploaded file
        input_path = await save_upload_file(file, settings.TEMP_DIR)

        # Convert archive
        options = {
            "compression_level": compression_level,
        }

        output_path = await archive_converter.convert_with_cache(
            input_path=input_path,
            output_format=output_format.lower(),
            options=options,
            session_id=session_id
        )

        # Clean up input file
        cleanup_file(input_path)

        # Generate download URL
        download_url = f"/api/archive/download/{output_path.name}"

        return ConversionResponse(
            session_id=session_id,
            status=ConversionStatus.COMPLETED,
            message="Archive conversion completed successfully",
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


# MIME type mapping for archive formats
ARCHIVE_MIME_TYPES = {
    "zip": "application/zip",
    "tar": "application/x-tar",
    "tar.gz": "application/gzip",
    "tgz": "application/gzip",
    "tar.bz2": "application/x-bzip2",
    "tbz2": "application/x-bzip2",
    "gz": "application/gzip",
    "7z": "application/x-7z-compressed",
}


@router.get("/download/{filename}")
async def download_archive(filename: str):
    """Download converted archive file"""
    # Validate filename to prevent path traversal
    file_path = validate_download_filename(filename, settings.UPLOAD_DIR)

    # Determine MIME type from extension (handle compound extensions like .tar.gz)
    if filename.endswith(".tar.gz"):
        media_type = "application/gzip"
    elif filename.endswith(".tar.bz2"):
        media_type = "application/x-bzip2"
    else:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        media_type = ARCHIVE_MIME_TYPES.get(ext, "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/formats", dependencies=[Depends(check_rate_limit)])
async def get_supported_formats():
    """Get list of supported archive formats"""
    formats = await archive_converter.get_supported_formats()
    return {
        "input_formats": formats["input"],
        "output_formats": formats["output"],
    }


@router.post("/info", response_model=FileInfo, dependencies=[Depends(check_rate_limit)])
async def get_archive_info(file: UploadFile = File(...)):
    """Get metadata about an archive file"""
    try:
        # Validate file
        validate_file_size(file, "archive")
        input_format = validate_file_extension(file.filename, settings.ARCHIVE_FORMATS)

        # Save file temporarily
        temp_path = await save_upload_file(file, settings.TEMP_DIR)

        # Get metadata and file size before cleanup
        metadata = await archive_converter.get_archive_info(temp_path)
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
        raise HTTPException(status_code=500, detail=f"Failed to get archive info: {str(e)}")
