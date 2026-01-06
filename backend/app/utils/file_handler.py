from fastapi import UploadFile
from pathlib import Path
import aiofiles
import uuid
import logging
from typing import Dict, Any, Optional
from PIL import Image

from app.config import settings

logger = logging.getLogger(__name__)


def _parse_fps_safe(fps_str: str) -> float:
    """Safely parse FPS from fraction string like '30000/1001'"""
    try:
        fps_str = str(fps_str).strip()
        if "/" in fps_str:
            parts = fps_str.split("/")
            if len(parts) == 2:
                numerator = float(parts[0])
                denominator = float(parts[1])
                if denominator != 0:
                    return round(numerator / denominator, 2)
        return float(fps_str)
    except (ValueError, ZeroDivisionError, AttributeError):
        return 0.0


async def save_upload_file(upload_file: UploadFile, destination_dir: Path = settings.TEMP_DIR) -> Path:
    """Save uploaded file to destination directory with unique filename"""
    # Generate unique filename
    file_extension = Path(upload_file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = destination_dir / unique_filename

    # Save file asynchronously
    async with aiofiles.open(file_path, 'wb') as f:
        content = await upload_file.read()
        await f.write(content)

    return file_path


async def get_image_info(file_path: Path) -> Dict[str, Any]:
    """Extract metadata from image file"""
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


async def get_video_info(file_path: Path) -> Dict[str, Any]:
    """Extract metadata from video file using ffprobe"""
    import subprocess
    import json

    try:
        cmd = [
            settings.FFPROBE_PATH,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(file_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=settings.SUBPROCESS_TIMEOUT)
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse ffprobe output as JSON: {e}")
                return {"error": "Invalid ffprobe output"}

            # Extract video stream info
            video_stream = next(
                (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
                {}
            )

            return {
                "duration": float(data.get("format", {}).get("duration", 0)),
                "size": int(data.get("format", {}).get("size", 0)),
                "format": data.get("format", {}).get("format_name", ""),
                "width": video_stream.get("width", 0),
                "height": video_stream.get("height", 0),
                "codec": video_stream.get("codec_name", ""),
                "fps": _parse_fps_safe(video_stream.get("r_frame_rate", "0/1")),
            }
        else:
            return {"error": "Failed to probe video"}
    except Exception as e:
        return {"error": str(e)}


async def get_audio_info(file_path: Path) -> Dict[str, Any]:
    """Extract metadata from audio file using ffprobe"""
    import subprocess
    import json

    try:
        cmd = [
            settings.FFPROBE_PATH,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(file_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=settings.SUBPROCESS_TIMEOUT)
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse ffprobe audio output as JSON: {e}")
                return {"error": "Invalid ffprobe output"}

            # Extract audio stream info
            audio_stream = next(
                (s for s in data.get("streams", []) if s.get("codec_type") == "audio"),
                {}
            )

            return {
                "duration": float(data.get("format", {}).get("duration", 0)),
                "size": int(data.get("format", {}).get("size", 0)),
                "format": data.get("format", {}).get("format_name", ""),
                "codec": audio_stream.get("codec_name", ""),
                "sample_rate": int(audio_stream.get("sample_rate", 0)),
                "channels": audio_stream.get("channels", 0),
                "bitrate": int(data.get("format", {}).get("bit_rate", 0)),
            }
        else:
            return {"error": "Failed to probe audio"}
    except Exception as e:
        return {"error": str(e)}


async def get_document_info(file_path: Path) -> Dict[str, Any]:
    """Extract metadata from document file"""
    try:
        file_extension = file_path.suffix.lower().lstrip('.')

        info = {
            "size": file_path.stat().st_size,
            "format": file_extension,
        }

        if file_extension == "pdf":
            try:
                from pypdf import PdfReader
                reader = PdfReader(str(file_path))
                info["pages"] = len(reader.pages)
                if reader.metadata:
                    info["title"] = reader.metadata.get("/Title", "")
                    info["author"] = reader.metadata.get("/Author", "")
            except Exception as e:
                logger.warning(f"Failed to extract PDF metadata: {str(e)}")
                pass

        elif file_extension == "docx":
            try:
                from docx import Document
                doc = Document(str(file_path))
                info["paragraphs"] = len(doc.paragraphs)
            except Exception as e:
                logger.warning(f"Failed to extract DOCX metadata: {str(e)}")
                pass

        return info
    except Exception as e:
        return {"error": str(e)}


async def get_file_info(file_path: Path, file_type: str) -> Dict[str, Any]:
    """Get file metadata based on file type"""
    if file_type == "image":
        return await get_image_info(file_path)
    elif file_type == "video":
        return await get_video_info(file_path)
    elif file_type == "audio":
        return await get_audio_info(file_path)
    elif file_type == "document":
        return await get_document_info(file_path)
    else:
        return {"error": "Unknown file type"}


def cleanup_file(file_path: Path) -> None:
    """Delete a file if it exists"""
    try:
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {e}")
