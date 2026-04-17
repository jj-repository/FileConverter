"""
Unit tests for app/utils/file_handler.py

Tests file upload handling, metadata extraction, and cleanup utilities.
"""

from unittest.mock import AsyncMock

import pytest
from app.utils.file_handler import cleanup_file, save_upload_file
from app.utils.subprocess_utils import parse_fps as _parse_fps_safe


class TestParseFpsSafe:
    """Test _parse_fps_safe function for parsing FPS values"""

    def test_parse_simple_fps(self):
        """Test parsing simple numeric FPS"""
        assert _parse_fps_safe("30") == 30.0
        assert _parse_fps_safe("60") == 60.0
        assert _parse_fps_safe("24") == 24.0

    def test_parse_fractional_fps(self):
        """Test parsing fractional FPS (e.g., NTSC)"""
        result = _parse_fps_safe("30000/1001")
        assert result == pytest.approx(29.97, rel=1e-3)

        result = _parse_fps_safe("24000/1001")
        assert result == pytest.approx(23.976, rel=1e-3)

    def test_parse_decimal_fps(self):
        """Test parsing decimal FPS"""
        assert _parse_fps_safe("29.97") == 29.97
        assert _parse_fps_safe("23.976") == 23.976  # Decimal values not rounded

    def test_parse_fps_with_whitespace(self):
        """Test parsing FPS with surrounding whitespace"""
        assert _parse_fps_safe("  30  ") == 30.0
        assert _parse_fps_safe(" 30000/1001 ") == pytest.approx(29.97, rel=1e-3)

    def test_parse_fps_zero_denominator(self):
        """Test handling division by zero"""
        assert _parse_fps_safe("30/0") == 0.0

    def test_parse_fps_invalid_format(self):
        """Test handling invalid FPS formats"""
        assert _parse_fps_safe("invalid") == 0.0
        assert _parse_fps_safe("30/60/90") == 0.0
        assert _parse_fps_safe("") == 0.0
        assert _parse_fps_safe("abc/def") == 0.0

    def test_parse_fps_none_value(self):
        """Test handling None/non-string returns 0.0"""
        assert _parse_fps_safe("n/a") == 0.0


class TestSaveUploadFile:
    """Test save_upload_file function for uploading files"""

    @pytest.mark.asyncio
    async def test_save_upload_file_success(self, temp_dir):
        """Test successful file upload"""
        mock_file = AsyncMock()
        mock_file.filename = "test.jpg"
        mock_file.read = AsyncMock(side_effect=[b"test image data", b""])

        saved_path = await save_upload_file(mock_file, temp_dir)

        assert saved_path.exists()
        assert saved_path.parent == temp_dir
        assert saved_path.suffix == ".jpg"
        assert saved_path.read_bytes() == b"test image data"

    @pytest.mark.asyncio
    async def test_save_upload_file_unique_names(self, temp_dir):
        """Test that uploaded files get unique names"""
        mock_file1 = AsyncMock()
        mock_file1.filename = "test.jpg"
        mock_file1.read = AsyncMock(side_effect=[b"data1", b""])

        mock_file2 = AsyncMock()
        mock_file2.filename = "test.jpg"
        mock_file2.read = AsyncMock(side_effect=[b"data2", b""])

        path1 = await save_upload_file(mock_file1, temp_dir)
        path2 = await save_upload_file(mock_file2, temp_dir)

        assert path1 != path2
        assert path1.exists()
        assert path2.exists()

    @pytest.mark.asyncio
    async def test_save_upload_file_preserves_extension(self, temp_dir):
        """Test that file extension is preserved"""
        extensions = [".jpg", ".png", ".pdf", ".mp4", ".txt"]

        for ext in extensions:
            mock_file = AsyncMock()
            mock_file.filename = f"test{ext}"
            mock_file.read = AsyncMock(side_effect=[b"data", b""])

            saved_path = await save_upload_file(mock_file, temp_dir)
            assert saved_path.suffix == ext


class TestCleanupFile:
    """Test cleanup_file function for deleting files"""

    def test_cleanup_existing_file(self, temp_dir):
        """Test deleting an existing file"""
        test_file = temp_dir / "to_delete.txt"
        test_file.write_text("temporary file")

        assert test_file.exists()

        cleanup_file(test_file)

        assert not test_file.exists()

    def test_cleanup_nonexistent_file(self, temp_dir):
        """Test cleanup handles non-existent file gracefully"""
        nonexistent = temp_dir / "does_not_exist.txt"

        # Should not raise an error
        cleanup_file(nonexistent)

    def test_cleanup_directory_ignored(self, temp_dir):
        """Test that directories are not deleted"""
        test_subdir = temp_dir / "subdir"
        test_subdir.mkdir()

        assert test_subdir.exists()

        cleanup_file(test_subdir)

        # Directory should still exist (only files are deleted)
        assert test_subdir.exists()

    def test_cleanup_file_permission_error(self, temp_dir):
        """Test handling permission errors during cleanup"""
        test_file = temp_dir / "readonly.txt"
        test_file.write_text("data")

        # Make file read-only on Unix systems
        import os

        os.chmod(test_file, 0o444)

        # cleanup_file should handle any errors gracefully and not raise
        try:
            cleanup_file(test_file)
        except Exception:
            pytest.fail("cleanup_file should not raise exceptions")

        # If file still exists, restore permissions for cleanup
        if test_file.exists():
            os.chmod(test_file, 0o644)
            test_file.unlink(missing_ok=True)
