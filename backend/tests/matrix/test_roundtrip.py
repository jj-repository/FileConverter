"""
Round-trip integrity.

The main matrix asserts output *exists*; this asserts data *survives* a
lossless A -> B -> A round trip. Catches silent data loss an existence check
can't see (dropped rows, mangled timings, lost columns).
"""

from __future__ import annotations

import uuid

import pytest

from tests.matrix.conftest import CONVERTERS
from tests.matrix.sample_factory import get_sample


async def _convert(category, src, out_fmt):
    converter = CONVERTERS[category]()
    return await converter.convert(src, out_fmt, {}, f"rt-{uuid.uuid4().hex[:8]}")


@pytest.mark.matrix
@pytest.mark.asyncio
@pytest.mark.parametrize("mid", ["json", "xml", "yaml"])
async def test_data_roundtrip_preserves_rows(mid, sample_cache_dir):
    """csv -> {json,xml,yaml} -> csv keeps the same records."""
    import pandas as pd

    src = get_sample("data", "csv", sample_cache_dir)
    a = await _convert("data", src, mid)
    b = await _convert("data", a, "csv")
    try:
        original = pd.read_csv(src)
        result = pd.read_csv(b)
        assert list(result.columns) == list(original.columns)
        assert result.shape == original.shape
        assert result.to_dict("records") == original.to_dict("records")
    finally:
        a.unlink(missing_ok=True)
        b.unlink(missing_ok=True)


@pytest.mark.matrix
@pytest.mark.asyncio
@pytest.mark.parametrize("mid", ["vtt", "ass"])
async def test_subtitle_roundtrip_preserves_timings(mid, sample_cache_dir):
    """srt -> {vtt,ass} -> srt keeps each line's start/end/text."""
    import pysubs2

    src = get_sample("subtitle", "srt", sample_cache_dir)
    a = await _convert("subtitle", src, mid)
    b = await _convert("subtitle", a, "srt")
    try:
        orig = pysubs2.load(str(src))
        result = pysubs2.load(str(b))
        assert len(result) == len(orig)
        for o, r in zip(orig, result):
            assert o.start == r.start
            assert o.end == r.end
            assert o.plaintext.strip() == r.plaintext.strip()
    finally:
        a.unlink(missing_ok=True)
        b.unlink(missing_ok=True)


@pytest.mark.matrix
@pytest.mark.asyncio
async def test_spreadsheet_roundtrip_preserves_values(sample_cache_dir):
    """xlsx -> csv -> xlsx keeps the same cell values."""
    import pandas as pd

    src = get_sample("spreadsheet", "xlsx", sample_cache_dir)
    a = await _convert("spreadsheet", src, "csv")
    b = await _convert("spreadsheet", a, "xlsx")
    try:
        original = pd.read_excel(src, engine="openpyxl")
        result = pd.read_excel(b, engine="openpyxl")
        assert list(result.columns) == list(original.columns)
        assert result.to_dict("records") == original.to_dict("records")
    finally:
        a.unlink(missing_ok=True)
        b.unlink(missing_ok=True)
