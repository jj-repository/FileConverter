from pathlib import Path
from typing import Dict, Any
import re

# Subtitle support
try:
    import pysubs2
    PYSUBS2_AVAILABLE = True
except ImportError:
    PYSUBS2_AVAILABLE = False

from app.services.base_converter import BaseConverter
from app.config import settings


class SubtitleConverter(BaseConverter):
    """Subtitle conversion service for SRT, VTT, ASS, SSA, SUB"""

    def __init__(self, websocket_manager=None):
        super().__init__(websocket_manager)
        self.supported_formats = {
            "input": list(settings.SUBTITLE_FORMATS),
            "output": list(settings.SUBTITLE_FORMATS),
        }

    async def get_supported_formats(self) -> Dict[str, list]:
        """Get supported subtitle formats"""
        return self.supported_formats

    async def convert(
        self,
        input_path: Path,
        output_format: str,
        options: Dict[str, Any],
        session_id: str
    ) -> Path:
        """
        Convert subtitle to target format

        Args:
            input_path: Path to input subtitle file
            output_format: Target format (srt, vtt, ass, ssa, sub)
            options: Conversion options
                - encoding: str (default: utf-8)
                - fps: float (for SUB format, default: 23.976)
                - keep_html_tags: bool (default: False)
                - keep_unknown_html_tags: bool (default: False)

        Returns:
            Path to converted subtitle file
        """
        await self.send_progress(session_id, 0, "converting", "Starting subtitle conversion")

        if not PYSUBS2_AVAILABLE:
            raise ValueError("Subtitle support not available. Install pysubs2.")

        # Validate format
        input_format = input_path.suffix.lower().lstrip('.')
        if not self.validate_format(input_format, output_format, self.supported_formats):
            raise ValueError(f"Unsupported conversion: {input_format} to {output_format}")

        # Generate output path
        output_path = settings.UPLOAD_DIR / f"{input_path.stem}_converted.{output_format}"

        # Get options
        encoding = options.get('encoding', 'utf-8')
        fps = options.get('fps', 23.976)
        keep_html_tags = options.get('keep_html_tags', False)
        keep_unknown_html_tags = options.get('keep_unknown_html_tags', False)

        await self.send_progress(session_id, 20, "converting", "Reading subtitle file")

        try:
            # Load subtitle file
            subs = pysubs2.load(str(input_path), encoding=encoding, fps=fps)

            await self.send_progress(session_id, 60, "converting", "Converting subtitle format")

            # Save in target format
            subs.save(
                str(output_path),
                encoding=encoding,
                format_=output_format,
                fps=fps,
                keep_html_tags=keep_html_tags,
                keep_unknown_html_tags=keep_unknown_html_tags
            )

            await self.send_progress(session_id, 100, "completed", "Subtitle conversion completed")

            return output_path

        except Exception as e:
            await self.send_progress(session_id, 0, "failed", f"Conversion failed: {str(e)}")
            raise

    async def adjust_timing(
        self,
        input_path: Path,
        offset_ms: int,
        session_id: str
    ) -> Path:
        """
        Adjust subtitle timing by offset (in milliseconds)

        Args:
            input_path: Path to input subtitle file
            offset_ms: Offset in milliseconds (positive = delay, negative = advance)
            session_id: Session ID for progress tracking

        Returns:
            Path to adjusted subtitle file
        """
        if not PYSUBS2_AVAILABLE:
            raise ValueError("Subtitle support not available. Install pysubs2.")

        await self.send_progress(session_id, 0, "converting", "Adjusting subtitle timing")

        input_format = input_path.suffix.lower().lstrip('.')
        output_path = settings.UPLOAD_DIR / f"{input_path.stem}_adjusted.{input_format}"

        try:
            # Load subtitle file
            subs = pysubs2.load(str(input_path))

            await self.send_progress(session_id, 50, "converting", "Applying time offset")

            # Shift all subtitles by offset
            subs.shift(ms=offset_ms)

            # Save adjusted subtitles
            subs.save(str(output_path))

            await self.send_progress(session_id, 100, "completed", "Timing adjustment completed")

            return output_path

        except Exception as e:
            await self.send_progress(session_id, 0, "failed", f"Adjustment failed: {str(e)}")
            raise

    async def get_subtitle_info(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from subtitle file"""
        try:
            if not PYSUBS2_AVAILABLE:
                return {"error": "pysubs2 not available"}

            input_format = file_path.suffix.lower().lstrip('.')

            # Load subtitle file
            subs = pysubs2.load(str(file_path))

            info = {
                "format": input_format,
                "size": file_path.stat().st_size,
                "subtitle_count": len(subs),
            }

            # Calculate duration
            if subs:
                first_line = subs[0]
                last_line = subs[-1]
                duration_ms = last_line.end - first_line.start
                duration_seconds = duration_ms / 1000.0

                info["first_subtitle_time"] = self._format_time(first_line.start)
                info["last_subtitle_time"] = self._format_time(last_line.end)
                info["duration_seconds"] = round(duration_seconds, 2)
                info["duration_formatted"] = self._format_duration(duration_seconds)

                # Get first few subtitle texts as preview
                preview_count = min(3, len(subs))
                info["preview"] = [
                    {
                        "start": self._format_time(sub.start),
                        "end": self._format_time(sub.end),
                        "text": sub.text
                    }
                    for sub in subs[:preview_count]
                ]

            return info

        except Exception as e:
            return {"error": str(e)}

    def _format_time(self, ms: int) -> str:
        """Format milliseconds to HH:MM:SS,mmm"""
        total_seconds = ms / 1000.0
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        milliseconds = int(ms % 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def _format_duration(self, seconds: float) -> str:
        """Format seconds to human-readable duration"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
