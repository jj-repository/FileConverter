"""
Tests for app/services/video_converter.py

COVERAGE GOAL: 85%+
Tests FFmpeg integration, command injection prevention, progress tracking
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio
import json

from app.services.video_converter import VideoConverter
from app.config import settings
from tests.mocks.ffmpeg_mock import FFmpegMock, FFprobeMock


# ============================================================================
# BASIC FUNCTIONALITY TESTS
# ============================================================================

class TestVideoConverterBasics:
    """Test basic VideoConverter functionality"""

    def test_initialization(self):
        """Test VideoConverter initializes correctly"""
        converter = VideoConverter()

        assert converter.supported_formats is not None
        assert "input" in converter.supported_formats
        assert "output" in converter.supported_formats
        assert "mp4" in converter.supported_formats["input"]
        assert "webm" in converter.supported_formats["output"]

    @pytest.mark.asyncio
    async def test_get_supported_formats(self):
        """Test get_supported_formats returns correct formats"""
        converter = VideoConverter()

        formats = await converter.get_supported_formats()

        assert "input" in formats
        assert "output" in formats
        assert isinstance(formats["input"], list)
        assert isinstance(formats["output"], list)
        assert len(formats["input"]) > 0
        assert len(formats["output"]) > 0


# ============================================================================
# SECURITY-CRITICAL TESTS (COMMAND INJECTION PREVENTION)
# ============================================================================

class TestVideoConverterSecurity:
    """Test security-critical validation"""

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_invalid_codec_rejected(self, temp_dir):
        """Test that codec='rm -rf /' is rejected"""
        converter = VideoConverter()

        input_file = temp_dir / "test.mp4"
        input_file.write_text("mock video")

        options = {
            "codec": "rm -rf /",  # Malicious codec
            "resolution": "720p",
            "bitrate": "2M"
        }

        with pytest.raises(ValueError) as exc_info:
            await converter.convert(input_file, "webm", options, "test-session")

        assert "Invalid codec" in str(exc_info.value)
        assert "rm -rf /" in str(exc_info.value)

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_invalid_resolution_rejected(self, temp_dir):
        """Test that resolution='9999p' is rejected"""
        converter = VideoConverter()

        input_file = temp_dir / "test.mp4"
        input_file.write_text("mock video")

        options = {
            "codec": "libx264",
            "resolution": "9999p",  # Invalid resolution
            "bitrate": "2M"
        }

        with pytest.raises(ValueError) as exc_info:
            await converter.convert(input_file, "webm", options, "test-session")

        assert "Invalid resolution" in str(exc_info.value)

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_invalid_bitrate_rejected(self, temp_dir):
        """Test that bitrate='999999M' is rejected"""
        converter = VideoConverter()

        input_file = temp_dir / "test.mp4"
        input_file.write_text("mock video")

        options = {
            "codec": "libx264",
            "resolution": "720p",
            "bitrate": "999999M"  # Invalid bitrate
        }

        with pytest.raises(ValueError) as exc_info:
            await converter.convert(input_file, "webm", options, "test-session")

        assert "Invalid bitrate" in str(exc_info.value)

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_command_injection_in_codec_blocked(self, temp_dir):
        """Test that codec with shell injection is blocked"""
        converter = VideoConverter()

        input_file = temp_dir / "test.mp4"
        input_file.write_text("mock video")

        malicious_codecs = [
            "; echo pwned",
            "| cat /etc/passwd",
            "&& malicious_command",
            "`whoami`",
            "$(cat /etc/passwd)"
        ]

        for codec in malicious_codecs:
            options = {"codec": codec, "resolution": "720p", "bitrate": "2M"}

            with pytest.raises(ValueError) as exc_info:
                await converter.convert(input_file, "webm", options, "test-session")

            assert "Invalid codec" in str(exc_info.value)

    @pytest.mark.security
    def test_all_allowed_codecs_are_valid(self):
        """Test that all ALLOWED_VIDEO_CODECS are recognized"""
        converter = VideoConverter()

        # All whitelisted codecs should be safe
        safe_codecs = settings.ALLOWED_VIDEO_CODECS

        assert "libx264" in safe_codecs
        assert "libx265" in safe_codecs
        assert "libvpx-vp9" in safe_codecs

        # Dangerous patterns should NOT be in whitelist
        assert "; rm" not in safe_codecs
        assert "| cat" not in safe_codecs


# ============================================================================
# CONVERSION TESTS
# ============================================================================

class TestVideoConversion:
    """Test video conversion logic"""

    @pytest.mark.asyncio
    async def test_convert_mp4_to_webm_success(self, temp_dir, mock_websocket_manager):
        """Test successful MP4 to WebM conversion"""
        converter = VideoConverter(mock_websocket_manager)

        input_file = temp_dir / "test.mp4"
        input_file.write_text("mock video content")

        output_file = settings.UPLOAD_DIR / "test_converted.webm"

        options = {
            "codec": "libvpx-vp9",
            "resolution": "720p",
            "bitrate": "2M"
        }

        # Mock FFprobe for duration
        with patch('subprocess.run') as mock_run:
            # First call: ffprobe (duration)
            mock_run.return_value = Mock(
                returncode=0,
                stdout="120.5",
                stderr=""
            )

            # Mock FFmpeg conversion
            with FFmpegMock.mock_successful_conversion(output_file):
                result = await converter.convert(input_file, "webm", options, "test-session")

                assert result == output_file
                assert output_file.exists()

                # Verify progress updates sent
                assert mock_websocket_manager.send_progress.called

    @pytest.mark.asyncio
    async def test_unsupported_format_raises_error(self, temp_dir):
        """Test that .exe to .mp4 raises ValueError"""
        converter = VideoConverter()

        input_file = temp_dir / "malware.exe"
        input_file.write_text("executable")

        options = {"codec": "libx264", "resolution": "original", "bitrate": "2M"}

        with pytest.raises(ValueError) as exc_info:
            await converter.convert(input_file, "mp4", options, "test-session")

        assert "Unsupported conversion" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_conversion_with_different_resolutions(self, temp_dir, mock_websocket_manager):
        """Test conversion with various resolution options"""
        converter = VideoConverter(mock_websocket_manager)

        # Ensure upload directory exists
        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        resolutions = ["original", "480p", "720p", "1080p", "4k"]

        for i, resolution in enumerate(resolutions):
            # Use unique input file for each resolution to avoid output path collision
            input_file = temp_dir / f"test_{resolution}.mp4"
            input_file.write_text("mock video")

            # Output path matches what converter actually generates
            output_file = settings.UPLOAD_DIR / f"test_{resolution}_converted.mp4"

            options = {
                "codec": "libx264",
                "resolution": resolution,
                "bitrate": "2M"
            }

            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=0, stdout="120.0", stderr="")

                with FFmpegMock.mock_successful_conversion(output_file):
                    result = await converter.convert(input_file, "mp4", options, "test-session")
                    assert result.exists()

                    # Clean up for next iteration
                    if output_file.exists():
                        output_file.unlink()

    @pytest.mark.asyncio
    async def test_conversion_timeout_handled(self, temp_dir):
        """Test that conversion >600s raises timeout error"""
        converter = VideoConverter()

        input_file = temp_dir / "test.mp4"
        input_file.write_text("mock video")

        options = {"codec": "libx264", "resolution": "720p", "bitrate": "2M"}

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="120.0", stderr="")

            with FFmpegMock.mock_timeout_conversion():
                with pytest.raises(Exception) as exc_info:
                    await converter.convert(input_file, "mp4", options, "test-session")

                assert "timed out" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_ffmpeg_error_propagated(self, temp_dir):
        """Test that FFmpeg errors are caught and raised"""
        converter = VideoConverter()

        input_file = temp_dir / "test.mp4"
        input_file.write_text("mock video")

        options = {"codec": "libx264", "resolution": "720p", "bitrate": "2M"}

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="120.0", stderr="")

            with FFmpegMock.mock_failed_conversion("FFmpeg error: Invalid codec"):
                with pytest.raises(Exception) as exc_info:
                    await converter.convert(input_file, "mp4", options, "test-session")

                assert "FFmpeg conversion failed" in str(exc_info.value)


# ============================================================================
# DURATION EXTRACTION TESTS
# ============================================================================

class TestVideoDuration:
    """Test video duration extraction"""

    @pytest.mark.asyncio
    async def test_get_video_duration_success(self, temp_dir):
        """Test successful duration extraction"""
        converter = VideoConverter()

        video_file = temp_dir / "test.mp4"
        video_file.write_text("mock video")

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="120.5",
                stderr=""
            )

            duration = await converter.get_video_duration(video_file)

            assert duration == 120.5

            # Verify ffprobe was called correctly
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert settings.FFPROBE_PATH in call_args
            assert str(video_file) in call_args

    @pytest.mark.asyncio
    async def test_get_video_duration_ffprobe_failure(self, temp_dir):
        """Test duration extraction when ffprobe fails"""
        converter = VideoConverter()

        video_file = temp_dir / "test.mp4"
        video_file.write_text("mock video")

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout="",
                stderr="Error: Invalid file"
            )

            duration = await converter.get_video_duration(video_file)

            assert duration == 0.0

    @pytest.mark.asyncio
    async def test_get_video_duration_invalid_output(self, temp_dir):
        """Test duration extraction with invalid output"""
        converter = VideoConverter()

        video_file = temp_dir / "test.mp4"
        video_file.write_text("mock video")

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="not_a_number",
                stderr=""
            )

            duration = await converter.get_video_duration(video_file)

            assert duration == 0.0


# ============================================================================
# PROGRESS PARSING TESTS
# ============================================================================

class TestProgressParsing:
    """Test FFmpeg progress parsing"""

    def test_parse_ffmpeg_progress_valid(self):
        """Test parsing valid FFmpeg progress output"""
        converter = VideoConverter()

        # Test various progress lines
        test_cases = [
            ("time=00:00:30.50", 120.0, 25.4),  # 30.5 / 120 * 100 = 25.4%
            ("time=00:01:00.00", 120.0, 50.0),  # 60 / 120 * 100 = 50%
            ("time=00:02:00.00", 120.0, 99.9),  # 120 / 120 * 100 = 100%, but capped at 99.9
        ]

        for line, total_duration, expected_progress in test_cases:
            progress = converter.parse_ffmpeg_progress(line, total_duration)
            assert progress is not None
            assert abs(progress - expected_progress) < 0.1  # Allow small floating point diff

    def test_parse_ffmpeg_progress_no_match(self):
        """Test parsing line without time pattern"""
        converter = VideoConverter()

        line = "frame=100 fps=30 bitrate=2000kbits/s"
        progress = converter.parse_ffmpeg_progress(line, 120.0)

        assert progress is None

    def test_parse_ffmpeg_progress_zero_duration(self):
        """Test parsing with zero duration"""
        converter = VideoConverter()

        line = "time=00:01:00.00"
        progress = converter.parse_ffmpeg_progress(line, 0.0)

        assert progress is None

    def test_parse_ffmpeg_progress_capped_at_99_9(self):
        """Test that progress is capped at 99.9%"""
        converter = VideoConverter()

        # Progress beyond 100%
        line = "time=00:03:00.00"  # 180 seconds
        progress = converter.parse_ffmpeg_progress(line, 120.0)  # Total 120 seconds

        assert progress == 99.9


# ============================================================================
# METADATA EXTRACTION TESTS
# ============================================================================

class TestVideoMetadata:
    """Test video metadata extraction"""

    @pytest.mark.asyncio
    async def test_get_video_metadata_success(self, temp_dir):
        """Test successful metadata extraction"""
        converter = VideoConverter()

        video_file = temp_dir / "test.mp4"
        video_file.write_text("mock video")

        with FFprobeMock.mock_video_with_audio_metadata():
            metadata = await converter.get_video_metadata(video_file)

            assert "duration" in metadata
            assert "width" in metadata
            assert "height" in metadata
            assert "video_codec" in metadata
            assert "audio_codec" in metadata
            assert metadata["width"] == 1920
            assert metadata["height"] == 1080

    @pytest.mark.asyncio
    async def test_get_video_metadata_no_audio_stream(self, temp_dir):
        """Test metadata extraction for video without audio"""
        converter = VideoConverter()

        video_file = temp_dir / "test.mp4"
        video_file.write_text("mock video")

        with FFprobeMock.mock_video_metadata():
            metadata = await converter.get_video_metadata(video_file)

            assert "audio_codec" in metadata
            assert metadata["audio_codec"] == ""  # No audio stream

    @pytest.mark.asyncio
    async def test_get_video_metadata_ffprobe_failure(self, temp_dir):
        """Test metadata extraction when ffprobe fails"""
        converter = VideoConverter()

        video_file = temp_dir / "test.mp4"
        video_file.write_text("mock video")

        with FFprobeMock.mock_failure():
            metadata = await converter.get_video_metadata(video_file)

            assert "error" in metadata
            assert metadata["error"] == "Failed to probe video"

    @pytest.mark.asyncio
    async def test_get_video_metadata_exception_during_processing(self, temp_dir):
        """Test metadata extraction when exception occurs during processing"""
        converter = VideoConverter()

        video_file = temp_dir / "test.mp4"
        video_file.write_text("mock video")

        # Mock subprocess.run to raise an exception
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Subprocess error")

            metadata = await converter.get_video_metadata(video_file)

            assert "error" in metadata
            assert "Subprocess error" in metadata["error"]

    def test_parse_fps_from_fraction(self):
        """Test FPS parsing from fraction string"""
        converter = VideoConverter()

        test_cases = [
            ("30/1", 30.0),
            ("30000/1001", 29.97),
            ("60/1", 60.0),
            ("0/1", 0.0),
        ]

        for fps_str, expected_fps in test_cases:
            fps = converter._parse_fps(fps_str)
            assert abs(fps - expected_fps) < 0.1

    def test_parse_fps_from_plain_number(self):
        """Test FPS parsing from plain number"""
        converter = VideoConverter()

        fps = converter._parse_fps("30.0")
        assert fps == 30.0

    def test_parse_fps_invalid_input(self):
        """Test FPS parsing with invalid input"""
        converter = VideoConverter()

        invalid_inputs = ["invalid", "30/0", "abc/def", ""]

        for fps_str in invalid_inputs:
            fps = converter._parse_fps(fps_str)
            assert fps == 0.0


# ============================================================================
# FORMAT VALIDATION TESTS
# ============================================================================

class TestFormatValidation:
    """Test format validation"""

    def test_validate_supported_input_formats(self):
        """Test that all supported input formats are validated"""
        converter = VideoConverter()

        supported_formats = ["mp4", "avi", "mov", "mkv", "webm", "flv"]

        for fmt in supported_formats:
            assert fmt in converter.supported_formats["input"]

    def test_validate_supported_output_formats(self):
        """Test that all supported output formats are validated"""
        converter = VideoConverter()

        supported_formats = ["mp4", "avi", "mov", "mkv", "webm"]

        for fmt in supported_formats:
            assert fmt in converter.supported_formats["output"]


# ============================================================================
# PROGRESS TRACKING TESTS
# ============================================================================

class TestProgressTracking:
    """Test WebSocket progress tracking"""

    @pytest.mark.asyncio
    async def test_progress_updates_sent(self, temp_dir, mock_websocket_manager):
        """Test that progress updates are sent during conversion"""
        converter = VideoConverter(mock_websocket_manager)

        input_file = temp_dir / "test.mp4"
        input_file.write_text("mock video")

        output_file = settings.UPLOAD_DIR / "test_converted.mp4"

        options = {"codec": "libx264", "resolution": "720p", "bitrate": "2M"}

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="120.0", stderr="")

            with FFmpegMock.mock_successful_conversion(output_file):
                await converter.convert(input_file, "mp4", options, "test-session")

                # Verify progress was sent
                assert mock_websocket_manager.send_progress.called
                calls = mock_websocket_manager.send_progress.call_args_list

                # Should have at least: start (0%), preparing (5%), start FFmpeg (10%), completed (100%)
                assert len(calls) >= 4

                # First call should be 0% starting
                first_call_args = calls[0].args if calls[0].args else calls[0].kwargs
                if isinstance(first_call_args, tuple):
                    assert first_call_args[1] == 0  # Progress 0%
                    assert first_call_args[2] == "converting"

                # Last call should be 100% completed
                last_call_args = calls[-1].args if calls[-1].args else calls[-1].kwargs
                if isinstance(last_call_args, tuple):
                    assert last_call_args[1] == 100  # Progress 100%
                    assert last_call_args[2] == "completed"

    @pytest.mark.asyncio
    async def test_progress_updates_on_failure(self, temp_dir, mock_websocket_manager):
        """Test that failure status is sent when conversion fails"""
        converter = VideoConverter(mock_websocket_manager)

        input_file = temp_dir / "test.mp4"
        input_file.write_text("mock video")

        options = {"codec": "libx264", "resolution": "720p", "bitrate": "2M"}

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="120.0", stderr="")

            with FFmpegMock.mock_failed_conversion("Test error"):
                with pytest.raises(Exception):
                    await converter.convert(input_file, "mp4", options, "test-session")

                # Verify failure status was sent
                calls = mock_websocket_manager.send_progress.call_args_list
                last_call_args = calls[-1].args if calls[-1].args else calls[-1].kwargs
                if isinstance(last_call_args, tuple):
                    assert last_call_args[2] == "failed"


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_output_file_not_created(self, temp_dir, mock_websocket_manager):
        """Test error when output file is not created by FFmpeg"""
        converter = VideoConverter(mock_websocket_manager)

        input_file = temp_dir / "test.mp4"
        input_file.write_text("mock video")

        options = {"codec": "libx264", "resolution": "720p", "bitrate": "2M"}

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="120.0", stderr="")

            # Mock FFmpeg success but don't create output file
            async def mock_proc_side_effect(*args, **kwargs):
                mock_process = AsyncMock()
                mock_process.returncode = 0
                mock_process.wait = AsyncMock(return_value=0)

                # Create proper empty async iterators
                async def stdout_iterator():
                    # Properly empty async generator - no items to yield
                    if False:
                        yield  # Makes this a generator but never executes

                mock_process.stdout = stdout_iterator()
                mock_process.stderr = AsyncMock()
                mock_process.stderr.read = AsyncMock(return_value=b'')

                # Mock communicate() to return (stdout, stderr) tuple
                mock_process.communicate = AsyncMock(return_value=(b'', b''))

                return mock_process

            with patch('asyncio.create_subprocess_exec', side_effect=mock_proc_side_effect):
                with pytest.raises(Exception) as exc_info:
                    await converter.convert(input_file, "mp4", options, "test-session")

                assert "Output file was not created" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_default_options_used_when_not_provided(self, temp_dir, mock_websocket_manager):
        """Test that default options are used when not provided"""
        converter = VideoConverter(mock_websocket_manager)

        input_file = temp_dir / "test.mp4"
        input_file.write_text("mock video")

        output_file = settings.UPLOAD_DIR / "test_converted.mp4"

        # Empty options - should use defaults
        options = {}

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="120.0", stderr="")

            with FFmpegMock.mock_successful_conversion(output_file):
                result = await converter.convert(input_file, "mp4", options, "test-session")

                # Should succeed with default codec (libx264), resolution (original), bitrate (2M)
                assert result.exists()
