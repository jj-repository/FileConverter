import asyncio
import json
import logging
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from app.config import settings
from app.services.base_converter import BaseConverter
from app.utils.subprocess_utils import parse_ffmpeg_progress as _parse_ffmpeg_progress
from app.utils.subprocess_utils import parse_fps as _parse_fps
from app.utils.subprocess_utils import subprocess_kwargs as _subprocess_kwargs

logger = logging.getLogger(__name__)


def _bitrate_to_kbps(bitrate: str) -> int:
    """Convert bitrate strings like '500k' or '5M' to integer kbps.

    Returns 0 for unrecognized formats so callers can skip rate-control flags.
    """
    if not bitrate:
        return 0
    s = bitrate.strip()
    try:
        if s.endswith("k") or s.endswith("K"):
            return int(s[:-1])
        if s.endswith("M"):
            return int(s[:-1]) * 1000
    except ValueError:
        return 0
    return 0


class VideoConverter(BaseConverter):
    """Video conversion service using FFmpeg"""

    def __init__(self, websocket_manager=None):
        super().__init__(websocket_manager)
        self.supported_formats = {
            "input": list(settings.VIDEO_FORMATS),
            "output": list(settings.VIDEO_FORMATS),
        }

    async def get_supported_formats(self) -> Dict[str, list]:
        """Get supported video formats"""
        return self.supported_formats

    async def get_video_duration(self, file_path: Path) -> float:
        """Get video duration in seconds using ffprobe"""
        try:
            cmd = [
                settings.FFPROBE_PATH,
                "-v",
                "error",
                "-protocol_whitelist",
                "file",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(file_path),
            ]

            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=settings.SUBPROCESS_TIMEOUT,
                **_subprocess_kwargs,
            )
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
            return 0.0
        except Exception as e:
            logger.error(f"Error getting video duration: {e}")
            return 0.0

    # Per-format conversion profile.
    #
    #   muxer:           value to pass via `-f` to disambiguate when an extension
    #                    is claimed by multiple muxers. ffmpeg's av_guess_format
    #                    falls back to alphabetical order of registered muxers,
    #                    so e.g. `.vob` is auto-picked as the `svcd` muxer (not
    #                    `vob`), which then rejects everything except mp1/mp2/mp3
    #                    + mpeg1video. Force the muxer here when that matters.
    #   video_codecs:    compatible video codecs for this container. The user's
    #                    requested codec is honored if it appears here; otherwise
    #                    we override with the first entry to keep the conversion
    #                    valid. None means any allowed codec works.
    #   audio_codec:     audio codec to emit. Forced (user can't override) so the
    #                    container's mux constraints aren't violated.
    _FORMAT_PROFILES = {
        "mp4":  {"muxer": None,     "video_codecs": ["libx264", "libx265", "mpeg4", "h264"], "audio_codec": "aac"},
        "mkv":  {"muxer": None,     "video_codecs": ["libx264", "libx265", "libvpx", "libvpx-vp9", "mpeg4"], "audio_codec": "aac"},
        "mov":  {"muxer": None,     "video_codecs": ["libx264", "libx265", "mpeg4", "h264"], "audio_codec": "aac"},
        "m4v":  {"muxer": None,     "video_codecs": ["libx264", "libx265", "mpeg4", "h264"], "audio_codec": "aac"},
        "avi":  {"muxer": None,     "video_codecs": ["libx264", "mpeg4", "h264"],            "audio_codec": "libmp3lame"},
        "flv":  {"muxer": None,     "video_codecs": ["libx264", "h264"],                     "audio_codec": "aac"},
        "wmv":  {"muxer": None,     "video_codecs": ["wmv2"],                                "audio_codec": "wmav2"},
        "webm": {"muxer": None,     "video_codecs": ["libvpx-vp9", "libvpx"],                "audio_codec": "libvorbis"},
        "3gp":  {"muxer": None,     "video_codecs": ["libx264", "h264", "mpeg4"],            "audio_codec": "aac"},
        "3g2":  {"muxer": None,     "video_codecs": ["libx264", "h264", "mpeg4"],            "audio_codec": "aac"},
        # AC-3 is the canonical audio for transport-stream containers (BD/ATSC).
        # Some Windows-native players refuse to demux AAC inside mpegts, so
        # ac3 is the safer default here even though aac is technically valid.
        "mts":  {"muxer": "mpegts", "video_codecs": ["libx264", "libx265", "h264"],          "audio_codec": "ac3"},
        "m2ts": {"muxer": "mpegts", "video_codecs": ["libx264", "libx265", "h264"],          "audio_codec": "ac3"},
        "ts":   {"muxer": "mpegts", "video_codecs": ["libx264", "libx265", "h264"],          "audio_codec": "ac3"},
        "vob":  {"muxer": "vob",    "video_codecs": ["mpeg2video"],                          "audio_codec": "mp2"},
        "ogv":  {"muxer": "ogg",    "video_codecs": ["libtheora"],                           "audio_codec": "libvorbis"},
    }

    # Audio-extraction profile: when the user picks an audio container as the
    # output, we drop the video stream and re-encode the first audio stream.
    _AUDIO_EXTRACT_PROFILES = {
        "mp3":  {"codec": "libmp3lame", "use_bitrate": True},
        "aac":  {"codec": "aac",        "use_bitrate": True},
        "m4a":  {"codec": "aac",        "use_bitrate": True},
        "ogg":  {"codec": "libvorbis",  "use_bitrate": True},
        "opus": {"codec": "libopus",    "use_bitrate": True},
        "flac": {"codec": "flac",       "use_bitrate": False},
        "wav":  {"codec": "pcm_s16le",  "use_bitrate": False},
        "wma":  {"codec": "wmav2",      "use_bitrate": True},
    }

    @classmethod
    def _get_profile(cls, output_format: str) -> Dict[str, Any]:
        return cls._FORMAT_PROFILES.get(
            output_format,
            {"muxer": None, "video_codecs": ["libx264"], "audio_codec": "aac"},
        )

    @classmethod
    def is_audio_extract_format(cls, output_format: str) -> bool:
        return output_format in cls._AUDIO_EXTRACT_PROFILES

    def get_video_codec_for_format(
        self, output_format: str, user_codec: Optional[str] = None
    ) -> str:
        """Get appropriate video codec for the output video format.

        Honors the user's choice when compatible with the container; otherwise
        falls back to the first compatible codec (silent override avoids the
        case where e.g. picking libx265 + .vob produces an unmuxable mismatch).
        """
        profile = self._get_profile(output_format)
        compatible = profile["video_codecs"]
        if user_codec and user_codec in compatible:
            return user_codec
        return compatible[0]

    def get_audio_codec_for_format(self, output_format: str) -> str:
        """Get appropriate audio codec for the output video format."""
        return self._get_profile(output_format)["audio_codec"]

    async def convert(
        self,
        input_path: Path,
        output_format: str,
        options: Dict[str, Any],
        session_id: str,
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
        if self.is_audio_extract_format(output_format):
            return await self._extract_audio(input_path, output_format, options, session_id)

        await self.send_progress(session_id, 0, "converting", "Starting video conversion")

        # Validate format
        input_format = input_path.suffix.lower().lstrip(".")
        if not self.validate_format(input_format, output_format, self.supported_formats):
            raise ValueError(f"Unsupported conversion: {input_format} to {output_format}")

        # Get video duration for progress tracking
        total_duration = await self.get_video_duration(input_path)

        # Generate output path
        output_path = settings.UPLOAD_DIR / f"{input_path.stem}_{uuid.uuid4().hex[:8]}.{output_format}"

        await self.send_progress(session_id, 5, "converting", "Preparing conversion")

        # Build FFmpeg command - validate all user inputs
        # Get appropriate codec for the output format (or use user-specified codec)
        codec = self.get_video_codec_for_format(output_format, options.get("codec"))
        if codec not in settings.ALLOWED_VIDEO_CODECS:
            raise ValueError(f"Invalid codec: {codec}. Allowed: {settings.ALLOWED_VIDEO_CODECS}")

        bitrate = options.get("bitrate", "2M")
        if bitrate not in settings.ALLOWED_BITRATES:
            raise ValueError(f"Invalid bitrate: {bitrate}. Allowed: {settings.ALLOWED_BITRATES}")

        resolution = options.get("resolution", "original")
        if resolution not in settings.ALLOWED_RESOLUTIONS:
            raise ValueError(
                f"Invalid resolution: {resolution}. Allowed: {settings.ALLOWED_RESOLUTIONS}"
            )

        cmd = [
            settings.FFMPEG_PATH,
            "-nostdin",
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(input_path),
            "-y",  # Overwrite output file
            "-progress",
            "pipe:1",  # Output progress to stdout
            "-loglevel",
            "error",
        ]

        # Explicit stream selection. Default ffmpeg "best stream" picking can
        # drop audio from MPEG program streams (vob/dvd) where the default
        # AC-3 / LPCM substream layout confuses the chooser. The trailing `?`
        # makes the audio map optional so silent inputs still convert.
        cmd.extend(["-map", "0:v:0", "-map", "0:a:0?"])

        # Add video codec
        cmd.extend(["-c:v", codec])

        # Add appropriate audio codec for the output format
        audio_codec = self.get_audio_codec_for_format(output_format)
        cmd.extend(["-c:a", audio_codec])

        # Add bitrate.
        # x264/x265 default rate control biases toward quality over hitting the
        # bitrate target -- with `-b:v` alone the encoder treats it as a soft
        # average and converted files at very different bitrates can end up
        # visually indistinguishable. Pinning -maxrate to the target and
        # -bufsize to 2x the target enforces a real ABR ceiling so the file
        # size tracks the user's selection.
        cmd.extend(["-b:v", bitrate])
        kbps = _bitrate_to_kbps(bitrate)
        if kbps and codec in ("libx264", "libx265", "h264"):
            cmd.extend(["-maxrate", bitrate, "-bufsize", f"{kbps * 2}k"])

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

        # Force output muxer for ambiguous extensions (e.g. .vob is claimed by
        # both the `vob` and `svcd` muxers; av_guess_format defaults to svcd
        # which only accepts mpeg1video + mp1/mp2/mp3 audio).
        muxer = self._get_profile(output_format).get("muxer")
        if muxer:
            cmd.extend(["-f", muxer])

        # Add output file
        cmd.append(str(output_path))

        await self.send_progress(session_id, 10, "converting", "Starting FFmpeg conversion")

        logger.info("FFmpeg cmd: %s", " ".join(cmd))

        # Run FFmpeg conversion with progress tracking
        try:
            _async_kwargs: dict = {}
            if sys.platform == "win32":
                _async_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                **_async_kwargs,
            )

            last_progress = 10
            stderr_output = b""

            try:
                # Read output line by line with timeout
                async with asyncio.timeout(settings.SUBPROCESS_TIMEOUT):
                    async for line in process.stdout:
                        line_str = line.decode("utf-8", errors="ignore")

                        # Parse progress
                        progress = _parse_ffmpeg_progress(line_str, total_duration)
                        if progress is not None and progress > last_progress:
                            # Map 0-100% to 10-95% to leave room for finalization
                            mapped_progress = 10 + (progress * 0.85)
                            last_progress = mapped_progress
                            await self.send_progress(
                                session_id,
                                mapped_progress,
                                "converting",
                                f"Converting video: {int(progress)}%",
                            )

                    # Wait for process to complete and consume remaining stderr
                    _, stderr_output = await process.communicate()
            except asyncio.TimeoutError:
                process.kill()
                # Ensure streams are consumed to prevent resource leaks
                try:
                    await process.communicate()
                except Exception:
                    logger.warning("Failed to consume streams after kill; continuing")
                raise Exception(f"Conversion timed out after {settings.SUBPROCESS_TIMEOUT} seconds")
            except Exception:
                # Ensure process is terminated and streams consumed on any error
                if process.returncode is None:
                    process.kill()
                    try:
                        await process.communicate()
                    except Exception:
                        logger.warning("Failed to consume streams after error kill; continuing")
                raise

            if process.returncode != 0:
                error_msg = (
                    stderr_output.decode("utf-8", errors="ignore")
                    if stderr_output
                    else "Unknown error"
                )
                # ffmpeg writes info banners (encoder version, build info, cpu caps)
                # before the actual failure line. Truncating from the start drops
                # the diagnostic. Log full stderr for debugging, surface the tail
                # in the exception so the user-facing error has the real cause.
                logger.error("FFmpeg conversion failed (full stderr):\n%s", error_msg)
                raise Exception(f"FFmpeg conversion failed: {error_msg[-500:]}")

            await self.send_progress(session_id, 98, "converting", "Finalizing video")

            # Verify output file exists
            if not output_path.exists():
                raise Exception("Output file was not created")

            await self.send_progress(session_id, 100, "completed", "Video conversion completed")

            return output_path

        except Exception as e:
            await self.send_progress(session_id, 0, "failed", f"Conversion failed: {str(e)}")
            raise

    async def _extract_audio(
        self,
        input_path: Path,
        output_format: str,
        options: Dict[str, Any],
        session_id: str,
    ) -> Path:
        """Extract audio from a video into one of the AUDIO_EXTRACT formats.

        Reuses the same progress / timeout / stderr handling as the video
        path but builds a `-vn -map 0:a:0 -c:a <codec> [-b:a <bitrate>]` cmd.
        """
        await self.send_progress(session_id, 0, "converting", "Starting audio extraction")

        profile = self._AUDIO_EXTRACT_PROFILES[output_format]
        codec = profile["codec"]
        if codec not in settings.ALLOWED_AUDIO_CODECS:
            raise ValueError(f"Invalid audio codec: {codec}")

        bitrate = options.get("bitrate", "192k") if profile["use_bitrate"] else None
        if bitrate is not None and bitrate not in settings.ALLOWED_BITRATES:
            raise ValueError(f"Invalid bitrate: {bitrate}")

        total_duration = await self.get_video_duration(input_path)
        output_path = settings.UPLOAD_DIR / f"{input_path.stem}_{uuid.uuid4().hex[:8]}.{output_format}"

        await self.send_progress(session_id, 5, "converting", "Preparing extraction")

        cmd = [
            settings.FFMPEG_PATH,
            "-nostdin",
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(input_path),
            "-y",
            "-progress",
            "pipe:1",
            "-loglevel",
            "error",
            "-vn",
            "-map",
            "0:a:0",
            "-c:a",
            codec,
        ]
        if bitrate:
            cmd.extend(["-b:a", bitrate])
        cmd.append(str(output_path))

        logger.info("FFmpeg audio-extract cmd: %s", " ".join(cmd))
        await self.send_progress(session_id, 10, "converting", "Starting FFmpeg extraction")

        try:
            _async_kwargs: dict = {}
            if sys.platform == "win32":
                _async_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                **_async_kwargs,
            )

            last_progress = 10
            stderr_output = b""

            try:
                async with asyncio.timeout(settings.SUBPROCESS_TIMEOUT):
                    async for line in process.stdout:
                        line_str = line.decode("utf-8", errors="ignore")
                        progress = _parse_ffmpeg_progress(line_str, total_duration)
                        if progress is not None and progress > last_progress:
                            mapped_progress = 10 + (progress * 0.85)
                            last_progress = mapped_progress
                            await self.send_progress(
                                session_id,
                                mapped_progress,
                                "converting",
                                f"Extracting audio: {int(progress)}%",
                            )
                    _, stderr_output = await process.communicate()
            except asyncio.TimeoutError:
                process.kill()
                try:
                    await process.communicate()
                except Exception:
                    logger.warning("Failed to consume streams after kill; continuing")
                raise Exception(f"Extraction timed out after {settings.SUBPROCESS_TIMEOUT} seconds")
            except Exception:
                if process.returncode is None:
                    process.kill()
                    try:
                        await process.communicate()
                    except Exception:
                        logger.warning("Failed to consume streams after error kill; continuing")
                raise

            if process.returncode != 0:
                error_msg = (
                    stderr_output.decode("utf-8", errors="ignore") if stderr_output else "Unknown error"
                )
                logger.error("FFmpeg audio extraction failed (full stderr):\n%s", error_msg)
                raise Exception(f"Audio extraction failed: {error_msg[-500:]}")

            await self.send_progress(session_id, 98, "converting", "Finalizing audio")

            if not output_path.exists():
                raise Exception("Output file was not created")

            await self.send_progress(session_id, 100, "completed", "Audio extraction completed")
            return output_path

        except Exception as e:
            await self.send_progress(session_id, 0, "failed", f"Extraction failed: {str(e)}")
            raise

    async def get_video_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract video metadata using ffprobe"""
        try:
            cmd = [
                settings.FFPROBE_PATH,
                "-v",
                "quiet",
                "-protocol_whitelist",
                "file",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(file_path),
            ]

            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=settings.SUBPROCESS_TIMEOUT,
                **_subprocess_kwargs,
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)

                # Extract video stream info
                video_stream = next(
                    (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
                    {},
                )

                # Extract audio stream info
                audio_stream = next(
                    (s for s in data.get("streams", []) if s.get("codec_type") == "audio"),
                    {},
                )

                return {
                    "duration": float(data.get("format", {}).get("duration", 0)),
                    "size": int(data.get("format", {}).get("size", 0)),
                    "format": data.get("format", {}).get("format_name", ""),
                    "width": video_stream.get("width", 0),
                    "height": video_stream.get("height", 0),
                    "video_codec": video_stream.get("codec_name", ""),
                    "audio_codec": audio_stream.get("codec_name", ""),
                    "fps": _parse_fps(video_stream.get("r_frame_rate", "0/1")),
                    "bitrate": int(data.get("format", {}).get("bit_rate", 0)),
                }
            else:
                return {"error": "Failed to probe video"}
        except Exception as e:
            return {"error": str(e)}
