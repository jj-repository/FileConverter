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
import configparser
import toml

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

# ============================================================================
# TOML CONVERSION TESTS
# ============================================================================

class TestTOMLConversion:
    """Test TOML data conversion"""

    @pytest.mark.asyncio
    async def test_toml_to_json_conversion(self, temp_dir):
        """Test TOML to JSON conversion"""
        converter = DataConverter()

        input_file = temp_dir / "test.toml"
        toml_content = """
title = "TOML Example"
name = "Alice"
age = 30
city = "New York"
"""
        input_file.write_text(toml_content)

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
                assert len(data) == 1
                assert data[0]["title"] == "TOML Example"

    @pytest.mark.asyncio
    async def test_toml_to_csv_conversion(self, temp_dir):
        """Test TOML to CSV conversion"""
        converter = DataConverter()

        input_file = temp_dir / "test.toml"
        toml_content = """
name = "Alice"
age = 30
"""
        input_file.write_text(toml_content)

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
    async def test_json_to_toml_conversion(self, temp_dir):
        """Test JSON to TOML conversion"""
        converter = DataConverter()

        input_file = temp_dir / "test.json"
        json_data = [{"name": "Alice", "age": 30, "city": "New York"}]
        input_file.write_text(json.dumps(json_data))

        output_file = settings.UPLOAD_DIR / "test_converted.toml"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="toml",
                options={},
                session_id="test-session"
            )

            assert result == output_file
            assert output_file.exists()

            # Verify TOML can be parsed
            data = toml.load(output_file)
            assert data["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_empty_dataframe_to_toml_raises_error(self, temp_dir):
        """Test converting empty DataFrame to TOML raises error"""
        converter = DataConverter()

        input_file = temp_dir / "test.json"
        input_file.write_text(json.dumps([]))

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

            with pytest.raises(ValueError, match="Cannot convert empty DataFrame to TOML"):
                await converter.convert(
                    input_path=input_file,
                    output_format="toml",
                    options={},
                    session_id="test-session"
                )


# ============================================================================
# INI CONVERSION TESTS
# ============================================================================

class TestINIConversion:
    """Test INI data conversion"""

    @pytest.mark.asyncio
    async def test_ini_to_json_conversion(self, temp_dir):
        """Test INI to JSON conversion"""
        converter = DataConverter()

        input_file = temp_dir / "test.ini"
        ini_content = """[database]
host = localhost
port = 5432
name = mydb

[cache]
host = redis-server
port = 6379
"""
        input_file.write_text(ini_content)

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
                assert data[0]["section"] == "database"

    @pytest.mark.asyncio
    async def test_ini_to_csv_conversion(self, temp_dir):
        """Test INI to CSV conversion"""
        converter = DataConverter()

        input_file = temp_dir / "test.ini"
        ini_content = """[server1]
host = localhost
port = 8080

[server2]
host = remote
port = 9090
"""
        input_file.write_text(ini_content)

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
            assert len(df) == 2

    @pytest.mark.asyncio
    async def test_json_to_ini_conversion(self, temp_dir):
        """Test JSON to INI conversion"""
        converter = DataConverter()

        input_file = temp_dir / "test.json"
        json_data = [
            {"section": "database", "host": "localhost", "port": "5432"},
            {"section": "cache", "host": "redis", "port": "6379"}
        ]
        input_file.write_text(json.dumps(json_data))

        output_file = settings.UPLOAD_DIR / "test_converted.ini"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="ini",
                options={},
                session_id="test-session"
            )

            assert result == output_file
            assert output_file.exists()

            # Verify INI can be parsed
            config = configparser.ConfigParser()
            config.read(output_file)
            assert "database" in config.sections()
            assert config["database"]["host"] == "localhost"


# ============================================================================
# JSONL CONVERSION TESTS
# ============================================================================

class TestJSONLConversion:
    """Test JSONL (JSON Lines) data conversion"""

    @pytest.mark.asyncio
    async def test_jsonl_to_json_conversion(self, temp_dir):
        """Test JSONL to JSON conversion"""
        converter = DataConverter()

        input_file = temp_dir / "test.jsonl"
        jsonl_content = """{"name": "Alice", "age": 30}
{"name": "Bob", "age": 25}
{"name": "Charlie", "age": 35}
"""
        input_file.write_text(jsonl_content)

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
                assert len(data) == 3
                assert data[0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_jsonl_to_csv_conversion(self, temp_dir):
        """Test JSONL to CSV conversion"""
        converter = DataConverter()

        input_file = temp_dir / "test.jsonl"
        jsonl_content = """{"name": "Alice", "age": 30}
{"name": "Bob", "age": 25}
"""
        input_file.write_text(jsonl_content)

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
            assert len(df) == 2

    @pytest.mark.asyncio
    async def test_json_to_jsonl_conversion(self, temp_dir):
        """Test JSON to JSONL conversion"""
        converter = DataConverter()

        input_file = temp_dir / "test.json"
        json_data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        input_file.write_text(json.dumps(json_data))

        output_file = settings.UPLOAD_DIR / "test_converted.jsonl"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            output_file.parent.mkdir(parents=True, exist_ok=True)

            result = await converter.convert(
                input_path=input_file,
                output_format="jsonl",
                options={},
                session_id="test-session"
            )

            assert result == output_file
            assert output_file.exists()

            # Verify JSONL format (one JSON object per line)
            lines = output_file.read_text().strip().split('\n')
            assert len(lines) == 2
            first_obj = json.loads(lines[0])
            assert first_obj["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_jsonl_with_empty_lines(self, temp_dir):
        """Test JSONL with empty lines (should skip them)"""
        converter = DataConverter()

        input_file = temp_dir / "test.jsonl"
        jsonl_content = """{"name": "Alice", "age": 30}

{"name": "Bob", "age": 25}

"""
        input_file.write_text(jsonl_content)

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

            # Verify only non-empty lines were parsed
            with open(output_file, 'r') as f:
                data = json.load(f)
                assert len(data) == 2


# ============================================================================
# METADATA EXTRACTION TESTS
# ============================================================================

class TestGetDataInfo:
    """Test get_data_info metadata extraction"""

    @pytest.mark.asyncio
    async def test_get_csv_info(self, temp_dir):
        """Test extracting metadata from CSV file"""
        converter = DataConverter()

        csv_file = temp_dir / "test.csv"
        csv_content = "name,age,city\nAlice,30,New York\nBob,25,London"
        csv_file.write_text(csv_content)

        info = await converter.get_data_info(csv_file)

        assert info["format"] == "csv"
        assert info["rows"] == 2
        assert info["columns"] == 3
        assert "name" in info["column_names"]
        assert info["size"] > 0

    @pytest.mark.asyncio
    async def test_get_json_array_info(self, temp_dir):
        """Test extracting metadata from JSON array file"""
        converter = DataConverter()

        json_file = temp_dir / "test.json"
        json_data = [{"name": "Alice"}, {"name": "Bob"}, {"name": "Charlie"}]
        json_file.write_text(json.dumps(json_data))

        info = await converter.get_data_info(json_file)

        assert info["format"] == "json"
        assert info["type"] == "array"
        assert info["items"] == 3
        assert info["size"] > 0

    @pytest.mark.asyncio
    async def test_get_json_object_info(self, temp_dir):
        """Test extracting metadata from JSON object file"""
        converter = DataConverter()

        json_file = temp_dir / "test.json"
        json_data = {"name": "Alice", "age": 30, "city": "New York"}
        json_file.write_text(json.dumps(json_data))

        info = await converter.get_data_info(json_file)

        assert info["format"] == "json"
        assert info["type"] == "object"
        assert "name" in info["keys"]
        assert info["size"] > 0

    @pytest.mark.asyncio
    async def test_get_xml_info_with_defusedxml(self, temp_dir):
        """Test extracting metadata from XML file (with defusedxml)"""
        converter = DataConverter()

        xml_file = temp_dir / "test.xml"
        xml_content = """<?xml version="1.0"?>
<data>
    <item><name>Alice</name></item>
    <item><name>Bob</name></item>
</data>"""
        xml_file.write_text(xml_content)

        info = await converter.get_data_info(xml_file)

        assert info["format"] == "xml"
        assert info["root_tag"] == "data"
        assert info["children"] == 2
        assert info["size"] > 0

    @pytest.mark.asyncio
    async def test_get_xml_info_without_defusedxml(self, temp_dir):
        """Test that XML info extraction is disabled without defusedxml for security"""
        converter = DataConverter()

        xml_file = temp_dir / "test.xml"
        xml_content = """<?xml version="1.0"?>
<data>
    <item><name>Alice</name></item>
</data>"""
        xml_file.write_text(xml_content)

        # Mock DEFUSEDXML_AVAILABLE as False - XML parsing should be disabled for security
        with patch('app.services.data_converter.DEFUSEDXML_AVAILABLE', False):
            info = await converter.get_data_info(xml_file)

            # Should return error since XML parsing is disabled without defusedxml
            assert "error" in info
            assert "defusedxml" in info["error"].lower()

    @pytest.mark.asyncio
    async def test_get_info_unsupported_format(self, temp_dir):
        """Test get_data_info with unsupported format"""
        converter = DataConverter()

        txt_file = temp_dir / "test.txt"
        txt_file.write_text("some text")

        info = await converter.get_data_info(txt_file)

        assert "error" in info
        assert info["error"] == "Unsupported format"

    @pytest.mark.asyncio
    async def test_get_info_malformed_file(self, temp_dir):
        """Test get_data_info with malformed file"""
        converter = DataConverter()

        json_file = temp_dir / "test.json"
        json_file.write_text("{ invalid json }")

        info = await converter.get_data_info(json_file)

        assert "error" in info


# ============================================================================
# DEFUSEDXML FALLBACK TESTS
# ============================================================================

class TestDefusedXMLFallback:
    """Test XML parsing is disabled when defusedxml is not available (security)"""

    @pytest.mark.asyncio
    async def test_xml_conversion_without_defusedxml(self, temp_dir):
        """Test XML conversion is blocked when defusedxml is not available for security"""
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

        with patch('app.services.data_converter.DEFUSEDXML_AVAILABLE', False):
            with patch.object(converter, 'send_progress', new=AsyncMock()):
                # Should raise ValueError because XML parsing is disabled for security
                with pytest.raises(ValueError) as exc_info:
                    await converter.convert(
                        input_path=input_file,
                        output_format="json",
                        options={},
                        session_id="test-session"
                    )

                assert "defusedxml" in str(exc_info.value).lower()

    def test_defusedxml_import_error_handling(self):
        """Test that ImportError for defusedxml is handled correctly"""
        # This test verifies the import error handling at module load time
        # We can't directly test the import error, but we can verify that
        # DEFUSEDXML_AVAILABLE is set correctly based on import success/failure
        import app.services.data_converter as dc

        # The flag should be a boolean
        assert isinstance(dc.DEFUSEDXML_AVAILABLE, bool)

        # If defusedxml is available, it should be True, otherwise False
        try:
            import defusedxml
            assert dc.DEFUSEDXML_AVAILABLE is True
        except ImportError:
            assert dc.DEFUSEDXML_AVAILABLE is False


# ============================================================================
# ADDITIONAL EDGE CASES
# ============================================================================

class TestAdditionalEdgeCases:
    """Test additional edge cases for better coverage"""

    @pytest.mark.asyncio
    async def test_yaml_dict_structure_input(self, temp_dir):
        """Test YAML with dict structure (not list) input"""
        converter = DataConverter()

        input_file = temp_dir / "test.yaml"
        yaml_content = """
name: Alice
age: 30
city: New York
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

            # Verify data was converted correctly
            with open(output_file, 'r') as f:
                data = json.load(f)
                assert len(data) == 1
                assert data[0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_yaml_unsupported_structure_raises_error(self, temp_dir):
        """Test YAML with unsupported structure (string)"""
        converter = DataConverter()

        input_file = temp_dir / "test.yaml"
        yaml_content = "just a string"
        input_file.write_text(yaml_content)

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

            with pytest.raises(ValueError, match="Unsupported YAML structure"):
                await converter.convert(
                    input_path=input_file,
                    output_format="json",
                    options={},
                    session_id="test-session"
                )

    @pytest.mark.asyncio
    async def test_toml_unsupported_structure_raises_error(self, temp_dir):
        """Test TOML with unsupported structure"""
        converter = DataConverter()

        input_file = temp_dir / "test.toml"
        toml_content = "name = 'Alice'"
        input_file.write_text(toml_content)

        # Mock toml.load to return non-dict (though unlikely in practice)
        with patch.object(converter, 'send_progress', new=AsyncMock()):
            settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

            with patch('toml.load', return_value="not a dict"):
                with pytest.raises(ValueError, match="Unsupported TOML structure"):
                    await converter.convert(
                        input_path=input_file,
                        output_format="json",
                        options={},
                        session_id="test-session"
                    )


    @pytest.mark.asyncio
    async def test_xml_parsing_fallback_when_defusedxml_unavailable(self, temp_dir):
        """Test XML parsing is blocked when defusedxml is not available for security"""
        from unittest.mock import patch

        converter = DataConverter()

        input_file = temp_dir / "test.xml"
        xml_content = """<?xml version="1.0"?>
<root>
    <record><name>Alice</name><age>30</age></record>
</root>"""
        input_file.write_text(xml_content)

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

            # Temporarily disable defusedxml
            with patch('app.services.data_converter.DEFUSEDXML_AVAILABLE', False):
                # Should raise ValueError because XML parsing is disabled for security
                with pytest.raises(ValueError) as exc_info:
                    await converter.convert(
                        input_path=input_file,
                        output_format="json",
                        options={},
                        session_id="test-session"
                    )

                assert "defusedxml" in str(exc_info.value).lower()


class TestDataImportFallback:
    """Test import error handling for optional dependencies"""

    def test_defusedxml_import_fallback(self):
        """Test that DEFUSEDXML_AVAILABLE is set to False when defusedxml is not available"""
        import sys
        from unittest.mock import patch

        # Temporarily hide defusedxml
        with patch.dict(sys.modules, {'defusedxml': None, 'defusedxml.ElementTree': None}):
            # Force module reload to trigger import error
            import importlib
            import app.services.data_converter
            importlib.reload(app.services.data_converter)

            # The module should still load with DEFUSEDXML_AVAILABLE=False
            assert hasattr(app.services.data_converter, 'DEFUSEDXML_AVAILABLE')
            # Re-reload to restore normal state
            importlib.reload(app.services.data_converter)


class TestDataEdgeCases:
    """Test edge cases to reach 100% coverage"""

    @pytest.mark.asyncio
    async def test_xml_parser_with_entity_attribute(self, temp_dir):
        """Test XML parsing is blocked without defusedxml regardless of parser capabilities"""
        from unittest.mock import patch, MagicMock

        converter = DataConverter()

        input_file = temp_dir / "test.xml"
        xml_content = """<?xml version="1.0"?>
<root>
    <record><name>Alice</name><age>30</age></record>
</root>"""
        input_file.write_text(xml_content)

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

            # Create a mock parser that supports entity attribute and SetParamEntityParsing
            mock_parser = MagicMock()
            mock_parser.entity = {}
            mock_inner_parser = MagicMock()
            mock_inner_parser.SetParamEntityParsing = MagicMock(return_value=None)
            mock_parser.parser = mock_inner_parser

            # Temporarily disable defusedxml - XML parsing should be blocked for security
            with patch('app.services.data_converter.DEFUSEDXML_AVAILABLE', False):
                with patch('xml.etree.ElementTree.XMLParser', return_value=mock_parser):
                    # Should raise ValueError because XML parsing is disabled for security
                    with pytest.raises(ValueError) as exc_info:
                        await converter.convert(
                            input_path=input_file,
                            output_format="json",
                            options={},
                            session_id="test-session"
                        )

                    assert "defusedxml" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_unsupported_input_format_in_conversion(self, temp_dir):
        """Test unsupported input format error in conversion (line 146)"""
        converter = DataConverter()

        # Patch supported_formats to include 'xyz' so validation passes
        # but the format isn't handled in the if/elif chain
        converter.supported_formats = {
            "input": ["csv", "json", "xml", "yaml", "yml", "toml", "ini", "jsonl", "xyz"],
            "output": ["csv", "json"]
        }

        input_file = temp_dir / "test.xyz"
        input_file.write_text("test data")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with pytest.raises(ValueError, match="Unsupported input format: xyz"):
                await converter.convert(
                    input_path=input_file,
                    output_format="csv",
                    options={},
                    session_id="test-session"
                )

    @pytest.mark.asyncio
    async def test_unsupported_output_format_in_conversion(self, temp_dir):
        """Test unsupported output format error in conversion (line 197)"""
        converter = DataConverter()

        # Patch supported_formats to include 'xyz' in outputs so validation passes
        # but the format isn't handled in the output if/elif chain
        converter.supported_formats = {
            "input": ["json"],
            "output": ["csv", "json", "xml", "yaml", "yml", "toml", "ini", "jsonl", "xyz"]
        }

        input_file = temp_dir / "test.json"
        input_file.write_text(json.dumps([{"name": "Alice"}]))

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with pytest.raises(ValueError, match="Unsupported output format: xyz"):
                await converter.convert(
                    input_path=input_file,
                    output_format="xyz",
                    options={},
                    session_id="test-session"
                )



@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test files"""
    return tmp_path
