"""
Comprehensive tests for Pydantic models in app/models/conversion.py

Tests cover:
- All enum values and string conversions
- Model validation with constraints
- Default values
- Field constraints (min/max values)
- Optional and required fields
- Nested models
- Edge cases and boundary conditions
"""

import pytest
from app.models.conversion import (
    BatchConversionResponse,
    BatchFileResult,
    BatchZipResponse,
    ConversionResponse,
    ConversionStatus,
    FileInfo,
    ProgressUpdate,
)
from pydantic import ValidationError

# ============================================================================
# ConversionStatus Enum Tests
# ============================================================================


class TestConversionStatusEnum:
    """Test ConversionStatus enum values and behavior"""

    def test_pending_status_value(self):
        """Test PENDING status has correct value"""
        assert ConversionStatus.PENDING.value == "pending"

    def test_uploading_status_value(self):
        """Test UPLOADING status has correct value"""
        assert ConversionStatus.UPLOADING.value == "uploading"

    def test_converting_status_value(self):
        """Test CONVERTING status has correct value"""
        assert ConversionStatus.CONVERTING.value == "converting"

    def test_completed_status_value(self):
        """Test COMPLETED status has correct value"""
        assert ConversionStatus.COMPLETED.value == "completed"

    def test_failed_status_value(self):
        """Test FAILED status has correct value"""
        assert ConversionStatus.FAILED.value == "failed"

    def test_all_status_members(self):
        """Test all ConversionStatus members exist"""
        status_values = {status.value for status in ConversionStatus}
        expected = {"pending", "uploading", "converting", "completed", "failed"}
        assert status_values == expected

    def test_status_string_conversion(self):
        """Test ConversionStatus can be converted to string"""
        status = ConversionStatus.PENDING
        assert str(status.value) == "pending"

    def test_status_string_initialization(self):
        """Test ConversionStatus can be initialized from string value"""
        status = ConversionStatus("pending")
        assert status == ConversionStatus.PENDING

    def test_status_is_string_enum(self):
        """Test ConversionStatus inherits from str"""
        assert issubclass(ConversionStatus, str)


# Format enum and request model tests removed — enums were unused dead code,
# routers validate against config.settings sets directly.

DEAD_TESTS_REMOVED = True  # placeholder

# ============================================================================
# ConversionResponse Tests
# ============================================================================


class TestConversionResponse:
    """Test ConversionResponse model"""

    def test_valid_response_with_all_fields(self):
        """Test creating response with all fields"""
        resp = ConversionResponse(
            session_id="sess-12345",
            status=ConversionStatus.COMPLETED,
            message="Conversion completed successfully",
            output_file="/path/to/output.png",
            download_url="https://example.com/download/output.png",
        )
        assert resp.session_id == "sess-12345"
        assert resp.status == ConversionStatus.COMPLETED
        assert resp.message == "Conversion completed successfully"
        assert resp.output_file == "/path/to/output.png"
        assert resp.download_url == "https://example.com/download/output.png"

    def test_response_with_required_fields_only(self):
        """Test response with only required fields"""
        resp = ConversionResponse(
            session_id="sess-12345",
            status=ConversionStatus.PENDING,
            message="Processing...",
        )
        assert resp.session_id == "sess-12345"
        assert resp.status == ConversionStatus.PENDING
        assert resp.message == "Processing..."
        assert resp.output_file is None
        assert resp.download_url is None

    def test_session_id_required(self):
        """Test session_id is required"""
        with pytest.raises(ValidationError) as exc_info:
            ConversionResponse(
                status=ConversionStatus.COMPLETED,
                message="Done",
            )
        assert "session_id" in str(exc_info.value).lower()

    def test_status_required(self):
        """Test status is required"""
        with pytest.raises(ValidationError) as exc_info:
            ConversionResponse(
                session_id="sess-123",
                message="Done",
            )
        assert "status" in str(exc_info.value).lower()

    def test_message_required(self):
        """Test message is required"""
        with pytest.raises(ValidationError) as exc_info:
            ConversionResponse(
                session_id="sess-123",
                status=ConversionStatus.COMPLETED,
            )
        assert "message" in str(exc_info.value).lower()

    def test_optional_output_file(self):
        """Test output_file is optional"""
        resp = ConversionResponse(
            session_id="sess-123",
            status=ConversionStatus.FAILED,
            message="Error",
        )
        assert resp.output_file is None

    def test_optional_download_url(self):
        """Test download_url is optional"""
        resp = ConversionResponse(
            session_id="sess-123",
            status=ConversionStatus.FAILED,
            message="Error",
        )
        assert resp.download_url is None

    def test_all_status_values_in_response(self):
        """Test all conversion statuses work in response"""
        for status in ConversionStatus:
            resp = ConversionResponse(
                session_id="sess-123",
                status=status,
                message=f"Status is {status.value}",
            )
            assert resp.status == status


# ============================================================================
# ProgressUpdate Tests
# ============================================================================


class TestProgressUpdate:
    """Test ProgressUpdate model"""

    def test_valid_progress_update_with_all_fields(self):
        """Test creating progress update with all fields"""
        update = ProgressUpdate(
            session_id="sess-12345",
            progress=50.5,
            status=ConversionStatus.CONVERTING,
            message="Converting image...",
            current_operation="applying filters",
        )
        assert update.session_id == "sess-12345"
        assert update.progress == 50.5
        assert update.status == ConversionStatus.CONVERTING
        assert update.message == "Converting image..."
        assert update.current_operation == "applying filters"

    def test_progress_zero_valid(self):
        """Test progress at minimum valid value (0)"""
        update = ProgressUpdate(
            session_id="sess-123",
            progress=0,
            status=ConversionStatus.UPLOADING,
            message="Starting...",
        )
        assert update.progress == 0

    def test_progress_hundred_valid(self):
        """Test progress at maximum valid value (100)"""
        update = ProgressUpdate(
            session_id="sess-123",
            progress=100,
            status=ConversionStatus.COMPLETED,
            message="Done!",
        )
        assert update.progress == 100

    def test_progress_float_value(self):
        """Test progress with float value"""
        update = ProgressUpdate(
            session_id="sess-123",
            progress=33.33,
            status=ConversionStatus.CONVERTING,
            message="Processing...",
        )
        assert update.progress == 33.33

    def test_progress_negative_rejected(self):
        """Test negative progress is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            ProgressUpdate(
                session_id="sess-123",
                progress=-1,
                status=ConversionStatus.CONVERTING,
                message="Error",
            )
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_progress_above_hundred_rejected(self):
        """Test progress > 100 is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            ProgressUpdate(
                session_id="sess-123",
                progress=101,
                status=ConversionStatus.CONVERTING,
                message="Error",
            )
        assert "less than or equal to 100" in str(exc_info.value)

    def test_session_id_required(self):
        """Test session_id is required"""
        with pytest.raises(ValidationError) as exc_info:
            ProgressUpdate(
                progress=50,
                status=ConversionStatus.CONVERTING,
                message="Processing...",
            )
        assert "session_id" in str(exc_info.value).lower()

    def test_progress_required(self):
        """Test progress is required"""
        with pytest.raises(ValidationError) as exc_info:
            ProgressUpdate(
                session_id="sess-123",
                status=ConversionStatus.CONVERTING,
                message="Processing...",
            )
        assert "progress" in str(exc_info.value).lower()

    def test_status_required(self):
        """Test status is required"""
        with pytest.raises(ValidationError) as exc_info:
            ProgressUpdate(
                session_id="sess-123",
                progress=50,
                message="Processing...",
            )
        assert "status" in str(exc_info.value).lower()

    def test_message_required(self):
        """Test message is required"""
        with pytest.raises(ValidationError) as exc_info:
            ProgressUpdate(
                session_id="sess-123",
                progress=50,
                status=ConversionStatus.CONVERTING,
            )
        assert "message" in str(exc_info.value).lower()

    def test_current_operation_optional(self):
        """Test current_operation is optional"""
        update = ProgressUpdate(
            session_id="sess-123",
            progress=50,
            status=ConversionStatus.CONVERTING,
            message="Processing...",
        )
        assert update.current_operation is None


# ============================================================================
# FileInfo Tests
# ============================================================================


class TestFileInfo:
    """Test FileInfo model"""

    def test_valid_file_info_with_all_fields(self):
        """Test creating FileInfo with all fields"""
        metadata = {"width": 1920, "height": 1080, "duration": 120}
        info = FileInfo(
            filename="test.mp4",
            size=1024000,
            format="mp4",
            metadata=metadata,
        )
        assert info.filename == "test.mp4"
        assert info.size == 1024000
        assert info.format == "mp4"
        assert info.metadata == metadata

    def test_valid_file_info_without_metadata(self):
        """Test creating FileInfo without metadata"""
        info = FileInfo(
            filename="test.jpg",
            size=512000,
            format="jpg",
        )
        assert info.filename == "test.jpg"
        assert info.size == 512000
        assert info.format == "jpg"
        assert info.metadata is None

    def test_filename_required(self):
        """Test filename is required"""
        with pytest.raises(ValidationError) as exc_info:
            FileInfo(
                size=1024,
                format="txt",
            )
        assert "filename" in str(exc_info.value).lower()

    def test_size_required(self):
        """Test size is required"""
        with pytest.raises(ValidationError) as exc_info:
            FileInfo(
                filename="test.txt",
                format="txt",
            )
        assert "size" in str(exc_info.value).lower()

    def test_format_required(self):
        """Test format is required"""
        with pytest.raises(ValidationError) as exc_info:
            FileInfo(
                filename="test.txt",
                size=1024,
            )
        assert "format" in str(exc_info.value).lower()

    def test_metadata_optional(self):
        """Test metadata is optional"""
        info = FileInfo(
            filename="test.txt",
            size=1024,
            format="txt",
        )
        assert info.metadata is None

    def test_metadata_with_various_keys(self):
        """Test metadata with various key-value pairs"""
        metadata = {
            "width": 1920,
            "height": 1080,
            "duration": 120.5,
            "bitrate": "5Mbps",
            "codec": "h264",
        }
        info = FileInfo(
            filename="video.mp4",
            size=1000000,
            format="mp4",
            metadata=metadata,
        )
        assert info.metadata == metadata


# ============================================================================
# BatchFileResult Tests
# ============================================================================


class TestBatchFileResult:
    """Test BatchFileResult model"""

    def test_successful_result(self):
        """Test successful batch file result"""
        result = BatchFileResult(
            filename="test.png",
            success=True,
            output_path="/output/test.jpg",
        )
        assert result.filename == "test.png"
        assert result.success is True
        assert result.output_path == "/output/test.jpg"
        assert result.error is None

    def test_failed_result(self):
        """Test failed batch file result"""
        result = BatchFileResult(
            filename="test.png",
            success=False,
            error="Invalid format",
        )
        assert result.filename == "test.png"
        assert result.success is False
        assert result.error == "Invalid format"
        assert result.output_path is None

    def test_filename_required(self):
        """Test filename is required"""
        with pytest.raises(ValidationError) as exc_info:
            BatchFileResult(
                success=True,
            )
        assert "filename" in str(exc_info.value).lower()

    def test_success_required(self):
        """Test success is required"""
        with pytest.raises(ValidationError) as exc_info:
            BatchFileResult(
                filename="test.txt",
            )
        assert "success" in str(exc_info.value).lower()

    def test_output_path_optional(self):
        """Test output_path is optional"""
        result = BatchFileResult(
            filename="test.txt",
            success=False,
        )
        assert result.output_path is None

    def test_error_optional(self):
        """Test error is optional"""
        result = BatchFileResult(
            filename="test.txt",
            success=True,
        )
        assert result.error is None


# ============================================================================
# BatchConversionResponse Tests
# ============================================================================


class TestBatchConversionResponse:
    """Test BatchConversionResponse model"""

    def test_valid_batch_response(self):
        """Test creating valid batch conversion response"""
        results = [
            BatchFileResult(
                filename="test1.jpg", success=True, output_path="/out/test1.png"
            ),
            BatchFileResult(
                filename="test2.jpg", success=True, output_path="/out/test2.png"
            ),
            BatchFileResult(
                filename="test3.jpg", success=False, error="Invalid format"
            ),
        ]
        resp = BatchConversionResponse(
            session_id="batch-123",
            total_files=3,
            successful=2,
            failed=1,
            results=results,
            message="Batch conversion completed",
        )
        assert resp.session_id == "batch-123"
        assert resp.total_files == 3
        assert resp.successful == 2
        assert resp.failed == 1
        assert len(resp.results) == 3
        assert resp.message == "Batch conversion completed"

    def test_empty_batch_results(self):
        """Test batch response with empty results"""
        resp = BatchConversionResponse(
            session_id="batch-123",
            total_files=0,
            successful=0,
            failed=0,
            results=[],
            message="No files processed",
        )
        assert resp.total_files == 0
        assert len(resp.results) == 0

    def test_all_successful(self):
        """Test batch response where all files are successful"""
        results = [
            BatchFileResult(filename="f1.jpg", success=True, output_path="/out/f1.png"),
            BatchFileResult(filename="f2.jpg", success=True, output_path="/out/f2.png"),
        ]
        resp = BatchConversionResponse(
            session_id="batch-456",
            total_files=2,
            successful=2,
            failed=0,
            results=results,
            message="All files converted successfully",
        )
        assert resp.successful == 2
        assert resp.failed == 0

    def test_all_failed(self):
        """Test batch response where all files failed"""
        results = [
            BatchFileResult(filename="f1.jpg", success=False, error="Error 1"),
            BatchFileResult(filename="f2.jpg", success=False, error="Error 2"),
        ]
        resp = BatchConversionResponse(
            session_id="batch-789",
            total_files=2,
            successful=0,
            failed=2,
            results=results,
            message="All files failed",
        )
        assert resp.successful == 0
        assert resp.failed == 2

    def test_session_id_required(self):
        """Test session_id is required"""
        with pytest.raises(ValidationError) as exc_info:
            BatchConversionResponse(
                total_files=1,
                successful=0,
                failed=1,
                results=[],
                message="Error",
            )
        assert "session_id" in str(exc_info.value).lower()

    def test_total_files_required(self):
        """Test total_files is required"""
        with pytest.raises(ValidationError) as exc_info:
            BatchConversionResponse(
                session_id="batch-123",
                successful=0,
                failed=0,
                results=[],
                message="Error",
            )
        assert "total_files" in str(exc_info.value).lower()

    def test_successful_required(self):
        """Test successful is required"""
        with pytest.raises(ValidationError) as exc_info:
            BatchConversionResponse(
                session_id="batch-123",
                total_files=1,
                failed=1,
                results=[],
                message="Error",
            )
        assert "successful" in str(exc_info.value).lower()

    def test_failed_required(self):
        """Test failed is required"""
        with pytest.raises(ValidationError) as exc_info:
            BatchConversionResponse(
                session_id="batch-123",
                total_files=1,
                successful=0,
                results=[],
                message="Error",
            )
        assert "failed" in str(exc_info.value).lower()

    def test_results_required(self):
        """Test results is required"""
        with pytest.raises(ValidationError) as exc_info:
            BatchConversionResponse(
                session_id="batch-123",
                total_files=1,
                successful=0,
                failed=1,
                message="Error",
            )
        assert "results" in str(exc_info.value).lower()

    def test_message_required(self):
        """Test message is required"""
        with pytest.raises(ValidationError) as exc_info:
            BatchConversionResponse(
                session_id="batch-123",
                total_files=1,
                successful=0,
                failed=1,
                results=[],
            )
        assert "message" in str(exc_info.value).lower()


# ============================================================================
# BatchZipResponse Tests
# ============================================================================


class TestBatchZipResponse:
    """Test BatchZipResponse model"""

    def test_valid_zip_response(self):
        """Test creating valid zip response"""
        resp = BatchZipResponse(
            zip_file="/output/batch-123.zip",
            download_url="https://example.com/download/batch-123.zip",
            file_count=5,
        )
        assert resp.zip_file == "/output/batch-123.zip"
        assert resp.download_url == "https://example.com/download/batch-123.zip"
        assert resp.file_count == 5

    def test_zip_file_required(self):
        """Test zip_file is required"""
        with pytest.raises(ValidationError) as exc_info:
            BatchZipResponse(
                download_url="https://example.com/download/batch.zip",
                file_count=5,
            )
        assert "zip_file" in str(exc_info.value).lower()

    def test_download_url_required(self):
        """Test download_url is required"""
        with pytest.raises(ValidationError) as exc_info:
            BatchZipResponse(
                zip_file="/output/batch.zip",
                file_count=5,
            )
        assert "download_url" in str(exc_info.value).lower()

    def test_file_count_required(self):
        """Test file_count is required"""
        with pytest.raises(ValidationError) as exc_info:
            BatchZipResponse(
                zip_file="/output/batch.zip",
                download_url="https://example.com/download/batch.zip",
            )
        assert "file_count" in str(exc_info.value).lower()

    def test_zero_file_count(self):
        """Test zip response with zero files"""
        resp = BatchZipResponse(
            zip_file="/output/empty.zip",
            download_url="https://example.com/download/empty.zip",
            file_count=0,
        )
        assert resp.file_count == 0

    def test_large_file_count(self):
        """Test zip response with large file count"""
        resp = BatchZipResponse(
            zip_file="/output/large.zip",
            download_url="https://example.com/download/large.zip",
            file_count=1000,
        )
        assert resp.file_count == 1000
