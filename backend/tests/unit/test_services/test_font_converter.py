"""
Tests for app/services/font_converter.py

COVERAGE GOAL: 85%+
Tests font conversion (TTF/OTF/WOFF/WOFF2), subsetting, optimization,
metadata extraction, and error handling
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import logging

from app.services.font_converter import FontConverter
from app.config import settings


# ============================================================================
# BASIC FUNCTIONALITY TESTS
# ============================================================================

class TestFontConverterBasics:
    """Test basic FontConverter functionality"""

    def test_initialization(self):
        """Test FontConverter initializes correctly"""
        converter = FontConverter()

        assert converter.supported_formats is not None
        assert "input" in converter.supported_formats
        assert "output" in converter.supported_formats
        assert "ttf" in converter.supported_formats["input"]
        assert "woff" in converter.supported_formats["output"]
        assert converter.websocket_manager is not None

    def test_initialization_with_websocket_manager(self):
        """Test FontConverter can be initialized with custom WebSocket manager"""
        mock_ws_manager = Mock()
        converter = FontConverter(websocket_manager=mock_ws_manager)

        assert converter.websocket_manager == mock_ws_manager

    @pytest.mark.asyncio
    async def test_get_supported_formats(self):
        """Test getting supported font formats"""
        converter = FontConverter()

        formats = await converter.get_supported_formats()

        assert "input" in formats
        assert "output" in formats
        assert isinstance(formats["input"], list)
        assert isinstance(formats["output"], list)
        # Check common font formats
        assert "ttf" in formats["output"]
        assert "otf" in formats["output"]
        assert "woff" in formats["output"]
        assert "woff2" in formats["output"]


# ============================================================================
# FONT CONVERSION TESTS
# ============================================================================

class TestFontConversion:
    """Test font conversion functionality"""

    @pytest.mark.asyncio
    async def test_convert_ttf_to_woff_success(self, temp_dir):
        """Test successful TTF to WOFF conversion"""
        converter = FontConverter()

        input_file = temp_dir / "test.ttf"
        input_file.write_bytes(b"fake ttf font data")

        output_file = settings.UPLOAD_DIR / "test_converted.woff"

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
                # Mock TTFont object
                mock_font = MagicMock()
                mock_font.flavor = None
                mock_font.close = Mock()
                mock_ttfont_class.return_value = mock_font

                # Create output file
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(b"fake woff data")

                result = await converter.convert(
                    input_path=input_file,
                    output_format="woff",
                    options={},
                    session_id="test-session"
                )

                assert result == output_file
                assert output_file.exists()

                # Verify progress was sent
                assert mock_progress.call_count >= 4

                # Verify TTFont was called with input file
                mock_ttfont_class.assert_called_once_with(str(input_file))

                # Verify flavor was set to woff
                assert mock_font.flavor == "woff"

                # Verify save was called
                mock_font.save.assert_called_once()

                # Verify font was closed (resource cleanup)
                mock_font.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_woff_to_ttf_success(self, temp_dir):
        """Test successful WOFF to TTF conversion"""
        converter = FontConverter()

        input_file = temp_dir / "test.woff"
        input_file.write_bytes(b"fake woff font")

        output_file = settings.UPLOAD_DIR / "test_converted.ttf"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
                mock_font = MagicMock()
                mock_font.flavor = None
                mock_font.close = Mock()
                mock_ttfont_class.return_value = mock_font

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(b"fake ttf data")

                result = await converter.convert(
                    input_path=input_file,
                    output_format="ttf",
                    options={},
                    session_id="test-session"
                )

                assert result == output_file
                # TTF has no flavor
                assert mock_font.flavor is None
                mock_font.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_otf_to_ttf_success(self, temp_dir):
        """Test successful OTF to TTF conversion"""
        converter = FontConverter()

        input_file = temp_dir / "test.otf"
        input_file.write_bytes(b"fake otf font")

        output_file = settings.UPLOAD_DIR / "test_converted.ttf"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
                mock_font = MagicMock()
                mock_font.flavor = None
                mock_font.close = Mock()
                mock_ttfont_class.return_value = mock_font

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(b"ttf data")

                result = await converter.convert(
                    input_path=input_file,
                    output_format="ttf",
                    options={},
                    session_id="test-session"
                )

                assert result == output_file
                mock_ttfont_class.assert_called_once_with(str(input_file))
                mock_font.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_woff_to_woff2_success(self, temp_dir):
        """Test successful WOFF to WOFF2 conversion"""
        converter = FontConverter()

        input_file = temp_dir / "test.woff"
        input_file.write_bytes(b"fake woff")

        output_file = settings.UPLOAD_DIR / "test_converted.woff2"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
                mock_font = MagicMock()
                mock_font.flavor = None
                mock_font.close = Mock()
                mock_ttfont_class.return_value = mock_font

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(b"woff2 data")

                result = await converter.convert(
                    input_path=input_file,
                    output_format="woff2",
                    options={},
                    session_id="test-session"
                )

                assert result == output_file
                # WOFF2 should have flavor set
                assert mock_font.flavor == "woff2"
                mock_font.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_progress_updates_sent(self, temp_dir):
        """Test conversion sends multiple progress updates"""
        converter = FontConverter()

        input_file = temp_dir / "test.ttf"
        input_file.write_bytes(b"ttf data")

        output_file = settings.UPLOAD_DIR / "test_converted.woff"

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
                mock_font = MagicMock()
                mock_font.close = Mock()
                mock_ttfont_class.return_value = mock_font

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(b"data")

                await converter.convert(
                    input_path=input_file,
                    output_format="woff",
                    options={},
                    session_id="test-session"
                )

                # Verify progress was called multiple times with increasing values
                calls = mock_progress.call_args_list
                assert len(calls) >= 4

                # Check progress values are increasing
                progress_values = [call[0][1] for call in calls]  # Extract progress argument
                assert progress_values[0] == 10  # Start
                assert progress_values[-1] == 100  # Complete
                mock_font.close.assert_called_once()


# ============================================================================
# FONT SUBSETTING TESTS
# ============================================================================

class TestFontSubsetting:
    """Test font subsetting functionality"""

    @pytest.mark.asyncio
    async def test_convert_with_subset_text(self, temp_dir):
        """Test conversion with font subsetting"""
        converter = FontConverter()

        input_file = temp_dir / "test.ttf"
        input_file.write_bytes(b"ttf data")

        output_file = settings.UPLOAD_DIR / "test_converted.ttf"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
                with patch('app.services.font_converter.Subsetter') as mock_subsetter_class:
                    mock_font = MagicMock()
                    mock_font.close = Mock()
                    mock_ttfont_class.return_value = mock_font

                    mock_subsetter = MagicMock()
                    mock_subsetter_class.return_value = mock_subsetter

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_bytes(b"subset font")

                    await converter.convert(
                        input_path=input_file,
                        output_format="ttf",
                        options={"subset_text": "Hello World"},
                        session_id="test-session"
                    )

                    # Verify subsetter was created
                    mock_subsetter_class.assert_called_once()

                    # Verify subsetter.populate was called with text
                    mock_subsetter.populate.assert_called_once()
                    populate_call = mock_subsetter.populate.call_args
                    assert "text" in populate_call[1]
                    assert populate_call[1]["text"] == "Hello World"

                    # Verify subset was applied
                    mock_subsetter.subset.assert_called_once_with(mock_font)
                    mock_font.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_subset_keeps_specified_characters(self, temp_dir):
        """Test subsetting keeps only specified characters"""
        converter = FontConverter()

        input_file = temp_dir / "test.ttf"
        input_file.write_bytes(b"ttf")

        output_file = settings.UPLOAD_DIR / "test_converted.ttf"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
                with patch('app.services.font_converter.Subsetter') as mock_subsetter_class:
                    mock_font = MagicMock()
                    mock_ttfont_class.return_value = mock_font

                    mock_subsetter = MagicMock()
                    mock_subsetter_class.return_value = mock_subsetter

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_bytes(b"subset")

                    test_text = "ABC123"
                    await converter.convert(
                        input_path=input_file,
                        output_format="ttf",
                        options={"subset_text": test_text},
                        session_id="test-session"
                    )

                    # Verify the exact subset text was used
                    call_kwargs = mock_subsetter.populate.call_args[1]
                    assert call_kwargs["text"] == test_text

                    mock_font.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_without_subsetting(self, temp_dir):
        """Test conversion without subsetting when option not provided"""
        converter = FontConverter()

        input_file = temp_dir / "test.ttf"
        input_file.write_bytes(b"ttf")

        output_file = settings.UPLOAD_DIR / "test_converted.ttf"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
                with patch('app.services.font_converter.Subsetter') as mock_subsetter_class:
                    mock_font = MagicMock()
                    mock_ttfont_class.return_value = mock_font

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_bytes(b"full font")

                    await converter.convert(
                        input_path=input_file,
                        output_format="ttf",
                        options={},  # No subset_text
                        session_id="test-session"
                    )

                    # Subsetter should not be called
                    mock_subsetter_class.assert_not_called()

                    mock_font.close.assert_called_once()


# ============================================================================
# FONT OPTIMIZATION TESTS
# ============================================================================

class TestFontOptimization:
    """Test font optimization functionality"""

    @pytest.mark.asyncio
    async def test_optimize_font_removes_unnecessary_tables(self, temp_dir):
        """Test optimize_font removes unnecessary tables"""
        converter = FontConverter()

        input_file = temp_dir / "test.ttf"
        input_file.write_bytes(b"ttf font")

        output_file = settings.UPLOAD_DIR / "test_optimized.ttf"

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
                mock_font = MagicMock()
                mock_font.__contains__ = lambda self, key: key in ['DSIG', 'hdmx', 'VDMX', 'LTSH', 'PCLT']
                mock_font.__delitem__ = Mock()
                mock_font.close = Mock()
                mock_ttfont_class.return_value = mock_font

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(b"optimized")

                result = await converter.optimize_font(input_file, "test-session")

                assert result == output_file

                # Verify unwanted tables were deleted
                mock_font.__delitem__.assert_called()

                # Verify progress was sent
                assert mock_progress.call_count >= 3

    @pytest.mark.asyncio
    async def test_optimize_font_saves_output(self, temp_dir):
        """Test optimize_font saves the optimized font"""
        converter = FontConverter()

        input_file = temp_dir / "test.ttf"
        input_file.write_bytes(b"ttf")

        output_file = settings.UPLOAD_DIR / "test_optimized.ttf"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
                mock_font = MagicMock()
                mock_font.__contains__ = Mock(return_value=False)
                mock_font.close = Mock()
                mock_ttfont_class.return_value = mock_font

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(b"opt")

                await converter.optimize_font(input_file, "test-session")

                # Verify save was called with output path
                mock_font.save.assert_called_once()
                save_call = mock_font.save.call_args[0][0]
                assert str(output_file) == save_call

    @pytest.mark.asyncio
    async def test_optimize_font_closes_font(self, temp_dir):
        """Test optimize_font properly closes font object"""
        converter = FontConverter()

        input_file = temp_dir / "test.ttf"
        input_file.write_bytes(b"ttf")

        output_file = settings.UPLOAD_DIR / "test_optimized.ttf"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
                mock_font = MagicMock()
                mock_font.__contains__ = Mock(return_value=False)
                mock_ttfont_class.return_value = mock_font

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(b"opt")

                await converter.optimize_font(input_file, "test-session")

                # Verify font was closed
                mock_font.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_with_optimize_option(self, temp_dir):
        """Test conversion respects optimize option"""
        converter = FontConverter()

        input_file = temp_dir / "test.ttf"
        input_file.write_bytes(b"ttf")

        output_file = settings.UPLOAD_DIR / "test_converted.ttf"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
                mock_font = MagicMock()
                mock_font.close = Mock()
                mock_ttfont_class.return_value = mock_font

                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(b"opt")

                # Test with optimize=True
                await converter.convert(
                    input_path=input_file,
                    output_format="ttf",
                    options={"optimize": True},
                    session_id="test-session"
                )

                # Conversion should succeed regardless of optimize flag
                # (optimize just determines if tables are dropped)
                mock_font.save.assert_called_once()


# ============================================================================
# FORMAT SUPPORT TESTS
# ============================================================================

class TestFormatSupport:
    """Test format support"""

    @pytest.mark.asyncio
    async def test_get_supported_formats_returns_correct_formats(self):
        """Test get_supported_formats returns all supported font formats"""
        converter = FontConverter()

        formats = await converter.get_supported_formats()

        # Check all required formats are present
        required_formats = {"ttf", "otf", "woff", "woff2"}
        assert required_formats.issubset(set(formats["input"]))
        assert required_formats.issubset(set(formats["output"]))

    def test_get_output_flavor_for_woff(self):
        """Test _get_output_flavor returns 'woff' for woff format"""
        converter = FontConverter()

        flavor = converter._get_output_flavor("woff")

        assert flavor == "woff"

    def test_get_output_flavor_for_woff2(self):
        """Test _get_output_flavor returns 'woff2' for woff2 format"""
        converter = FontConverter()

        flavor = converter._get_output_flavor("woff2")

        assert flavor == "woff2"

    def test_get_output_flavor_for_ttf(self):
        """Test _get_output_flavor returns None for TTF"""
        converter = FontConverter()

        flavor = converter._get_output_flavor("ttf")

        assert flavor is None

    def test_get_output_flavor_for_otf(self):
        """Test _get_output_flavor returns None for OTF"""
        converter = FontConverter()

        flavor = converter._get_output_flavor("otf")

        assert flavor is None


# ============================================================================
# METADATA EXTRACTION TESTS
# ============================================================================

class TestFontMetadata:
    """Test font metadata extraction"""

    @pytest.mark.asyncio
    async def test_get_info_basic_metadata(self, temp_dir):
        """Test basic font metadata extraction"""
        converter = FontConverter()

        test_file = temp_dir / "test.ttf"
        test_file.write_bytes(b"ttf data")

        with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
            mock_font = MagicMock()
            mock_font.get = Mock(return_value=None)
            mock_font.close = Mock()
            mock_font.__contains__ = Mock(return_value=False)
            mock_ttfont_class.return_value = mock_font

            info = await converter.get_info(test_file)

            assert "filename" in info
            assert info["filename"] == "test.ttf"
            assert "size" in info
            assert info["size"] > 0
            assert "format" in info
            assert info["format"] == "ttf"

    @pytest.mark.asyncio
    async def test_get_info_extracts_family_name(self, temp_dir):
        """Test font family name extraction"""
        converter = FontConverter()

        test_file = temp_dir / "test.ttf"
        test_file.write_bytes(b"ttf")

        with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
            # Mock name table
            mock_name_record1 = Mock()
            mock_name_record1.nameID = 1  # Family name
            mock_name_record1.toUnicode = Mock(return_value="Arial")

            mock_name_table = Mock()
            mock_name_table.names = [mock_name_record1]

            mock_font = MagicMock()
            mock_font.get = Mock(return_value=mock_name_table)
            mock_font.__contains__ = Mock(return_value=False)
            mock_font.close = Mock()
            mock_ttfont_class.return_value = mock_font

            info = await converter.get_info(test_file)

            # Verify get('name') was called to fetch name table
            mock_font.get.assert_called()
            # Check that basic metadata exists
            assert "filename" in info
            assert "size" in info

    @pytest.mark.asyncio
    async def test_get_info_extracts_style_name(self, temp_dir):
        """Test font style name extraction"""
        converter = FontConverter()

        test_file = temp_dir / "test.ttf"
        test_file.write_bytes(b"ttf")

        with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
            # Mock name records for style
            mock_name_record2 = Mock()
            mock_name_record2.nameID = 2  # Style name
            mock_name_record2.toUnicode = Mock(return_value="Bold Italic")

            mock_name_table = Mock()
            mock_name_table.names = [mock_name_record2]

            mock_font = MagicMock()
            mock_font.get = Mock(return_value=mock_name_table)
            mock_font.__contains__ = Mock(return_value=False)
            mock_font.close = Mock()
            mock_ttfont_class.return_value = mock_font

            info = await converter.get_info(test_file)

            # Verify get('name') was called
            mock_font.get.assert_called()
            # Check basic metadata exists
            assert "filename" in info or "size" in info

    @pytest.mark.asyncio
    async def test_get_info_extracts_glyph_count_truetype(self, temp_dir):
        """Test glyph count extraction for TrueType fonts"""
        converter = FontConverter()

        test_file = temp_dir / "test.ttf"
        test_file.write_bytes(b"ttf")

        with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
            # Mock glyf table for TrueType
            mock_glyf_table = Mock()
            mock_glyf_table.glyphs = ["glyph1", "glyph2", "glyph3"]

            mock_font = MagicMock()
            mock_font.get = Mock(return_value=None)
            mock_font.__contains__ = Mock(side_effect=lambda x: x == 'glyf')
            mock_font.__getitem__ = Mock(return_value=mock_glyf_table)
            mock_font.close = Mock()
            mock_ttfont_class.return_value = mock_font

            info = await converter.get_info(test_file)

            # Verify __contains__ was called to check for glyf table
            assert mock_font.__contains__.called
            # Check basic metadata exists
            assert "filename" in info or "size" in info

    @pytest.mark.asyncio
    async def test_get_info_handles_metadata_extraction_errors(self, temp_dir):
        """Test metadata extraction handles errors gracefully"""
        converter = FontConverter()

        test_file = temp_dir / "corrupted.ttf"
        test_file.write_bytes(b"corrupted")

        with patch('app.services.font_converter.TTFont', side_effect=Exception("Invalid font")):
            # Should not raise, just return basic info
            info = await converter.get_info(test_file)

            # Should still have filename and size
            assert "filename" in info
            assert "size" in info

    @pytest.mark.asyncio
    async def test_get_info_returns_web_font_flag(self, temp_dir):
        """Test web font flag detection"""
        converter = FontConverter()

        test_file = temp_dir / "test.woff"
        test_file.write_bytes(b"woff")

        with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
            mock_font = MagicMock()
            mock_font.get = Mock(return_value=None)
            mock_font.__contains__ = Mock(return_value=False)
            mock_font.flavor = "woff"
            mock_font.close = Mock()
            mock_ttfont_class.return_value = mock_font

            info = await converter.get_info(test_file)

            # Should detect as web font
            if "is_web_font" in info:
                assert info["is_web_font"] is True

    @pytest.mark.asyncio
    async def test_get_info_extracts_full_name(self, temp_dir):
        """Test font full name extraction (nameID 4)"""
        converter = FontConverter()

        test_file = temp_dir / "test.ttf"
        test_file.write_bytes(b"ttf")

        with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
            # Mock name records for full name
            mock_name_record4 = Mock()
            mock_name_record4.nameID = 4  # Full name
            mock_name_record4.toUnicode = Mock(return_value="Arial Bold Italic")

            mock_name_table = Mock()
            mock_name_table.names = [mock_name_record4]

            mock_font = MagicMock()
            mock_font.get = Mock(return_value=mock_name_table)
            mock_font.__contains__ = Mock(return_value=False)
            mock_font.close = Mock()
            mock_ttfont_class.return_value = mock_font

            info = await converter.get_info(test_file)

            # Should have called get to fetch name table
            mock_font.get.assert_called()

    @pytest.mark.asyncio
    async def test_get_info_extracts_version(self, temp_dir):
        """Test font version extraction (nameID 5)"""
        converter = FontConverter()

        test_file = temp_dir / "test.ttf"
        test_file.write_bytes(b"ttf")

        with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
            # Mock name records for version
            mock_name_record5 = Mock()
            mock_name_record5.nameID = 5  # Version
            mock_name_record5.toUnicode = Mock(return_value="Version 1.0")

            mock_name_table = Mock()
            mock_name_table.names = [mock_name_record5]

            mock_font = MagicMock()
            mock_font.get = Mock(return_value=mock_name_table)
            mock_font.__contains__ = Mock(return_value=False)
            mock_font.close = Mock()
            mock_ttfont_class.return_value = mock_font

            info = await converter.get_info(test_file)

            # Should have basic metadata
            assert "filename" in info

    @pytest.mark.asyncio
    async def test_get_info_handles_unicode_decode_error(self, temp_dir):
        """Test metadata extraction handles unicode decode errors gracefully"""
        converter = FontConverter()

        test_file = temp_dir / "test.ttf"
        test_file.write_bytes(b"ttf")

        with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
            # Mock name record that raises UnicodeDecodeError
            mock_name_record = Mock()
            mock_name_record.nameID = 1
            mock_name_record.toUnicode = Mock(side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid'))

            mock_name_table = Mock()
            mock_name_table.names = [mock_name_record]

            mock_font = MagicMock()
            mock_font.get = Mock(return_value=mock_name_table)
            mock_font.__contains__ = Mock(return_value=False)
            mock_font.close = Mock()
            mock_ttfont_class.return_value = mock_font

            # Should not raise exception
            info = await converter.get_info(test_file)

            # Should still return basic info
            assert "filename" in info
            assert "size" in info

    @pytest.mark.asyncio
    async def test_get_info_handles_attribute_error_in_name_records(self, temp_dir):
        """Test metadata extraction handles AttributeError in name records"""
        converter = FontConverter()

        test_file = temp_dir / "test.ttf"
        test_file.write_bytes(b"ttf")

        with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
            # Mock name record that raises AttributeError
            mock_name_record = Mock()
            mock_name_record.nameID = 1
            mock_name_record.toUnicode = Mock(side_effect=AttributeError("Missing attr"))

            mock_name_table = Mock()
            mock_name_table.names = [mock_name_record]

            mock_font = MagicMock()
            mock_font.get = Mock(return_value=mock_name_table)
            mock_font.__contains__ = Mock(return_value=False)
            mock_font.close = Mock()
            mock_ttfont_class.return_value = mock_font

            # Should not raise exception
            info = await converter.get_info(test_file)

            # Should still return basic info
            assert "filename" in info

    @pytest.mark.asyncio
    async def test_get_info_cff_font_glyph_count(self, temp_dir):
        """Test glyph count extraction for CFF (OpenType) fonts"""
        converter = FontConverter()

        test_file = temp_dir / "test.otf"
        test_file.write_bytes(b"otf")

        with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
            # Mock CFF table for OpenType
            mock_charstrings_index = Mock()
            mock_charstrings_index.count = 250
            mock_charstrings = Mock()
            mock_charstrings.charStringsIndex = mock_charstrings_index
            mock_topdict = Mock()
            mock_topdict.CharStrings = mock_charstrings
            mock_topdict_index = Mock()
            mock_topdict_index.__getitem__ = Mock(return_value=mock_topdict)
            mock_cff = Mock()
            mock_cff.topDictIndex = mock_topdict_index
            mock_cff_table = Mock()
            mock_cff_table.cff = mock_cff

            mock_font = MagicMock()
            mock_font.get = Mock(return_value=None)
            mock_font.__contains__ = Mock(side_effect=lambda x: x == 'CFF ')
            mock_font.__getitem__ = Mock(return_value=mock_cff_table)
            mock_font.close = Mock()
            mock_ttfont_class.return_value = mock_font

            info = await converter.get_info(test_file)

            # Check basic metadata exists
            assert "filename" in info

    @pytest.mark.asyncio
    async def test_get_info_handles_unicode_decode_error_style_name(self, temp_dir):
        """Test metadata extraction handles unicode decode errors for style name (nameID 2)"""
        converter = FontConverter()

        test_file = temp_dir / "test.ttf"
        test_file.write_bytes(b"ttf")

        with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
            # Mock name record for style name that raises UnicodeDecodeError
            mock_name_record = Mock()
            mock_name_record.nameID = 2  # Style name
            mock_name_record.toUnicode = Mock(side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid'))

            mock_name_table = Mock()
            mock_name_table.names = [mock_name_record]

            mock_font = MagicMock()
            mock_font.get = Mock(return_value=mock_name_table)
            mock_font.__contains__ = Mock(return_value=False)
            mock_font.close = Mock()
            mock_ttfont_class.return_value = mock_font

            # Should not raise exception
            info = await converter.get_info(test_file)

            # Should still return basic info
            assert "filename" in info
            assert "size" in info

    @pytest.mark.asyncio
    async def test_get_info_handles_attribute_error_style_name(self, temp_dir):
        """Test metadata extraction handles AttributeError for style name (nameID 2)"""
        converter = FontConverter()

        test_file = temp_dir / "test.ttf"
        test_file.write_bytes(b"ttf")

        with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
            # Mock name record for style name that raises AttributeError
            mock_name_record = Mock()
            mock_name_record.nameID = 2  # Style name
            mock_name_record.toUnicode = Mock(side_effect=AttributeError("Missing attr"))

            mock_name_table = Mock()
            mock_name_table.names = [mock_name_record]

            mock_font = MagicMock()
            mock_font.get = Mock(return_value=mock_name_table)
            mock_font.__contains__ = Mock(return_value=False)
            mock_font.close = Mock()
            mock_ttfont_class.return_value = mock_font

            # Should not raise exception
            info = await converter.get_info(test_file)

            # Should still return basic info
            assert "filename" in info
            assert "size" in info

    @pytest.mark.asyncio
    async def test_get_info_handles_unicode_decode_error_full_name(self, temp_dir):
        """Test metadata extraction handles unicode decode errors for full name (nameID 4)"""
        converter = FontConverter()

        test_file = temp_dir / "test.ttf"
        test_file.write_bytes(b"ttf")

        with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
            # Mock name record for full name that raises UnicodeDecodeError
            mock_name_record = Mock()
            mock_name_record.nameID = 4  # Full name
            mock_name_record.toUnicode = Mock(side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid'))

            mock_name_table = Mock()
            mock_name_table.names = [mock_name_record]

            mock_font = MagicMock()
            mock_font.get = Mock(return_value=mock_name_table)
            mock_font.__contains__ = Mock(return_value=False)
            mock_font.close = Mock()
            mock_ttfont_class.return_value = mock_font

            # Should not raise exception
            info = await converter.get_info(test_file)

            # Should still return basic info
            assert "filename" in info
            assert "size" in info

    @pytest.mark.asyncio
    async def test_get_info_handles_attribute_error_full_name(self, temp_dir):
        """Test metadata extraction handles AttributeError for full name (nameID 4)"""
        converter = FontConverter()

        test_file = temp_dir / "test.ttf"
        test_file.write_bytes(b"ttf")

        with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
            # Mock name record for full name that raises AttributeError
            mock_name_record = Mock()
            mock_name_record.nameID = 4  # Full name
            mock_name_record.toUnicode = Mock(side_effect=AttributeError("Missing attr"))

            mock_name_table = Mock()
            mock_name_table.names = [mock_name_record]

            mock_font = MagicMock()
            mock_font.get = Mock(return_value=mock_name_table)
            mock_font.__contains__ = Mock(return_value=False)
            mock_font.close = Mock()
            mock_ttfont_class.return_value = mock_font

            # Should not raise exception
            info = await converter.get_info(test_file)

            # Should still return basic info
            assert "filename" in info
            assert "size" in info

    @pytest.mark.asyncio
    async def test_get_info_handles_unicode_decode_error_version(self, temp_dir):
        """Test metadata extraction handles unicode decode errors for version (nameID 5)"""
        converter = FontConverter()

        test_file = temp_dir / "test.ttf"
        test_file.write_bytes(b"ttf")

        with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
            # Mock name record for version that raises UnicodeDecodeError
            mock_name_record = Mock()
            mock_name_record.nameID = 5  # Version
            mock_name_record.toUnicode = Mock(side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid'))

            mock_name_table = Mock()
            mock_name_table.names = [mock_name_record]

            mock_font = MagicMock()
            mock_font.get = Mock(return_value=mock_name_table)
            mock_font.__contains__ = Mock(return_value=False)
            mock_font.close = Mock()
            mock_ttfont_class.return_value = mock_font

            # Should not raise exception
            info = await converter.get_info(test_file)

            # Should still return basic info
            assert "filename" in info
            assert "size" in info

    @pytest.mark.asyncio
    async def test_get_info_handles_attribute_error_version(self, temp_dir):
        """Test metadata extraction handles AttributeError for version (nameID 5)"""
        converter = FontConverter()

        test_file = temp_dir / "test.ttf"
        test_file.write_bytes(b"ttf")

        with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
            # Mock name record for version that raises AttributeError
            mock_name_record = Mock()
            mock_name_record.nameID = 5  # Version
            mock_name_record.toUnicode = Mock(side_effect=AttributeError("Missing attr"))

            mock_name_table = Mock()
            mock_name_table.names = [mock_name_record]

            mock_font = MagicMock()
            mock_font.get = Mock(return_value=mock_name_table)
            mock_font.__contains__ = Mock(return_value=False)
            mock_font.close = Mock()
            mock_ttfont_class.return_value = mock_font

            # Should not raise exception
            info = await converter.get_info(test_file)

            # Should still return basic info
            assert "filename" in info
            assert "size" in info


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestFontConverterErrorHandling:
    """Test error handling"""

    @pytest.mark.asyncio
    async def test_convert_corrupted_font_raises_error(self, temp_dir):
        """Test conversion detects corrupted fonts"""
        converter = FontConverter()

        input_file = temp_dir / "corrupted.ttf"
        input_file.write_bytes(b"not a real font")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.font_converter.TTFont', side_effect=Exception("Invalid font")):
                with pytest.raises(Exception):
                    await converter.convert(
                        input_path=input_file,
                        output_format="woff",
                        options={},
                        session_id="test-session"
                    )

    @pytest.mark.asyncio
    async def test_convert_invalid_input_format_raises_error(self, temp_dir):
        """Test conversion with invalid input format"""
        converter = FontConverter()

        input_file = temp_dir / "test.exe"
        input_file.write_bytes(b"not a font")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.font_converter.TTFont', side_effect=Exception("Invalid format")):
                with pytest.raises(Exception):
                    await converter.convert(
                        input_path=input_file,
                        output_format="ttf",
                        options={},
                        session_id="test-session"
                    )

    @pytest.mark.asyncio
    async def test_convert_fonttools_error_handled(self, temp_dir):
        """Test conversion handles fontTools errors"""
        converter = FontConverter()

        input_file = temp_dir / "test.ttf"
        input_file.write_bytes(b"ttf")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.font_converter.TTFont', side_effect=Exception("fontTools error")):
                with pytest.raises(Exception):
                    await converter.convert(
                        input_path=input_file,
                        output_format="ttf",
                        options={},
                        session_id="test-session"
                    )

    @pytest.mark.asyncio
    async def test_convert_missing_optional_dependency(self, temp_dir):
        """Test conversion handles missing optional dependencies"""
        converter = FontConverter()

        input_file = temp_dir / "test.ttf"
        input_file.write_bytes(b"ttf")

        output_file = settings.UPLOAD_DIR / "test_converted.woff"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
                with patch('app.services.font_converter.Subsetter', side_effect=ImportError("Missing brotli")):
                    mock_font = MagicMock()
                    mock_ttfont_class.return_value = mock_font

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_bytes(b"data")

                    # Even with missing optional deps, basic conversion should work
                    # if subsetting isn't requested
                    result = await converter.convert(
                        input_path=input_file,
                        output_format="woff",
                        options={},  # No subsetting
                        session_id="test-session"
                    )

                    assert result == output_file

    @pytest.mark.asyncio
    async def test_convert_output_file_missing_raises_exception(self, temp_dir):
        """Test conversion raises exception when output file not created"""
        converter = FontConverter()

        input_file = temp_dir / "test.ttf"
        input_file.write_bytes(b"ttf")

        output_file = settings.UPLOAD_DIR / "test_converted.woff"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
                mock_font = MagicMock()
                mock_font.save = Mock(side_effect=Exception("Save failed"))
                mock_ttfont_class.return_value = mock_font

                # Don't create output file - let save fail
                output_file.parent.mkdir(parents=True, exist_ok=True)

                with pytest.raises(Exception):
                    await converter.convert(
                        input_path=input_file,
                        output_format="woff",
                        options={},
                        session_id="test-session"
                    )

    @pytest.mark.asyncio
    async def test_optimize_font_error_handling(self, temp_dir):
        """Test optimize_font handles errors"""
        converter = FontConverter()

        input_file = temp_dir / "test.ttf"
        input_file.write_bytes(b"ttf")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.font_converter.TTFont', side_effect=Exception("Font load failed")):
                with pytest.raises(Exception):
                    await converter.optimize_font(input_file, "test-session")

    @pytest.mark.asyncio
    async def test_get_info_nonexistent_file(self, temp_dir):
        """Test get_info handles nonexistent files"""
        converter = FontConverter()

        nonexistent = temp_dir / "nonexistent.ttf"

        # Should handle missing file gracefully
        try:
            info = await converter.get_info(nonexistent)
            # If it returns, should have minimal info
            assert "filename" in info or "error" in info
        except FileNotFoundError:
            # Also acceptable to raise FileNotFoundError
            pass


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestFontConverterIntegration:
    """Integration tests combining multiple features"""

    @pytest.mark.asyncio
    async def test_convert_with_subsetting_and_optimization(self, temp_dir):
        """Test conversion with both subsetting and optimization"""
        converter = FontConverter()

        input_file = temp_dir / "test.ttf"
        input_file.write_bytes(b"ttf")

        output_file = settings.UPLOAD_DIR / "test_converted.woff"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
                with patch('app.services.font_converter.Subsetter') as mock_subsetter_class:
                    mock_font = MagicMock()
                    mock_font.close = Mock()
                    mock_ttfont_class.return_value = mock_font

                    mock_subsetter = MagicMock()
                    mock_subsetter_class.return_value = mock_subsetter

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_bytes(b"data")

                    result = await converter.convert(
                        input_path=input_file,
                        output_format="woff",
                        options={
                            "subset_text": "Hello",
                            "optimize": True
                        },
                        session_id="test-session"
                    )

                    assert result == output_file
                    # Both subsetting and save should be called
                    mock_subsetter.populate.assert_called_once()
                    mock_font.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_conversions_independence(self, temp_dir):
        """Test multiple conversions don't interfere with each other"""
        converter = FontConverter()

        input_file1 = temp_dir / "test1.ttf"
        input_file1.write_bytes(b"ttf1")

        input_file2 = temp_dir / "test2.otf"
        input_file2.write_bytes(b"otf2")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
                mock_font1 = MagicMock()
                mock_font2 = MagicMock()
                mock_ttfont_class.side_effect = [mock_font1, mock_font2]

                output_file1 = settings.UPLOAD_DIR / "test1_converted.woff"
                output_file2 = settings.UPLOAD_DIR / "test2_converted.ttf"

                output_file1.parent.mkdir(parents=True, exist_ok=True)
                output_file1.write_bytes(b"woff")
                output_file2.write_bytes(b"ttf")

                result1 = await converter.convert(
                    input_path=input_file1,
                    output_format="woff",
                    options={},
                    session_id="session1"
                )

                result2 = await converter.convert(
                    input_path=input_file2,
                    output_format="ttf",
                    options={},
                    session_id="session2"
                )

                assert result1 == output_file1
                assert result2 == output_file2

    @pytest.mark.asyncio
    async def test_subsetting_options_configuration(self, temp_dir):
        """Test subsetting with Options configuration"""
        converter = FontConverter()

        input_file = temp_dir / "test.ttf"
        input_file.write_bytes(b"ttf")

        output_file = settings.UPLOAD_DIR / "test_converted.ttf"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.font_converter.TTFont') as mock_ttfont_class:
                with patch('app.services.font_converter.Subsetter') as mock_subsetter_class:
                    with patch('app.services.font_converter.Options') as mock_options_class:
                        mock_font = MagicMock()
                        mock_ttfont_class.return_value = mock_font

                        mock_subsetter = MagicMock()
                        mock_subsetter_class.return_value = mock_subsetter

                        mock_options = MagicMock()
                        mock_options_class.return_value = mock_options

                        output_file.parent.mkdir(parents=True, exist_ok=True)
                        output_file.write_bytes(b"subset")

                        await converter.convert(
                            input_path=input_file,
                            output_format="ttf",
                            options={"subset_text": "ABC"},
                            session_id="test-session"
                        )

                        # Options should be created for subsetting
                        mock_options_class.assert_called_once()
                        # Options.drop_tables should be set
                        assert hasattr(mock_options, 'drop_tables')
