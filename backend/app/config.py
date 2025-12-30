from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Set
from app.utils.binary_paths import get_ffmpeg_path, get_ffprobe_path, get_pandoc_path


class Settings(BaseSettings):
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # File storage paths
    BASE_DIR: Path = Path(__file__).resolve().parent
    UPLOAD_DIR: Path = BASE_DIR / "static" / "uploads"
    TEMP_DIR: Path = BASE_DIR / "static" / "temp"
    OUTPUT_DIR: Path = BASE_DIR / "static" / "uploads"  # Base output directory

    # File size limits (in bytes)
    MAX_UPLOAD_SIZE: int = 524288000  # 500MB
    VIDEO_MAX_SIZE: int = 524288000   # 500MB
    IMAGE_MAX_SIZE: int = 104857600   # 100MB
    AUDIO_MAX_SIZE: int = 104857600   # 100MB
    DOCUMENT_MAX_SIZE: int = 52428800  # 50MB
    ARCHIVE_MAX_SIZE: int = 524288000  # 500MB
    SPREADSHEET_MAX_SIZE: int = 104857600  # 100MB
    SUBTITLE_MAX_SIZE: int = 10485760  # 10MB
    EBOOK_MAX_SIZE: int = 52428800  # 50MB
    FONT_MAX_SIZE: int = 20971520  # 20MB

    # Cleanup settings
    TEMP_FILE_LIFETIME: int = 3600  # 1 hour in seconds

    # Cache settings
    CACHE_ENABLED: bool = True
    CACHE_EXPIRATION_HOURS: int = 1  # Default cache lifetime
    CACHE_MAX_SIZE_MB: int = 1000  # Maximum cache size in MB

    # Binary paths (will be set after initialization to use bundled binaries)
    FFMPEG_PATH: str = ""
    FFPROBE_PATH: str = ""
    PANDOC_PATH: str = ""

    # Supported formats
    IMAGE_FORMATS: Set[str] = {"png", "jpg", "jpeg", "webp", "gif", "bmp", "tiff", "ico", "heic", "heif", "svg", "tga"}
    VIDEO_FORMATS: Set[str] = {"mp4", "avi", "mov", "mkv", "webm", "flv", "wmv", "m4v", "3gp", "3g2", "mts", "m2ts", "vob", "ts", "ogv"}
    AUDIO_FORMATS: Set[str] = {"mp3", "wav", "flac", "aac", "ogg", "m4a", "wma", "opus", "alac", "ape", "mka"}
    DOCUMENT_FORMATS: Set[str] = {"txt", "pdf", "docx", "md", "html", "rtf", "odt"}
    DATA_FORMATS: Set[str] = {"csv", "json", "xml", "yaml", "yml", "toml", "ini", "jsonl"}
    ARCHIVE_FORMATS: Set[str] = {"zip", "tar", "tar.gz", "tgz", "tar.bz2", "tbz2", "gz", "7z"}
    SPREADSHEET_FORMATS: Set[str] = {"xlsx", "xls", "ods", "csv", "tsv"}
    SUBTITLE_FORMATS: Set[str] = {"srt", "vtt", "ass", "ssa", "sub"}
    EBOOK_FORMATS: Set[str] = {"epub", "txt", "html", "pdf"}
    FONT_FORMATS: Set[str] = {"ttf", "otf", "woff", "woff2"}

    # FFmpeg allowed options (whitelist for security)
    ALLOWED_VIDEO_CODECS: Set[str] = {"libx264", "libx265", "libvpx", "libvpx-vp9", "mpeg4", "h264"}
    ALLOWED_AUDIO_CODECS: Set[str] = {"aac", "libmp3lame", "libvorbis", "libopus", "flac", "pcm_s16le"}
    ALLOWED_RESOLUTIONS: Set[str] = {"original", "480p", "720p", "1080p", "4k", "2k"}
    ALLOWED_BITRATES: Set[str] = {"500k", "1M", "2M", "3M", "4M", "5M", "8M", "10M", "128k", "192k", "256k", "320k"}
    ALLOWED_SAMPLE_RATES: Set[str] = {"44100", "48000", "96000", "22050"}
    ALLOWED_AUDIO_CHANNELS: Set[str] = {"1", "2"}

    # Subprocess timeout (in seconds)
    SUBPROCESS_TIMEOUT: int = 600  # 10 minutes max for conversions

    # CORS settings (can be overridden via environment variable ALLOWED_ORIGINS as comma-separated list)
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"

    @property
    def cors_origins(self) -> list:
        """Parse ALLOWED_ORIGINS string into list"""
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
        return self.ALLOWED_ORIGINS

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Cache directory
CACHE_DIR: Path = settings.OUTPUT_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Set binary paths (bundled binaries take priority, fall back to system)
settings.FFMPEG_PATH = get_ffmpeg_path()
settings.FFPROBE_PATH = get_ffprobe_path()
settings.PANDOC_PATH = get_pandoc_path()
