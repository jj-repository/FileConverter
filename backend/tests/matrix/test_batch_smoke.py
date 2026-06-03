"""
Batch endpoint smoke test (HTTP).

POST several files to /api/batch/convert and assert the batch flow reports
per-file success. The batch router only accepts image/video/audio/document
inputs, so this uses images.
"""

from __future__ import annotations

import pytest

from tests.matrix.sample_factory import SampleUnavailable, get_sample


@pytest.mark.matrix
def test_batch_convert_multiple_images(sample_cache_dir, test_client):
    try:
        png = get_sample("image", "png", sample_cache_dir)
    except SampleUnavailable as e:
        pytest.skip(str(e))

    data = png.read_bytes()
    files = [("files", (f"img_{i}.png", data, "image/png")) for i in range(3)]

    resp = test_client.post(
        "/api/batch/convert",
        files=files,
        data={"output_format": "webp"},
    )

    assert resp.status_code == 200, f"{resp.status_code}: {resp.text[:300]}"
    body = resp.json()
    assert body["total_files"] == 3
    assert body["successful"] == 3
    assert body["failed"] == 0
    assert len(body["results"]) == 3


@pytest.mark.matrix
def test_batch_rejects_empty_file_list(test_client):
    """No files -> a clean client error, not a crash."""
    resp = test_client.post(
        "/api/batch/convert",
        data={"output_format": "webp"},
    )
    assert resp.status_code >= 400 and resp.status_code < 500


@pytest.mark.matrix
def test_batch_mixed_valid_and_garbage(sample_cache_dir, test_client):
    """A good image + a corrupt one: batch completes, reports the failure."""
    try:
        png = get_sample("image", "png", sample_cache_dir)
    except SampleUnavailable as e:
        pytest.skip(str(e))

    files = [
        ("files", ("good.png", png.read_bytes(), "image/png")),
        ("files", ("bad.png", b"\x00\xff not a png \x01", "image/png")),
    ]
    resp = test_client.post(
        "/api/batch/convert",
        files=files,
        data={"output_format": "webp"},
    )
    # Either the corrupt file is rejected up front (4xx) or the batch runs and
    # reports it as a failed item — both are acceptable; a 500 is not.
    assert resp.status_code < 500, f"{resp.status_code}: {resp.text[:300]}"
    if resp.status_code == 200:
        body = resp.json()
        assert body["total_files"] == 2
        assert body["successful"] >= 1
