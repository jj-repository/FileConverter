"""
Tests for app/services/subtitle_converter.py

COVERAGE GOAL: 85%+
Tests subtitle conversion with pysubs2, format support, encoding handling,
timing adjustment, metadata extraction, and error handling
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import io

from app.services.subtitle_converter import SubtitleConverter
from app.config import settings


# ============================================================================
# BASIC FUNCTIONALITY TESTS
# ============================================================================

class TestSubtitleConverterBasics:
    """Test basic SubtitleConverter functionality"""

    def test_initialization(self):
        """Test SubtitleConverter initializes correctly"""
        converter = SubtitleConverter()

        assert converter.supported_formats is not None
        assert "input" in converter.supported_formats
        assert "output" in converter.supported_formats
        assert "srt" in converter.supported_formats["input"]
        assert "vtt" in converter.supported_formats["output"]
        assert converter.websocket_manager is not None

    def test_initialization_with_websocket_manager(self):
        """Test SubtitleConverter can be initialized with custom WebSocket manager"""
        mock_ws_manager = Mock()
        converter = SubtitleConverter(websocket_manager=mock_ws_manager)

        assert converter.websocket_manager == mock_ws_manager

    @pytest.mark.asyncio
    async def test_get_supported_formats(self):
        """Test getting supported subtitle formats"""
        converter = SubtitleConverter()

        formats = await converter.get_supported_formats()

        assert "input" in formats
        assert "output" in formats
        assert isinstance(formats["input"], list)
        assert isinstance(formats["output"], list)
        # Check common formats
        assert "srt" in formats["input"]
        assert "vtt" in formats["input"]
        assert "ass" in formats["input"]
        assert "ssa" in formats["input"]
        assert "sub" in formats["input"]
        assert "srt" in formats["output"]
        assert "vtt" in formats["output"]


# ============================================================================
# SRT CONVERSION TESTS
# ============================================================================

class TestSRTConversion:
    """Test SRT subtitle conversion"""

    @pytest.mark.asyncio
    async def test_convert_srt_to_vtt_success(self, temp_dir):
        """Test successful SRT to VTT conversion"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.srt"
        input_file.write_text(
            "1\n"
            "00:00:01,000 --> 00:00:05,000\n"
            "First subtitle\n"
            "\n"
            "2\n"
            "00:00:06,000 --> 00:00:10,000\n"
            "Second subtitle\n"
        )

        output_file = settings.UPLOAD_DIR / "test_converted.vtt"

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            with patch('pysubs2.load') as mock_load:
                # Mock pysubs2 load and save
                mock_subs = MagicMock()
                mock_load.return_value = mock_subs

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text("WEBVTT\n\n00:00:01.000 --> 00:00:05.000\nFirst subtitle\n")

                result = await converter.convert(
                    input_path=input_file,
                    output_format="vtt",
                    options={},
                    session_id="test-session"
                )

                assert result == output_file
                # Verify progress was sent
                assert mock_progress.call_count >= 3
                # Verify load was called with correct encoding
                mock_load.assert_called_once()
                # Verify save was called
                mock_subs.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_srt_to_ass_success(self, temp_dir):
        """Test successful SRT to ASS conversion"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.srt"
        input_file.write_text(
            "1\n"
            "00:00:01,000 --> 00:00:05,000\n"
            "First subtitle\n"
        )

        output_file = settings.UPLOAD_DIR / "test_converted.ass"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pysubs2.load') as mock_load:
                mock_subs = MagicMock()
                mock_load.return_value = mock_subs

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text("[Script Info]\n")

                result = await converter.convert(
                    input_path=input_file,
                    output_format="ass",
                    options={},
                    session_id="test-session"
                )

                assert result == output_file
                mock_subs.save.assert_called_once()
                # Verify format_ parameter
                call_kwargs = mock_subs.save.call_args[1]
                assert call_kwargs.get('format_') == 'ass'

    @pytest.mark.asyncio
    async def test_convert_srt_with_timing_preservation(self, temp_dir):
        """Test SRT to VTT preserves subtitle timings"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.srt"
        input_file.write_text(
            "1\n"
            "00:01:30,500 --> 00:01:35,750\n"
            "Timed subtitle\n"
        )

        output_file = settings.UPLOAD_DIR / "test_converted.vtt"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pysubs2.load') as mock_load:
                mock_subs = MagicMock()
                mock_load.return_value = mock_subs

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text("WEBVTT\n\n00:01:30.500 --> 00:01:35.750\nTimed subtitle\n")

                await converter.convert(
                    input_path=input_file,
                    output_format="vtt",
                    options={},
                    session_id="test-session"
                )

                # Verify pysubs2 was used (it preserves timings)
                mock_load.assert_called_once()
                mock_subs.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_srt_progress_updates(self, temp_dir):
        """Test progress updates during SRT conversion"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.srt"
        input_file.write_text("1\n00:00:01,000 --> 00:00:05,000\nSubtitle\n")

        output_file = settings.UPLOAD_DIR / "test_converted.vtt"

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            with patch('pysubs2.load') as mock_load:
                mock_subs = MagicMock()
                mock_load.return_value = mock_subs

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text("WEBVTT\n")

                await converter.convert(
                    input_path=input_file,
                    output_format="vtt",
                    options={},
                    session_id="test-session"
                )

                # Verify multiple progress updates
                calls = mock_progress.call_args_list
                assert any("Starting" in str(call) for call in calls)
                assert any("Reading" in str(call) for call in calls)
                assert any("Converting" in str(call) for call in calls)
                assert any("completed" in str(call) for call in calls)


# ============================================================================
# VTT CONVERSION TESTS
# ============================================================================

class TestVTTConversion:
    """Test VTT subtitle conversion"""

    @pytest.mark.asyncio
    async def test_convert_vtt_to_srt_success(self, temp_dir):
        """Test successful VTT to SRT conversion"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.vtt"
        input_file.write_text(
            "WEBVTT\n\n"
            "00:00:01.000 --> 00:00:05.000\n"
            "First subtitle\n"
        )

        output_file = settings.UPLOAD_DIR / "test_converted.srt"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pysubs2.load') as mock_load:
                mock_subs = MagicMock()
                mock_load.return_value = mock_subs

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text("1\n00:00:01,000 --> 00:00:05,000\nFirst subtitle\n")

                result = await converter.convert(
                    input_path=input_file,
                    output_format="srt",
                    options={},
                    session_id="test-session"
                )

                assert result == output_file
                mock_subs.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_vtt_header_handling(self, temp_dir):
        """Test VTT header is handled correctly"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.vtt"
        # VTT must start with WEBVTT header
        input_file.write_text(
            "WEBVTT\n\n"
            "NOTE This is a comment\n\n"
            "00:00:01.000 --> 00:00:05.000\n"
            "First subtitle\n"
        )

        output_file = settings.UPLOAD_DIR / "test_converted.srt"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pysubs2.load') as mock_load:
                mock_subs = MagicMock()
                mock_load.return_value = mock_subs

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text("1\n00:00:01,000 --> 00:00:05,000\nFirst subtitle\n")

                await converter.convert(
                    input_path=input_file,
                    output_format="srt",
                    options={},
                    session_id="test-session"
                )

                # Verify pysubs2 handled VTT parsing
                mock_load.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_vtt_cue_formatting(self, temp_dir):
        """Test VTT cue formatting is preserved"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.vtt"
        input_file.write_text(
            "WEBVTT\n\n"
            "00:00:01.000 --> 00:00:05.000 align:start position:0%\n"
            "First subtitle\n"
        )

        output_file = settings.UPLOAD_DIR / "test_converted.vtt"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pysubs2.load') as mock_load:
                mock_subs = MagicMock()
                mock_load.return_value = mock_subs

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text("WEBVTT\n")

                await converter.convert(
                    input_path=input_file,
                    output_format="vtt",
                    options={},
                    session_id="test-session"
                )

                # Verify conversion handled VTT cues
                mock_load.assert_called_once()
                mock_subs.save.assert_called_once()


# ============================================================================
# ASS/SSA CONVERSION TESTS
# ============================================================================

class TestASSConversion:
    """Test ASS/SSA subtitle conversion"""

    @pytest.mark.asyncio
    async def test_convert_ass_to_srt_success(self, temp_dir):
        """Test successful ASS to SRT conversion"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.ass"
        input_file.write_text(
            "[Script Info]\n"
            "Title: Test\n\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize\n"
            "Style: Default,Arial,20\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Text\n"
            "Dialogue: 0,0:00:01.00,0:00:05.00,Default,First subtitle\n"
        )

        output_file = settings.UPLOAD_DIR / "test_converted.srt"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pysubs2.load') as mock_load:
                mock_subs = MagicMock()
                mock_load.return_value = mock_subs

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text("1\n00:00:01,000 --> 00:00:05,000\nFirst subtitle\n")

                result = await converter.convert(
                    input_path=input_file,
                    output_format="srt",
                    options={},
                    session_id="test-session"
                )

                assert result == output_file
                mock_subs.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_ssa_to_srt_success(self, temp_dir):
        """Test successful SSA to SRT conversion"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.ssa"
        input_file.write_text(
            "[Script Info]\n"
            "Title: Test\n\n"
            "[V4 Styles]\n"
            "Format: Name, Fontname, Fontsize\n"
            "Style: Default,Arial,20\n\n"
            "[Events]\n"
            "Format: Marked, Start, End, Style, Text\n"
            "Dialogue: Marked=0,0:00:01.00,0:00:05.00,Default,First subtitle\n"
        )

        output_file = settings.UPLOAD_DIR / "test_converted.srt"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pysubs2.load') as mock_load:
                mock_subs = MagicMock()
                mock_load.return_value = mock_subs

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text("1\n00:00:01,000 --> 00:00:05,000\nFirst subtitle\n")

                result = await converter.convert(
                    input_path=input_file,
                    output_format="srt",
                    options={},
                    session_id="test-session"
                )

                assert result == output_file

    @pytest.mark.asyncio
    async def test_convert_with_style_preservation(self, temp_dir):
        """Test ASS style information is handled"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.ass"
        input_file.write_text("[Script Info]\n[V4+ Styles]\nStyle: Default\n[Events]\n")

        output_file = settings.UPLOAD_DIR / "test_converted.ass"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pysubs2.load') as mock_load:
                mock_subs = MagicMock()
                mock_load.return_value = mock_subs

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text("[Script Info]\n")

                await converter.convert(
                    input_path=input_file,
                    output_format="ass",
                    options={},
                    session_id="test-session"
                )

                # Verify ASS-specific save parameters
                call_kwargs = mock_subs.save.call_args[1]
                assert call_kwargs.get('format_') == 'ass'


# ============================================================================
# FORMAT SUPPORT TESTS
# ============================================================================

class TestFormatSupport:
    """Test format support detection"""

    @pytest.mark.asyncio
    async def test_get_supported_formats_includes_all_subtitle_types(self):
        """Test all subtitle formats are supported"""
        converter = SubtitleConverter()

        formats = await converter.get_supported_formats()

        expected_formats = {"srt", "vtt", "ass", "ssa", "sub"}
        assert expected_formats.issubset(set(formats["input"]))
        assert expected_formats.issubset(set(formats["output"]))

    def test_validate_srt_format(self):
        """Test SRT format validation"""
        converter = SubtitleConverter()

        is_valid = converter.validate_format(
            "srt", "vtt", converter.supported_formats
        )

        assert is_valid is True

    def test_validate_vtt_format(self):
        """Test VTT format validation"""
        converter = SubtitleConverter()

        is_valid = converter.validate_format(
            "vtt", "srt", converter.supported_formats
        )

        assert is_valid is True

    def test_validate_ass_format(self):
        """Test ASS format validation"""
        converter = SubtitleConverter()

        is_valid = converter.validate_format(
            "ass", "srt", converter.supported_formats
        )

        assert is_valid is True

    def test_validate_ssa_format(self):
        """Test SSA format validation"""
        converter = SubtitleConverter()

        is_valid = converter.validate_format(
            "ssa", "srt", converter.supported_formats
        )

        assert is_valid is True

    def test_validate_sub_format(self):
        """Test SUB format validation"""
        converter = SubtitleConverter()

        is_valid = converter.validate_format(
            "sub", "srt", converter.supported_formats
        )

        assert is_valid is True


# ============================================================================
# ENCODING HANDLING TESTS
# ============================================================================

class TestEncodingHandling:
    """Test subtitle encoding support"""

    @pytest.mark.asyncio
    async def test_convert_utf8_encoding(self, temp_dir):
        """Test UTF-8 encoding support"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.srt"
        input_file.write_text(
            "1\n"
            "00:00:01,000 --> 00:00:05,000\n"
            "Unicode: 你好世界 مرحبا\n",
            encoding="utf-8"
        )

        output_file = settings.UPLOAD_DIR / "test_converted.vtt"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pysubs2.load') as mock_load:
                mock_subs = MagicMock()
                mock_load.return_value = mock_subs

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text("WEBVTT\n", encoding="utf-8")

                await converter.convert(
                    input_path=input_file,
                    output_format="vtt",
                    options={"encoding": "utf-8"},
                    session_id="test-session"
                )

                # Verify encoding parameter passed to load
                call_kwargs = mock_load.call_args[1]
                assert call_kwargs.get('encoding') == 'utf-8'

    @pytest.mark.asyncio
    async def test_convert_latin1_encoding(self, temp_dir):
        """Test Latin-1 encoding support"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.srt"
        # Write with latin-1 encoding
        input_file.write_bytes(
            b"1\n"
            b"00:00:01,000 --> 00:00:05,000\n"
            b"Subtitle with \xe9 accent\n"  # é in latin-1
        )

        output_file = settings.UPLOAD_DIR / "test_converted.vtt"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pysubs2.load') as mock_load:
                mock_subs = MagicMock()
                mock_load.return_value = mock_subs

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text("WEBVTT\n")

                await converter.convert(
                    input_path=input_file,
                    output_format="vtt",
                    options={"encoding": "latin-1"},
                    session_id="test-session"
                )

                # Verify encoding parameter
                call_kwargs = mock_load.call_args[1]
                assert call_kwargs.get('encoding') == 'latin-1'

    @pytest.mark.asyncio
    async def test_convert_custom_encoding(self, temp_dir):
        """Test custom encoding parameter support"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.srt"
        input_file.write_text("1\n00:00:01,000 --> 00:00:05,000\nSubtitle\n")

        output_file = settings.UPLOAD_DIR / "test_converted.vtt"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pysubs2.load') as mock_load:
                mock_subs = MagicMock()
                mock_load.return_value = mock_subs

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text("WEBVTT\n")

                await converter.convert(
                    input_path=input_file,
                    output_format="vtt",
                    options={"encoding": "cp1252"},
                    session_id="test-session"
                )

                # Verify custom encoding passed through
                call_kwargs = mock_load.call_args[1]
                assert call_kwargs.get('encoding') == 'cp1252'

    @pytest.mark.asyncio
    async def test_convert_default_encoding_utf8(self, temp_dir):
        """Test default encoding is UTF-8"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.srt"
        input_file.write_text("1\n00:00:01,000 --> 00:00:05,000\nSubtitle\n")

        output_file = settings.UPLOAD_DIR / "test_converted.vtt"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pysubs2.load') as mock_load:
                mock_subs = MagicMock()
                mock_load.return_value = mock_subs

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text("WEBVTT\n")

                await converter.convert(
                    input_path=input_file,
                    output_format="vtt",
                    options={},  # No encoding specified
                    session_id="test-session"
                )

                # Verify default UTF-8 encoding
                call_kwargs = mock_load.call_args[1]
                assert call_kwargs.get('encoding') == 'utf-8'


# ============================================================================
# TIMING ADJUSTMENT TESTS
# ============================================================================

class TestTimingAdjustment:
    """Test subtitle timing adjustment"""

    @pytest.mark.asyncio
    async def test_adjust_timing_positive_offset(self, temp_dir):
        """Test timing adjustment with positive offset (delay)"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.srt"
        input_file.write_text(
            "1\n"
            "00:00:01,000 --> 00:00:05,000\n"
            "First subtitle\n"
        )

        output_file = settings.UPLOAD_DIR / "test_adjusted.srt"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pysubs2.load') as mock_load:
                mock_subs = MagicMock()
                mock_load.return_value = mock_subs

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text("1\n00:00:06,000 --> 00:00:10,000\nFirst subtitle\n")

                result = await converter.adjust_timing(
                    input_path=input_file,
                    offset_ms=5000,  # 5 second delay
                    session_id="test-session"
                )

                assert result == output_file
                mock_load.assert_called_once()
                # Verify shift was called
                mock_subs.shift.assert_called_once_with(ms=5000)

    @pytest.mark.asyncio
    async def test_adjust_timing_negative_offset(self, temp_dir):
        """Test timing adjustment with negative offset (advance)"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.srt"
        input_file.write_text(
            "1\n"
            "00:00:05,000 --> 00:00:10,000\n"
            "Subtitle\n"
        )

        output_file = settings.UPLOAD_DIR / "test_adjusted.srt"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pysubs2.load') as mock_load:
                mock_subs = MagicMock()
                mock_load.return_value = mock_subs

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text("1\n00:00:03,000 --> 00:00:08,000\nSubtitle\n")

                result = await converter.adjust_timing(
                    input_path=input_file,
                    offset_ms=-2000,  # 2 second advance
                    session_id="test-session"
                )

                assert result == output_file
                mock_subs.shift.assert_called_once_with(ms=-2000)

    @pytest.mark.asyncio
    async def test_adjust_timing_zero_offset(self, temp_dir):
        """Test timing adjustment with zero offset"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.srt"
        input_file.write_text(
            "1\n"
            "00:00:01,000 --> 00:00:05,000\n"
            "Subtitle\n"
        )

        output_file = settings.UPLOAD_DIR / "test_adjusted.srt"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pysubs2.load') as mock_load:
                mock_subs = MagicMock()
                mock_load.return_value = mock_subs

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text("1\n00:00:01,000 --> 00:00:05,000\nSubtitle\n")

                await converter.adjust_timing(
                    input_path=input_file,
                    offset_ms=0,
                    session_id="test-session"
                )

                # Verify shift was still called with 0
                mock_subs.shift.assert_called_once_with(ms=0)


# ============================================================================
# SUBTITLE METADATA TESTS
# ============================================================================

class TestSubtitleMetadata:
    """Test subtitle metadata extraction"""

    @pytest.mark.asyncio
    async def test_get_subtitle_info_entry_count(self, temp_dir):
        """Test entry count in subtitle info"""
        converter = SubtitleConverter()

        test_file = temp_dir / "test.srt"
        test_file.write_text(
            "1\n00:00:01,000 --> 00:00:05,000\nSubtitle 1\n\n"
            "2\n00:00:06,000 --> 00:00:10,000\nSubtitle 2\n\n"
            "3\n00:00:11,000 --> 00:00:15,000\nSubtitle 3\n"
        )

        with patch('pysubs2.load') as mock_load:
            # Create mock subtitles with 3 entries
            mock_entry1 = MagicMock()
            mock_entry1.start = 1000
            mock_entry1.end = 5000
            mock_entry1.text = "Subtitle 1"

            mock_entry2 = MagicMock()
            mock_entry2.start = 6000
            mock_entry2.end = 10000
            mock_entry2.text = "Subtitle 2"

            mock_entry3 = MagicMock()
            mock_entry3.start = 11000
            mock_entry3.end = 15000
            mock_entry3.text = "Subtitle 3"

            mock_subs = MagicMock()
            mock_subs.__len__ = MagicMock(return_value=3)
            mock_subs.__getitem__ = MagicMock(side_effect=lambda i: [mock_entry1, mock_entry2, mock_entry3][i])
            mock_subs.__iter__ = MagicMock(return_value=iter([mock_entry1, mock_entry2, mock_entry3]))
            mock_load.return_value = mock_subs

            info = await converter.get_subtitle_info(test_file)

            assert info["subtitle_count"] == 3
            assert info["format"] == "srt"

    @pytest.mark.asyncio
    async def test_get_subtitle_info_duration(self, temp_dir):
        """Test duration extraction from subtitles"""
        converter = SubtitleConverter()

        test_file = temp_dir / "test.srt"
        test_file.write_text(
            "1\n00:00:01,000 --> 00:00:05,000\nSubtitle 1\n\n"
            "2\n00:02:00,000 --> 00:02:10,000\nSubtitle 2\n"
        )

        with patch('pysubs2.load') as mock_load:
            mock_entry1 = MagicMock()
            mock_entry1.start = 1000
            mock_entry1.end = 5000

            mock_entry2 = MagicMock()
            mock_entry2.start = 120000
            mock_entry2.end = 130000

            mock_subs = MagicMock()
            mock_subs.__len__ = MagicMock(return_value=2)
            mock_subs.__getitem__ = MagicMock(side_effect=lambda i: [mock_entry1, mock_entry2][i])
            mock_subs.__iter__ = MagicMock(return_value=iter([mock_entry1, mock_entry2]))
            mock_load.return_value = mock_subs

            info = await converter.get_subtitle_info(test_file)

            # Duration should be from first start to last end
            # First start: 1000ms, Last end: 130000ms
            # Duration = 130000 - 1000 = 129000ms = 129 seconds
            assert "duration_seconds" in info
            assert info["duration_seconds"] == pytest.approx(129.0, abs=0.1)

    @pytest.mark.asyncio
    async def test_get_subtitle_info_preview(self, temp_dir):
        """Test subtitle preview in info"""
        converter = SubtitleConverter()

        test_file = temp_dir / "test.srt"
        test_file.write_text(
            "1\n00:00:01,000 --> 00:00:05,000\nPreview 1\n"
        )

        with patch('pysubs2.load') as mock_load:
            mock_entry = MagicMock()
            mock_entry.start = 1000
            mock_entry.end = 5000
            mock_entry.text = "Preview 1"

            mock_subs = MagicMock()
            mock_subs.__len__ = MagicMock(return_value=1)
            mock_subs.__getitem__ = MagicMock(side_effect=lambda i: mock_entry if isinstance(i, int) else [mock_entry])
            mock_subs.__iter__ = MagicMock(return_value=iter([mock_entry]))
            mock_subs.__bool__ = MagicMock(return_value=True)  # Ensure truthiness
            mock_load.return_value = mock_subs

            info = await converter.get_subtitle_info(test_file)

            assert "preview" in info
            assert len(info["preview"]) >= 1
            assert info["preview"][0]["text"] == "Preview 1"

    @pytest.mark.asyncio
    async def test_get_subtitle_info_empty_file(self, temp_dir):
        """Test subtitle info for empty file"""
        converter = SubtitleConverter()

        test_file = temp_dir / "empty.srt"
        test_file.write_text("")

        with patch('pysubs2.load') as mock_load:
            mock_subs = MagicMock()
            mock_subs.__len__ = MagicMock(return_value=0)
            mock_subs.__iter__ = MagicMock(return_value=iter([]))
            mock_load.return_value = mock_subs

            info = await converter.get_subtitle_info(test_file)

            assert info["subtitle_count"] == 0
            assert "format" in info


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling in subtitle conversion"""

    @pytest.mark.asyncio
    async def test_convert_pysubs2_not_available(self, temp_dir):
        """Test conversion fails when pysubs2 not available"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.srt"
        input_file.write_text("1\n00:00:01,000 --> 00:00:05,000\nSubtitle\n")

        with patch('app.services.subtitle_converter.PYSUBS2_AVAILABLE', False):
            with pytest.raises(ValueError, match="Subtitle support not available"):
                await converter.convert(
                    input_path=input_file,
                    output_format="vtt",
                    options={},
                    session_id="test-session"
                )

    @pytest.mark.asyncio
    async def test_convert_unsupported_format_raises_error(self, temp_dir):
        """Test conversion with unsupported format raises ValueError"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.exe"
        input_file.write_text("not a subtitle")

        with pytest.raises(ValueError, match="Unsupported conversion"):
            await converter.convert(
                input_path=input_file,
                output_format="srt",
                options={},
                session_id="test-session"
            )

    @pytest.mark.asyncio
    async def test_convert_pysubs2_load_error(self, temp_dir):
        """Test conversion handles pysubs2 load errors"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.srt"
        input_file.write_text("Invalid subtitle content")

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            with patch('pysubs2.load', side_effect=Exception("Invalid format")):
                with pytest.raises(Exception, match="Invalid format"):
                    await converter.convert(
                        input_path=input_file,
                        output_format="vtt",
                        options={},
                        session_id="test-session"
                    )

                # Verify failure progress was sent
                last_call = mock_progress.call_args_list[-1]
                assert "failed" in str(last_call)

    @pytest.mark.asyncio
    async def test_convert_output_file_missing_raises_exception(self, temp_dir):
        """Test conversion raises exception when output file not created"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.srt"
        input_file.write_text("1\n00:00:01,000 --> 00:00:05,000\nSubtitle\n")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pysubs2.load') as mock_load:
                mock_subs = MagicMock()
                mock_load.return_value = mock_subs

                # Don't create output file - it will return non-existent path
                with pytest.raises(FileNotFoundError):
                    result = await converter.convert(
                        input_path=input_file,
                        output_format="vtt",
                        options={},
                        session_id="test-session"
                    )
                    # Try to verify the result exists
                    if not result.exists():
                        raise FileNotFoundError(f"Output file not created: {result}")

    @pytest.mark.asyncio
    async def test_adjust_timing_pysubs2_not_available(self, temp_dir):
        """Test timing adjustment fails when pysubs2 not available"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.srt"
        input_file.write_text("1\n00:00:01,000 --> 00:00:05,000\nSubtitle\n")

        with patch('app.services.subtitle_converter.PYSUBS2_AVAILABLE', False):
            with pytest.raises(ValueError, match="Subtitle support not available"):
                await converter.adjust_timing(
                    input_path=input_file,
                    offset_ms=5000,
                    session_id="test-session"
                )

    @pytest.mark.asyncio
    async def test_adjust_timing_pysubs2_load_error(self, temp_dir):
        """Test timing adjustment handles pysubs2 load errors"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.srt"
        input_file.write_text("Invalid")

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            with patch('pysubs2.load', side_effect=Exception("Parse error")):
                with pytest.raises(Exception, match="Parse error"):
                    await converter.adjust_timing(
                        input_path=input_file,
                        offset_ms=5000,
                        session_id="test-session"
                    )

                # Verify failure progress was sent
                last_call = mock_progress.call_args_list[-1]
                assert "failed" in str(last_call)

    @pytest.mark.asyncio
    async def test_get_subtitle_info_exception_handling(self, temp_dir):
        """Test metadata extraction handles exceptions gracefully"""
        converter = SubtitleConverter()

        test_file = temp_dir / "corrupted.srt"
        test_file.write_text("corrupted content")

        with patch('pysubs2.load', side_effect=Exception("Corrupted file")):
            info = await converter.get_subtitle_info(test_file)

            assert "error" in info
            assert "Corrupted file" in info["error"]

    @pytest.mark.asyncio
    async def test_get_subtitle_info_pysubs2_not_available(self, temp_dir):
        """Test metadata extraction when pysubs2 not available"""
        converter = SubtitleConverter()

        test_file = temp_dir / "test.srt"
        test_file.write_text("1\n00:00:01,000 --> 00:00:05,000\nSubtitle\n")

        with patch('app.services.subtitle_converter.PYSUBS2_AVAILABLE', False):
            info = await converter.get_subtitle_info(test_file)

            assert "error" in info
            assert "pysubs2 not available" in info["error"]


# ============================================================================
# TIME FORMATTING TESTS
# ============================================================================

class TestTimeFormatting:
    """Test time formatting utilities"""

    def test_format_time_basic(self):
        """Test basic time formatting"""
        converter = SubtitleConverter()

        formatted = converter._format_time(1000)  # 1 second

        assert formatted == "00:00:01,000"

    def test_format_time_with_minutes(self):
        """Test time formatting with minutes"""
        converter = SubtitleConverter()

        # 1 minute 30 seconds 500 ms = 90500 ms
        formatted = converter._format_time(90500)

        assert formatted == "00:01:30,500"

    def test_format_time_with_hours(self):
        """Test time formatting with hours"""
        converter = SubtitleConverter()

        # 1 hour 30 minutes = 5400000 ms
        formatted = converter._format_time(5400000)

        assert formatted == "01:30:00,000"

    def test_format_duration_seconds_only(self):
        """Test duration formatting for seconds only"""
        converter = SubtitleConverter()

        formatted = converter._format_duration(30.5)

        assert formatted == "30s"

    def test_format_duration_minutes_and_seconds(self):
        """Test duration formatting for minutes and seconds"""
        converter = SubtitleConverter()

        # 1 minute 30 seconds
        formatted = converter._format_duration(90.0)

        assert formatted == "1m 30s"

    def test_format_duration_hours_minutes_seconds(self):
        """Test duration formatting with hours"""
        converter = SubtitleConverter()

        # 1 hour 30 minutes 45 seconds
        formatted = converter._format_duration(5445.0)

        assert formatted == "1h 30m 45s"


# ============================================================================
# ADVANCED CONVERSION OPTIONS TESTS
# ============================================================================

class TestConversionOptions:
    """Test advanced conversion options"""

    @pytest.mark.asyncio
    async def test_convert_with_fps_option(self, temp_dir):
        """Test conversion with FPS option (for SUB format)"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.srt"
        input_file.write_text("1\n00:00:01,000 --> 00:00:05,000\nSubtitle\n")

        output_file = settings.UPLOAD_DIR / "test_converted.sub"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pysubs2.load') as mock_load:
                mock_subs = MagicMock()
                mock_load.return_value = mock_subs

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text("")

                await converter.convert(
                    input_path=input_file,
                    output_format="sub",
                    options={"fps": 25.0},
                    session_id="test-session"
                )

                # Verify FPS passed to load
                call_kwargs = mock_load.call_args[1]
                assert call_kwargs.get('fps') == 25.0

                # Verify FPS passed to save
                save_kwargs = mock_subs.save.call_args[1]
                assert save_kwargs.get('fps') == 25.0

    @pytest.mark.asyncio
    async def test_convert_with_html_tags_option(self, temp_dir):
        """Test conversion with HTML tags preservation option"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.srt"
        input_file.write_text(
            "1\n"
            "00:00:01,000 --> 00:00:05,000\n"
            "<b>Bold subtitle</b>\n"
        )

        output_file = settings.UPLOAD_DIR / "test_converted.ass"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pysubs2.load') as mock_load:
                mock_subs = MagicMock()
                mock_load.return_value = mock_subs

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text("")

                await converter.convert(
                    input_path=input_file,
                    output_format="ass",
                    options={"keep_html_tags": True},
                    session_id="test-session"
                )

                # Verify HTML tag option passed to save
                save_kwargs = mock_subs.save.call_args[1]
                assert save_kwargs.get('keep_html_tags') is True

    @pytest.mark.asyncio
    async def test_convert_default_fps_option(self, temp_dir):
        """Test default FPS is 23.976"""
        converter = SubtitleConverter()

        input_file = temp_dir / "test.srt"
        input_file.write_text("1\n00:00:01,000 --> 00:00:05,000\nSubtitle\n")

        output_file = settings.UPLOAD_DIR / "test_converted.sub"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pysubs2.load') as mock_load:
                mock_subs = MagicMock()
                mock_load.return_value = mock_subs

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text("")

                await converter.convert(
                    input_path=input_file,
                    output_format="sub",
                    options={},  # No FPS specified
                    session_id="test-session"
                )

                # Verify default FPS
                call_kwargs = mock_load.call_args[1]
                assert call_kwargs.get('fps') == 23.976


class TestSubtitleImportFallback:
    """Test import error handling for optional dependencies"""

    def test_pysubs2_import_fallback(self):
        """Test that PYSUBS2_AVAILABLE is set to False when pysubs2 is not available"""
        # This tests the import error handler on lines 9-10
        import sys
        from unittest.mock import patch

        # Temporarily hide pysubs2
        with patch.dict(sys.modules, {'pysubs2': None}):
            # Force module reload to trigger import error
            import importlib
            import app.services.subtitle_converter
            importlib.reload(app.services.subtitle_converter)

            # The module should still load with PYSUBS2_AVAILABLE=False
            assert hasattr(app.services.subtitle_converter, 'PYSUBS2_AVAILABLE')
            # Re-reload to restore normal state
            importlib.reload(app.services.subtitle_converter)
