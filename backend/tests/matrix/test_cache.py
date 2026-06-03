"""
Cache correctness.

The main matrix calls convert() directly, bypassing the cache. This drives
convert_with_cache() twice on identical input+options and asserts the second
call is served from cache and returns byte-identical output.
"""

from __future__ import annotations

import uuid

import pytest

from app.config import settings
from app.services.cache_service import get_cache_service
from tests.matrix.conftest import CONVERTERS
from tests.matrix.sample_factory import SampleUnavailable, get_sample


@pytest.mark.matrix
@pytest.mark.asyncio
async def test_second_conversion_hits_cache(sample_cache_dir):
    if not settings.CACHE_ENABLED:
        pytest.skip("cache disabled")
    cache = get_cache_service()
    if cache is None:
        pytest.skip("cache service unavailable")

    try:
        sample = get_sample("image", "png", sample_cache_dir)
    except SampleUnavailable as e:
        pytest.skip(str(e))

    converter = CONVERTERS["image"]()
    options = {"quality": 80}

    hits_before = cache.stats["hits"]
    out1 = await converter.convert_with_cache(sample, "webp", options, f"c-{uuid.uuid4().hex[:8]}")
    bytes1 = out1.read_bytes()
    out2 = await converter.convert_with_cache(sample, "webp", options, f"c-{uuid.uuid4().hex[:8]}")
    bytes2 = out2.read_bytes()

    try:
        # The second identical request must have registered a cache hit...
        assert cache.stats["hits"] > hits_before, "second identical conversion did not hit cache"
        # ...and returned exactly the same output.
        assert bytes1 == bytes2, "cached output differs from freshly converted output"
        assert len(bytes2) > 0
    finally:
        out1.unlink(missing_ok=True)
        out2.unlink(missing_ok=True)


@pytest.mark.matrix
@pytest.mark.asyncio
async def test_different_options_do_not_collide(sample_cache_dir):
    """Different options for the same input must not return the same cached file."""
    if not settings.CACHE_ENABLED or get_cache_service() is None:
        pytest.skip("cache unavailable")

    try:
        sample = get_sample("image", "png", sample_cache_dir)
    except SampleUnavailable as e:
        pytest.skip(str(e))

    converter = CONVERTERS["image"]()
    small = await converter.convert_with_cache(
        sample, "png", {"width": 16}, f"c-{uuid.uuid4().hex[:8]}"
    )
    large = await converter.convert_with_cache(
        sample, "png", {"width": 48}, f"c-{uuid.uuid4().hex[:8]}"
    )

    try:
        from PIL import Image

        with Image.open(small) as a:
            assert a.width == 16
        with Image.open(large) as b:
            assert b.width == 48
    finally:
        small.unlink(missing_ok=True)
        large.unlink(missing_ok=True)
