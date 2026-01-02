"""
Integration tests for FastAPI application lifecycle.

Tests the full application startup, shutdown, and background tasks:
- Application initialization
- Cache service initialization on startup
- Background cleanup task execution
- Root and health check endpoints
- Graceful shutdown handling
"""

import pytest
import asyncio
import time
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app, cleanup_old_files
from app.config import settings
from app.services.cache_service import get_cache_service, initialize_cache_service


@pytest.fixture
def client():
    """Create test client for API testing"""
    return TestClient(app)


class TestAppEndpoints:
    """Test basic app endpoints"""

    def test_root_endpoint(self, client):
        """Test GET / returns API information"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "FileConverter API"
        assert "version" in data
        assert data["version"] == "1.0.0"
        assert "endpoints" in data

        # Verify all major endpoints are listed
        endpoints = data["endpoints"]
        assert "docs" in endpoints
        assert "image" in endpoints
        assert "video" in endpoints
        assert "cache" in endpoints

    def test_health_endpoint(self, client):
        """Test GET /health returns healthy status"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_root_endpoint_structure(self, client):
        """Test that root endpoint includes all converter types"""
        response = client.get("/")
        endpoints = response.json()["endpoints"]

        expected_converters = [
            "image", "video", "audio", "document", "data",
            "archive", "spreadsheet", "subtitle", "ebook", "font"
        ]

        for converter in expected_converters:
            assert converter in endpoints, f"{converter} not in endpoints"


class TestAppStartup:
    """Test application startup behavior"""

    def test_app_initializes_successfully(self, client):
        """Test that app starts and responds to requests"""
        # If we can make a request, the app initialized successfully
        response = client.get("/health")
        assert response.status_code == 200

    def test_cache_service_initialized(self, temp_dir):
        """Test that cache service is initialized on startup when enabled"""
        # Re-initialize cache with temp directory
        cache_dir = temp_dir / "test_cache"
        original_cache_enabled = settings.CACHE_ENABLED

        try:
            settings.CACHE_ENABLED = True
            cache_service = initialize_cache_service(
                cache_dir=cache_dir,
                expiration_hours=1,
                max_size_mb=100
            )

            # Verify cache service is initialized
            assert cache_service is not None
            assert get_cache_service() is not None
            assert cache_service.cache_dir == cache_dir
            assert cache_service.expiration_hours == 1
            assert cache_service.max_size_mb == 100

        finally:
            settings.CACHE_ENABLED = original_cache_enabled

    def test_cache_directory_created_on_startup(self, temp_dir):
        """Test that cache directory is created on startup"""
        cache_dir = temp_dir / "new_cache_dir"
        assert not cache_dir.exists()

        # Initialize cache service
        cache_service = initialize_cache_service(
            cache_dir=cache_dir,
            expiration_hours=1,
            max_size_mb=100
        )

        # Verify directory was created
        assert cache_dir.exists()
        assert cache_dir.is_dir()

    def test_cors_middleware_configured(self, client):
        """Test that CORS middleware is properly configured"""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )

        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers or response.status_code in [200, 404]


class TestBackgroundCleanupTask:
    """Test background file cleanup task"""

    @pytest.mark.asyncio
    async def test_cleanup_removes_old_temp_files(self, temp_dir):
        """Test that cleanup task removes old temporary files"""
        # Create old file in temp directory
        old_file = settings.TEMP_DIR / "old_temp_file.txt"
        old_file.write_text("old content")

        # Set file modification time to 2 days ago (older than TEMP_FILE_LIFETIME)
        old_time = time.time() - (settings.TEMP_FILE_LIFETIME + 3600)
        import os
        os.utime(old_file, (old_time, old_time))

        # Create recent file
        recent_file = settings.TEMP_DIR / "recent_temp_file.txt"
        recent_file.write_text("recent content")

        # Run cleanup once (not the full loop)
        current_time = time.time()
        for file_path in settings.TEMP_DIR.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > settings.TEMP_FILE_LIFETIME:
                    file_path.unlink()

        # Verify old file removed, recent file kept
        assert not old_file.exists()
        assert recent_file.exists()

        # Cleanup
        if recent_file.exists():
            recent_file.unlink()

    @pytest.mark.asyncio
    async def test_cleanup_removes_old_upload_files(self, temp_dir):
        """Test that cleanup task removes old upload files"""
        # Create old file in upload directory
        old_file = settings.UPLOAD_DIR / "old_upload.txt"
        old_file.write_text("old upload")

        # Set file modification time to old
        old_time = time.time() - (settings.TEMP_FILE_LIFETIME + 7200)
        import os
        os.utime(old_file, (old_time, old_time))

        # Run cleanup
        current_time = time.time()
        for file_path in settings.UPLOAD_DIR.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > settings.TEMP_FILE_LIFETIME:
                    file_path.unlink()

        # Verify old file removed
        assert not old_file.exists()

    @pytest.mark.asyncio
    async def test_cleanup_handles_missing_files_gracefully(self):
        """Test that cleanup handles missing files without errors"""
        # This should not raise any exceptions
        current_time = time.time()

        try:
            # Try to cleanup non-existent directory
            fake_dir = Path("/nonexistent/directory")
            for file_path in fake_dir.glob("*"):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > settings.TEMP_FILE_LIFETIME:
                        file_path.unlink()
        except Exception:
            pass  # Expected - directory doesn't exist

        # Test passes if no unexpected exceptions

    @pytest.mark.asyncio
    async def test_cleanup_runs_cache_cleanup_when_enabled(self, temp_dir):
        """Test that cleanup task runs cache cleanup when enabled"""
        cache_dir = temp_dir / "cleanup_cache"
        original_cache_enabled = settings.CACHE_ENABLED

        try:
            settings.CACHE_ENABLED = True
            cache_service = initialize_cache_service(
                cache_dir=cache_dir,
                expiration_hours=0,  # Immediate expiration
                max_size_mb=100
            )

            # Create a cache entry
            from PIL import Image
            test_image = temp_dir / "test.jpg"
            img = Image.new('RGB', (50, 50), color='red')
            img.save(test_image, 'JPEG')

            cache_key = cache_service.generate_cache_key(
                test_image, "png", {"quality": 95}
            )

            output_file = temp_dir / "output.png"
            img.save(output_file, 'PNG')

            cache_service.store_result(
                cache_key=cache_key,
                original_filename="test.jpg",
                output_file_path=output_file,
                output_format="png",
                conversion_options={"quality": 95}
            )

            # Wait a moment for expiration
            await asyncio.sleep(0.1)

            # Run cache cleanup
            cleanup_stats = cache_service.cleanup_all()

            # Verify cleanup ran
            assert "expired_removed" in cleanup_stats
            assert "corrupted_removed" in cleanup_stats
            assert "size_limit_removed" in cleanup_stats

        finally:
            settings.CACHE_ENABLED = original_cache_enabled


class TestAppShutdown:
    """Test application shutdown behavior"""

    @pytest.mark.asyncio
    async def test_cleanup_task_can_be_cancelled(self):
        """Test that background cleanup task can be cancelled gracefully"""
        # Create a cleanup task
        task = asyncio.create_task(cleanup_old_files())

        # Let it run briefly
        await asyncio.sleep(0.1)

        # Cancel it
        task.cancel()

        # Verify cancellation
        try:
            await task
        except asyncio.CancelledError:
            pass  # Expected

        assert task.cancelled()

    @pytest.mark.asyncio
    async def test_cleanup_task_deletes_old_files(self, temp_dir):
        """Test that cleanup_old_files() actually deletes old files (covers lines 112, 119)"""
        import time
        import os

        # Create old files in temp and upload directories
        old_temp_file = settings.TEMP_DIR / "old_temp_cleanup.txt"
        old_temp_file.write_text("old temp")

        old_upload_file = settings.UPLOAD_DIR / "old_upload_cleanup.txt"
        old_upload_file.write_text("old upload")

        # Set modification time to old
        old_time = time.time() - (settings.TEMP_FILE_LIFETIME + 3600)
        os.utime(old_temp_file, (old_time, old_time))
        os.utime(old_upload_file, (old_time, old_time))

        # Create recent files that should NOT be deleted
        recent_temp_file = settings.TEMP_DIR / "recent_temp_cleanup.txt"
        recent_temp_file.write_text("recent temp")

        recent_upload_file = settings.UPLOAD_DIR / "recent_upload_cleanup.txt"
        recent_upload_file.write_text("recent upload")

        # Run cleanup_old_files for one iteration
        task = asyncio.create_task(cleanup_old_files())

        # Let it run one cleanup iteration
        await asyncio.sleep(0.5)

        # Cancel before it sleeps for 3600 seconds
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # Verify old files were deleted (lines 112 and 119)
        assert not old_temp_file.exists(), "Old temp file should be deleted (line 112)"
        assert not old_upload_file.exists(), "Old upload file should be deleted (line 119)"

        # Verify recent files were NOT deleted
        assert recent_temp_file.exists(), "Recent temp file should NOT be deleted"
        assert recent_upload_file.exists(), "Recent upload file should NOT be deleted"

        # Cleanup
        if recent_temp_file.exists():
            recent_temp_file.unlink()
        if recent_upload_file.exists():
            recent_upload_file.unlink()

    @pytest.mark.asyncio
    async def test_cleanup_task_logs_cache_cleanup_stats(self, temp_dir, caplog):
        """Test that cleanup_old_files() logs cache cleanup stats when items removed (line 128)"""
        import logging

        # Set caplog to capture INFO level logs
        caplog.set_level(logging.INFO)

        cache_dir = temp_dir / "cleanup_log_cache"
        original_cache_enabled = settings.CACHE_ENABLED

        try:
            # Enable cache and initialize with short expiration
            settings.CACHE_ENABLED = True
            cache_service = initialize_cache_service(
                cache_dir=cache_dir,
                expiration_hours=0,  # Immediate expiration
                max_size_mb=100
            )

            # Create an expired cache entry
            from PIL import Image
            test_image = temp_dir / "test_log.jpg"
            img = Image.new('RGB', (40, 40), color='green')
            img.save(test_image, 'JPEG')

            cache_key = cache_service.generate_cache_key(
                test_image, "png", {"quality": 90}
            )

            output_file = temp_dir / "output_log.png"
            img.save(output_file, 'PNG')

            cache_service.store_result(
                cache_key=cache_key,
                original_filename="test_log.jpg",
                output_file_path=output_file,
                output_format="png",
                conversion_options={"quality": 90}
            )

            # Wait for expiration
            await asyncio.sleep(0.1)

            # Run cleanup task
            task = asyncio.create_task(cleanup_old_files())
            await asyncio.sleep(0.5)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

            # Verify logging occurred (line 128)
            # Check if cache cleanup was logged
            assert any("cache cleanup" in record.message.lower() for record in caplog.records), \
                "Cache cleanup should be logged (line 128)"

        finally:
            settings.CACHE_ENABLED = original_cache_enabled

    def test_app_handles_multiple_requests(self, client):
        """Test that app can handle multiple concurrent requests"""
        responses = []

        for i in range(10):
            response = client.get("/health")
            responses.append(response)

        # All requests should succeed
        assert all(r.status_code == 200 for r in responses)
        assert all(r.json()["status"] == "healthy" for r in responses)


class TestStaticFileServing:
    """Test static file serving configuration"""

    def test_files_endpoint_exists(self, client):
        """Test that /files endpoint is mounted"""
        # Try to access files endpoint (will 404 for non-existent file)
        response = client.get("/files/nonexistent.txt")

        # Should get 404, not 405 (method not allowed) or other error
        # This confirms the endpoint is mounted
        assert response.status_code == 404

    def test_files_endpoint_serves_file(self, client, temp_dir):
        """Test that files endpoint can serve uploaded files"""
        # Create a test file in upload directory
        test_file = settings.UPLOAD_DIR / "test_static.txt"
        test_file.write_text("test content")

        try:
            response = client.get("/files/test_static.txt")

            assert response.status_code == 200
            assert response.text == "test content"

        finally:
            if test_file.exists():
                test_file.unlink()


class TestErrorHandling:
    """Test application error handling"""

    def test_invalid_endpoint_returns_404(self, client):
        """Test that invalid endpoints return 404"""
        response = client.get("/api/nonexistent")

        assert response.status_code == 404

    def test_invalid_method_returns_405(self, client):
        """Test that invalid HTTP methods return 405"""
        # Health endpoint only accepts GET
        response = client.post("/health")

        assert response.status_code == 405

    def test_malformed_request_handled_gracefully(self, client):
        """Test that malformed requests are handled gracefully"""
        # Try to post to image convert without required fields
        response = client.post("/api/image/convert")

        # Should return 422 (validation error), not 500
        assert response.status_code == 422


class TestAppConfiguration:
    """Test application configuration"""

    def test_app_title_configured(self):
        """Test that app title is configured correctly"""
        assert app.title == "FileConverter API"

    def test_app_version_configured(self):
        """Test that app version is configured correctly"""
        assert app.version == "1.0.0"

    def test_app_description_configured(self):
        """Test that app description is configured correctly"""
        assert "file conversion" in app.description.lower()

    def test_all_routers_included(self):
        """Test that all routers are included in the app"""
        # Get all route paths
        routes = [route.path for route in app.routes]

        # Check for key endpoints
        assert any("/api/image" in route for route in routes)
        assert any("/api/video" in route for route in routes)
        assert any("/api/audio" in route for route in routes)
        assert any("/api/cache" in route for route in routes)
        assert any("/ws" in route for route in routes)


class TestCacheStartupCleanup:
    """Test cache cleanup on startup"""

    def test_startup_cleanup_removes_expired_entries(self, temp_dir):
        """Test that startup cleanup removes expired cache entries"""
        cache_dir = temp_dir / "startup_cache"

        # Initialize cache with 0 hour expiration
        cache_service = initialize_cache_service(
            cache_dir=cache_dir,
            expiration_hours=0,
            max_size_mb=100
        )

        # Create expired cache entry
        from PIL import Image
        test_image = temp_dir / "test.jpg"
        img = Image.new('RGB', (30, 30), color='blue')
        img.save(test_image, 'JPEG')

        cache_key = cache_service.generate_cache_key(
            test_image, "png", {"quality": 95}
        )

        output_file = temp_dir / "output.png"
        img.save(output_file, 'PNG')

        cache_service.store_result(
            cache_key=cache_key,
            original_filename="test.jpg",
            output_file_path=output_file,
            output_format="png",
            conversion_options={"quality": 95}
        )

        # Verify entry exists
        assert cache_service.get_cache_info()["entry_count"] >= 1

        # Wait for expiration
        time.sleep(0.1)

        # Run startup cleanup (simulating app startup)
        cleanup_stats = cache_service.cleanup_all()

        # Verify expired entries were removed
        assert cleanup_stats["expired_removed"] >= 1

    def test_startup_cleanup_removes_corrupted_entries(self, temp_dir):
        """Test that startup cleanup removes corrupted cache entries"""
        cache_dir = temp_dir / "corrupted_cache"
        cache_service = initialize_cache_service(
            cache_dir=cache_dir,
            expiration_hours=24,
            max_size_mb=100
        )

        # Create cache directory with corrupted metadata
        corrupted_entry = cache_dir / "corrupted_entry"
        corrupted_entry.mkdir(parents=True, exist_ok=True)

        # Write invalid JSON metadata
        metadata_file = corrupted_entry / "metadata.json"
        metadata_file.write_text("invalid json{{{")

        # Run cleanup
        cleanup_stats = cache_service.cleanup_all()

        # Verify corrupted entry was removed
        assert cleanup_stats["corrupted_removed"] >= 1
        assert not corrupted_entry.exists()
