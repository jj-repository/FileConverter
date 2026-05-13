from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.config import settings
from app.models.conversion import ConversionResponse, FileInfo
from app.routers.base_router import handle_convert, handle_download, handle_formats, handle_info
from app.services.video_converter import VideoConverter
from app.utils.validation import VIDEO_MIME_TYPES
from app.utils.websocket_security import check_rate_limit

# Audio container formats the user can request as a video-converter output
# (the video stream is dropped, audio is re-encoded). Kept narrower than
# settings.AUDIO_FORMATS because not every audio container has a sensible
# encoder default for arbitrary video sources.
AUDIO_EXTRACT_FORMATS: set = {"mp3", "aac", "m4a", "ogg", "opus", "flac", "wav", "wma"}

router = APIRouter()
converter = VideoConverter()

VideoCodec = Literal["libx264", "libx265", "libvpx", "libvpx-vp9", "mpeg4", "h264"]
VideoResolution = Literal["original", "480p", "720p", "1080p", "4k", "2k"]
# Includes audio bitrates (128k-320k) because the video endpoint also handles
# audio extraction (Extract Audio toggle), where the frontend sends a kbps
# value matching the AUDIO_BITRATES dropdown.
VideoBitrate = Literal[
    "500k", "1M", "2M", "3M", "4M", "5M", "8M", "10M",
    "128k", "192k", "256k", "320k",
]

VIDEO_MIME_MAP = {
    "mp4": "video/mp4",
    "avi": "video/x-msvideo",
    "mov": "video/quicktime",
    "mkv": "video/x-matroska",
    "webm": "video/webm",
    "flv": "video/x-flv",
    "wmv": "video/x-ms-wmv",
    "m4v": "video/x-m4v",
    "3gp": "video/3gpp",
    "3g2": "video/3gpp2",
    "ts": "video/mp2t",
    "ogv": "video/ogg",
}


@router.post(
    "/convert", response_model=ConversionResponse, dependencies=[Depends(check_rate_limit)]
)
async def convert_video(
    file: UploadFile = File(...),
    output_format: str = Form(...),
    codec: Annotated[Optional[VideoCodec], Form(description="Video codec")] = None,
    resolution: Annotated[
        Optional[VideoResolution], Form(description="Target resolution")
    ] = "original",
    bitrate: Annotated[Optional[VideoBitrate], Form(description="Video bitrate")] = "2M",
):
    """Convert a video to a different format."""
    return await handle_convert(
        file,
        output_format,
        {"codec": codec, "resolution": resolution, "bitrate": bitrate},
        converter=converter,
        formats=settings.VIDEO_FORMATS,
        category="video",
        mime_types=VIDEO_MIME_TYPES,
        api_prefix="video",
        extra_output_formats=AUDIO_EXTRACT_FORMATS,
    )


@router.get("/download/{filename}", dependencies=[Depends(check_rate_limit)])
async def download_video(filename: str):
    """Download converted video file."""
    return await handle_download(filename, VIDEO_MIME_MAP)


@router.get("/formats", dependencies=[Depends(check_rate_limit)])
async def get_supported_formats():
    """Get list of supported video formats."""
    return await handle_formats(converter)


@router.post("/info", response_model=FileInfo, dependencies=[Depends(check_rate_limit)])
async def get_video_info(file: UploadFile = File(...)):
    """Get metadata about a video file."""
    return await handle_info(
        file,
        converter=converter,
        formats=settings.VIDEO_FORMATS,
        category="video",
        metadata_getter="get_video_metadata",
    )
