# FileConverter - Security Audit and Improvements

## Executive Summary

Comprehensive code review completed on 2025-12-29. Found **3 CRITICAL**, **5 HIGH**, and **12 MEDIUM** priority issues.

---

## CRITICAL SECURITY VULNERABILITIES (Fix Immediately)

### 1. **Arbitrary Code Execution via eval()** 🔴
**File:** `backend/app/utils/file_handler.py:73`
**Severity:** CRITICAL
**Issue:** Using `eval()` on FFprobe output (FPS parsing)
```python
"fps": eval(video_stream.get("r_frame_rate", "0/1"))
```
**Risk:** Malicious video file could execute arbitrary Python code
**Fix:** Replace with safe fraction parsing

### 2. **Path Traversal in Download Endpoint** 🔴
**File:** `backend/app/routers/image.py:94-106` (and video, audio, document routers)
**Severity:** CRITICAL
**Issue:** No validation of filename parameter allows path traversal
```python
@router.get("/download/{filename}")
async def download_image(filename: str):
    file_path = settings.UPLOAD_DIR / filename  # ❌ No validation
```
**Risk:** Attacker can download arbitrary files: `/api/image/download/../../etc/passwd`
**Fix:** Validate filename has no path separators, is within UPLOAD_DIR

### 3. **Command Injection in FFmpeg/FFprobe Calls** 🔴
**Files:** `backend/app/services/video_converter.py`, `audio_converter.py`
**Severity:** CRITICAL
**Issue:** User-supplied codec, bitrate, resolution passed directly to subprocess
```python
codec = options.get('codec', 'libx264')  # ❌ No validation
cmd.extend(["-c:v", codec])
```
**Risk:** Injection of arbitrary FFmpeg flags or shell commands
**Fix:** Whitelist allowed codecs, bitrates, resolutions

---

## HIGH SECURITY ISSUES

### 4. **SSRF and Arbitrary File Write in Electron** 🟠
**File:** `frontend/electron/main.js:170-211`
**Severity:** HIGH
**Issue:** `download-file` IPC accepts arbitrary URLs and paths from renderer
```javascript
ipcMain.handle('download-file', async (event, { url, directory, filename }) => {
  const outputPath = path.join(directory, filename);  // ❌ No validation
  protocol.get(url, ...)  // ❌ No URL validation
```
**Risk:**
- SSRF: Download from internal/localhost URLs
- Path traversal: Write to arbitrary filesystem locations
- Download malicious files
**Fix:** Validate URL is http/https and external, sanitize paths

### 5. **Path Traversal in Electron show-item-in-folder** 🟠
**File:** `frontend/electron/main.js:164-166`
**Severity:** HIGH
**Issue:** No validation of filePath parameter
**Fix:** Validate path exists and is within allowed directories

### 6. **No Session Validation on Downloads** 🟠
**Files:** All router download endpoints
**Severity:** HIGH
**Issue:** Anyone with filename can download without session ownership check
**Fix:** Store session-to-file mapping, validate ownership

### 7. **No Rate Limiting** 🟠
**File:** Backend API
**Severity:** HIGH
**Issue:** No rate limiting on API endpoints
**Risk:** DoS attacks, resource exhaustion
**Fix:** Add rate limiting middleware (slowapi)

### 8. **Subprocess Timeout Missing** 🟠
**Files:** `utils/file_handler.py:56, 96`, `services/video_converter.py`
**Severity:** HIGH
**Issue:** FFmpeg/FFprobe calls can hang indefinitely
**Fix:** Add timeouts to all subprocess calls

---

## MEDIUM SECURITY/STABILITY ISSUES

### 9. **Weak Content Security Policy**
**File:** `frontend/electron/main.js:32`
**Issue:** CSP uses 'unsafe-inline' for scripts and styles
**Fix:** Remove unsafe-inline, use nonces or hashes

### 10. **MIME Type Not Detected**
**Files:** All download endpoints
**Issue:** Returns `application/octet-stream` instead of actual MIME type
**Fix:** Use `mimetypes` module or `python-magic`

### 11. **No Input Validation for Codec Options**
**Files:** Video/Audio converters
**Issue:** No whitelist for codecs, bitrates, resolutions
**Fix:** Define allowed values, validate against whitelist

### 12. **File Content Loaded Entirely in Memory**
**File:** `utils/file_handler.py:20`
**Issue:** `await upload_file.read()` loads entire file into RAM
**Fix:** Stream file to disk in chunks

### 13. **Bare Except Clauses**
**Files:** Multiple files use `except:` without type
**Issue:** Catches KeyboardInterrupt, SystemExit
**Fix:** Use specific exception types

### 14. **Imports Inside Functions**
**Files:** Multiple files import inside functions
**Issue:** Performance overhead, non-standard pattern
**Fix:** Move imports to top of file

### 15. **Unused ThreadPoolExecutor**
**File:** `services/video_converter.py:21`
**Issue:** Created but never used
**Fix:** Remove or use for CPU-bound operations

### 16. **Duplicate Batch Converter Components**
**Files:** `BatchConverter.tsx`, `BatchConverterImproved.tsx`
**Issue:** Two implementations, unclear which is used
**Fix:** Remove old version, keep improved

### 17. **Hard-coded Magic Numbers**
**Files:** Throughout codebase
**Issue:** 500MB, 100MB, 100 files, 1 hour - no constants
**Fix:** Move to configuration constants

### 18. **No Structured Logging**
**Files:** All files use print() or console.log()
**Issue:** No log levels, timestamps, structured data
**Fix:** Use Python logging module, structured format

### 19. **Missing Process Cleanup**
**Files:** Video/Audio converters
**Issue:** Subprocess not killed on cancellation/error
**Fix:** Add try/finally with process.kill()

### 20. **Error Messages Leak Implementation Details**
**Files:** All routers
**Issue:** Detailed error messages expose paths, stack traces
**Fix:** Generic user messages, detailed logs server-side

---

## CODE QUALITY IMPROVEMENTS

### Performance
- [ ] Stream large file uploads instead of buffering
- [ ] Add caching for format validation
- [ ] Use connection pooling for database (if added)
- [ ] Optimize image conversion for large batches

### Testing
- [ ] Add unit tests for converters
- [ ] Add integration tests for API endpoints
- [ ] Add security tests (path traversal, injection)
- [ ] Add load/stress tests

### Documentation
- [ ] Add docstrings to all functions
- [ ] Document security considerations
- [ ] Add API documentation (OpenAPI/Swagger)
- [ ] Add architecture diagrams

### Monitoring
- [ ] Add health check endpoint
- [ ] Add metrics collection (Prometheus)
- [ ] Add request tracing
- [ ] Add error tracking (Sentry)

---

## IMPLEMENTATION PRIORITY

### Phase 1: Critical Fixes (DO NOW)
1. Fix eval() vulnerability (5 min)
2. Fix path traversal in downloads (15 min)
3. Fix command injection (30 min)
4. Fix Electron SSRF/path traversal (20 min)
**Total: ~70 minutes**

### Phase 2: High Priority (NEXT)
5. Add session validation (30 min)
6. Add rate limiting (20 min)
7. Add subprocess timeouts (15 min)
8. Fix bare excepts (15 min)
**Total: ~80 minutes**

### Phase 3: Medium Priority (SOON)
9. Improve CSP (10 min)
10. Add proper MIME types (10 min)
11. Add input validation whitelists (30 min)
12. Stream file uploads (30 min)
13. Add structured logging (30 min)
**Total: ~110 minutes**

### Phase 4: Code Quality (LATER)
14. Remove duplicates (10 min)
15. Extract magic numbers (20 min)
16. Move imports to top (15 min)
17. Add process cleanup (20 min)
18. Improve error messages (20 min)
**Total: ~85 minutes**

---

## TESTING PLAN

After implementing fixes, test:
1. Path traversal attempts (expect 400/403)
2. Command injection attempts (expect sanitization)
3. Large file uploads (expect streaming)
4. Concurrent requests (expect rate limiting)
5. Invalid input (expect validation errors)
6. Process timeouts (expect graceful failure)
7. Download without session (expect 403)
8. All converters still work correctly

---

## RISK ASSESSMENT

**Before Fixes:**
- **Overall Risk:** CRITICAL
- **Public Exposure Risk:** CRITICAL (if exposed to internet)
- **Local Usage Risk:** HIGH (malicious files can execute code)

**After Phase 1 Fixes:**
- **Overall Risk:** MEDIUM
- **Public Exposure Risk:** HIGH (still needs rate limiting, session validation)
- **Local Usage Risk:** LOW

**After All Fixes:**
- **Overall Risk:** LOW
- **Public Exposure Risk:** MEDIUM (always some risk with public APIs)
- **Local Usage Risk:** VERY LOW

---

## COMPLIANCE NOTES

- OWASP Top 10: Currently violates A03 (Injection), A01 (Broken Access Control), A05 (Security Misconfiguration)
- After fixes: Addresses all critical OWASP issues
- CWE-78 (OS Command Injection): FIXED
- CWE-22 (Path Traversal): FIXED
- CWE-502 (Deserialization of Untrusted Data): FIXED (eval removal)
