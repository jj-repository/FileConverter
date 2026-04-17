"""Unit tests for app/utils/subprocess_utils.py — shared subprocess helpers."""

import pytest
from app.utils.subprocess_utils import parse_ffmpeg_progress, parse_fps


class TestParseFps:
    @pytest.mark.parametrize(
        "fps_str, expected",
        [
            ("30000/1001", pytest.approx(29.97, rel=1e-3)),
            ("24000/1001", pytest.approx(23.976, rel=1e-3)),
            ("60000/1001", pytest.approx(59.94, rel=1e-3)),
            ("25/1", 25.0),
            ("30/1", 30.0),
        ],
    )
    def test_parse_fraction(self, fps_str, expected):
        assert parse_fps(fps_str) == expected

    def test_parse_plain_number(self):
        assert parse_fps("30.0") == pytest.approx(30.0)

    def test_parse_integer_string(self):
        assert parse_fps("24") == pytest.approx(24.0)

    def test_zero_denominator_returns_zero(self):
        assert parse_fps("30/0") == 0.0

    def test_invalid_string_returns_zero(self):
        assert parse_fps("invalid") == 0.0

    def test_empty_string_returns_zero(self):
        assert parse_fps("") == 0.0

    def test_non_numeric_string_returns_zero(self):
        assert parse_fps("n/a") == 0.0


class TestParseFFmpegProgress:
    def test_basic_progress(self):
        line = "time=00:00:30.50 bitrate=192.0kbits/s"
        result = parse_ffmpeg_progress(line, 120.0)
        assert result == pytest.approx(25.4, rel=1e-2)

    def test_fifty_percent(self):
        line = "time=00:01:00.00 bitrate=192.0kbits/s"
        result = parse_ffmpeg_progress(line, 120.0)
        assert result == pytest.approx(50.0)

    def test_hours_component(self):
        line = "time=01:00:00.00 bitrate=192.0kbits/s"
        result = parse_ffmpeg_progress(line, 7200.0)
        assert result == pytest.approx(50.0)

    def test_capped_at_99_9(self):
        line = "time=00:03:00.00 bitrate=192.0kbits/s"
        result = parse_ffmpeg_progress(line, 120.0)
        assert result == pytest.approx(99.9)

    def test_no_time_match_returns_none(self):
        assert parse_ffmpeg_progress("frame=100 fps=25 q=28.0", 120.0) is None

    def test_zero_duration_returns_none(self):
        line = "time=00:01:00.00 bitrate=192.0kbits/s"
        assert parse_ffmpeg_progress(line, 0.0) is None

    def test_empty_line_returns_none(self):
        assert parse_ffmpeg_progress("", 120.0) is None
