"""
HTTP smoke test — one representative conversion per category through the full
FastAPI stack (upload validation → routing → convert_with_cache → download).

This complements the service-layer matrix (test_conversion_matrix.py): the
matrix proves the conversion logic for every pair, while this proves the
upload/validation/routing/download plumbing works end-to-end per category.
"""

from __future__ import annotations

import pytest

from tests.matrix.sample_factory import SampleUnavailable, get_sample

# (category, input_format, output_format) — one known-representative pair each.
SMOKE_PAIRS = [
    ("image", "png", "webp"),
    ("video", "mp4", "mkv"),
    ("audio", "wav", "mp3"),
    ("document", "md", "html"),
    ("data", "json", "csv"),
    ("archive", "zip", "tar"),
    ("spreadsheet", "csv", "xlsx"),
    ("subtitle", "srt", "vtt"),
    ("ebook", "epub", "txt"),
    ("font", "ttf", "woff"),
]


@pytest.mark.matrix
@pytest.mark.parametrize(
    "category,in_fmt,out_fmt",
    SMOKE_PAIRS,
    ids=[f"{c}:{i}->{o}" for c, i, o in SMOKE_PAIRS],
)
def test_http_convert_and_download(category, in_fmt, out_fmt, sample_cache_dir, test_client):
    try:
        sample = get_sample(category, in_fmt, sample_cache_dir)
    except SampleUnavailable as e:
        pytest.skip(f"no input sample for {category}/{in_fmt}: {e}")

    with sample.open("rb") as fh:
        resp = test_client.post(
            f"/api/{category}/convert",
            files={"file": (sample.name, fh, "application/octet-stream")},
            data={"output_format": out_fmt},
        )

    assert resp.status_code == 200, f"convert returned {resp.status_code}: {resp.text}"
    body = resp.json()
    assert body["status"] == "completed", body
    assert body["output_file"], body

    # The advertised download link must actually serve the file.
    dl = test_client.get(f"/api/{category}/download/{body['output_file']}")
    assert dl.status_code == 200, f"download returned {dl.status_code}: {dl.text}"
    assert len(dl.content) > 0, "download served an empty file"
