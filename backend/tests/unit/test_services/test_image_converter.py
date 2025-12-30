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
