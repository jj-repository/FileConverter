# Decisions & Standards

## Design Decisions
| Decision | Rationale |
|----------|-----------|
| Separate FastAPI backend | Python has better file conversion libraries than Node |
| HTTP frontend↔backend | Simpler than IPC; backend usable standalone |
| No settings persistence yet | MVP; not critical for core |
| Update opens browser | Simpler; avoids signature verification complexity |
| Bundled Python backend | Self-contained; no Python install required |

## Won't Fix
| Issue | Reason |
|-------|--------|
| No settings UI | Low priority, defaults work |
| Partial update system | Releases page sufficient; full auto-update adds complexity |
| Large app size (~200MB) | Electron + Python runtime; acceptable |
| Backend startup delay | Health check polling, typically <2s |

## Known Issues
1. Partial update system — needs full UI integration
2. No settings persistence

## Recent Fixes (Jun 2026)
**Conversion-matrix gaps closed (2026-06-01).** The new matrix (`tests/matrix/`) found 69 pairs advertised in `get_supported_formats()` that `convert()` couldn't do; all fixed, matrix now 660 pass / 0 fail / 10 skip (ape input only):
- image `*→heic`: map `heic→HEIF` (PIL encoder name)
- audio `*→opus`/`*→alac`: add `opus→libopus`,`alac→alac` to codec_map (+`-f ipod` for alac); `ape` made input-only (no FFmpeg encoder)
- archive `tar*→zip`: clamp ZIP entry mtimes to ≥1980
- document `pdf→*`: pypdf text-extraction → Pandoc (Markdown)
- ebook: rewrote as HTML hub (any input→sanitized HTML→any output)
- spreadsheet `xls`: add `xlrd` (read) + `xlwt` (write; pandas 3.x dropped xlwt engine)
- subtitle `*→sub`: map `sub→microdvd` for pysubs2 save
- data yaml output: `yaml.dump(sort_keys=False)` — PyYAML alphabetized keys, scrambling column order on csv→yaml→csv round-trips (found by `test_roundtrip.py`)
- video codec validation: `convert()` now rejects a user codec not in `ALLOWED_VIDEO_CODECS` with `ValueError("Invalid codec …")` (was silently ignored). Restores the intended security contract; valid-but-incompatible codecs are still silently overridden. Fixes 2 long-failing security tests.

**Matrix test suites expanded (2026-06-01).** Added robustness (garbage input), options coverage, round-trip integrity, batch smoke, cache correctness — all under `tests/matrix/`, run via `scripts/run_matrix.py` (710 pass / 10 skip).

**Convention (intentional):** conversion/processing failures return **HTTP 500**, not 4xx. ~20 router integration tests enforce this (`== 500` / `in [400,500]`). The robustness test asserts only that garbage is rejected (≥400) and the worker doesn't crash — it does NOT require 4xx. Considered flipping corrupt-input to 422 but rejected it: would break the established, test-enforced contract for a marginal semantic gain.

## Recent Fixes (Jan 2026)
Audio converter stderr handling (deadlock prevention), symlink traversal protection, host 0.0.0.0→127.0.0.1, admin auth on /api/cache/info, JSON parsing errors in data converter, SVG temp file cleanup ✓

## Quality Standards
Target: reliable, secure, user-friendly file converter.
Do not optimize: conversion speed limited by ffmpeg/tools; architecture is appropriate.
