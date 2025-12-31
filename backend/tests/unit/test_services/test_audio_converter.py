"""
Tests for app/services/audio_converter.py

COVERAGE GOAL: 85%+
Tests audio conversion with FFmpeg, codec selection, bitrate/sample rate options,
progress tracking, and metadata extraction
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import subprocess
import json

from app.services.audio_converter import AudioConverter
from app.config import settings


# ============================================================================
# BASIC FUNCTIONALITY TESTS
# ============================================================================

class TestAudioConverterBasics:
    """Test basic AudioConverter functionality"""

    def test_initialization(self):
        """Test AudioConverter initializes correctly"""
        converter = AudioConverter()

        assert converter.supported_formats is not None
        assert "input" in converter.supported_formats
        assert "output" in converter.supported_formats
        assert "mp3" in converter.supported_formats["input"]
        assert "wav" in converter.supported_formats["output"]
        assert converter.executor is not None

    def test_initialization_with_websocket_manager(self):
        """Test AudioConverter can be initialized with custom WebSocket manager"""
        mock_ws_manager = Mock()
        converter = AudioConverter(websocket_manager=mock_ws_manager)

        assert converter.websocket_manager == mock_ws_manager

    @pytest.mark.asyncio
    async def test_get_supported_formats(self):
        """Test getting supported audio formats"""
        converter = AudioConverter()

        formats = await converter.get_supported_formats()

        assert "input" in formats
        assert "output" in formats
        assert isinstance(formats["input"], list)
        assert isinstance(formats["output"], list)
        # Check common formats
        assert "mp3" in formats["output"]
        assert "wav" in formats["output"]
        assert "flac" in formats["output"]
        assert "aac" in formats["output"]


# ============================================================================
# AUDIO DURATION TESTS
# ============================================================================

class TestAudioDuration:
    """Test audio duration detection"""

    @pytest.mark.asyncio
    async def test_get_audio_duration_success(self, temp_dir):
        """Test successful audio duration retrieval"""
        converter = AudioConverter()
        test_file = temp_dir / "test.mp3"
        test_file.write_text("fake audio")

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="123.456\n"
            )

            duration = await converter.get_audio_duration(test_file)

            assert duration == 123.456
            mock_run.assert_called_once()
            # Verify ffprobe command
            call_args = mock_run.call_args[0][0]
            assert settings.FFPROBE_PATH in call_args
            assert str(test_file) in call_args
            assert "duration" in " ".join(call_args)

    @pytest.mark.asyncio
    async def test_get_audio_duration_error(self, temp_dir):
        """Test audio duration returns 0.0 on error"""
        converter = AudioConverter()
        test_file = temp_dir / "test.mp3"
        test_file.write_text("fake audio")

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout=""
            )

            duration = await converter.get_audio_duration(test_file)

            assert duration == 0.0

    @pytest.mark.asyncio
    async def test_get_audio_duration_exception(self, temp_dir):
        """Test audio duration handles exceptions gracefully"""
        converter = AudioConverter()
        test_file = temp_dir / "test.mp3"
        test_file.write_text("fake audio")

        with patch('subprocess.run', side_effect=Exception("FFprobe error")):
            duration = await converter.get_audio_duration(test_file)

            assert duration == 0.0


# ============================================================================
# PROGRESS PARSING TESTS
# ============================================================================

class TestProgressParsing:
    """Test FFmpeg progress parsing"""

    def test_parse_ffmpeg_progress_valid(self):
        """Test parsing valid FFmpeg progress output"""
        converter = AudioConverter()

        # Total duration: 100 seconds
        # Current time: 50 seconds = 50% progress
        line = "time=00:00:50.00 bitrate=192.0kbits/s"
        progress = converter.parse_ffmpeg_progress(line, 100.0)

        assert progress is not None
        assert progress == pytest.approx(50.0, abs=0.1)

    def test_parse_ffmpeg_progress_hours(self):
        """Test parsing progress with hours"""
        converter = AudioConverter()

        # Total duration: 7200 seconds (2 hours)
        # Current time: 1 hour = 3600 seconds = 50% progress
        line = "time=01:00:00.00 bitrate=192.0kbits/s"
        progress = converter.parse_ffmpeg_progress(line, 7200.0)

        assert progress is not None
        assert progress == pytest.approx(50.0, abs=0.1)

    def test_parse_ffmpeg_progress_99_cap(self):
        """Test progress is capped at 99.9%"""
        converter = AudioConverter()

        # Total duration: 100 seconds
        # Current time: 200 seconds (over 100%) - should cap at 99.9%
        line = "time=00:03:20.00 bitrate=192.0kbits/s"
        progress = converter.parse_ffmpeg_progress(line, 100.0)

        assert progress is not None
        assert progress == 99.9

    def test_parse_ffmpeg_progress_no_match(self):
        """Test parsing returns None when no time pattern found"""
        converter = AudioConverter()

        line = "Invalid output without time"
        progress = converter.parse_ffmpeg_progress(line, 100.0)

        assert progress is None

    def test_parse_ffmpeg_progress_zero_duration(self):
        """Test parsing returns None when total duration is 0"""
        converter = AudioConverter()

        line = "time=00:00:50.00 bitrate=192.0kbits/s"
        progress = converter.parse_ffmpeg_progress(line, 0.0)

        assert progress is None


# ============================================================================
# CODEC SELECTION TESTS
# ============================================================================

class TestCodecSelection:
    """Test audio codec selection"""

    def test_get_audio_codec_mp3(self):
        """Test codec selection for MP3"""
        converter = AudioConverter()

        codec = converter.get_audio_codec("mp3")

        assert codec == "libmp3lame"

    def test_get_audio_codec_aac(self):
        """Test codec selection for AAC"""
        converter = AudioConverter()

        codec = converter.get_audio_codec("aac")

        assert codec == "aac"

    def test_get_audio_codec_flac(self):
        """Test codec selection for FLAC"""
        converter = AudioConverter()

        codec = converter.get_audio_codec("flac")

        assert codec == "flac"

    def test_get_audio_codec_wav(self):
        """Test codec selection for WAV"""
        converter = AudioConverter()

        codec = converter.get_audio_codec("wav")

        assert codec == "pcm_s16le"

    def test_get_audio_codec_ogg(self):
        """Test codec selection for OGG"""
        converter = AudioConverter()

        codec = converter.get_audio_codec("ogg")

        assert codec == "libvorbis"

    def test_get_audio_codec_custom_override(self):
        """Test custom codec override"""
        converter = AudioConverter()

        codec = converter.get_audio_codec("mp3", codec="libshine")

        assert codec == "libshine"

    def test_get_audio_codec_unknown_format(self):
        """Test codec selection for unknown format defaults to libmp3lame"""
        converter = AudioConverter()

        codec = converter.get_audio_codec("xyz")

        assert codec == "libmp3lame"


# ============================================================================
# CONVERSION TESTS
# ============================================================================

class TestAudioConversion:
    """Test audio conversion functionality"""

    @pytest.mark.asyncio
    async def test_convert_mp3_to_wav_success(self, temp_dir):
        """Test successful audio conversion"""
        converter = AudioConverter()

        input_file = temp_dir / "test.mp3"
        input_file.write_text("fake mp3 audio")

        output_file = settings.UPLOAD_DIR / "test_converted.wav"

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            with patch.object(converter, 'get_audio_duration', return_value=100.0):
                with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                    # Mock FFmpeg process
                    mock_process = AsyncMock()
                    mock_process.returncode = 0
                    mock_process.stdout = AsyncMock()
                    mock_process.stdout.__aiter__.return_value = iter([
                        b"time=00:00:50.00 bitrate=192.0kbits/s\n"
                    ])
                    mock_process.stderr = AsyncMock()
                    mock_process.wait = AsyncMock()
                    mock_subprocess.return_value = mock_process

                    # Create fake output file
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("converted audio")

                    result = await converter.convert(
                        input_path=input_file,
                        output_format="wav",
                        options={},
                        session_id="test-session"
                    )

                    assert result == output_file
                    assert output_file.exists()

                    # Verify progress was sent
                    assert mock_progress.call_count >= 4  # Start, prepare, converting, complete

                    # Verify FFmpeg command
                    mock_subprocess.assert_called_once()
                    call_args = mock_subprocess.call_args[0]
                    assert settings.FFMPEG_PATH in call_args
                    assert "-i" in call_args
                    assert "-c:a" in call_args

    @pytest.mark.asyncio
    async def test_convert_with_bitrate_option(self, temp_dir):
        """Test conversion with bitrate option"""
        converter = AudioConverter()

        input_file = temp_dir / "test.mp3"
        input_file.write_text("fake audio")

        output_file = settings.UPLOAD_DIR / "test_converted.mp3"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch.object(converter, 'get_audio_duration', return_value=100.0):
                with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                    mock_process = AsyncMock()
                    mock_process.returncode = 0
                    mock_process.stdout = AsyncMock()
                    mock_process.stdout.__aiter__.return_value = iter([])
                    mock_process.stderr = AsyncMock()
                    mock_process.wait = AsyncMock()
                    mock_subprocess.return_value = mock_process

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("converted")

                    await converter.convert(
                        input_path=input_file,
                        output_format="mp3",
                        options={"bitrate": "320k"},
                        session_id="test-session"
                    )

                    # Verify bitrate in FFmpeg command
                    call_args = mock_subprocess.call_args[0]
                    assert "-b:a" in call_args
                    assert "320k" in call_args

    @pytest.mark.asyncio
    async def test_convert_lossless_no_bitrate(self, temp_dir):
        """Test conversion to lossless format (FLAC) doesn't add bitrate"""
        converter = AudioConverter()

        input_file = temp_dir / "test.mp3"
        input_file.write_text("fake audio")

        output_file = settings.UPLOAD_DIR / "test_converted.flac"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch.object(converter, 'get_audio_duration', return_value=100.0):
                with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                    mock_process = AsyncMock()
                    mock_process.returncode = 0
                    mock_process.stdout = AsyncMock()
                    mock_process.stdout.__aiter__.return_value = iter([])
                    mock_process.stderr = AsyncMock()
                    mock_process.wait = AsyncMock()
                    mock_subprocess.return_value = mock_process

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("converted")

                    await converter.convert(
                        input_path=input_file,
                        output_format="flac",
                        options={"bitrate": "320k"},  # Should be ignored
                        session_id="test-session"
                    )

                    # Verify bitrate NOT in FFmpeg command for FLAC
                    call_args = mock_subprocess.call_args[0]
                    # -b:a should not be present for lossless formats
                    if "-b:a" in call_args:
                        # Find index and verify it's not followed by our bitrate
                        pytest.fail("Bitrate should not be applied to FLAC")

    @pytest.mark.asyncio
    async def test_convert_with_sample_rate(self, temp_dir):
        """Test conversion with sample rate option"""
        converter = AudioConverter()

        input_file = temp_dir / "test.mp3"
        input_file.write_text("fake audio")

        output_file = settings.UPLOAD_DIR / "test_converted.mp3"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch.object(converter, 'get_audio_duration', return_value=100.0):
                with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                    mock_process = AsyncMock()
                    mock_process.returncode = 0
                    mock_process.stdout = AsyncMock()
                    mock_process.stdout.__aiter__.return_value = iter([])
                    mock_process.stderr = AsyncMock()
                    mock_process.wait = AsyncMock()
                    mock_subprocess.return_value = mock_process

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("converted")

                    await converter.convert(
                        input_path=input_file,
                        output_format="mp3",
                        options={"sample_rate": 44100},
                        session_id="test-session"
                    )

                    # Verify sample rate in FFmpeg command
                    call_args = mock_subprocess.call_args[0]
                    assert "-ar" in call_args
                    assert "44100" in call_args

    @pytest.mark.asyncio
    async def test_convert_with_channels(self, temp_dir):
        """Test conversion with channel option (mono/stereo)"""
        converter = AudioConverter()

        input_file = temp_dir / "test.mp3"
        input_file.write_text("fake audio")

        output_file = settings.UPLOAD_DIR / "test_converted.mp3"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch.object(converter, 'get_audio_duration', return_value=100.0):
                with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                    mock_process = AsyncMock()
                    mock_process.returncode = 0
                    mock_process.stdout = AsyncMock()
                    mock_process.stdout.__aiter__.return_value = iter([])
                    mock_process.stderr = AsyncMock()
                    mock_process.wait = AsyncMock()
                    mock_subprocess.return_value = mock_process

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("converted")

                    await converter.convert(
                        input_path=input_file,
                        output_format="mp3",
                        options={"channels": 1},  # Mono
                        session_id="test-session"
                    )

                    # Verify channels in FFmpeg command
                    call_args = mock_subprocess.call_args[0]
                    assert "-ac" in call_args
                    assert "1" in call_args

    @pytest.mark.asyncio
    async def test_convert_unsupported_format_raises_error(self, temp_dir):
        """Test conversion with unsupported format raises ValueError"""
        converter = AudioConverter()

        input_file = temp_dir / "test.exe"
        input_file.write_text("not audio")

        with pytest.raises(ValueError, match="Unsupported conversion"):
            await converter.convert(
                input_path=input_file,
                output_format="mp3",
                options={},
                session_id="test-session"
            )

    @pytest.mark.asyncio
    async def test_convert_ffmpeg_error_raises_exception(self, temp_dir):
        """Test conversion handles FFmpeg errors"""
        converter = AudioConverter()

        input_file = temp_dir / "test.mp3"
        input_file.write_text("fake audio")

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            with patch.object(converter, 'get_audio_duration', return_value=100.0):
                with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                    # Mock failed FFmpeg process
                    mock_process = AsyncMock()
                    mock_process.returncode = 1
                    mock_process.stdout = AsyncMock()
                    mock_process.stdout.__aiter__.return_value = iter([])
                    mock_process.stderr = AsyncMock()
                    mock_process.stderr.read = AsyncMock(return_value=b"FFmpeg error: invalid codec")
                    mock_process.wait = AsyncMock()
                    mock_subprocess.return_value = mock_process

                    with pytest.raises(Exception, match="FFmpeg conversion failed"):
                        await converter.convert(
                            input_path=input_file,
                            output_format="mp3",
                            options={},
                            session_id="test-session"
                        )

                    # Verify failure progress was sent
                    last_call = mock_progress.call_args_list[-1]
                    assert "failed" in str(last_call)

    @pytest.mark.asyncio
    async def test_convert_output_file_missing_raises_exception(self, temp_dir):
        """Test conversion raises exception when output file not created"""
        converter = AudioConverter()

        input_file = temp_dir / "test.mp3"
        input_file.write_text("fake audio")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch.object(converter, 'get_audio_duration', return_value=100.0):
                with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                    mock_process = AsyncMock()
                    mock_process.returncode = 0
                    mock_process.stdout = AsyncMock()
                    mock_process.stdout.__aiter__.return_value = iter([])
                    mock_process.stderr = AsyncMock()
                    mock_process.wait = AsyncMock()
                    mock_subprocess.return_value = mock_process

                    # Don't create output file

                    with pytest.raises(Exception, match="Output file was not created"):
                        await converter.convert(
                            input_path=input_file,
                            output_format="mp3",
                            options={},
                            session_id="test-session"
                        )


# ============================================================================
# METADATA EXTRACTION TESTS
# ============================================================================

class TestAudioMetadata:
    """Test audio metadata extraction"""

    @pytest.mark.asyncio
    async def test_get_audio_metadata_success(self, temp_dir):
        """Test successful metadata extraction"""
        converter = AudioConverter()

        test_file = temp_dir / "test.mp3"
        test_file.write_text("fake audio")

        mock_metadata = {
            "format": {
                "duration": "245.67",
                "size": "1234567",
                "format_name": "mp3",
                "bit_rate": "192000"
            },
            "streams": [
                {
                    "codec_type": "audio",
                    "codec_name": "mp3",
                    "sample_rate": "44100",
                    "channels": 2,
                    "channel_layout": "stereo"
                }
            ]
        }

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=json.dumps(mock_metadata)
            )

            metadata = await converter.get_audio_metadata(test_file)

            assert metadata["duration"] == 245.67
            assert metadata["size"] == 1234567
            assert metadata["format"] == "mp3"
            assert metadata["codec"] == "mp3"
            assert metadata["sample_rate"] == 44100
            assert metadata["channels"] == 2
            assert metadata["bitrate"] == 192000
            assert metadata["channel_layout"] == "stereo"

    @pytest.mark.asyncio
    async def test_get_audio_metadata_ffprobe_error(self, temp_dir):
        """Test metadata extraction handles ffprobe errors"""
        converter = AudioConverter()

        test_file = temp_dir / "test.mp3"
        test_file.write_text("fake audio")

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout=""
            )

            metadata = await converter.get_audio_metadata(test_file)

            assert "error" in metadata
            assert metadata["error"] == "Failed to probe audio"

    @pytest.mark.asyncio
    async def test_get_audio_metadata_exception(self, temp_dir):
        """Test metadata extraction handles exceptions"""
        converter = AudioConverter()

        test_file = temp_dir / "test.mp3"
        test_file.write_text("fake audio")

        with patch('subprocess.run', side_effect=Exception("FFprobe crashed")):
            metadata = await converter.get_audio_metadata(test_file)

            assert "error" in metadata
            assert "FFprobe crashed" in metadata["error"]

    @pytest.mark.asyncio
    async def test_get_audio_metadata_no_audio_stream(self, temp_dir):
        """Test metadata extraction handles files without audio stream"""
        converter = AudioConverter()

        test_file = temp_dir / "test.mp4"
        test_file.write_text("fake video")

        mock_metadata = {
            "format": {
                "duration": "100.0",
                "size": "1000000",
                "format_name": "mp4"
            },
            "streams": [
                {
                    "codec_type": "video",  # No audio stream
                    "codec_name": "h264"
                }
            ]
        }

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=json.dumps(mock_metadata)
            )

            metadata = await converter.get_audio_metadata(test_file)

            # Should return empty values for audio-specific fields
            assert metadata["codec"] == ""
            assert metadata["sample_rate"] == 0
            assert metadata["channels"] == 0
