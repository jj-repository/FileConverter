#!/usr/bin/env python3
"""
Entry point for the FileConverter backend server.
This script is designed to be bundled with PyInstaller.
"""
import sys
import os
import uvicorn


def main():
    """Run the FastAPI server."""
    # Get port from command line args or use default
    # Default to localhost for security - use --host 0.0.0.0 to accept external connections
    port = 8000
    host = "127.0.0.1"

    # Parse command line arguments
    for i, arg in enumerate(sys.argv[1:]):
        if arg == '--port' and i + 1 < len(sys.argv[1:]):
            port = int(sys.argv[i + 2])
        elif arg == '--host' and i + 1 < len(sys.argv[1:]):
            host = sys.argv[i + 2]

    # Run the server
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
