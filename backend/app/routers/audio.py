from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from pathlib import Path
import uuid
from typing import Optional

from app.services.audio_converter import AudioConverter
from app.utils.file_handler import save_upload_file, cleanup_file
from app.utils.validation import validate_download_filename,  validate_file_size, validate_file_extension
from app.models.conversion import ConversionResponse, ConversionStatus, FileInfo
from app.config import settings


router = APIRouter()
audio_converter = AudioConverter()


@router.post("/convert", response_model=ConversionResponse)
async def convert_audio(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    codec: Optional[str] = Form(None),
    bitrate: Optional[str] = Form("192k"),
    sample_rate: Optional[int] = Form(None),
    channels: Optional[int] = Form(None),
):
    """
    Convert an audio file to a different format

    - **file**: Audio file to convert
    - **output_format**: Target format (mp3, wav, flac, aac, ogg, m4a, wma)
    - **codec**: Audio codec (optional, will auto-select based on format)
    - **bitrate**: Audio bitrate (e.g., 128k, 192k, 320k, default: 192k)
    - **sample_rate**: Sample rate in Hz (e.g., 44100, 48000, optional)
    - **channels**: Number of channels (1=mono, 2=stereo, optional)
    """
    session_id = str(uuid.uuid4())

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

        # Convert audio
        options = {
            "codec": codec,
            "bitrate": bitrate,
            "sample_rate": sample_rate,
            "channels": channels,
        }

        output_path = await audio_converter.convert(
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

        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@router.get("/download/{filename}")
async def download_audio(filename: str):
    """Download converted audio file"""
    # Validate filename to prevent path traversal
    file_path = validate_download_filename(filename, settings.UPLOAD_DIR)


    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream"
    )


@router.get("/formats")
async def get_supported_formats():
    """Get list of supported audio formats"""
    formats = await audio_converter.get_supported_formats()
    return {
        "input_formats": formats["input"],
        "output_formats": formats["output"],
    }


@router.post("/info", response_model=FileInfo)
async def get_audio_info(file: UploadFile = File(...)):
    """Get metadata about an audio file"""
    try:
        # Validate file
        validate_file_size(file, "audio")
        input_format = validate_file_extension(file.filename, settings.AUDIO_FORMATS)

        # Save file temporarily
        temp_path = await save_upload_file(file, settings.TEMP_DIR)

        # Get metadata
        metadata = await audio_converter.get_audio_metadata(temp_path)

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
        raise HTTPException(status_code=500, detail=f"Failed to get audio info: {str(e)}")
