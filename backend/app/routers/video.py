from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from pathlib import Path
import uuid
from typing import Optional

from app.services.video_converter import VideoConverter
from app.utils.file_handler import save_upload_file, cleanup_file
from app.utils.validation import validate_download_filename,  validate_file_size, validate_file_extension
from app.models.conversion import ConversionResponse, ConversionStatus, FileInfo
from app.config import settings
from app.utils.websocket_security import session_validator


router = APIRouter()
video_converter = VideoConverter()


@router.post("/convert", response_model=ConversionResponse)
async def convert_video(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    codec: Optional[str] = Form("libx264"),
    resolution: Optional[str] = Form("original"),
    bitrate: Optional[str] = Form("2M"),
):
    """
    Convert a video to a different format

    - **file**: Video file to convert
    - **output_format**: Target format (mp4, avi, mov, mkv, webm, flv, wmv)
    - **codec**: Video codec (libx264, libx265, libvpx-vp9, default: libx264)
    - **resolution**: Target resolution (480p, 720p, 1080p, 4k, original, default: original)
    - **bitrate**: Video bitrate (e.g., 2M, 5M, default: 2M)
    """
    session_id = str(uuid.uuid4())
    session_validator.register_session(session_id)

    try:
        # Validate file size
        validate_file_size(file, "video")

        # Validate file extension
        input_format = validate_file_extension(file.filename, settings.VIDEO_FORMATS)

        # Validate output format
        if output_format.lower() not in settings.VIDEO_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported output format: {output_format}"
            )

        # Save uploaded file
        input_path = await save_upload_file(file, settings.TEMP_DIR)

        # Convert video
        options = {
            "codec": codec,
            "resolution": resolution,
            "bitrate": bitrate,
        }

        output_path = await video_converter.convert(
            input_path=input_path,
            output_format=output_format.lower(),
            options=options,
            session_id=session_id
        )

        # Clean up input file
        cleanup_file(input_path)

        # Generate download URL
        download_url = f"/api/video/download/{output_path.name}"

        return ConversionResponse(
            session_id=session_id,
            status=ConversionStatus.COMPLETED,
            message="Video conversion completed successfully",
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


@router.get("/download/{filename}")
async def download_video(filename: str):
    """Download converted video file"""
    # Validate filename to prevent path traversal
    file_path = validate_download_filename(filename, settings.UPLOAD_DIR)


    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream"
    )


@router.get("/formats")
async def get_supported_formats():
    """Get list of supported video formats"""
    formats = await video_converter.get_supported_formats()
    return {
        "input_formats": formats["input"],
        "output_formats": formats["output"],
    }


@router.post("/info", response_model=FileInfo)
async def get_video_info(file: UploadFile = File(...)):
    """Get metadata about a video file"""
    try:
        # Validate file
        validate_file_size(file, "video")
        input_format = validate_file_extension(file.filename, settings.VIDEO_FORMATS)

        # Save file temporarily
        temp_path = await save_upload_file(file, settings.TEMP_DIR)

        # Get metadata
        metadata = await video_converter.get_video_metadata(temp_path)

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
        raise HTTPException(status_code=500, detail=f"Failed to get video info: {str(e)}")
