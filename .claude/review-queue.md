# FileConverter Audit Review Queue

Generated: 2026-04-17
Agents: code-quality, security, performance, test-quality, architecture, frontend-specialist (first run), devops
Prior audit: 2026-04-05

## Fixed This Session (22 items)

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
- **[MEDIUM] S3**: `electron/main.cjs` CSP `style-src` includes `'unsafe-inline'` unconditionally (should be dev-only like `script-src`). File: `main.cjs:240`
- **[MEDIUM] S4**: `electron/main.cjs` download path check uses `startsWith` on pre-resolved path — brittle on Windows UNC paths. File: `main.cjs:470`
- **[LOW] S5**: SSRF blocklist in Electron incomplete — octal/hex IPs, IPv6-mapped v4, `fc::/7` prefix check is string-based not parsed. File: `main.cjs:434`
- **[LOW] S6**: CORS config doesn't validate against wildcard `"*"` when `allow_credentials=True`. File: `main.py:154`
- **[LOW] S7**: Batch ZIP download validates session UUID format but doesn't verify session belongs to requester. File: `batch.py:254`
- **[LOW] S8**: WebSocket origin check allows any `file://` URL, not just the Electron app origin. File: `websocket.py:43`

### Performance
- **[MEDIUM] P1**: `cache_service.py` uses `threading.Lock` for stats in async context — replace with `asyncio.Lock` or lockless int. File: `cache_service.py:68`
- **[LOW] P2**: `batch_converter.py` semaphore hardcoded to `4` — expose as `settings.BATCH_CONCURRENCY`. File: `batch_converter.py:132`
- **[LOW] P3**: Audio/video converter timeout handler swallows second `TimeoutError` with bare `pass`. File: `audio_converter.py:240`, `video_converter.py:254`
- **[LOW] P4**: `useWebSocket.ts` reconnect reads `reconnectAttemptRef.current` in render return — always stale. File: `useWebSocket.ts:153`

### Code Quality
- **[MEDIUM] CQ1**: `base_converter.py` still directly holds `WebSocketManager` — SoC partially improved by module split but coupling remains. File: `base_converter.py:52`
- **[LOW] CQ2**: `_parse_fps` duplicated between `video_converter.py` and (removed) `file_handler.py` — move to `subprocess_utils`. File: `video_converter.py:350`
- **[LOW] CQ3**: Font `optimize` option accepted via Form but never read in `convert()`. File: `font_converter.py`
- **[LOW] CQ4**: Font `_apply_subset` dead method — `Options` object created but never passed to `Subsetter`, method never called. File: `font_converter.py:106`
- **[LOW] CQ5**: `batch.py` `Literal` type aliases duplicate config whitelist sets. File: `batch.py:42`
- **[LOW] CQ6**: `FontConverter.tsx` `window.electron` guard inconsistency vs `EbookConverter` (partially fixed this session — 3/3 guards now `.isElectron`; download button uses `<a>` not `<Button>` like other converters). File: `FontConverter.tsx`
- **[LOW] CQ7**: `electron/main.cjs` file stream not destroyed on early-exit paths (HTTPS check, non-200 response). File: `main.cjs:475`

### Architecture
- **[MEDIUM] A1**: Frontend hardcodes format lists — `constants.ts` is 3rd source of truth vs backend config and `/formats` API. `EbookConverter` and `FontConverter` don't call `getFormats()`. File: `EbookConverter.tsx:101`, `FontConverter.tsx:100`
- **[MEDIUM] A2**: `FontConverter.tsx` / `EbookConverter.tsx` use different layout patterns, download button styles, and status text (FontConverter entirely un-i18n'd). File: `FontConverter.tsx`, `EbookConverter.tsx`
- **[MEDIUM] A3**: `font.py` `/optimize` endpoint uses bespoke try/except instead of `handle_convert` helper pattern. File: `font.py:58`
- **[LOW] A4**: `/formats` response shape inconsistent — ebook/font add `notes` key, others don't; TypeScript type misses `notes`. File: `ebook.py:65`, `font.py:118`
- **[LOW] A5**: `base_converter.py` uses raw string `"completed"` instead of `ConversionStatus.COMPLETED`. File: `base_converter.py:113`
- **[LOW] A6**: `data` router maps to `DOCUMENT_MAX_SIZE` — no dedicated `DATA_MAX_SIZE` setting. File: `validation.py:108`
- **[LOW] A7**: Version string exists in `backend/app/__init__.py` (`"1.03"`) and `frontend/package.json` (`"1.3.0"`) with no shared source of truth.

### Tests
- **[HIGH] T1**: Frontend coverage threshold (60%) defined in `vitest.config.ts` but never enforced by CI — `npm run test:run --coverage` doesn't apply thresholds. File: `frontend-tests.yml:46`
- **[HIGH] T2**: `conversionFlows.test.tsx` has 11 instances of `expect(true).toBe(true)` — vacuous, can never fail. File: `conversionFlows.test.tsx:109,254,296,444`
- **[HIGH] T3 (H16)**: No E2E test covers actual conversion — Playwright only tests UI, backend never started. File: `e2e/*.spec.ts`, `playwright.config.ts`
- **[MEDIUM] T4**: `useConverter.test.ts` only checks that hook functions exist — no behavior, state transitions, or error handling tested. File: `useConverter.test.ts`
- **[MEDIUM] T5**: `version.py` router has zero test coverage (`_version_newer`, network error path, rate limit). File: `app/routers/version.py`
- **[MEDIUM] T6**: `subprocess_utils.py` has no direct unit tests; Windows `CREATE_NO_WINDOW` branch untestable on Linux CI. File: `app/utils/subprocess_utils.py`
- **[MEDIUM] T7**: Format selection test in `conversionFlows.test.tsx` wraps all assertions in `if (formatSelects.length > 0)` — silently skips when selector not found. File: `conversionFlows.test.tsx:448`
- **[LOW] T8**: `e2e/ui.spec.ts:70` — `toBeGreaterThanOrEqual(0)` always passes (accepts 0 elements). Fix: `toBeGreaterThan(0)`. File: `e2e/ui.spec.ts:70`
- **[LOW] T9**: `e2e/formInteractions.spec.ts:133` — `typeof boolean` always true. Fix: assert specific boolean value.
- **[LOW] T10**: `e2e/accessibility.spec.ts:50` — accessible name assertion can silently pass with `undefined`. Fix: use Playwright's `toHaveAccessibleName()`.
- **[LOW] T11**: `test_websocket_router.py` missing tests for mid-conversion disconnect and invalid session rejection.
- **[LOW] T12**: Progress parsing test logic duplicated across `test_video_converter.py` and `test_audio_converter.py` — should live in `test_subprocess_utils.py`.

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
- **[LOW] F10**: `DropZone.tsx:112` — `getMimeType` returns `'*/*'` for subtitle/ebook/font/archive/data types.
- **[LOW] F11**: `EbookConverter.tsx` + `FontConverter.tsx` don't show "Convert Another" / Reset after completion (inconsistent UX vs 8 other converters).
- **[LOW] F12**: `main.cjs:16` — `GITHUB_REPO = 'jj-repository/FileConverter'` may be a placeholder — verify actual repo name.
- **[LOW] F13**: `main.cjs:475` — download handler pipes response with no `Content-Length` / size limit.
- **[LOW] F14**: `Button.tsx:50` — `"Processing..."` hardcoded, not translated.

### DevOps
- **[HIGH] D1**: FFmpeg and Pandoc downloaded in `build-release.yml` without SHA256 verification — `echo "Verifying..."` is a no-op. File: `build-release.yml:88`
- **[MEDIUM] D2**: `ci.yml:213` — `safety check --json || true` double-suppressed AND silently skips when no API key. Switch to `pip-audit` or `safety scan`.
- **[MEDIUM] D3**: `dependabot-auto-merge.yml` triggers on ALL PRs (not just Dependabot ones by branch); auto-merges all minor updates without package-level scope restriction.
- **[LOW] D4**: `dependabot.yml` missing `target-branch: develop`; `requirements-dev.txt` not tracked (pending split of test deps).
- **[LOW] D5**: `backend/requirements.txt` still contains test deps (`pytest`, `pytest-asyncio`, `pytest-cov`, `httpx`) — split to `requirements-dev.txt`.

## Findings Count

| Severity | Fixed this session | Still open |
|---|---|---|
| Critical | 0 | 0 |
| High | 8 | 7 |
| Medium | 11 | 15 |
| Low | 9 | 23 |
| **Total** | **28** | **45** |
