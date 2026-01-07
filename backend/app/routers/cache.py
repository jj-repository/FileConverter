"""Cache management router for monitoring and controlling the conversion cache"""

import logging
from datetime import datetime, UTC
from fastapi import APIRouter, HTTPException, Header, Depends, Request
from typing import Dict, Any, Optional

from app.services.cache_service import get_cache_service
from app.config import settings
from app.utils.websocket_security import admin_auth_rate_limiter, get_client_ip

router = APIRouter()
logger = logging.getLogger(__name__)


def _audit_log(
    action: str,
    client_ip: str,
    success: bool,
    details: Optional[str] = None
) -> None:
    """
    Log admin operations for security audit trail.

    All admin endpoint access is logged with timestamp, IP, action, and result.
    """
    timestamp = datetime.now(UTC).isoformat()
    status = "SUCCESS" if success else "FAILED"
    log_msg = f"ADMIN_AUDIT [{timestamp}] IP={client_ip} action={action} status={status}"
    if details:
        log_msg += f" details={details}"

    if success:
        logger.info(log_msg)
    else:
        logger.warning(log_msg)


async def verify_admin_key(
    request: Request,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")
) -> str:
    """
    Verify admin API key for protected endpoints.

    SECURITY:
    - Admin key is ALWAYS required, even in DEBUG mode
    - Rate limits failed authentication attempts (5 failures = 5 minute lockout)
    - Logs all authentication attempts for audit trail

    To use admin endpoints:
    1. Set ADMIN_API_KEY environment variable
    2. Pass the key in X-Admin-Key header

    Returns:
        The client IP for use in audit logging
    """
    client_ip = get_client_ip(request)

    # Check for lockout before processing
    is_locked, remaining = admin_auth_rate_limiter.is_locked_out(client_ip)
    if is_locked:
        _audit_log("AUTH_ATTEMPT", client_ip, False, f"locked_out remaining={remaining}s")
        raise HTTPException(
            status_code=429,
            detail=f"Too many failed attempts. Try again in {remaining} seconds.",
            headers={"Retry-After": str(remaining)}
        )

    # SECURITY: Always require admin key - never bypass based on DEBUG mode
    if not settings.ADMIN_API_KEY:
        _audit_log("AUTH_ATTEMPT", client_ip, False, "admin_key_not_configured")
        raise HTTPException(
            status_code=403,
            detail="Admin endpoints are disabled. Set ADMIN_API_KEY environment variable to enable."
        )

    if not x_admin_key or x_admin_key != settings.ADMIN_API_KEY:
        # Record failed attempt
        admin_auth_rate_limiter.record_failure(client_ip)
        _audit_log("AUTH_ATTEMPT", client_ip, False, "invalid_key")
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing admin API key"
        )

    # Successful auth - clear any previous failures
    admin_auth_rate_limiter.clear_failures(client_ip)
    _audit_log("AUTH_ATTEMPT", client_ip, True, None)

    return client_ip


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
async def cleanup_cache(client_ip: str = Depends(verify_admin_key)) -> Dict[str, Any]:
    """
    Manually trigger cache cleanup

    Removes expired entries and enforces size limits.
    Requires X-Admin-Key header with valid admin API key.
    """
    if not settings.CACHE_ENABLED:
        _audit_log("CACHE_CLEANUP", client_ip, False, "cache_disabled")
        raise HTTPException(status_code=400, detail="Cache is disabled")

    cache_service = get_cache_service()
    if cache_service is None:
        _audit_log("CACHE_CLEANUP", client_ip, False, "service_not_initialized")
        raise HTTPException(status_code=503, detail="Cache service not initialized")

    stats = cache_service.cleanup_all()
    _audit_log("CACHE_CLEANUP", client_ip, True, f"removed={stats.get('removed', 0)}")

    return {
        "success": True,
        "message": "Cache cleanup completed",
        "stats": stats
    }


@router.delete("/clear")
async def clear_cache(client_ip: str = Depends(verify_admin_key)) -> Dict[str, str]:
    """
    Clear entire cache

    WARNING: This removes all cached conversion results.
    Requires X-Admin-Key header with valid admin API key.
    """
    if not settings.CACHE_ENABLED:
        _audit_log("CACHE_CLEAR", client_ip, False, "cache_disabled")
        raise HTTPException(status_code=400, detail="Cache is disabled")

    cache_service = get_cache_service()
    if cache_service is None:
        _audit_log("CACHE_CLEAR", client_ip, False, "service_not_initialized")
        raise HTTPException(status_code=503, detail="Cache service not initialized")

    cache_service.clear_all()
    _audit_log("CACHE_CLEAR", client_ip, True, "all_entries_removed")

    return {
        "success": True,
        "message": "Cache cleared successfully"
    }
