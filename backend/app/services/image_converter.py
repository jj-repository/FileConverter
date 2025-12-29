from pathlib import Path
from typing import Dict, Any
from PIL import Image
import asyncio

from app.services.base_converter import BaseConverter
from app.config import settings


class ImageConverter(BaseConverter):
    """Image conversion service using Pillow"""

    def __init__(self, websocket_manager=None):
        super().__init__(websocket_manager)
        self.supported_formats = {
            "input": list(settings.IMAGE_FORMATS),
            "output": list(settings.IMAGE_FORMATS),
        }

    async def get_supported_formats(self) -> Dict[str, list]:
        """Get supported image formats"""
        return self.supported_formats

    async def convert(
        self,
        input_path: Path,
        output_format: str,
        options: Dict[str, Any],
        session_id: str
    ) -> Path:
        """
        Convert image to target format

        Args:
            input_path: Path to input image
            output_format: Target format (png, jpg, webp, etc.)
            options: Conversion options
                - quality: int (1-100) for JPEG/WEBP quality
                - width: int (optional) for resize
                - height: int (optional) for resize

        Returns:
            Path to converted image
        """
        await self.send_progress(session_id, 0, "converting", "Starting image conversion")

        # Validate format
        input_format = input_path.suffix.lower().lstrip('.')
        if not self.validate_format(input_format, output_format, self.supported_formats):
            raise ValueError(f"Unsupported conversion: {input_format} to {output_format}")

        # Generate output path
        output_path = settings.UPLOAD_DIR / f"{input_path.stem}_converted.{output_format}"

        await self.send_progress(session_id, 20, "converting", "Loading image")

        # Open image
        with Image.open(input_path) as img:
            await self.send_progress(session_id, 40, "converting", "Processing image")

            # Handle transparency for formats that don't support it
            if output_format.lower() in ['jpg', 'jpeg'] and img.mode in ['RGBA', 'LA', 'P']:
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background

            # Resize if dimensions provided
            width = options.get('width')
            height = options.get('height')

            if width or height:
                await self.send_progress(session_id, 60, "converting", "Resizing image")

                original_width, original_height = img.size

                # Calculate dimensions maintaining aspect ratio
                if width and height:
                    new_size = (width, height)
                elif width:
                    ratio = width / original_width
                    new_size = (width, int(original_height * ratio))
                else:  # height only
                    ratio = height / original_height
                    new_size = (int(original_width * ratio), height)

                img = img.resize(new_size, Image.Resampling.LANCZOS)

            await self.send_progress(session_id, 80, "converting", "Saving converted image")

            # Prepare save options
            save_options = {}

            # Quality setting for JPEG and WEBP
            if output_format.lower() in ['jpg', 'jpeg', 'webp']:
                save_options['quality'] = options.get('quality', 95)

            # Optimize for all formats
            save_options['optimize'] = True

            # Convert to RGB for JPEG
            if output_format.lower() in ['jpg', 'jpeg'] and img.mode != 'RGB':
                img = img.convert('RGB')

            # Save image
            img.save(output_path, format=output_format.upper(), **save_options)

        await self.send_progress(session_id, 100, "completed", "Image conversion completed")

        return output_path

    async def get_image_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract image metadata"""
        try:
            with Image.open(file_path) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                    "size": file_path.stat().st_size,
                }
        except Exception as e:
            return {"error": str(e)}
