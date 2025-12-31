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
from pydantic import ValidationError

from app.models.conversion import (
    ConversionStatus,
    ImageFormat,
    VideoFormat,
    AudioFormat,
    DocumentFormat,
    ImageConversionRequest,
    VideoConversionRequest,
    AudioConversionRequest,
    DocumentConversionRequest,
    ConversionResponse,
    ProgressUpdate,
    FileInfo,
    BatchFileResult,
    BatchConversionResponse,
    BatchZipResponse,
)


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


# ============================================================================
# ImageFormat Enum Tests
# ============================================================================

class TestImageFormatEnum:
    """Test ImageFormat enum values"""

    def test_all_image_formats_exist(self):
        """Test all ImageFormat values exist"""
        formats = {fmt.value for fmt in ImageFormat}
        expected = {"png", "jpg", "jpeg", "webp", "gif", "bmp", "tiff", "ico"}
        assert formats == expected

    def test_png_format_value(self):
        """Test PNG format has correct value"""
        assert ImageFormat.PNG.value == "png"

    def test_jpg_format_value(self):
        """Test JPG format has correct value"""
        assert ImageFormat.JPG.value == "jpg"

    def test_jpeg_format_value(self):
        """Test JPEG format has correct value"""
        assert ImageFormat.JPEG.value == "jpeg"

    def test_webp_format_value(self):
        """Test WEBP format has correct value"""
        assert ImageFormat.WEBP.value == "webp"

    def test_gif_format_value(self):
        """Test GIF format has correct value"""
        assert ImageFormat.GIF.value == "gif"

    def test_bmp_format_value(self):
        """Test BMP format has correct value"""
        assert ImageFormat.BMP.value == "bmp"

    def test_tiff_format_value(self):
        """Test TIFF format has correct value"""
        assert ImageFormat.TIFF.value == "tiff"

    def test_ico_format_value(self):
        """Test ICO format has correct value"""
        assert ImageFormat.ICO.value == "ico"

    def test_image_format_string_initialization(self):
        """Test ImageFormat can be initialized from string"""
        fmt = ImageFormat("png")
        assert fmt == ImageFormat.PNG


# ============================================================================
# VideoFormat Enum Tests
# ============================================================================

class TestVideoFormatEnum:
    """Test VideoFormat enum values"""

    def test_all_video_formats_exist(self):
        """Test all VideoFormat values exist"""
        formats = {fmt.value for fmt in VideoFormat}
        expected = {"mp4", "avi", "mov", "mkv", "webm", "flv", "wmv"}
        assert formats == expected

    def test_mp4_format_value(self):
        """Test MP4 format has correct value"""
        assert VideoFormat.MP4.value == "mp4"

    def test_avi_format_value(self):
        """Test AVI format has correct value"""
        assert VideoFormat.AVI.value == "avi"

    def test_mov_format_value(self):
        """Test MOV format has correct value"""
        assert VideoFormat.MOV.value == "mov"

    def test_mkv_format_value(self):
        """Test MKV format has correct value"""
        assert VideoFormat.MKV.value == "mkv"

    def test_webm_format_value(self):
        """Test WEBM format has correct value"""
        assert VideoFormat.WEBM.value == "webm"

    def test_flv_format_value(self):
        """Test FLV format has correct value"""
        assert VideoFormat.FLV.value == "flv"

    def test_wmv_format_value(self):
        """Test WMV format has correct value"""
        assert VideoFormat.WMV.value == "wmv"


# ============================================================================
# AudioFormat Enum Tests
# ============================================================================

class TestAudioFormatEnum:
    """Test AudioFormat enum values"""

    def test_all_audio_formats_exist(self):
        """Test all AudioFormat values exist"""
        formats = {fmt.value for fmt in AudioFormat}
        expected = {"mp3", "wav", "flac", "aac", "ogg", "m4a", "wma"}
        assert formats == expected

    def test_mp3_format_value(self):
        """Test MP3 format has correct value"""
        assert AudioFormat.MP3.value == "mp3"

    def test_wav_format_value(self):
        """Test WAV format has correct value"""
        assert AudioFormat.WAV.value == "wav"

    def test_flac_format_value(self):
        """Test FLAC format has correct value"""
        assert AudioFormat.FLAC.value == "flac"

    def test_aac_format_value(self):
        """Test AAC format has correct value"""
        assert AudioFormat.AAC.value == "aac"

    def test_ogg_format_value(self):
        """Test OGG format has correct value"""
        assert AudioFormat.OGG.value == "ogg"

    def test_m4a_format_value(self):
        """Test M4A format has correct value"""
        assert AudioFormat.M4A.value == "m4a"

    def test_wma_format_value(self):
        """Test WMA format has correct value"""
        assert AudioFormat.WMA.value == "wma"


# ============================================================================
# DocumentFormat Enum Tests
# ============================================================================

class TestDocumentFormatEnum:
    """Test DocumentFormat enum values"""

    def test_all_document_formats_exist(self):
        """Test all DocumentFormat values exist"""
        formats = {fmt.value for fmt in DocumentFormat}
        expected = {"txt", "pdf", "docx", "md", "html", "rtf"}
        assert formats == expected

    def test_txt_format_value(self):
        """Test TXT format has correct value"""
        assert DocumentFormat.TXT.value == "txt"

    def test_pdf_format_value(self):
        """Test PDF format has correct value"""
        assert DocumentFormat.PDF.value == "pdf"

    def test_docx_format_value(self):
        """Test DOCX format has correct value"""
        assert DocumentFormat.DOCX.value == "docx"

    def test_md_format_value(self):
        """Test MD format has correct value"""
        assert DocumentFormat.MD.value == "md"

    def test_html_format_value(self):
        """Test HTML format has correct value"""
        assert DocumentFormat.HTML.value == "html"

    def test_rtf_format_value(self):
        """Test RTF format has correct value"""
        assert DocumentFormat.RTF.value == "rtf"


# ============================================================================
# ImageConversionRequest Tests
# ============================================================================

class TestImageConversionRequest:
    """Test ImageConversionRequest model"""

    def test_valid_request_with_all_parameters(self):
        """Test creating valid request with all parameters"""
        req = ImageConversionRequest(
            output_format=ImageFormat.PNG,
            quality=80,
            width=1920,
            height=1080,
        )
        assert req.output_format == ImageFormat.PNG
        assert req.quality == 80
        assert req.width == 1920
        assert req.height == 1080

    def test_valid_request_with_format_only(self):
        """Test creating valid request with only format"""
        req = ImageConversionRequest(output_format=ImageFormat.JPG)
        assert req.output_format == ImageFormat.JPG

    def test_quality_default_value(self):
        """Test quality default value is 95"""
        req = ImageConversionRequest(output_format=ImageFormat.PNG)
        assert req.quality == 95

    def test_quality_minimum_valid(self):
        """Test quality at minimum valid value (1)"""
        req = ImageConversionRequest(
            output_format=ImageFormat.PNG,
            quality=1,
        )
        assert req.quality == 1

    def test_quality_maximum_valid(self):
        """Test quality at maximum valid value (100)"""
        req = ImageConversionRequest(
            output_format=ImageFormat.PNG,
            quality=100,
        )
        assert req.quality == 100

    def test_quality_below_minimum_rejected(self):
        """Test quality below 1 is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            ImageConversionRequest(
                output_format=ImageFormat.PNG,
                quality=0,
            )
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_quality_above_maximum_rejected(self):
        """Test quality above 100 is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            ImageConversionRequest(
                output_format=ImageFormat.PNG,
                quality=101,
            )
        assert "less than or equal to 100" in str(exc_info.value)

    def test_width_minimum_valid(self):
        """Test width at minimum valid value (1)"""
        req = ImageConversionRequest(
            output_format=ImageFormat.PNG,
            width=1,
        )
        assert req.width == 1

    def test_width_large_value(self):
        """Test width with large valid value"""
        req = ImageConversionRequest(
            output_format=ImageFormat.PNG,
            width=8000,
        )
        assert req.width == 8000

    def test_width_zero_rejected(self):
        """Test width of 0 is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            ImageConversionRequest(
                output_format=ImageFormat.PNG,
                width=0,
            )
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_width_negative_rejected(self):
        """Test negative width is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            ImageConversionRequest(
                output_format=ImageFormat.PNG,
                width=-100,
            )
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_height_minimum_valid(self):
        """Test height at minimum valid value (1)"""
        req = ImageConversionRequest(
            output_format=ImageFormat.PNG,
            height=1,
        )
        assert req.height == 1

    def test_height_zero_rejected(self):
        """Test height of 0 is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            ImageConversionRequest(
                output_format=ImageFormat.PNG,
                height=0,
            )
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_height_negative_rejected(self):
        """Test negative height is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            ImageConversionRequest(
                output_format=ImageFormat.PNG,
                height=-50,
            )
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_output_format_required(self):
        """Test output_format is required"""
        with pytest.raises(ValidationError) as exc_info:
            ImageConversionRequest()
        assert "output_format" in str(exc_info.value).lower()

    def test_width_and_height_optional(self):
        """Test width and height are optional"""
        req = ImageConversionRequest(output_format=ImageFormat.WEBP)
        assert req.width is None
        assert req.height is None

    def test_quality_optional(self):
        """Test quality is optional (has default)"""
        req = ImageConversionRequest(output_format=ImageFormat.PNG)
        assert req.quality is not None

    def test_all_format_options(self):
        """Test all image format options work"""
        for fmt in ImageFormat:
            req = ImageConversionRequest(output_format=fmt)
            assert req.output_format == fmt


# ============================================================================
# VideoConversionRequest Tests
# ============================================================================

class TestVideoConversionRequest:
    """Test VideoConversionRequest model"""

    def test_valid_request_with_all_parameters(self):
        """Test creating valid request with all parameters"""
        req = VideoConversionRequest(
            output_format=VideoFormat.MP4,
            codec="libx265",
            resolution="1080p",
            bitrate="5M",
        )
        assert req.output_format == VideoFormat.MP4
        assert req.codec == "libx265"
        assert req.resolution == "1080p"
        assert req.bitrate == "5M"

    def test_codec_default_value(self):
        """Test codec default value is libx264"""
        req = VideoConversionRequest(output_format=VideoFormat.MP4)
        assert req.codec == "libx264"

    def test_resolution_default_value(self):
        """Test resolution default value is original"""
        req = VideoConversionRequest(output_format=VideoFormat.AVI)
        assert req.resolution == "original"

    def test_bitrate_default_value(self):
        """Test bitrate default value is 2M"""
        req = VideoConversionRequest(output_format=VideoFormat.MKV)
        assert req.bitrate == "2M"

    def test_custom_codec(self):
        """Test custom codec values"""
        codecs = ["libx264", "libx265", "h264", "vp8", "vp9"]
        for codec in codecs:
            req = VideoConversionRequest(
                output_format=VideoFormat.MP4,
                codec=codec,
            )
            assert req.codec == codec

    def test_custom_resolution(self):
        """Test custom resolution values"""
        resolutions = ["720p", "1080p", "2K", "4K", "480p"]
        for resolution in resolutions:
            req = VideoConversionRequest(
                output_format=VideoFormat.MP4,
                resolution=resolution,
            )
            assert req.resolution == resolution

    def test_custom_bitrate(self):
        """Test custom bitrate values"""
        bitrates = ["1M", "2M", "5M", "10M", "500k"]
        for bitrate in bitrates:
            req = VideoConversionRequest(
                output_format=VideoFormat.MP4,
                bitrate=bitrate,
            )
            assert req.bitrate == bitrate

    def test_output_format_required(self):
        """Test output_format is required"""
        with pytest.raises(ValidationError) as exc_info:
            VideoConversionRequest()
        assert "output_format" in str(exc_info.value).lower()

    def test_all_video_formats(self):
        """Test all video format options work"""
        for fmt in VideoFormat:
            req = VideoConversionRequest(output_format=fmt)
            assert req.output_format == fmt

    def test_parameters_are_optional(self):
        """Test codec, resolution, and bitrate are optional"""
        req = VideoConversionRequest(output_format=VideoFormat.MP4)
        assert req.codec is not None  # has default
        assert req.resolution is not None  # has default
        assert req.bitrate is not None  # has default


# ============================================================================
# AudioConversionRequest Tests
# ============================================================================

class TestAudioConversionRequest:
    """Test AudioConversionRequest model"""

    def test_valid_request_with_all_parameters(self):
        """Test creating valid request with all parameters"""
        req = AudioConversionRequest(
            output_format=AudioFormat.MP3,
            bitrate="320k",
            sample_rate=48000,
            channels=2,
        )
        assert req.output_format == AudioFormat.MP3
        assert req.bitrate == "320k"
        assert req.sample_rate == 48000
        assert req.channels == 2

    def test_bitrate_default_value(self):
        """Test bitrate default value is 192k"""
        req = AudioConversionRequest(output_format=AudioFormat.MP3)
        assert req.bitrate == "192k"

    def test_sample_rate_default_value(self):
        """Test sample_rate default value is 44100"""
        req = AudioConversionRequest(output_format=AudioFormat.WAV)
        assert req.sample_rate == 44100

    def test_channels_default_value(self):
        """Test channels default value is 2"""
        req = AudioConversionRequest(output_format=AudioFormat.FLAC)
        assert req.channels == 2

    def test_channels_minimum_valid(self):
        """Test channels at minimum valid value (1 - mono)"""
        req = AudioConversionRequest(
            output_format=AudioFormat.MP3,
            channels=1,
        )
        assert req.channels == 1

    def test_channels_maximum_valid(self):
        """Test channels at maximum valid value (2 - stereo)"""
        req = AudioConversionRequest(
            output_format=AudioFormat.MP3,
            channels=2,
        )
        assert req.channels == 2

    def test_channels_zero_rejected(self):
        """Test channels of 0 is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            AudioConversionRequest(
                output_format=AudioFormat.MP3,
                channels=0,
            )
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_channels_above_two_rejected(self):
        """Test channels > 2 is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            AudioConversionRequest(
                output_format=AudioFormat.MP3,
                channels=3,
            )
        assert "less than or equal to 2" in str(exc_info.value)

    def test_channels_negative_rejected(self):
        """Test negative channels is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            AudioConversionRequest(
                output_format=AudioFormat.MP3,
                channels=-1,
            )
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_custom_bitrate(self):
        """Test custom bitrate values"""
        bitrates = ["128k", "192k", "256k", "320k"]
        for bitrate in bitrates:
            req = AudioConversionRequest(
                output_format=AudioFormat.MP3,
                bitrate=bitrate,
            )
            assert req.bitrate == bitrate

    def test_custom_sample_rate(self):
        """Test custom sample rate values"""
        sample_rates = [22050, 44100, 48000, 96000]
        for sr in sample_rates:
            req = AudioConversionRequest(
                output_format=AudioFormat.WAV,
                sample_rate=sr,
            )
            assert req.sample_rate == sr

    def test_output_format_required(self):
        """Test output_format is required"""
        with pytest.raises(ValidationError) as exc_info:
            AudioConversionRequest()
        assert "output_format" in str(exc_info.value).lower()

    def test_all_audio_formats(self):
        """Test all audio format options work"""
        for fmt in AudioFormat:
            req = AudioConversionRequest(output_format=fmt)
            assert req.output_format == fmt


# ============================================================================
# DocumentConversionRequest Tests
# ============================================================================

class TestDocumentConversionRequest:
    """Test DocumentConversionRequest model"""

    def test_valid_request(self):
        """Test creating valid document conversion request"""
        req = DocumentConversionRequest(output_format=DocumentFormat.PDF)
        assert req.output_format == DocumentFormat.PDF

    def test_output_format_required(self):
        """Test output_format is required"""
        with pytest.raises(ValidationError) as exc_info:
            DocumentConversionRequest()
        assert "output_format" in str(exc_info.value).lower()

    def test_all_document_formats(self):
        """Test all document format options work"""
        for fmt in DocumentFormat:
            req = DocumentConversionRequest(output_format=fmt)
            assert req.output_format == fmt

    def test_document_txt_format(self):
        """Test TXT format"""
        req = DocumentConversionRequest(output_format=DocumentFormat.TXT)
        assert req.output_format == DocumentFormat.TXT

    def test_document_docx_format(self):
        """Test DOCX format"""
        req = DocumentConversionRequest(output_format=DocumentFormat.DOCX)
        assert req.output_format == DocumentFormat.DOCX

    def test_document_md_format(self):
        """Test MD format"""
        req = DocumentConversionRequest(output_format=DocumentFormat.MD)
        assert req.output_format == DocumentFormat.MD

    def test_document_html_format(self):
        """Test HTML format"""
        req = DocumentConversionRequest(output_format=DocumentFormat.HTML)
        assert req.output_format == DocumentFormat.HTML


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
            BatchFileResult(filename="test1.jpg", success=True, output_path="/out/test1.png"),
            BatchFileResult(filename="test2.jpg", success=True, output_path="/out/test2.png"),
            BatchFileResult(filename="test3.jpg", success=False, error="Invalid format"),
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
