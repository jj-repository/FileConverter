import asyncio
import json
import uuid
from pathlib import Path
from typing import Any, Dict

import pandas as pd

# Use defusedxml for parsing XML (XXE protection) - REQUIRED for security
try:
    from defusedxml import ElementTree as DefusedET

    DEFUSEDXML_AVAILABLE = True
except ImportError:
    DEFUSEDXML_AVAILABLE = False
    import warnings

    warnings.warn(
        "defusedxml is not installed. XML parsing will be disabled for security. "
        "Install with: pip install defusedxml",
        RuntimeWarning,
    )

# Use standard ElementTree for creating XML only (defusedxml doesn't support Element creation)
import configparser
import xml.etree.ElementTree as ET

import toml
import yaml

from app.config import settings
from app.services.base_converter import BaseConverter


class DataConverter(BaseConverter):
    """Data conversion service for CSV, JSON, XML, YAML, TOML, INI, JSONL"""

    def __init__(self, websocket_manager=None):
        super().__init__(websocket_manager)
        self.supported_formats = {
            "input": list(settings.DATA_FORMATS),
            "output": list(settings.DATA_FORMATS),
        }

    async def get_supported_formats(self) -> Dict[str, list]:
        """Get supported data formats"""
        return self.supported_formats

    async def convert(
        self,
        input_path: Path,
        output_format: str,
        options: Dict[str, Any],
        session_id: str,
    ) -> Path:
        """
        Convert data file to target format

        Args:
            input_path: Path to input data file
            output_format: Target format (csv, json, xml, yaml, yml, toml, ini, jsonl)
            options: Conversion options
                - encoding: str (default: utf-8)
                - delimiter: str (for CSV, default: ,)
                - pretty: bool (for JSON/YAML, default: True)

        Returns:
            Path to converted data file
        """
        await self.send_progress(session_id, 0, "converting", "Starting data conversion")

        # Validate format
        input_format = input_path.suffix.lower().lstrip(".")
        if not self.validate_format(input_format, output_format, self.supported_formats):
            raise ValueError(f"Unsupported conversion: {input_format} to {output_format}")

        # Generate output path
        output_path = settings.UPLOAD_DIR / f"{input_path.stem}_{uuid.uuid4().hex[:8]}.{output_format}"

        # Get options
        encoding = options.get("encoding", "utf-8")
        delimiter = options.get("delimiter", ",")
        pretty = options.get("pretty", True)

        await self.send_progress(session_id, 20, "converting", "Reading input file")

        try:
            # Read input file based on format (blocking I/O offloaded to thread)
            if input_format == "xml":
                df = await self._xml_to_dataframe(input_path, encoding)
            else:
                df = await asyncio.to_thread(
                    self._sync_read_dataframe, input_path, input_format, encoding, delimiter
                )

            await self.send_progress(session_id, 60, "converting", "Converting data format")

            # Write output file based on format (blocking I/O offloaded to thread)
            if output_format == "xml":
                await self._dataframe_to_xml(df, output_path, encoding)
            else:
                await asyncio.to_thread(
                    self._sync_write_dataframe,
                    df,
                    output_path,
                    output_format,
                    encoding,
                    delimiter,
                    pretty,
                )

            await self.send_progress(session_id, 100, "completed", "Data conversion completed")

            return output_path

        except Exception as e:
            await self.send_progress(session_id, 0, "failed", f"Conversion failed: {str(e)}")
            raise

    @staticmethod
    def _sync_read_dataframe(
        input_path: Path, input_format: str, encoding: str, delimiter: str
    ) -> pd.DataFrame:
        """Blocking read; called via asyncio.to_thread."""
        if input_format == "csv":
            try:
                return pd.read_csv(input_path, encoding=encoding, delimiter=delimiter)
            except pd.errors.ParserError:
                return pd.read_csv(
                    input_path,
                    encoding=encoding,
                    delimiter=delimiter,
                    on_bad_lines="skip",
                )
        if input_format == "json":
            with open(input_path, "r", encoding=encoding) as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
                    raise ValueError(
                        f"Invalid JSON file: {e.msg} at line {e.lineno}, column {e.colno}"
                    )
            if isinstance(data, list):
                if len(data) == 0:
                    return pd.DataFrame(columns=["value"])
                return pd.DataFrame(data)
            if isinstance(data, dict):
                if all(isinstance(v, list) for v in data.values()):
                    return pd.DataFrame(data)
                return pd.DataFrame([data])
            raise ValueError("Unsupported JSON structure")
        if input_format in ["yaml", "yml"]:
            with open(input_path, "r", encoding=encoding) as f:
                data = yaml.safe_load(f)
            if isinstance(data, list):
                return pd.DataFrame(data)
            if isinstance(data, dict):
                return pd.DataFrame([data])
            raise ValueError("Unsupported YAML structure")
        if input_format == "toml":
            data = toml.load(input_path)
            if isinstance(data, dict):
                return pd.DataFrame([data])
            raise ValueError("Unsupported TOML structure")
        if input_format == "ini":
            config = configparser.ConfigParser()
            config.read(input_path, encoding=encoding)
            rows = []
            for section in config.sections():
                row = {"section": section}
                row.update(dict(config.items(section)))
                rows.append(row)
            return pd.DataFrame(rows)
        if input_format == "jsonl":
            # SECURITY: Limit line length and row count to prevent memory exhaustion
            MAX_LINE_LENGTH = 10 * 1024 * 1024  # 10MB per line
            MAX_ROWS = 1_000_000
            rows = []
            with open(input_path, "r", encoding=encoding) as f:
                for line_num, line in enumerate(f, 1):
                    if line_num > MAX_ROWS:
                        raise ValueError(
                            f"JSONL file exceeds maximum row limit ({MAX_ROWS:,} rows)"
                        )
                    if len(line) > MAX_LINE_LENGTH:
                        raise ValueError(
                            f"Line {line_num} exceeds maximum length "
                            f"({MAX_LINE_LENGTH // 1024 // 1024}MB)"
                        )
                    if line.strip():
                        rows.append(json.loads(line))
            return pd.DataFrame(rows)
        raise ValueError(f"Unsupported input format: {input_format}")

    @staticmethod
    def _sync_write_dataframe(
        df: pd.DataFrame,
        output_path: Path,
        output_format: str,
        encoding: str,
        delimiter: str,
        pretty: bool,
    ) -> None:
        """Blocking write; called via asyncio.to_thread."""
        if output_format == "csv":
            df.to_csv(output_path, index=False, encoding=encoding, sep=delimiter)
            return
        if output_format == "json":
            json_data = df.to_dict("records")
            with open(output_path, "w", encoding=encoding) as f:
                if pretty:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(json_data, f, ensure_ascii=False)
            return
        if output_format in ["yaml", "yml"]:
            data = df.to_dict("records")
            with open(output_path, "w", encoding=encoding) as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            return
        if output_format == "toml":
            if len(df) == 0:
                raise ValueError("Cannot convert empty DataFrame to TOML")
            data = df.iloc[0].to_dict()
            with open(output_path, "w", encoding=encoding) as f:
                toml.dump(data, f)
            return
        if output_format == "ini":
            config = configparser.ConfigParser()
            for record in df.to_dict("records"):
                section = str(record.get("section", "DEFAULT"))
                if section not in config.sections() and section != "DEFAULT":
                    config.add_section(section)
                for col, val in record.items():
                    if col != "section":
                        config.set(section, col, str(val))
            with open(output_path, "w", encoding=encoding) as f:
                config.write(f)
            return
        if output_format == "jsonl":
            with open(output_path, "w", encoding=encoding) as f:
                for record in df.to_dict("records"):
                    json.dump(record, f, ensure_ascii=False)
                    f.write("\n")
            return
        raise ValueError(f"Unsupported output format: {output_format}")

    async def _xml_to_dataframe(self, xml_path: Path, encoding: str) -> pd.DataFrame:
        """Convert simple XML to DataFrame with XXE protection"""
        # SECURITY: Require defusedxml for XML parsing to prevent XXE attacks
        if not DEFUSEDXML_AVAILABLE:
            raise ValueError(
                "XML parsing is disabled for security reasons. "
                "Please install defusedxml: pip install defusedxml"
            )
        tree = DefusedET.parse(xml_path)

        root = tree.getroot()

        # Assume structure: <root><item><field>value</field></item></root>
        data = []
        for item in root:
            row = {}
            for child in item:
                row[child.tag] = child.text
            data.append(row)

        return pd.DataFrame(data)

    async def _dataframe_to_xml(self, df: pd.DataFrame, output_path: Path, encoding: str):
        """Convert DataFrame to simple XML"""
        root = ET.Element("data")

        for record in df.to_dict("records"):
            item = ET.SubElement(root, "item")
            for col, value in record.items():
                field = ET.SubElement(item, str(col))
                field.text = str(value)

        tree = ET.ElementTree(root)
        tree.write(output_path, encoding=encoding, xml_declaration=True)

    async def get_data_info(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from data file"""
        try:
            input_format = file_path.suffix.lower().lstrip(".")

            if input_format == "csv":
                df = pd.read_csv(file_path)
                return {
                    "format": "csv",
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": df.columns.tolist(),
                    "size": file_path.stat().st_size,
                }
            elif input_format == "json":
                with open(file_path, "r") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError as e:
                        return {"error": f"Invalid JSON: {e.msg} at line {e.lineno}"}
                    if isinstance(data, list):
                        return {
                            "format": "json",
                            "type": "array",
                            "items": len(data),
                            "size": file_path.stat().st_size,
                        }
                    else:
                        return {
                            "format": "json",
                            "type": "object",
                            "keys": list(data.keys()) if isinstance(data, dict) else None,
                            "size": file_path.stat().st_size,
                        }
            elif input_format == "xml":
                # SECURITY: Require defusedxml for XML parsing
                if not DEFUSEDXML_AVAILABLE:
                    return {"error": "XML parsing disabled - defusedxml not installed"}
                tree = DefusedET.parse(file_path)
                root = tree.getroot()
                return {
                    "format": "xml",
                    "root_tag": root.tag,
                    "children": len(list(root)),
                    "size": file_path.stat().st_size,
                }
            else:
                return {"error": "Unsupported format"}

        except Exception as e:
            return {"error": str(e)}
