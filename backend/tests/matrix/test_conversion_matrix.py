"""
Service-layer conversion matrix.

For every declared input→output pair of every converter, synthesize a real
input file, run the actual ``convert()`` implementation, and assert it produces
a non-empty output. Results feed the session-end grid (see conftest.Recorder).

Run it with::

    python scripts/run_matrix.py            # or
    pytest tests/matrix -m matrix -o addopts="" -q

It is excluded from the default test run (it is slow and intentionally
surfaces real failures) via ``-m "not matrix"`` in pytest.ini.
"""

from __future__ import annotations

import uuid

import pytest

from tests.matrix.conftest import CONVERTERS, build_matrix_params
from tests.matrix.sample_factory import SampleUnavailable, get_sample

try:
    from tests.matrix.known_gaps import KNOWN_GAPS
except ImportError:  # baseline not generated yet
    KNOWN_GAPS = {}


def _param(category, in_fmt, out_fmt):
    """Build a parametrize entry, xfailing pairs in the known-gaps baseline.

    strict=False so a fixed gap surfaces as XPASS (signal to regenerate the
    baseline) rather than failing. Pairs NOT in the baseline fail hard, so a
    genuine regression turns the suite red.
    """
    marks = []
    reason = KNOWN_GAPS.get((category, in_fmt, out_fmt))
    if reason is not None:
        marks.append(pytest.mark.xfail(reason=reason, strict=False))
    return pytest.param(
        category, in_fmt, out_fmt, marks=marks, id=f"{category}:{in_fmt}->{out_fmt}"
    )


_PARAMS = [_param(*p) for p in build_matrix_params()]


@pytest.mark.matrix
@pytest.mark.asyncio
@pytest.mark.parametrize("category,in_fmt,out_fmt", _PARAMS)
async def test_conversion(category, in_fmt, out_fmt, sample_cache_dir, recorder):
    # 1. Get (or synthesize) a valid input sample.
    try:
        sample = get_sample(category, in_fmt, sample_cache_dir)
    except SampleUnavailable as e:
        recorder.record(category, in_fmt, out_fmt, "skip", str(e))
        pytest.skip(f"no input sample for {category}/{in_fmt}: {e}")

    # 2. Run the real conversion.
    converter = CONVERTERS[category]()
    session_id = f"matrix-{uuid.uuid4().hex[:8]}"
    output_path = None
    try:
        output_path = await converter.convert(sample, out_fmt, {}, session_id)
        assert output_path.exists(), "converter returned a path that does not exist"
        assert output_path.stat().st_size > 0, "converter produced an empty file"
    except Exception as e:  # noqa: BLE001 — we want every failure recorded
        recorder.record(category, in_fmt, out_fmt, "fail", f"{type(e).__name__}: {e}")
        pytest.fail(f"{category} {in_fmt}->{out_fmt} failed: {type(e).__name__}: {e}")
    else:
        recorder.record(category, in_fmt, out_fmt, "pass")
    finally:
        if output_path is not None and output_path.exists():
            try:
                output_path.unlink()
            except OSError:
                pass
