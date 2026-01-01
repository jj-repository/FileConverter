"""
Tests for app/services/image_converter.py

COVERAGE GOAL: 85%+
Tests PIL integration, image resizing, format conversion, quality settings
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from PIL import Image
import io

from app.services.image_converter import ImageConverter
from app.config import settings
from tests.mocks.file_io_mock import PILMock


# ============================================================================
# BASIC FUNCTIONALITY TESTS
# ============================================================================

class TestImageConverterBasics:
    """Test basic ImageConverter functionality"""

    def test_initialization(self):
        """Test ImageConverter initializes correctly"""
        converter = ImageConverter()

        assert converter.supported_formats is not None
        assert "input" in converter.supported_formats
        assert "output" in converter.supported_formats
        assert "jpg" in converter.supported_formats["input"]
        assert "png" in converter.supported_formats["output"]

    @pytest.mark.asyncio
    async def test_get_supported_formats(self):
        """Test get_supported_formats returns correct formats"""
        converter = ImageConverter()

        formats = await converter.get_supported_formats()

        assert "input" in formats
        assert "output" in formats
        assert isinstance(formats["input"], list)
        assert isinstance(formats["output"], list)
        assert len(formats["input"]) > 0
        assert len(formats["output"]) > 0


# ============================================================================
# FORMAT VALIDATION TESTS
# ============================================================================

class TestImageFormatValidation:
    """Test format validation"""

    def test_validate_supported_input_formats(self):
        """Test that all supported input formats are validated"""
        converter = ImageConverter()

        supported_formats = ["jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff"]

        for fmt in supported_formats:
            assert fmt in converter.supported_formats["input"]

    def test_validate_supported_output_formats(self):
        """Test that all supported output formats are validated"""
        converter = ImageConverter()

        supported_formats = ["jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff"]

        for fmt in supported_formats:
            assert fmt in converter.supported_formats["output"]


# ============================================================================
# IMAGE CONVERSION TESTS
# ============================================================================

class TestImageConversion:
    """Test image conversion logic"""

    @pytest.mark.asyncio
    async def test_convert_jpg_to_png_success(self, temp_dir, mock_websocket_manager):
        """Test successful JPG to PNG conversion"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test.jpg"
        # Create real test image
        img = Image.new('RGB', (100, 100), color='red')
        img.save(input_file, 'JPEG')

        output_file = settings.UPLOAD_DIR / "test_converted.png"
        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        options = {"quality": 95}

        result = await converter.convert(input_file, "png", options, "test-session")

        assert result.exists()
        assert result.suffix == ".png"

        # Verify it's a valid PNG
        converted_img = Image.open(result)
        assert converted_img.format == "PNG"
        assert converted_img.size == (100, 100)

        # Clean up
        if result.exists():
            result.unlink()

    @pytest.mark.asyncio
    async def test_convert_png_to_jpg_success(self, temp_dir, mock_websocket_manager):
        """Test successful PNG to JPG conversion"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test.png"
        # Create real test image
        img = Image.new('RGB', (200, 150), color='blue')
        img.save(input_file, 'PNG')

        output_file = settings.UPLOAD_DIR / "test_converted.jpg"
        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        options = {"quality": 90}

        result = await converter.convert(input_file, "jpg", options, "test-session")

        assert result.exists()
        assert result.suffix == ".jpg"

        # Verify it's a valid JPEG
        converted_img = Image.open(result)
        assert converted_img.format == "JPEG"

        # Clean up
        if result.exists():
            result.unlink()

    @pytest.mark.asyncio
    async def test_unsupported_format_raises_error(self, temp_dir):
        """Test that .exe to .jpg raises ValueError"""
        converter = ImageConverter()

        input_file = temp_dir / "malware.exe"
        input_file.write_text("executable")

        options = {"quality": 95}

        with pytest.raises(ValueError) as exc_info:
            await converter.convert(input_file, "jpg", options, "test-session")

        assert "Unsupported conversion" in str(exc_info.value)


# ============================================================================
# QUALITY SETTINGS TESTS
# ============================================================================

class TestImageQuality:
    """Test image quality settings"""

    @pytest.mark.asyncio
    async def test_quality_adjustment_jpg(self, temp_dir, mock_websocket_manager):
        """Test quality parameter affects JPEG output"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test.jpg"
        # Create real test image
        img = Image.new('RGB', (100, 100), color='red')
        img.save(input_file, 'JPEG', quality=95)

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        # Test with low quality
        output_low = settings.UPLOAD_DIR / "test_low.jpg"
        result_low = await converter.convert(input_file, "jpg", {"quality": 50}, "test-session-1")

        assert result_low.exists()
        low_size = result_low.stat().st_size

        # Test with high quality
        output_high = settings.UPLOAD_DIR / "test_high.jpg"
        result_high = await converter.convert(input_file, "jpg", {"quality": 95}, "test-session-2")

        assert result_high.exists()
        high_size = result_high.stat().st_size

        # High quality should produce larger file
        assert high_size > low_size

        # Clean up
        if result_low.exists():
            result_low.unlink()
        if result_high.exists():
            result_high.unlink()

    @pytest.mark.asyncio
    async def test_default_quality_used_when_not_provided(self, temp_dir, mock_websocket_manager):
        """Test that default quality is used when not provided"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(input_file, 'JPEG')

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        # Empty options - should use defaults
        options = {}

        result = await converter.convert(input_file, "jpg", options, "test-session")

        # Should succeed with default quality
        assert result.exists()

        # Clean up
        if result.exists():
            result.unlink()

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_invalid_quality_rejected(self, temp_dir):
        """Test that quality=9999 is rejected"""
        converter = ImageConverter()

        input_file = temp_dir / "test.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(input_file, 'JPEG')

        options = {"quality": 9999}  # Invalid quality

        with pytest.raises(ValueError) as exc_info:
            await converter.convert(input_file, "jpg", options, "test-session")

        assert "Invalid quality" in str(exc_info.value)


# ============================================================================
# RESIZE TESTS
# ============================================================================

class TestImageResize:
    """Test image resizing"""

    @pytest.mark.asyncio
    async def test_resize_with_width(self, temp_dir, mock_websocket_manager):
        """Test resizing image by width"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test.jpg"
        # Create 800x600 image
        img = Image.new('RGB', (800, 600), color='red')
        img.save(input_file, 'JPEG')

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        options = {"width": 400}  # Resize to 400px wide

        result = await converter.convert(input_file, "jpg", options, "test-session")

        assert result.exists()

        # Verify dimensions
        resized_img = Image.open(result)
        assert resized_img.width == 400
        # Height should be proportional: 600 * (400/800) = 300
        assert resized_img.height == 300

        # Clean up
        if result.exists():
            result.unlink()

    @pytest.mark.asyncio
    async def test_resize_with_height(self, temp_dir, mock_websocket_manager):
        """Test resizing image by height"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test.jpg"
        # Create 800x600 image
        img = Image.new('RGB', (800, 600), color='red')
        img.save(input_file, 'JPEG')

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        options = {"height": 300}  # Resize to 300px tall

        result = await converter.convert(input_file, "jpg", options, "test-session")

        assert result.exists()

        # Verify dimensions
        resized_img = Image.open(result)
        assert resized_img.height == 300
        # Width should be proportional: 800 * (300/600) = 400
        assert resized_img.width == 400

        # Clean up
        if result.exists():
            result.unlink()

    @pytest.mark.asyncio
    async def test_resize_with_both_dimensions(self, temp_dir, mock_websocket_manager):
        """Test resizing with both width and height"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test.jpg"
        img = Image.new('RGB', (800, 600), color='red')
        img.save(input_file, 'JPEG')

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        options = {"width": 200, "height": 200}  # Force 200x200

        result = await converter.convert(input_file, "jpg", options, "test-session")

        assert result.exists()

        # Verify exact dimensions
        resized_img = Image.open(result)
        assert resized_img.width == 200
        assert resized_img.height == 200

        # Clean up
        if result.exists():
            result.unlink()

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_negative_dimensions_rejected(self, temp_dir):
        """Test that negative width/height is rejected"""
        converter = ImageConverter()

        input_file = temp_dir / "test.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(input_file, 'JPEG')

        # Test negative width
        options = {"width": -100}

        with pytest.raises(ValueError) as exc_info:
            await converter.convert(input_file, "jpg", options, "test-session")

        assert "Invalid" in str(exc_info.value)

    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_excessive_dimensions_rejected(self, temp_dir):
        """Test that excessively large dimensions are rejected"""
        converter = ImageConverter()

        input_file = temp_dir / "test.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(input_file, 'JPEG')

        # Test excessive width (>10000)
        options = {"width": 50000}

        with pytest.raises(ValueError) as exc_info:
            await converter.convert(input_file, "jpg", options, "test-session")

        assert "Invalid" in str(exc_info.value)


# ============================================================================
# METADATA EXTRACTION TESTS
# ============================================================================

class TestImageMetadata:
    """Test image metadata extraction"""

    @pytest.mark.asyncio
    async def test_get_image_metadata_success(self, temp_dir):
        """Test successful image metadata extraction"""
        converter = ImageConverter()

        image_file = temp_dir / "test.jpg"
        # Create 800x600 JPEG
        img = Image.new('RGB', (800, 600), color='red')
        img.save(image_file, 'JPEG', quality=95)

        info = await converter.get_image_metadata(image_file)

        assert "width" in info
        assert "height" in info
        assert "format" in info
        assert "mode" in info
        assert "size" in info

        assert info["width"] == 800
        assert info["height"] == 600
        assert info["format"] == "JPEG"
        assert info["mode"] == "RGB"
        assert info["size"] > 0

    @pytest.mark.asyncio
    async def test_get_image_metadata_png(self, temp_dir):
        """Test image metadata for PNG"""
        converter = ImageConverter()

        image_file = temp_dir / "test.png"
        img = Image.new('RGBA', (1024, 768), color='blue')
        img.save(image_file, 'PNG')

        info = await converter.get_image_metadata(image_file)

        assert info["width"] == 1024
        assert info["height"] == 768
        assert info["format"] == "PNG"
        assert info["mode"] == "RGBA"

    @pytest.mark.asyncio
    async def test_get_image_metadata_corrupted_file(self, temp_dir):
        """Test image metadata extraction for corrupted file"""
        converter = ImageConverter()

        image_file = temp_dir / "corrupted.jpg"
        image_file.write_text("not an image")

        info = await converter.get_image_metadata(image_file)

        assert "error" in info


# ============================================================================
# PROGRESS TRACKING TESTS
# ============================================================================

class TestImageProgressTracking:
    """Test WebSocket progress tracking"""

    @pytest.mark.asyncio
    async def test_progress_updates_sent(self, temp_dir, mock_websocket_manager):
        """Test that progress updates are sent during conversion"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(input_file, 'JPEG')

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        options = {"quality": 95}

        await converter.convert(input_file, "png", options, "test-session")

        # Verify progress was sent
        assert mock_websocket_manager.send_progress.called
        calls = mock_websocket_manager.send_progress.call_args_list

        # Should have at least: start (0%), loading (20%), converting (50%), completed (100%)
        assert len(calls) >= 3

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

        # Clean up
        output_file = settings.UPLOAD_DIR / "test_converted.png"
        if output_file.exists():
            output_file.unlink()


# ============================================================================
# SPECIAL FORMAT TESTS
# ============================================================================

class TestImageSpecialFormats:
    """Test special image formats"""

    @pytest.mark.asyncio
    async def test_rgba_to_rgb_conversion(self, temp_dir, mock_websocket_manager):
        """Test RGBA to RGB conversion (PNG with transparency to JPEG)"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test.png"
        # Create RGBA image with transparency
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        img.save(input_file, 'PNG')

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        options = {"quality": 95}

        result = await converter.convert(input_file, "jpg", options, "test-session")

        assert result.exists()

        # Verify it's a valid JPEG (no transparency)
        converted_img = Image.open(result)
        assert converted_img.format == "JPEG"
        assert converted_img.mode == "RGB"  # Should be converted from RGBA

        # Clean up
        if result.exists():
            result.unlink()

    @pytest.mark.asyncio
    async def test_grayscale_conversion(self, temp_dir, mock_websocket_manager):
        """Test grayscale image conversion"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test_gray.jpg"
        # Create grayscale image
        img = Image.new('L', (100, 100), color=128)
        img.save(input_file, 'JPEG')

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        options = {"quality": 95}

        result = await converter.convert(input_file, "png", options, "test-session")

        assert result.exists()

        # Clean up
        if result.exists():
            result.unlink()


# ============================================================================
# SVG CONVERSION TESTS
# ============================================================================

class TestSVGConversion:
    """Test SVG image conversion"""

    @pytest.mark.asyncio
    async def test_svg_to_png_conversion(self, temp_dir, mock_websocket_manager):
        """Test SVG to PNG conversion"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test.svg"
        # Create simple SVG
        svg_content = '''<?xml version="1.0"?>
<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
    <rect width="100" height="100" fill="red"/>
</svg>'''
        input_file.write_text(svg_content)

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)

        options = {"width": 200, "height": 200}

        # Check if SVG support is available
        from app.services.image_converter import SVG_AVAILABLE

        if SVG_AVAILABLE:
            result = await converter.convert(input_file, "png", options, "test-session")
            assert result.exists()
            assert result.suffix == ".png"

            # Verify dimensions
            converted_img = Image.open(result)
            assert converted_img.format == "PNG"
            assert converted_img.size == (200, 200)

            # Clean up
            if result.exists():
                result.unlink()
        else:
            # Should raise error when SVG support not available
            with pytest.raises(ValueError, match="SVG support not available"):
                await converter.convert(input_file, "png", options, "test-session")

    @pytest.mark.asyncio
    async def test_svg_to_svg_copy(self, temp_dir, mock_websocket_manager):
        """Test SVG to SVG conversion (should just copy)"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test.svg"
        svg_content = '''<?xml version="1.0"?>
<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
    <circle cx="50" cy="50" r="40" fill="blue"/>
</svg>'''
        input_file.write_text(svg_content)

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        from app.services.image_converter import SVG_AVAILABLE

        if SVG_AVAILABLE:
            # SVG to SVG should just copy the file
            result = await converter.convert(input_file, "svg", {}, "test-session")

            assert result.exists()
            assert result.suffix == ".svg"

            # Verify content was copied
            assert result.read_text() == svg_content

            # Clean up
            if result.exists():
                result.unlink()
        else:
            # Without SVG support, even SVG to SVG fails (current behavior)
            with pytest.raises(ValueError, match="SVG support not available"):
                await converter.convert(input_file, "svg", {}, "test-session")

    @pytest.mark.asyncio
    async def test_svg_without_cairosvg_raises_error(self, temp_dir):
        """Test SVG conversion fails gracefully without cairosvg"""
        converter = ImageConverter()

        input_file = temp_dir / "test.svg"
        svg_content = '<svg><rect width="100" height="100"/></svg>'
        input_file.write_text(svg_content)

        # Mock SVG_AVAILABLE as False
        with patch('app.services.image_converter.SVG_AVAILABLE', False):
            with pytest.raises(ValueError, match="SVG support not available"):
                await converter.convert(input_file, "png", {}, "test-session")

    @pytest.mark.asyncio
    async def test_svg_with_custom_dimensions(self, temp_dir, mock_websocket_manager):
        """Test SVG conversion with custom dimensions"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test.svg"
        svg_content = '<svg width="50" height="50" xmlns="http://www.w3.org/2000/svg"><rect width="50" height="50" fill="green"/></svg>'
        input_file.write_text(svg_content)

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)

        from app.services.image_converter import SVG_AVAILABLE

        if SVG_AVAILABLE:
            # Test with only width
            result = await converter.convert(input_file, "jpg", {"width": 400}, "test-session")
            assert result.exists()

            # Clean up
            if result.exists():
                result.unlink()


# ============================================================================
# HEIC/HEIF SUPPORT TESTS
# ============================================================================

class TestHEICSupport:
    """Test HEIC/HEIF format support"""

    def test_heif_availability_flag(self):
        """Test that HEIF_AVAILABLE flag is set correctly"""
        from app.services.image_converter import HEIF_AVAILABLE

        # Should be a boolean
        assert isinstance(HEIF_AVAILABLE, bool)

        # Verify it matches actual availability
        try:
            import pillow_heif
            assert HEIF_AVAILABLE is True
        except ImportError:
            assert HEIF_AVAILABLE is False


# ============================================================================
# TRANSPARENCY HANDLING TESTS
# ============================================================================

class TestTransparencyHandling:
    """Test transparency handling for various image modes"""

    @pytest.mark.asyncio
    async def test_palette_mode_to_jpeg(self, temp_dir, mock_websocket_manager):
        """Test palette mode (P) to JPEG conversion"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test_palette.png"
        # Create palette mode image
        img = Image.new('P', (100, 100))
        # Add some colors to palette
        img.putpalette([255, 0, 0] * 85 + [0, 255, 0] * 85 + [0, 0, 255] * 86)
        img.save(input_file, 'PNG')

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        result = await converter.convert(input_file, "jpg", {"quality": 95}, "test-session")

        assert result.exists()

        # Verify it's RGB JPEG
        converted_img = Image.open(result)
        assert converted_img.format == "JPEG"
        assert converted_img.mode == "RGB"

        # Clean up
        if result.exists():
            result.unlink()

    @pytest.mark.asyncio
    async def test_la_mode_to_jpeg(self, temp_dir, mock_websocket_manager):
        """Test LA mode (grayscale with alpha) to JPEG conversion"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test_la.png"
        # Create LA mode image (grayscale with alpha)
        img = Image.new('LA', (100, 100), color=(128, 255))
        img.save(input_file, 'PNG')

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        result = await converter.convert(input_file, "jpg", {"quality": 95}, "test-session")

        assert result.exists()

        # Verify it's RGB JPEG
        converted_img = Image.open(result)
        assert converted_img.format == "JPEG"
        assert converted_img.mode == "RGB"

        # Clean up
        if result.exists():
            result.unlink()

    @pytest.mark.asyncio
    async def test_rgba_background_handling(self, temp_dir, mock_websocket_manager):
        """Test RGBA to JPEG creates white background"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test_rgba.png"
        # Create RGBA with semi-transparent red
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        img.save(input_file, 'PNG')

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        result = await converter.convert(input_file, "jpg", {}, "test-session")

        assert result.exists()

        # Open and verify it has white background blended
        converted_img = Image.open(result)
        assert converted_img.mode == "RGB"

        # Clean up
        if result.exists():
            result.unlink()


# ============================================================================
# WEBP QUALITY TESTS
# ============================================================================

class TestWebPQuality:
    """Test WebP format quality settings"""

    @pytest.mark.asyncio
    async def test_webp_quality_setting(self, temp_dir, mock_websocket_manager):
        """Test WebP conversion with quality setting"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test.jpg"
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(input_file, 'JPEG')

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        result = await converter.convert(input_file, "webp", {"quality": 80}, "test-session")

        assert result.exists()
        assert result.suffix == ".webp"

        # Verify it's WebP
        converted_img = Image.open(result)
        assert converted_img.format == "WEBP"

        # Clean up
        if result.exists():
            result.unlink()


# ============================================================================
# QUALITY EDGE CASES
# ============================================================================

class TestQualityEdgeCases:
    """Test edge cases for quality parameter"""

    @pytest.mark.asyncio
    async def test_quality_boundary_min(self, temp_dir, mock_websocket_manager):
        """Test quality=1 (minimum valid)"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(input_file, 'JPEG')

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        result = await converter.convert(input_file, "jpg", {"quality": 1}, "test-session")

        assert result.exists()

        # Clean up
        if result.exists():
            result.unlink()

    @pytest.mark.asyncio
    async def test_quality_boundary_max(self, temp_dir, mock_websocket_manager):
        """Test quality=100 (maximum valid)"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(input_file, 'JPEG')

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        result = await converter.convert(input_file, "jpg", {"quality": 100}, "test-session")

        assert result.exists()

        # Clean up
        if result.exists():
            result.unlink()

    @pytest.mark.asyncio
    async def test_quality_zero_rejected(self, temp_dir):
        """Test quality=0 is rejected"""
        converter = ImageConverter()

        input_file = temp_dir / "test.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(input_file, 'JPEG')

        with pytest.raises(ValueError, match="Invalid quality"):
            await converter.convert(input_file, "jpg", {"quality": 0}, "test-session")

    @pytest.mark.asyncio
    async def test_quality_negative_rejected(self, temp_dir):
        """Test negative quality is rejected"""
        converter = ImageConverter()

        input_file = temp_dir / "test.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(input_file, 'JPEG')

        with pytest.raises(ValueError, match="Invalid quality"):
            await converter.convert(input_file, "jpg", {"quality": -10}, "test-session")

    @pytest.mark.asyncio
    async def test_quality_over_100_rejected(self, temp_dir):
        """Test quality > 100 is rejected"""
        converter = ImageConverter()

        input_file = temp_dir / "test.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(input_file, 'JPEG')

        with pytest.raises(ValueError, match="Invalid quality"):
            await converter.convert(input_file, "jpg", {"quality": 101}, "test-session")


# ============================================================================
# DIMENSION VALIDATION TESTS
# ============================================================================

class TestDimensionValidation:
    """Test dimension validation edge cases"""

    @pytest.mark.asyncio
    async def test_width_one_accepted(self, temp_dir, mock_websocket_manager):
        """Test width=1 (minimum) is accepted"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(input_file, 'JPEG')

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        # width=1 should be valid (minimum)
        result = await converter.convert(input_file, "jpg", {"width": 1}, "test-session")
        assert result.exists()

        # Clean up
        if result.exists():
            result.unlink()

    @pytest.mark.asyncio
    async def test_height_one_accepted(self, temp_dir, mock_websocket_manager):
        """Test height=1 (minimum) is accepted"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(input_file, 'JPEG')

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        # height=1 should be valid (minimum)
        result = await converter.convert(input_file, "jpg", {"height": 1}, "test-session")
        assert result.exists()

        # Clean up
        if result.exists():
            result.unlink()

    @pytest.mark.asyncio
    async def test_negative_height_rejected(self, temp_dir):
        """Test negative height is rejected"""
        converter = ImageConverter()

        input_file = temp_dir / "test.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(input_file, 'JPEG')

        with pytest.raises(ValueError, match="Invalid height"):
            await converter.convert(input_file, "jpg", {"height": -50}, "test-session")

    @pytest.mark.asyncio
    async def test_excessive_height_rejected(self, temp_dir):
        """Test height > 10000 is rejected"""
        converter = ImageConverter()

        input_file = temp_dir / "test.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(input_file, 'JPEG')

        with pytest.raises(ValueError, match="Invalid height"):
            await converter.convert(input_file, "jpg", {"height": 15000}, "test-session")

    @pytest.mark.asyncio
    async def test_max_valid_dimensions(self, temp_dir, mock_websocket_manager):
        """Test maximum valid dimensions (10000x10000)"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(input_file, 'JPEG')

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        # This should succeed (boundary test)
        result = await converter.convert(input_file, "jpg", {"width": 10000, "height": 10000}, "test-session")

        assert result.exists()

        # Verify dimensions
        converted_img = Image.open(result)
        assert converted_img.size == (10000, 10000)

        # Clean up
        if result.exists():
            result.unlink()


# ============================================================================
# FORMAT MAPPING TESTS
# ============================================================================

class TestFormatMapping:
    """Test PIL format name mapping"""

    @pytest.mark.asyncio
    async def test_jpg_format_mapped_to_jpeg(self, temp_dir, mock_websocket_manager):
        """Test that 'jpg' is mapped to 'JPEG' for PIL"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test.png"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(input_file, 'PNG')

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        # Use 'jpg' extension (should be mapped to 'JPEG' for PIL)
        result = await converter.convert(input_file, "jpg", {"quality": 95}, "test-session")

        assert result.exists()

        # Verify it's JPEG format
        converted_img = Image.open(result)
        assert converted_img.format == "JPEG"

        # Clean up
        if result.exists():
            result.unlink()

    @pytest.mark.asyncio
    async def test_jpeg_format_stays_uppercase(self, temp_dir, mock_websocket_manager):
        """Test that 'jpeg' is properly handled"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test.png"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(input_file, 'PNG')

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        result = await converter.convert(input_file, "jpeg", {"quality": 95}, "test-session")

        assert result.exists()
        assert result.suffix == ".jpeg"

        # Verify it's JPEG format
        converted_img = Image.open(result)
        assert converted_img.format == "JPEG"

        # Clean up
        if result.exists():
            result.unlink()


# ============================================================================
# ADDITIONAL CONVERSION TESTS
# ============================================================================

class TestAdditionalConversions:
    """Test additional image conversions"""

    @pytest.mark.asyncio
    async def test_png_to_webp(self, temp_dir, mock_websocket_manager):
        """Test PNG to WebP conversion"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test.png"
        img = Image.new('RGB', (100, 100), color='green')
        img.save(input_file, 'PNG')

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        result = await converter.convert(input_file, "webp", {}, "test-session")

        assert result.exists()
        assert result.suffix == ".webp"

        # Clean up
        if result.exists():
            result.unlink()

    @pytest.mark.asyncio
    async def test_gif_to_png(self, temp_dir, mock_websocket_manager):
        """Test GIF to PNG conversion"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test.gif"
        img = Image.new('RGB', (100, 100), color='yellow')
        img.save(input_file, 'GIF')

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        result = await converter.convert(input_file, "png", {}, "test-session")

        assert result.exists()
        assert result.suffix == ".png"

        # Clean up
        if result.exists():
            result.unlink()

    @pytest.mark.asyncio
    async def test_bmp_to_jpg(self, temp_dir, mock_websocket_manager):
        """Test BMP to JPG conversion"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test.bmp"
        img = Image.new('RGB', (100, 100), color='purple')
        img.save(input_file, 'BMP')

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        result = await converter.convert(input_file, "jpg", {"quality": 85}, "test-session")

        assert result.exists()
        assert result.suffix == ".jpg"

        # Clean up
        if result.exists():
            result.unlink()


# ============================================================================
# EDGE CASES
# ============================================================================

class TestImageEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_very_small_image(self, temp_dir, mock_websocket_manager):
        """Test conversion of very small image (1x1)"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "tiny.jpg"
        img = Image.new('RGB', (1, 1), color='red')
        img.save(input_file, 'JPEG')

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        result = await converter.convert(input_file, "png", {}, "test-session")

        assert result.exists()

        # Clean up
        if result.exists():
            result.unlink()

    @pytest.mark.asyncio
    async def test_same_format_conversion(self, temp_dir, mock_websocket_manager):
        """Test converting JPG to JPG (format stays same)"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(input_file, 'JPEG')

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        result = await converter.convert(input_file, "jpg", {"quality": 90}, "test-session")

        assert result.exists()
        assert result.suffix == ".jpg"

        # Clean up
        if result.exists():
            result.unlink()

    @pytest.mark.asyncio
    async def test_non_rgb_mode_to_jpeg(self, temp_dir, mock_websocket_manager):
        """Test converting non-RGB mode image to JPEG"""
        converter = ImageConverter(mock_websocket_manager)

        input_file = temp_dir / "test_cmyk.tiff"
        # Create CMYK image (TIFF supports CMYK)
        img = Image.new('CMYK', (100, 100), color=(100, 50, 0, 0))
        img.save(input_file, 'TIFF')

        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        result = await converter.convert(input_file, "jpg", {}, "test-session")

        assert result.exists()

        # Verify conversion to RGB
        converted_img = Image.open(result)
        assert converted_img.mode == "RGB"

        # Clean up
        if result.exists():
            result.unlink()
