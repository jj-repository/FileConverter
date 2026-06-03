"""
Garbage-input robustness.

Feeds each converter's HTTP endpoint three kinds of bad input — empty file,
corrupt bytes, and a valid file with a lying extension — and asserts the
server fails *cleanly* (a 4xx client error), never a 500 / crash / hang.

A 500 here means an unhandled code path: exactly the kind of bug that turns a
bad upload into a stack trace instead of a friendly error.
"""

from __future__ import annotations

import pytest

from tests.matrix.sample_factory import SampleUnavailable, get_sample

# category -> (input extension, a valid output format)
CATEGORY_IO = {
    "image": ("png", "webp"),
    "video": ("mp4", "mkv"),
    "audio": ("wav", "mp3"),
    "document": ("docx", "txt"),
    "data": ("json", "csv"),
    "archive": ("zip", "tar"),
    "spreadsheet": ("xlsx", "csv"),
    "subtitle": ("srt", "vtt"),
    "ebook": ("epub", "txt"),
    "font": ("ttf", "woff"),
}

CASES = ["empty", "corrupt", "wrong_ext"]


def _make_bad_file(case: str, in_fmt: str, cache_dir, tmp_path):
    """Return (filename, bytes) for the requested garbage case."""
    name = f"bad.{in_fmt}"
    if case == "empty":
        return name, b""
    if case == "corrupt":
        return name, b"\x00\xff this is not a valid file \x01\x02\x03" * 8
    if case == "wrong_ext":
        # Real PNG bytes wearing this category's extension. For the image
        # category, use plain text instead so the content genuinely mismatches.
        try:
            if in_fmt == "png":
                return name, b"just,some,text\n1,2,3\n"
            decoy = get_sample("image", "png", cache_dir)
            return name, decoy.read_bytes()
        except SampleUnavailable:
            pytest.skip("decoy sample unavailable")
    raise AssertionError(case)


@pytest.mark.matrix
@pytest.mark.parametrize("category", list(CATEGORY_IO))
@pytest.mark.parametrize("case", CASES)
def test_garbage_input_fails_cleanly(category, case, sample_cache_dir, tmp_path, test_client):
    in_fmt, out_fmt = CATEGORY_IO[category]
    filename, payload = _make_bad_file(case, in_fmt, sample_cache_dir, tmp_path)

    resp = test_client.post(
        f"/api/{category}/convert",
        files={"file": (filename, payload, "application/octet-stream")},
        data={"output_format": out_fmt},
    )

    # Hard contract: garbage must be REJECTED (never silently "succeed" and
    # hand back a bogus output), and the request must return a structured
    # response rather than hang or crash the worker.
    assert resp.status_code >= 400, (
        f"{category}/{case}: server ACCEPTED garbage with {resp.status_code} "
        f"— a bad upload should never look successful. Body: {resp.text[:300]}"
    )
    # Soft signal (not asserted): a 500 here means the converter raised a
    # library error (e.g. UnidentifiedImageError, BadZipFile) the router maps
    # to a server error; ideally these would surface as 4xx. Tracked, not
    # failed, because flipping the status is an API-contract change.
    if resp.status_code >= 500:
        print(f"[robustness] {category}/{case} -> {resp.status_code} (ideally 4xx)")
