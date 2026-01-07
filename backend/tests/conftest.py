"""
Shared pytest fixtures for FileConverter backend tests
"""

import pytest
import asyncio
from pathlib import Path
from typing import Generator
from fastapi.testclient import TestClient
import tempfile
import shutil
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import io
import json
from PIL import Image

# Test app imports
from app.main import app
from app.config import settings
from app.services.cache_service import CacheService


# ============================================================================
# ASYNC FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# APP FIXTURES
# ============================================================================

@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """FastAPI test client with DEBUG mode enabled for admin endpoints"""
    # Enable DEBUG mode to allow access to admin endpoints without API key
    original_debug = settings.DEBUG
    settings.DEBUG = True
    with TestClient(app) as client:
        yield client
    settings.DEBUG = original_debug


@pytest.fixture
def test_app():
    """FastAPI app instance for testing"""
    return app


# ============================================================================
# DIRECTORY FIXTURES
# ============================================================================

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test files"""
    temp_path = Path(tempfile.mkdtemp(prefix="fileconverter_test_"))
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_cache_dir() -> Generator[Path, None, None]:
    """Create temporary cache directory"""
    cache_path = Path(tempfile.mkdtemp(prefix="cache_test_"))
    yield cache_path
    shutil.rmtree(cache_path, ignore_errors=True)


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory"""
    return Path(__file__).parent / "fixtures"


# ============================================================================
# FILE FIXTURES - SAMPLE FILES
# ============================================================================

@pytest.fixture
def sample_image_jpg(temp_dir: Path) -> Path:
    """Create a sample JPG image (800x600)"""
    img_path = temp_dir / "sample.jpg"
    img = Image.new('RGB', (800, 600), color='red')
    img.save(img_path, 'JPEG', quality=95)
    return img_path


@pytest.fixture
def sample_image_png(temp_dir: Path) -> Path:
    """Create a sample PNG image (1024x768)"""
    img_path = temp_dir / "sample.png"
    img = Image.new('RGB', (1024, 768), color='blue')
    img.save(img_path, 'PNG')
    return img_path


@pytest.fixture
def sample_image_svg(temp_dir: Path) -> Path:
    """Create a sample SVG image"""
    svg_path = temp_dir / "sample.svg"
    svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
        <circle cx="50" cy="50" r="40" fill="green" />
    </svg>'''
    svg_path.write_text(svg_content)
    return svg_path


@pytest.fixture
def sample_audio_mp3(temp_dir: Path) -> Path:
    """Create a sample MP3 audio file using FFmpeg"""
    import subprocess
    audio_path = temp_dir / "sample.mp3"

    try:
        # Use FFmpeg to generate a valid MP3 file (1 second of silence)
        subprocess.run([
            'ffmpeg', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
            '-t', '1', '-q:a', '9', '-acodec', 'libmp3lame',
            str(audio_path)
        ], check=True, capture_output=True, timeout=5)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        # Fallback: create a minimal but valid MP3 structure
        # This is a 1-frame MP3 file that FFmpeg can recognize
        mp3_header = b'\xff\xfb\x90\x00'  # Valid MPEG1 Layer3 header
        audio_path.write_bytes(mp3_header + (b'\x00' * 417))

    return audio_path


@pytest.fixture
def sample_audio_wav(temp_dir: Path) -> Path:
    """Create a sample WAV audio file using FFmpeg"""
    import subprocess
    audio_path = temp_dir / "sample.wav"

    try:
        # Use FFmpeg to generate a valid WAV file (1 second of silence)
        subprocess.run([
            'ffmpeg', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
            '-t', '1', '-acodec', 'pcm_s16le',
            str(audio_path)
        ], check=True, capture_output=True, timeout=5)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        # Fallback: create a minimal valid WAV file
        import struct
        with audio_path.open('wb') as f:
            # RIFF header
            f.write(b'RIFF')
            f.write(struct.pack('<I', 36 + 8820))  # File size - 8
            f.write(b'WAVE')

            # fmt chunk
            f.write(b'fmt ')
            f.write(struct.pack('<I', 16))  # fmt chunk size
            f.write(struct.pack('<H', 1))   # PCM
            f.write(struct.pack('<H', 2))   # Stereo
            f.write(struct.pack('<I', 44100))  # Sample rate
            f.write(struct.pack('<I', 44100 * 2 * 2))  # Byte rate
            f.write(struct.pack('<H', 4))   # Block align
            f.write(struct.pack('<H', 16))  # Bits per sample

            # data chunk
            f.write(b'data')
            f.write(struct.pack('<I', 8820))  # data size (0.05 seconds)
            f.write(b'\x00' * 8820)

    return audio_path


@pytest.fixture
def sample_video(temp_dir: Path) -> Path:
    """Create a sample MP4 video for testing using FFmpeg"""
    import subprocess
    video_path = temp_dir / "test_video.mp4"

    # Try to create a real video using FFmpeg
    try:
        subprocess.run([
            'ffmpeg', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=320x240:rate=1',
            '-f', 'lavfi', '-i', 'sine=frequency=440:duration=1',
            '-pix_fmt', 'yuv420p', '-c:v', 'libx264', '-preset', 'ultrafast',
            '-c:a', 'aac', '-t', '1',
            str(video_path)
        ], check=True, capture_output=True, timeout=10)
        return video_path
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        # Fallback: create minimal valid MP4 with moov atom
        # This is a very minimal but valid MP4 structure
        mp4_data = bytes.fromhex(
            # ftyp box
            "0000001c6674797069736f6d00000200" +
            "69736f6d69736f3269736f33" +
            # moov box (required for FFmpeg)
            "000000086d6f6f76"
        )
        video_path.write_bytes(mp4_data + (b"\x00" * 1000))
        return video_path


@pytest.fixture
def sample_text_file(temp_dir: Path) -> Path:
    """Create a sample text file"""
    txt_path = temp_dir / "sample.txt"
    txt_path.write_text("This is a test document for FileConverter.\n" * 100)
    return txt_path


@pytest.fixture
def sample_markdown_file(temp_dir: Path) -> Path:
    """Create a sample markdown file"""
    md_path = temp_dir / "sample.md"
    md_content = "# Test Document\n\nThis is a **test** markdown file.\n\n## Section 1\n\nSome content here."
    md_path.write_text(md_content)
    return md_path


@pytest.fixture
def corrupted_file(temp_dir: Path) -> Path:
    """Create a corrupted file (invalid data)"""
    corrupt_path = temp_dir / "corrupted.jpg"
    corrupt_path.write_bytes(b'\x00\x01\x02\x03INVALID_DATA_NOT_A_REAL_IMAGE')
    return corrupt_path


@pytest.fixture
def oversized_file_marker() -> dict:
    """
    Marker for oversized file testing (doesn't create actual file)
    Returns metadata for mocking file size checks
    """
    return {
        "filename": "oversized.mp4",
        "size": 600 * 1024 * 1024,  # 600 MB
        "exceeds_limit": True,
        "max_size": 500 * 1024 * 1024  # 500 MB
    }


# ============================================================================
# UPLOAD FILE FIXTURES
# ============================================================================

@pytest.fixture
def upload_file_image_png():
    """Mock UploadFile for PNG image"""
    img = Image.new('RGB', (100, 100), color='green')
    img_bytes = io.BytesIO()
    img.save(img_bytes, 'PNG')
    img_bytes.seek(0)

    mock_file = Mock()
    mock_file.filename = "test_image.png"
    mock_file.file = img_bytes
    mock_file.content_type = "image/png"

    async def async_read():
        return img_bytes.getvalue()

    mock_file.read = async_read
    return mock_file


@pytest.fixture
def upload_file_image_jpg():
    """Mock UploadFile for JPG image"""
    img = Image.new('RGB', (200, 200), color='blue')
    img_bytes = io.BytesIO()
    img.save(img_bytes, 'JPEG', quality=95)
    img_bytes.seek(0)

    mock_file = Mock()
    mock_file.filename = "test_image.jpg"
    mock_file.file = img_bytes
    mock_file.content_type = "image/jpeg"

    async def async_read():
        return img_bytes.getvalue()

    mock_file.read = async_read
    return mock_file


@pytest.fixture
def upload_file_video():
    """Mock UploadFile for video"""
    video_data = b"MOCK_VIDEO_DATA_HEADER" + (b"\x00" * 10000)  # 10KB mock video

    mock_file = Mock()
    mock_file.filename = "test_video.mp4"
    mock_file.file = io.BytesIO(video_data)
    mock_file.file.seek(0)
    mock_file.content_type = "video/mp4"

    async def async_read():
        return video_data

    mock_file.read = async_read
    return mock_file


@pytest.fixture
def upload_file_document():
    """Mock UploadFile for document"""
    doc_data = b"Mock document content for testing"

    mock_file = Mock()
    mock_file.filename = "test_document.txt"
    mock_file.file = io.BytesIO(doc_data)
    mock_file.file.seek(0)
    mock_file.content_type = "text/plain"

    async def async_read():
        return doc_data

    mock_file.read = async_read
    return mock_file


# ============================================================================
# CACHE FIXTURES
# ============================================================================

@pytest.fixture
def cache_service(temp_cache_dir: Path) -> CacheService:
    """Create cache service for testing"""
    return CacheService(
        cache_dir=temp_cache_dir,
        expiration_hours=1,
        max_size_mb=100
    )


@pytest.fixture
def mock_cache_service():
    """Mock cache service"""
    mock_service = Mock(spec=CacheService)
    mock_service.generate_cache_key.return_value = "test_cache_key_12345"
    mock_service.get_cached_result.return_value = None  # Default: cache miss
    mock_service.store_result.return_value = None
    mock_service.get_cache_info.return_value = {
        "total_size_mb": 0.0,
        "entry_count": 0,
        "stats": {"hits": 0, "misses": 0, "total_requests": 0},
        "hit_rate": 0.0
    }
    return mock_service


# ============================================================================
# FFMPEG/FFPROBE MOCKS
# ============================================================================

@pytest.fixture
def mock_ffmpeg_success():
    """Mock successful FFmpeg conversion"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            returncode=0,
            stdout=b'',
            stderr=b''
        )
        yield mock_run


@pytest.fixture
def mock_ffmpeg_failure():
    """Mock failed FFmpeg conversion"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            returncode=1,
            stdout=b'',
            stderr=b'FFmpeg error: Invalid codec'
        )
        yield mock_run


@pytest.fixture
def mock_ffprobe_metadata():
    """Mock FFprobe metadata extraction for video"""
    metadata = {
        "format": {
            "duration": "120.5",
            "size": "10485760",
            "format_name": "mp4",
            "bit_rate": "2000000"
        },
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
                "r_frame_rate": "30/1",
                "avg_frame_rate": "30/1"
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
                "sample_rate": "48000",
                "channels": 2,
                "channel_layout": "stereo"
            }
        ]
    }

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(metadata),
            stderr=''
        )
        yield mock_run


@pytest.fixture
def mock_ffprobe_audio_metadata():
    """Mock FFprobe metadata extraction for audio"""
    metadata = {
        "format": {
            "duration": "180.25",
            "size": "5242880",
            "format_name": "mp3",
            "bit_rate": "192000"
        },
        "streams": [
            {
                "codec_type": "audio",
                "codec_name": "mp3",
                "sample_rate": "44100",
                "channels": 2,
                "channel_layout": "stereo",
                "bit_rate": "192000"
            }
        ]
    }

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(metadata),
            stderr=''
        )
        yield mock_run


# ============================================================================
# PANDOC MOCKS
# ============================================================================

@pytest.fixture
def mock_pandoc_success():
    """Mock successful Pandoc conversion"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            returncode=0,
            stdout='Converted content',
            stderr=''
        )
        yield mock_run


@pytest.fixture
def mock_pandoc_failure():
    """Mock failed Pandoc conversion"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            returncode=1,
            stdout='',
            stderr='Pandoc error: Unknown format'
        )
        yield mock_run


# ============================================================================
# WEBSOCKET FIXTURES
# ============================================================================

@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection"""
    ws = AsyncMock()
    ws.send_json = AsyncMock()
    ws.send_text = AsyncMock()
    ws.receive_json = AsyncMock(return_value={"session_id": "test_session"})
    ws.receive_text = AsyncMock(return_value='{"action": "ping"}')
    ws.close = AsyncMock()
    ws.accept = AsyncMock()
    return ws


@pytest.fixture
def mock_websocket_manager():
    """Mock WebSocket manager"""
    from app.services.base_converter import WebSocketManager

    manager = Mock(spec=WebSocketManager)
    manager.active_connections = {}
    manager.connect = AsyncMock()
    manager.disconnect = Mock()
    manager.send_progress = AsyncMock()
    return manager


# ============================================================================
# SECURITY TEST FIXTURES
# ============================================================================

@pytest.fixture
def malicious_filenames():
    """Collection of malicious filenames for path traversal testing"""
    return [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "file\x00.txt",  # Null byte injection
        "file/../../etc/passwd",
        "./../../secret.key",
        "file\\..\\.\\..\\secret",
        "../../../../root/.ssh/id_rsa",
        "/etc/passwd",  # Absolute path
        "C:\\Windows\\System32\\config\\SAM",  # Windows absolute path
    ]


@pytest.fixture
def command_injection_payloads():
    """Command injection test payloads"""
    return [
        "; rm -rf /",
        "| cat /etc/passwd",
        "& del /F /S /Q C:\\*",
        "`whoami`",
        "$(cat /etc/passwd)",
        "&& echo pwned",
        "|| echo hacked",
    ]


# ============================================================================
# VALIDATION FIXTURES
# ============================================================================

@pytest.fixture
def valid_conversion_options():
    """Valid conversion options for different file types"""
    return {
        "image": {
            "quality": 95,
            "width": 800,
            "height": 600
        },
        "video": {
            "codec": "libx264",
            "resolution": "720p",
            "bitrate": "2M"
        },
        "audio": {
            "bitrate": "192k",
            "sample_rate": "44100",
            "channels": "2"
        },
        "document": {
            "preserve_formatting": True,
            "toc": False
        }
    }


@pytest.fixture
def invalid_conversion_options():
    """Invalid conversion options (should fail validation)"""
    return {
        "video_bad_codec": {
            "codec": "malicious_codec",
            "resolution": "720p"
        },
        "video_bad_resolution": {
            "codec": "libx264",
            "resolution": "9999p"
        },
        "video_bad_bitrate": {
            "codec": "libx264",
            "bitrate": "999999M"
        },
        "audio_bad_sample_rate": {
            "sample_rate": "999999"
        },
        "audio_bad_channels": {
            "channels": "99"
        },
        "image_bad_quality": {
            "quality": 9999
        },
        "image_negative_dimensions": {
            "width": -100,
            "height": -200
        }
    }


# ============================================================================
# SESSION FIXTURES
# ============================================================================

@pytest.fixture
def test_session_id():
    """Generate test session ID"""
    import uuid
    return str(uuid.uuid4())


@pytest.fixture
def test_session_ids():
    """Generate multiple test session IDs"""
    import uuid
    return [str(uuid.uuid4()) for _ in range(5)]


# ============================================================================
# PIL/IMAGE MOCKS
# ============================================================================

@pytest.fixture
def mock_pil_image():
    """Mock PIL Image for image operations"""
    mock_img = MagicMock(spec=Image.Image)
    mock_img.width = 800
    mock_img.height = 600
    mock_img.format = 'JPEG'
    mock_img.mode = 'RGB'
    mock_img.size = (800, 600)
    mock_img.save = Mock()
    mock_img.resize = Mock(return_value=mock_img)
    mock_img.convert = Mock(return_value=mock_img)
    return mock_img


# ============================================================================
# FILE SIZE FIXTURES
# ============================================================================

@pytest.fixture
def file_size_limits():
    """File size limits for different file types"""
    return {
        "image": 104857600,  # 100MB
        "video": 524288000,  # 500MB
        "audio": 104857600,  # 100MB
        "document": 52428800,  # 50MB
        "archive": 524288000,  # 500MB
        "spreadsheet": 104857600,  # 100MB
        "subtitle": 10485760,  # 10MB
        "ebook": 52428800,  # 50MB
        "font": 20971520,  # 20MB
    }


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Automatically cleanup test files after each test"""
    yield
    # Cleanup runs after test
    test_dirs = [
        settings.TEMP_DIR,
        settings.UPLOAD_DIR,
    ]
    for test_dir in test_dirs:
        if test_dir.exists():
            for item in test_dir.glob("test_*"):
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                except Exception:
                    pass  # Ignore cleanup errors


# ============================================================================
# RATE LIMITER FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter state before each test to prevent 429 errors"""
    from app.utils.websocket_security import conversion_rate_limiter
    conversion_rate_limiter.reset()
    yield
    # Reset again after test for clean state
    conversion_rate_limiter.reset()


# ============================================================================
# BINARY PATH MOCKS
# ============================================================================

@pytest.fixture
def mock_ffmpeg_binary_paths():
    """Mock FFmpeg binary paths"""
    with patch('app.utils.binary_paths.get_ffmpeg_path') as mock_ffmpeg, \
         patch('app.utils.binary_paths.get_ffprobe_path') as mock_ffprobe:
        mock_ffmpeg.return_value = '/usr/bin/ffmpeg'
        mock_ffprobe.return_value = '/usr/bin/ffprobe'
        yield mock_ffmpeg, mock_ffprobe


@pytest.fixture
def mock_pandoc_binary_path():
    """Mock Pandoc binary path"""
    with patch('app.utils.binary_paths.get_pandoc_path') as mock_pandoc:
        mock_pandoc.return_value = '/usr/bin/pandoc'
        yield mock_pandoc
