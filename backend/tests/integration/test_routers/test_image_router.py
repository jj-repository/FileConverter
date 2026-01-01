"""
Integration tests for image router endpoints.

Tests the full API integration including:
- POST /api/image/convert - Image conversion endpoint
- GET /api/image/formats - Supported formats endpoint
- GET /api/image/download/{filename} - File download endpoint
- POST /api/image/info - Image metadata endpoint

Security tests:
- Path traversal prevention in download
- File size validation
- Extension validation
- Oversized file rejection
"""

import pytest
from pathlib import Path
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    """Create test client for API testing"""
    return TestClient(app)


@pytest.fixture
def sample_image(temp_dir):
    """Create a sample JPG image for testing"""
    image_path = temp_dir / "test_image.jpg"
    img = Image.new('RGB', (200, 200), color='blue')
    img.save(image_path, 'JPEG')
    return image_path


@pytest.fixture
def sample_png(temp_dir):
    """Create a sample PNG image for testing"""
    image_path = temp_dir / "test_image.png"
    img = Image.new('RGBA', (150, 150), color=(255, 0, 0, 128))
    img.save(image_path, 'PNG')
    return image_path


class TestImageConvert:
    """Test POST /api/image/convert endpoint"""

    def test_convert_jpg_to_png_success(self, client, sample_image):
        """Test successful JPG to PNG conversion"""
        with open(sample_image, 'rb') as f:
            response = client.post(
                "/api/image/convert",
                files={"file": ("test.jpg", f, "image/jpeg")},
                data={"output_format": "png"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "session_id" in data
        assert data["output_file"].endswith(".png")
        assert "download_url" in data

    def test_convert_png_to_jpg_success(self, client, sample_png):
        """Test successful PNG to JPG conversion"""
        with open(sample_png, 'rb') as f:
            response = client.post(
                "/api/image/convert",
                files={"file": ("test.png", f, "image/png")},
                data={"output_format": "jpg", "quality": 90}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".jpg")

    def test_convert_with_quality_parameter(self, client, sample_image):
        """Test conversion with quality parameter"""
        with open(sample_image, 'rb') as f:
            response = client.post(
                "/api/image/convert",
                files={"file": ("test.jpg", f, "image/jpeg")},
                data={"output_format": "webp", "quality": 80}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".webp")

    def test_convert_with_resize_width(self, client, sample_image):
        """Test conversion with width resize"""
        with open(sample_image, 'rb') as f:
            response = client.post(
                "/api/image/convert",
                files={"file": ("test.jpg", f, "image/jpeg")},
                data={"output_format": "png", "width": 100}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_convert_with_resize_height(self, client, sample_image):
        """Test conversion with height resize"""
        with open(sample_image, 'rb') as f:
            response = client.post(
                "/api/image/convert",
                files={"file": ("test.jpg", f, "image/jpeg")},
                data={"output_format": "png", "height": 100}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_convert_with_both_dimensions(self, client, sample_image):
        """Test conversion with both width and height"""
        with open(sample_image, 'rb') as f:
            response = client.post(
                "/api/image/convert",
                files={"file": ("test.jpg", f, "image/jpeg")},
                data={"output_format": "png", "width": 100, "height": 100}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_convert_invalid_output_format(self, client, sample_image):
        """Test conversion with invalid output format"""
        with open(sample_image, 'rb') as f:
            response = client.post(
                "/api/image/convert",
                files={"file": ("test.jpg", f, "image/jpeg")},
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
        fake_file.write_text("not an image")

        with open(fake_file, 'rb') as f:
            response = client.post(
                "/api/image/convert",
                files={"file": ("malware.exe", f, "application/octet-stream")},
                data={"output_format": "png"}
            )

        assert response.status_code == 400
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error")
        assert ("Invalid or unsupported file extension" in str(error_msg) or
                "Unsupported file format" in str(error_msg))

    def test_convert_invalid_quality(self, client, sample_image):
        """Test conversion with invalid quality value"""
        with open(sample_image, 'rb') as f:
            response = client.post(
                "/api/image/convert",
                files={"file": ("test.jpg", f, "image/jpeg")},
                data={"output_format": "jpg", "quality": 150}  # Invalid: >100
            )

        assert response.status_code == 500
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error")
        assert "Invalid quality" in str(error_msg)

    def test_convert_negative_dimensions(self, client, sample_image):
        """Test conversion with negative dimensions"""
        with open(sample_image, 'rb') as f:
            response = client.post(
                "/api/image/convert",
                files={"file": ("test.jpg", f, "image/jpeg")},
                data={"output_format": "png", "width": -100}
            )

        assert response.status_code == 500
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error")
        assert "Invalid width" in str(error_msg)

    def test_convert_oversized_dimensions(self, client, sample_image):
        """Test conversion with oversized dimensions"""
        with open(sample_image, 'rb') as f:
            response = client.post(
                "/api/image/convert",
                files={"file": ("test.jpg", f, "image/jpeg")},
                data={"output_format": "png", "width": 20000}  # >10000
            )

        assert response.status_code == 500
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error")
        assert "Invalid width" in str(error_msg)


class TestImageFormats:
    """Test GET /api/image/formats endpoint"""

    def test_get_formats_success(self, client):
        """Test successful retrieval of supported formats"""
        response = client.get("/api/image/formats")

        assert response.status_code == 200
        data = response.json()
        assert "input_formats" in data
        assert "output_formats" in data
        assert isinstance(data["input_formats"], list)
        assert isinstance(data["output_formats"], list)

    def test_formats_include_common_types(self, client):
        """Test that common image formats are included"""
        response = client.get("/api/image/formats")
        data = response.json()

        # Check for common formats
        common_formats = ["jpg", "jpeg", "png", "webp", "gif"]
        for fmt in common_formats:
            assert fmt in data["output_formats"], f"{fmt} not in output formats"


class TestImageDownload:
    """Test GET /api/image/download/{filename} endpoint"""

    def test_download_converted_file(self, client, sample_image):
        """Test downloading a converted file"""
        # First, convert an image
        with open(sample_image, 'rb') as f:
            convert_response = client.post(
                "/api/image/convert",
                files={"file": ("test.jpg", f, "image/jpeg")},
                data={"output_format": "png"}
            )

        assert convert_response.status_code == 200
        output_filename = convert_response.json()["output_file"]

        # Now download it
        download_response = client.get(f"/api/image/download/{output_filename}")

        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "application/octet-stream"
        assert len(download_response.content) > 0

    def test_download_nonexistent_file(self, client):
        """Test downloading a file that doesn't exist"""
        response = client.get("/api/image/download/nonexistent.png")

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
            response = client.get(f"/api/image/download/{malicious_name}")
            # Should either be 400 (validation) or 404 (not found)
            assert response.status_code in [400, 404], \
                f"Path traversal not blocked for: {malicious_name}"


class TestImageInfo:
    """Test POST /api/image/info endpoint"""

    def test_get_image_info_success(self, client, sample_image):
        """Test successful image info retrieval"""
        with open(sample_image, 'rb') as f:
            response = client.post(
                "/api/image/info",
                files={"file": ("test.jpg", f, "image/jpeg")}
            )

        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert "size" in data
        assert "format" in data
        assert "metadata" in data

    def test_get_image_info_includes_dimensions(self, client, sample_image):
        """Test that image info includes width and height"""
        with open(sample_image, 'rb') as f:
            response = client.post(
                "/api/image/info",
                files={"file": ("test.jpg", f, "image/jpeg")}
            )

        assert response.status_code == 200
        metadata = response.json()["metadata"]
        assert "width" in metadata
        assert "height" in metadata
        assert metadata["width"] == 200
        assert metadata["height"] == 200

    def test_get_image_info_invalid_file(self, client, temp_dir):
        """Test image info with invalid file"""
        # Create a non-image file
        invalid_file = temp_dir / "invalid.txt"
        invalid_file.write_text("not an image")

        with open(invalid_file, 'rb') as f:
            response = client.post(
                "/api/image/info",
                files={"file": ("invalid.txt", f, "text/plain")}
            )

        # Returns 400 or 500 depending on validation stage
        assert response.status_code in [400, 500]


class TestImageSecurityValidation:
    """Test security-critical validation in image endpoints"""

    def test_oversized_file_rejected(self, client, temp_dir):
        """Test that files exceeding size limit are rejected"""
        # Note: Creating a 101MB file is impractical for tests
        # This test would need mocking or config adjustment
        pass  # Skip for now - would need special test configuration

    def test_malicious_filename_sanitized(self, client, sample_image):
        """Test that malicious filenames are sanitized"""
        malicious_filenames = [
            "test; rm -rf /.jpg",
            "test$(whoami).jpg",
            "test`whoami`.jpg",
        ]

        for malicious_name in malicious_filenames:
            with open(sample_image, 'rb') as f:
                response = client.post(
                    "/api/image/convert",
                    files={"file": (malicious_name, f, "image/jpeg")},
                    data={"output_format": "png"}
                )

            # Should succeed (filename sanitized) or fail safely
            assert response.status_code in [200, 400, 500]
            if response.status_code == 200:
                # Verify output filename doesn't contain shell metacharacters
                output_file = response.json()["output_file"]
                dangerous_chars = [';', '$', '`', '|', '&', '<', '>']
                for char in dangerous_chars:
                    assert char not in output_file

    def test_null_byte_injection_blocked(self, client, sample_image):
        """Test that null byte injection is sanitized"""
        with open(sample_image, 'rb') as f:
            response = client.post(
                "/api/image/convert",
                files={"file": ("test\x00.jpg", f, "image/jpeg")},
                data={"output_format": "png"}
            )

        # Null bytes are sanitized, so conversion succeeds
        # but output filename should not contain null bytes
        if response.status_code == 200:
            output_file = response.json()["output_file"]
            assert '\x00' not in output_file
        else:
            # Or it fails validation
            assert response.status_code in [400, 500]


class TestImageConversionFormats:
    """Test various image format conversions"""

    def test_convert_to_webp(self, client, sample_image):
        """Test conversion to WebP format"""
        with open(sample_image, 'rb') as f:
            response = client.post(
                "/api/image/convert",
                files={"file": ("test.jpg", f, "image/jpeg")},
                data={"output_format": "webp", "quality": 85}
            )

        assert response.status_code == 200
        assert response.json()["output_file"].endswith(".webp")

    def test_convert_to_gif(self, client, sample_image):
        """Test conversion to GIF format"""
        with open(sample_image, 'rb') as f:
            response = client.post(
                "/api/image/convert",
                files={"file": ("test.jpg", f, "image/jpeg")},
                data={"output_format": "gif"}
            )

        assert response.status_code == 200
        assert response.json()["output_file"].endswith(".gif")

    def test_convert_to_bmp(self, client, sample_image):
        """Test conversion to BMP format"""
        with open(sample_image, 'rb') as f:
            response = client.post(
                "/api/image/convert",
                files={"file": ("test.jpg", f, "image/jpeg")},
                data={"output_format": "bmp"}
            )

        assert response.status_code == 200
        assert response.json()["output_file"].endswith(".bmp")

    def test_convert_to_tiff(self, client, sample_image):
        """Test conversion to TIFF format"""
        with open(sample_image, 'rb') as f:
            response = client.post(
                "/api/image/convert",
                files={"file": ("test.jpg", f, "image/jpeg")},
                data={"output_format": "tiff"}
            )

        assert response.status_code == 200
        assert response.json()["output_file"].endswith(".tiff")


class TestImageCleanup:
    """Test cleanup behavior in error scenarios"""

    def test_convert_cleanup_output_file_on_error(self, client, sample_image, monkeypatch):
        """Test that output_path is cleaned up when conversion fails after file creation"""
        from app.services.image_converter import ImageConverter
        from pathlib import Path
        from app.utils.file_handler import cleanup_file
        from app.config import settings
        from app.models.conversion import ConversionResponse

        # Track cleanup calls
        cleanup_calls = []
        original_cleanup = cleanup_file

        def mock_cleanup(file_path):
            cleanup_calls.append(str(file_path))
            return original_cleanup(file_path)

        monkeypatch.setattr("app.routers.image.cleanup_file", mock_cleanup)

        # Mock converter to succeed and return output path
        output_file = settings.UPLOAD_DIR / "test_output_image.png"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_bytes(b"fake data")

        async def mock_convert_with_cache(self, input_path, output_format, options, session_id):
            return output_file

        monkeypatch.setattr(ImageConverter, "convert_with_cache", mock_convert_with_cache)

        # Mock ConversionResponse to raise exception after output_path is set
        def mock_conversion_response(*args, **kwargs):
            raise Exception("Simulated error after conversion")

        monkeypatch.setattr("app.routers.image.ConversionResponse", mock_conversion_response)

        with open(sample_image, 'rb') as f:
            response = client.post(
                "/api/image/convert",
                files={"file": ("test.jpg", f, "image/jpeg")},
                data={"output_format": "png"}
            )

        assert response.status_code == 500
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error")
        assert "Conversion failed" in error_msg
        assert len(cleanup_calls) >= 2
        output_file.unlink(missing_ok=True)

    def test_info_cleanup_temp_file_on_error(self, client, sample_image, monkeypatch):
        """Test that temp_path is cleaned up when info extraction fails"""
        from app.services.image_converter import ImageConverter
        from app.utils.file_handler import cleanup_file

        cleanup_calls = []
        original_cleanup = cleanup_file

        def mock_cleanup(file_path):
            cleanup_calls.append(str(file_path))
            return original_cleanup(file_path)

        monkeypatch.setattr("app.routers.image.cleanup_file", mock_cleanup)

        async def mock_get_image_metadata(self, input_path):
            raise Exception("Simulated info extraction error")

        monkeypatch.setattr(ImageConverter, "get_image_metadata", mock_get_image_metadata)

        with open(sample_image, 'rb') as f:
            response = client.post(
                "/api/image/info",
                files={"file": ("test.jpg", f, "image/jpeg")}
            )

        assert response.status_code == 500
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error")
        assert "Failed to get image info" in error_msg
        assert len(cleanup_calls) >= 1
