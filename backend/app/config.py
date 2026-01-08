from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from pathlib import Path
from typing import Set
import logging
import sys
from app.utils.binary_paths import get_ffmpeg_path, get_ffprobe_path, get_pandoc_path

# Configure logger for config warnings
_config_logger = logging.getLogger(__name__)

# Minimum length for admin API key (16 characters provides reasonable entropy)
MIN_ADMIN_API_KEY_LENGTH = 16


class Settings(BaseSettings):
    # Server settings - default to localhost for security
    # For production deployment:
    #   - Set HOST="0.0.0.0" via environment variable to accept external connections
    #   - Ensure proper firewall rules and reverse proxy (nginx/caddy) are configured
    #   - Enable HTTPS via reverse proxy, not directly in this app
    #   - Update ALLOWED_ORIGINS to match your production domain
    HOST: str = "127.0.0.1"
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
    ALLOWED_AUDIO_CODECS: Set[str] = {"aac", "libmp3lame", "libvorbis", "libopus", "flac", "pcm_s16le", "wmav2"}
    ALLOWED_RESOLUTIONS: Set[str] = {"original", "480p", "720p", "1080p", "4k", "2k"}
    ALLOWED_BITRATES: Set[str] = {"500k", "1M", "2M", "3M", "4M", "5M", "8M", "10M", "128k", "192k", "256k", "320k"}
    ALLOWED_SAMPLE_RATES: Set[str] = {"44100", "48000", "96000", "22050"}
    ALLOWED_AUDIO_CHANNELS: Set[str] = {"1", "2"}

    # Subprocess timeout (in seconds)
    SUBPROCESS_TIMEOUT: int = 600  # 10 minutes max for conversions

    # Security: Trusted proxy configuration
    # Set TRUSTED_PROXIES to a comma-separated list of IP addresses or CIDR ranges
    # that are allowed to set X-Forwarded-For headers. If empty, X-Forwarded-For is ignored.
    # Example: TRUSTED_PROXIES="127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
    TRUSTED_PROXIES: str = ""

    # CORS settings (can be overridden via environment variable ALLOWED_ORIGINS as comma-separated list)
    # In production (DEBUG=False), set ALLOWED_ORIGINS to your actual domain(s)
    # Example: ALLOWED_ORIGINS="https://myapp.com,https://www.myapp.com"
    ALLOWED_ORIGINS: str = ""

    # Admin API key for cache management endpoints (set via ADMIN_API_KEY environment variable)
    # If not set, admin endpoints will be disabled in production (non-DEBUG mode)
    # Must be at least MIN_ADMIN_API_KEY_LENGTH characters when set
    ADMIN_API_KEY: str = ""

    @field_validator('ADMIN_API_KEY')
    @classmethod
    def validate_admin_api_key(cls, v: str) -> str:
        """Validate ADMIN_API_KEY has sufficient length when set"""
        if v and len(v) < MIN_ADMIN_API_KEY_LENGTH:
            warning_msg = (
                f"SECURITY WARNING: ADMIN_API_KEY is set but too short "
                f"(minimum {MIN_ADMIN_API_KEY_LENGTH} characters required, got {len(v)}). "
                f"Admin endpoints will be disabled. Use a longer, randomly generated key."
            )
            _config_logger.warning(warning_msg)
            print(f"\n{'='*80}\n{warning_msg}\n{'='*80}\n", file=sys.stderr)
            # Return empty string to disable admin endpoints with weak key
            return ""
        return v

    @property
    def cors_origins(self) -> list:
        """Parse ALLOWED_ORIGINS string into list.

        In DEBUG mode, allows localhost origins for development.
        In production, requires explicit ALLOWED_ORIGINS configuration.
        """
        # If explicit origins are configured, use those
        if self.ALLOWED_ORIGINS:
            # Handle both string and list types (list for testing)
            if isinstance(self.ALLOWED_ORIGINS, list):
                origins = self.ALLOWED_ORIGINS
            else:
                origins = [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

            # In production, warn if localhost origins are configured
            if not self.DEBUG:
                localhost_origins = [o for o in origins if "localhost" in o or "127.0.0.1" in o]
                if localhost_origins:
                    import logging
                    logging.getLogger(__name__).warning(
                        f"Localhost origins configured in production mode: {localhost_origins}. "
                        "This may be a security risk."
                    )
            return origins

        # In DEBUG mode only, allow localhost origins for development
        if self.DEBUG:
            return [
                "http://localhost:5173",
                "http://localhost:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000",
            ]

        # Production with no configured origins - return empty list (no CORS)
        return []

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


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
