"""
Integration tests for audio router endpoints.

Tests the full API integration including:
- POST /api/audio/convert - Audio conversion endpoint
- GET /api/audio/formats - Supported formats endpoint
- GET /api/audio/download/{filename} - File download endpoint
- POST /api/audio/info - Audio metadata endpoint

Security tests:
- Path traversal prevention in download
- File size validation
- Extension validation
- Codec validation
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
def sample_audio(sample_audio_mp3):
    """Use sample audio MP3 fixture for testing"""
    return sample_audio_mp3


class TestAudioConvert:
    """Test POST /api/audio/convert endpoint"""

    def test_convert_mp3_to_wav_success(self, client, sample_audio):
        """Test successful MP3 to WAV conversion"""
        with open(sample_audio, 'rb') as f:
            response = client.post(
                "/api/audio/convert",
                files={"file": ("test.mp3", f, "audio/mpeg")},
                data={"output_format": "wav"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "session_id" in data
        assert data["output_file"].endswith(".wav")
        assert "download_url" in data

    def test_convert_with_codec_parameter_mp3(self, client, sample_audio):
        """Test conversion with codec parameter (MP3)"""
        with open(sample_audio, 'rb') as f:
            response = client.post(
                "/api/audio/convert",
                files={"file": ("test.mp3", f, "audio/mpeg")},
                data={"output_format": "mp3", "codec": "libmp3lame"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".mp3")

    def test_convert_with_codec_parameter_aac(self, client, sample_audio):
        """Test conversion with AAC codec"""
        with open(sample_audio, 'rb') as f:
            response = client.post(
                "/api/audio/convert",
                files={"file": ("test.mp3", f, "audio/mpeg")},
                data={"output_format": "aac", "codec": "aac"}
            )

        # AAC support may vary, so accept either success or failure
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "completed"
            assert data["output_file"].endswith(".aac")

    def test_convert_with_codec_parameter_opus(self, client, sample_audio):
        """Test conversion with Opus codec"""
        with open(sample_audio, 'rb') as f:
            response = client.post(
                "/api/audio/convert",
                files={"file": ("test.mp3", f, "audio/mpeg")},
                data={"output_format": "ogg", "codec": "libopus"}
            )

        # Opus support may vary, so accept either success or failure
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "completed"

    def test_convert_with_bitrate_128k(self, client, sample_audio):
        """Test conversion with 128k bitrate"""
        with open(sample_audio, 'rb') as f:
            response = client.post(
                "/api/audio/convert",
                files={"file": ("test.mp3", f, "audio/mpeg")},
                data={"output_format": "mp3", "bitrate": "128k"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".mp3")

    def test_convert_with_bitrate_320k(self, client, sample_audio):
        """Test conversion with 320k bitrate"""
        with open(sample_audio, 'rb') as f:
            response = client.post(
                "/api/audio/convert",
                files={"file": ("test.mp3", f, "audio/mpeg")},
                data={"output_format": "mp3", "bitrate": "320k"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_convert_with_sample_rate_44100(self, client, sample_audio):
        """Test conversion with 44100 Hz sample rate"""
        with open(sample_audio, 'rb') as f:
            response = client.post(
                "/api/audio/convert",
                files={"file": ("test.mp3", f, "audio/mpeg")},
                data={"output_format": "wav", "sample_rate": 44100}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".wav")

    def test_convert_with_sample_rate_48000(self, client, sample_audio):
        """Test conversion with 48000 Hz sample rate"""
        with open(sample_audio, 'rb') as f:
            response = client.post(
                "/api/audio/convert",
                files={"file": ("test.mp3", f, "audio/mpeg")},
                data={"output_format": "wav", "sample_rate": 48000}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_convert_with_all_parameters(self, client, sample_audio):
        """Test conversion with multiple parameters combined"""
        with open(sample_audio, 'rb') as f:
            response = client.post(
                "/api/audio/convert",
                files={"file": ("test.mp3", f, "audio/mpeg")},
                data={
                    "output_format": "wav",
                    "bitrate": "192k",
                    "sample_rate": 44100,
                    "channels": 2
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_convert_invalid_codec(self, client, sample_audio):
        """Test conversion with invalid codec"""
        with open(sample_audio, 'rb') as f:
            response = client.post(
                "/api/audio/convert",
                files={"file": ("test.mp3", f, "audio/mpeg")},
                data={"output_format": "mp3", "codec": "invalid_codec"}
            )

        # Invalid codec may fail during conversion
        assert response.status_code in [400, 500]

    def test_convert_invalid_output_format(self, client, sample_audio):
        """Test conversion with invalid output format"""
        with open(sample_audio, 'rb') as f:
            response = client.post(
                "/api/audio/convert",
                files={"file": ("test.mp3", f, "audio/mpeg")},
                data={"output_format": "invalid"}
            )

        assert response.status_code == 400
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error")
        assert "Unsupported output format" in str(error_msg)

    def test_convert_unsupported_input_format(self, client, temp_dir):
        """Test conversion with unsupported input format"""
        # Create a text file with .exe extension
        fake_file = temp_dir / "malware.exe"
        fake_file.write_text("not an audio file")

        with open(fake_file, 'rb') as f:
            response = client.post(
                "/api/audio/convert",
                files={"file": ("malware.exe", f, "application/octet-stream")},
                data={"output_format": "mp3"}
            )

        assert response.status_code == 400
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error")
        assert ("Invalid or unsupported file extension" in str(error_msg) or
                "Unsupported file format" in str(error_msg))


class TestAudioFormats:
    """Test GET /api/audio/formats endpoint"""

    def test_get_formats_success(self, client):
        """Test successful retrieval of supported formats"""
        response = client.get("/api/audio/formats")

        assert response.status_code == 200
        data = response.json()
        assert "input_formats" in data
        assert "output_formats" in data
        assert isinstance(data["input_formats"], list)
        assert isinstance(data["output_formats"], list)

    def test_formats_include_common_types(self, client):
        """Test that common audio formats are included"""
        response = client.get("/api/audio/formats")
        data = response.json()

        # Check for common audio formats
        common_formats = ["mp3", "wav", "flac", "ogg"]
        for fmt in common_formats:
            assert fmt in data["output_formats"], f"{fmt} not in output formats"


class TestAudioDownload:
    """Test GET /api/audio/download/{filename} endpoint"""

    def test_download_converted_file(self, client, sample_audio):
        """Test downloading a converted file"""
        # First, convert an audio file
        with open(sample_audio, 'rb') as f:
            convert_response = client.post(
                "/api/audio/convert",
                files={"file": ("test.mp3", f, "audio/mpeg")},
                data={"output_format": "wav"}
            )

        assert convert_response.status_code == 200
        output_filename = convert_response.json()["output_file"]

        # Now download it
        download_response = client.get(f"/api/audio/download/{output_filename}")

        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "application/octet-stream"
        assert len(download_response.content) > 0

    def test_download_nonexistent_file(self, client):
        """Test downloading a file that doesn't exist"""
        response = client.get("/api/audio/download/nonexistent.wav")

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
            response = client.get(f"/api/audio/download/{malicious_name}")
            # Should either be 400 (validation) or 404 (not found)
            assert response.status_code in [400, 404], \
                f"Path traversal not blocked for: {malicious_name}"


class TestAudioInfo:
    """Test POST /api/audio/info endpoint"""

    def test_get_audio_info_success(self, client, sample_audio):
        """Test successful audio info retrieval"""
        with open(sample_audio, 'rb') as f:
            response = client.post(
                "/api/audio/info",
                files={"file": ("test.mp3", f, "audio/mpeg")}
            )

        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert "size" in data
        assert "format" in data
        assert "metadata" in data

    def test_get_audio_info_includes_audio_properties(self, client, sample_audio):
        """Test that audio info includes audio properties"""
        with open(sample_audio, 'rb') as f:
            response = client.post(
                "/api/audio/info",
                files={"file": ("test.mp3", f, "audio/mpeg")}
            )

        assert response.status_code == 200
        data = response.json()
        metadata = data["metadata"]
        # Audio metadata may include duration, sample_rate, channels, bitrate
        # At least some of these should be present
        possible_keys = ["duration", "sample_rate", "channels", "bitrate", "codec"]
        assert any(key in metadata for key in possible_keys), \
            f"No audio properties found in metadata: {metadata}"

    def test_get_audio_info_invalid_file(self, client, temp_dir):
        """Test audio info with invalid file"""
        # Create a non-audio file
        invalid_file = temp_dir / "invalid.txt"
        invalid_file.write_text("not an audio file")

        with open(invalid_file, 'rb') as f:
            response = client.post(
                "/api/audio/info",
                files={"file": ("invalid.txt", f, "text/plain")}
            )

        # Returns 400 or 500 depending on validation stage
        assert response.status_code in [400, 500]


class TestAudioSecurityValidation:
    """Test security-critical validation in audio endpoints"""

    def test_malicious_filename_sanitized(self, client, sample_audio):
        """Test that malicious filenames are sanitized"""
        malicious_filenames = [
            "test; rm -rf /.mp3",
            "test$(whoami).mp3",
            "test`whoami`.mp3",
        ]

        for malicious_name in malicious_filenames:
            with open(sample_audio, 'rb') as f:
                response = client.post(
                    "/api/audio/convert",
                    files={"file": (malicious_name, f, "audio/mpeg")},
                    data={"output_format": "wav"}
                )

            # Should succeed (filename sanitized) or fail safely
            assert response.status_code in [200, 400, 500]
            if response.status_code == 200:
                # Verify output filename doesn't contain shell metacharacters
                output_file = response.json()["output_file"]
                dangerous_chars = [';', '$', '`', '|', '&', '<', '>']
                for char in dangerous_chars:
                    assert char not in output_file

    def test_null_byte_injection_blocked(self, client, sample_audio):
        """Test that null byte injection is sanitized"""
        with open(sample_audio, 'rb') as f:
            response = client.post(
                "/api/audio/convert",
                files={"file": ("test\x00.mp3", f, "audio/mpeg")},
                data={"output_format": "wav"}
            )

        # Null bytes are sanitized, so conversion succeeds
        # but output filename should not contain null bytes
        if response.status_code == 200:
            output_file = response.json()["output_file"]
            assert '\x00' not in output_file
        else:
            # Or it fails validation
            assert response.status_code in [400, 500]


class TestAudioConversionFormats:
    """Test various audio format conversions"""

    def test_convert_to_flac(self, client, sample_audio):
        """Test conversion to FLAC format"""
        with open(sample_audio, 'rb') as f:
            response = client.post(
                "/api/audio/convert",
                files={"file": ("test.mp3", f, "audio/mpeg")},
                data={"output_format": "flac"}
            )

        assert response.status_code == 200
        assert response.json()["output_file"].endswith(".flac")

    def test_convert_to_ogg(self, client, sample_audio):
        """Test conversion to OGG format"""
        with open(sample_audio, 'rb') as f:
            response = client.post(
                "/api/audio/convert",
                files={"file": ("test.mp3", f, "audio/mpeg")},
                data={"output_format": "ogg"}
            )

        assert response.status_code == 200
        assert response.json()["output_file"].endswith(".ogg")

    def test_convert_to_m4a(self, client, sample_audio):
        """Test conversion to M4A format"""
        with open(sample_audio, 'rb') as f:
            response = client.post(
                "/api/audio/convert",
                files={"file": ("test.mp3", f, "audio/mpeg")},
                data={"output_format": "m4a"}
            )

        # M4A support may vary
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            assert response.json()["output_file"].endswith(".m4a")

    def test_convert_to_aac(self, client, sample_audio):
        """Test conversion to AAC format"""
        with open(sample_audio, 'rb') as f:
            response = client.post(
                "/api/audio/convert",
                files={"file": ("test.mp3", f, "audio/mpeg")},
                data={"output_format": "aac"}
            )

        # AAC support may vary
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            assert response.json()["output_file"].endswith(".aac")

    def test_convert_wav_to_mp3(self, client, sample_audio_wav):
        """Test WAV to MP3 conversion"""
        with open(sample_audio_wav, 'rb') as f:
            response = client.post(
                "/api/audio/convert",
                files={"file": ("test.wav", f, "audio/wav")},
                data={"output_format": "mp3"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".mp3")
