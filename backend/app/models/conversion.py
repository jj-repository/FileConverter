from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum


class ConversionStatus(str, Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    CONVERTING = "converting"
    COMPLETED = "completed"
    FAILED = "failed"


class ImageFormat(str, Enum):
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    WEBP = "webp"
    GIF = "gif"
    BMP = "bmp"
    TIFF = "tiff"
    ICO = "ico"


class VideoFormat(str, Enum):
    MP4 = "mp4"
    AVI = "avi"
    MOV = "mov"
    MKV = "mkv"
    WEBM = "webm"
    FLV = "flv"
    WMV = "wmv"


class AudioFormat(str, Enum):
    MP3 = "mp3"
    WAV = "wav"
    FLAC = "flac"
    AAC = "aac"
    OGG = "ogg"
    M4A = "m4a"
    WMA = "wma"


class DocumentFormat(str, Enum):
    TXT = "txt"
    PDF = "pdf"
    DOCX = "docx"
    MD = "md"
    HTML = "html"
    RTF = "rtf"


class ImageConversionRequest(BaseModel):
    output_format: ImageFormat
    quality: Optional[int] = Field(default=95, ge=1, le=100)
    width: Optional[int] = Field(default=None, ge=1)
    height: Optional[int] = Field(default=None, ge=1)


class VideoConversionRequest(BaseModel):
    output_format: VideoFormat
    codec: Optional[str] = Field(default="libx264")
    resolution: Optional[str] = Field(default="original")  # e.g., "720p", "1080p"
    bitrate: Optional[str] = Field(default="2M")


class AudioConversionRequest(BaseModel):
    output_format: AudioFormat
    bitrate: Optional[str] = Field(default="192k")
    sample_rate: Optional[int] = Field(default=44100)
    channels: Optional[int] = Field(default=2, ge=1, le=2)


class DocumentConversionRequest(BaseModel):
    output_format: DocumentFormat


class ConversionResponse(BaseModel):
    session_id: str
    status: ConversionStatus
    message: str
    output_file: Optional[str] = None
    download_url: Optional[str] = None


class ProgressUpdate(BaseModel):
    session_id: str
    progress: float = Field(ge=0, le=100)
    status: ConversionStatus
    message: str
    current_operation: Optional[str] = None


class FileInfo(BaseModel):
    filename: str
    size: int
    format: str
    metadata: Optional[Dict[str, Any]] = None


class BatchFileResult(BaseModel):
    """Result for a single file in batch conversion"""
    filename: str
    success: bool
    output_path: Optional[str] = None
    error: Optional[str] = None


class BatchConversionResponse(BaseModel):
    """Response for batch conversion endpoint"""
    session_id: str
    total_files: int
    successful: int
    failed: int
    results: List[BatchFileResult]
    message: str


class BatchZipResponse(BaseModel):
    """Response for batch ZIP creation endpoint"""
    zip_file: str
    download_url: str
    file_count: int
