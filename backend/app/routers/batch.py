import re
import uuid
from pathlib import Path
from typing import Annotated, List, Literal, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.config import settings
from app.middleware.error_handler import sanitize_error_message
from app.models.conversion import BatchConversionResponse, BatchZipResponse
from app.services.batch_converter import BatchConverter
from app.utils.file_handler import (
    cleanup_file,
    make_content_disposition,
    save_upload_file,
)
from app.utils.validation import (
    AUDIO_MIME_TYPES,
    DOCUMENT_MIME_TYPES,
    IMAGE_MIME_TYPES,
    VIDEO_MIME_TYPES,
    validate_download_filename,
    validate_file_size,
    validate_mime_type,
)
from app.utils.websocket_security import check_rate_limit, session_validator


def _cleanup_after_download(path: str):
    try:
        Path(path).unlink(missing_ok=True)
    except Exception:
        pass


router = APIRouter()
batch_converter = BatchConverter()


# Whitelist types for batch parameters (reuse from other routers)
VideoCodec = Literal["libx264", "libx265", "libvpx", "libvpx-vp9", "mpeg4", "h264"]
VideoResolution = Literal["original", "480p", "720p", "1080p", "4k", "2k"]
VideoBitrate = Literal[
    "500k", "1M", "2M", "3M", "4M", "5M", "8M", "10M", "128k", "192k", "256k", "320k"
]


@router.post(
    "/convert",
    response_model=BatchConversionResponse,
    dependencies=[Depends(check_rate_limit)],
)
async def convert_batch(
    files: List[UploadFile] = File(...),
    output_format: str = Form(...),
    parallel: Optional[bool] = Form(True),
    # Image options with validation
    quality: Annotated[
        Optional[int], Form(ge=1, le=100, description="Image quality (1-100)")
    ] = None,
    width: Annotated[
        Optional[int], Form(ge=1, le=10000, description="Image width (1-10000)")
    ] = None,
    height: Annotated[
        Optional[int], Form(ge=1, le=10000, description="Image height (1-10000)")
    ] = None,
    # Video options with validation
    codec: Annotated[Optional[VideoCodec], Form(description="Video codec")] = None,
    resolution: Annotated[
        Optional[VideoResolution], Form(description="Video resolution")
    ] = None,
    bitrate: Annotated[
        Optional[VideoBitrate], Form(description="Video/audio bitrate")
    ] = None,
    # Audio options with validation
    sample_rate: Annotated[
        Optional[int],
        Form(ge=8000, le=192000, description="Audio sample rate (8000-192000)"),
    ] = None,
    channels: Annotated[
        Optional[int], Form(ge=1, le=2, description="Audio channels (1=mono, 2=stereo)")
    ] = None,
    # Document options
    preserve_formatting: Optional[bool] = Form(None),
    toc: Optional[bool] = Form(None),
):
    """
    Convert multiple files in batch

    - **files**: List of files to convert
    - **output_format**: Target format for all files
    - **parallel**: Process files in parallel (default: True)
    - Additional format-specific options are passed through to converters
    """
    # Validate output format against all supported formats
    all_formats = (
        settings.IMAGE_FORMATS
        | settings.VIDEO_FORMATS
        | settings.AUDIO_FORMATS
        | settings.DOCUMENT_FORMATS
    )
    if output_format.lower() not in all_formats:
        raise HTTPException(
            status_code=400, detail=f"Unsupported output format: {output_format}"
        )

    session_id = str(uuid.uuid4())
    session_validator.register_session(session_id)
    input_paths = []
    output_paths = []

    try:
        # Validate that we have files
        if not files or len(files) == 0:
            raise HTTPException(status_code=400, detail="No files provided")

        # Limit batch size
        max_batch_size = 100  # Increased from 20 to 100
        if len(files) > max_batch_size:
            raise HTTPException(
                status_code=400,
                detail=f"Batch size exceeds maximum of {max_batch_size} files",
            )

        # Save all uploaded files
        for file in files:
            # Validate file size based on file type
            input_format = (
                file.filename.split(".")[-1].lower() if "." in file.filename else ""
            )

            # Determine file type for size validation
            if input_format in settings.IMAGE_FORMATS:
                file_type = "image"
            elif input_format in settings.VIDEO_FORMATS:
                file_type = "video"
            elif input_format in settings.AUDIO_FORMATS:
                file_type = "audio"
            elif input_format in settings.DOCUMENT_FORMATS:
                file_type = "document"
            else:
                raise HTTPException(
                    status_code=400, detail=f"Unsupported file format: {input_format}"
                )

            validate_file_size(file, file_type)

            # Save file
            input_path = await save_upload_file(file, settings.TEMP_DIR)

            # Validate MIME type to prevent file type spoofing
            mime_types_map = {
                "image": IMAGE_MIME_TYPES,
                "video": VIDEO_MIME_TYPES,
                "audio": AUDIO_MIME_TYPES,
                "document": DOCUMENT_MIME_TYPES,
            }
            if file_type in mime_types_map:
                validate_mime_type(input_path, mime_types_map[file_type])

            input_paths.append(input_path)

        # Build options dict
        options = {}

        # Image options
        if quality is not None:
            options["quality"] = quality
        if width is not None:
            options["width"] = width
        if height is not None:
            options["height"] = height

        # Video options
        if codec is not None:
            options["codec"] = codec
        if resolution is not None:
            options["resolution"] = resolution
        if bitrate is not None:
            options["bitrate"] = bitrate

        # Audio options
        if sample_rate is not None:
            options["sample_rate"] = sample_rate
        if channels is not None:
            options["channels"] = channels

        # Document options
        if preserve_formatting is not None:
            options["preserve_formatting"] = preserve_formatting
        if toc is not None:
            options["toc"] = toc

        # Convert files
        results = await batch_converter.convert_batch(
            input_paths=input_paths,
            output_format=output_format.lower(),
            options=options,
            session_id=session_id,
            parallel=parallel,
        )

        # Clean up input files
        for input_path in input_paths:
            cleanup_file(input_path)

        # Collect successful output paths for potential ZIP creation
        for result in results:
            if result.get("success") and "output_path" in result:
                output_paths.append(result["output_path"])

        # Calculate success statistics
        total_files = len(results)
        successful = sum(1 for r in results if r.get("success"))
        failed = total_files - successful

        return {
            "session_id": session_id,
            "total_files": total_files,
            "successful": successful,
            "failed": failed,
            "results": results,
            "message": f"Batch conversion completed: {successful}/{total_files} successful",
        }

    except HTTPException:
        raise
    except Exception as e:
        # Clean up on error
        for input_path in input_paths:
            cleanup_file(input_path)
        for output_path in output_paths:
            cleanup_file(Path(output_path))

        raise HTTPException(
            status_code=500,
            detail=f"Batch conversion failed: {sanitize_error_message(str(e))}",
        )


@router.post("/download-zip", response_model=BatchZipResponse)
async def create_download_zip(
    session_id: str = Form(...),
    filenames: List[str] = Form(...),
):
    """
    Create a ZIP archive of converted files for download

    - **session_id**: Batch session ID
    - **filenames**: List of filenames to include in ZIP
    """
    # Validate session_id format
    if not re.match(
        r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$", session_id
    ):
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    try:
        # Validate and collect file paths
        file_paths = []
        for filename in filenames:
            # Validate filename to prevent path traversal
            file_path = validate_download_filename(filename, settings.UPLOAD_DIR)
            if file_path.exists():
                file_paths.append(file_path)

        if not file_paths:
            raise HTTPException(status_code=404, detail="No files found")

        # Create ZIP archive
        zip_name = f"batch_{session_id}.zip"
        await batch_converter.create_zip_archive(file_paths, zip_name)

        return {
            "zip_file": zip_name,
            "download_url": f"/api/batch/download/{zip_name}",
            "file_count": len(file_paths),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create ZIP: {sanitize_error_message(str(e))}",
        )


@router.get("/download/{filename}", dependencies=[Depends(check_rate_limit)])
async def download_file(filename: str):
    """Download a converted file or ZIP archive"""
    # Validate filename to prevent path traversal
    file_path = validate_download_filename(filename, settings.UPLOAD_DIR)

    # Determine MIME type - batch downloads are typically ZIP files
    if filename.endswith(".zip"):
        media_type = "application/zip"
    else:
        media_type = "application/octet-stream"

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type,
        headers={"Content-Disposition": make_content_disposition(filename)},
    )
