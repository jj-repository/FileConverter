"""
FFmpeg and FFprobe mocking utilities
"""

from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json
from pathlib import Path
import asyncio


class FFmpegMock:
    """Mock FFmpeg subprocess calls"""

    @staticmethod
    def mock_successful_conversion(output_file_path: Path = None):
        """
        Mock successful FFmpeg conversion
        Returns mock that:
        - Creates output file if path provided
        - Returns exit code 0
        - Provides progress output

        Args:
            output_file_path: Optional path where output file should be created
        """
        async def async_proc_mock(*args, **kwargs):
            # Create output file if path provided
            if output_file_path:
                output_file_path.write_bytes(b"MOCK_CONVERTED_VIDEO_DATA")

            mock_proc = AsyncMock()
            mock_proc.returncode = 0
            mock_proc.wait = AsyncMock(return_value=0)

            # Mock progress output with proper async iteration
            progress_lines = [
                b"frame=100 fps=30 time=00:00:03.33 bitrate=2000.0kbits/s\n",
                b"frame=200 fps=30 time=00:00:06.66 bitrate=2000.0kbits/s\n",
                b"frame=300 fps=30 time=00:00:10.00 bitrate=2000.0kbits/s\n",
            ]

            # Create async iterator for stdout
            async def stdout_iterator():
                for line in progress_lines:
                    yield line

            mock_proc.stdout = stdout_iterator()

            # Create async iterator for stderr (empty)
            async def stderr_iterator():
                return
                yield  # Make it a generator

            mock_proc.stderr = AsyncMock()
            mock_proc.stderr.read = AsyncMock(return_value=b'')

            return mock_proc

        return patch('asyncio.create_subprocess_exec', side_effect=async_proc_mock)

    @staticmethod
    def mock_failed_conversion(error_message="FFmpeg error: Conversion failed"):
        """
        Mock failed FFmpeg conversion

        Args:
            error_message: Error message to return
        """
        async def async_proc_mock(*args, **kwargs):
            mock_proc = AsyncMock()
            mock_proc.returncode = 1
            mock_proc.wait = AsyncMock(return_value=1)

            # Create async iterator for stdout (empty)
            async def stdout_iterator():
                return
                yield  # Make it a generator

            mock_proc.stdout = stdout_iterator()

            # Return error in stderr
            mock_proc.stderr = AsyncMock()
            mock_proc.stderr.read = AsyncMock(return_value=error_message.encode())

            return mock_proc

        return patch('asyncio.create_subprocess_exec', side_effect=async_proc_mock)

    @staticmethod
    def mock_timeout_conversion():
        """Mock FFmpeg conversion that times out"""
        async def async_proc_mock(*args, **kwargs):
            mock_proc = AsyncMock()
            mock_proc.kill = AsyncMock()
            mock_proc.wait = AsyncMock()

            # Create async iterator that hangs/times out
            async def stdout_iterator():
                # Simulate timeout by raising TimeoutError when iterating
                await asyncio.sleep(1000)  # This will timeout with asyncio.timeout
                yield  # Make it a generator

            mock_proc.stdout = stdout_iterator()
            mock_proc.stderr = AsyncMock()

            return mock_proc

        return patch('asyncio.create_subprocess_exec', side_effect=async_proc_mock)

    @staticmethod
    def mock_progress_output(total_duration_seconds=120, num_updates=10):
        """
        Generate realistic FFmpeg progress output

        Args:
            total_duration_seconds: Total duration of video in seconds
            num_updates: Number of progress updates to generate
        """
        progress_lines = []
        for i in range(1, num_updates + 1):
            time_seconds = (total_duration_seconds / num_updates) * i
            hours = int(time_seconds // 3600)
            minutes = int((time_seconds % 3600) // 60)
            seconds = int(time_seconds % 60)
            milliseconds = int((time_seconds - int(time_seconds)) * 100)

            progress_line = (
                f"frame={i*100} fps=30 time={hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:02d} "
                f"bitrate=2000.0kbits/s speed=1.0x\n"
            )
            progress_lines.append(progress_line.encode())

        return progress_lines


class FFprobeMock:
    """Mock FFprobe metadata extraction"""

    @staticmethod
    def mock_video_metadata(
        duration=120.5,
        width=1920,
        height=1080,
        codec="h264",
        fps="30/1",
        bit_rate="2000000"
    ):
        """
        Mock FFprobe video metadata response

        Args:
            duration: Video duration in seconds
            width: Video width in pixels
            height: Video height in pixels
            codec: Video codec name
            fps: Frame rate as fraction string
            bit_rate: Bit rate in bits per second
        """
        metadata = {
            "format": {
                "duration": str(duration),
                "size": "10485760",
                "format_name": "mp4",
                "bit_rate": bit_rate
            },
            "streams": [
                {
                    "index": 0,
                    "codec_type": "video",
                    "codec_name": codec,
                    "width": width,
                    "height": height,
                    "r_frame_rate": fps,
                    "avg_frame_rate": fps
                }
            ]
        }

        mock_run = Mock(
            returncode=0,
            stdout=json.dumps(metadata),
            stderr=''
        )

        return patch('subprocess.run', return_value=mock_run)

    @staticmethod
    def mock_audio_metadata(
        duration=180.25,
        sample_rate="44100",
        channels=2,
        codec="mp3",
        bit_rate="192000"
    ):
        """
        Mock FFprobe audio metadata response

        Args:
            duration: Audio duration in seconds
            sample_rate: Sample rate in Hz
            channels: Number of audio channels
            codec: Audio codec name
            bit_rate: Bit rate in bits per second
        """
        metadata = {
            "format": {
                "duration": str(duration),
                "size": "5242880",
                "format_name": codec,
                "bit_rate": bit_rate
            },
            "streams": [
                {
                    "index": 0,
                    "codec_type": "audio",
                    "codec_name": codec,
                    "sample_rate": str(sample_rate),
                    "channels": channels,
                    "channel_layout": "stereo" if channels == 2 else "mono",
                    "bit_rate": bit_rate
                }
            ]
        }

        mock_run = Mock(
            returncode=0,
            stdout=json.dumps(metadata),
            stderr=''
        )

        return patch('subprocess.run', return_value=mock_run)

    @staticmethod
    def mock_video_with_audio_metadata(
        video_duration=120.5,
        video_width=1920,
        video_height=1080,
        audio_sample_rate="48000",
        audio_channels=2
    ):
        """
        Mock FFprobe metadata for video with audio track

        Args:
            video_duration: Video duration in seconds
            video_width: Video width in pixels
            video_height: Video height in pixels
            audio_sample_rate: Audio sample rate in Hz
            audio_channels: Number of audio channels
        """
        metadata = {
            "format": {
                "duration": str(video_duration),
                "size": "15728640",
                "format_name": "mp4",
                "bit_rate": "3000000"
            },
            "streams": [
                {
                    "index": 0,
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": video_width,
                    "height": video_height,
                    "r_frame_rate": "30/1",
                    "avg_frame_rate": "30/1"
                },
                {
                    "index": 1,
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "sample_rate": str(audio_sample_rate),
                    "channels": audio_channels,
                    "channel_layout": "stereo" if audio_channels == 2 else "mono",
                    "bit_rate": "192000"
                }
            ]
        }

        mock_run = Mock(
            returncode=0,
            stdout=json.dumps(metadata),
            stderr=''
        )

        return patch('subprocess.run', return_value=mock_run)

    @staticmethod
    def mock_failure(error_message="FFprobe error: Invalid file"):
        """
        Mock FFprobe failure

        Args:
            error_message: Error message to return
        """
        mock_run = Mock(
            returncode=1,
            stdout='',
            stderr=error_message
        )

        return patch('subprocess.run', return_value=mock_run)


class FFmpegCommandValidator:
    """Helper to validate FFmpeg command construction"""

    @staticmethod
    def validate_no_shell_injection(command_args: list) -> bool:
        """
        Validate that FFmpeg command doesn't use shell injection

        Args:
            command_args: List of command arguments

        Returns:
            True if command is safe (no shell characters)
        """
        shell_chars = [';', '|', '&', '`', '$', '>', '<', '\n', '\r']

        for arg in command_args:
            arg_str = str(arg)
            for char in shell_chars:
                if char in arg_str:
                    return False
        return True

    @staticmethod
    def validate_whitelisted_codec(codec: str, allowed_codecs: set) -> bool:
        """
        Validate that codec is in whitelist

        Args:
            codec: Codec name to check
            allowed_codecs: Set of allowed codec names

        Returns:
            True if codec is allowed
        """
        return codec in allowed_codecs

    @staticmethod
    def extract_output_path(command_args: list) -> str:
        """
        Extract output path from FFmpeg command

        Args:
            command_args: List of command arguments

        Returns:
            Output file path as string
        """
        # Output path is typically the last argument
        if command_args:
            return str(command_args[-1])
        return None
