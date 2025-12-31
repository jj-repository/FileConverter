"""
Integration tests for document router endpoints.

Tests the full API integration including:
- POST /api/document/convert - Document conversion endpoint
- GET /api/document/formats - Supported formats endpoint
- GET /api/document/download/{filename} - File download endpoint
- POST /api/document/info - Document metadata endpoint

Security tests:
- Path traversal prevention in download
- File size validation
- Extension validation
- Malicious filename sanitization
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    """Create test client for API testing"""
    return TestClient(app)


@pytest.fixture
def sample_docx(temp_dir):
    """Create a sample DOCX document for testing"""
    # Create a minimal DOCX file (ZIP-based format)
    import zipfile
    from io import BytesIO

    docx_path = temp_dir / "test_document.docx"

    # Create minimal DOCX structure
    with zipfile.ZipFile(docx_path, 'w') as zf:
        # Add [Content_Types].xml
        zf.writestr('[Content_Types].xml',
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '</Types>')

        # Add _rels/.rels
        zf.writestr('_rels/.rels',
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '</Relationships>')

        # Add word/document.xml
        zf.writestr('word/document.xml',
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:body>'
            '<w:p><w:r><w:t>Test DOCX Document</w:t></w:r></w:p>'
            '<w:p><w:r><w:t>This is sample content for testing document conversion.</w:t></w:r></w:p>'
            '</w:body>'
            '</w:document>')

    return docx_path


@pytest.fixture
def sample_markdown(temp_dir):
    """Create a sample Markdown document for testing"""
    md_path = temp_dir / "test_document.md"
    md_content = """# Test Document

This is a **markdown** document for testing.

## Section 1

Some content with _emphasis_.

- Item 1
- Item 2
- Item 3

### Subsection

More content here.

## Section 2

Final section.
"""
    md_path.write_text(md_content)
    return md_path


@pytest.fixture
def sample_txt(temp_dir):
    """Create a sample text document for testing"""
    txt_path = temp_dir / "test_document.txt"
    txt_content = """Test Text Document

This is a sample text document for testing document conversion.

It contains multiple lines and paragraphs.

Paragraph 2: Testing the conversion functionality.
Paragraph 3: Document router endpoints.
"""
    txt_path.write_text(txt_content)
    return txt_path


class TestDocumentConvert:
    """Test POST /api/document/convert endpoint"""

    def test_convert_docx_to_pdf_success(self, client, sample_docx):
        """Test successful DOCX to PDF conversion"""
        with open(sample_docx, 'rb') as f:
            response = client.post(
                "/api/document/convert",
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"output_format": "pdf"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "session_id" in data
        assert data["output_file"].endswith(".pdf")
        assert "download_url" in data

    def test_convert_md_to_html_success(self, client, sample_markdown):
        """Test successful Markdown to HTML conversion"""
        with open(sample_markdown, 'rb') as f:
            response = client.post(
                "/api/document/convert",
                files={"file": ("test.md", f, "text/markdown")},
                data={"output_format": "html"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".html")
        assert "download_url" in data

    def test_convert_with_toc_true(self, client, sample_docx):
        """Test document conversion with table of contents enabled"""
        with open(sample_docx, 'rb') as f:
            response = client.post(
                "/api/document/convert",
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"output_format": "pdf", "toc": "true"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".pdf")

    def test_convert_with_toc_false(self, client, sample_docx):
        """Test document conversion with table of contents disabled"""
        with open(sample_docx, 'rb') as f:
            response = client.post(
                "/api/document/convert",
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"output_format": "pdf", "toc": "false"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_convert_with_preserve_formatting_true(self, client, sample_markdown):
        """Test conversion with preserve formatting enabled"""
        with open(sample_markdown, 'rb') as f:
            response = client.post(
                "/api/document/convert",
                files={"file": ("test.md", f, "text/markdown")},
                data={"output_format": "docx", "preserve_formatting": "true"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_convert_with_preserve_formatting_false(self, client, sample_markdown):
        """Test conversion with preserve formatting disabled"""
        with open(sample_markdown, 'rb') as f:
            response = client.post(
                "/api/document/convert",
                files={"file": ("test.md", f, "text/markdown")},
                data={"output_format": "txt", "preserve_formatting": "false"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_convert_invalid_output_format(self, client, sample_docx):
        """Test conversion with invalid output format"""
        with open(sample_docx, 'rb') as f:
            response = client.post(
                "/api/document/convert",
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"output_format": "invalid_format"}
            )

        assert response.status_code == 400
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error")
        assert "Unsupported output format" in str(error_msg) or "unsupported" in str(error_msg).lower()

    def test_convert_unsupported_input_format(self, client, temp_dir):
        """Test conversion with unsupported input format"""
        # Create a fake document file with unsupported extension
        fake_file = temp_dir / "malware.exe"
        fake_file.write_text("not a document")

        with open(fake_file, 'rb') as f:
            response = client.post(
                "/api/document/convert",
                files={"file": ("malware.exe", f, "application/octet-stream")},
                data={"output_format": "pdf"}
            )

        assert response.status_code == 400
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error")
        assert ("Invalid or unsupported file extension" in str(error_msg) or
                "Unsupported file format" in str(error_msg))

    def test_convert_txt_to_html(self, client, sample_txt):
        """Test TXT to HTML conversion"""
        with open(sample_txt, 'rb') as f:
            response = client.post(
                "/api/document/convert",
                files={"file": ("test.txt", f, "text/plain")},
                data={"output_format": "html"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["output_file"].endswith(".html")

    def test_convert_txt_to_docx(self, client, sample_txt):
        """Test TXT to DOCX conversion"""
        with open(sample_txt, 'rb') as f:
            response = client.post(
                "/api/document/convert",
                files={"file": ("test.txt", f, "text/plain")},
                data={"output_format": "docx"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["output_file"].endswith(".docx")

    def test_convert_txt_to_rtf(self, client, sample_txt):
        """Test TXT to RTF conversion"""
        with open(sample_txt, 'rb') as f:
            response = client.post(
                "/api/document/convert",
                files={"file": ("test.txt", f, "text/plain")},
                data={"output_format": "rtf"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["output_file"].endswith(".rtf")


class TestDocumentFormats:
    """Test GET /api/document/formats endpoint"""

    def test_get_formats_success(self, client):
        """Test successful retrieval of supported document formats"""
        response = client.get("/api/document/formats")

        assert response.status_code == 200
        data = response.json()
        assert "input_formats" in data
        assert "output_formats" in data
        assert isinstance(data["input_formats"], list)
        assert isinstance(data["output_formats"], list)

    def test_formats_include_common_types(self, client):
        """Test that common document formats are included"""
        response = client.get("/api/document/formats")
        data = response.json()

        # Check for common formats
        common_output_formats = ["pdf", "txt", "docx", "html", "md"]
        for fmt in common_output_formats:
            assert fmt in data["output_formats"], f"{fmt} not in output formats"


class TestDocumentDownload:
    """Test GET /api/document/download/{filename} endpoint"""

    def test_download_converted_file(self, client, sample_docx):
        """Test downloading a converted document file"""
        # First, convert a document
        with open(sample_docx, 'rb') as f:
            convert_response = client.post(
                "/api/document/convert",
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"output_format": "pdf"}
            )

        assert convert_response.status_code == 200
        output_filename = convert_response.json()["output_file"]

        # Now download it
        download_response = client.get(f"/api/document/download/{output_filename}")

        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "application/octet-stream"
        assert len(download_response.content) > 0

    def test_download_nonexistent_file(self, client):
        """Test downloading a file that doesn't exist"""
        response = client.get("/api/document/download/nonexistent.pdf")

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
            response = client.get(f"/api/document/download/{malicious_name}")
            # Should either be 400 (validation) or 404 (not found)
            assert response.status_code in [400, 404], \
                f"Path traversal not blocked for: {malicious_name}"


class TestDocumentInfo:
    """Test POST /api/document/info endpoint"""

    def test_get_document_info_success(self, client, sample_docx):
        """Test successful document info retrieval"""
        with open(sample_docx, 'rb') as f:
            response = client.post(
                "/api/document/info",
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            )

        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert "size" in data
        assert "format" in data
        assert "metadata" in data

    def test_get_markdown_document_info(self, client, sample_markdown):
        """Test getting info for markdown document"""
        with open(sample_markdown, 'rb') as f:
            response = client.post(
                "/api/document/info",
                files={"file": ("test.md", f, "text/markdown")}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "md"
        assert data["filename"] == "test.md"

    def test_get_text_document_info(self, client, sample_txt):
        """Test getting info for text document"""
        with open(sample_txt, 'rb') as f:
            response = client.post(
                "/api/document/info",
                files={"file": ("test.txt", f, "text/plain")}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "txt"
        assert data["size"] > 0

    def test_get_document_info_invalid_file(self, client, temp_dir):
        """Test document info with invalid file"""
        # Create a non-document file
        invalid_file = temp_dir / "invalid.xyz"
        invalid_file.write_text("not a document")

        with open(invalid_file, 'rb') as f:
            response = client.post(
                "/api/document/info",
                files={"file": ("invalid.xyz", f, "application/octet-stream")}
            )

        # Returns 400 or 500 depending on validation stage
        assert response.status_code in [400, 500]


class TestDocumentSecurityValidation:
    """Test security-critical validation in document endpoints"""

    def test_malicious_filename_sanitized(self, client, sample_docx):
        """Test that malicious filenames are sanitized"""
        malicious_filenames = [
            "test; rm -rf /.docx",
            "test$(whoami).docx",
            "test`whoami`.docx",
        ]

        for malicious_name in malicious_filenames:
            with open(sample_docx, 'rb') as f:
                response = client.post(
                    "/api/document/convert",
                    files={"file": (malicious_name, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                    data={"output_format": "pdf"}
                )

            # Should succeed (filename sanitized) or fail safely
            assert response.status_code in [200, 400, 500]
            if response.status_code == 200:
                # Verify output filename doesn't contain shell metacharacters
                output_file = response.json()["output_file"]
                dangerous_chars = [';', '$', '`', '|', '&', '<', '>']
                for char in dangerous_chars:
                    assert char not in output_file

    def test_null_byte_injection_blocked(self, client, sample_docx):
        """Test that null byte injection is sanitized"""
        with open(sample_docx, 'rb') as f:
            response = client.post(
                "/api/document/convert",
                files={"file": ("test\x00.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"output_format": "pdf"}
            )

        # Null bytes are sanitized, so conversion succeeds
        # but output filename should not contain null bytes
        if response.status_code == 200:
            output_file = response.json()["output_file"]
            assert '\x00' not in output_file
        else:
            # Or it fails validation
            assert response.status_code in [400, 500]


class TestDocumentConversionFormats:
    """Test various document format conversions"""

    def test_convert_md_to_pdf(self, client, sample_markdown):
        """Test conversion of Markdown to PDF"""
        with open(sample_markdown, 'rb') as f:
            response = client.post(
                "/api/document/convert",
                files={"file": ("test.md", f, "text/markdown")},
                data={"output_format": "pdf"}
            )

        assert response.status_code == 200
        assert response.json()["output_file"].endswith(".pdf")

    def test_convert_md_to_docx(self, client, sample_markdown):
        """Test conversion of Markdown to DOCX"""
        with open(sample_markdown, 'rb') as f:
            response = client.post(
                "/api/document/convert",
                files={"file": ("test.md", f, "text/markdown")},
                data={"output_format": "docx"}
            )

        assert response.status_code == 200
        assert response.json()["output_file"].endswith(".docx")

    def test_convert_docx_to_txt(self, client, sample_docx):
        """Test conversion of DOCX to TXT"""
        with open(sample_docx, 'rb') as f:
            response = client.post(
                "/api/document/convert",
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"output_format": "txt"}
            )

        assert response.status_code == 200
        assert response.json()["output_file"].endswith(".txt")

    def test_convert_docx_to_html(self, client, sample_docx):
        """Test conversion of DOCX to HTML"""
        with open(sample_docx, 'rb') as f:
            response = client.post(
                "/api/document/convert",
                files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"output_format": "html"}
            )

        assert response.status_code == 200
        assert response.json()["output_file"].endswith(".html")
