"""Shared subprocess utilities for converter services."""

import re
import subprocess
import sys
from typing import Optional

# Windows: hide console window for subprocess calls
subprocess_kwargs: dict = {}
if sys.platform == "win32":
    subprocess_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW


def parse_ffmpeg_progress(line: str, total_duration: float) -> Optional[float]:
    """Parse FFmpeg progress from output line.

    Returns percentage (0-99.9) or None if no progress info found.
    """
    time_match = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
    if time_match and total_duration > 0:
        hours = int(time_match.group(1))
        minutes = int(time_match.group(2))
        seconds = float(time_match.group(3))
        current_time = hours * 3600 + minutes * 60 + seconds
        progress = (current_time / total_duration) * 100
        return min(progress, 99.9)
    return None
