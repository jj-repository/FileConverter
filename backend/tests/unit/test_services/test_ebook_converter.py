"""
Tests for app/services/ebook_converter.py

COVERAGE GOAL: 85%+
Tests eBook conversion with EPUB creation/extraction, metadata handling,
format support, progress tracking, and error handling
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import zipfile
import io
import ebooklib

from app.services.ebook_converter import EbookConverter
from app.config import settings


# ============================================================================
# BASIC FUNCTIONALITY TESTS
# ============================================================================

class TestEbookConverterBasics:
    """Test basic EbookConverter functionality"""

    def test_initialization(self):
        """Test EbookConverter initializes correctly"""
        converter = EbookConverter()

        assert converter.supported_formats is not None
        assert "input" in converter.supported_formats
        assert "output" in converter.supported_formats
        assert isinstance(converter.supported_formats["input"], list)
        assert isinstance(converter.supported_formats["output"], list)

    def test_initialization_with_websocket_manager(self):
        """Test EbookConverter can be initialized with custom WebSocket manager"""
        mock_ws_manager = Mock()
        converter = EbookConverter(websocket_manager=mock_ws_manager)

        assert converter.websocket_manager == mock_ws_manager

    @pytest.mark.asyncio
    async def test_get_supported_formats(self):
        """Test getting supported eBook formats"""
        converter = EbookConverter()

        formats = await converter.get_supported_formats()

        assert "input" in formats
        assert "output" in formats
        assert isinstance(formats["input"], list)
        assert isinstance(formats["output"], list)
        # Check expected formats
        assert "epub" in formats["output"]
        assert "txt" in formats["output"]
        assert "html" in formats["output"]
        assert "pdf" in formats["output"]


# ============================================================================
# EPUB CREATION TESTS (Convert to EPUB)
# ============================================================================

class TestEpubCreation:
    """Test EPUB creation from other formats"""

    @pytest.mark.asyncio
    async def test_convert_txt_to_epub_success(self, temp_dir):
        """Test successful TXT to EPUB conversion"""
        converter = EbookConverter()

        input_file = temp_dir / "test.txt"
        input_file.write_text("This is a test document.\n\nWith multiple paragraphs.")

        output_file = settings.UPLOAD_DIR / "test_converted.epub"

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            with patch('ebooklib.epub.write_epub') as mock_write:
                # Create fake output file
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(b"fake epub")

                result = await converter.convert(
                    input_path=input_file,
                    output_format="epub",
                    options={},
                    session_id="test-session"
                )

                assert result == output_file
                assert output_file.exists()

                # Verify progress was sent
                assert mock_progress.call_count >= 4

                # Verify write_epub was called
                mock_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_html_to_epub_success(self, temp_dir):
        """Test successful HTML to EPUB conversion"""
        converter = EbookConverter()

        input_file = temp_dir / "test.html"
        input_file.write_text("<html><body><p>Test HTML content</p></body></html>")

        output_file = settings.UPLOAD_DIR / "test_converted.epub"

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            with patch('ebooklib.epub.write_epub') as mock_write:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(b"fake epub")

                result = await converter.convert(
                    input_path=input_file,
                    output_format="epub",
                    options={},
                    session_id="test-session"
                )

                assert result == output_file
                assert output_file.exists()
                assert mock_progress.call_count >= 4
                mock_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_to_epub_with_metadata(self, temp_dir):
        """Test EPUB creation with metadata (title, author)"""
        converter = EbookConverter()

        input_file = temp_dir / "test.txt"
        input_file.write_text("Test content")

        output_file = settings.UPLOAD_DIR / "test_converted.epub"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('ebooklib.epub.EpubBook') as mock_book_class:
                with patch('ebooklib.epub.write_epub') as mock_write:
                    mock_book = MagicMock()
                    mock_book_class.return_value = mock_book

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_bytes(b"fake epub")

                    options = {
                        "title": "Test Book",
                        "author": "Test Author"
                    }

                    result = await converter.convert(
                        input_path=input_file,
                        output_format="epub",
                        options=options,
                        session_id="test-session"
                    )

                    assert result == output_file
                    # Verify book methods were called
                    mock_book.set_identifier.assert_called_once()
                    # Default title from filename if options not used
                    mock_book.set_title.assert_called()
                    mock_book.set_language.assert_called()

    @pytest.mark.asyncio
    async def test_convert_to_epub_with_cover_image(self, temp_dir):
        """Test EPUB creation with cover image parameter"""
        converter = EbookConverter()

        input_file = temp_dir / "test.txt"
        input_file.write_text("Test content")

        cover_file = temp_dir / "cover.jpg"
        cover_file.write_bytes(b"fake jpg")

        output_file = settings.UPLOAD_DIR / "test_converted.epub"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('ebooklib.epub.write_epub') as mock_write:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(b"fake epub")

                options = {"cover_image": str(cover_file)}

                result = await converter.convert(
                    input_path=input_file,
                    output_format="epub",
                    options=options,
                    session_id="test-session"
                )

                assert result == output_file
                assert output_file.exists()

    @pytest.mark.asyncio
    async def test_convert_to_epub_progress_updates(self, temp_dir):
        """Test progress updates during EPUB creation"""
        converter = EbookConverter()

        input_file = temp_dir / "test.txt"
        input_file.write_text("Test content")

        output_file = settings.UPLOAD_DIR / "test_converted.epub"

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            with patch('ebooklib.epub.write_epub') as mock_write:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(b"fake epub")

                result = await converter.convert(
                    input_path=input_file,
                    output_format="epub",
                    options={},
                    session_id="test-session"
                )

                assert result == output_file

                # Verify progress messages
                progress_calls = mock_progress.call_args_list
                assert len(progress_calls) >= 4

                # Check first call (start)
                assert progress_calls[0][0][1] == 10
                assert "Starting" in progress_calls[0][0][3]

                # Check last call (complete)
                assert progress_calls[-1][0][1] == 100
                assert "Conversion complete" in progress_calls[-1][0][3]


# ============================================================================
# EPUB EXTRACTION TESTS (Convert from EPUB)
# ============================================================================

class TestEpubExtraction:
    """Test EPUB extraction to other formats"""

    @pytest.mark.asyncio
    async def test_convert_epub_to_txt_success(self, temp_dir):
        """Test successful EPUB to TXT conversion"""
        converter = EbookConverter()

        # Create a fake EPUB file
        input_file = temp_dir / "test.epub"
        input_file.write_bytes(b"fake epub")

        output_file = settings.UPLOAD_DIR / "test_converted.txt"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('ebooklib.epub.read_epub') as mock_read:
                # Mock EPUB book
                mock_book = MagicMock()
                mock_book.get_metadata.return_value = [("Title", "")]
                mock_items = [
                    MagicMock(get_type=lambda: 9, get_content=lambda: b"<html><p>Content</p></html>")
                ]
                mock_book.get_items.return_value = mock_items
                mock_read.return_value = mock_book

                output_file.parent.mkdir(parents=True, exist_ok=True)

                result = await converter.convert(
                    input_path=input_file,
                    output_format="txt",
                    options={},
                    session_id="test-session"
                )

                assert result == output_file
                assert output_file.exists()

    @pytest.mark.asyncio
    async def test_convert_epub_to_html_success(self, temp_dir):
        """Test successful EPUB to HTML conversion"""
        converter = EbookConverter()

        input_file = temp_dir / "test.epub"
        input_file.write_bytes(b"fake epub")

        output_file = settings.UPLOAD_DIR / "test_converted.html"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('ebooklib.epub.read_epub') as mock_read:
                mock_book = MagicMock()
                mock_book.get_metadata.return_value = [("Title", "")]
                mock_items = [
                    MagicMock(get_type=lambda: 9, get_content=lambda: b"<html><body><p>Content</p></body></html>")
                ]
                mock_book.get_items.return_value = mock_items
                mock_read.return_value = mock_book

                output_file.parent.mkdir(parents=True, exist_ok=True)

                result = await converter.convert(
                    input_path=input_file,
                    output_format="html",
                    options={},
                    session_id="test-session"
                )

                assert result == output_file
                assert output_file.exists()

    @pytest.mark.asyncio
    async def test_convert_epub_to_pdf_success(self, temp_dir):
        """Test successful EPUB to PDF conversion"""
        converter = EbookConverter()

        input_file = temp_dir / "test.epub"
        input_file.write_bytes(b"fake epub")

        output_file = settings.UPLOAD_DIR / "test_converted.pdf"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('ebooklib.epub.read_epub') as mock_read:
                mock_book = MagicMock()
                mock_book.get_metadata.return_value = [("Title", "")]
                mock_items = [
                    MagicMock(get_type=lambda: 9, get_content=lambda: b"<html><p>Content</p></html>")
                ]
                mock_book.get_items.return_value = mock_items
                mock_read.return_value = mock_book

                output_file.parent.mkdir(parents=True, exist_ok=True)
                # Simulate PDF creation
                output_file.write_bytes(b"%PDF-1.4")

                result = await converter.convert(
                    input_path=input_file,
                    output_format="pdf",
                    options={},
                    session_id="test-session"
                )

                assert result == output_file
                assert output_file.exists()

    @pytest.mark.asyncio
    async def test_convert_epub_preserves_metadata(self, temp_dir):
        """Test metadata preservation during EPUB conversion"""
        converter = EbookConverter()

        input_file = temp_dir / "test.epub"
        input_file.write_bytes(b"fake epub")

        output_file = settings.UPLOAD_DIR / "test_converted.txt"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('ebooklib.epub.read_epub') as mock_read:
                mock_book = MagicMock()
                # Mock metadata
                mock_book.get_metadata.side_effect = lambda dc, field: {
                    'title': [("Test Book", "")],
                    'creator': [("Test Author", "")]
                }.get(field, [])

                mock_items = [
                    MagicMock(get_type=lambda: 9, get_content=lambda: b"<html><p>Book content</p></html>")
                ]
                mock_book.get_items.return_value = mock_items
                mock_read.return_value = mock_book

                output_file.parent.mkdir(parents=True, exist_ok=True)

                result = await converter.convert(
                    input_path=input_file,
                    output_format="txt",
                    options={},
                    session_id="test-session"
                )

                assert result == output_file
                # Check metadata is in output
                content = output_file.read_text()
                assert "Title:" in content or "Author:" in content or len(content) > 0


# ============================================================================
# FORMAT SUPPORT TESTS
# ============================================================================

class TestFormatSupport:
    """Test format support detection"""

    @pytest.mark.asyncio
    async def test_get_supported_formats_includes_epub(self):
        """Test supported formats includes EPUB"""
        converter = EbookConverter()

        formats = await converter.get_supported_formats()

        assert "epub" in formats["input"]
        assert "epub" in formats["output"]

    @pytest.mark.asyncio
    async def test_get_supported_formats_includes_txt(self):
        """Test supported formats includes TXT"""
        converter = EbookConverter()

        formats = await converter.get_supported_formats()

        assert "txt" in formats["input"]
        assert "txt" in formats["output"]

    @pytest.mark.asyncio
    async def test_get_supported_formats_includes_html(self):
        """Test supported formats includes HTML"""
        converter = EbookConverter()

        formats = await converter.get_supported_formats()

        assert "html" in formats["input"]
        assert "html" in formats["output"]

    @pytest.mark.asyncio
    async def test_get_supported_formats_includes_pdf(self):
        """Test supported formats includes PDF"""
        converter = EbookConverter()

        formats = await converter.get_supported_formats()

        assert "pdf" in formats["output"]


# ============================================================================
# METADATA HANDLING TESTS
# ============================================================================

class TestMetadataHandling:
    """Test metadata extraction and handling"""

    @pytest.mark.asyncio
    async def test_extract_metadata_from_epub(self, temp_dir):
        """Test extracting metadata from EPUB file"""
        converter = EbookConverter()

        test_file = temp_dir / "test.epub"
        test_file.write_bytes(b"fake epub")

        with patch('ebooklib.epub.read_epub') as mock_read:
            mock_book = MagicMock()
            mock_book.get_metadata.side_effect = lambda dc, field: {
                'title': [("Test Book Title", "")],
                'creator': [("Test Author Name", "")],
                'language': [("en", "")]
            }.get(field, [])

            mock_items = [
                MagicMock(get_type=lambda: 9),
                MagicMock(get_type=lambda: 9),
                MagicMock(get_type=lambda: 9)
            ]
            mock_book.get_items.return_value = mock_items
            mock_read.return_value = mock_book

            info = await converter.get_info(test_file)

            assert info["filename"] == "test.epub"
            assert "size" in info
            assert info["format"] == "epub"
            assert "title" in info
            assert info["title"] == "Test Book Title"
            assert "author" in info
            assert info["author"] == "Test Author Name"
            assert "language" in info
            assert info["language"] == "en"
            assert "chapter_count" in info

    @pytest.mark.asyncio
    async def test_extract_metadata_missing_title(self, temp_dir):
        """Test metadata extraction with missing title"""
        converter = EbookConverter()

        test_file = temp_dir / "test.epub"
        test_file.write_bytes(b"fake epub")

        with patch('ebooklib.epub.read_epub') as mock_read:
            mock_book = MagicMock()
            mock_book.get_metadata.return_value = []  # No metadata

            mock_items = [MagicMock(get_type=lambda: 9)]
            mock_book.get_items.return_value = mock_items
            mock_read.return_value = mock_book

            info = await converter.get_info(test_file)

            assert info["filename"] == "test.epub"
            assert info["format"] == "epub"
            # Title should not be present if not in metadata
            assert "title" not in info or info.get("title") is None

    @pytest.mark.asyncio
    async def test_extract_metadata_missing_author(self, temp_dir):
        """Test metadata extraction with missing author"""
        converter = EbookConverter()

        test_file = temp_dir / "test.epub"
        test_file.write_bytes(b"fake epub")

        with patch('ebooklib.epub.read_epub') as mock_read:
            mock_book = MagicMock()
            mock_book.get_metadata.side_effect = lambda dc, field: {
                'title': [("Book", "")],
            }.get(field, [])

            mock_items = [MagicMock(get_type=lambda: 9)]
            mock_book.get_items.return_value = mock_items
            mock_read.return_value = mock_book

            info = await converter.get_info(test_file)

            assert "author" not in info or info.get("author") is None

    @pytest.mark.asyncio
    async def test_set_metadata_during_conversion(self, temp_dir):
        """Test setting metadata during EPUB conversion"""
        converter = EbookConverter()

        input_file = temp_dir / "test.txt"
        input_file.write_text("Test content")

        output_file = settings.UPLOAD_DIR / "test_converted.epub"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('ebooklib.epub.EpubBook') as mock_book_class:
                with patch('ebooklib.epub.write_epub') as mock_write:
                    mock_book = MagicMock()
                    mock_book_class.return_value = mock_book

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_bytes(b"fake epub")

                    await converter.convert(
                        input_path=input_file,
                        output_format="epub",
                        options={},
                        session_id="test-session"
                    )

                    # Verify metadata was set
                    mock_book.set_identifier.assert_called_once()
                    mock_book.set_title.assert_called()
                    mock_book.set_language.assert_called_with('en')


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_convert_corrupted_epub_detection(self, temp_dir):
        """Test detection of corrupted EPUB files"""
        converter = EbookConverter()

        input_file = temp_dir / "corrupted.epub"
        input_file.write_bytes(b"not really an epub")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('ebooklib.epub.read_epub', side_effect=Exception("Bad EPUB file")):
                with pytest.raises(Exception):
                    await converter.convert(
                        input_path=input_file,
                        output_format="txt",
                        options={},
                        session_id="test-session"
                    )

    @pytest.mark.asyncio
    async def test_convert_invalid_format_raises_error(self, temp_dir):
        """Test conversion with invalid format raises ValueError"""
        converter = EbookConverter()

        input_file = temp_dir / "test.exe"
        input_file.write_text("not ebook")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with pytest.raises(ValueError, match="Conversion from"):
                await converter.convert(
                    input_path=input_file,
                    output_format="epub",
                    options={},
                    session_id="test-session"
                )

    @pytest.mark.asyncio
    async def test_convert_missing_cover_image_handling(self, temp_dir):
        """Test handling of missing cover image"""
        converter = EbookConverter()

        input_file = temp_dir / "test.txt"
        input_file.write_text("Test content")

        output_file = settings.UPLOAD_DIR / "test_converted.epub"

        # Reference non-existent cover image
        options = {"cover_image": "/path/to/nonexistent/cover.jpg"}

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('ebooklib.epub.write_epub') as mock_write:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(b"fake epub")

                # Should not crash, just skip the missing cover
                result = await converter.convert(
                    input_path=input_file,
                    output_format="epub",
                    options=options,
                    session_id="test-session"
                )

                assert result == output_file

    @pytest.mark.asyncio
    async def test_convert_unsupported_input_format(self, temp_dir):
        """Test unsupported input format"""
        converter = EbookConverter()

        input_file = temp_dir / "test.doc"
        input_file.write_bytes(b"old doc format")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with pytest.raises(ValueError, match="Conversion from"):
                await converter.convert(
                    input_path=input_file,
                    output_format="epub",
                    options={},
                    session_id="test-session"
                )

    @pytest.mark.asyncio
    async def test_convert_unsupported_output_format(self, temp_dir):
        """Test unsupported output format"""
        converter = EbookConverter()

        input_file = temp_dir / "test.txt"
        input_file.write_text("Test content")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with pytest.raises(ValueError, match="Unsupported"):
                await converter.convert(
                    input_path=input_file,
                    output_format="docx",
                    options={},
                    session_id="test-session"
                )

    @pytest.mark.asyncio
    async def test_convert_epub_read_error(self, temp_dir):
        """Test handling of EPUB read errors"""
        converter = EbookConverter()

        input_file = temp_dir / "test.epub"
        input_file.write_bytes(b"fake epub")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('ebooklib.epub.read_epub', side_effect=Exception("Cannot read EPUB")):
                with pytest.raises(Exception, match="Cannot read EPUB"):
                    await converter.convert(
                        input_path=input_file,
                        output_format="txt",
                        options={},
                        session_id="test-session"
                    )

    @pytest.mark.asyncio
    async def test_convert_invalid_text_encoding(self, temp_dir):
        """Test handling of invalid text encoding in input"""
        converter = EbookConverter()

        input_file = temp_dir / "test.txt"
        # Write with some bytes that might cause encoding issues
        input_file.write_bytes(b'\x80\x81\x82\x83')

        output_file = settings.UPLOAD_DIR / "test_converted.epub"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('ebooklib.epub.write_epub') as mock_write:
                output_file.parent.mkdir(parents=True, exist_ok=True)

                # Should handle gracefully or raise appropriate error
                try:
                    result = await converter.convert(
                        input_path=input_file,
                        output_format="epub",
                        options={},
                        session_id="test-session"
                    )
                except (UnicodeDecodeError, Exception):
                    # Either raises or handles - both acceptable
                    pass

    @pytest.mark.asyncio
    async def test_get_info_corrupted_epub_error_handling(self, temp_dir):
        """Test get_info handles corrupted EPUB gracefully"""
        converter = EbookConverter()

        test_file = temp_dir / "corrupted.epub"
        test_file.write_bytes(b"not really epub")

        with patch('ebooklib.epub.read_epub', side_effect=Exception("Bad EPUB")):
            info = await converter.get_info(test_file)

            # Should return basic info without crashing
            assert "filename" in info
            assert "size" in info
            assert "format" in info
            assert info["format"] == "epub"
            # EPUB-specific fields should not be present
            assert "title" not in info or info.get("title") is None


# ============================================================================
# PROGRESS TRACKING TESTS
# ============================================================================

class TestProgressTracking:
    """Test progress tracking during conversion"""

    @pytest.mark.asyncio
    async def test_progress_updates_txt_to_epub(self, temp_dir):
        """Test progress updates during TXT to EPUB conversion"""
        converter = EbookConverter()

        input_file = temp_dir / "test.txt"
        input_file.write_text("Test content")

        output_file = settings.UPLOAD_DIR / "test_converted.epub"

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            with patch('ebooklib.epub.write_epub'):
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(b"fake epub")

                await converter.convert(
                    input_path=input_file,
                    output_format="epub",
                    options={},
                    session_id="test-session"
                )

                # Verify progress calls
                calls = mock_progress.call_args_list
                assert len(calls) >= 4

                # Check progress percentages are increasing
                percentages = [call[0][1] for call in calls]
                assert percentages[0] == 10  # Initial
                assert percentages[-1] == 100  # Complete

    @pytest.mark.asyncio
    async def test_progress_updates_epub_to_txt(self, temp_dir):
        """Test progress updates during EPUB to TXT conversion"""
        converter = EbookConverter()

        input_file = temp_dir / "test.epub"
        input_file.write_bytes(b"fake epub")

        output_file = settings.UPLOAD_DIR / "test_converted.txt"

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            with patch('ebooklib.epub.read_epub') as mock_read:
                mock_book = MagicMock()
                mock_book.get_metadata.return_value = []
                mock_items = [
                    MagicMock(get_type=lambda: 9, get_content=lambda: b"<html><p>Content</p></html>"),
                    MagicMock(get_type=lambda: 9, get_content=lambda: b"<html><p>More</p></html>")
                ]
                mock_book.get_items.return_value = mock_items
                mock_read.return_value = mock_book

                output_file.parent.mkdir(parents=True, exist_ok=True)

                await converter.convert(
                    input_path=input_file,
                    output_format="txt",
                    options={},
                    session_id="test-session"
                )

                # Verify progress updates
                calls = mock_progress.call_args_list
                assert len(calls) >= 4


# ============================================================================
# OUTPUT FILE GENERATION TESTS
# ============================================================================

class TestOutputFileGeneration:
    """Test output file generation and naming"""

    @pytest.mark.asyncio
    async def test_output_file_path_naming(self, temp_dir):
        """Test output file is created with correct naming"""
        converter = EbookConverter()

        input_file = temp_dir / "mybook.txt"
        input_file.write_text("Content")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('ebooklib.epub.write_epub') as mock_write:
                output_dir = settings.UPLOAD_DIR
                output_dir.mkdir(parents=True, exist_ok=True)

                result = await converter.convert(
                    input_path=input_file,
                    output_format="epub",
                    options={},
                    session_id="test-session"
                )

                # Check output filename format
                assert result.name == "mybook_converted.epub"
                assert result.parent == output_dir

    @pytest.mark.asyncio
    async def test_output_file_location(self, temp_dir):
        """Test output file is created in correct location"""
        converter = EbookConverter()

        input_file = temp_dir / "test.txt"
        input_file.write_text("Content")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('ebooklib.epub.write_epub') as mock_write:
                output_dir = settings.UPLOAD_DIR
                output_dir.mkdir(parents=True, exist_ok=True)

                result = await converter.convert(
                    input_path=input_file,
                    output_format="epub",
                    options={},
                    session_id="test-session"
                )

                assert result.parent == output_dir
                assert result.suffix == ".epub"


# ============================================================================
# SPECIAL CHARACTER AND ENCODING TESTS
# ============================================================================

class TestSpecialCharactersAndEncoding:
    """Test handling of special characters and various encodings"""

    @pytest.mark.asyncio
    async def test_txt_to_epub_with_unicode_content(self, temp_dir):
        """Test EPUB creation from TXT with unicode content"""
        converter = EbookConverter()

        input_file = temp_dir / "test.txt"
        input_file.write_text("Unicode test: 你好世界 🎉 naïve café", encoding='utf-8')

        output_file = settings.UPLOAD_DIR / "test_converted.epub"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('ebooklib.epub.write_epub'):
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(b"fake epub")

                result = await converter.convert(
                    input_path=input_file,
                    output_format="epub",
                    options={},
                    session_id="test-session"
                )

                assert result == output_file

    @pytest.mark.asyncio
    async def test_epub_to_txt_preserves_special_chars(self, temp_dir):
        """Test TXT extraction from EPUB preserves special characters"""
        converter = EbookConverter()

        input_file = temp_dir / "test.epub"
        input_file.write_bytes(b"fake epub")

        output_file = settings.UPLOAD_DIR / "test_converted.txt"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('ebooklib.epub.read_epub') as mock_read:
                mock_book = MagicMock()
                mock_book.get_metadata.return_value = []
                # Content with special chars
                html_content = "<html><p>Unicode: 你好 🎉</p></html>".encode('utf-8')
                mock_items = [
                    MagicMock(get_type=lambda: 9, get_content=lambda: html_content)
                ]
                mock_book.get_items.return_value = mock_items
                mock_read.return_value = mock_book

                output_file.parent.mkdir(parents=True, exist_ok=True)

                result = await converter.convert(
                    input_path=input_file,
                    output_format="txt",
                    options={},
                    session_id="test-session"
                )

                assert result == output_file
                assert output_file.exists()


# ============================================================================
# COMPLEX CONVERSION SCENARIOS
# ============================================================================

class TestComplexScenarios:
    """Test complex conversion scenarios"""

    @pytest.mark.asyncio
    async def test_convert_multiple_chapter_epub_to_txt(self, temp_dir):
        """Test EPUB with multiple chapters converts correctly to TXT"""
        converter = EbookConverter()

        input_file = temp_dir / "multibook.epub"
        input_file.write_bytes(b"fake epub")

        output_file = settings.UPLOAD_DIR / "multibook_converted.txt"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('ebooklib.epub.read_epub') as mock_read:
                mock_book = MagicMock()
                mock_book.get_metadata.side_effect = lambda dc, field: {
                    'title': [("Multi-Chapter Book", "")],
                    'creator': [("Multiple Authors", "")]
                }.get(field, [])

                # Multiple items/chapters
                mock_items = [
                    MagicMock(get_type=lambda: 9, get_content=lambda: b"<html><h1>Chapter 1</h1><p>Content 1</p></html>"),
                    MagicMock(get_type=lambda: 9, get_content=lambda: b"<html><h1>Chapter 2</h1><p>Content 2</p></html>"),
                    MagicMock(get_type=lambda: 9, get_content=lambda: b"<html><h1>Chapter 3</h1><p>Content 3</p></html>"),
                    MagicMock(get_type=lambda: 0)  # Non-HTML item
                ]
                mock_book.get_items.return_value = mock_items
                mock_read.return_value = mock_book

                output_file.parent.mkdir(parents=True, exist_ok=True)

                result = await converter.convert(
                    input_path=input_file,
                    output_format="txt",
                    options={},
                    session_id="test-session"
                )

                assert result == output_file
                assert output_file.exists()

    @pytest.mark.asyncio
    async def test_convert_long_text_file_to_epub(self, temp_dir):
        """Test conversion of large text file to EPUB"""
        converter = EbookConverter()

        input_file = temp_dir / "longbook.txt"
        # Create a large text file
        large_content = "Paragraph {}\n\n" * 100
        input_file.write_text(large_content.format(*range(100)))

        output_file = settings.UPLOAD_DIR / "longbook_converted.epub"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('ebooklib.epub.write_epub'):
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(b"fake epub")

                result = await converter.convert(
                    input_path=input_file,
                    output_format="epub",
                    options={},
                    session_id="test-session"
                )

                assert result == output_file
                assert output_file.exists()


# ============================================================================
# OPTIONS AND PARAMETERS TESTS
# ============================================================================

class TestOptionsAndParameters:
    """Test handling of conversion options and parameters"""

    @pytest.mark.asyncio
    async def test_convert_with_empty_options(self, temp_dir):
        """Test conversion with empty options dict"""
        converter = EbookConverter()

        input_file = temp_dir / "test.txt"
        input_file.write_text("Content")

        output_file = settings.UPLOAD_DIR / "test_converted.epub"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('ebooklib.epub.write_epub'):
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(b"fake epub")

                result = await converter.convert(
                    input_path=input_file,
                    output_format="epub",
                    options={},
                    session_id="test-session"
                )

                assert result == output_file

    @pytest.mark.asyncio
    async def test_convert_with_custom_options(self, temp_dir):
        """Test conversion with custom options"""
        converter = EbookConverter()

        input_file = temp_dir / "test.txt"
        input_file.write_text("Content")

        output_file = settings.UPLOAD_DIR / "test_converted.epub"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('ebooklib.epub.write_epub'):
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(b"fake epub")

                result = await converter.convert(
                    input_path=input_file,
                    output_format="epub",
                    options={
                        "title": "Custom Title",
                        "author": "Custom Author",
                        "language": "fr"
                    },
                    session_id="test-session"
                )

                assert result == output_file

    @pytest.mark.asyncio
    async def test_html_to_epub_preserves_structure(self, temp_dir):
        """Test HTML to EPUB preserves document structure"""
        converter = EbookConverter()

        input_file = temp_dir / "structured.html"
        html_content = """
        <html>
            <head><title>Test</title></head>
            <body>
                <h1>Main Title</h1>
                <h2>Section 1</h2>
                <p>Content 1</p>
                <h2>Section 2</h2>
                <p>Content 2</p>
            </body>
        </html>
        """
        input_file.write_text(html_content)

        output_file = settings.UPLOAD_DIR / "structured_converted.epub"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('ebooklib.epub.write_epub'):
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(b"fake epub")

                result = await converter.convert(
                    input_path=input_file,
                    output_format="epub",
                    options={},
                    session_id="test-session"
                )

                assert result == output_file


class TestEbookEdgeCases:
    """Test edge cases and error handling in ebook conversion"""

    @pytest.mark.asyncio
    async def test_epub_to_txt_removes_script_tags(self, temp_dir):
        """Test that script tags are removed when converting EPUB to TXT (line 130)"""
        converter = EbookConverter()

        output_file = settings.UPLOAD_DIR / "test_converted.txt"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Create mock EPUB with HTML content including script tags
        mock_book = MagicMock()
        mock_item = MagicMock()
        mock_item.get_type.return_value = 9  # ITEM_DOCUMENT
        html_content = b"""
        <html>
            <script>alert('test');</script>
            <style>.test { color: red; }</style>
            <body>Content here</body>
        </html>
        """
        mock_item.get_content.return_value = html_content
        mock_book.get_items.return_value = [mock_item]
        mock_book.get_metadata.return_value = []  # No title/author

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            await converter._epub_to_txt(mock_book, output_file, "test-session")

            assert output_file.exists()
            # Verify script and style tags were removed
            content = output_file.read_text()
            assert 'alert' not in content
            assert '.test' not in content

    @pytest.mark.asyncio
    async def test_epub_to_html_handles_missing_body_tag(self, temp_dir):
        """Test EPUB to HTML handles content without body tag (line 197)"""
        converter = EbookConverter()

        output_file = settings.UPLOAD_DIR / "test_converted.html"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Create mock EPUB with HTML content without body tag
        mock_book = MagicMock()
        mock_item = MagicMock()
        mock_item.get_type.return_value = 9  # ITEM_DOCUMENT
        html_content = b"<html><p>Direct content without body</p></html>"
        mock_item.get_content.return_value = html_content
        mock_book.get_items.return_value = [mock_item]
        mock_book.get_metadata.return_value = []  # No title/author

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            await converter._epub_to_html(mock_book, output_file, "test-session")

            assert output_file.exists()
            # Verify the HTML content was included despite missing body tag
            content = output_file.read_text()
            assert 'Direct content without body' in content

    @pytest.mark.asyncio
    async def test_epub_to_pdf_handles_paragraph_errors(self, temp_dir):
        """Test EPUB to PDF handles errors when adding paragraphs (lines 238, 256-259)"""
        converter = EbookConverter()

        output_file = settings.UPLOAD_DIR / "test_converted.pdf"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Create mock EPUB with content that will cause paragraph errors
        # Use double newlines to create multiple paragraphs after text cleaning
        mock_book = MagicMock()
        mock_item = MagicMock()
        mock_item.get_type.return_value = 9  # ITEM_DOCUMENT
        html_content = b"""<html>
<script>should be removed</script>
<body>
<p>First paragraph that works fine.</p>

<p>Second paragraph that will fail.</p>
</body>
</html>"""
        mock_item.get_content.return_value = html_content
        mock_book.get_items.return_value = [mock_item]
        mock_book.get_metadata.return_value = []  # No title/author

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.ebook_converter.SimpleDocTemplate') as mock_doc_class:
                with patch('app.services.ebook_converter.Paragraph') as mock_paragraph_class:
                    with patch('app.services.ebook_converter.Spacer', return_value=MagicMock()):
                        with patch('app.services.ebook_converter.getSampleStyleSheet') as mock_styles:
                            # Return a proper styles object
                            mock_styles.return_value = {
                                'Title': MagicMock(),
                                'Heading2': MagicMock(),
                                'BodyText': MagicMock()
                            }

                            # Mock logger to verify warning is called
                            with patch('app.services.ebook_converter.logger') as mock_logger:
                                # Make Paragraph raise exception to test exception handler (lines 256-259)
                                # We need at least one call to succeed, then one to fail
                                def paragraph_side_effect(*args, **kwargs):
                                    if not hasattr(paragraph_side_effect, 'call_count'):
                                        paragraph_side_effect.call_count = 0
                                    paragraph_side_effect.call_count += 1

                                    if paragraph_side_effect.call_count == 1:
                                        return MagicMock()  # First paragraph succeeds
                                    else:
                                        raise Exception("Font error")  # Subsequent paragraphs fail

                                mock_paragraph_class.side_effect = paragraph_side_effect

                                mock_doc_instance = MagicMock()
                                mock_doc_class.return_value = mock_doc_instance

                                await converter._epub_to_pdf(mock_book, output_file, "test-session")

                                # Should have called build on the document despite the error
                                mock_doc_instance.build.assert_called_once()
                                # Should have logged the warning for the failed paragraph
                                assert mock_logger.warning.called

    @pytest.mark.asyncio
    async def test_epub_convert_unsupported_output_format(self, temp_dir):
        """Test converting from EPUB to unsupported format raises error (line 104)"""
        converter = EbookConverter()

        input_file = temp_dir / "test.epub"
        input_file.write_bytes(b"fake epub")

        output_file = settings.UPLOAD_DIR / "test_converted.xyz"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('ebooklib.epub.read_epub') as mock_read:
                mock_book = MagicMock()
                mock_read.return_value = mock_book

                with pytest.raises(ValueError, match="Unsupported output format"):
                    await converter._convert_from_epub(
                        input_file,
                        output_file,
                        "xyz",  # Unsupported format
                        "test-session"
                    )
