"""
Font Converter Service
Handles conversion between font formats using fonttools
"""
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options

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
        session_id: str
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

        input_format = input_path.suffix[1:].lower()

        # Generate output filename
        output_filename = f"{input_path.stem}_converted.{output_format}"
        output_path = settings.UPLOAD_DIR / output_filename

        try:
            await self.send_progress(session_id, 30, "converting", "Loading font file")

            # Load font
            font = TTFont(str(input_path))

            await self.send_progress(session_id, 50, "converting", f"Converting to {output_format.upper()}")

            # Apply subsetting if requested
            subset_text = options.get('subset_text')
            if subset_text:
                await self._apply_subset(font, subset_text, session_id)

            # Determine output flavor
            flavor = self._get_output_flavor(output_format)

            # Save font
            await self.send_progress(session_id, 80, "converting", "Saving converted font")

            # Set flavor for WOFF/WOFF2
            if flavor:
                font.flavor = flavor

            # Save with options
            optimize = options.get('optimize', True)
            font.save(str(output_path))

            font.close()

            await self.send_progress(session_id, 100, "converting", "Conversion complete")
            return output_path

        except Exception as e:
            logger.error(f"Font conversion failed: {e}")
            raise

    def _get_output_flavor(self, output_format: str) -> Optional[str]:
        """Get the fonttools flavor for the output format"""
        flavor_map = {
            'woff': 'woff',
            'woff2': 'woff2',
            'ttf': None,  # No flavor needed
            'otf': None,  # No flavor needed
        }
        return flavor_map.get(output_format)

    async def _apply_subset(self, font: TTFont, subset_text: str, session_id: str):
        """Apply subsetting to keep only specified characters"""
        await self.send_progress(session_id, 60, "converting", "Applying font subsetting")

        # Create subsetter
        subsetter = Subsetter()

        # Configure options
        options = Options()
        options.drop_tables = []  # Don't drop any tables by default

        # Add glyphs for the subset text
        subsetter.populate(text=subset_text)

        # Apply subset
        subsetter.subset(font)

    async def get_info(self, file_path: Path) -> Dict[str, Any]:
        """
        Get information about a font file

        Args:
            file_path: Path to the font file

        Returns:
            Dictionary with font information
        """
        info = {
            'filename': file_path.name,
            'size': file_path.stat().st_size,
            'format': file_path.suffix[1:].lower(),
        }

        try:
            font = TTFont(str(file_path))

            # Get font name
            name_table = font.get('name')
            if name_table:
                # Get font family name (ID 1)
                for record in name_table.names:
                    if record.nameID == 1:  # Font Family
                        try:
                            info['family_name'] = record.toUnicode()
                            break
                        except (UnicodeDecodeError, AttributeError) as e:
                            logger.debug(f"Failed to decode font family name: {str(e)}")
                            pass

                # Get font subfamily (style) name (ID 2)
                for record in name_table.names:
                    if record.nameID == 2:  # Subfamily
                        try:
                            info['style_name'] = record.toUnicode()
                            break
                        except (UnicodeDecodeError, AttributeError) as e:
                            logger.debug(f"Failed to decode font style name: {str(e)}")
                            pass

                # Get full font name (ID 4)
                for record in name_table.names:
                    if record.nameID == 4:  # Full name
                        try:
                            info['full_name'] = record.toUnicode()
                            break
                        except (UnicodeDecodeError, AttributeError) as e:
                            logger.debug(f"Failed to decode full font name: {str(e)}")
                            pass

                # Get version (ID 5)
                for record in name_table.names:
                    if record.nameID == 5:  # Version
                        try:
                            info['version'] = record.toUnicode()
                            break
                        except (UnicodeDecodeError, AttributeError) as e:
                            logger.debug(f"Failed to decode font version: {str(e)}")
                            pass

            # Get glyph count
            if 'glyf' in font:  # TrueType
                info['glyph_count'] = len(font['glyf'].glyphs)
            elif 'CFF ' in font:  # OpenType/CFF
                info['glyph_count'] = font['CFF '].cff.topDictIndex[0].CharStrings.charStringsIndex.count

            # Check if it's a web font
            if hasattr(font, 'flavor'):
                info['is_web_font'] = font.flavor in ['woff', 'woff2']
                if font.flavor:
                    info['web_format'] = font.flavor

            font.close()

        except Exception as e:
            logger.warning(f"Could not extract font metadata: {e}")

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

        try:
            font = TTFont(str(input_path))

            await self.send_progress(session_id, 50, "converting", "Optimizing font tables")

            # Remove unnecessary tables for web use
            tables_to_drop = [
                'DSIG',  # Digital signature
                'hdmx',  # Horizontal device metrics
                'VDMX',  # Vertical device metrics
                'LTSH',  # Linear threshold
                'PCLT',  # PCL 5 data
            ]

            for table in tables_to_drop:
                if table in font:
                    del font[table]

            await self.send_progress(session_id, 80, "converting", "Saving optimized font")

            font.save(str(output_path))
            font.close()

            await self.send_progress(session_id, 100, "converting", "Optimization complete")
            return output_path

        except Exception as e:
            logger.error(f"Font optimization failed: {e}")
            raise
