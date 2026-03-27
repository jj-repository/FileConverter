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

## Recent Fixes (Jan 2026)
Audio converter stderr handling (deadlock prevention), symlink traversal protection, host 0.0.0.0→127.0.0.1, admin auth on /api/cache/info, JSON parsing errors in data converter, SVG temp file cleanup ✓

## Quality Standards
Target: reliable, secure, user-friendly file converter.
Do not optimize: conversion speed limited by ffmpeg/tools; architecture is appropriate.
