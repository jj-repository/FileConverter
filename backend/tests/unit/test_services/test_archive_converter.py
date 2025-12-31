"""
Tests for app/services/archive_converter.py

COVERAGE GOAL: 85%+
Tests archive creation/extraction, format conversion, compression levels,
path traversal prevention, and progress tracking via WebSocket
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
import zipfile
import tarfile
import gzip
import shutil
from io import BytesIO

from app.services.archive_converter import ArchiveConverter
from app.config import settings


# ============================================================================
# BASIC FUNCTIONALITY TESTS
# ============================================================================

class TestArchiveConverterBasics:
    """Test basic ArchiveConverter functionality"""

    def test_initialization(self):
        """Test ArchiveConverter initializes correctly"""
        converter = ArchiveConverter()

        assert converter.supported_formats is not None
        assert "input" in converter.supported_formats
        assert "output" in converter.supported_formats
        assert "zip" in converter.supported_formats["input"]
        assert "tar" in converter.supported_formats["output"]
        assert "tar.gz" in converter.supported_formats["output"]

    def test_initialization_with_websocket_manager(self):
        """Test ArchiveConverter can be initialized with custom WebSocket manager"""
        mock_ws_manager = Mock()
        converter = ArchiveConverter(websocket_manager=mock_ws_manager)

        assert converter.websocket_manager == mock_ws_manager

    @pytest.mark.asyncio
    async def test_get_supported_formats(self):
        """Test getting supported archive formats"""
        converter = ArchiveConverter()

        formats = await converter.get_supported_formats()

        assert "input" in formats
        assert "output" in formats
        assert isinstance(formats["input"], list)
        assert isinstance(formats["output"], list)
        # Check common archive formats
        assert "zip" in formats["output"]
        assert "tar" in formats["output"]
        assert "tar.gz" in formats["output"]
        assert "7z" in formats["output"]


# ============================================================================
# FORMAT NORMALIZATION TESTS
# ============================================================================

class TestFormatNormalization:
    """Test archive format normalization"""

    def test_normalize_format_tgz_to_tar_gz(self):
        """Test normalizing tgz to tar.gz"""
        converter = ArchiveConverter()

        result = converter._normalize_format("tgz")

        assert result == "tar.gz"

    def test_normalize_format_tbz2_to_tar_bz2(self):
        """Test normalizing tbz2 to tar.bz2"""
        converter = ArchiveConverter()

        result = converter._normalize_format("tbz2")

        assert result == "tar.bz2"

    def test_normalize_format_lowercase(self):
        """Test format is converted to lowercase"""
        converter = ArchiveConverter()

        result = converter._normalize_format("ZIP")

        assert result == "zip"

    def test_normalize_format_unchanged(self):
        """Test format that doesn't need normalization remains unchanged"""
        converter = ArchiveConverter()

        result = converter._normalize_format("tar")

        assert result == "tar"


# ============================================================================
# COMPRESSION MODE TESTS
# ============================================================================

class TestCompressionMode:
    """Test tar compression mode selection"""

    def test_get_compression_mode_tar_gz(self):
        """Test getting compression mode for tar.gz"""
        converter = ArchiveConverter()

        mode = converter._get_compression_mode("tar.gz")

        assert mode == "w:gz"

    def test_get_compression_mode_tgz_alias(self):
        """Test getting compression mode for tgz (alias)"""
        converter = ArchiveConverter()

        mode = converter._get_compression_mode("tgz")

        assert mode == "w:gz"

    def test_get_compression_mode_tar_bz2(self):
        """Test getting compression mode for tar.bz2"""
        converter = ArchiveConverter()

        mode = converter._get_compression_mode("tar.bz2")

        assert mode == "w:bz2"

    def test_get_compression_mode_tar_uncompressed(self):
        """Test getting compression mode for plain tar"""
        converter = ArchiveConverter()

        mode = converter._get_compression_mode("tar")

        assert mode == "w"

    def test_get_compression_mode_unknown_defaults_to_uncompressed(self):
        """Test unknown format defaults to uncompressed"""
        converter = ArchiveConverter()

        mode = converter._get_compression_mode("unknown")

        assert mode == "w"


# ============================================================================
# FORMAT DETECTION TESTS
# ============================================================================

class TestFormatDetection:
    """Test archive format detection"""

    def test_detect_format_zip(self, temp_dir):
        """Test ZIP format detection"""
        converter = ArchiveConverter()
        test_file = temp_dir / "test.zip"
        test_file.write_bytes(b"PK\x03\x04")  # ZIP header

        result = converter._detect_format(test_file)

        assert result == "zip"

    def test_detect_format_tar_gz(self, temp_dir):
        """Test TAR.GZ format detection"""
        converter = ArchiveConverter()
        test_file = temp_dir / "test.tar.gz"
        test_file.write_bytes(b"dummy")

        result = converter._detect_format(test_file)

        assert result == "tar.gz"

    def test_detect_format_tgz_alias(self, temp_dir):
        """Test TGZ alias detection"""
        converter = ArchiveConverter()
        test_file = temp_dir / "test.tgz"
        test_file.write_bytes(b"dummy")

        result = converter._detect_format(test_file)

        assert result == "tar.gz"

    def test_detect_format_tar_bz2(self, temp_dir):
        """Test TAR.BZ2 format detection"""
        converter = ArchiveConverter()
        test_file = temp_dir / "test.tar.bz2"
        test_file.write_bytes(b"dummy")

        result = converter._detect_format(test_file)

        assert result == "tar.bz2"

    def test_detect_format_tar(self, temp_dir):
        """Test TAR format detection"""
        converter = ArchiveConverter()
        test_file = temp_dir / "test.tar"
        test_file.write_bytes(b"dummy")

        result = converter._detect_format(test_file)

        assert result == "tar"

    def test_detect_format_7z(self, temp_dir):
        """Test 7Z format detection"""
        converter = ArchiveConverter()
        test_file = temp_dir / "test.7z"
        test_file.write_bytes(b"dummy")

        result = converter._detect_format(test_file)

        assert result == "7z"

    def test_detect_format_gz(self, temp_dir):
        """Test GZ format detection"""
        converter = ArchiveConverter()
        test_file = temp_dir / "test.gz"
        test_file.write_bytes(b"dummy")

        result = converter._detect_format(test_file)

        assert result == "gz"

    def test_detect_format_unknown_raises_error(self, temp_dir):
        """Test unknown format raises ValueError"""
        converter = ArchiveConverter()
        test_file = temp_dir / "test.unknown"
        test_file.write_bytes(b"dummy")

        with pytest.raises(ValueError, match="Unknown archive format"):
            converter._detect_format(test_file)


# ============================================================================
# ARCHIVE EXTRACTION TESTS
# ============================================================================

class TestArchiveExtraction:
    """Test archive extraction functionality"""

    @pytest.mark.asyncio
    async def test_extract_zip_success(self, temp_dir):
        """Test successful ZIP extraction"""
        converter = ArchiveConverter()

        # Create a test ZIP file
        archive_path = temp_dir / "test.zip"
        extract_path = temp_dir / "extracted"
        extract_path.mkdir()

        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.writestr("file1.txt", "content1")
            zf.writestr("file2.txt", "content2")

        await converter._extract_archive(archive_path, extract_path, "zip")

        assert (extract_path / "file1.txt").exists()
        assert (extract_path / "file2.txt").exists()
        assert (extract_path / "file1.txt").read_text() == "content1"

    @pytest.mark.asyncio
    async def test_extract_tar_gz_success(self, temp_dir):
        """Test successful TAR.GZ extraction"""
        converter = ArchiveConverter()

        # Create a test TAR.GZ file
        archive_path = temp_dir / "test.tar.gz"
        extract_path = temp_dir / "extracted"
        extract_path.mkdir()

        with tarfile.open(archive_path, "w:gz") as tf:
            file1_path = temp_dir / "file1.txt"
            file1_path.write_text("content1")
            tf.add(file1_path, arcname="file1.txt")

        await converter._extract_archive(archive_path, extract_path, "tar.gz")

        assert (extract_path / "file1.txt").exists()

    @pytest.mark.asyncio
    async def test_extract_tar_uncompressed(self, temp_dir):
        """Test TAR extraction (uncompressed)"""
        converter = ArchiveConverter()

        # Create a test TAR file
        archive_path = temp_dir / "test.tar"
        extract_path = temp_dir / "extracted"
        extract_path.mkdir()

        with tarfile.open(archive_path, "w") as tf:
            file1_path = temp_dir / "file1.txt"
            file1_path.write_text("content1")
            tf.add(file1_path, arcname="file1.txt")

        await converter._extract_archive(archive_path, extract_path, "tar")

        assert (extract_path / "file1.txt").exists()

    @pytest.mark.asyncio
    async def test_extract_tar_bz2(self, temp_dir):
        """Test TAR.BZ2 extraction"""
        converter = ArchiveConverter()

        # Create a test TAR.BZ2 file
        archive_path = temp_dir / "test.tar.bz2"
        extract_path = temp_dir / "extracted"
        extract_path.mkdir()

        with tarfile.open(archive_path, "w:bz2") as tf:
            file1_path = temp_dir / "file1.txt"
            file1_path.write_text("content1")
            tf.add(file1_path, arcname="file1.txt")

        await converter._extract_archive(archive_path, extract_path, "tar.bz2")

        assert (extract_path / "file1.txt").exists()

    @pytest.mark.asyncio
    async def test_extract_gz_single_file(self, temp_dir):
        """Test GZ extraction (single file)"""
        converter = ArchiveConverter()

        # Create a test GZ file
        archive_path = temp_dir / "file.txt.gz"
        extract_path = temp_dir / "extracted"
        extract_path.mkdir()

        with gzip.open(archive_path, "wb") as f:
            f.write(b"file content")

        await converter._extract_archive(archive_path, extract_path, "gz")

        assert (extract_path / "file.txt").exists()
        assert (extract_path / "file.txt").read_bytes() == b"file content"

    @pytest.mark.asyncio
    async def test_extract_path_traversal_prevention_tar(self, temp_dir):
        """Test TAR extraction prevents path traversal attacks"""
        converter = ArchiveConverter()

        # Create a TAR with malicious path traversal
        archive_path = temp_dir / "test.tar"
        extract_path = temp_dir / "extracted"
        extract_path.mkdir()

        with tarfile.open(archive_path, "w") as tf:
            # Add a member with path traversal
            tarinfo = tarfile.TarInfo(name="../../etc/passwd")
            tarinfo.size = 0
            tf.addfile(tarinfo)

        with pytest.raises(ValueError, match="Unsafe archive member"):
            await converter._extract_archive(archive_path, extract_path, "tar")

    @pytest.mark.asyncio
    async def test_extract_path_traversal_absolute_path_tar(self, temp_dir):
        """Test TAR extraction prevents absolute path extraction"""
        converter = ArchiveConverter()

        # Create a TAR with absolute path
        archive_path = temp_dir / "test.tar"
        extract_path = temp_dir / "extracted"
        extract_path.mkdir()

        with tarfile.open(archive_path, "w") as tf:
            # Add a member with absolute path
            tarinfo = tarfile.TarInfo(name="/etc/passwd")
            tarinfo.size = 0
            tf.addfile(tarinfo)

        with pytest.raises(ValueError, match="Unsafe archive member"):
            await converter._extract_archive(archive_path, extract_path, "tar")

    @pytest.mark.asyncio
    async def test_extract_unsupported_format_raises_error(self, temp_dir):
        """Test extraction with unsupported format raises ValueError"""
        converter = ArchiveConverter()

        archive_path = temp_dir / "test.xyz"
        extract_path = temp_dir / "extracted"
        extract_path.mkdir()
        archive_path.write_bytes(b"dummy")

        with pytest.raises(ValueError, match="Unsupported format for extraction"):
            await converter._extract_archive(archive_path, extract_path, "xyz")

    @pytest.mark.asyncio
    async def test_extract_corrupted_zip_raises_error(self, temp_dir):
        """Test extraction of corrupted ZIP raises error"""
        converter = ArchiveConverter()

        # Create a corrupted ZIP file
        archive_path = temp_dir / "corrupted.zip"
        extract_path = temp_dir / "extracted"
        extract_path.mkdir()
        archive_path.write_bytes(b"PK\x03\x04CORRUPTED_DATA")

        with pytest.raises(Exception):
            await converter._extract_archive(archive_path, extract_path, "zip")

    @pytest.mark.asyncio
    async def test_extract_7z_available(self, temp_dir):
        """Test 7Z extraction when py7zr is available"""
        converter = ArchiveConverter()

        archive_path = temp_dir / "test.7z"
        extract_path = temp_dir / "extracted"
        extract_path.mkdir()

        with patch('app.services.archive_converter.py7zr') as mock_7z:
            mock_archive = MagicMock()
            mock_7z.SevenZipFile.return_value.__enter__.return_value = mock_archive

            await converter._extract_archive(archive_path, extract_path, "7z")

            mock_7z.SevenZipFile.assert_called_once()
            mock_archive.extractall.assert_called_once_with(path=extract_path)

    @pytest.mark.asyncio
    async def test_extract_7z_unavailable_raises_error(self, temp_dir):
        """Test 7Z extraction fails gracefully when py7zr is not available"""
        converter = ArchiveConverter()

        archive_path = temp_dir / "test.7z"
        extract_path = temp_dir / "extracted"
        extract_path.mkdir()

        with patch('app.services.archive_converter.SEVENZ_AVAILABLE', False):
            with pytest.raises(ValueError, match="7z support not available"):
                await converter._extract_archive(archive_path, extract_path, "7z")


# ============================================================================
# ARCHIVE CREATION TESTS
# ============================================================================

class TestArchiveCreation:
    """Test archive creation functionality"""

    @pytest.mark.asyncio
    async def test_create_zip_archive_from_multiple_files(self, temp_dir):
        """Test creating ZIP archive from multiple files"""
        converter = ArchiveConverter()

        # Create source files
        source_dir = temp_dir / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("content1")
        (source_dir / "file2.txt").write_text("content2")

        output_path = temp_dir / "archive.zip"

        await converter._create_archive(source_dir, output_path, "zip", 6)

        assert output_path.exists()
        with zipfile.ZipFile(output_path, 'r') as zf:
            assert "file1.txt" in zf.namelist()
            assert "file2.txt" in zf.namelist()

    @pytest.mark.asyncio
    async def test_create_tar_archive_from_multiple_files(self, temp_dir):
        """Test creating TAR archive from multiple files"""
        converter = ArchiveConverter()

        # Create source files
        source_dir = temp_dir / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("content1")
        (source_dir / "file2.txt").write_text("content2")

        output_path = temp_dir / "archive.tar"

        await converter._create_archive(source_dir, output_path, "tar", 6)

        assert output_path.exists()
        with tarfile.open(output_path, "r") as tf:
            assert "file1.txt" in tf.getnames()
            assert "file2.txt" in tf.getnames()

    @pytest.mark.asyncio
    async def test_create_tar_gz_archive_with_compression(self, temp_dir):
        """Test creating TAR.GZ archive with compression"""
        converter = ArchiveConverter()

        # Create source files
        source_dir = temp_dir / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("content1" * 100)
        (source_dir / "file2.txt").write_text("content2" * 100)

        output_path = temp_dir / "archive.tar.gz"

        await converter._create_archive(source_dir, output_path, "tar.gz", 6)

        assert output_path.exists()
        with tarfile.open(output_path, "r:gz") as tf:
            assert "file1.txt" in tf.getnames()
            assert "file2.txt" in tf.getnames()

    @pytest.mark.asyncio
    async def test_create_tar_bz2_archive(self, temp_dir):
        """Test creating TAR.BZ2 archive"""
        converter = ArchiveConverter()

        # Create source files
        source_dir = temp_dir / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("content1")

        output_path = temp_dir / "archive.tar.bz2"

        await converter._create_archive(source_dir, output_path, "tar.bz2", 6)

        assert output_path.exists()
        with tarfile.open(output_path, "r:bz2") as tf:
            assert "file1.txt" in tf.getnames()

    @pytest.mark.asyncio
    async def test_create_archive_with_compression_level(self, temp_dir):
        """Test creating ZIP archive respects compression level"""
        converter = ArchiveConverter()

        # Create source files
        source_dir = temp_dir / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("content1" * 100)

        output_path_0 = temp_dir / "archive_no_compression.zip"
        output_path_9 = temp_dir / "archive_max_compression.zip"

        await converter._create_archive(source_dir, output_path_0, "zip", 0)
        await converter._create_archive(source_dir, output_path_9, "zip", 9)

        assert output_path_0.exists()
        assert output_path_9.exists()
        # Max compression should be smaller or equal to no compression
        assert output_path_9.stat().st_size <= output_path_0.stat().st_size

    @pytest.mark.asyncio
    async def test_create_archive_nested_directory_structure(self, temp_dir):
        """Test creating archive preserves nested directory structure"""
        converter = ArchiveConverter()

        # Create nested directory structure
        source_dir = temp_dir / "source"
        source_dir.mkdir()
        (source_dir / "subdir1").mkdir()
        (source_dir / "subdir1" / "file1.txt").write_text("content1")
        (source_dir / "subdir2").mkdir()
        (source_dir / "subdir2" / "file2.txt").write_text("content2")

        output_path = temp_dir / "archive.zip"

        await converter._create_archive(source_dir, output_path, "zip", 6)

        with zipfile.ZipFile(output_path, 'r') as zf:
            names = zf.namelist()
            assert "subdir1/file1.txt" in names or "subdir1\\file1.txt" in names
            assert "subdir2/file2.txt" in names or "subdir2\\file2.txt" in names

    @pytest.mark.asyncio
    async def test_create_archive_empty_directory_raises_error(self, temp_dir):
        """Test creating archive from empty directory raises error"""
        converter = ArchiveConverter()

        source_dir = temp_dir / "empty_source"
        source_dir.mkdir()

        output_path = temp_dir / "archive.zip"

        # GZ format should raise error on empty directory
        with pytest.raises(ValueError, match="No files found"):
            await converter._create_archive(source_dir, output_path, "gz", 6)

    @pytest.mark.asyncio
    async def test_create_gz_single_file(self, temp_dir):
        """Test creating GZ archive from single file"""
        converter = ArchiveConverter()

        source_dir = temp_dir / "source"
        source_dir.mkdir()
        (source_dir / "file.txt").write_text("content")

        output_path = temp_dir / "file.txt.gz"

        await converter._create_archive(source_dir, output_path, "gz", 6)

        assert output_path.exists()
        with gzip.open(output_path, "rb") as f:
            assert f.read() == b"content"

    @pytest.mark.asyncio
    async def test_create_7z_archive(self, temp_dir):
        """Test creating 7Z archive when py7zr is available"""
        converter = ArchiveConverter()

        source_dir = temp_dir / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("content1")

        output_path = temp_dir / "archive.7z"

        with patch('app.services.archive_converter.py7zr') as mock_7z:
            mock_archive = MagicMock()
            mock_7z.SevenZipFile.return_value.__enter__.return_value = mock_archive

            await converter._create_archive(source_dir, output_path, "7z", 6)

            mock_7z.SevenZipFile.assert_called_once()
            mock_archive.write.assert_called()

    @pytest.mark.asyncio
    async def test_create_7z_unavailable_raises_error(self, temp_dir):
        """Test 7Z creation fails gracefully when py7zr is not available"""
        converter = ArchiveConverter()

        source_dir = temp_dir / "source"
        source_dir.mkdir()

        output_path = temp_dir / "archive.7z"

        with patch('app.services.archive_converter.SEVENZ_AVAILABLE', False):
            with pytest.raises(ValueError, match="7z support not available"):
                await converter._create_archive(source_dir, output_path, "7z", 6)

    @pytest.mark.asyncio
    async def test_create_archive_unsupported_format_raises_error(self, temp_dir):
        """Test creation with unsupported format raises ValueError"""
        converter = ArchiveConverter()

        source_dir = temp_dir / "source"
        source_dir.mkdir()
        (source_dir / "file.txt").write_text("content")

        output_path = temp_dir / "archive.xyz"

        with pytest.raises(ValueError, match="Unsupported format for creation"):
            await converter._create_archive(source_dir, output_path, "xyz", 6)


# ============================================================================
# CONVERSION TESTS
# ============================================================================

class TestArchiveConversion:
    """Test archive conversion functionality"""

    @pytest.mark.asyncio
    async def test_convert_zip_to_tar_gz_success(self, temp_dir):
        """Test successful ZIP to TAR.GZ conversion"""
        converter = ArchiveConverter()

        # Create a test ZIP file
        input_path = temp_dir / "test.zip"
        output_path = settings.UPLOAD_DIR / "test_converted.tar.gz"

        with zipfile.ZipFile(input_path, 'w') as zf:
            zf.writestr("file1.txt", "content1")
            zf.writestr("file2.txt", "content2")

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            result = await converter.convert(
                input_path=input_path,
                output_format="tar.gz",
                options={},
                session_id="test-session"
            )

            assert result == output_path
            assert output_path.exists()

            # Verify progress was sent
            assert mock_progress.call_count >= 3
            # Check for start, converting, and completion
            calls = [str(call) for call in mock_progress.call_args_list]
            assert any("0" in str(c) for c in calls)  # Start at 0
            assert any("100" in str(c) for c in calls)  # Complete at 100

    @pytest.mark.asyncio
    async def test_convert_tar_to_zip_success(self, temp_dir):
        """Test successful TAR to ZIP conversion"""
        converter = ArchiveConverter()

        # Create a test TAR file
        input_path = temp_dir / "test.tar"
        output_path = settings.UPLOAD_DIR / "test_converted.zip"

        with tarfile.open(input_path, "w") as tf:
            file_path = temp_dir / "file1.txt"
            file_path.write_text("content1")
            tf.add(file_path, arcname="file1.txt")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            result = await converter.convert(
                input_path=input_path,
                output_format="zip",
                options={},
                session_id="test-session"
            )

            assert result == output_path
            assert output_path.exists()

    @pytest.mark.asyncio
    async def test_convert_same_format_copies_file(self, temp_dir):
        """Test converting to same format just copies the file"""
        converter = ArchiveConverter()

        input_path = temp_dir / "test.zip"
        output_path = settings.UPLOAD_DIR / "test_converted.zip"

        with zipfile.ZipFile(input_path, 'w') as zf:
            zf.writestr("file1.txt", "content1")

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            with patch('shutil.copy') as mock_copy:
                result = await converter.convert(
                    input_path=input_path,
                    output_format="zip",
                    options={},
                    session_id="test-session"
                )

                # Should use shutil.copy for same format
                mock_copy.assert_called_once()
                # Verify progress messages
                assert mock_progress.call_count >= 2

    @pytest.mark.asyncio
    async def test_convert_with_compression_level_option(self, temp_dir):
        """Test conversion respects compression level option"""
        converter = ArchiveConverter()

        input_path = temp_dir / "test.zip"
        output_path = settings.UPLOAD_DIR / "test_converted.tar.gz"

        with zipfile.ZipFile(input_path, 'w') as zf:
            zf.writestr("file1.txt", "content1" * 100)

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            result = await converter.convert(
                input_path=input_path,
                output_format="tar.gz",
                options={"compression_level": 9},
                session_id="test-session"
            )

            assert result == output_path
            assert output_path.exists()

    @pytest.mark.asyncio
    async def test_convert_progress_updates_sent(self, temp_dir):
        """Test conversion sends progress updates via WebSocket"""
        converter = ArchiveConverter()

        input_path = temp_dir / "test.zip"
        output_path = settings.UPLOAD_DIR / "test_converted.tar"

        with zipfile.ZipFile(input_path, 'w') as zf:
            zf.writestr("file1.txt", "content1")

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            await converter.convert(
                input_path=input_path,
                output_format="tar",
                options={},
                session_id="test-session"
            )

            # Verify progress was called multiple times
            assert mock_progress.call_count >= 3
            # Check first call (0%)
            first_call = mock_progress.call_args_list[0]
            assert "test-session" in str(first_call)
            # Check last call (100%)
            last_call = mock_progress.call_args_list[-1]
            assert "completed" in str(last_call)

    @pytest.mark.asyncio
    async def test_convert_invalid_input_format_raises_error(self, temp_dir):
        """Test conversion with invalid input format raises ValueError"""
        converter = ArchiveConverter()

        input_path = temp_dir / "test.exe"
        input_path.write_bytes(b"not an archive")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with pytest.raises(ValueError, match="Unknown archive format"):
                await converter.convert(
                    input_path=input_path,
                    output_format="zip",
                    options={},
                    session_id="test-session"
                )

    @pytest.mark.asyncio
    async def test_convert_invalid_output_format_raises_error(self, temp_dir):
        """Test conversion with invalid output format raises ValueError"""
        converter = ArchiveConverter()

        input_path = temp_dir / "test.zip"
        with zipfile.ZipFile(input_path, 'w') as zf:
            zf.writestr("file1.txt", "content1")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with pytest.raises(ValueError, match="Unsupported output format"):
                await converter.convert(
                    input_path=input_path,
                    output_format="exe",
                    options={},
                    session_id="test-session"
                )

    @pytest.mark.asyncio
    async def test_convert_error_sends_failure_progress(self, temp_dir):
        """Test conversion error sends failure progress update"""
        converter = ArchiveConverter()

        input_path = temp_dir / "corrupted.zip"
        input_path.write_bytes(b"PK\x03\x04CORRUPTED")

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            with pytest.raises(Exception):
                await converter.convert(
                    input_path=input_path,
                    output_format="tar",
                    options={},
                    session_id="test-session"
                )

            # Verify failure progress was sent
            failure_calls = [c for c in mock_progress.call_args_list if "failed" in str(c)]
            assert len(failure_calls) > 0


# ============================================================================
# ARCHIVE INFO TESTS
# ============================================================================

class TestArchiveInfo:
    """Test archive metadata extraction"""

    @pytest.mark.asyncio
    async def test_get_archive_info_zip(self, temp_dir):
        """Test getting metadata from ZIP archive"""
        converter = ArchiveConverter()

        archive_path = temp_dir / "test.zip"
        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.writestr("file1.txt", "content1")
            zf.writestr("file2.txt", "content2")

        info = await converter.get_archive_info(archive_path)

        assert info["format"] == "zip"
        assert "size" in info
        assert info["files"] == 2
        assert "file_list" in info

    @pytest.mark.asyncio
    async def test_get_archive_info_tar_gz(self, temp_dir):
        """Test getting metadata from TAR.GZ archive"""
        converter = ArchiveConverter()

        archive_path = temp_dir / "test.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tf:
            file1 = temp_dir / "file1.txt"
            file1.write_text("content1")
            tf.add(file1, arcname="file1.txt")

        info = await converter.get_archive_info(archive_path)

        assert info["format"] == "tar.gz"
        assert "size" in info
        assert info["files"] >= 1
        assert "file_list" in info

    @pytest.mark.asyncio
    async def test_get_archive_info_gz_single_file(self, temp_dir):
        """Test getting metadata from GZ archive"""
        converter = ArchiveConverter()

        archive_path = temp_dir / "file.txt.gz"
        with gzip.open(archive_path, "wb") as f:
            f.write(b"content")

        info = await converter.get_archive_info(archive_path)

        assert info["format"] == "gz"
        assert info["files"] == 1
        assert "size" in info

    @pytest.mark.asyncio
    async def test_get_archive_info_7z(self, temp_dir):
        """Test getting metadata from 7Z archive"""
        converter = ArchiveConverter()

        archive_path = temp_dir / "test.7z"

        with patch('app.services.archive_converter.py7zr') as mock_7z:
            mock_archive = MagicMock()
            mock_archive.getnames.return_value = ["file1.txt", "file2.txt"]
            mock_7z.SevenZipFile.return_value.__enter__.return_value = mock_archive

            archive_path.write_bytes(b"dummy")  # Create dummy file

            info = await converter.get_archive_info(archive_path)

            assert info["format"] == "7z"
            assert "size" in info

    @pytest.mark.asyncio
    async def test_get_archive_info_error_handling(self, temp_dir):
        """Test archive info handles corrupted files gracefully"""
        converter = ArchiveConverter()

        archive_path = temp_dir / "corrupted.zip"
        archive_path.write_bytes(b"CORRUPTED_DATA")

        info = await converter.get_archive_info(archive_path)

        assert "error" in info

    @pytest.mark.asyncio
    async def test_get_archive_info_large_archive_limits_file_list(self, temp_dir):
        """Test archive info limits file list to first 10 files"""
        converter = ArchiveConverter()

        archive_path = temp_dir / "test.zip"
        with zipfile.ZipFile(archive_path, 'w') as zf:
            for i in range(20):
                zf.writestr(f"file{i}.txt", f"content{i}")

        info = await converter.get_archive_info(archive_path)

        assert info["files"] == 20
        assert len(info["file_list"]) <= 10


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_create_archive_with_invalid_compression_level(self, temp_dir):
        """Test archive creation with valid compression level"""
        converter = ArchiveConverter()

        source_dir = temp_dir / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("content1")

        output_path = temp_dir / "archive.zip"

        # Valid compression level (0-9) should work
        await converter._create_archive(source_dir, output_path, "zip", 5)

        assert output_path.exists()

    def test_normalize_format_case_insensitive(self):
        """Test format normalization is case insensitive"""
        converter = ArchiveConverter()

        assert converter._normalize_format("TAR.GZ") == "tar.gz"
        assert converter._normalize_format("TGZ") == "tar.gz"
        assert converter._normalize_format("ZIP") == "zip"

    @pytest.mark.asyncio
    async def test_extract_archive_with_special_characters_in_filenames(self, temp_dir):
        """Test extracting archives with special characters in filenames"""
        converter = ArchiveConverter()

        archive_path = temp_dir / "test.zip"
        extract_path = temp_dir / "extracted"
        extract_path.mkdir()

        with zipfile.ZipFile(archive_path, 'w') as zf:
            zf.writestr("file with spaces.txt", "content")
            zf.writestr("file-with-dashes.txt", "content")
            zf.writestr("file_with_underscores.txt", "content")

        await converter._extract_archive(archive_path, extract_path, "zip")

        assert (extract_path / "file with spaces.txt").exists()
        assert (extract_path / "file-with-dashes.txt").exists()
        assert (extract_path / "file_with_underscores.txt").exists()

    @pytest.mark.asyncio
    async def test_convert_format_alias_tgz(self, temp_dir):
        """Test conversion using TGZ alias for TAR.GZ"""
        converter = ArchiveConverter()

        input_path = temp_dir / "test.zip"
        output_path = settings.UPLOAD_DIR / "test_converted.tgz"

        with zipfile.ZipFile(input_path, 'w') as zf:
            zf.writestr("file1.txt", "content1")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            result = await converter.convert(
                input_path=input_path,
                output_format="tgz",
                options={},
                session_id="test-session"
            )

            # Should normalize tgz to tar.gz
            assert result.name.endswith(".tar.gz") or result.name.endswith(".tgz")


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestArchiveConversionIntegration:
    """Integration tests for complete archive workflows"""

    @pytest.mark.asyncio
    async def test_full_workflow_zip_extract_recompress(self, temp_dir):
        """Test full workflow: create ZIP, extract, and recompress as TAR.GZ"""
        converter = ArchiveConverter()

        # Step 1: Create source files
        source_dir = temp_dir / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("content1")
        (source_dir / "file2.txt").write_text("content2")

        # Step 2: Create ZIP
        zip_path = temp_dir / "archive.zip"
        await converter._create_archive(source_dir, zip_path, "zip", 6)
        assert zip_path.exists()

        # Step 3: Extract ZIP
        extract_dir = temp_dir / "extracted"
        extract_dir.mkdir()
        await converter._extract_archive(zip_path, extract_dir, "zip")
        assert (extract_dir / "file1.txt").exists()

        # Step 4: Recompress as TAR.GZ
        tar_gz_path = temp_dir / "archive.tar.gz"
        await converter._create_archive(extract_dir, tar_gz_path, "tar.gz", 6)
        assert tar_gz_path.exists()

    @pytest.mark.asyncio
    async def test_full_workflow_tar_to_zip_with_progress(self, temp_dir):
        """Test full conversion with progress tracking"""
        converter = ArchiveConverter()

        # Create input TAR
        input_path = temp_dir / "test.tar"
        with tarfile.open(input_path, "w") as tf:
            file_path = temp_dir / "file1.txt"
            file_path.write_text("content1")
            tf.add(file_path, arcname="file1.txt")

        output_path = settings.UPLOAD_DIR / "test_converted.zip"

        progress_updates = []

        async def mock_send_progress(session_id, progress, status, message):
            progress_updates.append({
                "progress": progress,
                "status": status,
                "message": message
            })

        with patch.object(converter, 'send_progress', side_effect=mock_send_progress):
            result = await converter.convert(
                input_path=input_path,
                output_format="zip",
                options={},
                session_id="test-session"
            )

            assert result == output_path
            assert output_path.exists()
            # Verify progress updates
            assert len(progress_updates) >= 3
            # Verify proper progression
            assert progress_updates[0]["progress"] == 0
            assert progress_updates[-1]["progress"] == 100
            assert progress_updates[-1]["status"] == "completed"
