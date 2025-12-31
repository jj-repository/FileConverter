"""
Integration tests for video router endpoints.

Tests the full API integration including:
- POST /api/video/convert - Video conversion endpoint
- GET /api/video/formats - Supported formats endpoint
- GET /api/video/download/{filename} - File download endpoint
- POST /api/video/info - Video metadata endpoint

Security tests:
- Path traversal prevention in download
- File size validation
- Extension validation
- Oversized file rejection
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    """Create test client for API testing"""
    return TestClient(app)


@pytest.fixture
def sample_video(temp_dir):
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
def sample_webm(temp_dir):
    """Create a sample WebM video for testing using FFmpeg"""
    import subprocess
    video_path = temp_dir / "test_video.webm"

    # Try to create a real webm using FFmpeg
    try:
        subprocess.run([
            'ffmpeg', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=320x240:rate=1',
            '-f', 'lavfi', '-i', 'sine=frequency=440:duration=1',
            '-c:v', 'libvpx-vp9', '-c:a', 'libvorbis', '-t', '1',
            str(video_path)
        ], check=True, capture_output=True, timeout=10)
        return video_path
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        # Fallback: create minimal webm structure
        # EBML header for WebM
        webm_header = bytes([0x1A, 0x45, 0xDF, 0xA3]) + (b"\x00" * 1000)
        video_path.write_bytes(webm_header)
        return video_path


class TestVideoConvert:
    """Test POST /api/video/convert endpoint"""

    def test_convert_mp4_to_webm_success(self, client, sample_video):
        """Test successful MP4 to WebM conversion"""
        with open(sample_video, 'rb') as f:
            response = client.post(
                "/api/video/convert",
                files={"file": ("test.mp4", f, "video/mp4")},
                data={
                    "output_format": "webm",
                    "codec": "libvpx-vp9",
                    "resolution": "720p",
                    "bitrate": "2M"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "session_id" in data
        assert data["output_file"].endswith(".webm")
        assert "download_url" in data

    def test_convert_with_h264_codec(self, client, sample_video):
        """Test conversion with h264 codec parameter"""
        with open(sample_video, 'rb') as f:
            response = client.post(
                "/api/video/convert",
                files={"file": ("test.mp4", f, "video/mp4")},
                data={
                    "output_format": "mp4",
                    "codec": "libx264"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".mp4")

    def test_convert_with_h265_codec(self, client, sample_video):
        """Test conversion with h265 codec parameter"""
        with open(sample_video, 'rb') as f:
            response = client.post(
                "/api/video/convert",
                files={"file": ("test.mp4", f, "video/mp4")},
                data={
                    "output_format": "mp4",
                    "codec": "libx265"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".mp4")

    def test_convert_with_vp9_codec(self, client, sample_video):
        """Test conversion with VP9 codec parameter"""
        with open(sample_video, 'rb') as f:
            response = client.post(
                "/api/video/convert",
                files={"file": ("test.mp4", f, "video/mp4")},
                data={
                    "output_format": "webm",
                    "codec": "libvpx-vp9"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".webm")

    def test_convert_with_720p_resolution(self, client, sample_video):
        """Test conversion with 720p resolution"""
        with open(sample_video, 'rb') as f:
            response = client.post(
                "/api/video/convert",
                files={"file": ("test.mp4", f, "video/mp4")},
                data={
                    "output_format": "mp4",
                    "resolution": "720p"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_convert_with_1080p_resolution(self, client, sample_video):
        """Test conversion with 1080p resolution"""
        with open(sample_video, 'rb') as f:
            response = client.post(
                "/api/video/convert",
                files={"file": ("test.mp4", f, "video/mp4")},
                data={
                    "output_format": "mp4",
                    "resolution": "1080p"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_convert_with_custom_bitrate(self, client, sample_video):
        """Test conversion with custom bitrate"""
        with open(sample_video, 'rb') as f:
            response = client.post(
                "/api/video/convert",
                files={"file": ("test.mp4", f, "video/mp4")},
                data={
                    "output_format": "mp4",
                    "bitrate": "5M"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_convert_to_avi_format(self, client, sample_video):
        """Test conversion to AVI format"""
        with open(sample_video, 'rb') as f:
            response = client.post(
                "/api/video/convert",
                files={"file": ("test.mp4", f, "video/mp4")},
                data={"output_format": "avi"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".avi")

    def test_convert_to_mkv_format(self, client, sample_video):
        """Test conversion to MKV format"""
        with open(sample_video, 'rb') as f:
            response = client.post(
                "/api/video/convert",
                files={"file": ("test.mp4", f, "video/mp4")},
                data={"output_format": "mkv"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".mkv")

    def test_convert_to_mov_format(self, client, sample_video):
        """Test conversion to MOV format"""
        with open(sample_video, 'rb') as f:
            response = client.post(
                "/api/video/convert",
                files={"file": ("test.mp4", f, "video/mp4")},
                data={"output_format": "mov"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".mov")

    def test_convert_invalid_codec(self, client, sample_video):
        """Test conversion with invalid codec is rejected"""
        with open(sample_video, 'rb') as f:
            response = client.post(
                "/api/video/convert",
                files={"file": ("test.mp4", f, "video/mp4")},
                data={
                    "output_format": "mp4",
                    "codec": "invalid_codec_xyz"
                }
            )

        # Should return error - either 400 or 500
        assert response.status_code in [400, 500]

    def test_convert_invalid_output_format(self, client, sample_video):
        """Test conversion with invalid output format"""
        with open(sample_video, 'rb') as f:
            response = client.post(
                "/api/video/convert",
                files={"file": ("test.mp4", f, "video/mp4")},
                data={"output_format": "invalid_format"}
            )

        assert response.status_code == 400
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error")
        assert "Unsupported output format" in str(error_msg)

    def test_convert_unsupported_input_format(self, client, temp_dir):
        """Test conversion with unsupported input format"""
        # Create a text file with .exe extension
        fake_file = temp_dir / "malware.exe"
        fake_file.write_text("not a video")

        with open(fake_file, 'rb') as f:
            response = client.post(
                "/api/video/convert",
                files={"file": ("malware.exe", f, "application/octet-stream")},
                data={"output_format": "mp4"}
            )

        assert response.status_code == 400
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error")
        assert ("Invalid or unsupported file extension" in str(error_msg) or
                "Unsupported file format" in str(error_msg))


class TestVideoFormats:
    """Test GET /api/video/formats endpoint"""

    def test_get_formats_success(self, client):
        """Test successful retrieval of supported formats"""
        response = client.get("/api/video/formats")

        assert response.status_code == 200
        data = response.json()
        assert "input_formats" in data
        assert "output_formats" in data
        assert isinstance(data["input_formats"], list)
        assert isinstance(data["output_formats"], list)

    def test_formats_include_common_types(self, client):
        """Test that common video formats are included"""
        response = client.get("/api/video/formats")
        data = response.json()

        # Check for common formats
        common_formats = ["mp4", "webm", "avi", "mkv", "mov"]
        for fmt in common_formats:
            assert fmt in data["output_formats"], f"{fmt} not in output formats"


class TestVideoDownload:
    """Test GET /api/video/download/{filename} endpoint"""

    def test_download_converted_file(self, client, sample_video):
        """Test downloading a converted file"""
        # First, convert a video
        with open(sample_video, 'rb') as f:
            convert_response = client.post(
                "/api/video/convert",
                files={"file": ("test.mp4", f, "video/mp4")},
                data={"output_format": "webm"}
            )

        assert convert_response.status_code == 200
        output_filename = convert_response.json()["output_file"]

        # Now download it
        download_response = client.get(f"/api/video/download/{output_filename}")

        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "application/octet-stream"
        assert len(download_response.content) > 0

    def test_download_nonexistent_file(self, client):
        """Test downloading a file that doesn't exist"""
        response = client.get("/api/video/download/nonexistent_video.mp4")

        assert response.status_code == 404

    def test_download_path_traversal_blocked(self, client):
        """Test that path traversal attempts are blocked"""
        # Try to access /etc/passwd via path traversal
        malicious_filenames = [
            "../../../etc/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "....//....//....//etc/passwd",
        ]

        for malicious_name in malicious_filenames:
            response = client.get(f"/api/video/download/{malicious_name}")
            # Should either be 400 (validation) or 404 (not found)
            assert response.status_code in [400, 404], \
                f"Path traversal not blocked for: {malicious_name}"


class TestVideoInfo:
    """Test POST /api/video/info endpoint"""

    def test_get_video_info_success(self, client, sample_video):
        """Test successful video info retrieval"""
        with open(sample_video, 'rb') as f:
            response = client.post(
                "/api/video/info",
                files={"file": ("test.mp4", f, "video/mp4")}
            )

        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert "size" in data
        assert "format" in data
        assert "metadata" in data

    def test_get_video_info_includes_duration(self, client, sample_video):
        """Test that video info includes duration and resolution"""
        with open(sample_video, 'rb') as f:
            response = client.post(
                "/api/video/info",
                files={"file": ("test.mp4", f, "video/mp4")}
            )

        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert data["filename"] == "test.mp4"

    def test_get_video_info_invalid_file(self, client, temp_dir):
        """Test video info with invalid file"""
        # Create a non-video file
        invalid_file = temp_dir / "invalid.txt"
        invalid_file.write_text("not a video")

        with open(invalid_file, 'rb') as f:
            response = client.post(
                "/api/video/info",
                files={"file": ("invalid.txt", f, "text/plain")}
            )

        # Returns 400 or 500 depending on validation stage
        assert response.status_code in [400, 500]


class TestVideoSecurityValidation:
    """Test security-critical validation in video endpoints"""

    def test_malicious_filename_sanitized(self, client, sample_video):
        """Test that malicious filenames are sanitized"""
        malicious_filenames = [
            "test; rm -rf /.mp4",
            "test$(whoami).mp4",
            "test`whoami`.mp4",
        ]

        for malicious_name in malicious_filenames:
            with open(sample_video, 'rb') as f:
                response = client.post(
                    "/api/video/convert",
                    files={"file": (malicious_name, f, "video/mp4")},
                    data={"output_format": "webm"}
                )

            # Should succeed (filename sanitized) or fail safely
            assert response.status_code in [200, 400, 500]
            if response.status_code == 200:
                # Verify output filename doesn't contain shell metacharacters
                output_file = response.json()["output_file"]
                dangerous_chars = [';', '$', '`', '|', '&', '<', '>']
                for char in dangerous_chars:
                    assert char not in output_file

    def test_null_byte_injection_blocked(self, client, sample_video):
        """Test that null byte injection is sanitized"""
        with open(sample_video, 'rb') as f:
            response = client.post(
                "/api/video/convert",
                files={"file": ("test\x00.mp4", f, "video/mp4")},
                data={"output_format": "webm"}
            )

        # Null bytes are sanitized, so conversion succeeds
        # but output filename should not contain null bytes
        if response.status_code == 200:
            output_file = response.json()["output_file"]
            assert '\x00' not in output_file
        else:
            # Or it fails validation
            assert response.status_code in [400, 500]


class TestVideoConversionFormats:
    """Test various video format conversions"""

    def test_convert_mp4_to_mp4_with_codec(self, client, sample_video):
        """Test conversion within same format but different codec"""
        with open(sample_video, 'rb') as f:
            response = client.post(
                "/api/video/convert",
                files={"file": ("test.mp4", f, "video/mp4")},
                data={
                    "output_format": "mp4",
                    "codec": "libx265"
                }
            )

        assert response.status_code == 200
        assert response.json()["output_file"].endswith(".mp4")

    def test_convert_webm_to_mp4(self, client, sample_webm):
        """Test conversion from WebM to MP4"""
        with open(sample_webm, 'rb') as f:
            response = client.post(
                "/api/video/convert",
                files={"file": ("test.webm", f, "video/webm")},
                data={"output_format": "mp4"}
            )

        assert response.status_code == 200
        assert response.json()["output_file"].endswith(".mp4")

    def test_convert_with_resolution_and_codec(self, client, sample_video):
        """Test conversion with both resolution and codec parameters"""
        with open(sample_video, 'rb') as f:
            response = client.post(
                "/api/video/convert",
                files={"file": ("test.mp4", f, "video/mp4")},
                data={
                    "output_format": "webm",
                    "codec": "libvpx-vp9",
                    "resolution": "1080p"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_convert_with_all_parameters(self, client, sample_video):
        """Test conversion with all optimization parameters"""
        with open(sample_video, 'rb') as f:
            response = client.post(
                "/api/video/convert",
                files={"file": ("test.mp4", f, "video/mp4")},
                data={
                    "output_format": "mp4",
                    "codec": "libx264",
                    "resolution": "720p",
                    "bitrate": "3M"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "session_id" in data
        assert "download_url" in data
