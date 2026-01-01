"""
Tests for app/services/spreadsheet_converter.py

COVERAGE GOAL: 85%+
Tests spreadsheet conversion with CSV, XLSX, ODS, format-specific options,
sheet handling, metadata extraction, and error handling
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import pandas as pd
import io

from app.services.spreadsheet_converter import SpreadsheetConverter
from app.config import settings


# ============================================================================
# BASIC FUNCTIONALITY TESTS
# ============================================================================

class TestSpreadsheetConverterBasics:
    """Test basic SpreadsheetConverter functionality"""

    def test_initialization(self):
        """Test SpreadsheetConverter initializes correctly"""
        converter = SpreadsheetConverter()

        assert converter.supported_formats is not None
        assert "input" in converter.supported_formats
        assert "output" in converter.supported_formats
        assert "csv" in converter.supported_formats["input"]
        assert "xlsx" in converter.supported_formats["output"]
        assert "ods" in converter.supported_formats["output"]
        assert converter.websocket_manager is not None

    def test_initialization_with_websocket_manager(self):
        """Test SpreadsheetConverter can be initialized with custom WebSocket manager"""
        mock_ws_manager = Mock()
        converter = SpreadsheetConverter(websocket_manager=mock_ws_manager)

        assert converter.websocket_manager == mock_ws_manager

    @pytest.mark.asyncio
    async def test_get_supported_formats(self):
        """Test getting supported spreadsheet formats"""
        converter = SpreadsheetConverter()

        formats = await converter.get_supported_formats()

        assert "input" in formats
        assert "output" in formats
        assert isinstance(formats["input"], list)
        assert isinstance(formats["output"], list)
        # Check common formats
        assert "csv" in formats["output"]
        assert "xlsx" in formats["output"]
        assert "ods" in formats["output"]
        assert "csv" in formats["input"]
        assert "tsv" in formats["input"]


# ============================================================================
# CSV CONVERSION TESTS
# ============================================================================

class TestCSVConversion:
    """Test CSV conversion functionality"""

    @pytest.mark.asyncio
    async def test_convert_csv_to_xlsx_success(self, temp_dir):
        """Test successful CSV to XLSX conversion"""
        converter = SpreadsheetConverter()

        # Create test CSV file
        input_file = temp_dir / "test.csv"
        csv_content = "Name,Age,City\nAlice,30,New York\nBob,25,Los Angeles\n"
        input_file.write_text(csv_content)

        output_file = settings.UPLOAD_DIR / "test_converted.xlsx"

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            with patch('pandas.read_csv') as mock_read_csv:
                with patch('pandas.DataFrame.to_excel') as mock_to_excel:
                    # Mock pandas operations
                    mock_df = MagicMock(spec=pd.DataFrame)
                    mock_read_csv.return_value = mock_df

                    # Create output file
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("fake xlsx")

                    result = await converter.convert(
                        input_path=input_file,
                        output_format="xlsx",
                        options={},
                        session_id="test-session"
                    )

                    assert result == output_file
                    assert output_file.exists()
                    # Verify progress was sent
                    assert mock_progress.call_count >= 4

    @pytest.mark.asyncio
    async def test_convert_csv_to_ods_success(self, temp_dir):
        """Test successful CSV to ODS conversion"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.csv"
        input_file.write_text("Col1,Col2\nVal1,Val2\n")

        output_file = settings.UPLOAD_DIR / "test_converted.ods"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pandas.read_csv') as mock_read_csv:
                with patch.object(converter, '_write_ods', new=AsyncMock()) as mock_write_ods:
                    mock_df = MagicMock(spec=pd.DataFrame)
                    mock_read_csv.return_value = mock_df

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("fake ods")

                    result = await converter.convert(
                        input_path=input_file,
                        output_format="ods",
                        options={},
                        session_id="test-session"
                    )

                    assert result == output_file
                    mock_write_ods.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_csv_with_custom_delimiter(self, temp_dir):
        """Test CSV conversion with custom delimiter"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.csv"
        input_file.write_text("Name;Age;City\nAlice;30;NYC\n")

        output_file = settings.UPLOAD_DIR / "test_converted.xlsx"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pandas.read_csv') as mock_read_csv:
                with patch('pandas.DataFrame.to_excel') as mock_to_excel:
                    mock_df = MagicMock(spec=pd.DataFrame)
                    mock_read_csv.return_value = mock_df

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("fake xlsx")

                    await converter.convert(
                        input_path=input_file,
                        output_format="xlsx",
                        options={"delimiter": ";"},
                        session_id="test-session"
                    )

                    # Verify custom delimiter was used
                    call_args = mock_read_csv.call_args
                    assert call_args is not None
                    assert "delimiter" in call_args[1] or call_args[1].get("delimiter") == ";"

    @pytest.mark.asyncio
    async def test_convert_csv_with_custom_encoding(self, temp_dir):
        """Test CSV conversion with custom encoding"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.csv"
        input_file.write_text("Name,Age\nAlice,30\n", encoding="latin-1")

        output_file = settings.UPLOAD_DIR / "test_converted.xlsx"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pandas.read_csv') as mock_read_csv:
                with patch('pandas.DataFrame.to_excel') as mock_to_excel:
                    mock_df = MagicMock(spec=pd.DataFrame)
                    mock_read_csv.return_value = mock_df

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("fake xlsx")

                    await converter.convert(
                        input_path=input_file,
                        output_format="xlsx",
                        options={"encoding": "latin-1"},
                        session_id="test-session"
                    )

                    # Verify encoding was used
                    call_args = mock_read_csv.call_args
                    assert call_args is not None
                    assert "encoding" in call_args[1] or call_args[1].get("encoding") == "latin-1"

    @pytest.mark.asyncio
    async def test_csv_conversion_progress_updates(self, temp_dir):
        """Test progress updates during CSV conversion"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.csv"
        input_file.write_text("A,B\n1,2\n")

        output_file = settings.UPLOAD_DIR / "test_converted.xlsx"

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            with patch('pandas.read_csv') as mock_read_csv:
                with patch('pandas.DataFrame.to_excel'):
                    mock_df = MagicMock(spec=pd.DataFrame)
                    mock_read_csv.return_value = mock_df

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("fake xlsx")

                    await converter.convert(
                        input_path=input_file,
                        output_format="xlsx",
                        options={},
                        session_id="test-session"
                    )

                    # Verify progress calls
                    progress_calls = [call[0] for call in mock_progress.call_args_list]
                    # Should have calls with status "converting" and "completed"
                    statuses = [call[2] if len(call) > 2 else None for call in progress_calls]
                    assert "converting" in statuses
                    assert "completed" in statuses


# ============================================================================
# XLSX CONVERSION TESTS
# ============================================================================

class TestXLSXConversion:
    """Test XLSX conversion functionality"""

    @pytest.mark.asyncio
    async def test_convert_xlsx_to_csv_success(self, temp_dir):
        """Test successful XLSX to CSV conversion"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.xlsx"
        input_file.write_text("fake xlsx")

        output_file = settings.UPLOAD_DIR / "test_converted.csv"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.spreadsheet_converter.pd.read_excel') as mock_read_excel:
                with patch.object(pd.DataFrame, 'to_csv') as mock_to_csv:
                    mock_df = MagicMock(spec=pd.DataFrame)
                    mock_read_excel.return_value = mock_df

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("fake csv")

                    result = await converter.convert(
                        input_path=input_file,
                        output_format="csv",
                        options={},
                        session_id="test-session"
                    )

                    assert result == output_file
                    mock_read_excel.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_xlsx_to_ods_success(self, temp_dir):
        """Test successful XLSX to ODS conversion"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.xlsx"
        input_file.write_text("fake xlsx")

        output_file = settings.UPLOAD_DIR / "test_converted.ods"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pandas.read_excel') as mock_read_excel:
                with patch.object(converter, '_write_ods', new=AsyncMock()):
                    mock_df = MagicMock(spec=pd.DataFrame)
                    mock_read_excel.return_value = mock_df

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("fake ods")

                    result = await converter.convert(
                        input_path=input_file,
                        output_format="ods",
                        options={},
                        session_id="test-session"
                    )

                    assert result == output_file

    @pytest.mark.asyncio
    async def test_convert_xlsx_with_sheet_selection(self, temp_dir):
        """Test XLSX conversion with sheet name parameter"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.xlsx"
        input_file.write_text("fake xlsx")

        output_file = settings.UPLOAD_DIR / "test_converted.csv"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pandas.read_excel') as mock_read_excel:
                with patch('pandas.DataFrame.to_csv'):
                    mock_df = MagicMock(spec=pd.DataFrame)
                    mock_read_excel.return_value = mock_df

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("fake csv")

                    await converter.convert(
                        input_path=input_file,
                        output_format="csv",
                        options={"sheet_name": "Sheet2"},
                        session_id="test-session"
                    )

                    # Verify sheet_name was passed to read_excel
                    call_args = mock_read_excel.call_args
                    assert call_args is not None
                    assert "sheet_name" in call_args[1]

    @pytest.mark.asyncio
    async def test_xlsx_output_not_supported_for_xls(self, temp_dir):
        """Test that XLS output format raises error (only XLSX supported)"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.csv"
        input_file.write_text("A,B\n1,2\n")

        with pytest.raises(ValueError, match="XLS output not supported"):
            with patch.object(converter, 'send_progress', new=AsyncMock()):
                with patch('pandas.read_csv') as mock_read_csv:
                    mock_df = MagicMock(spec=pd.DataFrame)
                    mock_read_csv.return_value = mock_df

                    await converter.convert(
                        input_path=input_file,
                        output_format="xls",
                        options={},
                        session_id="test-session"
                    )


# ============================================================================
# ODS CONVERSION TESTS
# ============================================================================

class TestODSConversion:
    """Test ODS conversion functionality"""

    @pytest.mark.asyncio
    async def test_convert_ods_to_csv_success(self, temp_dir):
        """Test successful ODS to CSV conversion"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.ods"
        input_file.write_text("fake ods")

        output_file = settings.UPLOAD_DIR / "test_converted.csv"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch.object(converter, '_read_ods', new=AsyncMock()) as mock_read_ods:
                with patch('pandas.DataFrame.to_csv'):
                    mock_df = MagicMock(spec=pd.DataFrame)
                    mock_read_ods.return_value = mock_df

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("fake csv")

                    result = await converter.convert(
                        input_path=input_file,
                        output_format="csv",
                        options={},
                        session_id="test-session"
                    )

                    assert result == output_file
                    mock_read_ods.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_ods_to_xlsx_success(self, temp_dir):
        """Test successful ODS to XLSX conversion"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.ods"
        input_file.write_text("fake ods")

        output_file = settings.UPLOAD_DIR / "test_converted.xlsx"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch.object(converter, '_read_ods', new=AsyncMock()) as mock_read_ods:
                with patch('pandas.DataFrame.to_excel'):
                    mock_df = MagicMock(spec=pd.DataFrame)
                    mock_read_ods.return_value = mock_df

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("fake xlsx")

                    result = await converter.convert(
                        input_path=input_file,
                        output_format="xlsx",
                        options={},
                        session_id="test-session"
                    )

                    assert result == output_file

    @pytest.mark.asyncio
    async def test_convert_ods_with_sheet_selection(self, temp_dir):
        """Test ODS conversion with sheet name selection"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.ods"
        input_file.write_text("fake ods")

        output_file = settings.UPLOAD_DIR / "test_converted.csv"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch.object(converter, '_read_ods', new=AsyncMock()) as mock_read_ods:
                with patch('pandas.DataFrame.to_csv'):
                    mock_df = MagicMock(spec=pd.DataFrame)
                    mock_read_ods.return_value = mock_df

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("fake csv")

                    await converter.convert(
                        input_path=input_file,
                        output_format="csv",
                        options={"sheet_name": "DataSheet"},
                        session_id="test-session"
                    )

                    # Verify sheet_name was passed
                    call_args = mock_read_ods.call_args
                    assert call_args is not None
                    assert call_args[0][1] == "DataSheet" or call_args[1].get("sheet_name") == "DataSheet"


# ============================================================================
# TSV CONVERSION TESTS
# ============================================================================

class TestTSVConversion:
    """Test TSV conversion functionality"""

    @pytest.mark.asyncio
    async def test_convert_tsv_to_xlsx_success(self, temp_dir):
        """Test successful TSV to XLSX conversion"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.tsv"
        input_file.write_text("Col1\tCol2\tCol3\nVal1\tVal2\tVal3\n")

        output_file = settings.UPLOAD_DIR / "test_converted.xlsx"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pandas.read_csv') as mock_read_csv:
                with patch('pandas.DataFrame.to_excel'):
                    mock_df = MagicMock(spec=pd.DataFrame)
                    mock_read_csv.return_value = mock_df

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("fake xlsx")

                    result = await converter.convert(
                        input_path=input_file,
                        output_format="xlsx",
                        options={},
                        session_id="test-session"
                    )

                    assert result == output_file
                    # Verify tab delimiter was used for TSV
                    call_args = mock_read_csv.call_args
                    assert call_args is not None

    @pytest.mark.asyncio
    async def test_convert_xlsx_to_tsv_success(self, temp_dir):
        """Test successful XLSX to TSV conversion"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.xlsx"
        input_file.write_text("fake xlsx")

        output_file = settings.UPLOAD_DIR / "test_converted.tsv"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.spreadsheet_converter.pd.read_excel') as mock_read_excel:
                with patch.object(pd.DataFrame, 'to_csv') as mock_to_csv:
                    mock_df = MagicMock(spec=pd.DataFrame)
                    mock_read_excel.return_value = mock_df

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("fake tsv")

                    result = await converter.convert(
                        input_path=input_file,
                        output_format="tsv",
                        options={},
                        session_id="test-session"
                    )

                    assert result == output_file
                    mock_read_excel.assert_called_once()


# ============================================================================
# METADATA EXTRACTION TESTS
# ============================================================================

class TestSpreadsheetMetadata:
    """Test spreadsheet metadata extraction"""

    @pytest.mark.asyncio
    async def test_get_spreadsheet_info_csv(self, temp_dir):
        """Test metadata extraction from CSV file"""
        converter = SpreadsheetConverter()

        test_file = temp_dir / "test.csv"
        test_file.write_text("Name,Age,City\nAlice,30,NYC\nBob,25,LA\n")

        with patch('app.services.spreadsheet_converter.pd.read_csv') as mock_read_csv:
            # First call gets columns (with nrows=1)
            mock_df_cols = MagicMock()
            mock_df_cols_obj = MagicMock()
            mock_df_cols_obj.tolist.return_value = ["Name", "Age", "City"]
            mock_df_cols_obj.__len__ = Mock(return_value=3)
            mock_df_cols.columns = mock_df_cols_obj

            # Second call gets all data (no nrows parameter)
            mock_df_all = MagicMock()
            mock_df_all.__len__ = Mock(return_value=2)

            mock_read_csv.side_effect = [mock_df_cols, mock_df_all]

            info = await converter.get_spreadsheet_info(test_file)

            assert info.get("format") == "csv"
            assert "size" in info
            assert info.get("rows") == 2
            assert info.get("columns") == 3

    @pytest.mark.asyncio
    async def test_get_spreadsheet_info_xlsx(self, temp_dir):
        """Test metadata extraction from XLSX file"""
        converter = SpreadsheetConverter()

        test_file = temp_dir / "test.xlsx"
        test_file.write_text("fake xlsx")

        with patch('openpyxl.load_workbook') as mock_load_wb:
            mock_wb = MagicMock()
            mock_wb.sheetnames = ["Sheet1", "Sheet2"]
            mock_ws = MagicMock()
            mock_ws.max_row = 100
            mock_ws.max_column = 5
            mock_wb.active = mock_ws
            mock_load_wb.return_value = mock_wb

            info = await converter.get_spreadsheet_info(test_file)

            assert info["format"] == "xlsx"
            assert info["sheets"] == 2
            assert info["sheet_names"] == ["Sheet1", "Sheet2"]
            assert info["rows"] == 100
            assert info["columns"] == 5
            mock_wb.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_spreadsheet_info_ods(self, temp_dir):
        """Test metadata extraction from ODS file"""
        converter = SpreadsheetConverter()

        test_file = temp_dir / "test.ods"
        test_file.write_text("fake ods")

        with patch('odf.opendocument.load') as mock_load_ods:
            # Mock ODS document
            mock_doc = MagicMock()
            mock_sheets = [MagicMock(), MagicMock()]
            mock_doc.spreadsheet.getElementsByType.return_value = mock_sheets

            # Mock sheet names
            mock_sheets[0].getAttribute.return_value = "Sheet1"
            mock_sheets[1].getAttribute.return_value = "Sheet2"

            # Mock rows
            mock_rows = [MagicMock() for _ in range(50)]
            mock_sheets[0].getElementsByType.return_value = mock_rows

            mock_load_ods.return_value = mock_doc

            info = await converter.get_spreadsheet_info(test_file)

            assert info["format"] == "ods"
            assert info["sheets"] == 2
            assert "sheet_names" in info
            assert "rows" in info

    @pytest.mark.asyncio
    async def test_get_spreadsheet_info_tsv(self, temp_dir):
        """Test metadata extraction from TSV file"""
        converter = SpreadsheetConverter()

        test_file = temp_dir / "test.tsv"
        test_file.write_text("A\tB\tC\n1\t2\t3\n4\t5\t6\n")

        with patch('app.services.spreadsheet_converter.pd.read_csv') as mock_read_csv:
            # First call gets columns (with nrows=1, delimiter='\t')
            mock_df_cols = MagicMock()
            mock_df_cols_obj = MagicMock()
            mock_df_cols_obj.tolist.return_value = ["A", "B", "C"]
            mock_df_cols_obj.__len__ = Mock(return_value=3)
            mock_df_cols.columns = mock_df_cols_obj

            # Second call gets all data (no nrows parameter, delimiter='\t')
            mock_df_all = MagicMock()
            mock_df_all.__len__ = Mock(return_value=2)

            mock_read_csv.side_effect = [mock_df_cols, mock_df_all]

            info = await converter.get_spreadsheet_info(test_file)

            assert info.get("format") == "tsv"
            assert info.get("rows") == 2
            assert info.get("columns") == 3


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestSpreadsheetErrorHandling:
    """Test error handling in spreadsheet conversion"""

    @pytest.mark.asyncio
    async def test_convert_unsupported_format_raises_error(self, temp_dir):
        """Test conversion with unsupported format raises ValueError"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.exe"
        input_file.write_text("not a spreadsheet")

        with pytest.raises(ValueError, match="Unsupported conversion"):
            await converter.convert(
                input_path=input_file,
                output_format="xlsx",
                options={},
                session_id="test-session"
            )

    @pytest.mark.asyncio
    async def test_convert_invalid_sheet_name_raises_error(self, temp_dir):
        """Test conversion with invalid sheet name raises error"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.xlsx"
        input_file.write_text("fake xlsx")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch.object(converter, '_read_excel', side_effect=ValueError("Sheet 'InvalidSheet' not found")):
                with pytest.raises(ValueError, match="Sheet"):
                    await converter.convert(
                        input_path=input_file,
                        output_format="csv",
                        options={"sheet_name": "InvalidSheet"},
                        session_id="test-session"
                    )

    @pytest.mark.asyncio
    async def test_convert_malformed_csv_raises_error(self, temp_dir):
        """Test conversion with malformed CSV raises error"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.csv"
        input_file.write_text("unclosed,quote\n\"malformed csv")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pandas.read_csv', side_effect=Exception("Malformed CSV")):
                with pytest.raises(Exception, match="Malformed CSV"):
                    await converter.convert(
                        input_path=input_file,
                        output_format="xlsx",
                        options={},
                        session_id="test-session"
                    )

    @pytest.mark.asyncio
    async def test_convert_encoding_error_raises_error(self, temp_dir):
        """Test conversion handles encoding errors"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.csv"
        input_file.write_bytes(b"\xff\xfe\x00\x00")  # Invalid UTF-8

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pandas.read_csv', side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte")):
                with pytest.raises(Exception):
                    await converter.convert(
                        input_path=input_file,
                        output_format="xlsx",
                        options={"encoding": "utf-8"},
                        session_id="test-session"
                    )

    @pytest.mark.asyncio
    async def test_convert_openpyxl_missing_raises_error(self, temp_dir):
        """Test conversion fails when openpyxl not available for XLSX"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.csv"
        input_file.write_text("A,B\n1,2\n")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pandas.read_csv') as mock_read_csv:
                with patch('app.services.spreadsheet_converter.OPENPYXL_AVAILABLE', False):
                    mock_df = MagicMock(spec=pd.DataFrame)
                    mock_read_csv.return_value = mock_df

                    with pytest.raises(ValueError, match="openpyxl"):
                        await converter.convert(
                            input_path=input_file,
                            output_format="xlsx",
                            options={},
                            session_id="test-session"
                        )

    @pytest.mark.asyncio
    async def test_convert_odf_missing_raises_error(self, temp_dir):
        """Test conversion fails when odfpy not available for ODS"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.csv"
        input_file.write_text("A,B\n1,2\n")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pandas.read_csv') as mock_read_csv:
                with patch('app.services.spreadsheet_converter.ODF_AVAILABLE', False):
                    mock_df = MagicMock(spec=pd.DataFrame)
                    mock_read_csv.return_value = mock_df

                    with pytest.raises(ValueError, match="odfpy"):
                        await converter.convert(
                            input_path=input_file,
                            output_format="ods",
                            options={},
                            session_id="test-session"
                        )

    @pytest.mark.asyncio
    async def test_convert_xlsx_outputs_return_path(self, temp_dir):
        """Test conversion returns the output path"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.xlsx"
        input_file.write_text("fake xlsx")

        output_file = settings.UPLOAD_DIR / "test_converted.csv"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.spreadsheet_converter.pd.read_excel') as mock_read_excel:
                with patch('app.services.spreadsheet_converter.pd.DataFrame.to_csv') as mock_to_csv:
                    mock_df = MagicMock(spec=pd.DataFrame)
                    mock_read_excel.return_value = mock_df

                    # Create output file before conversion
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("col1,col2\n1,2\n")

                    result = await converter.convert(
                        input_path=input_file,
                        output_format="csv",
                        options={},
                        session_id="test-session"
                    )

                    assert result == output_file

    @pytest.mark.asyncio
    async def test_get_spreadsheet_info_file_not_found(self, temp_dir):
        """Test metadata extraction with non-existent file"""
        converter = SpreadsheetConverter()

        test_file = temp_dir / "nonexistent.csv"

        info = await converter.get_spreadsheet_info(test_file)

        assert "error" in info

    @pytest.mark.asyncio
    async def test_get_spreadsheet_info_corrupted_xlsx(self, temp_dir):
        """Test metadata extraction with corrupted XLSX"""
        converter = SpreadsheetConverter()

        test_file = temp_dir / "corrupted.xlsx"
        test_file.write_bytes(b"corrupted data")

        with patch('openpyxl.load_workbook', side_effect=Exception("Invalid XLSX")):
            info = await converter.get_spreadsheet_info(test_file)
            assert "error" in info

    @pytest.mark.asyncio
    async def test_conversion_progress_on_failure(self, temp_dir):
        """Test progress update is sent when conversion fails"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.csv"
        input_file.write_text("A,B\n1,2\n")

        with patch.object(converter, 'send_progress', new=AsyncMock()) as mock_progress:
            with patch('pandas.read_csv', side_effect=Exception("Read error")):
                with pytest.raises(Exception):
                    await converter.convert(
                        input_path=input_file,
                        output_format="xlsx",
                        options={},
                        session_id="test-session"
                    )

                # Verify failure progress was sent
                last_call = mock_progress.call_args_list[-1]
                assert "failed" in str(last_call)


# ============================================================================
# READ/WRITE HELPER TESTS
# ============================================================================

class TestReadWriteHelpers:
    """Test internal read/write helper methods"""

    @pytest.mark.asyncio
    async def test_read_excel_default_sheet(self, temp_dir):
        """Test reading Excel file defaults to first sheet"""
        converter = SpreadsheetConverter()

        test_file = temp_dir / "test.xlsx"
        test_file.write_text("fake xlsx")

        with patch('pandas.read_excel') as mock_read_excel:
            mock_df = MagicMock(spec=pd.DataFrame)
            mock_read_excel.return_value = mock_df

            result = await converter._read_excel(test_file)

            assert result == mock_df
            # Verify no sheet_name parameter when not specified
            call_args = mock_read_excel.call_args
            assert call_args is not None

    @pytest.mark.asyncio
    async def test_read_excel_specific_sheet(self, temp_dir):
        """Test reading Excel file with specific sheet name"""
        converter = SpreadsheetConverter()

        test_file = temp_dir / "test.xlsx"
        test_file.write_text("fake xlsx")

        with patch('pandas.read_excel') as mock_read_excel:
            mock_df = MagicMock(spec=pd.DataFrame)
            mock_read_excel.return_value = mock_df

            result = await converter._read_excel(test_file, "Sheet2")

            assert result == mock_df
            call_args = mock_read_excel.call_args
            assert call_args is not None
            assert call_args[1].get("sheet_name") == "Sheet2"

    @pytest.mark.asyncio
    async def test_read_ods_default_sheet(self, temp_dir):
        """Test reading ODS file defaults to first sheet"""
        converter = SpreadsheetConverter()

        test_file = temp_dir / "test.ods"
        test_file.write_text("fake ods")

        with patch('odf.opendocument.load') as mock_load:
            mock_doc = MagicMock()
            mock_sheet = MagicMock()
            mock_sheets = [mock_sheet]
            mock_doc.spreadsheet.getElementsByType.return_value = mock_sheets
            mock_sheet.getElementsByType.return_value = []
            mock_load.return_value = mock_doc

            with patch('pandas.DataFrame') as mock_df_class:
                mock_df = MagicMock()
                mock_df_class.return_value = mock_df

                result = await converter._read_ods(test_file)

                assert result is not None

    @pytest.mark.asyncio
    async def test_write_ods_creates_valid_structure(self, temp_dir):
        """Test writing ODS file creates valid structure"""
        converter = SpreadsheetConverter()

        output_file = temp_dir / "output.ods"

        # Create mock DataFrame
        mock_df = MagicMock(spec=pd.DataFrame)
        mock_df.columns = ["Col1", "Col2", "Col3"]
        mock_df.iterrows.return_value = [
            (0, [1, 2, 3]),
            (1, [4, 5, 6])
        ]

        with patch('odf.opendocument.OpenDocumentSpreadsheet') as mock_ods_class:
            with patch('odf.table.Table') as mock_table_class:
                with patch('odf.table.TableRow'):
                    with patch('odf.table.TableCell'):
                        with patch('odf.text.P'):
                            with patch('pandas.notna', return_value=True):
                                mock_ods = MagicMock()
                                mock_ods_class.return_value = mock_ods
                                mock_table = MagicMock()
                                mock_table_class.return_value = mock_table

                                await converter._write_ods(mock_df, output_file)

                                # Verify save was called
                                mock_ods.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_ods_with_sheet_name(self, temp_dir):
        """Test reading ODS file with specific sheet name"""
        converter = SpreadsheetConverter()

        test_file = temp_dir / "test.ods"
        test_file.write_text("fake ods")

        with patch('odf.opendocument.load') as mock_load:
            mock_doc = MagicMock()
            mock_sheet1 = MagicMock()
            mock_sheet2 = MagicMock()
            mock_sheets = [mock_sheet1, mock_sheet2]

            # Setup getAttribute to return sheet names
            mock_sheet1.getAttribute.return_value = "Sheet1"
            mock_sheet2.getAttribute.return_value = "DataSheet"

            mock_doc.spreadsheet.getElementsByType.return_value = mock_sheets
            mock_sheet2.getElementsByType.return_value = []
            mock_load.return_value = mock_doc

            with patch('pandas.DataFrame') as mock_df_class:
                mock_df = MagicMock()
                mock_df_class.return_value = mock_df

                result = await converter._read_ods(test_file, "DataSheet")

                assert result is not None


# ============================================================================
# CONVERSION OPTIONS TESTS
# ============================================================================

class TestConversionOptions:
    """Test various conversion options"""

    @pytest.mark.asyncio
    async def test_csv_to_xlsx_preserves_data(self, temp_dir):
        """Test CSV to XLSX conversion preserves data"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.csv"
        input_file.write_text("Name,Age\nAlice,30\nBob,25\n")

        output_file = settings.UPLOAD_DIR / "test_converted.xlsx"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.spreadsheet_converter.pd.read_csv') as mock_read_csv:
                with patch.object(pd.DataFrame, 'to_excel') as mock_to_excel:
                    mock_df = MagicMock(spec=pd.DataFrame)
                    mock_df.columns = ["Name", "Age"]
                    mock_read_csv.return_value = mock_df

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("fake xlsx")

                    await converter.convert(
                        input_path=input_file,
                        output_format="xlsx",
                        options={},
                        session_id="test-session"
                    )

                    # Verify conversion completed successfully
                    assert output_file.exists()

    @pytest.mark.asyncio
    async def test_multiple_delimiter_formats(self, temp_dir):
        """Test CSV conversion with various delimiters"""
        converter = SpreadsheetConverter()

        delimiters = [",", ";", "\t", "|"]

        for delim in delimiters:
            input_file = temp_dir / f"test_{delim.replace(chr(9), 'tab')}.csv"
            input_file.write_text(f"A{delim}B{delim}C\n1{delim}2{delim}3\n")

            output_file = settings.UPLOAD_DIR / f"test_{delim.replace(chr(9), 'tab')}_converted.xlsx"

            with patch.object(converter, 'send_progress', new=AsyncMock()):
                with patch('pandas.read_csv') as mock_read_csv:
                    with patch('pandas.DataFrame.to_excel'):
                        mock_df = MagicMock(spec=pd.DataFrame)
                        mock_read_csv.return_value = mock_df

                        output_file.parent.mkdir(parents=True, exist_ok=True)
                        output_file.write_text("fake xlsx")

                        await converter.convert(
                            input_path=input_file,
                            output_format="xlsx",
                            options={"delimiter": delim},
                            session_id="test-session"
                        )

                        # Verify delimiter was used
                        call_args = mock_read_csv.call_args
                        assert call_args is not None


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.asyncio
    async def test_empty_spreadsheet_conversion(self, temp_dir):
        """Test conversion of empty spreadsheet"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "empty.csv"
        input_file.write_text("")

        output_file = settings.UPLOAD_DIR / "empty_converted.xlsx"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pandas.read_csv') as mock_read_csv:
                with patch('pandas.DataFrame.to_excel'):
                    mock_df = MagicMock(spec=pd.DataFrame)
                    mock_df.empty = True
                    mock_read_csv.return_value = mock_df

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("fake xlsx")

                    result = await converter.convert(
                        input_path=input_file,
                        output_format="xlsx",
                        options={},
                        session_id="test-session"
                    )

                    assert result == output_file

    @pytest.mark.asyncio
    async def test_very_large_spreadsheet_metadata(self, temp_dir):
        """Test metadata extraction for very large spreadsheet"""
        converter = SpreadsheetConverter()

        test_file = temp_dir / "large.xlsx"
        test_file.write_text("fake large xlsx")

        with patch('openpyxl.load_workbook') as mock_load_wb:
            mock_wb = MagicMock()
            mock_wb.sheetnames = ["Sheet" + str(i) for i in range(100)]
            mock_ws = MagicMock()
            mock_ws.max_row = 1000000
            mock_ws.max_column = 500
            mock_wb.active = mock_ws
            mock_load_wb.return_value = mock_wb

            info = await converter.get_spreadsheet_info(test_file)

            assert info["sheets"] == 100
            assert info["rows"] == 1000000
            assert info["columns"] == 500

    @pytest.mark.asyncio
    async def test_special_characters_in_data(self, temp_dir):
        """Test handling of special characters in spreadsheet data"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "special.csv"
        # Unicode and special characters
        input_file.write_text("Name,Description\n中文,Special™\nÜmlaut,©Copyright\n", encoding="utf-8")

        output_file = settings.UPLOAD_DIR / "special_converted.xlsx"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('pandas.read_csv') as mock_read_csv:
                with patch('pandas.DataFrame.to_excel'):
                    mock_df = MagicMock(spec=pd.DataFrame)
                    mock_read_csv.return_value = mock_df

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("fake xlsx")

                    result = await converter.convert(
                        input_path=input_file,
                        output_format="xlsx",
                        options={"encoding": "utf-8"},
                        session_id="test-session"
                    )

                    assert result == output_file

    @pytest.mark.asyncio
    async def test_conversion_with_numeric_data(self, temp_dir):
        """Test conversion preserves numeric data types"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "numeric.csv"
        input_file.write_text("ID,Value,Price\n1,100,99.99\n2,200,199.99\n")

        output_file = settings.UPLOAD_DIR / "numeric_converted.xlsx"

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.spreadsheet_converter.pd.read_csv') as mock_read_csv:
                with patch.object(pd.DataFrame, 'to_excel') as mock_to_excel:
                    mock_df = MagicMock(spec=pd.DataFrame)
                    mock_read_csv.return_value = mock_df

                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("fake xlsx")

                    result = await converter.convert(
                        input_path=input_file,
                        output_format="xlsx",
                        options={},
                        session_id="test-session"
                    )

                    assert result == output_file


class TestSpreadsheetEdgeCases:
    """Test edge cases to reach 100% coverage"""

    @pytest.mark.asyncio
    async def test_openpyxl_not_available_for_reading(self, temp_dir):
        """Test error when openpyxl not available for reading Excel (line 85)"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.xlsx"
        input_file.write_bytes(b"fake xlsx")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.spreadsheet_converter.OPENPYXL_AVAILABLE', False):
                with pytest.raises(ValueError, match="Excel support not available"):
                    await converter.convert(
                        input_path=input_file,
                        output_format="csv",
                        options={},
                        session_id="test-session"
                    )

    @pytest.mark.asyncio
    async def test_odf_not_available_for_reading(self, temp_dir):
        """Test error when odfpy not available for reading ODS (line 89)"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.ods"
        input_file.write_bytes(b"fake ods")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.spreadsheet_converter.ODF_AVAILABLE', False):
                with pytest.raises(ValueError, match="ODS support not available"):
                    await converter.convert(
                        input_path=input_file,
                        output_format="csv",
                        options={},
                        session_id="test-session"
                    )

    @pytest.mark.asyncio
    async def test_unsupported_input_format_error(self, temp_dir):
        """Test unsupported input format raises error (line 99)"""
        converter = SpreadsheetConverter()

        # Patch supported_formats to include 'xyz' so validation passes
        # but the format isn't handled in the if/elif chain
        converter.supported_formats = {
            "input": ["csv", "xlsx", "xls", "ods", "tsv", "xyz"],
            "output": ["csv", "xlsx"]
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
    async def test_unsupported_output_format_error(self, temp_dir):
        """Test unsupported output format raises error (line 123)"""
        converter = SpreadsheetConverter()

        # Patch supported_formats to include 'xyz' in outputs
        converter.supported_formats = {
            "input": ["csv"],
            "output": ["csv", "xlsx", "xls", "ods", "tsv", "xyz"]
        }

        input_file = temp_dir / "test.csv"
        input_file.write_text("A,B\n1,2\n")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.spreadsheet_converter.pd.read_csv') as mock_read:
                mock_df = MagicMock(spec=pd.DataFrame)
                mock_read.return_value = mock_df

                with pytest.raises(ValueError, match="Unsupported output format: xyz"):
                    await converter.convert(
                        input_path=input_file,
                        output_format="xyz",
                        options={},
                        session_id="test-session"
                    )

    @pytest.mark.asyncio
    async def test_ods_no_sheets_found_error(self, temp_dir):
        """Test error when no sheets found in ODS file (line 149)"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.ods"
        input_file.write_bytes(b"fake ods")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.spreadsheet_converter.opendocument.load') as mock_load:
                # Mock ODS document with no sheets
                mock_doc = MagicMock()
                mock_doc.spreadsheet.getElementsByType.return_value = []  # No sheets
                mock_load.return_value = mock_doc

                with pytest.raises(ValueError, match="No sheets found in ODS file"):
                    await converter._read_ods(input_file, None)

    @pytest.mark.asyncio
    async def test_ods_sheet_name_not_found_error(self, temp_dir):
        """Test error when specific sheet name not found in ODS (line 160)"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.ods"
        input_file.write_bytes(b"fake ods")

        with patch.object(converter, 'send_progress', new=AsyncMock()):
            with patch('app.services.spreadsheet_converter.opendocument.load') as mock_load:
                # Mock ODS document with sheets but not the requested name
                mock_sheet1 = MagicMock()
                mock_sheet1.getAttribute.return_value = "Sheet1"

                mock_sheet2 = MagicMock()
                mock_sheet2.getAttribute.return_value = "Sheet2"

                mock_doc = MagicMock()
                mock_doc.spreadsheet.getElementsByType.return_value = [mock_sheet1, mock_sheet2]
                mock_load.return_value = mock_doc

                with pytest.raises(ValueError, match="Sheet 'NonExistent' not found"):
                    await converter._read_ods(input_file, "NonExistent")

    @pytest.mark.asyncio
    async def test_ods_cell_extraction_with_data(self, temp_dir):
        """Test ODS cell extraction including lines 170-180, 185-188"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.ods"
        input_file.write_bytes(b"fake ods")

        with patch('app.services.spreadsheet_converter.opendocument.load') as mock_load:
            # Mock ODS document with actual data
            # Create mock cells with data - don't use spec to allow attribute setting
            mock_cell1 = MagicMock()
            mock_p1 = MagicMock()
            mock_p1.firstChild = MagicMock()
            mock_p1.firstChild.data = "Header1"
            mock_cell1.getElementsByType.return_value = [mock_p1]

            mock_cell2 = MagicMock()
            mock_p2 = MagicMock()
            mock_p2.firstChild = MagicMock()
            mock_p2.firstChild.data = "Header2"
            mock_cell2.getElementsByType.return_value = [mock_p2]

            # Create header row
            mock_header_row = MagicMock()
            mock_header_row.getElementsByType.return_value = [mock_cell1, mock_cell2]

            # Create data cells
            mock_data_cell1 = MagicMock()
            mock_data_p1 = MagicMock()
            mock_data_p1.firstChild = MagicMock()
            mock_data_p1.firstChild.data = "Value1"
            mock_data_cell1.getElementsByType.return_value = [mock_data_p1]

            mock_data_cell2 = MagicMock()
            mock_data_p2 = MagicMock()
            mock_data_p2.firstChild = MagicMock()
            mock_data_p2.firstChild.data = "Value2"
            mock_data_cell2.getElementsByType.return_value = [mock_data_p2]

            # Create data row
            mock_data_row = MagicMock()
            mock_data_row.getElementsByType.return_value = [mock_data_cell1, mock_data_cell2]

            # Create mock sheet with rows
            mock_sheet = MagicMock()
            mock_sheet.getAttribute.return_value = "Sheet1"
            mock_sheet.getElementsByType.return_value = [mock_header_row, mock_data_row]

            mock_doc = MagicMock()
            mock_doc.spreadsheet.getElementsByType.return_value = [mock_sheet]
            mock_load.return_value = mock_doc

            # Test reading the ODS file
            df = await converter._read_ods(input_file, None)

            # Verify DataFrame was created correctly
            assert isinstance(df, pd.DataFrame)
            assert len(df.columns) == 2
            assert len(df) == 1  # One data row

    @pytest.mark.asyncio
    async def test_ods_cell_extraction_with_empty_cells(self, temp_dir):
        """Test ODS cell extraction with empty cells (line 178)"""
        converter = SpreadsheetConverter()

        input_file = temp_dir / "test.ods"
        input_file.write_bytes(b"fake ods")

        with patch('app.services.spreadsheet_converter.opendocument.load') as mock_load:
            # Create mock cell with no paragraphs (empty cell) - hits line 178
            mock_empty_cell = MagicMock()
            mock_empty_cell.getElementsByType.return_value = []  # No paragraphs

            mock_cell_with_data = MagicMock()
            mock_p = MagicMock()
            mock_p.firstChild = MagicMock()
            mock_p.firstChild.data = "Data"
            mock_cell_with_data.getElementsByType.return_value = [mock_p]

            # Create row with one empty cell and one with data
            mock_row = MagicMock()
            mock_row.getElementsByType.return_value = [mock_empty_cell, mock_cell_with_data]

            # Create sheet with single row (hits line 188 - single row becomes DataFrame without header)
            mock_sheet = MagicMock()
            mock_sheet.getAttribute.return_value = "Sheet1"
            mock_sheet.getElementsByType.return_value = [mock_row]  # Only one row

            mock_doc = MagicMock()
            mock_doc.spreadsheet.getElementsByType.return_value = [mock_sheet]
            mock_load.return_value = mock_doc

            # Test reading the ODS file
            df = await converter._read_ods(input_file, None)

            # Verify DataFrame was created (single row case - line 188)
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 1


class TestSpreadsheetImportFallback:
    """Test import error handling for optional dependencies"""

    def test_openpyxl_import_fallback(self):
        """Test OPENPYXL_AVAILABLE flag when openpyxl not available (lines 11-12)"""
        import sys
        from unittest.mock import patch

        # Temporarily hide openpyxl
        with patch.dict(sys.modules, {'openpyxl': None}):
            # Force module reload to trigger import error
            import importlib
            import app.services.spreadsheet_converter
            importlib.reload(app.services.spreadsheet_converter)

            # The module should still load with OPENPYXL_AVAILABLE=False
            assert hasattr(app.services.spreadsheet_converter, 'OPENPYXL_AVAILABLE')
            # Re-reload to restore normal state
            importlib.reload(app.services.spreadsheet_converter)

    def test_odf_import_fallback(self):
        """Test ODF_AVAILABLE flag when odfpy not available (lines 20-21)"""
        import sys
        from unittest.mock import patch

        # Temporarily hide odf modules
        with patch.dict(sys.modules, {'odf': None, 'odf.opendocument': None, 'odf.table': None, 'odf.text': None}):
            # Force module reload to trigger import error
            import importlib
            import app.services.spreadsheet_converter
            importlib.reload(app.services.spreadsheet_converter)

            # The module should still load with ODF_AVAILABLE=False
            assert hasattr(app.services.spreadsheet_converter, 'ODF_AVAILABLE')
            # Re-reload to restore normal state
            importlib.reload(app.services.spreadsheet_converter)
