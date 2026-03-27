# Security

## Backend
- Rate limiting (slowapi)
- CORS configuration
- Input validation on all endpoints
- Admin key auth for cache endpoints
- Symlink path traversal protection (archive extraction)
- JSON parsing error handling (data converter)

## Frontend (Electron)
- Context isolation, sandbox mode, no nodeIntegration
- CSP headers
- Localhost-only backend binding (127.0.0.1)

## Review (2026-01-10 — Production Ready)
Backend: path traversal, symlink protection, input validation, rate limiting, CORS, admin auth, subprocess stderr consumed, timeouts, JSON errors, file size limits ✓
Frontend: context isolation, sandbox, no nodeIntegration, localhost binding, TypeScript types complete, React structured, Toast notifications, i18n ✓
