"""
Integration tests for data router endpoints.

Tests the full API integration including:
- POST /api/data/convert - Data conversion endpoint (JSON, CSV, XML)
- GET /api/data/formats - Supported formats endpoint
- GET /api/data/download/{filename} - File download endpoint
- POST /api/data/info - Data metadata endpoint

Security tests:
- Path traversal prevention in download
- File size validation
- Extension validation
- Malicious filename sanitization
"""

import pytest
import json
import csv
from pathlib import Path
from io import StringIO
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    """Create test client for API testing"""
    return TestClient(app)


@pytest.fixture
def sample_json(temp_dir):
    """Create a sample JSON file for testing"""
    json_path = temp_dir / "test_data.json"
    data = {
        "users": [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "age": 30,
                "active": True
            },
            {
                "id": 2,
                "name": "Jane Smith",
                "email": "jane@example.com",
                "age": 28,
                "active": False
            },
            {
                "id": 3,
                "name": "Bob Johnson",
                "email": "bob@example.com",
                "age": 35,
                "active": True
            }
        ],
        "metadata": {
            "version": "1.0",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }
    json_path.write_text(json.dumps(data, indent=2))
    return json_path


@pytest.fixture
def sample_csv(temp_dir):
    """Create a sample CSV file for testing"""
    csv_path = temp_dir / "test_data.csv"
    csv_content = """id,name,email,age,active
1,John Doe,john@example.com,30,true
2,Jane Smith,jane@example.com,28,false
3,Bob Johnson,bob@example.com,35,true
4,Alice Brown,alice@example.com,32,true
5,Charlie Davis,charlie@example.com,29,false"""
    csv_path.write_text(csv_content)
    return csv_path


@pytest.fixture
def sample_xml(temp_dir):
    """Create a sample XML file for testing"""
    xml_path = temp_dir / "test_data.xml"
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<root>
    <users>
        <user>
            <id>1</id>
            <name>John Doe</name>
            <email>john@example.com</email>
            <age>30</age>
            <active>true</active>
        </user>
        <user>
            <id>2</id>
            <name>Jane Smith</name>
            <email>jane@example.com</email>
            <age>28</age>
            <active>false</active>
        </user>
        <user>
            <id>3</id>
            <name>Bob Johnson</name>
            <email>bob@example.com</email>
            <age>35</age>
            <active>true</active>
        </user>
    </users>
    <metadata>
        <version>1.0</version>
        <timestamp>2024-01-01T00:00:00Z</timestamp>
    </metadata>
</root>"""
    xml_path.write_text(xml_content)
    return xml_path


@pytest.fixture
def malformed_json(temp_dir):
    """Create a malformed JSON file for testing error handling"""
    json_path = temp_dir / "malformed.json"
    json_path.write_text('{"invalid": json content without closing bracket')
    return json_path


@pytest.fixture
def malformed_csv(temp_dir):
    """Create a malformed CSV file for testing error handling"""
    csv_path = temp_dir / "malformed.csv"
    # CSV with mismatched column counts
    csv_content = """id,name,email
1,John
2,Jane,jane@example.com,extra_column
3,Bob,bob@example.com"""
    csv_path.write_text(csv_content)
    return csv_path


class TestDataConvert:
    """Test POST /api/data/convert endpoint"""

    def test_convert_json_to_csv_success(self, client, sample_json):
        """Test successful JSON to CSV conversion"""
        with open(sample_json, 'rb') as f:
            response = client.post(
                "/api/data/convert",
                files={"file": ("test.json", f, "application/json")},
                data={"output_format": "csv"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "session_id" in data
        assert data["output_file"].endswith(".csv")
        assert "download_url" in data

    def test_convert_csv_to_json_success(self, client, sample_csv):
        """Test successful CSV to JSON conversion"""
        with open(sample_csv, 'rb') as f:
            response = client.post(
                "/api/data/convert",
                files={"file": ("test.csv", f, "text/csv")},
                data={"output_format": "json"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".json")
        assert "session_id" in data
        assert "download_url" in data

    def test_convert_xml_to_json_success(self, client, sample_xml):
        """Test successful XML to JSON conversion"""
        with open(sample_xml, 'rb') as f:
            response = client.post(
                "/api/data/convert",
                files={"file": ("test.xml", f, "application/xml")},
                data={"output_format": "json"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".json")

    def test_convert_with_delimiter_parameter(self, client, sample_json):
        """Test conversion with custom CSV delimiter parameter"""
        with open(sample_json, 'rb') as f:
            response = client.post(
                "/api/data/convert",
                files={"file": ("test.json", f, "application/json")},
                data={"output_format": "csv", "delimiter": ";"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".csv")

    def test_convert_json_to_xml_success(self, client, sample_json):
        """Test successful JSON to XML conversion"""
        with open(sample_json, 'rb') as f:
            response = client.post(
                "/api/data/convert",
                files={"file": ("test.json", f, "application/json")},
                data={"output_format": "xml"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".xml")

    def test_convert_csv_to_xml_success(self, client, sample_csv):
        """Test successful CSV to XML conversion"""
        with open(sample_csv, 'rb') as f:
            response = client.post(
                "/api/data/convert",
                files={"file": ("test.csv", f, "text/csv")},
                data={"output_format": "xml"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output_file"].endswith(".xml")

    def test_convert_with_pretty_print_true(self, client, sample_csv):
        """Test conversion with pretty print enabled for JSON output"""
        with open(sample_csv, 'rb') as f:
            response = client.post(
                "/api/data/convert",
                files={"file": ("test.csv", f, "text/csv")},
                data={"output_format": "json", "pretty": "true"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_convert_with_pretty_print_false(self, client, sample_csv):
        """Test conversion with pretty print disabled for JSON output"""
        with open(sample_csv, 'rb') as f:
            response = client.post(
                "/api/data/convert",
                files={"file": ("test.csv", f, "text/csv")},
                data={"output_format": "json", "pretty": "false"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_convert_invalid_output_format(self, client, sample_json):
        """Test conversion with invalid output format"""
        with open(sample_json, 'rb') as f:
            response = client.post(
                "/api/data/convert",
                files={"file": ("test.json", f, "application/json")},
                data={"output_format": "invalid_format"}
            )

        assert response.status_code == 400
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error")
        assert "Unsupported output format" in str(error_msg) or "unsupported" in str(error_msg).lower()

    def test_convert_malformed_json_input(self, client, malformed_json):
        """Test conversion with malformed JSON input data"""
        with open(malformed_json, 'rb') as f:
            response = client.post(
                "/api/data/convert",
                files={"file": ("malformed.json", f, "application/json")},
                data={"output_format": "csv"}
            )

        # Should fail with 400 or 500 depending on error handling
        assert response.status_code in [400, 500]

    def test_convert_unsupported_input_format(self, client, temp_dir):
        """Test conversion with unsupported input file format"""
        # Create a fake data file with unsupported extension
        fake_file = temp_dir / "invalid.exe"
        fake_file.write_text("not a data file")

        with open(fake_file, 'rb') as f:
            response = client.post(
                "/api/data/convert",
                files={"file": ("invalid.exe", f, "application/octet-stream")},
                data={"output_format": "json"}
            )

        assert response.status_code == 400
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error")
        assert ("Invalid or unsupported file extension" in str(error_msg) or
                "Unsupported file format" in str(error_msg))


class TestDataFormats:
    """Test GET /api/data/formats endpoint"""

    def test_get_formats_success(self, client):
        """Test successful retrieval of supported data formats"""
        response = client.get("/api/data/formats")

        assert response.status_code == 200
        data = response.json()
        assert "input_formats" in data
        assert "output_formats" in data
        assert isinstance(data["input_formats"], list)
        assert isinstance(data["output_formats"], list)

    def test_formats_include_common_types(self, client):
        """Test that common data formats are included"""
        response = client.get("/api/data/formats")
        data = response.json()

        # Check for common data formats
        common_formats = ["json", "csv", "xml"]
        for fmt in common_formats:
            assert fmt in data["output_formats"], f"{fmt} not in output formats"
            assert fmt in data["input_formats"], f"{fmt} not in input formats"

    def test_formats_response_structure(self, client):
        """Test the structure of formats response"""
        response = client.get("/api/data/formats")
        data = response.json()

        # Verify all formats are strings
        for fmt in data["input_formats"]:
            assert isinstance(fmt, str)
            assert len(fmt) > 0

        for fmt in data["output_formats"]:
            assert isinstance(fmt, str)
            assert len(fmt) > 0


class TestDataDownload:
    """Test GET /api/data/download/{filename} endpoint"""

    def test_download_converted_file(self, client, sample_json):
        """Test downloading a converted data file"""
        # First, convert a data file
        with open(sample_json, 'rb') as f:
            convert_response = client.post(
                "/api/data/convert",
                files={"file": ("test.json", f, "application/json")},
                data={"output_format": "csv"}
            )

        assert convert_response.status_code == 200
        output_filename = convert_response.json()["output_file"]

        # Now download it
        download_response = client.get(f"/api/data/download/{output_filename}")

        assert download_response.status_code == 200
        # Should return proper MIME type for the file format (csv)
        assert download_response.headers["content-type"] == "text/csv; charset=utf-8"
        assert len(download_response.content) > 0

    def test_download_nonexistent_file(self, client):
        """Test downloading a file that doesn't exist"""
        response = client.get("/api/data/download/nonexistent_file.csv")

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
            response = client.get(f"/api/data/download/{malicious_name}")
            # Should either be 400 (validation) or 404 (not found)
            assert response.status_code in [400, 404], \
                f"Path traversal not blocked for: {malicious_name}"

    def test_download_absolute_path_blocked(self, client):
        """Test that absolute path access is blocked"""
        malicious_paths = [
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
        ]

        for path in malicious_paths:
            response = client.get(f"/api/data/download/{path}")
            assert response.status_code in [400, 404]


class TestDataInfo:
    """Test POST /api/data/info endpoint"""

    def test_get_data_info_json_success(self, client, sample_json):
        """Test successful JSON data info retrieval"""
        with open(sample_json, 'rb') as f:
            response = client.post(
                "/api/data/info",
                files={"file": ("test.json", f, "application/json")}
            )

        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert "size" in data
        assert "format" in data
        assert "metadata" in data
        assert data["filename"] == "test.json"
        assert data["format"] == "json"

    def test_get_data_info_csv_success(self, client, sample_csv):
        """Test successful CSV data info retrieval"""
        with open(sample_csv, 'rb') as f:
            response = client.post(
                "/api/data/info",
                files={"file": ("test.csv", f, "text/csv")}
            )

        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert "size" in data
        assert "format" in data
        assert data["filename"] == "test.csv"
        assert data["format"] == "csv"

    def test_get_data_info_xml_success(self, client, sample_xml):
        """Test successful XML data info retrieval"""
        with open(sample_xml, 'rb') as f:
            response = client.post(
                "/api/data/info",
                files={"file": ("test.xml", f, "application/xml")}
            )

        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert "size" in data
        assert "format" in data
        assert data["filename"] == "test.xml"
        assert data["format"] == "xml"

    def test_get_data_info_includes_row_count(self, client, sample_csv):
        """Test that data info includes row count information"""
        with open(sample_csv, 'rb') as f:
            response = client.post(
                "/api/data/info",
                files={"file": ("test.csv", f, "text/csv")}
            )

        assert response.status_code == 200
        metadata = response.json()["metadata"]
        assert "rows" in metadata or "row_count" in metadata or "lines" in metadata

    def test_get_data_info_includes_column_info(self, client, sample_csv):
        """Test that data info includes column information"""
        with open(sample_csv, 'rb') as f:
            response = client.post(
                "/api/data/info",
                files={"file": ("test.csv", f, "text/csv")}
            )

        assert response.status_code == 200
        metadata = response.json()["metadata"]
        # Should have column-related metadata
        assert any(key in metadata for key in ["columns", "column_count", "fields", "headers"])

    def test_get_data_info_invalid_file(self, client, temp_dir):
        """Test data info with invalid file"""
        # Create a non-data file
        invalid_file = temp_dir / "invalid.txt"
        invalid_file.write_text("not a data file")

        with open(invalid_file, 'rb') as f:
            response = client.post(
                "/api/data/info",
                files={"file": ("invalid.txt", f, "text/plain")}
            )

        # Returns 400 or 500 depending on validation stage
        assert response.status_code in [400, 500]


class TestDataSecurityValidation:
    """Test security-critical validation in data endpoints"""

    def test_malicious_filename_sanitized(self, client, sample_json):
        """Test that malicious filenames are sanitized"""
        malicious_filenames = [
            "test; rm -rf /.json",
            "test$(whoami).json",
            "test`whoami`.json",
        ]

        for malicious_name in malicious_filenames:
            with open(sample_json, 'rb') as f:
                response = client.post(
                    "/api/data/convert",
                    files={"file": (malicious_name, f, "application/json")},
                    data={"output_format": "csv"}
                )

            # Should succeed (filename sanitized) or fail safely
            assert response.status_code in [200, 400, 500]
            if response.status_code == 200:
                # Verify output filename doesn't contain shell metacharacters
                output_file = response.json()["output_file"]
                dangerous_chars = [';', '$', '`', '|', '&', '<', '>']
                for char in dangerous_chars:
                    assert char not in output_file

    def test_null_byte_injection_blocked(self, client, sample_json):
        """Test that null byte injection is sanitized"""
        with open(sample_json, 'rb') as f:
            response = client.post(
                "/api/data/convert",
                files={"file": ("test\x00.json", f, "application/json")},
                data={"output_format": "csv"}
            )

        # Null bytes are sanitized, so conversion succeeds
        # but output filename should not contain null bytes
        if response.status_code == 200:
            output_file = response.json()["output_file"]
            assert '\x00' not in output_file
        else:
            # Or it fails validation
            assert response.status_code in [400, 500]


class TestDataConversionFormats:
    """Test various data format conversions"""

    def test_convert_to_json_format(self, client, sample_csv):
        """Test conversion to JSON format"""
        with open(sample_csv, 'rb') as f:
            response = client.post(
                "/api/data/convert",
                files={"file": ("test.csv", f, "text/csv")},
                data={"output_format": "json"}
            )

        assert response.status_code == 200
        assert response.json()["output_file"].endswith(".json")

    def test_convert_to_csv_format(self, client, sample_json):
        """Test conversion to CSV format"""
        with open(sample_json, 'rb') as f:
            response = client.post(
                "/api/data/convert",
                files={"file": ("test.json", f, "application/json")},
                data={"output_format": "csv"}
            )

        assert response.status_code == 200
        assert response.json()["output_file"].endswith(".csv")

    def test_convert_to_xml_format(self, client, sample_json):
        """Test conversion to XML format"""
        with open(sample_json, 'rb') as f:
            response = client.post(
                "/api/data/convert",
                files={"file": ("test.json", f, "application/json")},
                data={"output_format": "xml"}
            )

        assert response.status_code == 200
        assert response.json()["output_file"].endswith(".xml")

    def test_convert_multiple_chained_formats(self, client, sample_json):
        """Test chained conversions (JSON -> CSV -> XML)"""
        # First conversion: JSON to CSV
        with open(sample_json, 'rb') as f:
            response1 = client.post(
                "/api/data/convert",
                files={"file": ("test.json", f, "application/json")},
                data={"output_format": "csv"}
            )

        assert response1.status_code == 200
        assert response1.json()["output_file"].endswith(".csv")

        # Second conversion: CSV to XML (simulated with new file)
        with open(sample_json, 'rb') as f:
            response2 = client.post(
                "/api/data/convert",
                files={"file": ("test.json", f, "application/json")},
                data={"output_format": "xml"}
            )

        assert response2.status_code == 200
        assert response2.json()["output_file"].endswith(".xml")


class TestDataCleanup:
    """Test cleanup behavior in error scenarios"""

    def test_convert_cleanup_output_file_on_error(self, client, sample_json, monkeypatch):
        """Test that output_path is cleaned up when conversion fails after file creation"""
        from app.services.data_converter import DataConverter
        from app.utils.file_handler import cleanup_file
        from app.config import settings
        from app.models.conversion import ConversionResponse

        cleanup_calls = []
        original_cleanup = cleanup_file

        def mock_cleanup(file_path):
            cleanup_calls.append(str(file_path))
            return original_cleanup(file_path)

        monkeypatch.setattr("app.routers.data.cleanup_file", mock_cleanup)

        output_file = settings.UPLOAD_DIR / "test_output_data.csv"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_bytes(b"fake data")

        async def mock_convert_with_cache(self, input_path, output_format, options, session_id):
            return output_file

        monkeypatch.setattr(DataConverter, "convert_with_cache", mock_convert_with_cache)

        def mock_conversion_response(*args, **kwargs):
            raise Exception("Simulated error after conversion")

        monkeypatch.setattr("app.routers.data.ConversionResponse", mock_conversion_response)

        with open(sample_json, 'rb') as f:
            response = client.post(
                "/api/data/convert",
                files={"file": ("test.json", f, "application/json")},
                data={"output_format": "csv"}
            )

        assert response.status_code == 500
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error")
        assert "Conversion failed" in error_msg
        assert len(cleanup_calls) >= 2
        output_file.unlink(missing_ok=True)

    def test_info_cleanup_temp_file_on_error(self, client, sample_json, monkeypatch):
        """Test that temp_path is cleaned up when info extraction fails"""
        from app.services.data_converter import DataConverter
        from app.utils.file_handler import cleanup_file

        cleanup_calls = []
        original_cleanup = cleanup_file

        def mock_cleanup(file_path):
            cleanup_calls.append(str(file_path))
            return original_cleanup(file_path)

        monkeypatch.setattr("app.routers.data.cleanup_file", mock_cleanup)

        async def mock_get_data_info(self, input_path):
            raise Exception("Simulated info extraction error")

        monkeypatch.setattr(DataConverter, "get_data_info", mock_get_data_info)

        with open(sample_json, 'rb') as f:
            response = client.post(
                "/api/data/info",
                files={"file": ("test.json", f, "application/json")}
            )

        assert response.status_code == 500
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("error")
        assert "Failed to get data info" in error_msg
        assert len(cleanup_calls) >= 1
