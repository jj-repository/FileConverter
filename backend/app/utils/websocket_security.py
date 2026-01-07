"""
WebSocket security utilities for rate limiting and session validation
"""

import time
import ipaddress
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Set
import logging
from fastapi import HTTPException, Request

from app.config import settings

logger = logging.getLogger(__name__)


class TrustedProxyValidator:
    """
    Validates that X-Forwarded-For headers come from trusted proxy sources.

    SECURITY: Only trusts X-Forwarded-For header if the direct client IP
    is in the configured trusted proxy list.
    """

    def __init__(self):
        self._trusted_networks: Set[ipaddress.IPv4Network | ipaddress.IPv6Network] = set()
        self._load_trusted_proxies()

    def _load_trusted_proxies(self) -> None:
        """Load trusted proxies from configuration."""
        if not settings.TRUSTED_PROXIES:
            return

        for proxy in settings.TRUSTED_PROXIES.split(","):
            proxy = proxy.strip()
            if not proxy:
                continue
            try:
                # Try parsing as a network (CIDR notation)
                if "/" in proxy:
                    network = ipaddress.ip_network(proxy, strict=False)
                else:
                    # Single IP - convert to /32 or /128 network
                    ip = ipaddress.ip_address(proxy)
                    if isinstance(ip, ipaddress.IPv4Address):
                        network = ipaddress.ip_network(f"{proxy}/32")
                    else:
                        network = ipaddress.ip_network(f"{proxy}/128")
                self._trusted_networks.add(network)
            except ValueError as e:
                logger.warning(f"Invalid trusted proxy configuration '{proxy}': {e}")

    def is_trusted_proxy(self, ip: str) -> bool:
        """Check if an IP address is a trusted proxy."""
        if not self._trusted_networks:
            return False

        try:
            client_ip = ipaddress.ip_address(ip)
            return any(client_ip in network for network in self._trusted_networks)
        except ValueError:
            return False

    def get_client_ip(self, request: Request) -> str:
        """
        Get the real client IP, respecting X-Forwarded-For only from trusted proxies.

        Args:
            request: FastAPI request object

        Returns:
            The client IP address
        """
        direct_ip = request.client.host if request.client else "unknown"

        # Only trust X-Forwarded-For if it comes from a trusted proxy
        if self.is_trusted_proxy(direct_ip):
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                # Take the first IP in the chain (original client)
                # X-Forwarded-For format: client, proxy1, proxy2, ...
                client_ip = forwarded_for.split(",")[0].strip()
                # Validate it's a real IP address
                try:
                    ipaddress.ip_address(client_ip)
                    return client_ip
                except ValueError:
                    logger.warning(f"Invalid IP in X-Forwarded-For header: {client_ip}")
                    return direct_ip

        return direct_ip


class AdminAuthRateLimiter:
    """
    Rate limiter specifically for admin authentication failures.

    Prevents brute force attacks on admin API key by rate limiting
    failed authentication attempts per IP.
    """

    def __init__(self, max_failures: int = 5, lockout_seconds: int = 300):
        """
        Initialize admin auth rate limiter.

        Args:
            max_failures: Maximum failed attempts before lockout
            lockout_seconds: Duration of lockout in seconds (default: 5 minutes)
        """
        self.max_failures = max_failures
        self.lockout_seconds = lockout_seconds
        self.failures: Dict[str, List[float]] = defaultdict(list)
        self.lockouts: Dict[str, float] = {}

    def record_failure(self, ip: str) -> None:
        """Record a failed authentication attempt."""
        current_time = time.time()

        # Clean up old failures
        self.failures[ip] = [
            t for t in self.failures[ip]
            if current_time - t < self.lockout_seconds
        ]

        # Record new failure
        self.failures[ip].append(current_time)

        # Check if lockout threshold reached
        if len(self.failures[ip]) >= self.max_failures:
            self.lockouts[ip] = current_time
            logger.warning(
                f"Admin auth lockout triggered for IP: {ip} "
                f"(failed {len(self.failures[ip])} times)"
            )

    def is_locked_out(self, ip: str) -> Tuple[bool, Optional[int]]:
        """
        Check if an IP is locked out.

        Returns:
            Tuple of (is_locked_out, seconds_remaining)
        """
        if ip not in self.lockouts:
            return False, None

        current_time = time.time()
        lockout_time = self.lockouts[ip]
        elapsed = current_time - lockout_time

        if elapsed >= self.lockout_seconds:
            # Lockout expired - clean up
            del self.lockouts[ip]
            self.failures[ip] = []
            return False, None

        remaining = int(self.lockout_seconds - elapsed)
        return True, remaining

    def clear_failures(self, ip: str) -> None:
        """Clear failure count for an IP (on successful auth)."""
        if ip in self.failures:
            del self.failures[ip]
        if ip in self.lockouts:
            del self.lockouts[ip]

    def reset(self) -> None:
        """Reset all state. Useful for testing."""
        self.failures.clear()
        self.lockouts.clear()


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
trusted_proxy_validator = TrustedProxyValidator()
admin_auth_rate_limiter = AdminAuthRateLimiter(max_failures=5, lockout_seconds=300)


async def check_rate_limit(request: Request) -> None:
    """
    FastAPI dependency to check conversion rate limit.

    Add this to conversion endpoints using Depends(check_rate_limit).

    Raises:
        HTTPException: 429 Too Many Requests if rate limit exceeded
    """
    # Get client IP using trusted proxy validation
    client_ip = trusted_proxy_validator.get_client_ip(request)

    is_allowed, reason = conversion_rate_limiter.is_allowed(client_ip)

    if not is_allowed:
        # Add Retry-After header to inform client when they can retry
        raise HTTPException(
            status_code=429,
            detail=reason,
            headers={"Retry-After": str(conversion_rate_limiter.time_window)}
        )


def get_client_ip(request: Request) -> str:
    """
    Get client IP using trusted proxy validation.

    This is a helper function for use in other modules.
    """
    return trusted_proxy_validator.get_client_ip(request)
