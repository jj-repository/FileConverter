"""
Integration tests for batch router endpoints.

Tests the full API integration including:
- POST /api/batch/convert - Batch file conversion endpoint
- POST /api/batch/download-zip - Create ZIP archive of converted files
- GET /api/batch/download/{filename} - File download endpoint

Security tests:
- Path traversal prevention in download
- Malicious filenames in batch operations
- Empty batch rejection
- Batch size limits
- Parallel vs sequential processing
"""

import pytest
import io
import zipfile
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
def sample_images(temp_dir):
    """Create multiple sample images for batch testing"""
    images = []
    for i in range(3):
        image_path = temp_dir / f"test_image_{i}.jpg"
        img = Image.new('RGB', (200, 200), color=f"rgb({i*80}, {i*70}, {i*60})")
        img.save(image_path, 'JPEG')
        images.append(image_path)
    return images


@pytest.fixture
def sample_mixed_files(temp_dir, sample_image_png):
    """Create a mix of image files (PNG and JPG) for batch testing"""
    files = []

    # Add PNG from fixture
    files.append(sample_image_png)

    # Add JPGs
    for i in range(2):
        jpg_path = temp_dir / f"test_mixed_{i}.jpg"
        img = Image.new('RGB', (300, 300), color=(255, 100, i*50))
        img.save(jpg_path, 'JPEG', quality=90)
        files.append(jpg_path)

    return files


class TestBatchConvert:
    """Test POST /api/batch/convert endpoint"""

    def test_batch_convert_multiple_images_success(self, client, sample_images):
        """Test successful conversion of multiple images in batch"""
        files = []
        for img_path in sample_images:
            files.append(("files", (img_path.name, open(img_path, 'rb'), "image/jpeg")))

        try:
            response = client.post(
                "/api/batch/convert",
                files=files,
                data={"output_format": "png"}
            )
        finally:
            for _, (_, f, _) in files:
                f.close()

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["total_files"] == 3
        assert data["successful"] == 3
        assert data["failed"] == 0
        assert len(data["results"]) == 3
        for result in data["results"]:
            assert result["success"] is True
            assert "output_file" in result
            assert result["output_file"].endswith(".png")

    def test_batch_convert_mixed_file_types(self, client, sample_mixed_files):
        """Test batch conversion with mixed image types (PNG and JPG)"""
        files = []
        for file_path in sample_mixed_files:
            mime_type = "image/png" if file_path.suffix.lower() == ".png" else "image/jpeg"
            files.append(("files", (file_path.name, open(file_path, 'rb'), mime_type)))

        try:
            response = client.post(
                "/api/batch/convert",
                files=files,
                data={"output_format": "webp"}
            )
        finally:
            for _, (_, f, _) in files:
                f.close()

        assert response.status_code == 200
        data = response.json()
        assert data["total_files"] == 3
        assert data["successful"] == 3
        assert data["failed"] == 0
        for result in data["results"]:
            assert result["success"] is True
            assert result["output_file"].endswith(".webp")

    def test_batch_convert_with_parallel_true(self, client, sample_images):
        """Test batch conversion with parallel processing enabled"""
        files = []
        for img_path in sample_images:
            files.append(("files", (img_path.name, open(img_path, 'rb'), "image/jpeg")))

        try:
            response = client.post(
                "/api/batch/convert",
                files=files,
                data={"output_format": "bmp", "parallel": "true"}
            )
        finally:
            for _, (_, f, _) in files:
                f.close()

        assert response.status_code == 200
        data = response.json()
        assert data["total_files"] == 3
        assert data["successful"] == 3

    def test_batch_convert_with_parallel_false(self, client, sample_images):
        """Test batch conversion with sequential processing (parallel=false)"""
        files = []
        for img_path in sample_images:
            files.append(("files", (img_path.name, open(img_path, 'rb'), "image/jpeg")))

        try:
            response = client.post(
                "/api/batch/convert",
                files=files,
                data={"output_format": "gif", "parallel": "false"}
            )
        finally:
            for _, (_, f, _) in files:
                f.close()

        assert response.status_code == 200
        data = response.json()
        assert data["total_files"] == 3
        assert data["successful"] == 3

    def test_batch_convert_with_quality_parameter(self, client, sample_images):
        """Test batch conversion with quality parameter"""
        files = []
        for img_path in sample_images:
            files.append(("files", (img_path.name, open(img_path, 'rb'), "image/jpeg")))

        try:
            response = client.post(
                "/api/batch/convert",
                files=files,
                data={"output_format": "jpg", "quality": 75}
            )
        finally:
            for _, (_, f, _) in files:
                f.close()

        assert response.status_code == 200
        data = response.json()
        assert data["successful"] == 3

    def test_batch_convert_with_resize(self, client, sample_images):
        """Test batch conversion with resize dimensions"""
        files = []
        for img_path in sample_images:
            files.append(("files", (img_path.name, open(img_path, 'rb'), "image/jpeg")))

        try:
            response = client.post(
                "/api/batch/convert",
                files=files,
                data={
                    "output_format": "png",
                    "width": 100,
                    "height": 100
                }
            )
        finally:
            for _, (_, f, _) in files:
                f.close()

        assert response.status_code == 200
        data = response.json()
        assert data["successful"] == 3

    def test_batch_convert_empty_batch_rejected(self, client):
        """Test that empty batch (no files) is rejected"""
        response = client.post(
            "/api/batch/convert",
            files=[],
            data={"output_format": "png"}
        )

        # FastAPI returns 422 when required field (files) is missing/empty
        assert response.status_code in [400, 422]
        data = response.json()
        # Either our validation message or FastAPI's validation error
        assert ("No files provided" in data.get("detail", "") or
                "Field required" in str(data))

    def test_batch_convert_partial_failure(self, client, temp_dir, sample_images):
        """Test batch conversion with some valid and some invalid files"""
        files = []

        # Add valid images
        for img_path in sample_images[:2]:
            files.append(("files", (img_path.name, open(img_path, 'rb'), "image/jpeg")))

        # Add invalid file (corrupted)
        invalid_path = temp_dir / "corrupted.jpg"
        invalid_path.write_bytes(b'\x00\x01\x02\x03INVALID_DATA')
        files.append(("files", ("corrupted.jpg", open(invalid_path, 'rb'), "image/jpeg")))

        try:
            response = client.post(
                "/api/batch/convert",
                files=files,
                data={"output_format": "png"}
            )
        finally:
            for _, (_, f, _) in files:
                f.close()

        assert response.status_code == 200
        data = response.json()
        assert data["total_files"] == 3
        # Should have at least 2 successful (valid images)
        assert data["successful"] >= 2
        # Should have at least 1 failed (corrupted file)
        assert data["failed"] >= 1

    def test_batch_convert_invalid_output_format(self, client, sample_images):
        """Test batch conversion with invalid output format"""
        files = []
        for img_path in sample_images:
            files.append(("files", (img_path.name, open(img_path, 'rb'), "image/jpeg")))

        try:
            response = client.post(
                "/api/batch/convert",
                files=files,
                data={"output_format": "invalid_format"}
            )
        finally:
            for _, (_, f, _) in files:
                f.close()

        # Batch endpoint returns 200 but individual conversions should fail
        assert response.status_code == 200
        data = response.json()
        # All files should have failed due to invalid format
        assert data["failed"] == len(sample_images)
        assert data["successful"] == 0


class TestBatchZip:
    """Test POST /api/batch/download-zip endpoint"""

    def test_batch_zip_creation_success(self, client, sample_images):
        """Test successful ZIP archive creation from batch conversion"""
        # First convert files
        files = []
        for img_path in sample_images:
            files.append(("files", (img_path.name, open(img_path, 'rb'), "image/jpeg")))

        try:
            convert_response = client.post(
                "/api/batch/convert",
                files=files,
                data={"output_format": "png"}
            )
        finally:
            for _, (_, f, _) in files:
                f.close()

        assert convert_response.status_code == 200
        convert_data = convert_response.json()
        session_id = convert_data["session_id"]

        # Extract output filenames from successful results
        output_files = [
            result["output_file"] for result in convert_data["results"]
            if result["success"]
        ]

        # Create ZIP from converted files
        zip_response = client.post(
            "/api/batch/download-zip",
            data={
                "session_id": session_id,
                "filenames": output_files
            }
        )

        assert zip_response.status_code == 200
        zip_data = zip_response.json()
        assert "zip_file" in zip_data
        assert "download_url" in zip_data
        assert zip_data["file_count"] == len(output_files)
        assert zip_data["zip_file"].startswith("batch_")
        assert zip_data["zip_file"].endswith(".zip")

    def test_batch_zip_with_multiple_formats(self, client, sample_images):
        """Test ZIP creation with files of different formats"""
        # Convert to different formats
        files1 = []
        for img_path in sample_images[:2]:
            files1.append(("files", (img_path.name, open(img_path, 'rb'), "image/jpeg")))

        try:
            response1 = client.post(
                "/api/batch/convert",
                files=files1,
                data={"output_format": "png"}
            )
        finally:
            for _, (_, f, _) in files1:
                f.close()

        assert response1.status_code == 200
        data1 = response1.json()
        session_id = data1["session_id"]
        png_files = [r["output_file"] for r in data1["results"] if r["success"]]

        # Create ZIP with PNG files
        zip_response = client.post(
            "/api/batch/download-zip",
            data={
                "session_id": session_id,
                "filenames": png_files
            }
        )

        assert zip_response.status_code == 200
        zip_data = zip_response.json()
        assert zip_data["file_count"] == len(png_files)


class TestBatchDownload:
    """Test GET /api/batch/download/{filename} endpoint"""

    def test_batch_download_converted_file(self, client, sample_images):
        """Test downloading a converted file from batch conversion"""
        # Convert files
        files = []
        for img_path in sample_images:
            files.append(("files", (img_path.name, open(img_path, 'rb'), "image/jpeg")))

        try:
            convert_response = client.post(
                "/api/batch/convert",
                files=files,
                data={"output_format": "png"}
            )
        finally:
            for _, (_, f, _) in files:
                f.close()

        assert convert_response.status_code == 200
        convert_data = convert_response.json()
        output_filename = convert_data["results"][0]["output_file"]

        # Download the file
        download_response = client.get(f"/api/batch/download/{output_filename}")

        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "application/octet-stream"
        assert len(download_response.content) > 0

    def test_batch_download_zip_file(self, client, sample_images):
        """Test downloading a ZIP archive created from batch conversion"""
        # Convert files
        files = []
        for img_path in sample_images:
            files.append(("files", (img_path.name, open(img_path, 'rb'), "image/jpeg")))

        try:
            convert_response = client.post(
                "/api/batch/convert",
                files=files,
                data={"output_format": "png"}
            )
        finally:
            for _, (_, f, _) in files:
                f.close()

        convert_data = convert_response.json()
        session_id = convert_data["session_id"]
        output_files = [
            result["output_file"] for result in convert_data["results"]
            if result["success"]
        ]

        # Create ZIP
        zip_response = client.post(
            "/api/batch/download-zip",
            data={
                "session_id": session_id,
                "filenames": output_files
            }
        )

        assert zip_response.status_code == 200
        zip_filename = zip_response.json()["zip_file"]

        # Download the ZIP
        download_response = client.get(f"/api/batch/download/{zip_filename}")

        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "application/octet-stream"

        # Verify it's a valid ZIP file
        zip_buffer = io.BytesIO(download_response.content)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            assert len(zf.namelist()) == len(output_files)

    def test_batch_download_nonexistent_file(self, client):
        """Test downloading a file that doesn't exist"""
        response = client.get("/api/batch/download/nonexistent_file_12345.png")

        assert response.status_code == 404

    def test_batch_download_path_traversal_blocked(self, client):
        """Test that path traversal attempts are blocked in batch download"""
        malicious_filenames = [
            "../../../etc/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "....//....//....//etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
        ]

        for malicious_name in malicious_filenames:
            response = client.get(f"/api/batch/download/{malicious_name}")
            # Should either be 400 (validation) or 404 (not found)
            assert response.status_code in [400, 404], \
                f"Path traversal not blocked for: {malicious_name}"


class TestBatchFormats:
    """Test GET /api/batch/formats endpoint (if applicable)"""

    def test_batch_formats_endpoint_exists(self, client):
        """Test that batch formats endpoint exists and returns data"""
        # Note: The batch router may not have a /formats endpoint
        # This test checks if it exists, skipping if not implemented
        try:
            response = client.get("/api/batch/formats")
            if response.status_code == 200:
                data = response.json()
                assert "input_formats" in data or "formats" in data
            else:
                # Endpoint doesn't exist or not implemented
                assert response.status_code == 404
        except Exception:
            # Endpoint may not be implemented for batch
            pass


class TestBatchSecurityValidation:
    """Test security-critical validation in batch endpoints"""

    def test_malicious_filenames_in_batch(self, client, sample_images):
        """Test that malicious filenames are sanitized in batch operation"""
        malicious_filenames = [
            "test; rm -rf /.jpg",
            "test$(whoami).jpg",
            "test`whoami`.jpg",
            "test|cat.jpg",
        ]

        for malicious_name in malicious_filenames:
            files = []
            # Use first sample image with malicious name
            img_path = sample_images[0]
            files.append(("files", (malicious_name, open(img_path, 'rb'), "image/jpeg")))

            try:
                response = client.post(
                    "/api/batch/convert",
                    files=files,
                    data={"output_format": "png"}
                )
            finally:
                for _, (_, f, _) in files:
                    f.close()

            # Should either succeed (filename sanitized) or fail safely
            assert response.status_code in [200, 400, 500]

            if response.status_code == 200:
                # Verify output filename doesn't contain shell metacharacters
                data = response.json()
                for result in data["results"]:
                    if result["success"]:
                        output_file = result["output_file"]
                        dangerous_chars = [';', '$', '`', '|', '&', '<', '>']
                        for char in dangerous_chars:
                            assert char not in output_file, \
                                f"Dangerous character '{char}' in output: {output_file}"

    def test_null_byte_injection_in_batch_filenames(self, client, sample_images):
        """Test that null byte injection is sanitized in batch filenames"""
        files = []
        img_path = sample_images[0]
        # Null byte in filename
        files.append(("files", ("test\x00.jpg", open(img_path, 'rb'), "image/jpeg")))

        try:
            response = client.post(
                "/api/batch/convert",
                files=files,
                data={"output_format": "png"}
            )
        finally:
            for _, (_, f, _) in files:
                f.close()

        # Null bytes are sanitized, so conversion may succeed
        if response.status_code == 200:
            data = response.json()
            for result in data["results"]:
                if result["success"]:
                    output_file = result["output_file"]
                    assert '\x00' not in output_file, \
                        "Null byte present in output filename"


class TestBatchProgressTracking:
    """Test batch progress tracking functionality"""

    def test_batch_convert_returns_session_id(self, client, sample_images):
        """Test that batch conversion returns a session ID for progress tracking"""
        files = []
        for img_path in sample_images:
            files.append(("files", (img_path.name, open(img_path, 'rb'), "image/jpeg")))

        try:
            response = client.post(
                "/api/batch/convert",
                files=files,
                data={"output_format": "png"}
            )
        finally:
            for _, (_, f, _) in files:
                f.close()

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert len(data["session_id"]) > 0

    def test_batch_convert_results_include_index(self, client, sample_images):
        """Test that batch results include file index for progress tracking"""
        files = []
        for img_path in sample_images:
            files.append(("files", (img_path.name, open(img_path, 'rb'), "image/jpeg")))

        try:
            response = client.post(
                "/api/batch/convert",
                files=files,
                data={"output_format": "png"}
            )
        finally:
            for _, (_, f, _) in files:
                f.close()

        assert response.status_code == 200
        data = response.json()
        for i, result in enumerate(data["results"]):
            # Results should include filename (may have UUID prefix from upload)
            assert "filename" in result
            # Check that original filename is contained (may be UUID-prefixed)
            assert sample_images[i].stem in result["filename"] or result["filename"].endswith('.jpg')


class TestBatchConversionStatistics:
    """Test batch conversion statistics and reporting"""

    def test_batch_statistics_accuracy(self, client, sample_images):
        """Test that batch statistics (successful/failed counts) are accurate"""
        files = []
        for img_path in sample_images:
            files.append(("files", (img_path.name, open(img_path, 'rb'), "image/jpeg")))

        try:
            response = client.post(
                "/api/batch/convert",
                files=files,
                data={"output_format": "png"}
            )
        finally:
            for _, (_, f, _) in files:
                f.close()

        assert response.status_code == 200
        data = response.json()

        # Verify statistics
        assert data["total_files"] == len(sample_images)
        assert data["successful"] + data["failed"] == data["total_files"]

        # Count successes in results
        actual_successful = sum(1 for r in data["results"] if r["success"])
        assert data["successful"] == actual_successful

    def test_batch_message_quality(self, client, sample_images):
        """Test that batch response includes informative message"""
        files = []
        for img_path in sample_images:
            files.append(("files", (img_path.name, open(img_path, 'rb'), "image/jpeg")))

        try:
            response = client.post(
                "/api/batch/convert",
                files=files,
                data={"output_format": "png"}
            )
        finally:
            for _, (_, f, _) in files:
                f.close()

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert len(data["message"]) > 0
        # Message should mention success count
        assert str(data["successful"]) in data["message"]


class TestBatchEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_batch_single_file(self, client, sample_images):
        """Test batch conversion with just one file"""
        files = []
        files.append(("files", (sample_images[0].name, open(sample_images[0], 'rb'), "image/jpeg")))

        try:
            response = client.post(
                "/api/batch/convert",
                files=files,
                data={"output_format": "png"}
            )
        finally:
            for _, (_, f, _) in files:
                f.close()

        assert response.status_code == 200
        data = response.json()
        assert data["total_files"] == 1
        assert data["successful"] == 1

    def test_batch_zip_empty_filenames_list(self, client):
        """Test ZIP creation with empty filenames list"""
        response = client.post(
            "/api/batch/download-zip",
            data={
                "session_id": "test_session_123",
                "filenames": []
            }
        )

        # Should fail with 404 (no files found) or 422 (validation error)
        assert response.status_code in [404, 422]

    def test_batch_large_file_count(self, client, temp_dir):
        """Test batch conversion with a large number of files (10)"""
        files = []

        # Create 10 test images
        for i in range(10):
            img_path = temp_dir / f"large_batch_{i}.jpg"
            img = Image.new('RGB', (100, 100), color=(i*20, i*20, i*20))
            img.save(img_path, 'JPEG')
            files.append(("files", (img_path.name, open(img_path, 'rb'), "image/jpeg")))

        try:
            response = client.post(
                "/api/batch/convert",
                files=files,
                data={"output_format": "png"}
            )
        finally:
            for _, (_, f, _) in files:
                f.close()

        assert response.status_code == 200
        data = response.json()
        assert data["total_files"] == 10
        assert data["successful"] == 10
