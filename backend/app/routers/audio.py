from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.config import settings
from app.models.conversion import ConversionResponse, FileInfo
from app.routers.base_router import handle_convert, handle_download, handle_formats, handle_info
from app.services.audio_converter import AudioConverter
from app.utils.validation import AUDIO_MIME_TYPES
from app.utils.websocket_security import check_rate_limit

router = APIRouter()
converter = AudioConverter()

AudioCodec = Literal["aac", "libmp3lame", "libvorbis", "libopus", "flac", "pcm_s16le", "wmav2"]
AudioBitrate = Literal["128k", "192k", "256k", "320k"]

AUDIO_MIME_MAP = {
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


@router.post(
    "/convert", response_model=ConversionResponse, dependencies=[Depends(check_rate_limit)]
)
async def convert_audio(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    codec: Annotated[
        Optional[AudioCodec], Form(description="Audio codec (auto-selected if not specified)")
    ] = None,
    bitrate: Annotated[Optional[AudioBitrate], Form(description="Audio bitrate")] = "192k",
    sample_rate: Annotated[
        Optional[int], Form(ge=8000, le=192000, description="Sample rate in Hz (8000-192000)")
    ] = None,
    channels: Annotated[
        Optional[int], Form(ge=1, le=2, description="Number of channels (1=mono, 2=stereo)")
    ] = None,
):
    """Convert an audio file to a different format."""
    return await handle_convert(
        file,
        output_format,
        {"codec": codec, "bitrate": bitrate, "sample_rate": sample_rate, "channels": channels},
        converter=converter,
        formats=settings.AUDIO_FORMATS,
        category="audio",
        mime_types=AUDIO_MIME_TYPES,
        api_prefix="audio",
    )


@router.get("/download/{filename}", dependencies=[Depends(check_rate_limit)])
async def download_audio(filename: str):
    """Download converted audio file."""
    return await handle_download(filename, AUDIO_MIME_MAP)


@router.get("/formats", dependencies=[Depends(check_rate_limit)])
async def get_supported_formats():
    """Get list of supported audio formats."""
    return await handle_formats(converter)


@router.post("/info", response_model=FileInfo, dependencies=[Depends(check_rate_limit)])
async def get_audio_info(file: UploadFile = File(...)):
    """Get metadata about an audio file."""
    return await handle_info(
        file,
        converter=converter,
        formats=settings.AUDIO_FORMATS,
        category="audio",
        metadata_getter="get_audio_metadata",
    )
