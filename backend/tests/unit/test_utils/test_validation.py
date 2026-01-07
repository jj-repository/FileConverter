"""
Security-critical tests for app/utils/validation.py

These tests focus on path traversal prevention, file size validation,
extension validation, and MIME type validation.

COVERAGE GOAL: 95%+
"""

import pytest
from fastapi import HTTPException
from pathlib import Path
from unittest.mock import Mock, patch
import io
import sys

from app.utils.validation import (
    validate_file_size,
    validate_file_extension,
    validate_mime_type,
    get_file_type_from_format,
    validate_download_filename
)
from app.config import settings


# ============================================================================
# PATH TRAVERSAL PREVENTION TESTS (CRITICAL SECURITY)
# ============================================================================

class TestValidateDownloadFilename:
    """Test validate_download_filename() - Path traversal prevention"""

    @pytest.mark.security
    def test_valid_filename_allowed(self, temp_dir):
        """Test that valid filename passes validation"""
        # Create a valid file
        test_file = temp_dir / "valid_file.mp4"
        test_file.write_text("test content")

        # Validate
        result = validate_download_filename("valid_file.mp4", temp_dir)

        assert result == test_file.resolve()

    @pytest.mark.security
    def test_path_traversal_blocked_unix(self, temp_dir):
        """Test that ../../../etc/passwd is blocked"""
        with pytest.raises(HTTPException) as exc_info:
            validate_download_filename("../../../etc/passwd", temp_dir)

        assert exc_info.value.status_code == 400
        assert "Invalid filename" in exc_info.value.detail

    @pytest.mark.security
    def test_path_traversal_blocked_windows(self, temp_dir):
        """Test that ..\\..\\..\\windows\\system32 is blocked"""
        with pytest.raises(HTTPException) as exc_info:
            validate_download_filename("..\\..\\..\\windows\\system32\\config\\sam", temp_dir)

        assert exc_info.value.status_code == 400
        assert "Invalid filename" in exc_info.value.detail

    @pytest.mark.security
    def test_path_traversal_with_dot_dot(self, temp_dir):
        """Test that filenames containing '..' are blocked"""
        malicious_names = [
            "../secret.txt",
            "..\\secret.txt",
            "../../etc/passwd",
            "./../../../root/.ssh/id_rsa"
        ]

        for name in malicious_names:
            with pytest.raises(HTTPException) as exc_info:
                validate_download_filename(name, temp_dir)

            assert exc_info.value.status_code == 400

    @pytest.mark.security
    def test_null_byte_injection_blocked(self, temp_dir):
        """Test that file\x00.txt (null byte injection) is blocked"""
        with pytest.raises(HTTPException) as exc_info:
            validate_download_filename("file\x00.txt", temp_dir)

        assert exc_info.value.status_code == 400
        assert "Invalid filename" in exc_info.value.detail

    @pytest.mark.security
    def test_path_separator_blocked(self, temp_dir):
        """Test that filenames with path separators are blocked"""
        with pytest.raises(HTTPException) as exc_info:
            validate_download_filename("subdir/file.txt", temp_dir)

        assert exc_info.value.status_code == 400

        with pytest.raises(HTTPException) as exc_info:
            validate_download_filename("subdir\\file.txt", temp_dir)

        assert exc_info.value.status_code == 400

    @pytest.mark.security
    def test_empty_filename_blocked(self, temp_dir):
        """Test that empty filename is blocked"""
        with pytest.raises(HTTPException) as exc_info:
            validate_download_filename("", temp_dir)

        assert exc_info.value.status_code == 400

    @pytest.mark.security
    def test_symlink_escape_blocked(self, temp_dir):
        """Test that symlinks pointing outside base_dir are blocked"""
        # Create a file outside temp_dir
        import tempfile
        outside_dir = Path(tempfile.mkdtemp(prefix="outside_"))
        outside_file = outside_dir / "secret.txt"
        outside_file.write_text("secret content")

        # Create symlink in temp_dir pointing to outside file
        symlink = temp_dir / "symlink.txt"
        try:
            symlink.symlink_to(outside_file)

            # Try to access via symlink - should be blocked
            with pytest.raises(HTTPException) as exc_info:
                validate_download_filename("symlink.txt", temp_dir)

            # Should fail with access denied (path resolves outside base_dir)
            assert exc_info.value.status_code == 403
            assert "Access denied" in exc_info.value.detail

        finally:
            # Cleanup
            if symlink.exists():
                symlink.unlink()
            outside_file.unlink()
            outside_dir.rmdir()

    def test_nonexistent_file_blocked(self, temp_dir):
        """Test that non-existent file raises 404"""
        with pytest.raises(HTTPException) as exc_info:
            validate_download_filename("nonexistent.txt", temp_dir)

        assert exc_info.value.status_code == 404
        assert "File not found" in exc_info.value.detail

    def test_directory_blocked(self, temp_dir):
        """Test that directories are blocked (not files)"""
        # Create a subdirectory
        subdir = temp_dir / "subdir"
        subdir.mkdir()

        with pytest.raises(HTTPException) as exc_info:
            validate_download_filename("subdir", temp_dir)

        assert exc_info.value.status_code == 400
        assert "Not a file" in exc_info.value.detail

    def test_valid_filename_with_dots_allowed(self, temp_dir):
        """Test that filename with dots (not ..) is allowed"""
        test_file = temp_dir / "my.file.with.dots.txt"
        test_file.write_text("content")

        result = validate_download_filename("my.file.with.dots.txt", temp_dir)

        assert result == test_file.resolve()

    def test_case_sensitive_validation(self, temp_dir):
        """Test that validation is case-sensitive"""
        test_file = temp_dir / "TestFile.MP4"
        test_file.write_text("content")

        # Should work with exact case
        result = validate_download_filename("TestFile.MP4", temp_dir)
        assert result.name == "TestFile.MP4"

    @pytest.mark.security
    def test_resolve_path_error_handling(self, temp_dir):
        """Test that OSError/RuntimeError during path resolution is handled"""
        test_file = temp_dir / "testfile.txt"
        test_file.write_text("content")

        # Mock resolve() to raise OSError
        with patch('pathlib.Path.resolve', side_effect=OSError("Permission denied")):
            with pytest.raises(HTTPException) as exc_info:
                validate_download_filename("testfile.txt", temp_dir)

            assert exc_info.value.status_code == 400
            assert "Invalid file path" in exc_info.value.detail

    @pytest.mark.security
    def test_resolve_runtime_error_handling(self, temp_dir):
        """Test that RuntimeError during path resolution is handled"""
        test_file = temp_dir / "testfile.txt"
        test_file.write_text("content")

        # Mock resolve() to raise RuntimeError
        with patch('pathlib.Path.resolve', side_effect=RuntimeError("Symlink loop")):
            with pytest.raises(HTTPException) as exc_info:
                validate_download_filename("testfile.txt", temp_dir)

            assert exc_info.value.status_code == 400
            assert "Invalid file path" in exc_info.value.detail


# ============================================================================
# FILE SIZE VALIDATION TESTS (SECURITY)
# ============================================================================

class TestValidateFileSize:
    """Test validate_file_size() - File size limit enforcement"""

    @pytest.mark.security
    def test_image_within_limit(self):
        """Test that image under 100MB passes"""
        # Create mock upload file with size < limit
        mock_file = Mock()
        mock_file.file = io.BytesIO(b"x" * (50 * 1024 * 1024))  # 50MB
        mock_file.file.seek(0)

        # Should not raise exception
        validate_file_size(mock_file, "image")

    @pytest.mark.security
    def test_image_exceeds_limit(self):
        """Test that image over 100MB raises 413"""
        # Create mock file exceeding limit
        mock_file = Mock()
        mock_file.file = Mock()
        mock_file.file.tell.return_value = 105 * 1024 * 1024  # 105MB
        mock_file.file.seek = Mock()

        with pytest.raises(HTTPException) as exc_info:
            validate_file_size(mock_file, "image")

        assert exc_info.value.status_code == 413
        assert "Image file too large" in exc_info.value.detail
        assert "100" in exc_info.value.detail  # Should mention 100MB limit

    @pytest.mark.security
    def test_video_within_limit(self):
        """Test that video under 500MB passes"""
        mock_file = Mock()
        mock_file.file = Mock()
        mock_file.file.tell.return_value = 400 * 1024 * 1024  # 400MB
        mock_file.file.seek = Mock()

        validate_file_size(mock_file, "video")

    @pytest.mark.security
    def test_video_exceeds_limit(self):
        """Test that video over 500MB raises 413"""
        mock_file = Mock()
        mock_file.file = Mock()
        mock_file.file.tell.return_value = 550 * 1024 * 1024  # 550MB
        mock_file.file.seek = Mock()

        with pytest.raises(HTTPException) as exc_info:
            validate_file_size(mock_file, "video")

        assert exc_info.value.status_code == 413
        assert "Video file too large" in exc_info.value.detail

    @pytest.mark.security
    def test_audio_exceeds_limit(self):
        """Test that audio over 100MB raises 413"""
        mock_file = Mock()
        mock_file.file = Mock()
        mock_file.file.tell.return_value = 105 * 1024 * 1024  # 105MB
        mock_file.file.seek = Mock()

        with pytest.raises(HTTPException) as exc_info:
            validate_file_size(mock_file, "audio")

        assert exc_info.value.status_code == 413
        assert "Audio file too large" in exc_info.value.detail

    @pytest.mark.security
    def test_document_exceeds_limit(self):
        """Test that document over 50MB raises 413"""
        mock_file = Mock()
        mock_file.file = Mock()
        mock_file.file.tell.return_value = 55 * 1024 * 1024  # 55MB
        mock_file.file.seek = Mock()

        with pytest.raises(HTTPException) as exc_info:
            validate_file_size(mock_file, "document")

        assert exc_info.value.status_code == 413
        assert "Document file too large" in exc_info.value.detail

    @pytest.mark.security
    def test_archive_exceeds_limit(self):
        """Test that archive over 500MB raises 413"""
        mock_file = Mock()
        mock_file.file = Mock()
        mock_file.file.tell.return_value = 550 * 1024 * 1024  # 550MB
        mock_file.file.seek = Mock()

        with pytest.raises(HTTPException) as exc_info:
            validate_file_size(mock_file, "archive")

        assert exc_info.value.status_code == 413
        assert "Archive file too large" in exc_info.value.detail

    @pytest.mark.security
    def test_subtitle_exceeds_limit(self):
        """Test that subtitle over 10MB raises 413"""
        mock_file = Mock()
        mock_file.file = Mock()
        mock_file.file.tell.return_value = 12 * 1024 * 1024  # 12MB
        mock_file.file.seek = Mock()

        with pytest.raises(HTTPException) as exc_info:
            validate_file_size(mock_file, "subtitle")

        assert exc_info.value.status_code == 413
        assert "Subtitle file too large" in exc_info.value.detail

    @pytest.mark.security
    def test_ebook_exceeds_limit(self):
        """Test that ebook over 50MB raises 413"""
        mock_file = Mock()
        mock_file.file = Mock()
        mock_file.file.tell.return_value = 55 * 1024 * 1024  # 55MB
        mock_file.file.seek = Mock()

        with pytest.raises(HTTPException) as exc_info:
            validate_file_size(mock_file, "ebook")

        assert exc_info.value.status_code == 413
        assert "eBook file too large" in exc_info.value.detail

    @pytest.mark.security
    def test_font_exceeds_limit(self):
        """Test that font over 20MB raises 413"""
        mock_file = Mock()
        mock_file.file = Mock()
        mock_file.file.tell.return_value = 25 * 1024 * 1024  # 25MB
        mock_file.file.seek = Mock()

        with pytest.raises(HTTPException) as exc_info:
            validate_file_size(mock_file, "font")

        assert exc_info.value.status_code == 413
        assert "Font file too large" in exc_info.value.detail

    @pytest.mark.security
    def test_spreadsheet_exceeds_limit(self):
        """Test that spreadsheet over 100MB raises 413"""
        mock_file = Mock()
        mock_file.file = Mock()
        mock_file.file.tell.return_value = 110 * 1024 * 1024  # 110MB
        mock_file.file.seek = Mock()

        with pytest.raises(HTTPException) as exc_info:
            validate_file_size(mock_file, "spreadsheet")

        assert exc_info.value.status_code == 413
        assert "Spreadsheet file too large" in exc_info.value.detail

    @pytest.mark.security
    def test_unknown_type_exceeds_general_limit(self):
        """Test that unknown file type exceeds MAX_UPLOAD_SIZE limit"""
        mock_file = Mock()
        mock_file.file = Mock()
        # Set size larger than MAX_UPLOAD_SIZE (which is 1GB)
        mock_file.file.tell.return_value = 1200 * 1024 * 1024  # 1.2GB
        mock_file.file.seek = Mock()

        with pytest.raises(HTTPException) as exc_info:
            validate_file_size(mock_file, "unknown_type")

        assert exc_info.value.status_code == 413
        assert "File too large" in exc_info.value.detail

    def test_file_at_exact_limit(self):
        """Test that file at exact limit is allowed"""
        mock_file = Mock()
        mock_file.file = Mock()
        mock_file.file.tell.return_value = settings.IMAGE_MAX_SIZE  # Exactly 100MB
        mock_file.file.seek = Mock()

        # Should not raise
        validate_file_size(mock_file, "image")

    def test_file_pointer_reset_after_validation(self):
        """Test that file pointer is reset to start after size check"""
        mock_file = Mock()
        mock_file.file = io.BytesIO(b"test content")

        validate_file_size(mock_file, "image")

        # File pointer should be at start
        assert mock_file.file.tell() == 0


# ============================================================================
# FILE EXTENSION VALIDATION TESTS
# ============================================================================

class TestValidateFileExtension:
    """Test validate_file_extension() - Extension validation"""

    def test_valid_extension_accepted(self):
        """Test that .jpg is accepted for images"""
        allowed_formats = {"jpg", "png", "gif"}

        result = validate_file_extension("test.jpg", allowed_formats)

        assert result == "jpg"

    @pytest.mark.security
    def test_invalid_extension_rejected(self):
        """Test that .exe raises 400"""
        allowed_formats = {"jpg", "png"}

        with pytest.raises(HTTPException) as exc_info:
            validate_file_extension("malware.exe", allowed_formats)

        assert exc_info.value.status_code == 400
        assert "Unsupported file format" in exc_info.value.detail

    def test_case_insensitive(self):
        """Test that .JPG and .jpg both work"""
        allowed_formats = {"jpg"}

        # Uppercase
        result1 = validate_file_extension("photo.JPG", allowed_formats)
        assert result1 == "jpg"

        # Lowercase
        result2 = validate_file_extension("photo.jpg", allowed_formats)
        assert result2 == "jpg"

        # Mixed case
        result3 = validate_file_extension("photo.JpG", allowed_formats)
        assert result3 == "jpg"

    def test_compound_extension_tar_gz(self):
        """Test that .tar.gz works for archives"""
        allowed_formats = {"tar.gz", "zip"}

        result = validate_file_extension("archive.tar.gz", allowed_formats)

        assert result == "tar.gz"

    def test_compound_extension_tar_bz2(self):
        """Test that .tar.bz2 works"""
        allowed_formats = {"tar.bz2", "zip"}

        result = validate_file_extension("archive.tar.bz2", allowed_formats)

        assert result == "tar.bz2"

    def test_compound_extension_tgz(self):
        """Test that .tgz works"""
        allowed_formats = {"tgz", "zip"}

        result = validate_file_extension("archive.tgz", allowed_formats)

        assert result == "tgz"

    def test_compound_extension_tbz2(self):
        """Test that .tbz2 works"""
        allowed_formats = {"tbz2", "zip"}

        result = validate_file_extension("archive.tbz2", allowed_formats)

        assert result == "tbz2"

    def test_multiple_dots_in_filename(self):
        """Test filename with multiple dots: my.file.name.jpg"""
        allowed_formats = {"jpg"}

        result = validate_file_extension("my.file.name.jpg", allowed_formats)

        assert result == "jpg"

    def test_no_extension(self):
        """Test filename without extension raises error"""
        allowed_formats = {"jpg"}

        with pytest.raises(HTTPException) as exc_info:
            validate_file_extension("noextension", allowed_formats)

        assert exc_info.value.status_code == 400

    def test_error_message_includes_allowed_formats(self):
        """Test that error message shows allowed formats"""
        allowed_formats = {"jpg", "png", "gif"}

        with pytest.raises(HTTPException) as exc_info:
            validate_file_extension("file.bmp", allowed_formats)

        assert "jpg" in exc_info.value.detail
        assert "png" in exc_info.value.detail
        assert "gif" in exc_info.value.detail


# ============================================================================
# MIME TYPE VALIDATION TESTS
# ============================================================================

class TestValidateMimeType:
    """Test validate_mime_type() - MIME type validation

    NOTE: MIME validation behavior changed for security:
    - In DEBUG mode: Validation is skipped silently if python-magic unavailable
    - In production (DEBUG=False): Raises HTTP 503 if python-magic unavailable
    - In production: Raises HTTP 400 on validation errors
    """

    def test_magic_availability_check(self):
        """Test that MAGIC_AVAILABLE is properly set based on magic import"""
        # Import the module to check if MAGIC_AVAILABLE is set correctly
        from app.utils import validation

        # MAGIC_AVAILABLE should be True if magic is installed, False otherwise
        try:
            import magic
            assert validation.MAGIC_AVAILABLE == True
        except ImportError:
            assert validation.MAGIC_AVAILABLE == False

    @pytest.mark.security
    def test_valid_mime_accepted(self, sample_image_jpg):
        """Test that valid MIME type is accepted when magic is available"""
        import app.utils.validation as validation_module

        expected_types = {"image/jpeg", "image/jpg"}

        # Create a mock magic module
        mock_magic_module = Mock()
        mock_mime_instance = Mock()
        mock_mime_instance.from_file.return_value = "image/jpeg"
        mock_magic_module.Magic.return_value = mock_mime_instance

        with patch.object(validation_module, 'MAGIC_AVAILABLE', True), \
             patch.object(validation_module, 'magic', mock_magic_module, create=True):
            validate_mime_type(sample_image_jpg, expected_types)

    @pytest.mark.security
    def test_mime_validation_without_magic_always_raises_503(self, sample_image_jpg):
        """Test that validation ALWAYS raises 503 if python-magic unavailable (security: no DEBUG bypass)"""
        # SECURITY: MIME validation is always enforced, regardless of DEBUG mode
        with patch('app.utils.validation.MAGIC_AVAILABLE', False):
            with pytest.raises(HTTPException) as exc_info:
                validate_mime_type(sample_image_jpg, {"video/mp4"})

            assert exc_info.value.status_code == 503
            assert "validation unavailable" in exc_info.value.detail.lower()

    @pytest.mark.security
    def test_mime_validation_without_magic_production_mode(self, sample_image_jpg):
        """Test that validation raises 503 if python-magic unavailable (production mode)"""
        with patch('app.utils.validation.MAGIC_AVAILABLE', False), \
             patch('app.utils.validation.settings.DEBUG', False):
            # In production mode, should raise 503 (service unavailable)
            with pytest.raises(HTTPException) as exc_info:
                validate_mime_type(sample_image_jpg, {"video/mp4"})

            assert exc_info.value.status_code == 503
            assert "validation unavailable" in exc_info.value.detail.lower()

    @pytest.mark.security
    @pytest.mark.skipif(not hasattr(__import__('app.utils.validation', fromlist=['MAGIC_AVAILABLE']), 'magic'),
                        reason="python-magic not installed")
    def test_mime_mismatch_blocked(self, sample_image_jpg):
        """Test that MIME type mismatch is detected (if python-magic available)"""
        try:
            import magic
        except ImportError:
            pytest.skip("python-magic not installed")

        with patch('app.utils.validation.MAGIC_AVAILABLE', True), \
             patch('magic.Magic') as mock_magic:

            # Mock magic to return image/jpeg
            mock_mime_instance = Mock()
            mock_mime_instance.from_file.return_value = "image/jpeg"
            mock_magic.return_value = mock_mime_instance

            # Expect video but get image - should fail
            with pytest.raises(HTTPException) as exc_info:
                validate_mime_type(sample_image_jpg, {"video/mp4"})

            assert exc_info.value.status_code == 400
            assert "Invalid file type" in exc_info.value.detail

    @pytest.mark.skipif(not hasattr(__import__('app.utils.validation', fromlist=['MAGIC_AVAILABLE']), 'magic'),
                        reason="python-magic not installed")
    def test_mime_validation_with_partial_match(self, sample_image_jpg):
        """Test that partial MIME type matching works (e.g., 'image/')"""
        try:
            import magic
        except ImportError:
            pytest.skip("python-magic not installed")

        with patch('app.utils.validation.MAGIC_AVAILABLE', True), \
             patch('magic.Magic') as mock_magic:

            mock_mime_instance = Mock()
            mock_mime_instance.from_file.return_value = "image/jpeg"
            mock_magic.return_value = mock_mime_instance

            # Should match with "image" prefix
            validate_mime_type(sample_image_jpg, {"image"})

    @pytest.mark.security
    def test_mime_validation_exception_always_raises_400(self, sample_image_jpg):
        """Test that exceptions in python-magic always raise 400 (security: fail closed)"""
        import app.utils.validation as validation_module

        # Create a mock magic module
        mock_magic_module = Mock()
        mock_magic_class = Mock()
        mock_magic_class.side_effect = Exception("magic library error")
        mock_magic_module.Magic = mock_magic_class

        # SECURITY: Exceptions during MIME validation always fail closed (return 400)
        with patch.object(validation_module, 'MAGIC_AVAILABLE', True), \
             patch.object(validation_module, 'magic', mock_magic_module, create=True):

            with pytest.raises(HTTPException) as exc_info:
                validate_mime_type(sample_image_jpg, {"video/mp4"})

            assert exc_info.value.status_code == 400
            assert "validation failed" in exc_info.value.detail.lower()

    @pytest.mark.security
    def test_mime_validation_exception_production_mode(self, sample_image_jpg):
        """Test that exceptions in python-magic raise 400 in production mode"""
        import app.utils.validation as validation_module

        # Create a mock magic module
        mock_magic_module = Mock()
        mock_magic_class = Mock()
        mock_magic_class.side_effect = Exception("magic library error")
        mock_magic_module.Magic = mock_magic_class

        with patch.object(validation_module, 'MAGIC_AVAILABLE', True), \
             patch.object(validation_module, 'magic', mock_magic_module, create=True):

            # Should raise 400 on validation errors
            with pytest.raises(HTTPException) as exc_info:
                validate_mime_type(sample_image_jpg, {"video/mp4"})

            assert exc_info.value.status_code == 400
            assert "validation failed" in exc_info.value.detail.lower()

    @pytest.mark.security
    def test_mime_validation_from_file_exception_always_raises_400(self, sample_image_jpg):
        """Test that from_file() exceptions always raise 400 (security: fail closed)"""
        import app.utils.validation as validation_module

        # Create a mock magic module
        mock_magic_module = Mock()
        mock_mime_instance = Mock()
        # Make from_file raise an exception
        mock_mime_instance.from_file.side_effect = Exception("Cannot read file")
        mock_magic_module.Magic.return_value = mock_mime_instance

        # SECURITY: from_file() exceptions always fail closed (return 400)
        with patch.object(validation_module, 'MAGIC_AVAILABLE', True), \
             patch.object(validation_module, 'magic', mock_magic_module, create=True):

            with pytest.raises(HTTPException) as exc_info:
                validate_mime_type(sample_image_jpg, {"video/mp4"})

            assert exc_info.value.status_code == 400
            assert "validation failed" in exc_info.value.detail.lower()


# ============================================================================
# FILE TYPE CATEGORIZATION TESTS
# ============================================================================

class TestGetFileTypeFromFormat:
    """Test get_file_type_from_format() - File type categorization"""

    def test_image_format_detection(self):
        """Test that jpg is detected as image"""
        result = get_file_type_from_format("jpg")
        assert result == "image"

    def test_video_format_detection(self):
        """Test that mp4 is detected as video"""
        result = get_file_type_from_format("mp4")
        assert result == "video"

    def test_audio_format_detection(self):
        """Test that mp3 is detected as audio"""
        result = get_file_type_from_format("mp3")
        assert result == "audio"

    def test_document_format_detection(self):
        """Test that pdf is detected as document"""
        result = get_file_type_from_format("pdf")
        assert result == "document"

    def test_unknown_format_raises_error(self):
        """Test that unknown format raises 400"""
        with pytest.raises(HTTPException) as exc_info:
            get_file_type_from_format("unknown")

        assert exc_info.value.status_code == 400
        assert "Unknown file format" in exc_info.value.detail

    def test_all_image_formats(self):
        """Test all supported image formats"""
        for fmt in settings.IMAGE_FORMATS:
            result = get_file_type_from_format(fmt)
            assert result == "image"

    def test_all_video_formats(self):
        """Test all supported video formats"""
        for fmt in settings.VIDEO_FORMATS:
            result = get_file_type_from_format(fmt)
            assert result == "video"

    def test_all_audio_formats(self):
        """Test all supported audio formats"""
        for fmt in settings.AUDIO_FORMATS:
            result = get_file_type_from_format(fmt)
            assert result == "audio"

    def test_all_document_formats(self):
        """Test all supported document formats"""
        for fmt in settings.DOCUMENT_FORMATS:
            result = get_file_type_from_format(fmt)
            assert result == "document"


# ============================================================================
# ADDITIONAL COVERAGE TESTS
# ============================================================================

class TestMagicImportSuccess:
    """Test magic import success to cover line 8"""

    def test_magic_import_available(self):
        """Test that MAGIC_AVAILABLE is set to True when magic import succeeds (line 8)"""
        import sys
        from unittest.mock import MagicMock

        # Create a mock magic module
        mock_magic = MagicMock()

        # Inject mock magic into sys.modules
        with patch.dict(sys.modules, {'magic': mock_magic}):
            # Force module reload to trigger import
            import importlib
            import app.utils.validation
            importlib.reload(app.utils.validation)

            # Verify MAGIC_AVAILABLE is True
            assert app.utils.validation.MAGIC_AVAILABLE is True

            # Clean up - reload again to restore original state
            importlib.reload(app.utils.validation)


class TestMimeTypeMismatchWithMagic:
    """Test MIME type mismatch detection when magic is available"""

    @pytest.mark.security
    def test_mime_mismatch_with_forced_magic(self, sample_image_jpg):
        """Test MIME type mismatch detection - should raise HTTP 400

        When magic is available and detects a MIME type mismatch,
        the function should raise an HTTPException with status 400.
        """
        from unittest.mock import MagicMock

        # Skip test if magic is not available (can't test the feature)
        from app.utils import validation
        if not validation.MAGIC_AVAILABLE:
            pytest.skip("python-magic not available, can't test MIME validation")

        # Create a mock for the magic.Magic class to return specific MIME type
        mock_mime_instance = MagicMock()
        mock_mime_instance.from_file.return_value = "image/jpeg"

        # Patch the magic.Magic class in the validation module
        with patch('app.utils.validation.magic.Magic', return_value=mock_mime_instance):
            # MIME mismatch should raise 400
            with pytest.raises(HTTPException) as exc_info:
                validate_mime_type(sample_image_jpg, {"video/mp4", "video/mpeg"})

            assert exc_info.value.status_code == 400
            assert "Invalid file type" in exc_info.value.detail


class TestValidateDownloadFilenameDotDot:
    """Test validate_download_filename with .. in filename"""

    def test_dot_dot_in_middle_of_filename(self, temp_dir):
        """Test that .. in middle of filename is blocked (line 159)"""
        base_dir = temp_dir

        # Create a valid file
        test_file = base_dir / "test.txt"
        test_file.write_text("test content")

        # Try filename with .. in the middle
        with pytest.raises(HTTPException) as exc_info:
            validate_download_filename("file..name.txt", base_dir)

        assert exc_info.value.status_code == 400
        assert "Invalid filename" in exc_info.value.detail

    def test_dot_dot_as_whole_component(self, temp_dir):
        """Test that .. as component is blocked"""
        base_dir = temp_dir

        with pytest.raises(HTTPException) as exc_info:
            validate_download_filename("..", base_dir)

        assert exc_info.value.status_code == 400
        assert "Invalid filename" in exc_info.value.detail
