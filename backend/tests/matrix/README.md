# Conversion Matrix

End-to-end smoke test of **every** `input → output` pair that each converter
advertises in `get_supported_formats()`. Instead of discovering broken
conversions one upload at a time, this runs all ~670 pairs in one ~50s sweep
and prints a pass/fail grid.

## Run it

```bash
cd backend
python scripts/run_matrix.py                 # full sweep
python scripts/run_matrix.py -k image        # one category
python scripts/run_matrix.py -k "audio or video"
```

Outputs:
- `conversion-matrix.md`  — human-readable grid + per-category failure details
- `conversion-matrix.json` — machine-readable results (feeds the gap baseline)

It is **excluded from the default `pytest` run** (slow + intentionally surfaces
gaps) via `-m "not matrix"` in `pytest.ini`.

## How it works

| File | Role |
|---|---|
| `sample_factory.py` | Synthesizes one minimal *valid* input file per format (PIL, ffmpeg, fonttools, pandoc, py7zr, …). Raises `SampleUnavailable` → the pair is *skipped*, never silently passed. |
| `test_conversion_matrix.py` | Service-layer: calls each converter's real `convert()` for every pair, asserts a non-empty output. |
| `test_http_smoke.py` | HTTP layer: one representative pair per category through the full FastAPI upload → convert → download path. |
| `conftest.py` | Records every result; writes the grid + JSON and prints a terminal summary at session end. |
| `known_gaps.py` | AUTO-GENERATED baseline of pairs the converters advertise but can't do. These are `xfail`ed so the suite stays green except for **new** regressions. |
| `test_robustness.py` | Garbage input (empty / corrupt / wrong-extension) per category — asserts the server rejects it (≥400) and never hangs or crashes. |
| `test_options.py` | Common conversion options (image quality/resize, audio bitrate/sample-rate/channels, document toc) with effects verified where observable. |
| `test_roundtrip.py` | Lossless A→B→A integrity: data (csv↔json/xml/yaml), subtitle timings (srt↔vtt/ass), spreadsheet values (xlsx↔csv). |
| `test_batch_smoke.py` | `/api/batch/convert` multi-file flow, incl. empty list + mixed good/garbage. |
| `test_cache.py` | `convert_with_cache` twice → asserts a cache hit + byte-identical output; different options don't collide. |

All run together via `scripts/run_matrix.py` (710 passed / 10 skipped as of 2026-06-01).

### Robustness note
Corrupt-but-right-extension uploads return **HTTP 500** (the converter library
throws e.g. `UnidentifiedImageError`/`BadZipFile`, which the router maps to a
server error). This is the project's **intentional, test-enforced convention** —
the integration suites (`test_audio_router`, `test_archive_router`,
`test_batch_router`) assert `500` / `in [400, 500]` for conversion failures.
The robustness test therefore asserts only that garbage is *rejected* (≥400) and
that the worker doesn't crash/hang; it logs the 500s as an informational signal.
Do **not** flip these to 4xx without updating those ~20 router tests too.

## Regression-guard workflow

1. A new break in a *passing* pair → that case **fails** (red). Fix it.
2. You fix a converter so a known gap now works → that case shows **XPASS**.
   Regenerate the baseline to drop it:
   ```bash
   python scripts/run_matrix.py
   python scripts/gen_known_gaps.py
   ```

## Gaps found on first run (2026-06-01) — all FIXED

The first sweep found 69 pairs each converter advertised but `convert()` couldn't
do. All were fixed the same day (`known_gaps.py` is now empty; the matrix is a
pure regression guard):

- **image `*→heic`** — mapped `heic→HEIF` (PIL's encoder name) in `image_converter.py`.
- **document `pdf→*`** — added a `pypdf` text-extraction path; PDF text is fed to Pandoc as Markdown.
- **ebook `txt↔html`, `*→pdf`, `pdf→*`** — rewrote `ebook_converter.py` as an HTML hub (load any input → sanitized HTML → render any output).
- **spreadsheet `xls` (in/out)** — added `xlrd` (read) + `xlwt` (write; pandas 3.x dropped its xlwt engine).
- **subtitle `*→sub`** — mapped `sub→microdvd` for the pysubs2 save call.
- **audio `*→opus`/`*→alac`** — added `opus→libopus`, `alac→alac` to `codec_map` (+ `-f ipod` muxer for alac); `ape` made input-only (FFmpeg has no encoder).
- **archive `tar*→zip`** — clamp each entry's ZIP timestamp to ≥1980.

`ape` audio input is *skipped* (FFmpeg has no Monkey's Audio encoder, so no sample
can be synthesized here) — not a converter bug.
