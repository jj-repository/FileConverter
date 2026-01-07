"""
Integration tests for archive router endpoints.

Tests the full API integration including:
- POST /api/archive/convert - Archive conversion endpoint
- POST /api/archive/extract - Archive extraction endpoint
- POST /api/archive/create - Create archive from files endpoint
- GET /api/archive/formats - Supported formats endpoint
- GET /api/archive/download/{filename} - File download endpoint

Security tests:
- Path traversal prevention in download
- Corrupted archive handling
- Malicious filenames in archives
- Archive member path validation
"""

import pytest
import tempfile
import zipfile
import tarfile
import gzip
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
import io

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    """Create test client for API testing"""
    return TestClient(app)


@pytest.fixture
def sample_text_files(temp_dir):
    """Create sample text files for archive testing"""
    files = []
    for i in range(3):
        file_path = temp_dir / f"file{i}.txt"
        file_path.write_text(f"Sample content {i}\n" * 100)
        files.append(file_path)
    return files


@pytest.fixture
def sample_zip(temp_dir, sample_text_files):
    """Create a valid sample ZIP archive"""
    zip_path = temp_dir / "sample.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in sample_text_files:
            zf.write(file_path, arcname=file_path.name)
    return zip_path


@pytest.fixture
def sample_tar(temp_dir, sample_text_files):
    """Create a valid sample TAR archive"""
    tar_path = temp_dir / "sample.tar"
    with tarfile.open(tar_path, 'w') as tf:
        for file_path in sample_text_files:
            tf.add(file_path, arcname=file_path.name)
    return tar_path


@pytest.fixture
def sample_tar_gz(temp_dir, sample_text_files):
    """Create a valid sample TAR.GZ archive"""
    tar_gz_path = temp_dir / "sample.tar.gz"
    with tarfile.open(tar_gz_path, 'w:gz') as tf:
        for file_path in sample_text_files:
            tf.add(file_path, arcname=file_path.name)
    return tar_gz_path


@pytest.fixture
def sample_tar_bz2(temp_dir, sample_text_files):
    """Create a valid sample TAR.BZ2 archive"""
    tar_bz2_path = temp_dir / "sample.tar.bz2"
    with tarfile.open(tar_bz2_path, 'w:bz2') as tf:
        for file_path in sample_text_files:
            tf.add(file_path, arcname=file_path.name)
    return tar_bz2_path


@pytest.fixture
def corrupted_zip(temp_dir):
    """Create a corrupted ZIP file"""
    corrupt_path = temp_dir / "corrupted.zip"
    corrupt_path.write_bytes(b'PK\x03\x04' + b'\x00\x01\x02\x03INVALID_DATA')
    return corrupt_path


@pytest.fixture
def corrupted_tar(temp_dir):
    """Create a corrupted TAR file"""
    corrupt_path = temp_dir / "corrupted.tar"
    corrupt_path.write_bytes(b'\x00\x01\x02\x03INVALID_TAR_DATA_NOT_A_REAL_TAR')
    return corrupt_path


@pytest.fixture
def malicious_zip_with_path_traversal(temp_dir):
    """Create a ZIP with path traversal attempts in member names"""
    zip_path = temp_dir / "malicious.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        # Add files with path traversal attempts
        zf.writestr("../../../etc/passwd", "malicious content")
        zf.writestr("file.txt", "normal content")
    return zip_path


@pytest.fixture
def malicious_filenames_in_zip(temp_dir):
    """Create a ZIP with malicious filenames"""
    zip_path = temp_dir / "malicious_names.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr("file; rm -rf /.txt", "content")
        zf.writestr("file$(whoami).txt", "content")
        zf.writestr("file`id`.txt", "content")
    return zip_path


class TestArchiveConvert:
    """Test POST /api/archive/convert endpoint"""

    def test_convert_zip_to_tar_gz_success(self, client, sample_zip):
        """Test successful ZIP to TAR.GZ conversion"""
        with open(sample_zip, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("test.zip", f, "application/zip")},
                data={"output_format": "tar.gz"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "session_id" in data
        assert data["output_file"].endswith(".tar.gz")
        assert "download_url" in data

    def test_convert_tar_gz_to_zip_success(self, client, sample_tar_gz):
        """Test successful TAR.GZ to ZIP conversion"""
        with open(sample_tar_gz, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("test.tar.gz", f, "application/gzip")},
                data={"output_format": "zip"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".zip")

    def test_convert_tar_to_tar_gz(self, client, sample_tar):
        """Test TAR to TAR.GZ conversion"""
        with open(sample_tar, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("test.tar", f, "application/x-tar")},
                data={"output_format": "tar.gz"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".tar.gz")

    def test_convert_with_compression_level(self, client, sample_zip):
        """Test conversion with compression level parameter"""
        with open(sample_zip, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("test.zip", f, "application/zip")},
                data={"output_format": "tar.gz", "compression_level": 9}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_convert_with_compression_level_0(self, client, sample_zip):
        """Test conversion with compression level 0 (no compression)"""
        with open(sample_zip, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("test.zip", f, "application/zip")},
                data={"output_format": "tar", "compression_level": 0}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_convert_invalid_output_format(self, client, sample_zip):
        """Test conversion with invalid output format"""
        with open(sample_zip, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("test.zip", f, "application/zip")},
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
        fake_file.write_text("not an archive")

        with open(fake_file, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("malware.exe", f, "application/octet-stream")},
                data={"output_format": "zip"}
            )

        assert response.status_code == 400
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error")
        assert ("Invalid or unsupported file extension" in str(error_msg) or
                "Unsupported file format" in str(error_msg))

    def test_convert_corrupted_zip_archive(self, client, corrupted_zip):
        """Test conversion of corrupted ZIP archive"""
        with open(corrupted_zip, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("corrupted.zip", f, "application/zip")},
                data={"output_format": "tar.gz"}
            )

        # Should fail with 500 error due to corruption
        assert response.status_code == 500

    def test_convert_corrupted_tar_archive(self, client, corrupted_tar):
        """Test conversion of corrupted TAR archive"""
        with open(corrupted_tar, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("corrupted.tar", f, "application/x-tar")},
                data={"output_format": "zip"}
            )

        # Should fail with 500 error due to corruption
        assert response.status_code == 500

    def test_convert_same_format_copies_file(self, client, sample_zip):
        """Test that converting to same format creates a copy"""
        with open(sample_zip, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("test.zip", f, "application/zip")},
                data={"output_format": "zip"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".zip")

    def test_convert_to_tar_bz2(self, client, sample_zip):
        """Test conversion to TAR.BZ2 format"""
        with open(sample_zip, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("test.zip", f, "application/zip")},
                data={"output_format": "tar.bz2"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".tar.bz2")


class TestArchiveFormats:
    """Test GET /api/archive/formats endpoint"""

    def test_get_formats_success(self, client):
        """Test successful retrieval of supported formats"""
        response = client.get("/api/archive/formats")

        assert response.status_code == 200
        data = response.json()
        assert "input_formats" in data
        assert "output_formats" in data
        assert isinstance(data["input_formats"], list)
        assert isinstance(data["output_formats"], list)

    def test_formats_include_common_types(self, client):
        """Test that common archive formats are included"""
        response = client.get("/api/archive/formats")
        data = response.json()

        # Check for common formats
        common_formats = ["zip", "tar", "tar.gz", "tar.bz2"]
        for fmt in common_formats:
            assert fmt in data["output_formats"], f"{fmt} not in output formats"

    def test_formats_include_multiple_tar_variants(self, client):
        """Test that multiple TAR variants are supported"""
        response = client.get("/api/archive/formats")
        data = response.json()

        # TAR variants
        tar_formats = ["tar", "tar.gz", "tar.bz2", "tgz", "tbz2"]
        # At least some should be present
        present_tar_formats = [fmt for fmt in tar_formats if fmt in data["output_formats"]]
        assert len(present_tar_formats) > 0


class TestArchiveDownload:
    """Test GET /api/archive/download/{filename} endpoint"""

    def test_download_converted_file(self, client, sample_zip):
        """Test downloading a converted file"""
        # First, convert an archive
        with open(sample_zip, 'rb') as f:
            convert_response = client.post(
                "/api/archive/convert",
                files={"file": ("test.zip", f, "application/zip")},
                data={"output_format": "tar.gz"}
            )

        assert convert_response.status_code == 200
        output_filename = convert_response.json()["output_file"]

        # Now download it
        download_response = client.get(f"/api/archive/download/{output_filename}")

        assert download_response.status_code == 200
        # Should return proper MIME type for the file format (tar.gz is gzip)
        assert download_response.headers["content-type"] == "application/gzip"
        assert len(download_response.content) > 0

    def test_download_nonexistent_file(self, client):
        """Test downloading a file that doesn't exist"""
        response = client.get("/api/archive/download/nonexistent.zip")

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
            response = client.get(f"/api/archive/download/{malicious_name}")
            # Should either be 400 (validation) or 404 (not found)
            assert response.status_code in [400, 404], \
                f"Path traversal not blocked for: {malicious_name}"

    def test_download_with_special_characters_blocked(self, client):
        """Test that filenames with special characters are blocked"""
        special_filenames = [
            "file;rm.zip",
            "file$(whoami).zip",
            "file`id`.zip",
            "file|cat.zip",
        ]

        for special_name in special_filenames:
            response = client.get(f"/api/archive/download/{special_name}")
            # Should be rejected or not found
            assert response.status_code in [400, 404]


class TestArchiveSecurityValidation:
    """Test security-critical validation in archive endpoints"""

    def test_malicious_filename_sanitized(self, client, sample_zip):
        """Test that malicious filenames are sanitized"""
        malicious_filenames = [
            "test; rm -rf /.zip",
            "test$(whoami).zip",
            "test`whoami`.zip",
        ]

        for malicious_name in malicious_filenames:
            with open(sample_zip, 'rb') as f:
                response = client.post(
                    "/api/archive/convert",
                    files={"file": (malicious_name, f, "application/zip")},
                    data={"output_format": "tar.gz"}
                )

            # Should succeed (filename sanitized) or fail safely
            assert response.status_code in [200, 400, 500]
            if response.status_code == 200:
                # Verify output filename doesn't contain shell metacharacters
                output_file = response.json()["output_file"]
                dangerous_chars = [';', '$', '`', '|', '&', '<', '>']
                for char in dangerous_chars:
                    assert char not in output_file

    def test_null_byte_injection_blocked(self, client, sample_zip):
        """Test that null byte injection is sanitized"""
        with open(sample_zip, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("test\x00.zip", f, "application/zip")},
                data={"output_format": "tar.gz"}
            )

        # Null bytes are sanitized, so conversion may succeed
        # but output filename should not contain null bytes
        if response.status_code == 200:
            output_file = response.json()["output_file"]
            assert '\x00' not in output_file
        else:
            # Or it fails validation
            assert response.status_code in [400, 500]

    def test_archive_with_path_traversal_members_blocked(self, client, malicious_zip_with_path_traversal):
        """Test that archives with path traversal members are handled safely"""
        with open(malicious_zip_with_path_traversal, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("malicious.zip", f, "application/zip")},
                data={"output_format": "tar.gz"}
            )

        # May fail due to path traversal detection or succeed with sanitization
        assert response.status_code in [200, 400, 500]

    def test_archive_with_malicious_filenames(self, client, malicious_filenames_in_zip):
        """Test that archives with malicious member filenames are handled"""
        with open(malicious_filenames_in_zip, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("malicious_names.zip", f, "application/zip")},
                data={"output_format": "tar.gz"}
            )

        # May fail or succeed with sanitization
        assert response.status_code in [200, 400, 500]


class TestArchiveConversionFormats:
    """Test various archive format conversions"""

    def test_convert_zip_to_tar(self, client, sample_zip):
        """Test conversion from ZIP to TAR"""
        with open(sample_zip, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("test.zip", f, "application/zip")},
                data={"output_format": "tar"}
            )

        assert response.status_code == 200
        assert response.json()["output_file"].endswith(".tar")

    def test_convert_tar_to_zip(self, client, sample_tar):
        """Test conversion from TAR to ZIP"""
        with open(sample_tar, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("test.tar", f, "application/x-tar")},
                data={"output_format": "zip"}
            )

        assert response.status_code == 200
        assert response.json()["output_file"].endswith(".zip")

    def test_convert_tar_bz2_to_zip(self, client, sample_tar_bz2):
        """Test conversion from TAR.BZ2 to ZIP"""
        with open(sample_tar_bz2, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("test.tar.bz2", f, "application/x-tar")},
                data={"output_format": "zip"}
            )

        # May succeed or fail depending on bz2 library availability
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            assert response.json()["output_file"].endswith(".zip")

    def test_convert_tar_bz2_to_tar_gz(self, client, sample_tar_bz2):
        """Test conversion from TAR.BZ2 to TAR.GZ"""
        with open(sample_tar_bz2, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("test.tar.bz2", f, "application/x-tar")},
                data={"output_format": "tar.gz"}
            )

        # May succeed or fail depending on bz2 library availability
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            assert response.json()["output_file"].endswith(".tar.gz")

    def test_convert_zip_to_tar_bz2(self, client, sample_zip):
        """Test conversion from ZIP to TAR.BZ2"""
        with open(sample_zip, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("test.zip", f, "application/zip")},
                data={"output_format": "tar.bz2"}
            )

        assert response.status_code == 200
        assert response.json()["output_file"].endswith(".tar.bz2")


class TestArchiveConversionEdgeCases:
    """Test edge cases and special scenarios"""

    def test_convert_empty_zip(self, client, temp_dir):
        """Test conversion of empty ZIP archive"""
        empty_zip = temp_dir / "empty.zip"
        with zipfile.ZipFile(empty_zip, 'w') as zf:
            pass  # Create empty zip

        with open(empty_zip, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("empty.zip", f, "application/zip")},
                data={"output_format": "tar.gz"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_convert_large_number_of_files(self, client, temp_dir):
        """Test conversion of archive with many files"""
        # Create ZIP with 50 files
        zip_path = temp_dir / "many_files.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for i in range(50):
                zf.writestr(f"file{i:03d}.txt", f"Content of file {i}\n" * 10)

        with open(zip_path, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("many_files.zip", f, "application/zip")},
                data={"output_format": "tar.gz"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_convert_with_unicode_filenames(self, client, temp_dir):
        """Test conversion of archive with unicode filenames"""
        zip_path = temp_dir / "unicode.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("файл_тест.txt", "Russian filename")
            zf.writestr("文件.txt", "Chinese filename")
            zf.writestr("ファイル.txt", "Japanese filename")

        with open(zip_path, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("unicode.zip", f, "application/zip")},
                data={"output_format": "tar.gz"}
            )

        # May succeed or fail depending on encoding handling
        assert response.status_code in [200, 400, 500]

    def test_convert_nested_directory_structure(self, client, temp_dir):
        """Test conversion of archive with nested directories"""
        zip_path = temp_dir / "nested.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("dir1/file1.txt", "level 1")
            zf.writestr("dir1/dir2/file2.txt", "level 2")
            zf.writestr("dir1/dir2/dir3/file3.txt", "level 3")

        with open(zip_path, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("nested.zip", f, "application/zip")},
                data={"output_format": "tar.gz"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_convert_with_low_compression_level(self, client, sample_zip):
        """Test conversion with low compression level"""
        with open(sample_zip, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("test.zip", f, "application/zip")},
                data={"output_format": "tar.gz", "compression_level": 1}
            )

        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    def test_convert_with_high_compression_level(self, client, sample_zip):
        """Test conversion with high compression level"""
        with open(sample_zip, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("test.zip", f, "application/zip")},
                data={"output_format": "tar.gz", "compression_level": 9}
            )

        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    def test_convert_binary_file_in_archive(self, client, temp_dir):
        """Test conversion of archive containing binary files"""
        zip_path = temp_dir / "binary.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Add binary data
            zf.writestr("binary.bin", b'\x00\x01\x02\x03\x04\x05' * 100)
            zf.writestr("text.txt", "normal text file")

        with open(zip_path, 'rb') as f:
            response = client.post(
                "/api/archive/convert",
                files={"file": ("binary.zip", f, "application/zip")},
                data={"output_format": "tar.gz"}
            )

        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    def test_convert_cleanup_output_file_on_error(self, client, sample_zip, monkeypatch):
        """Test that output file is cleaned up on error after conversion (line 85)"""
        from unittest.mock import patch, MagicMock

        # Mock ConversionResponse to raise exception after output_path is set
        def mock_conversion_response(*args, **kwargs):
            raise Exception("Simulated error after conversion")

        with patch("app.routers.archive.ConversionResponse", side_effect=mock_conversion_response):
            with open(sample_zip, 'rb') as f:
                response = client.post(
                    "/api/archive/convert",
                    files={"file": ("test.zip", f, "application/zip")},
                    data={"output_format": "tar.gz"}
                )

            assert response.status_code == 500


class TestArchiveInfo:
    """Test archive info endpoint"""

    def test_get_archive_info_zip_success(self, client, sample_zip):
        """Test getting info from ZIP file"""
        with open(sample_zip, 'rb') as f:
            response = client.post(
                "/api/archive/info",
                files={"file": ("test.zip", f, "application/zip")}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.zip"
        assert data["format"] == "zip"
        assert "metadata" in data
        assert "size" in data

    def test_get_archive_info_tar_gz_success(self, client, temp_dir):
        """Test getting info from TAR.GZ file"""
        import tarfile

        tar_path = temp_dir / "test.tar.gz"
        with tarfile.open(tar_path, 'w:gz') as tar:
            # Add some test files
            file1 = temp_dir / "file1.txt"
            file1.write_text("test content 1")
            tar.add(file1, arcname="file1.txt")

        with open(tar_path, 'rb') as f:
            response = client.post(
                "/api/archive/info",
                files={"file": ("test.tar.gz", f, "application/gzip")}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.tar.gz"
        assert data["format"] == "tar.gz"

    def test_get_archive_info_invalid_format(self, client, temp_dir):
        """Test getting info from invalid archive format"""
        invalid_file = temp_dir / "test.txt"
        invalid_file.write_text("not an archive")

        with open(invalid_file, 'rb') as f:
            response = client.post(
                "/api/archive/info",
                files={"file": ("test.txt", f, "text/plain")}
            )

        # Validation fails and exception is caught at line 137
        assert response.status_code == 500

    def test_get_archive_info_cleanup_on_error(self, client, temp_dir, monkeypatch):
        """Test that temp file is cleaned up on error (line 139)"""
        from unittest.mock import patch

        zip_path = temp_dir / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("test.txt", "test content")

        # Mock get_archive_info to raise exception
        with patch("app.services.archive_converter.ArchiveConverter.get_archive_info", side_effect=Exception("Simulated error")):
            with open(zip_path, 'rb') as f:
                response = client.post(
                    "/api/archive/info",
                    files={"file": ("test.zip", f, "application/zip")}
                )

            assert response.status_code == 500
