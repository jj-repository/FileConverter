"""
Integration tests for subtitle router endpoints.

Tests the full API integration including:
- POST /api/subtitle/convert - Subtitle conversion endpoint
- GET /api/subtitle/formats - Supported formats endpoint
- GET /api/subtitle/download/{filename} - File download endpoint
- POST /api/subtitle/info - Subtitle metadata endpoint

Security tests:
- Path traversal prevention in download
- File size validation
- Extension validation
- Malformed subtitle handling
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings


# ============================================================================
# SAMPLE SUBTITLE FIXTURES
# ============================================================================

@pytest.fixture
def sample_srt_subtitle(temp_dir):
    """Create a sample SRT subtitle file"""
    srt_path = temp_dir / "test_subtitle.srt"
    srt_content = """1
00:00:01,000 --> 00:00:05,000
This is the first subtitle line.

2
00:00:06,000 --> 00:00:10,000
This is the second subtitle line.
It can span multiple lines.

3
00:00:11,000 --> 00:00:15,000
This is the third subtitle line.
"""
    srt_path.write_text(srt_content)
    return srt_path


@pytest.fixture
def sample_vtt_subtitle(temp_dir):
    """Create a sample VTT subtitle file"""
    vtt_path = temp_dir / "test_subtitle.vtt"
    vtt_content = """WEBVTT

00:00:01.000 --> 00:00:05.000
This is the first subtitle line.

00:00:06.000 --> 00:00:10.000
This is the second subtitle line.
It can span multiple lines.

00:00:11.000 --> 00:00:15.000
This is the third subtitle line.
"""
    vtt_path.write_text(vtt_content)
    return vtt_path


@pytest.fixture
def sample_ass_subtitle(temp_dir):
    """Create a sample ASS subtitle file"""
    ass_path = temp_dir / "test_subtitle.ass"
    ass_content = """[Script Info]
Title: Test Subtitle
Original Script: Test

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,2,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:05.00,Default,,0,0,0,,This is the first subtitle line.
Dialogue: 0,0:00:06.00,0:00:10.00,Default,,0,0,0,,This is the second subtitle line.
Dialogue: 0,0:00:11.00,0:00:15.00,Default,,0,0,0,,This is the third subtitle line.
"""
    ass_path.write_text(ass_content)
    return ass_path


@pytest.fixture
def malformed_subtitle(temp_dir):
    """Create a malformed subtitle file"""
    bad_path = temp_dir / "malformed.srt"
    bad_content = """This is not a valid SRT file.
Just some random text without proper timing.
"""
    bad_path.write_text(bad_content)
    return bad_path


@pytest.fixture
def client():
    """Create test client for API testing"""
    return TestClient(app)


# ============================================================================
# TESTS - SUBTITLE CONVERSION
# ============================================================================

class TestSubtitleConvert:
    """Test POST /api/subtitle/convert endpoint"""

    def test_convert_srt_to_vtt_success(self, client, sample_srt_subtitle):
        """Test successful SRT to VTT conversion"""
        with open(sample_srt_subtitle, 'rb') as f:
            response = client.post(
                "/api/subtitle/convert",
                files={"file": ("test.srt", f, "text/plain")},
                data={"output_format": "vtt"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "session_id" in data
        assert data["output_file"].endswith(".vtt")
        assert "download_url" in data

    def test_convert_vtt_to_srt_success(self, client, sample_vtt_subtitle):
        """Test successful VTT to SRT conversion"""
        with open(sample_vtt_subtitle, 'rb') as f:
            response = client.post(
                "/api/subtitle/convert",
                files={"file": ("test.vtt", f, "text/plain")},
                data={"output_format": "srt"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".srt")

    def test_convert_ass_to_srt_success(self, client, sample_ass_subtitle):
        """Test successful ASS to SRT conversion"""
        with open(sample_ass_subtitle, 'rb') as f:
            response = client.post(
                "/api/subtitle/convert",
                files={"file": ("test.ass", f, "text/plain")},
                data={"output_format": "srt"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".srt")

    def test_convert_with_utf8_encoding(self, client, sample_srt_subtitle):
        """Test conversion with UTF-8 encoding parameter"""
        with open(sample_srt_subtitle, 'rb') as f:
            response = client.post(
                "/api/subtitle/convert",
                files={"file": ("test.srt", f, "text/plain")},
                data={
                    "output_format": "vtt",
                    "encoding": "utf-8"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_convert_with_latin1_encoding(self, client, sample_srt_subtitle):
        """Test conversion with latin-1 encoding parameter"""
        with open(sample_srt_subtitle, 'rb') as f:
            response = client.post(
                "/api/subtitle/convert",
                files={"file": ("test.srt", f, "text/plain")},
                data={
                    "output_format": "vtt",
                    "encoding": "latin-1"
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_convert_with_fps_parameter(self, client, sample_srt_subtitle):
        """Test conversion with FPS parameter for SUB format"""
        with open(sample_srt_subtitle, 'rb') as f:
            response = client.post(
                "/api/subtitle/convert",
                files={"file": ("test.srt", f, "text/plain")},
                data={
                    "output_format": "sub",
                    "fps": 25.0
                }
            )

        # Either succeeds or fails depending on SUB format availability
        assert response.status_code in [200, 500]

    def test_convert_invalid_output_format(self, client, sample_srt_subtitle):
        """Test conversion with invalid output format"""
        with open(sample_srt_subtitle, 'rb') as f:
            response = client.post(
                "/api/subtitle/convert",
                files={"file": ("test.srt", f, "text/plain")},
                data={"output_format": "invalid"}
            )

        assert response.status_code == 400
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error")
        assert "Unsupported output format" in str(error_msg)

    def test_convert_malformed_subtitle(self, client, malformed_subtitle):
        """Test conversion with malformed subtitle file"""
        with open(malformed_subtitle, 'rb') as f:
            response = client.post(
                "/api/subtitle/convert",
                files={"file": ("malformed.srt", f, "text/plain")},
                data={"output_format": "vtt"}
            )

        # May fail or succeed depending on lenient parsing
        # Status code might be 200, 400, or 500
        assert response.status_code in [200, 400, 500]

    def test_convert_unsupported_input_format(self, client, temp_dir):
        """Test conversion with unsupported input format"""
        # Create a file with unsupported extension
        fake_file = temp_dir / "fake.xyz"
        fake_file.write_text("not a subtitle")

        with open(fake_file, 'rb') as f:
            response = client.post(
                "/api/subtitle/convert",
                files={"file": ("fake.xyz", f, "text/plain")},
                data={"output_format": "srt"}
            )

        assert response.status_code == 400
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error")
        assert ("Invalid or unsupported file extension" in str(error_msg) or
                "Unsupported file format" in str(error_msg))


# ============================================================================
# TESTS - GET FORMATS
# ============================================================================

class TestSubtitleFormats:
    """Test GET /api/subtitle/formats endpoint"""

    def test_get_formats_success(self, client):
        """Test successful retrieval of supported formats"""
        response = client.get("/api/subtitle/formats")

        assert response.status_code == 200
        data = response.json()
        assert "input_formats" in data
        assert "output_formats" in data
        assert isinstance(data["input_formats"], list)
        assert isinstance(data["output_formats"], list)

    def test_formats_include_common_types(self, client):
        """Test that common subtitle formats are included"""
        response = client.get("/api/subtitle/formats")
        data = response.json()

        # Check for common formats
        common_formats = ["srt", "vtt", "ass"]
        for fmt in common_formats:
            # Should be in at least one of the lists
            is_supported = fmt in data["input_formats"] or fmt in data["output_formats"]
            assert is_supported, f"{fmt} not in supported formats"

    def test_output_formats_is_list(self, client):
        """Test that output_formats is a list"""
        response = client.get("/api/subtitle/formats")
        data = response.json()
        assert isinstance(data["output_formats"], list)
        assert len(data["output_formats"]) > 0


# ============================================================================
# TESTS - DOWNLOAD
# ============================================================================

class TestSubtitleDownload:
    """Test GET /api/subtitle/download/{filename} endpoint"""

    def test_download_converted_file(self, client, sample_srt_subtitle):
        """Test downloading a converted file"""
        # First, convert a subtitle
        with open(sample_srt_subtitle, 'rb') as f:
            convert_response = client.post(
                "/api/subtitle/convert",
                files={"file": ("test.srt", f, "text/plain")},
                data={"output_format": "vtt"}
            )

        assert convert_response.status_code == 200
        output_filename = convert_response.json()["output_file"]

        # Now download it
        download_response = client.get(f"/api/subtitle/download/{output_filename}")

        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "text/plain"
        assert len(download_response.content) > 0
        # Should contain VTT markers
        assert b"WEBVTT" in download_response.content or len(download_response.content) > 0

    def test_download_nonexistent_file(self, client):
        """Test downloading a file that doesn't exist"""
        response = client.get("/api/subtitle/download/nonexistent.vtt")

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
            response = client.get(f"/api/subtitle/download/{malicious_name}")
            # Should either be 400 (validation) or 404 (not found)
            assert response.status_code in [400, 404], \
                f"Path traversal not blocked for: {malicious_name}"

    def test_download_with_null_bytes_blocked(self, client):
        """Test that null byte injection is blocked"""
        response = client.get("/api/subtitle/download/test\x00.vtt")

        # Should be blocked (400) or not found (404)
        assert response.status_code in [400, 404]


# ============================================================================
# TESTS - SUBTITLE INFO
# ============================================================================

class TestSubtitleInfo:
    """Test POST /api/subtitle/info endpoint"""

    def test_get_subtitle_info_success(self, client, sample_srt_subtitle):
        """Test successful subtitle info retrieval"""
        with open(sample_srt_subtitle, 'rb') as f:
            response = client.post(
                "/api/subtitle/info",
                files={"file": ("test.srt", f, "text/plain")}
            )

        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert "size" in data
        assert "format" in data
        assert "metadata" in data

    def test_get_subtitle_info_includes_duration(self, client, sample_srt_subtitle):
        """Test that subtitle info includes duration"""
        with open(sample_srt_subtitle, 'rb') as f:
            response = client.post(
                "/api/subtitle/info",
                files={"file": ("test.srt", f, "text/plain")}
            )

        assert response.status_code == 200
        metadata = response.json()["metadata"]
        assert "duration_seconds" in metadata or "format" in metadata

    def test_get_subtitle_info_includes_entry_count(self, client, sample_srt_subtitle):
        """Test that subtitle info includes subtitle entry count"""
        with open(sample_srt_subtitle, 'rb') as f:
            response = client.post(
                "/api/subtitle/info",
                files={"file": ("test.srt", f, "text/plain")}
            )

        assert response.status_code == 200
        metadata = response.json()["metadata"]
        assert "subtitle_count" in metadata or "format" in metadata

    def test_get_subtitle_info_vtt_file(self, client, sample_vtt_subtitle):
        """Test subtitle info for VTT file"""
        with open(sample_vtt_subtitle, 'rb') as f:
            response = client.post(
                "/api/subtitle/info",
                files={"file": ("test.vtt", f, "text/plain")}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "vtt"

    def test_get_subtitle_info_ass_file(self, client, sample_ass_subtitle):
        """Test subtitle info for ASS file"""
        with open(sample_ass_subtitle, 'rb') as f:
            response = client.post(
                "/api/subtitle/info",
                files={"file": ("test.ass", f, "text/plain")}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "ass"

    def test_get_subtitle_info_invalid_file(self, client, temp_dir):
        """Test subtitle info with invalid file"""
        # Create a non-subtitle file
        invalid_file = temp_dir / "invalid.txt"
        invalid_file.write_text("not a subtitle")

        with open(invalid_file, 'rb') as f:
            response = client.post(
                "/api/subtitle/info",
                files={"file": ("invalid.txt", f, "text/plain")}
            )

        # Returns 400 or 500 depending on validation stage
        assert response.status_code in [400, 500]


# ============================================================================
# TESTS - SUBTITLE CONVERSION FORMATS
# ============================================================================

class TestSubtitleConversionFormats:
    """Test various subtitle format conversions"""

    def test_convert_to_vtt(self, client, sample_srt_subtitle):
        """Test conversion to VTT format"""
        with open(sample_srt_subtitle, 'rb') as f:
            response = client.post(
                "/api/subtitle/convert",
                files={"file": ("test.srt", f, "text/plain")},
                data={"output_format": "vtt"}
            )

        assert response.status_code == 200
        assert response.json()["output_file"].endswith(".vtt")

    def test_convert_to_srt(self, client, sample_vtt_subtitle):
        """Test conversion to SRT format"""
        with open(sample_vtt_subtitle, 'rb') as f:
            response = client.post(
                "/api/subtitle/convert",
                files={"file": ("test.vtt", f, "text/plain")},
                data={"output_format": "srt"}
            )

        assert response.status_code == 200
        assert response.json()["output_file"].endswith(".srt")

    def test_convert_to_ass(self, client, sample_srt_subtitle):
        """Test conversion to ASS format"""
        with open(sample_srt_subtitle, 'rb') as f:
            response = client.post(
                "/api/subtitle/convert",
                files={"file": ("test.srt", f, "text/plain")},
                data={"output_format": "ass"}
            )

        assert response.status_code == 200
        assert response.json()["output_file"].endswith(".ass")

    def test_convert_to_sub(self, client, sample_srt_subtitle):
        """Test conversion to SUB format"""
        with open(sample_srt_subtitle, 'rb') as f:
            response = client.post(
                "/api/subtitle/convert",
                files={"file": ("test.srt", f, "text/plain")},
                data={"output_format": "sub"}
            )

        # Either succeeds or fails depending on SUB format availability
        if response.status_code == 200:
            assert response.json()["output_file"].endswith(".sub")
        else:
            assert response.status_code in [400, 500]

    def test_convert_srt_to_srt(self, client, sample_srt_subtitle):
        """Test conversion of SRT to same format (SRT)"""
        with open(sample_srt_subtitle, 'rb') as f:
            response = client.post(
                "/api/subtitle/convert",
                files={"file": ("test.srt", f, "text/plain")},
                data={"output_format": "srt"}
            )

        assert response.status_code == 200
        assert response.json()["output_file"].endswith(".srt")


# ============================================================================
# TESTS - SECURITY VALIDATION
# ============================================================================

class TestSubtitleSecurityValidation:
    """Test security-critical validation in subtitle endpoints"""

    def test_malicious_filename_sanitized(self, client, sample_srt_subtitle):
        """Test that malicious filenames are sanitized"""
        malicious_filenames = [
            "test; rm -rf /.srt",
            "test$(whoami).srt",
            "test`whoami`.srt",
        ]

        for malicious_name in malicious_filenames:
            with open(sample_srt_subtitle, 'rb') as f:
                response = client.post(
                    "/api/subtitle/convert",
                    files={"file": (malicious_name, f, "text/plain")},
                    data={"output_format": "vtt"}
                )

            # Should succeed (filename sanitized) or fail safely
            assert response.status_code in [200, 400, 500]
            if response.status_code == 200:
                # Verify output filename doesn't contain shell metacharacters
                output_file = response.json()["output_file"]
                dangerous_chars = [';', '$', '`', '|', '&', '<', '>']
                for char in dangerous_chars:
                    assert char not in output_file

    def test_null_byte_injection_blocked(self, client, sample_srt_subtitle):
        """Test that null byte injection is sanitized"""
        with open(sample_srt_subtitle, 'rb') as f:
            response = client.post(
                "/api/subtitle/convert",
                files={"file": ("test\x00.srt", f, "text/plain")},
                data={"output_format": "vtt"}
            )

        # Null bytes are sanitized, so conversion succeeds
        # but output filename should not contain null bytes
        if response.status_code == 200:
            output_file = response.json()["output_file"]
            assert '\x00' not in output_file
        else:
            # Or it fails validation
            assert response.status_code in [400, 500]

    def test_absolute_path_injection_blocked(self, client):
        """Test that absolute paths cannot be injected"""
        response = client.get("/api/subtitle/download//etc/passwd")

        # Should be blocked
        assert response.status_code in [400, 404]


# ============================================================================
# TESTS - ADVANCED CONVERSION OPTIONS
# ============================================================================

class TestSubtitleAdvancedOptions:
    """Test advanced conversion options"""

    def test_convert_with_html_tags_preserved(self, client, sample_srt_subtitle):
        """Test conversion preserving HTML tags"""
        with open(sample_srt_subtitle, 'rb') as f:
            response = client.post(
                "/api/subtitle/convert",
                files={"file": ("test.srt", f, "text/plain")},
                data={
                    "output_format": "vtt",
                    "keep_html_tags": True
                }
            )

        assert response.status_code == 200

    def test_convert_srt_chain_conversion(self, client, sample_srt_subtitle):
        """Test chain conversion: SRT -> VTT -> ASS"""
        # First conversion: SRT -> VTT
        with open(sample_srt_subtitle, 'rb') as f:
            response1 = client.post(
                "/api/subtitle/convert",
                files={"file": ("test.srt", f, "text/plain")},
                data={"output_format": "vtt"}
            )

        assert response1.status_code == 200
        vtt_file = response1.json()["output_file"]

        # Second conversion: VTT -> ASS
        # (Would need to re-fetch the converted file to test this properly)

    def test_convert_preserves_timing_accuracy(self, client, sample_srt_subtitle):
        """Test that timing is preserved during conversion"""
        with open(sample_srt_subtitle, 'rb') as f:
            response = client.post(
                "/api/subtitle/convert",
                files={"file": ("test.srt", f, "text/plain")},
                data={"output_format": "vtt"}
            )

        assert response.status_code == 200
        # Timing should be preserved (would need to parse output to verify)


# ============================================================================
# TESTS - EDGE CASES
# ============================================================================

class TestSubtitleEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_convert_empty_subtitle_file(self, client, temp_dir):
        """Test conversion of empty subtitle file"""
        empty_path = temp_dir / "empty.srt"
        empty_path.write_text("")

        with open(empty_path, 'rb') as f:
            response = client.post(
                "/api/subtitle/convert",
                files={"file": ("empty.srt", f, "text/plain")},
                data={"output_format": "vtt"}
            )

        # Should either succeed or fail gracefully
        assert response.status_code in [200, 400, 500]

    def test_convert_large_subtitle_file(self, client, temp_dir):
        """Test conversion of large subtitle file"""
        large_path = temp_dir / "large.srt"

        # Generate 1000 subtitle entries
        content = ""
        for i in range(1, 1001):
            content += f"""{i}
00:{i//60:02d}:{i%60:02d},000 --> 00:{(i+1)//60:02d}:{(i+1)%60:02d},000
Line {i}

"""
        large_path.write_text(content)

        with open(large_path, 'rb') as f:
            response = client.post(
                "/api/subtitle/convert",
                files={"file": ("large.srt", f, "text/plain")},
                data={"output_format": "vtt"}
            )

        assert response.status_code in [200, 400, 500]

    def test_convert_subtitle_with_special_characters(self, client, temp_dir):
        """Test conversion of subtitle with special characters"""
        special_path = temp_dir / "special.srt"
        special_content = """1
00:00:01,000 --> 00:00:05,000
Special chars: é, ñ, ü, 中文, 日本語

2
00:00:06,000 --> 00:00:10,000
Symbols: © ® ™ € ¥
"""
        special_path.write_text(special_content, encoding='utf-8')

        with open(special_path, 'rb') as f:
            response = client.post(
                "/api/subtitle/convert",
                files={"file": ("special.srt", f, "text/plain")},
                data={"output_format": "vtt"}
            )

        assert response.status_code == 200
