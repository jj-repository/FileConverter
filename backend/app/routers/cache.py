"""Cache management router for monitoring and controlling the conversion cache"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.services.cache_service import get_cache_service
from app.config import settings

router = APIRouter()


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


@router.post("/cleanup")
async def cleanup_cache() -> Dict[str, Any]:
    """
    Manually trigger cache cleanup

    Removes expired entries and enforces size limits
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


@router.delete("/clear")
async def clear_cache() -> Dict[str, str]:
    """
    Clear entire cache

    WARNING: This removes all cached conversion results
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
