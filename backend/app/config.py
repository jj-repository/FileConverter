from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Set
from app.utils.binary_paths import get_ffmpeg_path, get_ffprobe_path, get_pandoc_path


class Settings(BaseSettings):
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # File storage paths
    BASE_DIR: Path = Path(__file__).resolve().parent
    UPLOAD_DIR: Path = BASE_DIR / "static" / "uploads"
    TEMP_DIR: Path = BASE_DIR / "static" / "temp"

    # File size limits (in bytes)
    MAX_UPLOAD_SIZE: int = 524288000  # 500MB
    VIDEO_MAX_SIZE: int = 524288000   # 500MB
    IMAGE_MAX_SIZE: int = 104857600   # 100MB
    AUDIO_MAX_SIZE: int = 104857600   # 100MB
    DOCUMENT_MAX_SIZE: int = 52428800  # 50MB

    # Cleanup settings
    TEMP_FILE_LIFETIME: int = 3600  # 1 hour in seconds

    # Binary paths (will be set after initialization to use bundled binaries)
    FFMPEG_PATH: str = ""
    FFPROBE_PATH: str = ""
    PANDOC_PATH: str = ""

    # Supported formats
    IMAGE_FORMATS: Set[str] = {"png", "jpg", "jpeg", "webp", "gif", "bmp", "tiff", "ico"}
    VIDEO_FORMATS: Set[str] = {"mp4", "avi", "mov", "mkv", "webm", "flv", "wmv"}
    AUDIO_FORMATS: Set[str] = {"mp3", "wav", "flac", "aac", "ogg", "m4a", "wma"}
    DOCUMENT_FORMATS: Set[str] = {"txt", "pdf", "docx", "md", "html", "rtf"}

    # CORS settings
    ALLOWED_ORIGINS: list = [
        "http://localhost:5173",  # Vite default dev server
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Set binary paths (bundled binaries take priority, fall back to system)
settings.FFMPEG_PATH = get_ffmpeg_path()
settings.FFPROBE_PATH = get_ffprobe_path()
settings.PANDOC_PATH = get_pandoc_path()
