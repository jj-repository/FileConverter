"""
Tests for app/services/document_converter.py

COVERAGE GOAL: 85%+
Tests document conversion with Pandoc, TOC generation, format-specific options,
and metadata extraction for PDF/DOCX
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import subprocess

from app.services.document_converter import DocumentConverter
from app.config import settings


# ============================================================================
# BASIC FUNCTIONALITY TESTS
# ============================================================================

class TestDocumentConverterBasics:
    """Test basic DocumentConverter functionality"""

    def test_initialization_pandoc_available(self):
        """Test DocumentConverter initializes when Pandoc is available"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)

            converter = DocumentConverter()

            assert converter.pandoc_available is True
            assert converter.supported_formats is not None
            assert "input" in converter.supported_formats
            assert "output" in converter.supported_formats
            assert "docx" in converter.supported_formats["input"]

    def test_initialization_pandoc_unavailable(self):
        """Test DocumentConverter handles missing Pandoc"""
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            converter = DocumentConverter()

            assert converter.pandoc_available is False

    def test_initialization_pandoc_timeout(self):
        """Test DocumentConverter handles Pandoc timeout"""
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("pandoc", 5)):
            converter = DocumentConverter()

            assert converter.pandoc_available is False

    @pytest.mark.asyncio
    async def test_get_supported_formats(self):
        """Test getting supported document formats"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)

            converter = DocumentConverter()
            formats = await converter.get_supported_formats()

            assert "input" in formats
            assert "output" in formats
            assert isinstance(formats["input"], list)
            assert isinstance(formats["output"], list)
            # Check common formats
            assert "pdf" in formats["output"]
            assert "docx" in formats["output"]
            assert "md" in formats["output"]
            assert "html" in formats["output"]


# ============================================================================
# PANDOC FORMAT MAPPING TESTS
# ============================================================================

class TestPandocFormatMapping:
    """Test Pandoc format identifier mapping"""

    def test_get_pandoc_format_txt(self):
        """Test TXT format mapping"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            converter = DocumentConverter()

            format_id = converter._get_pandoc_format("txt")

            assert format_id == "markdown"

    def test_get_pandoc_format_md(self):
        """Test Markdown format mapping"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            converter = DocumentConverter()

            format_id = converter._get_pandoc_format("md")

            assert format_id == "markdown"

    def test_get_pandoc_format_html(self):
        """Test HTML format mapping"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            converter = DocumentConverter()

            format_id = converter._get_pandoc_format("html")

            assert format_id == "html"

    def test_get_pandoc_format_docx(self):
        """Test DOCX format mapping"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            converter = DocumentConverter()

            format_id = converter._get_pandoc_format("docx")

            assert format_id == "docx"

    def test_get_pandoc_format_unknown(self):
        """Test unknown format returns itself"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            converter = DocumentConverter()

            format_id = converter._get_pandoc_format("xyz")

            assert format_id == "xyz"


# ============================================================================
# CONVERSION TESTS
# ============================================================================

class TestDocumentConversion:
    """Test document conversion functionality"""

    @pytest.mark.asyncio
    async def test_convert_md_to_html_success(self, temp_dir):
        """Test successful Markdown to HTML conversion"""
        with patch('subprocess.run') as mock_check:
            mock_check.return_value = Mock(returncode=0)
            converter = DocumentConverter()

            input_file = temp_dir / "test.md"
            input_file.write_text("# Test Document\n\nContent here.")

            output_file = settings.UPLOAD_DIR / "test_converted.html"

            with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
                with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                    # Mock Pandoc process
                    mock_process = AsyncMock()
                    mock_process.returncode = 0
                    mock_process.communicate = AsyncMock(return_value=(b"", b""))
                    mock_subprocess.return_value = mock_process

                    # Create fake output file
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("<h1>Test Document</h1><p>Content here.</p>")

                    result = await converter.convert(
                        input_path=input_file,
                        output_format="html",
                        options={},
                        session_id="test-session"
                    )

                    assert result == output_file
                    assert output_file.exists()

                    # Verify progress was sent
                    assert mock_progress.call_count >= 4

                    # Verify Pandoc command
                    mock_subprocess.assert_called_once()
                    call_args = mock_subprocess.call_args[0]
                    assert settings.PANDOC_PATH in call_args
                    assert str(input_file) in call_args
                    assert "-o" in call_args
                    assert "--standalone" in call_args  # HTML should have standalone flag

    @pytest.mark.asyncio
    async def test_convert_pandoc_not_available_raises_error(self, temp_dir):
        """Test conversion fails when Pandoc is not installed"""
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            converter = DocumentConverter()

            input_file = temp_dir / "test.md"
            input_file.write_text("# Test")

            with pytest.raises(Exception, match="Pandoc is not installed"):
                await converter.convert(
                    input_path=input_file,
                    output_format="html",
                    options={},
                    session_id="test-session"
                )

    @pytest.mark.asyncio
    async def test_convert_with_toc_enabled(self, temp_dir):
        """Test conversion with table of contents"""
        with patch('subprocess.run') as mock_check:
            mock_check.return_value = Mock(returncode=0)
            converter = DocumentConverter()

            input_file = temp_dir / "test.md"
            input_file.write_text("# Chapter 1\n\nContent")

            output_file = settings.UPLOAD_DIR / "test_converted.pdf"

            with patch.object(converter, 'send_progress', new=AsyncMock()):
                with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                    mock_process = AsyncMock()
                    mock_process.returncode = 0
                    mock_process.communicate = AsyncMock(return_value=(b"", b""))
                    mock_subprocess.return_value = mock_process

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("PDF content")

                    await converter.convert(
                        input_path=input_file,
                        output_format="pdf",
                        options={"toc": True},
                        session_id="test-session"
                    )

                    # Verify --toc flag in command
                    call_args = mock_subprocess.call_args[0]
                    assert "--toc" in call_args

    @pytest.mark.asyncio
    async def test_convert_pdf_includes_engine(self, temp_dir):
        """Test PDF conversion includes PDF engine"""
        with patch('subprocess.run') as mock_check:
            mock_check.return_value = Mock(returncode=0)
            converter = DocumentConverter()

            input_file = temp_dir / "test.md"
            input_file.write_text("# Test")

            output_file = settings.UPLOAD_DIR / "test_converted.pdf"

            with patch.object(converter, 'send_progress', new=AsyncMock()):
                with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                    mock_process = AsyncMock()
                    mock_process.returncode = 0
                    mock_process.communicate = AsyncMock(return_value=(b"", b""))
                    mock_subprocess.return_value = mock_process

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("PDF")

                    await converter.convert(
                        input_path=input_file,
                        output_format="pdf",
                        options={},
                        session_id="test-session"
                    )

                    # Verify --pdf-engine flag
                    call_args = mock_subprocess.call_args[0]
                    assert "--pdf-engine=pdflatex" in call_args

    @pytest.mark.asyncio
    async def test_convert_toc_only_for_supported_formats(self, temp_dir):
        """Test TOC is only added for PDF, HTML, DOCX"""
        with patch('subprocess.run') as mock_check:
            mock_check.return_value = Mock(returncode=0)
            converter = DocumentConverter()

            input_file = temp_dir / "test.md"
            input_file.write_text("# Test")

            output_file = settings.UPLOAD_DIR / "test_converted.txt"

            with patch.object(converter, 'send_progress', new=AsyncMock()):
                with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                    mock_process = AsyncMock()
                    mock_process.returncode = 0
                    mock_process.communicate = AsyncMock(return_value=(b"", b""))
                    mock_subprocess.return_value = mock_process

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("text")

                    await converter.convert(
                        input_path=input_file,
                        output_format="txt",
                        options={"toc": True},  # Should be ignored for TXT
                        session_id="test-session"
                    )

                    # Verify --toc is NOT in command for TXT
                    call_args = mock_subprocess.call_args[0]
                    assert "--toc" not in call_args

    @pytest.mark.asyncio
    async def test_convert_unsupported_format_raises_error(self, temp_dir):
        """Test conversion with unsupported format raises ValueError"""
        with patch('subprocess.run') as mock_check:
            mock_check.return_value = Mock(returncode=0)
            converter = DocumentConverter()

            input_file = temp_dir / "test.exe"
            input_file.write_text("not a document")

            with pytest.raises(ValueError, match="Unsupported conversion"):
                await converter.convert(
                    input_path=input_file,
                    output_format="pdf",
                    options={},
                    session_id="test-session"
                )

    @pytest.mark.asyncio
    async def test_convert_pandoc_error_raises_exception(self, temp_dir):
        """Test conversion handles Pandoc errors"""
        with patch('subprocess.run') as mock_check:
            mock_check.return_value = Mock(returncode=0)
            converter = DocumentConverter()

            input_file = temp_dir / "test.md"
            input_file.write_text("# Test")

            with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
                with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                    # Mock failed Pandoc process
                    mock_process = AsyncMock()
                    mock_process.returncode = 1
                    mock_process.communicate = AsyncMock(return_value=(b"", b"Pandoc error: invalid input"))
                    mock_subprocess.return_value = mock_process

                    with pytest.raises(Exception, match="Pandoc conversion failed"):
                        await converter.convert(
                            input_path=input_file,
                            output_format="html",
                            options={},
                            session_id="test-session"
                        )

                    # Verify failure progress was sent
                    last_call = mock_progress.call_args_list[-1]
                    assert "failed" in str(last_call)

    @pytest.mark.asyncio
    async def test_convert_output_file_missing_raises_exception(self, temp_dir):
        """Test conversion raises exception when output file not created"""
        with patch('subprocess.run') as mock_check:
            mock_check.return_value = Mock(returncode=0)
            converter = DocumentConverter()

            input_file = temp_dir / "test.md"
            input_file.write_text("# Test")

            with patch.object(converter, 'send_progress', new=AsyncMock()):
                with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                    mock_process = AsyncMock()
                    mock_process.returncode = 0
                    mock_process.communicate = AsyncMock(return_value=(b"", b""))
                    mock_subprocess.return_value = mock_process

                    # Don't create output file

                    with pytest.raises(Exception, match="Output file was not created"):
                        await converter.convert(
                            input_path=input_file,
                            output_format="html",
                            options={},
                            session_id="test-session"
                        )


# ============================================================================
# METADATA EXTRACTION TESTS
# ============================================================================

class TestDocumentMetadata:
    """Test document metadata extraction"""

    @pytest.mark.asyncio
    async def test_get_metadata_basic(self, temp_dir):
        """Test basic metadata extraction"""
        with patch('subprocess.run') as mock_check:
            mock_check.return_value = Mock(returncode=0)
            converter = DocumentConverter()

            test_file = temp_dir / "test.md"
            test_file.write_text("# Test Document\n\nSome content here.")

            with patch('subprocess.run') as mock_pandoc:
                # Mock Pandoc word count extraction
                mock_pandoc.return_value = Mock(
                    returncode=0,
                    stdout="Test Document Some content here"
                )

                metadata = await converter.get_document_metadata(test_file)

                assert "size" in metadata
                assert "format" in metadata
                assert metadata["format"] == "md"
                assert "word_count" in metadata
                assert "character_count" in metadata
                assert "line_count" in metadata

    @pytest.mark.asyncio
    async def test_get_metadata_docx(self, temp_dir):
        """Test DOCX metadata extraction"""
        with patch('subprocess.run') as mock_check:
            mock_check.return_value = Mock(returncode=0)
            converter = DocumentConverter()

            test_file = temp_dir / "test.docx"
            test_file.write_bytes(b"fake docx")

            with patch('subprocess.run'):  # Mock Pandoc
                with patch('docx.Document') as mock_doc_class:
                    # Mock DOCX document
                    mock_doc = Mock()
                    mock_doc.paragraphs = ["p1", "p2", "p3"]
                    mock_doc.sections = ["s1"]
                    mock_doc_class.return_value = mock_doc

                    metadata = await converter.get_document_metadata(test_file)

                    assert metadata["format"] == "docx"
                    assert metadata["paragraph_count"] == 3
                    assert metadata["section_count"] == 1

    @pytest.mark.asyncio
    async def test_get_metadata_pdf(self, temp_dir):
        """Test PDF metadata extraction"""
        with patch('subprocess.run') as mock_check:
            mock_check.return_value = Mock(returncode=0)
            converter = DocumentConverter()

            test_file = temp_dir / "test.pdf"
            test_file.write_bytes(b"%PDF-1.4 fake pdf")

            with patch('subprocess.run'):  # Mock Pandoc
                with patch('PyPDF2.PdfReader') as mock_pdf_class:
                    # Mock PDF reader
                    mock_pdf = Mock()
                    mock_pdf.pages = [Mock(), Mock(), Mock()]  # 3 pages
                    mock_pdf.metadata = Mock()
                    mock_pdf.metadata.title = "Test Document"
                    mock_pdf.metadata.author = "Test Author"
                    mock_pdf_class.return_value = mock_pdf

                    metadata = await converter.get_document_metadata(test_file)

                    assert metadata["format"] == "pdf"
                    assert metadata["page_count"] == 3
                    assert metadata["title"] == "Test Document"
                    assert metadata["author"] == "Test Author"

    @pytest.mark.asyncio
    async def test_get_metadata_pandoc_unavailable(self, temp_dir):
        """Test metadata extraction when Pandoc is unavailable"""
        with patch('subprocess.run', side_effect=FileNotFoundError()):
            converter = DocumentConverter()

            test_file = temp_dir / "test.md"
            test_file.write_text("# Test")

            metadata = await converter.get_document_metadata(test_file)

            # Should still return basic metadata
            assert "size" in metadata
            assert "format" in metadata
            # But not word count (requires Pandoc)
            assert "word_count" not in metadata

    @pytest.mark.asyncio
    async def test_get_metadata_docx_error_handled(self, temp_dir):
        """Test DOCX metadata extraction handles errors gracefully"""
        with patch('subprocess.run') as mock_check:
            mock_check.return_value = Mock(returncode=0)
            converter = DocumentConverter()

            test_file = temp_dir / "test.docx"
            test_file.write_bytes(b"corrupted docx")

            with patch('subprocess.run'):
                with patch('docx.Document', side_effect=Exception("Corrupted file")):
                    metadata = await converter.get_document_metadata(test_file)

                    # Should not crash, just skip DOCX-specific metadata
                    assert "format" in metadata
                    assert "paragraph_count" not in metadata

    @pytest.mark.asyncio
    async def test_get_metadata_exception_handling(self, temp_dir):
        """Test metadata extraction handles general exceptions"""
        with patch('subprocess.run') as mock_check:
            mock_check.return_value = Mock(returncode=0)
            converter = DocumentConverter()

            # Non-existent file
            test_file = temp_dir / "nonexistent.md"

            metadata = await converter.get_document_metadata(test_file)

            assert "error" in metadata
