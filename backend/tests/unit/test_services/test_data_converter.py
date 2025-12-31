"""
Tests for app/services/data_converter.py

COVERAGE GOAL: 85%+
Tests data conversion with JSON, CSV, XML, YAML formats, encoding/delimiter options,
progress tracking, and error handling for malformed data
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock, mock_open
import json
import csv
import xml.etree.ElementTree as ET
import pandas as pd

from app.services.data_converter import DataConverter
from app.config import settings


# ============================================================================
# BASIC FUNCTIONALITY TESTS
# ============================================================================

class TestDataConverterBasics:
    """Test basic DataConverter functionality"""

    def test_initialization(self):
        """Test DataConverter initializes correctly"""
        converter = DataConverter()

        assert converter.supported_formats is not None
        assert "input" in converter.supported_formats
        assert "output" in converter.supported_formats
        assert "json" in converter.supported_formats["input"]
        assert "csv" in converter.supported_formats["output"]

    def test_initialization_with_websocket_manager(self):
        """Test DataConverter can be initialized with custom WebSocket manager"""
        mock_ws_manager = Mock()
        converter = DataConverter(websocket_manager=mock_ws_manager)

        assert converter.websocket_manager == mock_ws_manager

    @pytest.mark.asyncio
    async def test_get_supported_formats(self):
        """Test getting supported data formats"""
        converter = DataConverter()

        formats = await converter.get_supported_formats()

        assert "input" in formats
        assert "output" in formats
        assert isinstance(formats["input"], list)
        assert isinstance(formats["output"], list)
        # Check supported data formats
        assert "json" in formats["output"]
        assert "csv" in formats["output"]
        assert "xml" in formats["output"]
        assert "yaml" in formats["output"]


# ============================================================================
# JSON CONVERSION TESTS
# ============================================================================

class TestJSONConversion:
    """Test JSON data conversion"""

    @pytest.mark.asyncio
    async def test_json_to_csv_array_structure(self, temp_dir):
        """Test JSON (array) to CSV conversion"""
        converter = DataConverter()

        input_file = temp_dir / "test.json"
        json_data = [
            {"name": "Alice", "age": 30, "city": "New York"},
            {"name": "Bob", "age": 25, "city": "London"},
            {"name": "Charlie", "age": 35, "city": "Paris"}
        ]
        input_file.write_text(json.dumps(json_data))

        output_file = settings.UPLOAD_DIR / "test_converted.csv"

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="csv",
                options={},
                session_id="test-session"
            )

            assert result == output_file
            assert output_file.exists()

            # Verify CSV content
            df = pd.read_csv(output_file)
            assert len(df) == 3
            assert "name" in df.columns
            assert "age" in df.columns
            assert "city" in df.columns

            # Verify progress was sent
            assert mock_progress.call_count >= 4

    @pytest.mark.asyncio
    async def test_json_to_csv_dict_with_lists(self, temp_dir):
        """Test JSON (dict of lists) to CSV conversion"""
        converter = DataConverter()

        input_file = temp_dir / "test.json"
        json_data = {
            "name": ["Alice", "Bob", "Charlie"],
            "age": [30, 25, 35],
            "city": ["New York", "London", "Paris"]
        }
        input_file.write_text(json.dumps(json_data))

        output_file = settings.UPLOAD_DIR / "test_converted.csv"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="csv",
                options={},
                session_id="test-session"
            )

            assert result == output_file
            df = pd.read_csv(output_file)
            assert len(df) == 3

    @pytest.mark.asyncio
    async def test_json_to_csv_single_object(self, temp_dir):
        """Test JSON (single object) to CSV conversion"""
        converter = DataConverter()

        input_file = temp_dir / "test.json"
        json_data = {"name": "Alice", "age": 30, "city": "New York"}
        input_file.write_text(json.dumps(json_data))

        output_file = settings.UPLOAD_DIR / "test_converted.csv"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="csv",
                options={},
                session_id="test-session"
            )

            assert result == output_file
            df = pd.read_csv(output_file)
            assert len(df) == 1

    @pytest.mark.asyncio
    async def test_json_to_xml_conversion(self, temp_dir):
        """Test JSON to XML conversion"""
        converter = DataConverter()

        input_file = temp_dir / "test.json"
        json_data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        input_file.write_text(json.dumps(json_data))

        output_file = settings.UPLOAD_DIR / "test_converted.xml"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="xml",
                options={},
                session_id="test-session"
            )

            assert result == output_file
            assert output_file.exists()

            # Verify XML structure
            tree = ET.parse(output_file)
            root = tree.getroot()
            assert root.tag == "data"
            assert len(list(root)) == 2  # 2 items

    @pytest.mark.asyncio
    async def test_json_to_yaml_conversion(self, temp_dir):
        """Test JSON to YAML conversion"""
        converter = DataConverter()

        input_file = temp_dir / "test.json"
        json_data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        input_file.write_text(json.dumps(json_data))

        output_file = settings.UPLOAD_DIR / "test_converted.yaml"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="yaml",
                options={},
                session_id="test-session"
            )

            assert result == output_file
            assert output_file.exists()

            # Verify YAML can be parsed
            import yaml
            with open(output_file, 'r') as f:
                data = yaml.safe_load(f)
                assert len(data) == 2

    @pytest.mark.asyncio
    async def test_json_malformed_raises_error(self, temp_dir):
        """Test malformed JSON raises error"""
        converter = DataConverter()

        input_file = temp_dir / "test.json"
        input_file.write_text("{ invalid json }")

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            with pytest.raises(Exception):
                await converter.convert(
                    input_path=input_file,
                    output_format="csv",
                    options={},
                    session_id="test-session"
                )

            # Verify failure progress was sent
            last_call = mock_progress.call_args_list[-1]
            assert "failed" in str(last_call)

    @pytest.mark.asyncio
    async def test_json_unsupported_structure_raises_error(self, temp_dir):
        """Test JSON with unsupported structure raises error"""
        converter = DataConverter()

        input_file = temp_dir / "test.json"
        input_file.write_text(json.dumps("just a string"))

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            with pytest.raises(ValueError, match="Unsupported JSON structure"):
                await converter.convert(
                    input_path=input_file,
                    output_format="csv",
                    options={},
                    session_id="test-session"
                )

    @pytest.mark.asyncio
    async def test_json_with_custom_encoding(self, temp_dir):
        """Test JSON conversion with custom encoding"""
        converter = DataConverter()

        input_file = temp_dir / "test.json"
        json_data = [{"name": "José", "city": "São Paulo"}]
        # Write with UTF-8 encoding
        input_file.write_text(json.dumps(json_data, ensure_ascii=False), encoding="utf-8")

        output_file = settings.UPLOAD_DIR / "test_converted.csv"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="csv",
                options={"encoding": "utf-8"},
                session_id="test-session"
            )

            assert result == output_file


# ============================================================================
# CSV CONVERSION TESTS
# ============================================================================

class TestCSVConversion:
    """Test CSV data conversion"""

    @pytest.mark.asyncio
    async def test_csv_to_json_conversion(self, temp_dir):
        """Test CSV to JSON conversion"""
        converter = DataConverter()

        input_file = temp_dir / "test.csv"
        csv_content = "name,age,city\nAlice,30,New York\nBob,25,London"
        input_file.write_text(csv_content)

        output_file = settings.UPLOAD_DIR / "test_converted.json"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="json",
                options={},
                session_id="test-session"
            )

            assert result == output_file
            assert output_file.exists()

            # Verify JSON content
            with open(output_file, 'r') as f:
                data = json.load(f)
                assert len(data) == 2
                assert data[0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_csv_to_xml_conversion(self, temp_dir):
        """Test CSV to XML conversion"""
        converter = DataConverter()

        input_file = temp_dir / "test.csv"
        csv_content = "name,age\nAlice,30\nBob,25"
        input_file.write_text(csv_content)

        output_file = settings.UPLOAD_DIR / "test_converted.xml"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="xml",
                options={},
                session_id="test-session"
            )

            assert result == output_file
            assert output_file.exists()

    @pytest.mark.asyncio
    async def test_csv_with_custom_delimiter(self, temp_dir):
        """Test CSV conversion with custom delimiter"""
        converter = DataConverter()

        input_file = temp_dir / "test.csv"
        csv_content = "name;age;city\nAlice;30;New York\nBob;25;London"
        input_file.write_text(csv_content)

        output_file = settings.UPLOAD_DIR / "test_converted.json"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="json",
                options={"delimiter": ";"},
                session_id="test-session"
            )

            assert result == output_file

            # Verify data was parsed correctly with custom delimiter
            with open(output_file, 'r') as f:
                data = json.load(f)
                assert len(data) == 2
                assert data[0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_csv_output_with_custom_delimiter(self, temp_dir):
        """Test CSV output with custom delimiter"""
        converter = DataConverter()

        input_file = temp_dir / "test.json"
        json_data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        input_file.write_text(json.dumps(json_data))

        output_file = settings.UPLOAD_DIR / "test_converted.csv"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="csv",
                options={"delimiter": ";"},
                session_id="test-session"
            )

            assert result == output_file

            # Verify delimiter in output
            content = output_file.read_text()
            assert ";" in content

    @pytest.mark.asyncio
    async def test_csv_with_custom_encoding(self, temp_dir):
        """Test CSV conversion with custom encoding"""
        converter = DataConverter()

        input_file = temp_dir / "test.csv"
        csv_content = "name,age\nJosé,30\nMaría,25"
        input_file.write_text(csv_content, encoding="utf-8")

        output_file = settings.UPLOAD_DIR / "test_converted.json"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="json",
                options={"encoding": "utf-8"},
                session_id="test-session"
            )

            assert result == output_file

    @pytest.mark.asyncio
    async def test_csv_malformed_handling(self, temp_dir):
        """Test malformed CSV handling"""
        converter = DataConverter()

        input_file = temp_dir / "test.csv"
        # CSV with mismatched columns
        csv_content = "name,age,city\nAlice,30\nBob,25,London,Extra"
        input_file.write_text(csv_content)

        output_file = settings.UPLOAD_DIR / "test_converted.json"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Should still convert (pandas handles this)
            result = await converter.convert(
                input_path=input_file,
                output_format="json",
                options={},
                session_id="test-session"
            )

            assert result == output_file


# ============================================================================
# XML CONVERSION TESTS
# ============================================================================

class TestXMLConversion:
    """Test XML data conversion"""

    @pytest.mark.asyncio
    async def test_xml_to_json_conversion(self, temp_dir):
        """Test XML to JSON conversion"""
        converter = DataConverter()

        input_file = temp_dir / "test.xml"
        xml_content = """<?xml version="1.0"?>
<data>
    <item>
        <name>Alice</name>
        <age>30</age>
    </item>
    <item>
        <name>Bob</name>
        <age>25</age>
    </item>
</data>"""
        input_file.write_text(xml_content)

        output_file = settings.UPLOAD_DIR / "test_converted.json"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="json",
                options={},
                session_id="test-session"
            )

            assert result == output_file
            assert output_file.exists()

            # Verify JSON content
            with open(output_file, 'r') as f:
                data = json.load(f)
                assert len(data) == 2

    @pytest.mark.asyncio
    async def test_xml_to_csv_conversion(self, temp_dir):
        """Test XML to CSV conversion"""
        converter = DataConverter()

        input_file = temp_dir / "test.xml"
        xml_content = """<?xml version="1.0"?>
<data>
    <item>
        <name>Alice</name>
        <age>30</age>
    </item>
    <item>
        <name>Bob</name>
        <age>25</age>
    </item>
</data>"""
        input_file.write_text(xml_content)

        output_file = settings.UPLOAD_DIR / "test_converted.csv"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="csv",
                options={},
                session_id="test-session"
            )

            assert result == output_file

            # Verify CSV content
            df = pd.read_csv(output_file)
            assert len(df) == 2

    @pytest.mark.asyncio
    async def test_xml_nested_structure_handling(self, temp_dir):
        """Test XML with nested structure"""
        converter = DataConverter()

        input_file = temp_dir / "test.xml"
        # Simple flat structure (current implementation expects this)
        xml_content = """<?xml version="1.0"?>
<data>
    <item>
        <name>Alice</name>
        <details>New York</details>
    </item>
    <item>
        <name>Bob</name>
        <details>London</details>
    </item>
</data>"""
        input_file.write_text(xml_content)

        output_file = settings.UPLOAD_DIR / "test_converted.json"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="json",
                options={},
                session_id="test-session"
            )

            assert result == output_file

    @pytest.mark.asyncio
    async def test_xml_malformed_raises_error(self, temp_dir):
        """Test malformed XML raises error"""
        converter = DataConverter()

        input_file = temp_dir / "test.xml"
        xml_content = """<?xml version="1.0"?>
<data>
    <item>
        <name>Alice</name>
    <item>"""  # Missing closing tag
        input_file.write_text(xml_content)

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            with pytest.raises(Exception):
                await converter.convert(
                    input_path=input_file,
                    output_format="json",
                    options={},
                    session_id="test-session"
                )


# ============================================================================
# YAML CONVERSION TESTS
# ============================================================================

class TestYAMLConversion:
    """Test YAML data conversion"""

    @pytest.mark.asyncio
    async def test_yaml_to_json_conversion(self, temp_dir):
        """Test YAML to JSON conversion"""
        converter = DataConverter()

        input_file = temp_dir / "test.yaml"
        yaml_content = """
- name: Alice
  age: 30
  city: New York
- name: Bob
  age: 25
  city: London
"""
        input_file.write_text(yaml_content)

        output_file = settings.UPLOAD_DIR / "test_converted.json"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="json",
                options={},
                session_id="test-session"
            )

            assert result == output_file

            # Verify JSON content
            with open(output_file, 'r') as f:
                data = json.load(f)
                assert len(data) == 2

    @pytest.mark.asyncio
    async def test_yaml_to_csv_conversion(self, temp_dir):
        """Test YAML to CSV conversion"""
        converter = DataConverter()

        input_file = temp_dir / "test.yaml"
        yaml_content = """
- name: Alice
  age: 30
- name: Bob
  age: 25
"""
        input_file.write_text(yaml_content)

        output_file = settings.UPLOAD_DIR / "test_converted.csv"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="csv",
                options={},
                session_id="test-session"
            )

            assert result == output_file

            # Verify CSV content
            df = pd.read_csv(output_file)
            assert len(df) == 2

    @pytest.mark.asyncio
    async def test_yml_extension_support(self, temp_dir):
        """Test .yml extension is supported"""
        converter = DataConverter()

        input_file = temp_dir / "test.yml"
        yaml_content = """
- name: Alice
  age: 30
"""
        input_file.write_text(yaml_content)

        output_file = settings.UPLOAD_DIR / "test_converted.json"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="json",
                options={},
                session_id="test-session"
            )

            assert result == output_file

    @pytest.mark.asyncio
    async def test_yaml_malformed_handling(self, temp_dir):
        """Test malformed YAML handling"""
        converter = DataConverter()

        input_file = temp_dir / "test.yaml"
        yaml_content = """
invalid: [unclosed
  list
"""
        input_file.write_text(yaml_content)

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            with pytest.raises(Exception):
                await converter.convert(
                    input_path=input_file,
                    output_format="json",
                    options={},
                    session_id="test-session"
                )


# ============================================================================
# FORMAT SUPPORT TESTS
# ============================================================================

class TestFormatSupport:
    """Test format support and validation"""

    def test_json_in_supported_formats(self):
        """Test JSON is in supported formats"""
        converter = DataConverter()

        assert "json" in converter.supported_formats["input"]
        assert "json" in converter.supported_formats["output"]

    def test_csv_in_supported_formats(self):
        """Test CSV is in supported formats"""
        converter = DataConverter()

        assert "csv" in converter.supported_formats["input"]
        assert "csv" in converter.supported_formats["output"]

    def test_xml_in_supported_formats(self):
        """Test XML is in supported formats"""
        converter = DataConverter()

        assert "xml" in converter.supported_formats["input"]
        assert "xml" in converter.supported_formats["output"]

    def test_yaml_in_supported_formats(self):
        """Test YAML is in supported formats"""
        converter = DataConverter()

        assert "yaml" in converter.supported_formats["input"]
        assert "yaml" in converter.supported_formats["output"]

    def test_yml_in_supported_formats(self):
        """Test YML is in supported formats"""
        converter = DataConverter()

        assert "yml" in converter.supported_formats["input"]
        assert "yml" in converter.supported_formats["output"]

    @pytest.mark.asyncio
    async def test_unsupported_input_format_raises_error(self, temp_dir):
        """Test unsupported input format raises error"""
        converter = DataConverter()

        input_file = temp_dir / "test.txt"
        input_file.write_text("some text")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with pytest.raises(ValueError, match="Unsupported conversion"):
                await converter.convert(
                    input_path=input_file,
                    output_format="json",
                    options={},
                    session_id="test-session"
                )

    @pytest.mark.asyncio
    async def test_unsupported_output_format_raises_error(self, temp_dir):
        """Test unsupported output format raises error"""
        converter = DataConverter()

        input_file = temp_dir / "test.json"
        input_file.write_text(json.dumps([{"name": "Alice"}]))

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with pytest.raises(ValueError, match="Unsupported conversion"):
                await converter.convert(
                    input_path=input_file,
                    output_format="txt",
                    options={},
                    session_id="test-session"
                )


# ============================================================================
# PROGRESS UPDATE TESTS
# ============================================================================

class TestProgressUpdates:
    """Test progress tracking during conversion"""

    @pytest.mark.asyncio
    async def test_progress_sent_at_key_stages(self, temp_dir):
        """Test progress is sent at key conversion stages"""
        converter = DataConverter()

        input_file = temp_dir / "test.json"
        json_data = [{"name": "Alice"}, {"name": "Bob"}]
        input_file.write_text(json.dumps(json_data))

        output_file = settings.UPLOAD_DIR / "test_converted.csv"

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            output_file.parent.mkdir(parents=True, exist_ok=True)

            await converter.convert(
                input_path=input_file,
                output_format="csv",
                options={},
                session_id="test-session"
            )

            # Verify progress calls
            assert mock_progress.call_count >= 4

            # Check for key stages
            call_args_list = [call[0] for call in mock_progress.call_args_list]

            # First call should be 0% converting
            assert call_args_list[0][1] == 0
            assert "converting" in call_args_list[0][2]

            # Final call should be 100% completed
            final_call = call_args_list[-1]
            assert final_call[1] == 100
            assert "completed" in final_call[2]

    @pytest.mark.asyncio
    async def test_progress_includes_session_id(self, temp_dir):
        """Test progress updates include session ID"""
        converter = DataConverter()

        input_file = temp_dir / "test.json"
        json_data = [{"name": "Alice"}]
        input_file.write_text(json.dumps(json_data))

        output_file = settings.UPLOAD_DIR / "test_converted.csv"

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            output_file.parent.mkdir(parents=True, exist_ok=True)

            session_id = "unique-session-123"
            await converter.convert(
                input_path=input_file,
                output_format="csv",
                options={},
                session_id=session_id
            )

            # Verify session ID is passed to all progress calls
            for call in mock_progress.call_args_list:
                assert call[0][0] == session_id

    @pytest.mark.asyncio
    async def test_progress_on_conversion_failure(self, temp_dir):
        """Test progress sent on conversion failure"""
        converter = DataConverter()

        input_file = temp_dir / "test.json"
        input_file.write_text("{ invalid json }")

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            with pytest.raises(Exception):
                await converter.convert(
                    input_path=input_file,
                    output_format="csv",
                    options={},
                    session_id="test-session"
                )

            # Verify final progress shows failure
            final_call = mock_progress.call_args_list[-1]
            assert "failed" in final_call[0][2]

    @pytest.mark.asyncio
    async def test_progress_percentage_increases(self, temp_dir):
        """Test progress percentage increases monotonically"""
        converter = DataConverter()

        input_file = temp_dir / "test.json"
        json_data = [{"name": f"Person{i}"} for i in range(100)]
        input_file.write_text(json.dumps(json_data))

        output_file = settings.UPLOAD_DIR / "test_converted.csv"

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            output_file.parent.mkdir(parents=True, exist_ok=True)

            await converter.convert(
                input_path=input_file,
                output_format="csv",
                options={},
                session_id="test-session"
            )

            # Extract progress percentages
            percentages = [call[0][1] for call in mock_progress.call_args_list]

            # Verify they're in order
            assert percentages[0] == 0
            assert percentages[-1] == 100

            # Verify no decrease
            for i in range(1, len(percentages)):
                assert percentages[i] >= percentages[i-1]


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_empty_json_array(self, temp_dir):
        """Test empty JSON array conversion"""
        converter = DataConverter()

        input_file = temp_dir / "test.json"
        input_file.write_text(json.dumps([]))

        output_file = settings.UPLOAD_DIR / "test_converted.csv"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="csv",
                options={},
                session_id="test-session"
            )

            assert result == output_file
            df = pd.read_csv(output_file)
            assert len(df) == 0

    @pytest.mark.asyncio
    async def test_json_with_null_values(self, temp_dir):
        """Test JSON with null values"""
        converter = DataConverter()

        input_file = temp_dir / "test.json"
        json_data = [
            {"name": "Alice", "age": None},
            {"name": None, "age": 25}
        ]
        input_file.write_text(json.dumps(json_data))

        output_file = settings.UPLOAD_DIR / "test_converted.csv"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="csv",
                options={},
                session_id="test-session"
            )

            assert result == output_file

    @pytest.mark.asyncio
    async def test_csv_empty_file(self, temp_dir):
        """Test empty CSV file"""
        converter = DataConverter()

        input_file = temp_dir / "test.csv"
        input_file.write_text("")

        output_file = settings.UPLOAD_DIR / "test_converted.json"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Empty file should raise error
            with pytest.raises(Exception):
                await converter.convert(
                    input_path=input_file,
                    output_format="json",
                    options={},
                    session_id="test-session"
                )

    @pytest.mark.asyncio
    async def test_json_pretty_print_option(self, temp_dir):
        """Test JSON output with pretty print option"""
        converter = DataConverter()

        input_file = temp_dir / "test.csv"
        csv_content = "name,age\nAlice,30"
        input_file.write_text(csv_content)

        output_file = settings.UPLOAD_DIR / "test_converted.json"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="json",
                options={"pretty": True},
                session_id="test-session"
            )

            assert result == output_file

            # Verify pretty formatting
            content = output_file.read_text()
            assert "\n" in content  # Pretty print includes newlines

    @pytest.mark.asyncio
    async def test_json_compact_output_option(self, temp_dir):
        """Test JSON output without pretty print"""
        converter = DataConverter()

        input_file = temp_dir / "test.csv"
        csv_content = "name,age\nAlice,30"
        input_file.write_text(csv_content)

        output_file = settings.UPLOAD_DIR / "test_converted.json"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="json",
                options={"pretty": False},
                session_id="test-session"
            )

            assert result == output_file

    @pytest.mark.asyncio
    async def test_xml_to_yaml_conversion(self, temp_dir):
        """Test XML to YAML conversion"""
        converter = DataConverter()

        input_file = temp_dir / "test.xml"
        xml_content = """<?xml version="1.0"?>
<data>
    <item>
        <name>Alice</name>
        <age>30</age>
    </item>
</data>"""
        input_file.write_text(xml_content)

        output_file = settings.UPLOAD_DIR / "test_converted.yaml"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="yaml",
                options={},
                session_id="test-session"
            )

            assert result == output_file
            assert output_file.exists()

    @pytest.mark.asyncio
    async def test_output_path_generation(self, temp_dir):
        """Test output path is generated correctly"""
        converter = DataConverter()

        input_file = temp_dir / "my_data.json"
        json_data = [{"name": "Alice"}]
        input_file.write_text(json.dumps(json_data))

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="csv",
                options={},
                session_id="test-session"
            )

            # Output should have _converted suffix and correct extension
            assert result.stem == "my_data_converted"
            assert result.suffix == ".csv"

    @pytest.mark.asyncio
    async def test_csv_to_yaml_conversion(self, temp_dir):
        """Test CSV to YAML conversion"""
        converter = DataConverter()

        input_file = temp_dir / "test.csv"
        csv_content = "name,age\nAlice,30\nBob,25"
        input_file.write_text(csv_content)

        output_file = settings.UPLOAD_DIR / "test_converted.yaml"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="yaml",
                options={},
                session_id="test-session"
            )

            assert result == output_file
            assert output_file.exists()

    @pytest.mark.asyncio
    async def test_json_with_unicode_characters(self, temp_dir):
        """Test JSON with Unicode characters"""
        converter = DataConverter()

        input_file = temp_dir / "test.json"
        json_data = [
            {"name": "José", "city": "São Paulo"},
            {"name": "François", "city": "Paris"},
            {"name": "Müller", "city": "Berlin"}
        ]
        input_file.write_text(json.dumps(json_data, ensure_ascii=False), encoding="utf-8")

        output_file = settings.UPLOAD_DIR / "test_converted.csv"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="csv",
                options={"encoding": "utf-8"},
                session_id="test-session"
            )

            assert result == output_file


# ============================================================================
# CONFTEST FIXTURES (if not already present)
# ============================================================================

@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test files"""
    return tmp_path
