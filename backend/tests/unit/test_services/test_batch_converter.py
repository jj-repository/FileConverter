"""
Tests for app/services/batch_converter.py

COVERAGE GOAL: 85%+
Tests batch conversion with parallel/sequential processing, ZIP creation,
format routing, progress tracking, and error handling for multiple files
"""

import pytest
import asyncio
import zipfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
from typing import List

from app.services.batch_converter import BatchConverter
from app.config import settings


# ============================================================================
# BASIC FUNCTIONALITY TESTS
# ============================================================================

class TestBatchConverterBasics:
    """Test basic BatchConverter initialization and setup"""

    def test_initialization_without_websocket(self):
        """Test BatchConverter initializes correctly without WebSocket manager"""
        converter = BatchConverter()

        assert converter.websocket_manager is None
        assert converter.image_converter is not None
        assert converter.video_converter is not None
        assert converter.audio_converter is not None
        assert converter.document_converter is not None
        assert converter.executor is not None

    def test_initialization_with_websocket_manager(self):
        """Test BatchConverter initializes with custom WebSocket manager"""
        mock_ws_manager = Mock()
        converter = BatchConverter(websocket_manager=mock_ws_manager)

        assert converter.websocket_manager == mock_ws_manager
        assert converter.image_converter is not None
        assert converter.video_converter is not None

    def test_initialization_creates_converters(self):
        """Test BatchConverter creates all converter instances"""
        mock_ws_manager = Mock()
        converter = BatchConverter(websocket_manager=mock_ws_manager)

        # Each converter should be passed the WebSocket manager
        assert converter.image_converter.websocket_manager == mock_ws_manager
        assert converter.video_converter.websocket_manager == mock_ws_manager
        assert converter.audio_converter.websocket_manager == mock_ws_manager
        assert converter.document_converter.websocket_manager == mock_ws_manager


# ============================================================================
# FORMAT ROUTING TESTS
# ============================================================================

class TestFormatRouting:
    """Test correct converter selection based on file format"""

    def test_get_converter_for_image_format(self):
        """Test router selects image converter for image formats"""
        converter = BatchConverter()

        result_converter, file_type = converter.get_converter_for_format("jpg")
        assert result_converter == converter.image_converter
        assert file_type == "image"

        result_converter, file_type = converter.get_converter_for_format("png")
        assert result_converter == converter.image_converter
        assert file_type == "image"

    def test_get_converter_for_video_format(self):
        """Test router selects video converter for video formats"""
        converter = BatchConverter()

        result_converter, file_type = converter.get_converter_for_format("mp4")
        assert result_converter == converter.video_converter
        assert file_type == "video"

        result_converter, file_type = converter.get_converter_for_format("mkv")
        assert result_converter == converter.video_converter
        assert file_type == "video"

    def test_get_converter_for_audio_format(self):
        """Test router selects audio converter for audio formats"""
        converter = BatchConverter()

        result_converter, file_type = converter.get_converter_for_format("mp3")
        assert result_converter == converter.audio_converter
        assert file_type == "audio"

        result_converter, file_type = converter.get_converter_for_format("wav")
        assert result_converter == converter.audio_converter
        assert file_type == "audio"

    def test_get_converter_for_document_format(self):
        """Test router selects document converter for document formats"""
        converter = BatchConverter()

        result_converter, file_type = converter.get_converter_for_format("pdf")
        assert result_converter == converter.document_converter
        assert file_type == "document"

        result_converter, file_type = converter.get_converter_for_format("docx")
        assert result_converter == converter.document_converter
        assert file_type == "document"

    def test_get_converter_for_unsupported_format(self):
        """Test router returns None for unsupported formats"""
        converter = BatchConverter()

        result_converter, file_type = converter.get_converter_for_format("xyz")
        assert result_converter is None
        assert file_type is None

        result_converter, file_type = converter.get_converter_for_format("exe")
        assert result_converter is None
        assert file_type is None

    def test_get_converter_requires_lowercase_format(self):
        """Test format routing requires lowercase format strings"""
        converter = BatchConverter()

        # Format should be lowercase (convert_single_file handles this with .lower())
        result_converter, file_type = converter.get_converter_for_format("jpg")
        assert result_converter == converter.image_converter
        assert file_type == "image"

        result_converter, file_type = converter.get_converter_for_format("mp3")
        assert result_converter == converter.audio_converter
        assert file_type == "audio"

        # Uppercase formats won't match (responsibility of caller to lowercase)
        result_converter, file_type = converter.get_converter_for_format("JPG")
        assert result_converter is None
        assert file_type is None


# ============================================================================
# SINGLE FILE CONVERSION TESTS
# ============================================================================

class TestConvertSingleFile:
    """Test single file conversion within batch context"""

    @pytest.mark.asyncio
    async def test_convert_single_file_success(self, temp_dir):
        """Test successful single file conversion"""
        converter = BatchConverter()
        input_file = temp_dir / "test.mp3"
        input_file.write_text("fake audio")

        output_file = settings.UPLOAD_DIR / "test_converted.wav"

        with patch.object(converter.audio_converter, 'convert', new=AsyncMock()) as mock_convert:
            mock_convert.return_value = output_file

            result = await converter.convert_single_file(
                input_path=input_file,
                output_format="wav",
                options={},
                session_id="test-session",
                file_index=0,
                total_files=3
            )

            assert result["success"] is True
            assert result["filename"] == "test.mp3"
            assert result["output_file"] == "test_converted.wav"
            assert result["session_id"] == "test-session"
            assert result["index"] == 0
            assert "/api/audio/download/" in result["download_url"]

    @pytest.mark.asyncio
    async def test_convert_single_file_unsupported_format(self, temp_dir):
        """Test single file conversion with unsupported format"""
        converter = BatchConverter()
        input_file = temp_dir / "test.xyz"
        input_file.write_text("fake file")

        result = await converter.convert_single_file(
            input_path=input_file,
            output_format="mp3",
            options={},
            session_id="test-session",
            file_index=0,
            total_files=1
        )

        assert result["success"] is False
        assert "Unsupported file format" in result["error"]
        assert result["filename"] == "test.xyz"
        assert result["index"] == 0

    @pytest.mark.asyncio
    async def test_convert_single_file_with_exception(self, temp_dir):
        """Test single file conversion handles exceptions"""
        converter = BatchConverter()
        input_file = temp_dir / "test.mp3"
        input_file.write_text("fake audio")

        with patch.object(converter.audio_converter, 'convert') as mock_convert:
            mock_convert.side_effect = Exception("Conversion error")

            result = await converter.convert_single_file(
                input_path=input_file,
                output_format="wav",
                options={},
                session_id="test-session",
                file_index=1,
                total_files=2
            )

            assert result["success"] is False
            assert "Conversion error" in result["error"]
            assert result["index"] == 1

    @pytest.mark.asyncio
    async def test_convert_single_file_sends_progress(self, temp_dir):
        """Test single file conversion sends progress updates"""
        mock_ws_manager = AsyncMock()
        converter = BatchConverter(websocket_manager=mock_ws_manager)

        input_file = temp_dir / "test.jpg"
        input_file.write_text("fake image")

        output_file = settings.UPLOAD_DIR / "test_converted.png"

        with patch.object(converter.image_converter, 'convert', new=AsyncMock()) as mock_convert:
            mock_convert.return_value = output_file

            await converter.convert_single_file(
                input_path=input_file,
                output_format="png",
                options={},
                session_id="test-session",
                file_index=0,
                total_files=2
            )

            # Verify progress was sent
            mock_ws_manager.send_progress.assert_called_once()
            call_args = mock_ws_manager.send_progress.call_args
            assert call_args[0][0] == "test-session"
            assert "converting" in call_args[0][2]

    @pytest.mark.asyncio
    async def test_convert_single_file_creates_correct_session_id(self, temp_dir):
        """Test single file conversion creates correct session ID for converter"""
        converter = BatchConverter()
        input_file = temp_dir / "test.mp3"
        input_file.write_text("fake audio")

        output_file = settings.UPLOAD_DIR / "test_converted.wav"

        with patch.object(converter.audio_converter, 'convert', new=AsyncMock()) as mock_convert:
            mock_convert.return_value = output_file

            await converter.convert_single_file(
                input_path=input_file,
                output_format="wav",
                options={},
                session_id="batch-123",
                file_index=2,
                total_files=5
            )

            # Session ID should be appended with file index
            call_args = mock_convert.call_args
            assert call_args[1]["session_id"] == "batch-123_2"


# ============================================================================
# BATCH CONVERSION - PARALLEL TESTS
# ============================================================================

class TestBatchConversionParallel:
    """Test parallel batch conversion (default behavior)"""

    @pytest.mark.asyncio
    async def test_convert_batch_multiple_files_parallel_success(self, temp_dir):
        """Test successful parallel batch conversion of multiple files"""
        converter = BatchConverter()

        input_files = [
            temp_dir / "test1.mp3",
            temp_dir / "test2.mp3",
            temp_dir / "test3.mp3",
        ]
        for f in input_files:
            f.write_text("fake audio")

        output_files = [
            settings.UPLOAD_DIR / f"test{i}_converted.wav"
            for i in range(1, 4)
        ]

        with patch.object(converter.audio_converter, 'convert', new=AsyncMock()) as mock_convert:
            # Each call returns corresponding output file
            mock_convert.side_effect = output_files

            results = await converter.convert_batch(
                input_paths=input_files,
                output_format="wav",
                options={},
                session_id="batch-session",
                parallel=True
            )

            assert len(results) == 3
            assert all(r["success"] for r in results)
            # Verify all files were processed
            assert mock_convert.call_count == 3

    @pytest.mark.asyncio
    async def test_convert_batch_parallel_partial_failure(self, temp_dir):
        """Test parallel batch conversion with mixed success/failure"""
        converter = BatchConverter()

        input_files = [
            temp_dir / "test1.mp3",
            temp_dir / "test2.xyz",  # Unsupported format
            temp_dir / "test3.mp3",
        ]
        for f in input_files:
            f.write_text("fake data")

        output_file = settings.UPLOAD_DIR / "test_converted.wav"

        with patch.object(converter.audio_converter, 'convert', new=AsyncMock()) as mock_convert:
            mock_convert.side_effect = [output_file, output_file]

            results = await converter.convert_batch(
                input_paths=input_files,
                output_format="wav",
                options={},
                session_id="batch-session",
                parallel=True
            )

            assert len(results) == 3
            # First and third succeed, second fails (unsupported format)
            assert results[0]["success"] is True
            assert results[1]["success"] is False
            assert results[2]["success"] is True
            assert "Unsupported file format" in results[1]["error"]

    @pytest.mark.asyncio
    async def test_convert_batch_parallel_exception_handling(self, temp_dir):
        """Test parallel batch handles exceptions from asyncio.gather"""
        converter = BatchConverter()

        input_files = [
            temp_dir / "test1.mp3",
            temp_dir / "test2.mp3",
        ]
        for f in input_files:
            f.write_text("fake audio")

        with patch.object(converter.audio_converter, 'convert') as mock_convert:
            # Simulate an exception from one of the parallel tasks
            mock_convert.side_effect = [
                settings.UPLOAD_DIR / "test1_converted.wav",
                Exception("Conversion failed"),
            ]

            results = await converter.convert_batch(
                input_paths=input_files,
                output_format="wav",
                options={},
                session_id="batch-session",
                parallel=True
            )

            assert len(results) == 2
            assert results[0]["success"] is True
            assert results[1]["success"] is False
            assert "Conversion failed" in results[1]["error"]

    @pytest.mark.asyncio
    async def test_convert_batch_parallel_all_exceptions(self, temp_dir):
        """Test parallel batch when all tasks raise exceptions"""
        converter = BatchConverter()

        input_files = [
            temp_dir / "test1.mp3",
            temp_dir / "test2.mp3",
            temp_dir / "test3.mp3",
        ]
        for f in input_files:
            f.write_text("fake audio")

        with patch.object(converter.audio_converter, 'convert') as mock_convert:
            # All tasks fail with exceptions
            mock_convert.side_effect = [
                Exception("Error 1"),
                Exception("Error 2"),
                Exception("Error 3"),
            ]

            results = await converter.convert_batch(
                input_paths=input_files,
                output_format="wav",
                options={},
                session_id="batch-session",
                parallel=True
            )

            assert len(results) == 3
            assert all(not r["success"] for r in results)
            assert "Error 1" in results[0]["error"]
            assert "Error 2" in results[1]["error"]
            assert "Error 3" in results[2]["error"]

    @pytest.mark.asyncio
    async def test_convert_batch_parallel_sends_initial_progress(self, temp_dir):
        """Test parallel batch sends initial progress update"""
        mock_ws_manager = AsyncMock()
        converter = BatchConverter(websocket_manager=mock_ws_manager)

        input_files = [temp_dir / "test1.mp3", temp_dir / "test2.mp3"]
        for f in input_files:
            f.write_text("fake audio")

        with patch.object(converter.audio_converter, 'convert', new=AsyncMock()):
            await converter.convert_batch(
                input_paths=input_files,
                output_format="wav",
                options={},
                session_id="batch-session",
                parallel=True
            )

            # First call should be initial progress with 0%
            first_call = mock_ws_manager.send_progress.call_args_list[0]
            assert first_call[0][1] == 0  # Progress 0%
            assert "Starting batch" in first_call[0][3]

    @pytest.mark.asyncio
    async def test_convert_batch_parallel_sends_completion_progress(self, temp_dir):
        """Test parallel batch sends completion progress with statistics"""
        mock_ws_manager = AsyncMock()
        converter = BatchConverter(websocket_manager=mock_ws_manager)

        input_files = [
            temp_dir / "test1.mp3",
            temp_dir / "test2.mp3",
            temp_dir / "test3.xyz",  # Will fail
        ]
        for f in input_files:
            f.write_text("fake data")

        with patch.object(converter.audio_converter, 'convert', new=AsyncMock()) as mock_convert:
            output_file = settings.UPLOAD_DIR / "test_converted.wav"
            mock_convert.side_effect = [output_file, output_file]

            await converter.convert_batch(
                input_paths=input_files,
                output_format="wav",
                options={},
                session_id="batch-session",
                parallel=True
            )

            # Last call should be completion progress with 100%
            last_call = mock_ws_manager.send_progress.call_args_list[-1]
            assert last_call[0][1] == 100  # Progress 100%
            assert "completed" in last_call[0][2]
            assert "2 successful" in last_call[0][3]
            assert "1 failed" in last_call[0][3]


# ============================================================================
# BATCH CONVERSION - SEQUENTIAL TESTS
# ============================================================================

class TestBatchConversionSequential:
    """Test sequential batch conversion"""

    @pytest.mark.asyncio
    async def test_convert_batch_sequential_success(self, temp_dir):
        """Test successful sequential batch conversion"""
        converter = BatchConverter()

        input_files = [
            temp_dir / "test1.mp3",
            temp_dir / "test2.mp3",
            temp_dir / "test3.mp3",
        ]
        for f in input_files:
            f.write_text("fake audio")

        output_files = [
            settings.UPLOAD_DIR / f"test{i}_converted.wav"
            for i in range(1, 4)
        ]

        with patch.object(converter.audio_converter, 'convert', new=AsyncMock()) as mock_convert:
            mock_convert.side_effect = output_files

            results = await converter.convert_batch(
                input_paths=input_files,
                output_format="wav",
                options={},
                session_id="batch-session",
                parallel=False
            )

            assert len(results) == 3
            assert all(r["success"] for r in results)
            assert mock_convert.call_count == 3

    @pytest.mark.asyncio
    async def test_convert_batch_sequential_partial_failure(self, temp_dir):
        """Test sequential batch conversion with partial failure"""
        converter = BatchConverter()

        input_files = [
            temp_dir / "test1.mp3",
            temp_dir / "test2.mp3",
            temp_dir / "test3.mp3",
        ]
        for f in input_files:
            f.write_text("fake audio")

        with patch.object(converter.audio_converter, 'convert', new=AsyncMock()) as mock_convert:
            output_file = settings.UPLOAD_DIR / "test_converted.wav"
            # First succeeds, second fails, third succeeds
            mock_convert.side_effect = [
                output_file,
                Exception("Conversion error"),
                output_file,
            ]

            results = await converter.convert_batch(
                input_paths=input_files,
                output_format="wav",
                options={},
                session_id="batch-session",
                parallel=False
            )

            assert len(results) == 3
            assert results[0]["success"] is True
            assert results[1]["success"] is False
            assert results[2]["success"] is True
            assert "Conversion error" in results[1]["error"]

    @pytest.mark.asyncio
    async def test_convert_batch_sequential_processes_in_order(self, temp_dir):
        """Test sequential batch processes files in order"""
        converter = BatchConverter()

        input_files = [
            temp_dir / "test1.mp3",
            temp_dir / "test2.mp3",
        ]
        for f in input_files:
            f.write_text("fake audio")

        call_order = []

        async def mock_convert_tracking(*args, **kwargs):
            call_order.append(kwargs.get("session_id"))
            return settings.UPLOAD_DIR / "test_converted.wav"

        with patch.object(converter.audio_converter, 'convert', new=AsyncMock(side_effect=mock_convert_tracking)):
            await converter.convert_batch(
                input_paths=input_files,
                output_format="wav",
                options={},
                session_id="batch-session",
                parallel=False
            )

            # Verify order: session_0, session_1
            assert len(call_order) == 2
            assert call_order[0] == "batch-session_0"
            assert call_order[1] == "batch-session_1"


# ============================================================================
# BATCH CONVERSION - EMPTY AND EDGE CASES
# ============================================================================

class TestBatchConversionEdgeCases:
    """Test batch conversion edge cases"""

    @pytest.mark.asyncio
    async def test_convert_batch_empty_file_list(self):
        """Test batch conversion with empty file list"""
        mock_ws_manager = AsyncMock()
        converter = BatchConverter(websocket_manager=mock_ws_manager)

        results = await converter.convert_batch(
            input_paths=[],
            output_format="wav",
            options={},
            session_id="batch-session",
            parallel=True
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_convert_batch_single_file(self, temp_dir):
        """Test batch conversion with single file"""
        converter = BatchConverter()

        input_file = temp_dir / "test.mp3"
        input_file.write_text("fake audio")

        output_file = settings.UPLOAD_DIR / "test_converted.wav"

        with patch.object(converter.audio_converter, 'convert', new=AsyncMock()) as mock_convert:
            mock_convert.return_value = output_file

            results = await converter.convert_batch(
                input_paths=[input_file],
                output_format="wav",
                options={},
                session_id="batch-session",
                parallel=True
            )

            assert len(results) == 1
            assert results[0]["success"] is True

    @pytest.mark.asyncio
    async def test_convert_batch_all_files_fail(self, temp_dir):
        """Test batch conversion where all files fail"""
        converter = BatchConverter()

        input_files = [
            temp_dir / "test1.xyz",
            temp_dir / "test2.abc",
            temp_dir / "test3.invalid",
        ]
        for f in input_files:
            f.write_text("invalid")

        results = await converter.convert_batch(
            input_paths=input_files,
            output_format="wav",
            options={},
            session_id="batch-session",
            parallel=True
        )

        assert len(results) == 3
        assert all(not r["success"] for r in results)


# ============================================================================
# ZIP CREATION TESTS
# ============================================================================

class TestZipCreation:
    """Test ZIP archive creation"""

    @pytest.mark.asyncio
    async def test_create_zip_archive_success(self, temp_dir):
        """Test successful ZIP archive creation"""
        converter = BatchConverter()

        # Create test files
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")

        zip_path = await converter.create_zip_archive(
            file_paths=[file1, file2],
            archive_name="test_archive.zip"
        )

        assert zip_path.exists()
        assert zip_path.name == "test_archive.zip"

        # Verify ZIP contents
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            names = zipf.namelist()
            assert "file1.txt" in names
            assert "file2.txt" in names
            assert zipf.read("file1.txt") == b"Content 1"
            assert zipf.read("file2.txt") == b"Content 2"

    @pytest.mark.asyncio
    async def test_create_zip_archive_single_file(self, temp_dir):
        """Test ZIP creation with single file"""
        converter = BatchConverter()

        test_file = temp_dir / "single.txt"
        test_file.write_text("Single file")

        zip_path = await converter.create_zip_archive(
            file_paths=[test_file],
            archive_name="single_archive.zip"
        )

        assert zip_path.exists()
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            assert "single.txt" in zipf.namelist()

    @pytest.mark.asyncio
    async def test_create_zip_archive_with_missing_file(self, temp_dir):
        """Test ZIP creation skips missing files"""
        converter = BatchConverter()

        existing_file = temp_dir / "exists.txt"
        existing_file.write_text("Exists")

        missing_file = temp_dir / "missing.txt"

        zip_path = await converter.create_zip_archive(
            file_paths=[existing_file, missing_file],
            archive_name="partial_archive.zip"
        )

        assert zip_path.exists()
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            names = zipf.namelist()
            assert "exists.txt" in names
            assert "missing.txt" not in names

    @pytest.mark.asyncio
    async def test_create_zip_archive_empty_list(self, temp_dir):
        """Test ZIP creation with empty file list"""
        converter = BatchConverter()

        zip_path = await converter.create_zip_archive(
            file_paths=[],
            archive_name="empty_archive.zip"
        )

        assert zip_path.exists()
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            assert len(zipf.namelist()) == 0

    @pytest.mark.asyncio
    async def test_create_zip_archive_multiple_formats(self, temp_dir):
        """Test ZIP creation with mixed file formats"""
        converter = BatchConverter()

        txt_file = temp_dir / "document.txt"
        wav_file = temp_dir / "audio.wav"
        jpg_file = temp_dir / "image.jpg"

        txt_file.write_text("Text content")
        wav_file.write_bytes(b"fake wav data")
        jpg_file.write_bytes(b"fake jpg data")

        zip_path = await converter.create_zip_archive(
            file_paths=[txt_file, wav_file, jpg_file],
            archive_name="mixed_archive.zip"
        )

        assert zip_path.exists()
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            names = zipf.namelist()
            assert len(names) == 3
            assert "document.txt" in names
            assert "audio.wav" in names
            assert "image.jpg" in names

    @pytest.mark.asyncio
    async def test_create_zip_archive_custom_name(self, temp_dir):
        """Test ZIP creation with custom archive name"""
        converter = BatchConverter()

        test_file = temp_dir / "content.txt"
        test_file.write_text("Content")

        custom_name = "my_custom_archive.zip"
        zip_path = await converter.create_zip_archive(
            file_paths=[test_file],
            archive_name=custom_name
        )

        assert zip_path.name == custom_name
        assert zip_path.exists()

    @pytest.mark.asyncio
    async def test_create_zip_archive_default_name(self, temp_dir):
        """Test ZIP creation uses default name when not specified"""
        converter = BatchConverter()

        test_file = temp_dir / "content.txt"
        test_file.write_text("Content")

        zip_path = await converter.create_zip_archive(
            file_paths=[test_file]
        )

        assert zip_path.name == "converted_files.zip"
        assert zip_path.exists()


# ============================================================================
# PROGRESS TRACKING TESTS
# ============================================================================

class TestProgressTracking:
    """Test progress tracking during batch conversion"""

    @pytest.mark.asyncio
    async def test_progress_tracking_per_file(self, temp_dir):
        """Test progress is tracked per file"""
        mock_ws_manager = AsyncMock()
        converter = BatchConverter(websocket_manager=mock_ws_manager)

        input_files = [
            temp_dir / "test1.mp3",
            temp_dir / "test2.mp3",
            temp_dir / "test3.mp3",
        ]
        for f in input_files:
            f.write_text("fake audio")

        with patch.object(converter.audio_converter, 'convert', new=AsyncMock()) as mock_convert:
            output_file = settings.UPLOAD_DIR / "test_converted.wav"
            mock_convert.return_value = output_file

            await converter.convert_batch(
                input_paths=input_files,
                output_format="wav",
                options={},
                session_id="batch-session",
                parallel=False
            )

            # Each file should trigger a progress update
            calls = mock_ws_manager.send_progress.call_args_list
            # Initial + 3 files + completion = at least 5 calls
            assert len(calls) >= 5

    @pytest.mark.asyncio
    async def test_progress_includes_file_status(self, temp_dir):
        """Test progress messages include file status information"""
        mock_ws_manager = AsyncMock()
        converter = BatchConverter(websocket_manager=mock_ws_manager)

        input_file = temp_dir / "test.mp3"
        input_file.write_text("fake audio")

        with patch.object(converter.audio_converter, 'convert', new=AsyncMock()):
            await converter.convert_batch(
                input_paths=[input_file],
                output_format="wav",
                options={},
                session_id="batch-session"
            )

            # Check progress calls contain filename
            calls = mock_ws_manager.send_progress.call_args_list
            file_mention_found = False
            for call in calls:
                message = call[0][3]  # Message is 4th argument
                if "test.mp3" in message or "1 of 1" in message:
                    file_mention_found = True
            assert file_mention_found

    @pytest.mark.asyncio
    async def test_progress_completion_shows_statistics(self, temp_dir):
        """Test completion progress shows success/failure statistics"""
        mock_ws_manager = AsyncMock()
        converter = BatchConverter(websocket_manager=mock_ws_manager)

        input_files = [
            temp_dir / "test1.mp3",
            temp_dir / "test2.mp3",
            temp_dir / "test3.xyz",  # Will fail
        ]
        for f in input_files:
            f.write_text("fake")

        with patch.object(converter.audio_converter, 'convert', new=AsyncMock()) as mock_convert:
            output_file = settings.UPLOAD_DIR / "test_converted.wav"
            mock_convert.side_effect = [output_file, output_file]

            await converter.convert_batch(
                input_paths=input_files,
                output_format="wav",
                options={},
                session_id="batch-session"
            )

            # Last call is completion
            last_call = mock_ws_manager.send_progress.call_args_list[-1]
            completion_msg = last_call[0][3]
            assert "2 successful" in completion_msg
            assert "1 failed" in completion_msg


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling in batch conversion"""

    @pytest.mark.asyncio
    async def test_partial_batch_failure_continues_processing(self, temp_dir):
        """Test batch continues processing after partial failures"""
        converter = BatchConverter()

        input_files = [
            temp_dir / "test1.mp3",
            temp_dir / "test2.mp3",
            temp_dir / "test3.mp3",
        ]
        for f in input_files:
            f.write_text("fake audio")

        with patch.object(converter.audio_converter, 'convert', new=AsyncMock()) as mock_convert:
            output_file = settings.UPLOAD_DIR / "test_converted.wav"
            # Fail, succeed, succeed
            mock_convert.side_effect = [
                Exception("Error 1"),
                output_file,
                output_file,
            ]

            results = await converter.convert_batch(
                input_paths=input_files,
                output_format="wav",
                options={},
                session_id="batch-session",
                parallel=False
            )

            # All files should be processed
            assert len(results) == 3
            successful = sum(1 for r in results if r["success"])
            assert successful == 2

    @pytest.mark.asyncio
    async def test_invalid_converter_type_error(self, temp_dir):
        """Test handling when converter type cannot be determined"""
        converter = BatchConverter()

        # Create file with unsupported extension
        input_file = temp_dir / "test.unknown"
        input_file.write_text("unknown format")

        result = await converter.convert_single_file(
            input_path=input_file,
            output_format="mp3",
            options={},
            session_id="test-session",
            file_index=0,
            total_files=1
        )

        assert result["success"] is False
        assert "Unsupported file format" in result["error"]

    @pytest.mark.asyncio
    async def test_conversion_error_includes_filename(self, temp_dir):
        """Test error results include filename for identification"""
        converter = BatchConverter()

        input_file = temp_dir / "my_audio_file.mp3"
        input_file.write_text("fake audio")

        with patch.object(converter.audio_converter, 'convert') as mock_convert:
            mock_convert.side_effect = Exception("Codec not supported")

            result = await converter.convert_single_file(
                input_path=input_file,
                output_format="wav",
                options={},
                session_id="test-session",
                file_index=0,
                total_files=1
            )

            assert result["filename"] == "my_audio_file.mp3"
            assert result["success"] is False
            assert "Codec not supported" in result["error"]

    @pytest.mark.asyncio
    async def test_conversion_error_propagates_correctly(self, temp_dir):
        """Test that conversion errors are properly captured and returned"""
        converter = BatchConverter()

        input_file = temp_dir / "test.mp3"
        input_file.write_text("fake audio")

        error_message = "FFmpeg process terminated unexpectedly"

        with patch.object(converter.audio_converter, 'convert') as mock_convert:
            mock_convert.side_effect = RuntimeError(error_message)

            result = await converter.convert_single_file(
                input_path=input_file,
                output_format="wav",
                options={},
                session_id="test-session",
                file_index=0,
                total_files=1
            )

            assert result["success"] is False
            assert error_message in result["error"]

    @pytest.mark.asyncio
    async def test_websocket_not_available_doesnt_crash(self, temp_dir):
        """Test batch conversion works when WebSocket manager is unavailable"""
        converter = BatchConverter(websocket_manager=None)

        input_file = temp_dir / "test.mp3"
        input_file.write_text("fake audio")

        output_file = settings.UPLOAD_DIR / "test_converted.wav"

        with patch.object(converter.audio_converter, 'convert', new=AsyncMock()) as mock_convert:
            mock_convert.return_value = output_file

            # Should not raise exception
            results = await converter.convert_batch(
                input_paths=[input_file],
                output_format="wav",
                options={},
                session_id="batch-session"
            )

            assert len(results) == 1
            assert results[0]["success"] is True


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestBatchConversionIntegration:
    """Integration tests for complete batch conversion workflows"""

    @pytest.mark.asyncio
    async def test_full_workflow_image_batch(self, temp_dir):
        """Test full workflow: batch convert images then create ZIP"""
        converter = BatchConverter()

        # Create input files
        input_files = [
            temp_dir / "image1.jpg",
            temp_dir / "image2.jpg",
        ]
        for f in input_files:
            f.write_bytes(b"fake jpg data")

        output_files = [
            settings.UPLOAD_DIR / "image1_converted.png",
            settings.UPLOAD_DIR / "image2_converted.png",
        ]

        with patch.object(converter.image_converter, 'convert', new=AsyncMock()) as mock_convert:
            mock_convert.side_effect = output_files

            # Convert batch
            results = await converter.convert_batch(
                input_paths=input_files,
                output_format="png",
                options={},
                session_id="batch-session"
            )

            assert len(results) == 2
            assert all(r["success"] for r in results)

            # Extract output paths
            output_paths = [r["output_path"] for r in results if r["success"]]

            # Create ZIP
            for output_file in output_files:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(b"fake png data")

            zip_path = await converter.create_zip_archive(
                file_paths=output_paths,
                archive_name="converted_images.zip"
            )

            assert zip_path.exists()
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                assert len(zipf.namelist()) == 2

    @pytest.mark.asyncio
    async def test_full_workflow_mixed_formats(self, temp_dir):
        """Test batch conversion of mixed file formats"""
        converter = BatchConverter()

        input_files = [
            temp_dir / "audio.mp3",
            temp_dir / "image.jpg",
            temp_dir / "document.txt",
        ]
        for f in input_files:
            f.write_bytes(b"fake data")

        with patch.object(converter.audio_converter, 'convert', new=AsyncMock()) as mock_audio:
            with patch.object(converter.image_converter, 'convert', new=AsyncMock()) as mock_image:
                with patch.object(converter.document_converter, 'convert', new=AsyncMock()) as mock_doc:
                    audio_output = settings.UPLOAD_DIR / "audio_converted.wav"
                    image_output = settings.UPLOAD_DIR / "image_converted.png"
                    doc_output = settings.UPLOAD_DIR / "document_converted.pdf"

                    mock_audio.return_value = audio_output
                    mock_image.return_value = image_output
                    mock_doc.return_value = doc_output

                    results = await converter.convert_batch(
                        input_paths=input_files,
                        output_format="wav",  # Won't apply to all, just routing
                        options={},
                        session_id="batch-session"
                    )

                    assert len(results) == 3

    @pytest.mark.asyncio
    async def test_concurrent_batch_sessions(self, temp_dir):
        """Test multiple concurrent batch conversion sessions"""
        converter = BatchConverter()

        input_files1 = [temp_dir / "batch1_file.mp3"]
        input_files2 = [temp_dir / "batch2_file.jpg"]

        input_files1[0].write_bytes(b"fake audio")
        input_files2[0].write_bytes(b"fake image")

        with patch.object(converter.audio_converter, 'convert', new=AsyncMock()) as mock_audio:
            with patch.object(converter.image_converter, 'convert', new=AsyncMock()) as mock_image:
                audio_output = settings.UPLOAD_DIR / "audio_converted.wav"
                image_output = settings.UPLOAD_DIR / "image_converted.png"

                mock_audio.return_value = audio_output
                mock_image.return_value = image_output

                # Run two batch conversions concurrently
                results1, results2 = await asyncio.gather(
                    converter.convert_batch(
                        input_paths=input_files1,
                        output_format="wav",
                        options={},
                        session_id="batch-session-1"
                    ),
                    converter.convert_batch(
                        input_paths=input_files2,
                        output_format="png",
                        options={},
                        session_id="batch-session-2"
                    )
                )

                assert len(results1) == 1
                assert len(results2) == 1
                assert all(r["success"] for r in results1)
                assert all(r["success"] for r in results2)
