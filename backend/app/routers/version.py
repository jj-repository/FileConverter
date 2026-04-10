"""Version and update checking router."""

import asyncio
import json
import logging
import urllib.error
import urllib.request

from fastapi import APIRouter, Depends

from app.utils.websocket_security import check_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()

# Version from FastAPI app (set in main.py), with fallback
from app import __version__ as APP_VERSION

GITHUB_REPO = "jj-repository/FileConverter"
GITHUB_RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"
GITHUB_API_LATEST = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def _version_newer(latest: str, current: str) -> bool:
    """Compare version strings to check if latest is newer than current."""
    try:
        latest_parts = tuple(map(int, latest.split(".")))
        current_parts = tuple(map(int, current.split(".")))
        return latest_parts > current_parts
    except (ValueError, AttributeError):
        return False


@router.get("")
async def get_version():
    """Get current application version."""
    return {
        "version": APP_VERSION,
        "github_repo": GITHUB_REPO,
        "releases_url": GITHUB_RELEASES_URL,
    }


@router.get("/check", dependencies=[Depends(check_rate_limit)])
async def check_for_updates():
    """Check GitHub for available updates."""
    try:
        request = urllib.request.Request(
            GITHUB_API_LATEST, headers={"User-Agent": f"FileConverter/{APP_VERSION}"}
        )

        def _fetch():
            with urllib.request.urlopen(request, timeout=10) as resp:
                return json.loads(resp.read().decode())

        data = await asyncio.to_thread(_fetch)

        latest_version = data.get("tag_name", "").lstrip("v")

        if not latest_version:
            return {
                "error": "No version tag found in release",
                "current_version": APP_VERSION,
            }

        update_available = _version_newer(latest_version, APP_VERSION)

        return {
            "current_version": APP_VERSION,
            "latest_version": latest_version,
            "update_available": update_available,
            "releases_url": GITHUB_RELEASES_URL,
            "release_notes": data.get("body", ""),
            "published_at": data.get("published_at", ""),
        }

    except urllib.error.URLError as e:
        logger.error(f"Network error checking for updates: {e}")
        return {"error": f"Network error: {e}", "current_version": APP_VERSION}
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")
        return {"error": str(e), "current_version": APP_VERSION}
