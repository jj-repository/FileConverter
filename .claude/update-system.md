# Update System

**Status:** Partially implemented — startup check done, full UI integration pending.

## Implemented
- Update check on startup (main.js), 10s timeout
- Version comparison, dialog with Download/Later

## Needed
- IPC handlers: `check-for-updates`, `download-update`
- React UpdateContext/hook for update state
- Settings storage for `auto_check_updates`
- Toast notifications for updates

Follow **TextCompare pattern** for Electron; adapt for React frontend.
