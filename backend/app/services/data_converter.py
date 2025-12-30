from pathlib import Path
from typing import Dict, Any
import pandas as pd
import json
import xml.etree.ElementTree as ET
import csv
import asyncio

from app.services.base_converter import BaseConverter
from app.config import settings


class DataConverter(BaseConverter):
    """Data conversion service for CSV, JSON, XML"""

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
        session_id: str
    ) -> Path:
        """
        Convert data file to target format

        Args:
            input_path: Path to input data file
            output_format: Target format (csv, json, xml)
            options: Conversion options
                - encoding: str (default: utf-8)
                - delimiter: str (for CSV, default: ,)
                - pretty: bool (for JSON, default: True)

        Returns:
            Path to converted data file
        """
        await self.send_progress(session_id, 0, "converting", "Starting data conversion")

        # Validate format
        input_format = input_path.suffix.lower().lstrip('.')
        if not self.validate_format(input_format, output_format, self.supported_formats):
            raise ValueError(f"Unsupported conversion: {input_format} to {output_format}")

        # Generate output path
        output_path = settings.UPLOAD_DIR / f"{input_path.stem}_converted.{output_format}"

        # Get options
        encoding = options.get('encoding', 'utf-8')
        delimiter = options.get('delimiter', ',')
        pretty = options.get('pretty', True)

        await self.send_progress(session_id, 20, "converting", "Reading input file")

        try:
            # Read input file based on format
            if input_format == 'csv':
                df = pd.read_csv(input_path, encoding=encoding, delimiter=delimiter)
            elif input_format == 'json':
                with open(input_path, 'r', encoding=encoding) as f:
                    data = json.load(f)
                    # Try to convert to DataFrame
                    if isinstance(data, list):
                        df = pd.DataFrame(data)
                    elif isinstance(data, dict):
                        # Check if it's a dict of lists (column-oriented)
                        if all(isinstance(v, list) for v in data.values()):
                            df = pd.DataFrame(data)
                        else:
                            # Single row
                            df = pd.DataFrame([data])
                    else:
                        raise ValueError("Unsupported JSON structure")
            elif input_format == 'xml':
                # Parse XML (simple flat structure)
                df = await self._xml_to_dataframe(input_path, encoding)
            else:
                raise ValueError(f"Unsupported input format: {input_format}")

            await self.send_progress(session_id, 60, "converting", "Converting data format")

            # Write output file based on format
            if output_format == 'csv':
                df.to_csv(output_path, index=False, encoding=encoding, sep=delimiter)
            elif output_format == 'json':
                # Convert DataFrame to JSON
                json_data = df.to_dict('records')
                with open(output_path, 'w', encoding=encoding) as f:
                    if pretty:
                        json.dump(json_data, f, indent=2, ensure_ascii=False)
                    else:
                        json.dump(json_data, f, ensure_ascii=False)
            elif output_format == 'xml':
                # Convert DataFrame to XML
                await self._dataframe_to_xml(df, output_path, encoding)
            else:
                raise ValueError(f"Unsupported output format: {output_format}")

            await self.send_progress(session_id, 100, "completed", "Data conversion completed")

            return output_path

        except Exception as e:
            await self.send_progress(session_id, 0, "failed", f"Conversion failed: {str(e)}")
            raise

    async def _xml_to_dataframe(self, xml_path: Path, encoding: str) -> pd.DataFrame:
        """Convert simple XML to DataFrame"""
        tree = ET.parse(xml_path)
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
        root = ET.Element('data')

        for _, row in df.iterrows():
            item = ET.SubElement(root, 'item')
            for col in df.columns:
                field = ET.SubElement(item, str(col))
                field.text = str(row[col])

        tree = ET.ElementTree(root)
        tree.write(output_path, encoding=encoding, xml_declaration=True)

    async def get_data_info(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from data file"""
        try:
            input_format = file_path.suffix.lower().lstrip('.')

            if input_format == 'csv':
                df = pd.read_csv(file_path, nrows=5)
                return {
                    "format": "csv",
                    "rows": len(pd.read_csv(file_path)),
                    "columns": len(df.columns),
                    "column_names": df.columns.tolist(),
                    "size": file_path.stat().st_size,
                }
            elif input_format == 'json':
                with open(file_path, 'r') as f:
                    data = json.load(f)
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
            elif input_format == 'xml':
                tree = ET.parse(file_path)
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
