"""
Font Converter Service
Handles conversion between font formats using fonttools
"""

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from fontTools.subset import Subsetter
from fontTools.ttLib import TTFont

from app.config import settings
from app.services.base_converter import BaseConverter

logger = logging.getLogger(__name__)


class FontConverter(BaseConverter):
    """Service for converting font formats"""

    def __init__(self, websocket_manager=None):
        super().__init__(websocket_manager)
        self.supported_formats = {
            "input": list(settings.FONT_FORMATS),
            "output": list(settings.FONT_FORMATS),
        }

    async def get_supported_formats(self) -> Dict[str, list]:
        """Get supported font formats"""
        return self.supported_formats

    async def convert(
        self,
        input_path: Path,
        output_format: str,
        options: Dict[str, Any],
        session_id: str,
    ) -> Path:
        """
        Convert font to target format

        Args:
            input_path: Path to input font file
            output_format: Target format (ttf, otf, woff, woff2)
            options: Conversion options
                - subset_text: str (optional, characters to include in subset)
                - optimize: bool (default: True, optimize tables)

        Returns:
            Path to converted font file
        """
        await self.send_progress(session_id, 10, "converting", "Starting font conversion")

        # Generate output filename
        output_filename = f"{input_path.stem}_{uuid.uuid4().hex}.{output_format}"
        output_path = settings.UPLOAD_DIR / output_filename

        _OPTIMIZE_DROP_TABLES = ["DSIG", "hdmx", "VDMX", "LTSH", "PCLT"]

        try:
            await self.send_progress(session_id, 30, "converting", "Loading font file")

            def _sync_font_convert():
                font = TTFont(str(input_path))
                subset_text = options.get("subset_text")
                if subset_text:
                    subsetter = Subsetter()
                    subsetter.populate(text=subset_text)
                    subsetter.subset(font)
                if options.get("optimize", True):
                    for table in _OPTIMIZE_DROP_TABLES:
                        if table in font:
                            del font[table]
                flavor = self._get_output_flavor(output_format)
                if flavor:
                    font.flavor = flavor
                font.save(str(output_path))
                return output_path

            await self.send_progress(
                session_id, 50, "converting", f"Converting to {output_format.upper()}"
            )

            result = await asyncio.to_thread(_sync_font_convert)

            await self.send_progress(session_id, 100, "converting", "Conversion complete")
            return result

        except Exception as e:
            logger.error(f"Font conversion failed: {e}")
            raise

    def _get_output_flavor(self, output_format: str) -> Optional[str]:
        """Get the fonttools flavor for the output format"""
        flavor_map = {
            "woff": "woff",
            "woff2": "woff2",
            "ttf": None,  # No flavor needed
            "otf": None,  # No flavor needed
        }
        return flavor_map.get(output_format)

    async def get_info(self, file_path: Path) -> Dict[str, Any]:
        """
        Get information about a font file

        Args:
            file_path: Path to the font file

        Returns:
            Dictionary with font information
        """
        info = {
            "filename": file_path.name,
            "size": file_path.stat().st_size,
            "format": file_path.suffix[1:].lower(),
        }

        def _sync_get_info() -> dict:
            font = None
            try:
                font = TTFont(str(file_path))
                result: dict = {}
                name_table = font.get("name")
                if name_table:
                    for record in name_table.names:
                        if record.nameID == 1:
                            try:
                                result["family_name"] = record.toUnicode()
                            except (UnicodeDecodeError, AttributeError) as e:
                                logger.debug(f"Failed to decode font family name: {e}")
                            break
                    for record in name_table.names:
                        if record.nameID == 2:
                            try:
                                result["style_name"] = record.toUnicode()
                            except (UnicodeDecodeError, AttributeError) as e:
                                logger.debug(f"Failed to decode font style name: {e}")
                            break
                    for record in name_table.names:
                        if record.nameID == 4:
                            try:
                                result["full_name"] = record.toUnicode()
                            except (UnicodeDecodeError, AttributeError) as e:
                                logger.debug(f"Failed to decode full font name: {e}")
                            break
                    for record in name_table.names:
                        if record.nameID == 5:
                            try:
                                result["version"] = record.toUnicode()
                            except (UnicodeDecodeError, AttributeError) as e:
                                logger.debug(f"Failed to decode font version: {e}")
                            break
                if "glyf" in font:
                    result["glyph_count"] = len(font["glyf"].glyphs)
                elif "CFF " in font:
                    result["glyph_count"] = (
                        font["CFF "].cff.topDictIndex[0].CharStrings.charStringsIndex.count
                    )
                if hasattr(font, "flavor"):
                    result["is_web_font"] = font.flavor in ["woff", "woff2"]
                    if font.flavor:
                        result["web_format"] = font.flavor
                return result
            except Exception as e:
                logger.warning(f"Could not extract font metadata: {e}")
                return {}
            finally:
                if font is not None:
                    font.close()

        info.update(await asyncio.to_thread(_sync_get_info))
        return info

    async def optimize_font(self, input_path: Path, session_id: str) -> Path:
        """
        Optimize a font by removing unnecessary data

        Args:
            input_path: Path to input font file
            session_id: Session ID for progress tracking

        Returns:
            Path to optimized font file
        """
        await self.send_progress(session_id, 10, "converting", "Starting font optimization")

        output_filename = f"{input_path.stem}_optimized{input_path.suffix}"
        output_path = settings.UPLOAD_DIR / output_filename

        tables_to_drop = ["DSIG", "hdmx", "VDMX", "LTSH", "PCLT"]

        def _sync_optimize() -> None:
            font = None
            try:
                font = TTFont(str(input_path))
                for table in tables_to_drop:
                    if table in font:
                        del font[table]
                font.save(str(output_path))
            except Exception as e:
                logger.error(f"Font optimization failed: {e}")
                raise
            finally:
                if font is not None:
                    font.close()

        await self.send_progress(session_id, 50, "converting", "Optimizing font tables")
        await asyncio.to_thread(_sync_optimize)
        await self.send_progress(session_id, 100, "converting", "Optimization complete")
        return output_path
