#!/usr/bin/env python3
"""
Entry point for the FileConverter backend server.
This script is designed to be bundled with PyInstaller.
"""

import logging
import logging.handlers
import os
import sys
import traceback
from pathlib import Path

import uvicorn


def configure_file_logging(log_dir: str) -> None:
    """Attach a rotating file handler to the root logger."""
    path = Path(log_dir)
    path.mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        path / "backend.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(fmt)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logging.getLogger(name).setLevel(logging.INFO)


def parse_arg(argv, flag):
    """Return value for --flag X, or None."""
    for i, a in enumerate(argv):
        if a == flag and i + 1 < len(argv):
            return argv[i + 1]
    return None


def main():
    """Run the FastAPI server."""
    argv = sys.argv[1:]

    if "--smoke-test" in argv:
        # Import-only check used by the build pipeline to verify the frozen
        # bundle contains every module the app touches at startup. Exits 0
        # on success, non-zero with traceback on any ImportError. Prints are
        # flushed so CI logs show progress even if a later import hangs.
        print("smoke-test: importing app.main", flush=True)
        import app.main  # noqa: F401

        print("smoke-test: imports OK", flush=True)
        return

    port = int(parse_arg(argv, "--port") or 8000)
    host = parse_arg(argv, "--host") or "127.0.0.1"
    log_dir = parse_arg(argv, "--log-dir") or os.environ.get("FC_LOG_DIR")

    if log_dir:
        try:
            configure_file_logging(log_dir)
            logging.getLogger(__name__).info(
                "Backend starting: host=%s port=%d log_dir=%s", host, port, log_dir
            )
        except Exception as e:  # noqa: BLE001 — log setup must not crash startup
            sys.stderr.write(f"log-setup failed: {e}\n")

    try:
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            log_level="info",
        )
    except Exception:
        logging.getLogger(__name__).critical(
            "Backend crashed during startup:\n%s", traceback.format_exc()
        )
        raise


if __name__ == "__main__":
    main()
