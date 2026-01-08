from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from fastapi.responses import FileResponse
from pathlib import Path
import uuid
from typing import Optional, Annotated, Literal

from app.services.audio_converter import AudioConverter
from app.utils.file_handler import save_upload_file, cleanup_file, make_content_disposition
from app.utils.validation import validate_download_filename, validate_file_size, validate_file_extension, validate_mime_type, AUDIO_MIME_TYPES
from app.models.conversion import ConversionResponse, ConversionStatus, FileInfo
from app.config import settings
from app.utils.websocket_security import session_validator, check_rate_limit
from app.middleware.error_handler import sanitize_error_message


router = APIRouter()
audio_converter = AudioConverter()


# Whitelist types for audio parameters
AudioCodec = Literal["aac", "libmp3lame", "libvorbis", "libopus", "flac", "pcm_s16le", "wmav2"]
AudioBitrate = Literal["128k", "192k", "256k", "320k"]


@router.post("/convert", response_model=ConversionResponse, dependencies=[Depends(check_rate_limit)])
async def convert_audio(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    codec: Annotated[Optional[AudioCodec], Form(description="Audio codec (auto-selected if not specified)")] = None,
    bitrate: Annotated[Optional[AudioBitrate], Form(description="Audio bitrate")] = "192k",
    sample_rate: Annotated[Optional[int], Form(ge=8000, le=192000, description="Sample rate in Hz (8000-192000)")] = None,
    channels: Annotated[Optional[int], Form(ge=1, le=2, description="Number of channels (1=mono, 2=stereo)")] = None,
):
    """
    Convert an audio file to a different format

    - **file**: Audio file to convert
    - **output_format**: Target format (mp3, wav, flac, aac, ogg, m4a, wma)
    - **codec**: Audio codec (aac, libmp3lame, libvorbis, libopus, flac, pcm_s16le, wmav2)
    - **bitrate**: Audio bitrate (128k, 192k, 256k, 320k)
    - **sample_rate**: Sample rate in Hz (22050, 44100, 48000, 96000)
    - **channels**: Number of channels (1=mono, 2=stereo)
    """
    session_id = str(uuid.uuid4())
    session_validator.register_session(session_id)

    try:
        # Validate file size
        validate_file_size(file, "audio")

        # Validate file extension
        input_format = validate_file_extension(file.filename, settings.AUDIO_FORMATS)

        # Validate output format
        if output_format.lower() not in settings.AUDIO_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported output format: {output_format}"
            )

        # Save uploaded file
        input_path = await save_upload_file(file, settings.TEMP_DIR)

        # Validate MIME type to prevent file type spoofing
        validate_mime_type(input_path, AUDIO_MIME_TYPES)

        # Convert audio
        options = {
            "codec": codec,
            "bitrate": bitrate,
            "sample_rate": sample_rate,
            "channels": channels,
        }

        output_path = await audio_converter.convert_with_cache(
            input_path=input_path,
            output_format=output_format.lower(),
            options=options,
            session_id=session_id
        )

        # Clean up input file
        cleanup_file(input_path)

        # Generate download URL
        download_url = f"/api/audio/download/{output_path.name}"

        return ConversionResponse(
            session_id=session_id,
            status=ConversionStatus.COMPLETED,
            message="Audio conversion completed successfully",
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


# MIME type mapping for audio formats
AUDIO_MIME_TYPES = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "flac": "audio/flac",
    "aac": "audio/aac",
    "ogg": "audio/ogg",
    "m4a": "audio/mp4",
    "wma": "audio/x-ms-wma",
    "opus": "audio/opus",
    "mka": "audio/x-matroska",
}


@router.get("/download/{filename}")
async def download_audio(filename: str):
    """Download converted audio file"""
    # Validate filename to prevent path traversal
    file_path = validate_download_filename(filename, settings.UPLOAD_DIR)

    # Determine MIME type from extension
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    media_type = AUDIO_MIME_TYPES.get(ext, "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type,
        headers={"Content-Disposition": make_content_disposition(filename)}
    )


@router.get("/formats", dependencies=[Depends(check_rate_limit)])
async def get_supported_formats():
    """Get list of supported audio formats"""
    formats = await audio_converter.get_supported_formats()
    return {
        "input_formats": formats["input"],
        "output_formats": formats["output"],
    }


@router.post("/info", response_model=FileInfo, dependencies=[Depends(check_rate_limit)])
async def get_audio_info(file: UploadFile = File(...)):
    """Get metadata about an audio file"""
    try:
        # Validate file
        validate_file_size(file, "audio")
        input_format = validate_file_extension(file.filename, settings.AUDIO_FORMATS)

        # Save file temporarily
        temp_path = await save_upload_file(file, settings.TEMP_DIR)

        # Get metadata and file size before cleanup
        metadata = await audio_converter.get_audio_metadata(temp_path)
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
        raise HTTPException(status_code=500, detail=f"Failed to get audio info: {sanitize_error_message(str(e))}")
