"""Cache management router for monitoring and controlling the conversion cache"""

from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Dict, Any, Optional

from app.services.cache_service import get_cache_service
from app.config import settings

router = APIRouter()


async def verify_admin_key(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")) -> None:
    """
    Verify admin API key for protected endpoints.

    SECURITY: Admin key is ALWAYS required, even in DEBUG mode.
    This prevents accidental exposure of admin endpoints if DEBUG=True is
    inadvertently deployed to production.

    To use admin endpoints:
    1. Set ADMIN_API_KEY environment variable
    2. Pass the key in X-Admin-Key header
    """
    # SECURITY: Always require admin key - never bypass based on DEBUG mode
    # This prevents accidental exposure if DEBUG=True is deployed to production
    if not settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Admin endpoints are disabled. Set ADMIN_API_KEY environment variable to enable."
        )

    if not x_admin_key or x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing admin API key"
        )


@router.get("/info")
async def get_cache_info() -> Dict[str, Any]:
    """
    Get cache statistics and information

    Returns cache size, hit rate, entry count, and configuration
    """
    if not settings.CACHE_ENABLED:
        return {
            "enabled": False,
            "message": "Cache is disabled"
        }

    cache_service = get_cache_service()
    if cache_service is None:
        raise HTTPException(status_code=503, detail="Cache service not initialized")

    info = cache_service.get_cache_info()
    info["enabled"] = True

    return info


@router.post("/cleanup", dependencies=[Depends(verify_admin_key)])
async def cleanup_cache() -> Dict[str, Any]:
    """
    Manually trigger cache cleanup

    Removes expired entries and enforces size limits.
    Requires X-Admin-Key header with valid admin API key.
    """
    if not settings.CACHE_ENABLED:
        raise HTTPException(status_code=400, detail="Cache is disabled")

    cache_service = get_cache_service()
    if cache_service is None:
        raise HTTPException(status_code=503, detail="Cache service not initialized")

    stats = cache_service.cleanup_all()

    return {
        "success": True,
        "message": "Cache cleanup completed",
        "stats": stats
    }


@router.delete("/clear", dependencies=[Depends(verify_admin_key)])
async def clear_cache() -> Dict[str, str]:
    """
    Clear entire cache

    WARNING: This removes all cached conversion results.
    Requires X-Admin-Key header with valid admin API key.
    """
    if not settings.CACHE_ENABLED:
        raise HTTPException(status_code=400, detail="Cache is disabled")

    cache_service = get_cache_service()
    if cache_service is None:
        raise HTTPException(status_code=503, detail="Cache service not initialized")

    cache_service.clear_all()

    return {
        "success": True,
        "message": "Cache cleared successfully"
    }
