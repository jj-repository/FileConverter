"""
WebSocket security utilities for rate limiting and session validation
"""

import time
from collections import defaultdict
from typing import Dict, List, Tuple
import logging
from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)


class WebSocketRateLimiter:
    """Rate limiter for WebSocket connections"""

    def __init__(self, max_connections_per_ip: int = 10, time_window: int = 60):
        """
        Initialize rate limiter

        Args:
            max_connections_per_ip: Maximum connections allowed per IP in time window
            time_window: Time window in seconds for rate limiting
        """
        self.max_connections_per_ip = max_connections_per_ip
        self.time_window = time_window
        self.connections: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, ip_address: str) -> Tuple[bool, str]:
        """
        Check if connection from IP is allowed

        Args:
            ip_address: Client IP address

        Returns:
            Tuple of (is_allowed, reason_if_not_allowed)
        """
        current_time = time.time()

        # Clean up old connection timestamps
        self.connections[ip_address] = [
            timestamp
            for timestamp in self.connections[ip_address]
            if current_time - timestamp < self.time_window
        ]

        # Check if limit exceeded
        if len(self.connections[ip_address]) >= self.max_connections_per_ip:
            logger.warning(f"Rate limit exceeded for IP: {ip_address}")
            return False, f"Too many connections. Maximum {self.max_connections_per_ip} connections per {self.time_window} seconds."

        # Record new connection
        self.connections[ip_address].append(current_time)
        return True, ""

    def remove_connection(self, ip_address: str):
        """Remove one connection from the count for an IP"""
        current_time = time.time()
        if ip_address in self.connections and self.connections[ip_address]:
            # Filter for valid timestamps first
            filtered = [
                timestamp
                for timestamp in self.connections[ip_address]
                if current_time - timestamp < self.time_window
            ]
            # Remove oldest connection if multiple remain, otherwise clean up
            if len(filtered) > 1:
                self.connections[ip_address] = filtered[1:]
            else:
                # Clean up empty or single-entry lists to prevent memory leaks
                del self.connections[ip_address]


class SessionValidator:
    """Validates WebSocket session IDs"""

    def __init__(self):
        """Initialize session validator"""
        self.active_sessions: Dict[str, float] = {}
        self.session_timeout = 3600  # 1 hour

    def register_session(self, session_id: str):
        """Register a new conversion session"""
        self.active_sessions[session_id] = time.time()
        logger.debug(f"Registered session: {session_id}")

    def is_valid_session(self, session_id: str) -> Tuple[bool, str]:
        """
        Check if session ID is valid

        Args:
            session_id: Session ID to validate

        Returns:
            Tuple of (is_valid, reason_if_not_valid)
        """
        # Clean up expired sessions
        current_time = time.time()
        expired_sessions = [
            sid
            for sid, timestamp in self.active_sessions.items()
            if current_time - timestamp > self.session_timeout
        ]
        for sid in expired_sessions:
            del self.active_sessions[sid]
            logger.debug(f"Expired session removed: {sid}")

        # Check if session exists
        if session_id not in self.active_sessions:
            logger.warning(f"Invalid session ID attempted: {session_id}")
            return False, "Invalid or expired session ID"

        return True, ""

    def remove_session(self, session_id: str):
        """Remove a session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.debug(f"Session removed: {session_id}")


class ConversionRateLimiter:
    """
    Rate limiter for conversion endpoints.

    Protects against DOS attacks by limiting the number of conversion requests
    per IP address within a time window.
    """

    def __init__(self, max_requests_per_ip: int = 60, time_window: int = 60):
        """
        Initialize rate limiter

        Args:
            max_requests_per_ip: Maximum conversion requests allowed per IP in time window (default: 60/min)
            time_window: Time window in seconds for rate limiting
        """
        self.max_requests_per_ip = max_requests_per_ip
        self.time_window = time_window
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self._enabled = True  # Can be disabled for testing

    def reset(self) -> None:
        """Reset all rate limiting state. Useful for testing."""
        self.requests.clear()

    def disable(self) -> None:
        """Disable rate limiting. Useful for testing."""
        self._enabled = False

    def enable(self) -> None:
        """Enable rate limiting."""
        self._enabled = True

    def is_allowed(self, ip_address: str) -> Tuple[bool, str]:
        """
        Check if conversion request from IP is allowed

        Args:
            ip_address: Client IP address

        Returns:
            Tuple of (is_allowed, reason_if_not_allowed)
        """
        # Allow all requests if rate limiting is disabled
        if not self._enabled:
            return True, ""

        current_time = time.time()

        # Clean up old request timestamps
        self.requests[ip_address] = [
            timestamp
            for timestamp in self.requests[ip_address]
            if current_time - timestamp < self.time_window
        ]

        # Check if limit exceeded
        if len(self.requests[ip_address]) >= self.max_requests_per_ip:
            logger.warning(f"Conversion rate limit exceeded for IP: {ip_address}")
            return False, f"Too many conversion requests. Maximum {self.max_requests_per_ip} requests per {self.time_window} seconds. Please try again later."

        # Record new request
        self.requests[ip_address].append(current_time)
        return True, ""

    def get_remaining_requests(self, ip_address: str) -> int:
        """Get remaining requests for an IP within current time window"""
        current_time = time.time()
        valid_requests = [
            timestamp
            for timestamp in self.requests.get(ip_address, [])
            if current_time - timestamp < self.time_window
        ]
        return max(0, self.max_requests_per_ip - len(valid_requests))


# Global instances
rate_limiter = WebSocketRateLimiter(max_connections_per_ip=10, time_window=60)
session_validator = SessionValidator()
conversion_rate_limiter = ConversionRateLimiter(max_requests_per_ip=30, time_window=60)


async def check_rate_limit(request: Request) -> None:
    """
    FastAPI dependency to check conversion rate limit.

    Add this to conversion endpoints using Depends(check_rate_limit).

    Raises:
        HTTPException: 429 Too Many Requests if rate limit exceeded
    """
    # Get client IP from request
    # Check X-Forwarded-For header for proxied requests, fall back to direct client
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain (original client)
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    is_allowed, reason = conversion_rate_limiter.is_allowed(client_ip)

    if not is_allowed:
        # Add Retry-After header to inform client when they can retry
        raise HTTPException(
            status_code=429,
            detail=reason,
            headers={"Retry-After": str(conversion_rate_limiter.time_window)}
        )
