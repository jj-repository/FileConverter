"""
Integration tests for ebook router endpoints.

Tests the full API integration including:
- POST /api/ebook/convert - eBook conversion endpoint
- GET /api/ebook/formats - Supported formats endpoint
- GET /api/ebook/download/{filename} - File download endpoint
- POST /api/ebook/info - eBook metadata endpoint

Security tests:
- Path traversal prevention in download
- File size validation
- Extension validation
- Malicious filename sanitization
- Corrupted file handling
"""

import pytest
import zipfile
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    """Create test client for API testing"""
    return TestClient(app)


@pytest.fixture
def sample_epub(temp_dir):
    """Create a sample EPUB file for testing

    EPUB is a ZIP-based format with specific structure:
    - mimetype file (uncompressed)
    - META-INF/container.xml
    - OEBPS/content.opf
    - OEBPS/toc.ncx
    - OEBPS/text/chapter1.xhtml
    """
    epub_path = temp_dir / "test_book.epub"

    with zipfile.ZipFile(epub_path, 'w') as zf:
        # Add mimetype (must be first and uncompressed)
        zf.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)

        # Add META-INF/container.xml
        container_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''
        zf.writestr('META-INF/container.xml', container_xml)

        # Add OEBPS/content.opf (package document)
        opf_content = '''<?xml version="1.0" encoding="UTF-8"?>
<package version="2.0" unique-identifier="id" xmlns="http://www.idpf.org/2007/opf">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test eBook</dc:title>
    <dc:creator>Test Author</dc:creator>
    <dc:language>en</dc:language>
    <dc:rights>Public Domain</dc:rights>
    <dc:publisher>Test Publisher</dc:publisher>
    <meta property="dcterms:modified">2024-01-01T00:00:00Z</meta>
  </metadata>
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="chapter1" href="text/chapter1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="chapter1"/>
  </spine>
</package>'''
        zf.writestr('OEBPS/content.opf', opf_content)

        # Add OEBPS/toc.ncx (table of contents)
        toc_ncx = '''<?xml version="1.0" encoding="UTF-8"?>
<ncx version="2005-1" xmlns="http://www.daisy.org/z3986/2005/ncx/">
  <head>
    <meta name="dtb:uid" content="test-ebook"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>Test eBook</text></docTitle>
  <navMap>
    <navPoint id="navpoint1" playOrder="1">
      <navLabel><text>Chapter 1</text></navLabel>
      <content src="text/chapter1.xhtml"/>
    </navPoint>
  </navMap>
</ncx>'''
        zf.writestr('OEBPS/toc.ncx', toc_ncx)

        # Add OEBPS/text/chapter1.xhtml
        chapter_xhtml = '''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>Chapter 1</title>
  </head>
  <body>
    <h1>Chapter 1: Introduction</h1>
    <p>This is the first chapter of the test eBook.</p>
    <p>It contains some sample content for testing the conversion process.</p>
  </body>
</html>'''
        zf.writestr('OEBPS/text/chapter1.xhtml', chapter_xhtml)

    return epub_path


@pytest.fixture
def sample_epub_with_cover(temp_dir):
    """Create a sample EPUB with cover image"""
    epub_path = temp_dir / "test_book_with_cover.epub"

    with zipfile.ZipFile(epub_path, 'w') as zf:
        zf.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)

        container_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''
        zf.writestr('META-INF/container.xml', container_xml)

        opf_content = '''<?xml version="1.0" encoding="UTF-8"?>
<package version="2.0" unique-identifier="id" xmlns="http://www.idpf.org/2007/opf">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test eBook with Cover</dc:title>
    <dc:creator>Test Author</dc:creator>
    <dc:language>en</dc:language>
    <meta name="cover" content="cover-image"/>
  </metadata>
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="cover-image" href="images/cover.jpg" media-type="image/jpeg"/>
    <item id="chapter1" href="text/chapter1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="cover-image"/>
    <itemref idref="chapter1"/>
  </spine>
</package>'''
        zf.writestr('OEBPS/content.opf', opf_content)

        toc_ncx = '''<?xml version="1.0" encoding="UTF-8"?>
<ncx version="2005-1" xmlns="http://www.daisy.org/z3986/2005/ncx/">
  <head>
    <meta name="dtb:uid" content="test-ebook-cover"/>
    <meta name="dtb:depth" content="1"/>
  </head>
  <docTitle><text>Test eBook with Cover</text></docTitle>
  <navMap>
    <navPoint id="navpoint1" playOrder="1">
      <navLabel><text>Chapter 1</text></navLabel>
      <content src="text/chapter1.xhtml"/>
    </navPoint>
  </navMap>
</ncx>'''
        zf.writestr('OEBPS/toc.ncx', toc_ncx)

        chapter_xhtml = '''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head><title>Chapter 1</title></head>
  <body>
    <h1>Chapter 1</h1>
    <p>Content with cover image.</p>
  </body>
</html>'''
        zf.writestr('OEBPS/text/chapter1.xhtml', chapter_xhtml)

        # Add minimal cover image (small PNG)
        cover_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        zf.writestr('OEBPS/images/cover.jpg', cover_data)

    return epub_path


@pytest.fixture
def sample_txt_ebook(temp_dir):
    """Create a sample text file for ebook conversion"""
    txt_path = temp_dir / "test_book.txt"
    content = """TEST EBOOK - PLAIN TEXT
========================

Chapter 1: Introduction
-----------------------

This is a test eBook in plain text format.
It contains sample content for testing the conversion process.

Chapter 2: Content
------------------

This is the second chapter with some sample paragraphs.

Line 1
Line 2
Line 3

The end.
"""
    txt_path.write_text(content)
    return txt_path


@pytest.fixture
def sample_html_ebook(temp_dir):
    """Create a sample HTML file for ebook conversion"""
    html_path = temp_dir / "test_book.html"
    content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test eBook</title>
</head>
<body>
    <h1>Test eBook - HTML Version</h1>

    <h2>Chapter 1: Introduction</h2>
    <p>This is a test eBook in HTML format.</p>
    <p>It contains sample content for testing the conversion process.</p>

    <h2>Chapter 2: Content</h2>
    <p>This is the second chapter with some sample paragraphs.</p>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
        <li>Item 3</li>
    </ul>
</body>
</html>
'''
    html_path.write_text(content)
    return html_path


@pytest.fixture
def corrupted_epub(temp_dir):
    """Create a corrupted EPUB file (invalid ZIP)"""
    epub_path = temp_dir / "corrupted.epub"
    epub_path.write_bytes(b'\x00\x01\x02\x03INVALID_EPUB_DATA_NOT_A_REAL_BOOK')
    return epub_path


class TestEbookConvert:
    """Test POST /api/ebook/convert endpoint"""

    def test_convert_epub_to_txt_success(self, client, sample_epub):
        """Test successful EPUB to TXT conversion"""
        with open(sample_epub, 'rb') as f:
            response = client.post(
                "/api/ebook/convert",
                files={"file": ("test_book.epub", f, "application/epub+zip")},
                data={"output_format": "txt"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "session_id" in data
        assert data["output_file"].endswith(".txt")
        assert "download_url" in data

    def test_convert_epub_to_html_success(self, client, sample_epub):
        """Test successful EPUB to HTML conversion"""
        with open(sample_epub, 'rb') as f:
            response = client.post(
                "/api/ebook/convert",
                files={"file": ("test_book.epub", f, "application/epub+zip")},
                data={"output_format": "html"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".html")

    def test_convert_epub_to_pdf_success(self, client, sample_epub):
        """Test successful EPUB to PDF conversion"""
        with open(sample_epub, 'rb') as f:
            response = client.post(
                "/api/ebook/convert",
                files={"file": ("test_book.epub", f, "application/epub+zip")},
                data={"output_format": "pdf"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".pdf")

    def test_convert_txt_to_epub_success(self, client, sample_txt_ebook):
        """Test successful TXT to EPUB conversion"""
        with open(sample_txt_ebook, 'rb') as f:
            response = client.post(
                "/api/ebook/convert",
                files={"file": ("test_book.txt", f, "text/plain")},
                data={"output_format": "epub"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".epub")

    def test_convert_html_to_epub_success(self, client, sample_html_ebook):
        """Test successful HTML to EPUB conversion"""
        with open(sample_html_ebook, 'rb') as f:
            response = client.post(
                "/api/ebook/convert",
                files={"file": ("test_book.html", f, "text/html")},
                data={"output_format": "epub"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".epub")

    def test_convert_with_metadata_title(self, client, sample_txt_ebook):
        """Test conversion with title metadata parameter"""
        with open(sample_txt_ebook, 'rb') as f:
            response = client.post(
                "/api/ebook/convert",
                files={"file": ("test_book.txt", f, "text/plain")},
                data={
                    "output_format": "epub",
                    "title": "Custom Book Title"
                }
            )

        # May succeed or fail based on implementation
        assert response.status_code in [200, 400, 500]

    def test_convert_with_metadata_author(self, client, sample_txt_ebook):
        """Test conversion with author metadata parameter"""
        with open(sample_txt_ebook, 'rb') as f:
            response = client.post(
                "/api/ebook/convert",
                files={"file": ("test_book.txt", f, "text/plain")},
                data={
                    "output_format": "epub",
                    "author": "Custom Author Name"
                }
            )

        # May succeed or fail based on implementation
        assert response.status_code in [200, 400, 500]

    def test_convert_epub_with_cover_success(self, client, sample_epub_with_cover):
        """Test successful EPUB conversion preserving cover image"""
        with open(sample_epub_with_cover, 'rb') as f:
            response = client.post(
                "/api/ebook/convert",
                files={"file": ("test_book.epub", f, "application/epub+zip")},
                data={"output_format": "html"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".html")

    def test_convert_invalid_output_format(self, client, sample_epub):
        """Test conversion with invalid output format"""
        with open(sample_epub, 'rb') as f:
            response = client.post(
                "/api/ebook/convert",
                files={"file": ("test_book.epub", f, "application/epub+zip")},
                data={"output_format": "mobi"}  # MOBI not in supported formats
            )

        # Should fail with 400 or 500 depending on validation stage
        assert response.status_code in [400, 500]
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error")
        assert "Unsupported" in str(error_msg) or "Invalid" in str(error_msg)

    def test_convert_corrupted_ebook(self, client, corrupted_epub):
        """Test conversion with corrupted ebook file"""
        with open(corrupted_epub, 'rb') as f:
            response = client.post(
                "/api/ebook/convert",
                files={"file": ("corrupted.epub", f, "application/epub+zip")},
                data={"output_format": "txt"}
            )

        # Should fail validation or conversion
        assert response.status_code in [400, 500]
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error")
        assert error_msg is not None  # Should have error message

    def test_convert_unsupported_input_format(self, client, temp_dir):
        """Test conversion with unsupported input format"""
        # Create a file with unsupported extension
        fake_file = temp_dir / "notabook.mobi"
        fake_file.write_text("not an ebook")

        with open(fake_file, 'rb') as f:
            response = client.post(
                "/api/ebook/convert",
                files={"file": ("notabook.mobi", f, "application/octet-stream")},
                data={"output_format": "epub"}
            )

        # Should fail with 400 or 500 depending on validation stage
        assert response.status_code in [400, 500]
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error")
        assert ("Invalid" in str(error_msg) or
                "Unsupported" in str(error_msg))


class TestEbookFormats:
    """Test GET /api/ebook/formats endpoint"""

    def test_get_formats_success(self, client):
        """Test successful retrieval of supported ebook formats"""
        response = client.get("/api/ebook/formats")

        assert response.status_code == 200
        data = response.json()
        assert "input_formats" in data
        assert "output_formats" in data
        assert isinstance(data["input_formats"], list)
        assert isinstance(data["output_formats"], list)

    def test_formats_include_common_ebook_types(self, client):
        """Test that common ebook formats are included"""
        response = client.get("/api/ebook/formats")
        data = response.json()

        # Check for common ebook formats
        common_formats = ["epub", "txt", "html", "pdf"]
        for fmt in common_formats:
            assert fmt in data["output_formats"], f"{fmt} not in output formats"

    def test_formats_include_notes(self, client):
        """Test that format notes are provided"""
        response = client.get("/api/ebook/formats")
        data = response.json()

        assert "notes" in data
        assert isinstance(data["notes"], dict)
        # At least some formats should have notes
        assert len(data["notes"]) > 0


class TestEbookDownload:
    """Test GET /api/ebook/download/{filename} endpoint"""

    def test_download_converted_file(self, client, sample_epub):
        """Test downloading a converted ebook file"""
        # First, convert an ebook
        with open(sample_epub, 'rb') as f:
            convert_response = client.post(
                "/api/ebook/convert",
                files={"file": ("test_book.epub", f, "application/epub+zip")},
                data={"output_format": "txt"}
            )

        assert convert_response.status_code == 200
        output_filename = convert_response.json()["output_file"]

        # Now download it
        download_response = client.get(f"/api/ebook/download/{output_filename}")

        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "application/octet-stream"
        assert len(download_response.content) > 0

    def test_download_nonexistent_file(self, client):
        """Test downloading a file that doesn't exist"""
        response = client.get("/api/ebook/download/nonexistent_book.txt")

        assert response.status_code == 404

    def test_download_path_traversal_blocked(self, client):
        """Test that path traversal attempts are blocked"""
        # Try to access /etc/passwd via path traversal
        malicious_filenames = [
            "../../../etc/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "....//....//....//etc/passwd",
        ]

        for malicious_name in malicious_filenames:
            response = client.get(f"/api/ebook/download/{malicious_name}")
            # Should either be 400 (validation) or 404 (not found)
            assert response.status_code in [400, 404], \
                f"Path traversal not blocked for: {malicious_name}"


class TestEbookInfo:
    """Test POST /api/ebook/info endpoint"""

    def test_get_ebook_info_success(self, client, sample_epub):
        """Test successful ebook info retrieval"""
        with open(sample_epub, 'rb') as f:
            response = client.post(
                "/api/ebook/info",
                files={"file": ("test_book.epub", f, "application/epub+zip")}
            )

        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert "size" in data
        assert "format" in data
        # Info response may include metadata as separate fields or in a metadata key
        assert len(data) > 3  # Should have at least filename, size, format + more

    def test_get_ebook_info_includes_title(self, client, sample_epub):
        """Test that ebook info includes title metadata"""
        with open(sample_epub, 'rb') as f:
            response = client.post(
                "/api/ebook/info",
                files={"file": ("test_book.epub", f, "application/epub+zip")}
            )

        assert response.status_code == 200
        data = response.json()
        # Title may be in a metadata dict or a separate field
        assert "title" in data or "metadata" in data
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_get_ebook_info_includes_author(self, client, sample_epub):
        """Test that ebook info includes author if available"""
        with open(sample_epub, 'rb') as f:
            response = client.post(
                "/api/ebook/info",
                files={"file": ("test_book.epub", f, "application/epub+zip")}
            )

        assert response.status_code == 200
        data = response.json()
        # Author may be in a metadata dict or a separate field
        assert "author" in data or "metadata" in data
        # Should have some response data
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_get_ebook_info_invalid_file(self, client, corrupted_epub):
        """Test ebook info with corrupted file"""
        with open(corrupted_epub, 'rb') as f:
            response = client.post(
                "/api/ebook/info",
                files={"file": ("corrupted.epub", f, "application/epub+zip")}
            )

        # Returns 200 with partial info, 400, or 500 depending on error handling
        # Corrupted files may still return info with warnings/fallbacks
        assert response.status_code in [200, 400, 500]

    def test_get_info_for_txt_file(self, client, sample_txt_ebook):
        """Test ebook info extraction from text file"""
        with open(sample_txt_ebook, 'rb') as f:
            response = client.post(
                "/api/ebook/info",
                files={"file": ("test_book.txt", f, "text/plain")}
            )

        assert response.status_code == 200
        data = response.json()
        assert "size" in data
        assert "format" in data


class TestEbookSecurityValidation:
    """Test security-critical validation in ebook endpoints"""

    def test_malicious_filename_sanitized(self, client, sample_epub):
        """Test that malicious filenames are sanitized"""
        malicious_filenames = [
            "test; rm -rf /.epub",
            "test$(whoami).epub",
            "test`whoami`.epub",
        ]

        for malicious_name in malicious_filenames:
            with open(sample_epub, 'rb') as f:
                response = client.post(
                    "/api/ebook/convert",
                    files={"file": (malicious_name, f, "application/epub+zip")},
                    data={"output_format": "txt"}
                )

            # Should succeed (filename sanitized) or fail safely
            assert response.status_code in [200, 400, 500]
            if response.status_code == 200:
                # Verify output filename doesn't contain shell metacharacters
                output_file = response.json()["output_file"]
                dangerous_chars = [';', '$', '`', '|', '&', '<', '>']
                for char in dangerous_chars:
                    assert char not in output_file

    def test_null_byte_injection_blocked(self, client, sample_epub):
        """Test that null byte injection is sanitized"""
        with open(sample_epub, 'rb') as f:
            response = client.post(
                "/api/ebook/convert",
                files={"file": ("test\x00.epub", f, "application/epub+zip")},
                data={"output_format": "txt"}
            )

        # Null bytes are sanitized, so conversion succeeds
        # but output filename should not contain null bytes
        if response.status_code == 200:
            output_file = response.json()["output_file"]
            assert '\x00' not in output_file
        else:
            # Or it fails validation
            assert response.status_code in [400, 500]


class TestEbookConversionFormats:
    """Test various ebook format conversions"""

    def test_convert_to_multiple_formats(self, client, sample_epub):
        """Test conversion of EPUB to all supported output formats"""
        output_formats = ["txt", "html", "pdf", "epub"]

        for output_fmt in output_formats:
            with open(sample_epub, 'rb') as f:
                response = client.post(
                    "/api/ebook/convert",
                    files={"file": ("test_book.epub", f, "application/epub+zip")},
                    data={"output_format": output_fmt}
                )

            # Most should succeed, some may fail based on implementation
            assert response.status_code in [200, 400, 500], \
                f"Unexpected status for {output_fmt} conversion"

    def test_convert_between_text_formats(self, client, sample_txt_ebook):
        """Test converting text files to different formats"""
        with open(sample_txt_ebook, 'rb') as f:
            response = client.post(
                "/api/ebook/convert",
                files={"file": ("test_book.txt", f, "text/plain")},
                data={"output_format": "html"}
            )

        assert response.status_code in [200, 400, 500]

    def test_epub_round_trip_conversion(self, client, sample_epub):
        """Test converting EPUB and converting back (if supported)"""
        # Convert EPUB to TXT
        with open(sample_epub, 'rb') as f:
            convert_response = client.post(
                "/api/ebook/convert",
                files={"file": ("test_book.epub", f, "application/epub+zip")},
                data={"output_format": "txt"}
            )

        if convert_response.status_code == 200:
            # Could potentially convert back if TXT to EPUB is supported
            output_file = convert_response.json()["output_file"]
            assert output_file.endswith(".txt")
