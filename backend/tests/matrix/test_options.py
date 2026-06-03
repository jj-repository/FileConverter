"""
Conversion options coverage.

The main matrix runs every pair with empty options. This exercises the common
per-converter parameters (image quality/resize, audio bitrate/sample-rate/
channels, document toc) and verifies effects where they're observable.
"""

from __future__ import annotations

import uuid

import pytest

from tests.matrix.conftest import CONVERTERS
from tests.matrix.sample_factory import SampleUnavailable, get_sample


async def _convert(category, in_fmt, out_fmt, options, cache_dir):
    try:
        sample = get_sample(category, in_fmt, cache_dir)
    except SampleUnavailable as e:
        pytest.skip(str(e))
    converter = CONVERTERS[category]()
    out = await converter.convert(sample, out_fmt, options, f"opt-{uuid.uuid4().hex[:8]}")
    assert out.exists() and out.stat().st_size > 0
    return out


@pytest.mark.matrix
@pytest.mark.asyncio
async def test_image_resize_exact(sample_cache_dir):
    """width+height both given -> output has exactly those dimensions."""
    from PIL import Image

    out = await _convert("image", "png", "png", {"width": 32, "height": 24}, sample_cache_dir)
    try:
        with Image.open(out) as img:
            assert img.size == (32, 24)
    finally:
        out.unlink(missing_ok=True)


@pytest.mark.matrix
@pytest.mark.asyncio
async def test_image_resize_aspect(sample_cache_dir):
    """width only -> height scales to preserve aspect ratio (square sample)."""
    from PIL import Image

    out = await _convert("image", "png", "png", {"width": 20}, sample_cache_dir)
    try:
        with Image.open(out) as img:
            assert img.width == 20
    finally:
        out.unlink(missing_ok=True)


@pytest.mark.matrix
@pytest.mark.asyncio
async def test_image_jpeg_quality(sample_cache_dir):
    """Lower JPEG quality should produce a smaller file than higher quality."""
    low = await _convert("image", "png", "jpg", {"quality": 10}, sample_cache_dir)
    high = await _convert("image", "png", "jpg", {"quality": 95}, sample_cache_dir)
    try:
        assert low.stat().st_size <= high.stat().st_size
    finally:
        low.unlink(missing_ok=True)
        high.unlink(missing_ok=True)


@pytest.mark.matrix
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "options",
    [
        {"bitrate": "128k"},
        {"sample_rate": "22050"},
        {"channels": "1"},
        {"bitrate": "192k", "sample_rate": "44100", "channels": "2"},
    ],
)
async def test_audio_options(options, sample_cache_dir):
    """Audio conversion accepts the documented options without error."""
    out = await _convert("audio", "wav", "mp3", options, sample_cache_dir)
    out.unlink(missing_ok=True)


@pytest.mark.matrix
@pytest.mark.asyncio
async def test_audio_channels_mono(sample_cache_dir):
    """channels=1 actually yields a mono stream (verified via ffprobe)."""
    import json
    import subprocess

    from app.config import settings

    out = await _convert("audio", "wav", "mp3", {"channels": "1"}, sample_cache_dir)
    try:
        res = subprocess.run(
            [
                settings.FFPROBE_PATH,
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=channels",
                "-of",
                "json",
                str(out),
            ],
            capture_output=True,
            timeout=30,
        )
        channels = json.loads(res.stdout)["streams"][0]["channels"]
        assert channels == 1
    finally:
        out.unlink(missing_ok=True)


@pytest.mark.matrix
@pytest.mark.asyncio
async def test_document_toc(sample_cache_dir):
    """document md->pdf with a table of contents requested still converts."""
    out = await _convert("document", "md", "pdf", {"toc": True}, sample_cache_dir)
    out.unlink(missing_ok=True)
