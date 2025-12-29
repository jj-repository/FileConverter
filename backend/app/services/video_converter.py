from pathlib import Path
from typing import Dict, Any, Optional
import subprocess
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.services.base_converter import BaseConverter
from app.config import settings


class VideoConverter(BaseConverter):
    """Video conversion service using FFmpeg"""

    def __init__(self, websocket_manager=None):
        super().__init__(websocket_manager)
        self.supported_formats = {
            "input": list(settings.VIDEO_FORMATS),
            "output": list(settings.VIDEO_FORMATS),
        }
        self.executor = ThreadPoolExecutor(max_workers=2)

    async def get_supported_formats(self) -> Dict[str, list]:
        """Get supported video formats"""
        return self.supported_formats

    async def get_video_duration(self, file_path: Path) -> float:
        """Get video duration in seconds using ffprobe"""
        try:
            cmd = [
                settings.FFPROBE_PATH,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(file_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=settings.SUBPROCESS_TIMEOUT)
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
            return 0.0
        except Exception as e:
            print(f"Error getting video duration: {e}")
            return 0.0

    def parse_ffmpeg_progress(self, line: str, total_duration: float) -> Optional[float]:
        """Parse FFmpeg progress from output line"""
        # Look for time=HH:MM:SS.MS pattern
        time_match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
        if time_match and total_duration > 0:
            hours = int(time_match.group(1))
            minutes = int(time_match.group(2))
            seconds = float(time_match.group(3))
            current_time = hours * 3600 + minutes * 60 + seconds
            progress = (current_time / total_duration) * 100
            return min(progress, 99.9)  # Cap at 99.9% until complete
        return None

    async def convert(
        self,
        input_path: Path,
        output_format: str,
        options: Dict[str, Any],
        session_id: str
    ) -> Path:
        """
        Convert video to target format

        Args:
            input_path: Path to input video
            output_format: Target format (mp4, avi, mov, mkv, webm, flv, wmv)
            options: Conversion options
                - codec: str (libx264, libx265, libvpx-vp9, etc.)
                - resolution: str (e.g., "720p", "1080p", "original")
                - bitrate: str (e.g., "2M", "5M")

        Returns:
            Path to converted video
        """
        await self.send_progress(session_id, 0, "converting", "Starting video conversion")

        # Validate format
        input_format = input_path.suffix.lower().lstrip('.')
        if not self.validate_format(input_format, output_format, self.supported_formats):
            raise ValueError(f"Unsupported conversion: {input_format} to {output_format}")

        # Get video duration for progress tracking
        total_duration = await self.get_video_duration(input_path)

        # Generate output path
        output_path = settings.UPLOAD_DIR / f"{input_path.stem}_converted.{output_format}"

        await self.send_progress(session_id, 5, "converting", "Preparing conversion")

        # Build FFmpeg command - validate all user inputs
        codec = options.get('codec', 'libx264')
        if codec not in settings.ALLOWED_VIDEO_CODECS:
            raise ValueError(f"Invalid codec: {codec}. Allowed: {settings.ALLOWED_VIDEO_CODECS}")

        bitrate = options.get('bitrate', '2M')
        if bitrate not in settings.ALLOWED_BITRATES:
            raise ValueError(f"Invalid bitrate: {bitrate}. Allowed: {settings.ALLOWED_BITRATES}")

        resolution = options.get('resolution', 'original')
        if resolution not in settings.ALLOWED_RESOLUTIONS:
            raise ValueError(f"Invalid resolution: {resolution}. Allowed: {settings.ALLOWED_RESOLUTIONS}")

        cmd = [
            settings.FFMPEG_PATH,
            "-i", str(input_path),
            "-y",  # Overwrite output file
            "-progress", "pipe:1",  # Output progress to stdout
            "-loglevel", "error",
        ]

        # Add codec
        cmd.extend(["-c:v", codec])
        cmd.extend(["-c:a", "aac"])  # Audio codec

        # Add bitrate
        cmd.extend(["-b:v", bitrate])

        # Add resolution if not original
        if resolution != "original":
            if resolution == "480p":
                cmd.extend(["-vf", "scale=-2:480"])
            elif resolution == "720p":
                cmd.extend(["-vf", "scale=-2:720"])
            elif resolution == "1080p":
                cmd.extend(["-vf", "scale=-2:1080"])
            elif resolution == "4k":
                cmd.extend(["-vf", "scale=-2:2160"])

        # Add output file
        cmd.append(str(output_path))

        await self.send_progress(session_id, 10, "converting", "Starting FFmpeg conversion")

        # Run FFmpeg conversion with progress tracking
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            last_progress = 10

            try:
                # Read output line by line with timeout
                async with asyncio.timeout(settings.SUBPROCESS_TIMEOUT):
                    async for line in process.stdout:
                        line_str = line.decode('utf-8', errors='ignore')

                        # Parse progress
                        progress = self.parse_ffmpeg_progress(line_str, total_duration)
                        if progress is not None and progress > last_progress:
                            # Map 0-100% to 10-95% to leave room for finalization
                            mapped_progress = 10 + (progress * 0.85)
                            last_progress = mapped_progress
                            await self.send_progress(
                                session_id,
                                mapped_progress,
                                "converting",
                                f"Converting video: {int(progress)}%"
                            )

                    # Wait for process to complete
                    await process.wait()
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise Exception(f"Conversion timed out after {settings.SUBPROCESS_TIMEOUT} seconds")

            if process.returncode != 0:
                stderr = await process.stderr.read()
                error_msg = stderr.decode('utf-8', errors='ignore')
                raise Exception(f"FFmpeg conversion failed: {error_msg[:200]}")

            await self.send_progress(session_id, 98, "converting", "Finalizing video")

            # Verify output file exists
            if not output_path.exists():
                raise Exception("Output file was not created")

            await self.send_progress(session_id, 100, "completed", "Video conversion completed")

            return output_path

        except Exception as e:
            await self.send_progress(session_id, 0, "failed", f"Conversion failed: {str(e)}")
            raise

    async def get_video_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract video metadata using ffprobe"""
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
                import json
                data = json.loads(result.stdout)

                # Extract video stream info
                video_stream = next(
                    (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
                    {}
                )

                # Extract audio stream info
                audio_stream = next(
                    (s for s in data.get("streams", []) if s.get("codec_type") == "audio"),
                    {}
                )

                return {
                    "duration": float(data.get("format", {}).get("duration", 0)),
                    "size": int(data.get("format", {}).get("size", 0)),
                    "format": data.get("format", {}).get("format_name", ""),
                    "width": video_stream.get("width", 0),
                    "height": video_stream.get("height", 0),
                    "video_codec": video_stream.get("codec_name", ""),
                    "audio_codec": audio_stream.get("codec_name", ""),
                    "fps": self._parse_fps(video_stream.get("r_frame_rate", "0/1")),
                    "bitrate": int(data.get("format", {}).get("bit_rate", 0)),
                }
            else:
                return {"error": "Failed to probe video"}
        except Exception as e:
            return {"error": str(e)}

    def _parse_fps(self, fps_str: str) -> float:
        """Parse FPS from fraction string like '30000/1001'"""
        try:
            if "/" in fps_str:
                num, denom = fps_str.split("/")
                return float(num) / float(denom) if float(denom) != 0 else 0
            return float(fps_str)
        except:
            return 0.0
