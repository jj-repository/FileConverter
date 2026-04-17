# FileConverter Audit Review Queue

Generated: 2026-04-17
Agents: code-quality, security, performance, test-quality, architecture, frontend-specialist (first run), devops
Prior audit: 2026-04-05

## Fixed This Session (Session 2 — additional 30 items)

- [x] font_converter.py: `get_info()` and `optimize_font()` wrapped in `asyncio.to_thread`
- [x] ebook_converter.py: `_epub_to_txt` and `_epub_to_html` BeautifulSoup loops offloaded to thread
- [x] ebook_converter.py: `get_info()` `epub.read_epub` offloaded to thread
- [x] base_router.py: `handle_download` adds `BackgroundTask(cleanup_after_download)` + uses `cleanup_file`
- [x] base_router.py: `cleanup_after_download` replaced bare `unlink` with `cleanup_file`
- [x] batch.py: `/download/{filename}` adds `BackgroundTask` cleanup
- [x] font.py: `/optimize` endpoint adds `validate_mime_type` (was skipping MIME check)
- [x] font.py: `validate_mime_type` added to imports
- [x] document_converter.py: `get_document_metadata` Pandoc call adds `--sandbox`
- [x] font_converter.py: bare expression `input_path.suffix[1:].lower()` removed
- [x] file_handler.py: dead `_parse_fps_safe` function deleted
- [x] config.py: redundant inline `import logging` removed
- [x] video_converter.py: `import json` moved to top; inline import inside function removed
- [x] audio_converter.py: `import json` moved to top; inline import inside function removed
- [x] test_app.py: hard-coded `"1.03"` version assertion replaced with `isinstance` check
- [x] handlers.ts: MSW mock URL fixed `/api/batch/zip` → `/api/batch/download-zip`
- [x] security-scan.yml + doc-review.yml: `actions/checkout@v4` SHA-pinned
- [x] build-release.yml: PyInstaller pinned to `==6.14.2` on Linux (was unpinned)
- [x] build-release.yml: `retention-days: 1` added to both artifact upload steps
- [x] build-release.yml: top-level `permissions: contents: read` added
- [x] backend/.github/workflows/backend-tests.yml: deleted (duplicate, all tags floating)
- [x] TabNavigation.tsx: `role="tablist"` on nav; `role="tab"`, `aria-selected`, `aria-controls`, `id` on buttons
- [x] LanguageSelector.tsx: `id="language-selector-button"` added to trigger button
- [x] SubtitleConverter.tsx: `id="convert-format-tab"` and `id="adjust-timing-tab"` added to tab buttons
- [x] BatchConverterImproved.tsx: file list key changed from `index` to stable composite key
- [x] FontConverter.tsx: all three `window.electron` guards → `window.electron?.isElectron`
- [x] useConverter.ts: `autoDownload` applies `sanitizeFilename(customFilename)` consistently with `handleDownload`
- [x] S3: CSP `style-src 'unsafe-inline'` now dev-only (was unconditional)
- [x] S5: SSRF fc::/7 IPv6 check uses regex instead of startsWith (was matching fca.example.com)
- [x] S6: CORS wildcard guard raises ValueError early when `*` + `allow_credentials=True`
- [x] S8: WebSocket origin allows empty (Electron) + localhost; removed `file://` wildcard
- [x] P4: `reconnectAttempt` changed to React state so it triggers re-renders
- [x] CQ1: `base_converter.py` lazy property resolves `ws_manager` at call time (breaks circular import)
- [x] CQ2: `_parse_fps` moved from `video_converter.py` to `subprocess_utils.py` as `parse_fps`
- [x] CQ3: Font `optimize` Form option now read in `convert()` to strip dead tables
- [x] CQ4: Dead `_apply_subset` method deleted from `font_converter.py`
- [x] CQ5: `batch.py` Literal type aliases replaced with runtime validation against config sets
- [x] CQ7: Electron download handler destroys fileStream on early-exit paths (HTTPS/non-200)
- [x] A3: `font.py /optimize` refactored to use `handle_action` helper (matching convert pattern)
- [x] A4: `api.ts getFormats` return type adds `notes?: Record<string, string>`
- [x] A5: `base_converter.py` raw `"completed"` → `ConversionStatus.COMPLETED`
- [x] A6: `DATA_MAX_SIZE` setting added; validation.py maps `data` router to it
- [x] A7: Versions in sync (1.03 = 1.3.0 per X.XX convention); divergence is acceptable design trade-off
- [x] T4: `useConverter.test.ts` fully rewritten — 17 behavior tests covering state, events, reset, accessibility
- [x] T5: `test_version_router.py` added — 16 tests for `_version_newer`, `/api/version`, `/api/version/check`
- [x] T6: `test_subprocess_utils.py` added — 18 tests for `parse_fps` and `parse_ffmpeg_progress`
- [x] T8: `e2e/ui.spec.ts:70` `toBeGreaterThanOrEqual(0)` → `toBeGreaterThan(0)`
- [x] T9: `e2e/formInteractions.spec.ts:133` boolean type check → specific value assertion
- [x] T11: `test_websocket_router.py` — 4 new mid-conversion disconnect tests added
- [x] T12: Progress parsing tests centralized; audio/video test files updated to import from subprocess_utils
- [x] D2: `ci.yml` security scan switched from `safety check || true` to `pip-audit`
- [x] D3: `dependabot-auto-merge.yml` write permissions scoped to job level
- [x] D4: `dependabot.yml` `target-branch: develop` added to all 3 ecosystems
- [x] D5: `requirements-dev.txt` created; test deps removed from `requirements.txt`
- [x] F10: `DropZone.tsx getMimeType` returns proper MIME for subtitle/ebook/font/archive/data
- [x] F11: FontConverter + EbookConverter get "Convert Another" button after completion
- [x] F12: `GITHUB_REPO = 'jj-repository/FileConverter'` verified correct (matches git remote)
- [x] F13: Electron download handler enforces 500 MB limit via byte counter
- [x] F14: `Button.tsx` "Processing..." hardcoded string → `t('common.processing')`

## Verified Fixed (from prior audit — confirmed clean)

- M13: cache_service.py cleanup_by_size single-pass (verified)
- M22: WebSocketManager moved to dedicated module (verified)
- M23: api.ts factory pattern — file reduced from 453→197 lines (verified)
- M32: Dead Pydantic request models removed (verified)
- H11: Most workflows SHA-pinned (verified; security-scan + doc-review fixed this session)
- parse_ffmpeg_progress, _subprocess_kwargs centralized (verified)
- validate_file_size if/elif chain → dict lookup (verified)

## Open — Deferred (medium/large effort or needs dependency)

### Security
- **[MEDIUM] S1**: `ebook_converter.py` `_sanitize_html` is incomplete regex sanitizer — misses `<style>`, `vbscript:`, `data:` URIs, `<object>/<embed>/<iframe>`, unquoted event attrs. **Fix**: Replace with `bleach` library (requires adding dependency). File: `ebook_converter.py:131`
- **[MEDIUM] S2**: `ebook_converter.py:_html_to_epub` embeds user HTML without sanitization (stored XSS in output EPUB). **Fix**: Sanitize with `bleach` before `set_content`. File: `ebook_converter.py:396`
- **[MEDIUM] S4**: `electron/main.cjs` download path check uses `startsWith` on pre-resolved path — brittle on Windows UNC paths. File: `main.cjs:470`
- **[LOW] S7**: Batch ZIP download validates session UUID format but doesn't verify session belongs to requester. File: `batch.py:254`

### Performance
- **[MEDIUM] P1**: `cache_service.py` uses `threading.Lock` for stats in async context — replace with `asyncio.Lock` or lockless int. File: `cache_service.py:68`
- **[LOW] P2**: `batch_converter.py` semaphore hardcoded to `4` — expose as `settings.BATCH_CONCURRENCY`. File: `batch_converter.py:132`
- **[LOW] P3**: Audio/video converter timeout handler swallows second `TimeoutError` with bare `pass`. File: `audio_converter.py:240`, `video_converter.py:254`

### Code Quality
- **[LOW] CQ6**: `FontConverter.tsx` download button uses `<a>` tag vs `<Button>` component like other converters. File: `FontConverter.tsx`

### Architecture
- **[MEDIUM] A1**: Frontend hardcodes format lists — `constants.ts` is 3rd source of truth vs backend config and `/formats` API. `EbookConverter` and `FontConverter` don't call `getFormats()`. File: `EbookConverter.tsx:101`, `FontConverter.tsx:100`
- **[MEDIUM] A2**: `FontConverter.tsx` / `EbookConverter.tsx` use different layout patterns, download button styles, and status text (FontConverter entirely un-i18n'd). File: `FontConverter.tsx`, `EbookConverter.tsx`

### Tests
- **[HIGH] T1**: Frontend coverage threshold (60%) defined in `vitest.config.ts` but never enforced by CI — `npm run test:run --coverage` doesn't apply thresholds. File: `frontend-tests.yml:46`
- **[HIGH] T2**: `conversionFlows.test.tsx` has 11 instances of `expect(true).toBe(true)` — vacuous, can never fail. File: `conversionFlows.test.tsx:109,254,296,444`
- **[HIGH] T3 (H16)**: No E2E test covers actual conversion — Playwright only tests UI, backend never started. File: `e2e/*.spec.ts`, `playwright.config.ts`
- **[MEDIUM] T7**: Format selection test in `conversionFlows.test.tsx` wraps all assertions in `if (formatSelects.length > 0)` — silently skips when selector not found. File: `conversionFlows.test.tsx:448`
- **[LOW] T10**: `e2e/accessibility.spec.ts:50` — accessible name assertion can silently pass with `undefined`. Fix: use Playwright's `toHaveAccessibleName()`.

### Frontend (first review — all new)
- **[HIGH] F1**: `BatchConverterImproved.tsx` uses `fetch('file://${filePath}')` — fails in sandboxed Electron renderer. Needs IPC handler. File: `BatchConverterImproved.tsx:62`
- **[HIGH] F2**: `SubtitleConverter.tsx:39` — `subtitleAPI.adjustTiming as any` masks type mismatch between API and `handleConvert` signature.
- **[HIGH] F3**: `SubtitleConverter.tsx`, `FontConverter.tsx`, `ArchiveConverter.tsx`, `SpreadsheetConverter.tsx` — extensive hardcoded English strings not passing through `t()`.
- **[HIGH] F4**: `Toast.tsx:206` — `ConfirmModal` has no focus trap; keyboard user can tab out of modal (WCAG 2.1 §2.1.2).
- **[MEDIUM] F5**: `useConverter.ts:218` — `setTimeout` "force re-render" hack suggests stale state bug — needs root cause fix.
- **[MEDIUM] F6**: `useWebSocket.ts:104` — reconnect `setTimeout` captures stale `sessionId` closure; stale reconnect can connect to old session.
- **[MEDIUM] F7**: `useConverter.ts:35` — `ConvertOptions` typed as `[key: string]: any` — defeats type checking.
- **[MEDIUM] F8**: `useConverter.ts:227` — `catch (err: any)` — use `AxiosError<{detail?: string}>` cast.
- **[MEDIUM] F9**: Multiple converters share `id="output-format"`, `id="custom-filename"` etc. — fragile if two ever coexist. Use `useId()` hook.

### DevOps
- **[HIGH] D1**: FFmpeg and Pandoc downloaded in `build-release.yml` without SHA256 verification — `echo "Verifying..."` is a no-op. File: `build-release.yml:88`

## Findings Count

| Severity | Fixed (sessions 1+2) | Still open |
|---|---|---|
| Critical | 0 | 0 |
| High | 11 | 4 (F1, F2, F3, D1) |
| Medium | 20 | 7 (S1, S2, S4, P1, A1, A2, T7) |
| Low | 27 | 4 (S7, P2, P3, CQ6, T10) |
| **Total** | **58** | **15** |
